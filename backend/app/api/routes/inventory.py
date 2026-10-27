from app.protected_route import ProtectedRoute
"""Search system inventory with location context and bounded result pages."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.system import System
from app.models.power_connection import PowerConnection
from app.models.pdu_outlet import PDUOutlet
from app.models.rack import Rack
from app.models.data_hall import DataHall
from app.models.datacenter import DataCenter
from app.drivers.bmc.base import PowerState
from app.drivers.bmc.simulated import BOOT_SECS, SHUTDOWN_SECS, CYCLE_SECS

router = APIRouter(route_class=ProtectedRoute, prefix="/inventory", tags=["inventory"])


def effective_power_state():
    now = datetime.now(timezone.utc)
    transitions = [("booting", BOOT_SECS, "on"), ("cycling", CYCLE_SECS, "on"), ("shutting_down", SHUTDOWN_SECS, "off")]
    wired = select(PowerConnection.id).where(PowerConnection.system_id == System.id).exists()
    powered = select(PowerConnection.id).join(PDUOutlet, PowerConnection.pdu_outlet_id == PDUOutlet.id).where(PowerConnection.system_id == System.id, PDUOutlet.state == 'on').exists()
    return case((and_(System.bmc_driver_type == 'simulated', wired, ~powered), 'off'), *[(and_(System.bmc_driver_type == 'simulated', System.power_state == source,
        or_(System.power_state_updated_at.is_(None), System.power_state_updated_at <= now - timedelta(seconds=seconds))), target)
        for source, seconds, target in transitions], else_=System.power_state)


@router.get("/systems")
async def search_systems(
    q: str = Query(default="", max_length=200),
    datacenter_id: uuid.UUID | None = None,
    data_hall_id: uuid.UUID | None = None,
    manufacturer: str | None = Query(default=None, max_length=120),
    system_type: str | None = Query(default=None, max_length=32),
    power_state: PowerState | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    db: AsyncSession = Depends(get_db, scope="function"),
):
    state = effective_power_state()
    stmt = select(System, Rack, DataHall, DataCenter, state.label('effective_state')).join(Rack, System.rack_id == Rack.id).join(DataHall, Rack.data_hall_id == DataHall.id).join(DataCenter, DataHall.datacenter_id == DataCenter.id)
    if q.strip():
        # contains(autoescape) treats %, _ and / as literal search characters.
        stmt = stmt.where(or_(*[func.lower(column).contains(q.strip().lower(), autoescape=True) for column in
            [System.name, System.serial_number, System.manufacturer, System.model, Rack.name, DataHall.name, DataCenter.name, DataCenter.location]]))
    for column, value in [(DataCenter.id, datacenter_id), (DataHall.id, data_hall_id), (System.manufacturer, manufacturer), (System.system_type, system_type)]:
        if value is not None:
            stmt = stmt.where(column == value)
    if power_state is not None:
        stmt = stmt.where(state == power_state.value)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (await db.execute(stmt.order_by(func.lower(System.name), System.id).offset(offset).limit(limit))).all()
    return {"total": total, "offset": offset, "limit": limit, "items": [
        {"id": system.id, "name": system.name, "serial_number": system.serial_number,
         "manufacturer": system.manufacturer, "model": system.model, "system_type": system.system_type,
         "power_state": current_state, "rack_id": rack.id, "rack_name": rack.name,
         "data_hall_id": hall.id, "data_hall_name": hall.name, "datacenter_id": dc.id, "datacenter_name": dc.name}
        for system, rack, hall, dc, current_state in rows]}


@router.get("/filters")
async def inventory_filters(db: AsyncSession = Depends(get_db, scope="function")):
    manufacturers = (await db.execute(select(System.manufacturer).where(System.manufacturer.is_not(None), System.manufacturer != '').distinct().order_by(System.manufacturer))).scalars().all()
    types = (await db.execute(select(System.system_type).distinct().order_by(System.system_type))).scalars().all()
    halls = (await db.execute(select(DataHall).order_by(DataHall.name))).scalars().all()
    return {"manufacturers": manufacturers, "system_types": types,
        "data_halls": [{"id": h.id, "name": h.name, "datacenter_id": h.datacenter_id} for h in halls]}
