import asyncio
import httpx
import pytest
from app.config import Settings
from app.market import MarketError, fetch_quote


def fetch(handler, provider='twelvedata', **kwargs):
    async def run():
        settings = Settings(market_provider=provider, market_api_key='test-key', **kwargs)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_quote(settings, client)
    return asyncio.run(run())


def test_normalizes_provider_response():
    def handler(request):
        assert request.url.params['symbol'] == 'NDX'
        assert request.url.params['apikey'] == 'test-key'
        return httpx.Response(200, json={'symbol': 'NDX', 'close': '20123.45', 'timestamp': 1700000000})
    quote = fetch(handler)
    assert str(quote.value) == '20123.45'
    assert quote.updated_at.tzinfo is not None
    assert not quote.is_demo


def test_fmp_normalizes_index_quote():
    def handler(request):
        assert request.url.host == 'financialmodelingprep.com'
        assert request.url.path == '/stable/quote'
        assert request.url.params['symbol'] == '^NDX'
        assert request.url.params['apikey'] == 'test-key'
        return httpx.Response(200, json=[{'symbol': '^NDX', 'price': 20123.45, 'timestamp': 1700000000}])
    quote = fetch(handler, provider='fmp', market_symbol='^NDX')
    assert str(quote.value) == '20123.45'
    assert quote.source == 'fmp'
    assert quote.symbol == 'NDX'
    assert not quote.is_demo
    assert quote.updated_at.isoformat() == '2023-11-14T22:13:20+00:00'


@pytest.mark.parametrize('data', [{}, [None], [{'symbol': 'QQQ', 'price': 10, 'timestamp': 1700000000}],
    [{'symbol': '^NDX', 'price': 'NaN', 'timestamp': 1700000000}],
    [{'symbol': '^NDX', 'price': -1, 'timestamp': 1700000000}],
    [{'symbol': '^NDX', 'price': 10, 'timestamp': 'invalid'}]])
def test_fmp_malformed_quote(data):
    with pytest.raises(MarketError) as error:
        fetch(lambda _: httpx.Response(200, json=data), provider='fmp', market_symbol='^NDX')
    assert error.value.status == 502


@pytest.mark.parametrize('status,data', [(402, {}), (403, {}), (429, {}), (200, []), (200, {'Error Message': 'test-key'})])
def test_fmp_unavailable_quote(status, data):
    with pytest.raises(MarketError) as error:
        fetch(lambda _: httpx.Response(status, json=data), provider='fmp', market_symbol='^NDX')
    assert error.value.status == 503
    assert 'test-key' not in error.value.message


@pytest.mark.parametrize('data', [[], {}, {'symbol': 'QQQ', 'close': '10', 'timestamp': 1700000000}, {'symbol': 'NDX', 'close': 'NaN', 'timestamp': 1700000000}, {'symbol': 'NDX', 'close': '-1', 'timestamp': 1700000000}, {'symbol': 'NDX', 'close': '10', 'timestamp': 'invalid'}])
def test_invalid_response(data):
    with pytest.raises(MarketError) as error:
        fetch(lambda _: httpx.Response(200, json=data))
    assert error.value.status == 502


@pytest.mark.parametrize('status', [401, 429, 500])
def test_provider_http_errors(status):
    with pytest.raises(MarketError):
        fetch(lambda _: httpx.Response(status))


def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout('timeout', request=request)
    with pytest.raises(MarketError) as error:
        fetch(handler)
    assert error.value.status == 504


def test_provider_error_body():
    with pytest.raises(MarketError):
        fetch(lambda _: httpx.Response(200, json={'status': 'error', 'message': 'private provider information'}))


def test_subscription_restriction_is_not_reported_as_connection_failure():
    with pytest.raises(MarketError) as error:
        fetch(lambda _: httpx.Response(404, json={'code': 404, 'status': 'error',
            'message': 'This symbol is available starting with the Grow or Venture plan. Consider upgrading now.'}))
    assert error.value.status == 503
    assert 'plan actual' in error.value.message


@pytest.mark.parametrize('status,expected', [(401, 'clave API'), (403, 'permiso'), (404, 'no encontró'), (500, 'error HTTP')])
def test_http_errors_have_actionable_messages(status, expected):
    with pytest.raises(MarketError) as error:
        fetch(lambda _: httpx.Response(status, json={'message': 'private provider information'}))
    assert expected in error.value.message
    assert 'private provider information' not in error.value.message
