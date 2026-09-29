import enum
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def new_id() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    analista = 'Analista'
    gerente = 'Gerente'
    administrador = 'Administrador'


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, create_constraint=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Portfolio(Base):
    __tablename__ = 'portfolios'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint('owner_id', 'name'),)


class Asset(Base):
    __tablename__ = 'assets'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default='USD')


class Position(Base):
    __tablename__ = 'positions'
    portfolio_id: Mapped[str] = mapped_column(ForeignKey('portfolios.id', ondelete='CASCADE'), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    __table_args__ = (CheckConstraint('quantity >= 0'), CheckConstraint('average_cost >= 0'))


class Quote(Base):
    __tablename__ = 'quotes'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(40))
    __table_args__ = (CheckConstraint('value > 0'), UniqueConstraint('asset_id', 'updated_at', 'source'))


class Alert(Base):
    __tablename__ = 'alerts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey('assets.id'), index=True)
    threshold: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    direction: Mapped[str] = mapped_column(String(5))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint('threshold > 0'), CheckConstraint("direction IN ('above', 'below')"))


class Simulation(Base):
    __tablename__ = 'simulations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey('portfolios.id'), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    parameters: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
