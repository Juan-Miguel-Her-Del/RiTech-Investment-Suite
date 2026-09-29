from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
from pydantic import BaseModel, Field

from app.config import Settings


class MarketError(Exception):
    def __init__(self, message: str, status: int = 502):
        self.message = message
        self.status = status


class MarketQuote(BaseModel):
    symbol: str = 'NDX'
    name: str = 'NASDAQ 100'
    value: Decimal = Field(gt=0)
    updated_at: datetime
    source: str
    is_demo: bool = False


async def fetch_quote(settings: Settings, client: httpx.AsyncClient) -> MarketQuote:
    if settings.market_provider == 'demo':
        return MarketQuote(value=Decimal('20000.00'), updated_at=datetime.now(timezone.utc), source='demo', is_demo=True)
    key = settings.market_api_key.get_secret_value()
    if not key:
        raise MarketError('El proveedor de mercado no está configurado.', 503)
    try:
        endpoint = ('https://financialmodelingprep.com/stable/quote'
                    if settings.market_provider == 'fmp' else 'https://api.twelvedata.com/quote')
        response = await client.get(endpoint, params={
            'symbol': settings.market_symbol, 'apikey': key,
        }, timeout=settings.market_timeout_seconds)
        if response.status_code == 429:
            raise MarketError('Se alcanzó el límite del proveedor. Intenta más tarde.', 503)
        if response.status_code == 401:
            raise MarketError('El proveedor rechazó la clave API. Revisa MARKET_API_KEY.', 503)
        if response.status_code == 403:
            raise MarketError('La cuenta del proveedor no tiene permiso para consultar este instrumento.', 503)
        if response.status_code == 402:
            raise MarketError('El plan actual del proveedor no incluye esta consulta. Verifica el acceso a índices en tu cuenta.', 503)
        if response.status_code == 404:
            try:
                error_data = response.json()
                message = str(error_data.get('message', '')).lower() if isinstance(error_data, dict) else ''
            except ValueError:
                message = ''
            if 'plan' in message and ('available starting' in message or 'upgrade' in message):
                raise MarketError('El plan actual de Twelve Data no incluye este instrumento. Para NDX, verifica el acceso a índices en tu cuenta.', 503)
            raise MarketError('El proveedor no encontró el instrumento. Revisa MARKET_SYMBOL y su disponibilidad en tu cuenta.', 503)
        response.raise_for_status()
        data = response.json()
        if settings.market_provider == 'fmp':
            if isinstance(data, dict) and 'Error Message' in data:
                raise MarketError('Financial Modeling Prep rechazó la consulta. Verifica la clave y los permisos del plan.', 503)
            if not isinstance(data, list):
                raise ValueError('Invalid response')
            if not data:
                raise MarketError('Financial Modeling Prep no devolvió cotización para el instrumento configurado.', 503)
            if len(data) != 1 or not isinstance(data[0], dict):
                raise ValueError('Invalid response')
            data = data[0]
        if not isinstance(data, dict):
            raise ValueError('Invalid response')
        if data.get('status') == 'error':
            raise MarketError('El proveedor no pudo entregar la cotización.', 503)
        if str(data.get('symbol', '')).upper() != settings.market_symbol.upper():
            raise ValueError('Unexpected instrument')
        value = Decimal(str(data['price' if settings.market_provider == 'fmp' else 'close']))
        timestamp = datetime.fromtimestamp(int(data['timestamp']), tz=timezone.utc)
        if not value.is_finite() or value <= 0:
            raise ValueError('Invalid price')
        return MarketQuote(value=value, updated_at=timestamp, source=settings.market_provider)
    except httpx.TimeoutException:
        raise MarketError('El proveedor de mercado tardó demasiado en responder.', 504) from None
    except httpx.HTTPStatusError:
        raise MarketError('El proveedor de mercado respondió con un error HTTP. Intenta más tarde.') from None
    except httpx.HTTPError:
        raise MarketError('No fue posible conectar con el proveedor de mercado.') from None
    except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError):
        raise MarketError('El proveedor devolvió una cotización inválida.') from None
