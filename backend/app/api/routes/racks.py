import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import commit_inventory, get_db, get_rack_or_404
from app.models.pdu import PDU
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.rack import Rack
from app.models.data_hall import DataHall
from app.models.system import System
from app.services.power_service import resolve_power_state
from app.schemas.pdu import PDUOutletRead, PDUWithOutletsRead
from app.schemas.rack import RackCreate, RackRead, HallLayoutUpdate
from app.schemas.system import RackElevationRead, SystemElevationRead

router = APIRouter(tags=["racks"])


@router.get("/data-halls/{data_hall_id}/racks", response_model=list[RackRead])
async def list_racks(data_hall_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if await db.get(DataHall, data_hall_id) is None:
        raise HTTPException(status_code=404, detail="Data hall not found")
    result = await db.execute(select(Rack).where(Rack.data_hall_id == data_hall_id))
    return result.scalars().all()


@router.post("/data-halls/{data_hall_id}/racks", response_model=RackRead, status_code=201)
async def create_rack(data_hall_id: uuid.UUID, payload: RackCreate, db: AsyncSession = Depends(get_db)):
    if await db.get(DataHall, data_hall_id) is None:
        raise HTTPException(status_code=404, detail="Data hall not found")
    rack = Rack(data_hall_id=data_hall_id, **payload.model_dump())
    db.add(rack)
    await commit_inventory(db)
    await db.refresh(rack)
    return rack


@router.get("/racks/{rack_id}", response_model=RackRead)
async def get_rack(rack: Rack = Depends(get_rack_or_404)):
    return rack


@router.patch("/racks/{rack_id}", response_model=RackRead)
async def update_rack(payload: RackCreate, rack: Rack = Depends(get_rack_or_404), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(System).where(System.rack_id == rack.id))
    if any(s.u_position + s.u_height - 1 > (payload.u_height if "u_height" in payload.model_fields_set else rack.u_height) for s in result.scalars().all()):
        raise HTTPException(status_code=409, detail="Rack capacity cannot be smaller than its installed systems")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rack, field, value)
    await commit_inventory(db)
    await db.refresh(rack)
    return rack


@router.delete("/racks/{rack_id}", status_code=204)
async def delete_rack(rack: Rack = Depends(get_rack_or_404), db: AsyncSession = Depends(get_db)):
    await db.delete(rack)
    await commit_inventory(db)


@router.get("/racks/{rack_id}/elevation", response_model=RackElevationRead)
async def get_rack_elevation(rack_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Rack).where(Rack.id == rack_id).options(selectinload(Rack.systems), selectinload(Rack.data_hall).selectinload(DataHall.datacenter))
    result = await db.execute(stmt)
    rack = result.scalar_one_or_none()
    if rack is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    for system in rack.systems:
        await resolve_power_state(db, system)
    systems = [SystemElevationRead.model_validate(s) for s in rack.systems]
    return RackElevationRead(id=rack.id, name=rack.name, u_height=rack.u_height, systems=systems, data_hall_id=rack.data_hall_id, data_hall_name=rack.data_hall.name, datacenter_id=rack.data_hall.datacenter_id, datacenter_name=rack.data_hall.datacenter.name)


@router.get("/racks/{rack_id}/pdus", response_model=list[PDUWithOutletsRead])
async def get_rack_pdus(rack_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(PDU)
        .where(PDU.rack_id == rack_id)
        .options(
            selectinload(PDU.outlets)
            .selectinload(PDUOutlet.power_connection)
            .selectinload(PowerConnection.system)
        )
    )
    result = await db.execute(stmt)
    pdus = result.scalars().all()

    response = []
    for pdu in pdus:
        outlets = []
        for outlet in sorted(pdu.outlets, key=lambda o: o.outlet_number):
            connection = outlet.power_connection
            system: System | None = connection.system if connection else None
            outlets.append(
                PDUOutletRead(
                    id=outlet.id,
                    outlet_number=outlet.outlet_number,
                    state=outlet.state,
                    connected_system_id=system.id if system else None,
                    connected_system_name=system.name if system else None,
                )
            )
        response.append(
            PDUWithOutletsRead(
                id=pdu.id,
                name=pdu.name,
                outlet_count=pdu.outlet_count,
                driver_type=pdu.driver_type,
                outlets=outlets,
            )
        )
    return response


@router.patch("/data-halls/{data_hall_id}/layout", response_model=list[RackRead])
async def update_hall_layout(data_hall_id: uuid.UUID, payload: HallLayoutUpdate, db: AsyncSession = Depends(get_db)):
    hall = await db.scalar(select(DataHall).where(DataHall.id == data_hall_id).with_for_update())
    if hall is None:
        raise HTTPException(status_code=404, detail="Data hall not found")
    racks = (await db.execute(select(Rack).where(Rack.data_hall_id == data_hall_id).with_for_update())).scalars().all()
    positions = {p.id: p for p in payload.racks}
    if len(positions) != len(payload.racks) or set(positions) != {r.id for r in racks}:
        raise HTTPException(status_code=409, detail="The hall inventory changed. Cancel and reload the layout.")
    for rack in racks:
        p = positions[rack.id]
        if rack.pos_x != p.previous_x or rack.pos_y != p.previous_y:
            raise HTTPException(status_code=409, detail="A rack moved since editing began. Cancel and reload the layout.")
    # Floor tiles occupy 150x110 within each 200-unit cell.
    for i, a in enumerate(payload.racks):
        for b in payload.racks[i + 1:]:
            if abs(a.pos_x - b.pos_x) < 0.75 and abs(a.pos_y - b.pos_y) < 0.55:
                raise HTTPException(status_code=409, detail="Rack positions overlap. Move them apart before saving.")
    for rack in racks:
        rack.pos_x, rack.pos_y = positions[rack.id].pos_x, positions[rack.id].pos_y
    await commit_inventory(db)
    return racks


@router.get("/racks/{rack_id}/deletion-summary")
async def rack_deletion_summary(rack: Rack = Depends(get_rack_or_404), db: AsyncSession = Depends(get_db)):
    system_ids = select(System.id).where(System.rack_id == rack.id)
    pdu_ids = select(PDU.id).where(PDU.rack_id == rack.id)
    outlet_ids = select(PDUOutlet.id).where(PDUOutlet.pdu_id.in_(pdu_ids))
    return {"systems": await db.scalar(select(func.count()).select_from(System).where(System.rack_id == rack.id)),
        "pdus": await db.scalar(select(func.count()).select_from(PDU).where(PDU.rack_id == rack.id)),
        "outlets": await db.scalar(select(func.count()).select_from(PDUOutlet).where(PDUOutlet.pdu_id.in_(pdu_ids))),
        "connections": await db.scalar(select(func.count()).select_from(PowerConnection).where(or_(PowerConnection.system_id.in_(system_ids), PowerConnection.pdu_outlet_id.in_(outlet_ids))))}
