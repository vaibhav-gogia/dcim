import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_system_or_404
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.system import System
from app.schemas.power_connection import PowerConnectionCreate, PowerConnectionRead
from app.schemas.system import SystemCreate, SystemRead, SystemUpdate

router = APIRouter(tags=["systems"])


def _ranges_overlap(a_start: int, a_height: int, b_start: int, b_height: int) -> bool:
    a_end = a_start + a_height - 1
    b_end = b_start + b_height - 1
    return a_start <= b_end and b_start <= a_end


async def _assert_no_overlap(
    db: AsyncSession, rack_id: uuid.UUID, u_position: int, u_height: int, exclude_system_id: uuid.UUID | None = None
) -> None:
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
async def list_systems(rack_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.rack_id == rack_id))
    return result.scalars().all()


@router.post("/racks/{rack_id}/systems", response_model=SystemRead, status_code=201)
async def create_system(rack_id: uuid.UUID, payload: SystemCreate, db: AsyncSession = Depends(get_db)):
    await _assert_no_overlap(db, rack_id, payload.u_position, payload.u_height)
    system = System(rack_id=rack_id, **payload.model_dump())
    db.add(system)
    await db.commit()
    await db.refresh(system)
    return system


@router.get("/systems/{system_id}", response_model=SystemRead)
async def get_system(system: System = Depends(get_system_or_404)):
    return system


@router.patch("/systems/{system_id}", response_model=SystemRead)
async def update_system(
    payload: SystemUpdate, system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db)
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
async def delete_system(system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db)):
    await db.delete(system)
    await db.commit()


@router.post("/systems/{system_id}/power-connections", response_model=PowerConnectionRead, status_code=201)
async def create_power_connection(
    payload: PowerConnectionCreate, system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db)
):
    outlet = await db.get(PDUOutlet, payload.pdu_outlet_id)
    if outlet is None:
        raise HTTPException(status_code=404, detail="PDU outlet not found")
    connection = PowerConnection(system_id=system.id, pdu_outlet_id=outlet.id, psu_label=payload.psu_label)
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/power-connections/{connection_id}", status_code=204)
async def delete_power_connection(connection_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    connection = await db.get(PowerConnection, connection_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Power connection not found")
    await db.delete(connection)
    await db.commit()
