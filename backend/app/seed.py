"""Idempotent development seed. Password is supplied interactively or through SEED_PASSWORD."""
import getpass
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import Asset, Portfolio, Role, User
from app.security import password_hash


def seed(password: str):
    if len(password) < 12:
        raise ValueError('Usa una contraseña de desarrollo de al menos 12 caracteres.')
    with Session(get_engine()) as db:
        for role in Role:
            email = f'{role.name}@ritech.local'
            user = db.scalar(select(User).where(User.email == email))
            if user is None:
                user = User(email=email, name=f'{role.value} de desarrollo', role=role,
                            password_hash=password_hash.hash(password))
                db.add(user)
                db.flush()
                db.add(Portfolio(owner_id=user.id, name='Portafolio de desarrollo', currency='USD'))
        if db.scalar(select(Asset).where(Asset.symbol == 'NDX')) is None:
            db.add(Asset(symbol='NDX', name='NASDAQ 100', kind='index', currency='USD'))
        db.commit()


if __name__ == '__main__':
    seed(os.environ.get('SEED_PASSWORD') or getpass.getpass('Contraseña para usuarios de desarrollo: '))
    print('Seed listo: analista@ritech.local, gerente@ritech.local, administrador@ritech.local')
