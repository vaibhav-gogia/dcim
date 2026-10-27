from app.protected_route import ProtectedRoute
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import commit_inventory, get_db, get_system_or_404
from app.models.pdu_outlet import PDUOutlet
from app.models.pdu import PDU
from app.models.power_connection import PowerConnection
from app.models.system import System
from app.services.power_service import resolve_power_state
from app.models.rack import Rack
from app.schemas.power_connection import PowerConnectionCreate, PowerConnectionRead
from app.schemas.system import SystemCreate, SystemRead, SystemUpdate

router = APIRouter(route_class=ProtectedRoute, tags=["systems"])


def _ranges_overlap(a_start: int, a_height: int, b_start: int, b_height: int) -> bool:
    a_end = a_start + a_height - 1
    b_end = b_start + b_height - 1
    return a_start <= b_end and b_start <= a_end


async def _assert_no_overlap(
    db: AsyncSession, rack_id: uuid.UUID, u_position: int, u_height: int, exclude_system_id: uuid.UUID | None = None
) -> None:
    rack = await db.get(Rack, rack_id)
    if rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    if u_position + u_height - 1 > rack.u_height:
        raise HTTPException(status_code=409, detail=f"System must fit within rack capacity of {rack.u_height}U")
    result = await db.execute(select(System).where(System.rack_id == rack_id))
    for existing in result.scalars().all():
        if exclude_system_id is not None and existing.id == exclude_system_id:
            continue
        if _ranges_overlap(u_position, u_height, existing.u_position, existing.u_height):
            raise HTTPException(
                status_code=409,
                detail=f"U{u_position}-{u_position + u_height - 1} overlaps existing system "
                f"'{existing.name}' at U{existing.u_position}-{existing.u_position + existing.u_height - 1}",
            )


@router.get("/racks/{rack_id}/systems", response_model=list[SystemRead])
async def list_systems(rack_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")):
    result = await db.execute(select(System).where(System.rack_id == rack_id))
    systems = result.scalars().all()
    for system in systems:
        await resolve_power_state(db, system)
    return systems


@router.post("/racks/{rack_id}/systems", response_model=SystemRead, status_code=201)
async def create_system(rack_id: uuid.UUID, payload: SystemCreate, db: AsyncSession = Depends(get_db, scope="function")):
    await _assert_no_overlap(db, rack_id, payload.u_position, payload.u_height)
    system = System(rack_id=rack_id, **payload.model_dump())
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return system


@router.get("/systems/{system_id}", response_model=SystemRead)
async def get_system(system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db, scope="function")):
    await resolve_power_state(db, system)
    return system


@router.patch("/systems/{system_id}", response_model=SystemRead)
async def update_system(
    payload: SystemUpdate, system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db, scope="function")
):
    updates = payload.model_dump(exclude_unset=True)
    new_position = updates.get("u_position", system.u_position)
    new_height = updates.get("u_height", system.u_height)
    if "u_position" in updates or "u_height" in updates:
        await _assert_no_overlap(db, system.rack_id, new_position, new_height, exclude_system_id=system.id)
    for field, value in updates.items():
        setattr(system, field, value)
    await db.commit()
    await db.refresh(system)
    return system


@router.delete("/systems/{system_id}", status_code=204)
async def delete_system(system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db, scope="function")):
    await db.delete(system)
    await db.commit()


@router.get("/systems/{system_id}/power-connections", response_model=list[PowerConnectionRead])
async def list_power_connections(system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db, scope="function")):
    result = await db.execute(select(PowerConnection).where(PowerConnection.system_id == system.id).order_by(PowerConnection.psu_label))
    return result.scalars().all()


@router.post("/systems/{system_id}/power-connections", response_model=PowerConnectionRead, status_code=201)
async def create_power_connection(
    payload: PowerConnectionCreate, system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db, scope="function")
):
    # Serialize assignments for one system, including duplicate PSU-label checks.
    await db.execute(select(System).where(System.id == system.id).with_for_update())
    outlet = await db.get(PDUOutlet, payload.pdu_outlet_id)
    if outlet is None:
        raise HTTPException(status_code=404, detail="PDU outlet not found")
    pdu = await db.get(PDU, outlet.pdu_id)
    if pdu.rack_id != system.rack_id:
        raise HTTPException(status_code=409, detail="Choose an outlet in the same rack as this system")
    label = payload.psu_label.strip()
    existing = await db.execute(select(PowerConnection).where(PowerConnection.system_id == system.id))
    if any(c.psu_label and c.psu_label.strip().casefold() == label.casefold() for c in existing.scalars().all()):
        raise HTTPException(status_code=409, detail="This PSU label already has a connection. Disconnect it first.")
    occupied = await db.execute(select(PowerConnection).where(PowerConnection.pdu_outlet_id == outlet.id))
    if occupied.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="This outlet is already assigned to a system")
    connection = PowerConnection(system_id=system.id, pdu_outlet_id=outlet.id, psu_label=label)
    db.add(connection)
    await commit_inventory(db)
    await db.refresh(connection)
    return connection


@router.delete("/power-connections/{connection_id}", status_code=204)
async def delete_power_connection(connection_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")):
    connection = await db.get(PowerConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Power connection not found")
    await db.delete(connection)
    await commit_inventory(db)
