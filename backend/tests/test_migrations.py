from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, func
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_engine
from app.models import User, Portfolio, Asset
from app.seed import seed


def test_upgrade_seed_rollback_upgrade(tmp_path, monkeypatch):
    url = f'sqlite:///{tmp_path / "migration.db"}'
    monkeypatch.setenv('DATABASE_URL', url)
    get_settings.cache_clear()
    get_engine.cache_clear()
    config = Config('alembic.ini')
    try:
        command.upgrade(config, 'head')
        engine = get_engine()
        assert {'users', 'portfolios', 'assets', 'positions', 'quotes', 'alerts', 'simulations', 'audit_events'} <= set(inspect(engine).get_table_names())
        seed('development-password')
        seed('development-password')
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(User)) == 3
            assert db.scalar(select(func.count()).select_from(Portfolio)) == 3
            assert db.scalar(select(func.count()).select_from(Asset)) == 1
        command.downgrade(config, 'base')
        assert inspect(engine).get_table_names() == ['alembic_version']
        command.upgrade(config, 'head')
        engine.dispose()
    finally:
        get_settings.cache_clear()
        get_engine.cache_clear()
