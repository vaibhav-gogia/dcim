import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import commit_inventory, get_db, get_rack_or_404
from app.models.pdu import PDU
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.rack import Rack
from app.models.data_hall import DataHall
from app.models.system import System
from app.schemas.pdu import PDUOutletRead, PDUWithOutletsRead
from app.schemas.rack import RackCreate, RackRead
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
