"""Security and action-history regressions, isolated in temporary PostgreSQL schemas."""
import os
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta
import httpx
import pytest
from sqlalchemy import select, update
from app.main import app
from app.database import get_db
from app.models.security import User, LoginSession, AuditEvent
from app.models.system import System
from app.security import now, digest
from tests.test_data_halls import client, create

pytestmark = pytest.mark.skipif(os.getenv('RUN_DB_TESTS') != '1', reason='Set RUN_DB_TESTS=1 for PostgreSQL tests')
PASSWORD = 'test-password-12345'


@asynccontextmanager
async def browser(username=None, password=PASSWORD):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test/api', headers={'origin': 'http://localhost:5173'}) as http:
        if username:
            response = await http.post('/auth/login', json={'username': username, 'password': password})
            assert response.status_code == 200, response.text
            http.headers['x-csrf-token'] = http.cookies['dcim_csrf']
        yield http


async def test_roles_enforced_for_all_inventory_mutations(client):
    viewer = await create(client, '/users', {'username': 'viewer-' + uuid.uuid4().hex[:8], 'password': PASSWORD, 'role': 'viewer'})
    operator = await create(client, '/users', {'username': 'operator-' + uuid.uuid4().hex[:8], 'password': PASSWORD, 'role': 'operator'})
    async with browser(viewer['username']) as v, browser(operator['username']) as o, browser() as anonymous:
        assert (await v.get('/inventory/systems')).status_code == 200
        assert (await v.get('/history')).status_code == 200
        assert (await v.get('/users')).status_code == 403
        assert (await anonymous.get('/inventory/systems')).status_code == 401
        assert (await anonymous.post('/datacenters', json={'name': 'denied'})).status_code == 401
        # Every registered non-power inventory mutation is admin-only, including
        # layouts, deletion and wiring. Denial happens before body/path validation.
        paths = app.openapi()['paths']
        checked = 0
        for template, operations in paths.items():
            if not template.startswith('/api/') or template.startswith('/api/auth/'):
                continue
            for method in {'post', 'patch', 'delete', 'put'} & operations.keys():
                path = template.replace('/api', '', 1)
                import re
                path = re.sub(r'\{[^}]+\}', str(uuid.uuid4()), path)
                assert (await v.request(method, path, json={})).status_code == 403, (method, path)
                power = '/power/' in path or '/outlets/' in path
                if not power:
                    assert (await o.request(method, path, json={})).status_code == 403, (method, path)
                checked += 1
        assert checked >= 20
        events = (await client.get('/history', params={'limit': 100})).json()['items']
        assert any(e['actor'] == viewer['username'] and e['outcome'] == 'failed' and e['status_code'] == 403 for e in events), events


async def test_sessions_csrf_expiry_passwords_and_revocation(client):
    account = await create(client, '/users', {'username': 'sessions-' + uuid.uuid4().hex[:8], 'password': PASSWORD, 'role': 'operator'})
    async with browser() as anonymous:
        bad = await anonymous.post('/auth/login', json={'username': account['username'], 'password': 'wrong-password'})
        assert bad.status_code == 401
        assert 'dcim_session' not in anonymous.cookies
        cross_origin = await anonymous.post('/auth/login', headers={'origin': 'https://evil.invalid'}, json={'username': account['username'], 'password': PASSWORD})
        assert cross_origin.status_code == 403
    async with browser(account['username']) as http:
        assert (await http.get('/auth/me')).json()['role'] == 'operator'
        assert (await http.post('/auth/logout', headers={'x-csrf-token': ''})).status_code == 403
        assert (await http.post('/auth/logout', headers={'origin': 'https://evil.invalid'})).status_code == 403
        raw = http.cookies['dcim_session']
        async for db in app.dependency_overrides[get_db]():
            stored = await db.scalar(select(LoginSession).where(LoginSession.token_hash == digest(raw)))
            assert stored is not None and stored.token_hash != raw
            assert stored.csrf_hash != http.cookies['dcim_csrf']
            user = await db.get(User, uuid.UUID(account['id']))
            assert PASSWORD not in user.password_hash
            stored.expires_at = now() - timedelta(seconds=1)
            await db.commit()
        assert (await http.get('/auth/me')).status_code == 401
    async with browser(account['username']) as http:
        assert (await client.patch(f"/users/{account['id']}", json={'role': 'viewer'})).status_code == 200
        assert (await http.get('/auth/me')).status_code == 401
    async with browser(account['username']) as http:
        assert (await http.get('/auth/me')).json()['role'] == 'viewer'
        response = await http.post('/auth/password', json={'current_password': PASSWORD, 'new_password': 'replacement-password-123'})
        assert response.status_code == 204
        assert (await http.get('/auth/me')).status_code == 401
    async with browser(account['username'], 'replacement-password-123') as http:
        assert (await http.post('/auth/logout')).status_code == 204
        assert (await http.get('/auth/me')).status_code == 401
    assert (await client.patch(f"/users/{account['id']}", json={'is_active': False})).status_code == 200
    async with browser() as http:
        assert (await http.post('/auth/login', json={'username': account['username'], 'password': 'replacement-password-123'})).status_code == 401


async def test_last_admin_and_secret_redaction(client):
    me = (await client.get('/auth/me')).json()
    async for db in app.dependency_overrides[get_db]():
        await db.execute(update(User).where(User.id != uuid.UUID(me['id'])).values(is_active=False))
        await db.commit()
    assert (await client.patch(f"/users/{me['id']}", json={'role': 'viewer'})).status_code == 409
    assert (await client.patch(f"/users/{me['id']}", json={'is_active': False})).status_code == 409
    marker = 'tiny-secret'
    invalid = await client.post('/users', json={'username': 'invalid-user', 'password': marker})
    assert invalid.status_code == 422 and marker not in invalid.text
    payload = (await client.get('/users')).json()
    assert 'password_hash' not in str(payload)
    assert marker not in (await client.get('/history', params={'limit': 100})).text


async def test_power_confirmation_and_history_completion(client):
    dc = await create(client, '/datacenters', {'name': 'audit-' + uuid.uuid4().hex})
    hall = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall'})
    rack = await create(client, f"/data-halls/{hall['id']}/racks", {'name': 'Audit rack'})
    system = await create(client, f"/racks/{rack['id']}/systems", {'name': 'Audit server', 'u_position': 1})
    sid = system['id']
    operator = await create(client, '/users', {'username': 'power-' + uuid.uuid4().hex[:8], 'password': PASSWORD, 'role': 'operator'})
    async with browser(operator['username']) as http:
        assert (await http.post(f'/systems/{sid}/power/cycle')).status_code == 409
        assert (await http.post(f'/systems/{sid}/power/on')).status_code == 200
        history = (await http.get('/history', params={'system_id': sid})).json()['items']
        assert any(e['outcome'] == 'pending' and e['actor'] == operator['username'] for e in history)
        async for db in app.dependency_overrides[get_db]():
            await db.execute(update(System).where(System.id == uuid.UUID(sid)).values(power_state_updated_at=now() - timedelta(seconds=30)))
            await db.commit()
        history = (await http.get('/history', params={'system_id': sid})).json()['items']
        assert any(e['outcome'] == 'succeeded' and '/power/on' in e['action'] for e in history), history
        assert (await http.post(f'/systems/{sid}/power/off', headers={'x-confirm-action': 'yes'})).status_code == 200
        assert (await http.post(f'/systems/{uuid.uuid4()}/power/on')).status_code == 404
    assert (await client.delete(f"/racks/{rack['id']}")).status_code == 204
    history = (await client.get('/history', params={'rack_id': rack['id']})).json()['items']
    assert any(e['target'] == 'Audit server' for e in history)
    assert any(e['target'] == 'Audit rack' and e['action'].startswith('DELETE') and e['outcome'] == 'succeeded' for e in history)


async def test_login_throttle_and_lock_expiry(client):
    account = await create(client, '/users', {'username': 'throttle-' + uuid.uuid4().hex[:8], 'password': PASSWORD, 'role': 'viewer'})
    async with browser() as http:
        for _ in range(5):
            assert (await http.post('/auth/login', json={'username': account['username'], 'password': 'incorrect'})).status_code == 401
        assert (await http.post('/auth/login', json={'username': account['username'], 'password': PASSWORD})).status_code == 401
        async for db in app.dependency_overrides[get_db]():
            await db.execute(update(User).where(User.id == uuid.UUID(account['id'])).values(locked_until=now() - timedelta(seconds=1)))
            await db.commit()
        login = await http.post('/auth/login', json={'username': account['username'], 'password': PASSWORD})
        assert login.status_code == 200
        cookies = login.headers.get_list('set-cookie')
        assert any('HttpOnly' in cookie and 'SameSite=strict' in cookie for cookie in cookies if cookie.startswith('dcim_session='))
        assert login.headers['cache-control'] == 'no-store'


async def test_unknown_driver_failure_is_not_reported_as_success(client, monkeypatch):
    from app.drivers.bmc.simulated import SimulatedBMCDriver
    dc = await create(client, '/datacenters', {'name': 'unknown-' + uuid.uuid4().hex})
    hall = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall'})
    rack = await create(client, f"/data-halls/{hall['id']}/racks", {'name': 'Rack'})
    system = await create(client, f"/racks/{rack['id']}/systems", {'name': 'Server', 'u_position': 1})
    async def timeout(self, target):
        raise TimeoutError('driver transport unavailable')
    monkeypatch.setattr(SimulatedBMCDriver, 'power_on', timeout)
    with pytest.raises(TimeoutError):
        await client.post(f"/systems/{system['id']}/power/on")
    events = (await client.get('/history', params={'system_id': system['id']})).json()['items']
    assert any(e['outcome'] == 'unknown' and e['status_code'] == 500 for e in events)
    assert not any(e['outcome'] == 'succeeded' and '/power/on' in e['action'] for e in events)
