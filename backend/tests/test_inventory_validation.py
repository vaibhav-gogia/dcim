"""Inventory boundaries must hold even when callers bypass the forms."""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.routes.systems import _assert_no_overlap
from app.api.routes.racks import create_rack, update_rack
from app.schemas.datacenter import DataCenterCreate
from app.schemas.rack import RackCreate
from app.schemas.system import SystemCreate, SystemUpdate


@pytest.mark.parametrize("schema,payload", [
    (DataCenterCreate, {"name": "   "}),
    (RackCreate, {"name": "rack", "u_height": 0}),
    (RackCreate, {"name": "rack", "pos_x": float("inf")}),
    (SystemCreate, {"name": "server", "u_position": 0}),
    (SystemCreate, {"name": "server", "u_position": 1, "u_height": -1}),
    (SystemUpdate, {"u_height": None}),
    (SystemUpdate, {"name": ""}),
])
def test_invalid_inventory_inputs(schema, payload):
    with pytest.raises(ValidationError):
        schema(**payload)


def database(capacity=42, systems=()):
    db = AsyncMock()
    db.get.return_value = SimpleNamespace(u_height=capacity)
    result = MagicMock()
    result.scalars.return_value.all.return_value = systems
    db.execute.return_value = result
    return db


async def test_system_must_fit_rack_and_exact_boundary_is_allowed():
    db = database()
    await _assert_no_overlap(db, uuid.uuid4(), 41, 2)
    with pytest.raises(HTTPException) as error:
        await _assert_no_overlap(db, uuid.uuid4(), 42, 2)
    assert error.value.status_code == 409


async def test_missing_rack_is_not_a_database_error():
    db = database()
    db.get.return_value = None
    with pytest.raises(HTTPException) as error:
        await _assert_no_overlap(db, uuid.uuid4(), 1, 1)
    assert error.value.status_code == 404


async def test_overlap_rejected_but_editing_same_system_allowed():
    system_id = uuid.uuid4()
    db = database(systems=[SimpleNamespace(id=system_id, name="installed", u_position=2, u_height=2)])
    with pytest.raises(HTTPException) as error:
        await _assert_no_overlap(db, uuid.uuid4(), 3, 1)
    assert error.value.status_code == 409
    await _assert_no_overlap(db, uuid.uuid4(), 3, 1, exclude_system_id=system_id)


async def test_rack_cannot_shrink_below_installed_equipment():
    db = database(systems=[SimpleNamespace(u_position=40, u_height=3)])
    with pytest.raises(HTTPException) as error:
        await update_rack(RackCreate(name="rack", u_height=41), SimpleNamespace(id=uuid.uuid4()), db)
    assert error.value.status_code == 409
    db.commit.assert_not_awaited()


async def test_missing_hall_rejected_before_creating_rack():
    db = database()
    db.get.return_value = None
    with pytest.raises(HTTPException) as error:
        await create_rack(uuid.uuid4(), RackCreate(name="rack"), db)
    assert error.value.status_code == 404
    db.commit.assert_not_awaited()
