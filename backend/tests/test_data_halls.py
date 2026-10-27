"""Database-backed hierarchy tests. Run with RUN_DB_TESTS=1 after migrations.

Each test runs inside an outer transaction; API commits use savepoints so all
created inventory is rolled back without touching pre-existing records.
"""
import os
import uuid

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from app.main import app

pytestmark = pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Set RUN_DB_TESTS=1 to run PostgreSQL integration tests")


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async def override_db():
            async with AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint") as session:
                yield session
        app.dependency_overrides[get_db] = override_db
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test/api") as http:
                yield http
        finally:
            app.dependency_overrides.pop(get_db, None)
            await transaction.rollback()
    await engine.dispose()


async def create(client, path, payload):
    response = await client.post(path, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_hall_isolation_names_navigation_and_cascades(client):
    dc = await create(client, "/datacenters", {"name": "hall-test-" + uuid.uuid4().hex})
    hall_a = await create(client, f"/datacenters/{dc['id']}/data-halls", {"name": "Hall A"})
    hall_b = await create(client, f"/datacenters/{dc['id']}/data-halls", {"name": "Hall B"})
    duplicate = await client.post(f"/datacenters/{dc['id']}/data-halls", json={"name": "Hall A"})
    assert duplicate.status_code == 409
    rack_a = await create(client, f"/data-halls/{hall_a['id']}/racks", {"name": "R01"})
    rack_b = await create(client, f"/data-halls/{hall_b['id']}/racks", {"name": "R01"})
    duplicate = await client.post(f"/data-halls/{hall_a['id']}/racks", json={"name": "R01"})
    assert duplicate.status_code == 409
    system = await create(client, f"/racks/{rack_a['id']}/systems", {"name": "server", "u_position": 1})
    pdu = await create(client, f"/racks/{rack_a['id']}/pdus", {"name": "PDU", "outlet_count": 2})
    response = await client.patch(f"/data-halls/{hall_a['id']}", json={"name": "Renamed hall"})
    assert response.status_code == 200
    floor = (await client.get(f"/data-halls/{hall_a['id']}/floor")).json()
    assert floor['name'] == 'Renamed hall'
    assert floor['datacenter_name'] == dc['name']
    assert [r['id'] for r in floor['racks']] == [rack_a['id']]
    elevation = (await client.get(f"/racks/{rack_a['id']}/elevation")).json()
    assert elevation['data_hall_name'] == 'Renamed hall'
    assert elevation['datacenter_id'] == dc['id']
    assert elevation['systems'][0]['id'] == system['id']
    assert (await client.delete(f"/data-halls/{hall_a['id']}")).status_code == 204
    assert (await client.get(f"/racks/{rack_a['id']}")).status_code == 404
    assert (await client.get(f"/systems/{system['id']}")).status_code == 404
    assert (await client.get(f"/pdus/{pdu['id']}")).status_code == 404
    assert (await client.get(f"/racks/{rack_b['id']}")).status_code == 200
    assert (await client.delete(f"/datacenters/{dc['id']}")).status_code == 204
    assert (await client.get(f"/data-halls/{hall_b['id']}")).status_code == 404
    assert (await client.get(f"/racks/{rack_b['id']}")).status_code == 404


async def test_missing_parents_and_invalid_hall_name(client):
    missing = str(uuid.uuid4())
    for path in [f"/data-halls/{missing}", f"/data-halls/{missing}/floor", f"/data-halls/{missing}/racks", f"/datacenters/{missing}/data-halls"]:
        assert (await client.get(path)).status_code == 404
    assert (await client.post(f"/datacenters/{missing}/data-halls", json={"name": "Hall"})).status_code == 404
    assert (await client.post(f"/data-halls/{missing}/racks", json={"name": "Rack"})).status_code == 404
    assert (await client.post(f"/datacenters/{missing}/data-halls", json={"name": "   "})).status_code == 422


async def test_complete_rack_power_setup_and_wiring_guards(client):
    dc = await create(client, '/datacenters', {'name': 'power-test-' + uuid.uuid4().hex})
    hall = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall'})
    rack = await create(client, f"/data-halls/{hall['id']}/racks", {'name': 'Rack'})
    other_rack = await create(client, f"/data-halls/{hall['id']}/racks", {'name': 'Other rack'})
    system = await create(client, f"/racks/{rack['id']}/systems", {'name': 'Server', 'u_position': 1})
    other_system = await create(client, f"/racks/{rack['id']}/systems", {'name': 'Other server', 'u_position': 2})
    for name in ['PDU A', 'PDU B']:
        await create(client, f"/racks/{rack['id']}/pdus", {'name': name, 'outlet_count': 2})
    pdus = (await client.get(f"/racks/{rack['id']}/pdus")).json()
    assert len(pdus) == 2
    assert all(len(p['outlets']) == 2 for p in pdus)
    a, b = pdus[0], pdus[1]
    outlet_a, outlet_b = a['outlets'][0]['id'], b['outlets'][0]['id']
    wiring_path = f"/systems/{system['id']}/power-connections"
    connection_a = await create(client, wiring_path, {'psu_label': 'PSU1', 'pdu_outlet_id': outlet_a})
    assert (await client.post(wiring_path, json={'psu_label': 'psu1', 'pdu_outlet_id': outlet_b})).status_code == 409
    assert (await client.post(f"/systems/{other_system['id']}/power-connections", json={'psu_label': 'PSU1', 'pdu_outlet_id': outlet_a})).status_code == 409
    foreign_pdu = await create(client, f"/racks/{other_rack['id']}/pdus", {'name': 'Foreign PDU', 'outlet_count': 1})
    foreign_outlet = (await client.get(f"/racks/{other_rack['id']}/pdus")).json()[0]['outlets'][0]['id']
    assert (await client.post(wiring_path, json={'psu_label': 'PSU2', 'pdu_outlet_id': foreign_outlet})).status_code == 409
    await create(client, wiring_path, {'psu_label': 'PSU2', 'pdu_outlet_id': outlet_b})
    assert len((await client.get(wiring_path)).json()) == 2
    for pdu in pdus:
        outlet_id = pdu['outlets'][0]['id']
        assert (await client.post(f"/pdus/{pdu['id']}/outlets/{outlet_id}/on")).status_code == 200
    response = await client.post(f"/systems/{system['id']}/power/on")
    assert response.status_code == 200, response.text
    assert response.json()['power_state'] == 'booting'
    # Advance the stored transition timestamp instead of sleeping in the test.
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import update
    from app.models.system import System
    async for db in app.dependency_overrides[get_db]():
        await db.execute(update(System).where(System.id == uuid.UUID(system['id'])).values(power_state_updated_at=datetime.now(timezone.utc) - timedelta(seconds=30)))
        await db.commit()
    health = await client.get(f"/systems/{system['id']}/health")
    assert health.status_code == 200
    assert health.json()['power_state'] == 'on'
    cycle = await client.post(f"/systems/{system['id']}/power/cycle")
    assert cycle.status_code == 200
    assert cycle.json()['power_state'] == 'cycling'
    pdus = (await client.get(f"/racks/{rack['id']}/pdus")).json()
    assert all(next(o for o in p['outlets'] if o['outlet_number'] == 1)['state'] == 'on' for p in pdus)
    assert (await client.patch(f"/pdus/{a['id']}", json={'name': 'Renamed PDU'})).status_code == 200
    assert (await client.get(f"/pdus/{a['id']}")).json()['outlet_count'] == 2
    assert (await client.delete(f"/power-connections/{connection_a['id']}")).status_code == 204
    assert len((await client.get(wiring_path)).json()) == 1
    pdus = (await client.get(f"/racks/{rack['id']}/pdus")).json()
    released = next(o for p in pdus for o in p['outlets'] if o['id'] == outlet_a)
    assert released['connected_system_id'] is None
    assert released['state'] == 'on'  # Unwiring changes inventory, not physical power.
    await create(client, f"/systems/{other_system['id']}/power-connections", {'psu_label': 'PSU1', 'pdu_outlet_id': outlet_a})
    assert (await client.post(f"/racks/{rack['id']}/pdus", json={'name': 'Invalid', 'outlet_count': 0})).status_code == 422
    assert (await client.post(f"/racks/{uuid.uuid4()}/pdus", json={'name': 'Missing rack'})).status_code == 404


async def test_inventory_search_filters_pagination_and_transitions(client):
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import update
    from app.models.system import System
    dc = await create(client, '/datacenters', {'name': 'search-test-' + uuid.uuid4().hex})
    hall_a = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall A'})
    hall_b = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall B'})
    rack_a = await create(client, f"/data-halls/{hall_a['id']}/racks", {'name': 'Rack A'})
    rack_b = await create(client, f"/data-halls/{hall_b['id']}/racks", {'name': 'Rack B'})
    first = await create(client, f"/racks/{rack_a['id']}/systems", {'name': 'Alpha', 'u_position': 1, 'manufacturer': 'Dell', 'serial_number': 'SN%_001', 'model': 'R750'})
    await create(client, f"/racks/{rack_b['id']}/systems", {'name': 'Beta', 'u_position': 1, 'manufacturer': 'HPE', 'system_type': 'storage'})
    async def search(**params):
        return await client.get("/inventory/systems", params={"datacenter_id": dc["id"], **params})
    assert (await search()).json()['total'] == 2
    result = (await search(**{'q': 'sn%_001'})).json()
    assert result['total'] == 1
    assert result['items'][0]['id'] == first['id']
    assert result['items'][0]['data_hall_name'] == 'Hall A'
    assert (await search(**{'manufacturer': 'Dell', 'system_type': 'storage'})).json()['total'] == 0
    assert (await search(**{'data_hall_id': hall_b['id'], 'manufacturer': 'HPE'})).json()['total'] == 1
    assert (await search(**{'q': 'r750'})).json()['total'] == 1
    assert (await search(**{'q': 'hall b'})).json()['total'] == 1
    page = (await search(**{'offset': 1, 'limit': 1})).json()
    assert page['total'] == 2 and page['items'][0]['name'] == 'Beta'
    assert (await search(**{'q': 'absent-unique-value'})).json()['items'] == []
    assert (await search(**{'power_state': 'invalid'})).status_code == 422
    assert (await search(**{'limit': 101})).status_code == 422
    async for db in app.dependency_overrides[get_db]():
        await db.execute(update(System).where(System.id == uuid.UUID(first['id'])).values(power_state='booting', power_state_updated_at=datetime.now(timezone.utc) - timedelta(seconds=30)))
        await db.commit()
    assert (await search(**{'power_state': 'on'})).json()['total'] == 1
    assert (await search(**{'power_state': 'booting'})).json()['total'] == 0
    options = (await client.get('/inventory/filters')).json()
    assert 'Dell' in options['manufacturers'] and 'storage' in options['system_types']
    assert any(h['id'] == hall_b['id'] and h['datacenter_id'] == dc['id'] for h in options['data_halls'])


@pytest.mark.parametrize('feed_count', [1, 2])
@pytest.mark.parametrize('initial_state', ['on', 'booting'])
async def test_pdu_supply_loss_redundancy_and_restore(client, feed_count, initial_state):
    dc = await create(client, '/datacenters', {'name': 'supply-' + uuid.uuid4().hex})
    hall = await create(client, f"/datacenters/{dc['id']}/data-halls", {'name': 'Hall'})
    rack = await create(client, f"/data-halls/{hall['id']}/racks", {'name': 'Rack'})
    system = await create(client, f"/racks/{rack['id']}/systems", {'name': 'Server', 'u_position': 1})
    sid = system['id']
    feeds = []
    for i in range(feed_count):
        pdu = await create(client, f"/racks/{rack['id']}/pdus", {'name': f'PDU {i}', 'outlet_count': 1})
        pdus = (await client.get(f"/racks/{rack['id']}/pdus")).json()
        outlet = next(p for p in pdus if p['id'] == pdu['id'])['outlets'][0]
        await create(client, f'/systems/{sid}/power-connections', {'psu_label': f'PSU{i+1}', 'pdu_outlet_id': outlet['id']})
        feeds.append(f"/pdus/{pdu['id']}/outlets/{outlet['id']}")
    rejected = await client.post(f'/systems/{sid}/power/on')
    assert rejected.status_code == 409
    assert 'Turn on a connected PDU outlet first' in rejected.json()['detail']
    assert (await client.get(f'/systems/{sid}/power')).json()['power_state'] == 'off'
    for feed in feeds:
        assert (await client.get(feed)).json()['state'] == 'off'
        assert (await client.post(feed + '/on')).status_code == 200
    assert (await client.post(f'/systems/{sid}/power/on')).json()['power_state'] == 'booting'
    if initial_state == 'on':
        from sqlalchemy import update
        from app.models.system import System
        async for db in app.dependency_overrides[get_db]():
            await db.execute(update(System).where(System.id == uuid.UUID(sid)).values(power_state='on'))
            await db.commit()
    # Losing the final feed interrupts a running system or in-progress boot.
    for i, feed in enumerate(feeds):
        assert (await client.post(feed + '/off')).status_code == 200
        health = (await client.get(f'/systems/{sid}/health')).json()
        assert health['psus'][f'psu{i+1}'] == 'no_input'
        if i < feed_count - 1:
            assert health['power_state'] == initial_state
            assert health['psus']['psu2'] == 'ok'
    assert health['power_state'] == 'off'
    assert all(rpm == 0 for rpm in health['fans_rpm'].values())
    assert (await client.get(f'/systems/{sid}')).json()['power_state'] == 'off'
    elevation = (await client.get(f"/racks/{rack['id']}/elevation")).json()
    assert elevation['systems'][0]['power_state'] == 'off'
    search = (await client.get('/inventory/systems', params={'datacenter_id': dc['id'], 'power_state': 'off'})).json()
    assert search['total'] == 1
    assert (await client.post(f'/systems/{sid}/power/cycle')).status_code == 409
    # Restoring AC does not silently boot the machine.
    await client.post(feeds[0] + '/on')
    health = (await client.get(f'/systems/{sid}/health')).json()
    assert health['power_state'] == 'off'
    assert health['psus']['psu1'] == 'ok'
    assert (await client.post(f'/systems/{sid}/power/on')).json()['power_state'] == 'booting'
    # Power On must leave the second, unpowered feed unchanged.
    if feed_count == 2:
        assert (await client.get(feeds[1])).json()['state'] == 'off'
        assert (await client.get(f'/systems/{sid}/health')).json()['psus']['psu2'] == 'no_input'
        await client.post(feeds[1] + '/on')
    # Cycling one redundant feed is harmless; cycling the sole remaining feed is not.
    await client.post(feeds[0] + '/cycle')
    expected = 'booting' if feed_count == 2 else 'off'
    assert (await client.get(f'/systems/{sid}/power')).json()['power_state'] == expected
    if feed_count == 2:
        await client.post(feeds[1] + '/off')
        await client.post(feeds[0] + '/cycle')
        assert (await client.get(f'/systems/{sid}/power')).json()['power_state'] == 'off'
