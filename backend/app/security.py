from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Role, User

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash('not-a-user-password')
bearer = HTTPBearer(auto_error=False)


def unauthorized():
    return HTTPException(401, 'Sesión inválida o expirada.', headers={'WWW-Authenticate': 'Bearer'})


def create_token(user: User) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    seconds = settings.jwt_minutes * 60
    token = jwt.encode({
        'sub': user.id, 'iat': now, 'exp': now + timedelta(seconds=seconds),
        'iss': settings.jwt_issuer, 'aud': settings.jwt_audience,
    }, settings.jwt_secret.get_secret_value(), algorithm='HS256')
    return token, seconds


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise unauthorized()
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret.get_secret_value(),
                             algorithms=['HS256'], issuer=settings.jwt_issuer,
                             audience=settings.jwt_audience, options={'require': ['sub', 'exp', 'iat', 'iss', 'aud']})
        user = db.get(User, payload['sub'])
    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise unauthorized() from None
    if user is None or not user.active:
        raise unauthorized()
    return user


def require_roles(*roles: Role):
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, 'Tu rol no permite esta operación.')
        return user
    return check
