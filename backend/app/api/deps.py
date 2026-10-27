import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.datacenter import DataCenter
from app.models.pdu import PDU
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.rack import Rack
from app.models.system import System

__all__ = ["get_db"]


async def get_datacenter_or_404(datacenter_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")) -> DataCenter:
    dc = await db.get(DataCenter, datacenter_id)
    if dc is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    return dc


async def get_rack_or_404(rack_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")) -> Rack:
    rack = await db.get(Rack, rack_id)
    if rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    return rack


async def get_system_or_404(system_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")) -> System:
    system = await db.get(System, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="System not found")
    return system


async def get_system_with_power_graph_or_404(
    system_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")
) -> System:
    """System eager-loaded with power_connections -> pdu_outlet -> pdu, for power actions."""
    stmt = (
        select(System)
        .where(System.id == system_id)
        .options(
            selectinload(System.power_connections)
            .selectinload(PowerConnection.pdu_outlet)
            .selectinload(PDUOutlet.pdu)
        )
    )
    result = await db.execute(stmt)
    system = result.scalar_one_or_none()
    if system is None:
        raise HTTPException(status_code=404, detail="System not found")
    return system


async def get_pdu_or_404(pdu_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")) -> PDU:
    stmt = select(PDU).where(PDU.id == pdu_id).options(selectinload(PDU.outlets))
    result = await db.execute(stmt)
    pdu = result.scalar_one_or_none()
    if pdu is None:
        raise HTTPException(status_code=404, detail="PDU not found")
    return pdu


async def get_outlet_or_404(outlet_id: uuid.UUID, pdu_id: uuid.UUID, db: AsyncSession = Depends(get_db, scope="function")) -> PDUOutlet:
    stmt = select(PDUOutlet).where(PDUOutlet.id == outlet_id).options(selectinload(PDUOutlet.pdu))
    result = await db.execute(stmt)
    outlet = result.scalar_one_or_none()
    if outlet is None or outlet.pdu_id != pdu_id:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return outlet


async def commit_inventory(db: AsyncSession) -> None:
    """Report inventory constraint conflicts without leaking database internals."""
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Inventory conflicts with an existing record. Check that the name is unique.") from error
