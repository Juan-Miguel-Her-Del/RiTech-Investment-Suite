from datetime import datetime, timedelta, timezone
import jwt
import pytest
from app.config import get_settings


def login(client, role='analista'):
    response = client.post('/auth/login', json={'email': f'{role}@ritech.local', 'password': 'development-password'})
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize('role', ['analista', 'gerente', 'administrador'])
def test_roles_can_login_and_get_quote(client, role):
    headers = login(client, role)
    assert client.get('/auth/me', headers=headers).json()['id'] == role
    quote = client.get('/quotes/nasdaq100', headers=headers)
    assert quote.status_code == 200
    assert quote.json()['is_demo'] is True
    assert float(quote.json()['value']) > 0
    assert quote.json()['updated_at']


@pytest.mark.parametrize('headers', [{}, {'Authorization': 'Bearer invalid'}, {'Authorization': 'Basic abc'}])
def test_protected_routes_reject_missing_or_invalid_tokens(client, headers):
    assert client.get('/quotes/nasdaq100', headers=headers).status_code == 401
    assert client.get('/admin/users', headers=headers).status_code == 401


@pytest.mark.parametrize('email,password', [('analista@ritech.local', 'wrong'), ('unknown@ritech.local', 'development-password')])
def test_invalid_credentials(client, email, password):
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Correo o contraseña incorrectos.'


def test_admin_authorization(client):
    for role in ['analista', 'gerente']:
        assert client.get('/admin/users', headers=login(client, role)).status_code == 403
    response = client.get('/admin/users', headers=login(client, 'administrador'))
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert 'password_hash' not in response.text


@pytest.mark.parametrize('case', ['expired', 'wrong_audience', 'wrong_issuer', 'wrong_signature', 'missing_exp'])
def test_rejects_invalid_claims(client, case):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {'sub': 'analista', 'iat': now, 'exp': now + timedelta(minutes=5),
               'iss': settings.jwt_issuer, 'aud': settings.jwt_audience}
    secret = settings.jwt_secret.get_secret_value()
    if case == 'expired': payload['exp'] = now - timedelta(seconds=1)
    if case == 'wrong_audience': payload['aud'] = 'other'
    if case == 'wrong_issuer': payload['iss'] = 'other'
    if case == 'wrong_signature': secret = 'another-secret-at-least-32-characters'
    if case == 'missing_exp': del payload['exp']
    token = jwt.encode(payload, secret, algorithm='HS256')
    assert client.get('/auth/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401


def test_health(client):
    assert client.get('/health/ready').status_code == 200
