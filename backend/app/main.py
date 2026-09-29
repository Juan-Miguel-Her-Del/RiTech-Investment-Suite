from contextlib import asynccontextmanager
import logging

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.market import MarketError, MarketQuote, fetch_quote
from app.models import AuditEvent, Role, User
from app.security import create_token, current_user, dummy_hash, password_hash, require_roles

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.redis = Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    async with httpx.AsyncClient() as client:
        app.state.http = client
        yield
    await app.state.redis.aclose()


app = FastAPI(title='RiTech Investment Suite', version='0.2.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins,
                   allow_methods=['GET', 'POST'], allow_headers=['Authorization', 'Content-Type'])


class LoginBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class UserView(BaseModel):
    id: str
    email: str
    name: str
    role: Role


def user_view(user: User) -> UserView:
    return UserView(id=user.id, email=user.email, name=user.name, role=user.role)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int
    user: UserView


@app.get('/health/live')
def live():
    return {'status': 'ok'}


@app.get('/health/ready')
async def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text('SELECT 1'))
        await app.state.redis.ping()
    except Exception:
        raise HTTPException(503, 'Servicios de datos no disponibles.') from None
    return {'status': 'ok', 'database': 'ok', 'redis': 'ok'}


@app.post('/auth/login', response_model=LoginResponse)
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    valid = password_hash.verify(body.password, user.password_hash if user else dummy_hash)
    if not valid or user is None or not user.active:
        raise HTTPException(401, 'Correo o contraseña incorrectos.')
    token, seconds = create_token(user)
    db.add(AuditEvent(user_id=user.id, action='auth.login'))
    db.commit()
    return LoginResponse(access_token=token, expires_in=seconds, user=user_view(user))


@app.get('/auth/me', response_model=UserView)
def me(user: User = Depends(current_user)):
    return user_view(user)


@app.get('/admin/users', response_model=list[UserView])
def users(_user: User = Depends(require_roles(Role.administrador)), db: Session = Depends(get_db)):
    return [user_view(user) for user in db.scalars(select(User).order_by(User.email).limit(100))]


@app.get('/quotes/nasdaq100', response_model=MarketQuote)
async def quote(_user: User = Depends(require_roles(Role.analista, Role.gerente, Role.administrador))):
    settings = get_settings()
    cache_key = f'quotes:{settings.market_provider}:{settings.market_symbol}'
    try:
        cached = await app.state.redis.get(cache_key)
        if cached:
            return MarketQuote.model_validate_json(cached)
    except (RedisError, ValueError):
        logger.warning('Quote cache unavailable; querying provider')
    try:
        result = await fetch_quote(settings, app.state.http)
    except MarketError as error:
        raise HTTPException(error.status, error.message) from None
    try:
        await app.state.redis.set(cache_key, result.model_dump_json(), ex=settings.market_cache_seconds)
    except RedisError:
        logger.warning('Unable to cache quote')
    return result
