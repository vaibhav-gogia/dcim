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
