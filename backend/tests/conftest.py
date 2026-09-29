import os
os.environ['JWT_SECRET'] = 'test-only-secret-with-at-least-32-characters'
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['MARKET_PROVIDER'] = 'demo'

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import password_hash


class FakeRedis:
    def __init__(self):
        self.values = {}
    async def get(self, key):
        return self.values.get(key)
    async def set(self, key, value, **kwargs):
        self.values[key] = value
    async def ping(self):
        return True
    async def aclose(self):
        pass


@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for role in Role:
            db.add(User(id=role.name, email=f'{role.name}@ritech.local', name=role.value,
                        role=role, password_hash=password_hash.hash('development-password')))
        db.commit()
    def override_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        app.state.redis = FakeRedis()
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
