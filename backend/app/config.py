from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str = 'postgresql+psycopg://ritech:ritech@localhost:5432/ritech'
    redis_url: str = 'redis://localhost:6379/0'
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = 'ritech-api'
    jwt_audience: str = 'ritech-app'
    jwt_minutes: int = Field(default=30, ge=1, le=120)
    cors_origins: list[str] = ['http://localhost:3000']
    market_provider: Literal['demo', 'twelvedata', 'fmp'] = 'demo'
    market_api_key: SecretStr = SecretStr('')
    market_symbol: str = 'NDX'
    market_timeout_seconds: float = Field(default=8, gt=0, le=30)
    market_cache_seconds: int = Field(default=60, ge=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
