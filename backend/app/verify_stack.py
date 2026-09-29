"""Validate PostgreSQL migrations and the API in a disposable database.

Run inside the development Compose container. Never touches the application database.
"""
import os
import secrets
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.config import get_settings
from app.database import get_engine


def main():
    settings = get_settings()
    original_url = make_url(settings.database_url)
    if original_url.get_backend_name() != 'postgresql':
        raise RuntimeError('This check requires PostgreSQL.')
    database_name = f'ritech_verify_{uuid4().hex}'
    admin = create_engine(original_url.set(database='postgres'), isolation_level='AUTOCOMMIT')
    created = False
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        created = True
        os.environ['DATABASE_URL'] = original_url.set(database=database_name).render_as_string(hide_password=False)
        os.environ['MARKET_PROVIDER'] = 'demo'
        get_settings.cache_clear()
        get_engine.cache_clear()
        config = Config('alembic.ini')
        command.upgrade(config, 'head')
        print('PASS: migration on empty PostgreSQL database')

        from app.seed import seed
        password = secrets.token_urlsafe(24)
        seed(password)
        seed(password)
        from app.main import app
        with TestClient(app) as client:
            assert client.get('/health/ready').status_code == 200
            assert client.get('/quotes/nasdaq100').status_code == 401
            for role in ['analista', 'gerente', 'administrador']:
                response = client.post('/auth/login', json={'email': f'{role}@ritech.local', 'password': password})
                assert response.status_code == 200
                headers = {'Authorization': f"Bearer {response.json()['access_token']}"}
                assert client.get('/auth/me', headers=headers).json()['role'].lower() == role
                quote = client.get('/quotes/nasdaq100', headers=headers)
                assert quote.status_code == 200 and quote.json()['is_demo'] is True
                users = client.get('/admin/users', headers=headers)
                assert users.status_code == (200 if role == 'administrador' else 403)
                if role == 'administrador':
                    assert len(users.json()) == 3
            assert client.post('/auth/login', json={'email': 'analista@ritech.local', 'password': 'wrong'}).status_code == 401
        print('PASS: idempotent seed, JWT, role permissions, Redis and demo quotes')
        command.downgrade(config, 'base')
        assert inspect(get_engine()).get_table_names() == ['alembic_version']
        command.upgrade(config, 'head')
        command.check(config)
        print('PASS: PostgreSQL rollback, reapply and schema/model consistency')
    finally:
        if created:
            get_engine().dispose()
            with admin.connect() as connection:
                connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
        admin.dispose()
        get_engine.cache_clear()
        get_settings.cache_clear()


if __name__ == '__main__':
    main()
