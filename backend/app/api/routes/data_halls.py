import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import commit_inventory, get_db
from app.models.data_hall import DataHall
from app.models.datacenter import DataCenter
from app.schemas.data_hall import DataHallCreate, DataHallRead, DataHallFloorRead

router = APIRouter(tags=["data halls"])


async def get_hall(data_hall_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    hall = await db.get(DataHall, data_hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Data hall not found")
    return hall


@router.get("/datacenters/{datacenter_id}/data-halls", response_model=list[DataHallRead])
async def list_halls(datacenter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    if await db.get(DataCenter, datacenter_id) is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    result = await db.execute(select(DataHall).where(DataHall.datacenter_id == datacenter_id).order_by(DataHall.name))
    return result.scalars().all()


@router.post("/datacenters/{datacenter_id}/data-halls", response_model=DataHallRead, status_code=201)
async def create_hall(datacenter_id: uuid.UUID, payload: DataHallCreate, db: AsyncSession = Depends(get_db)):
    if await db.get(DataCenter, datacenter_id) is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    hall = DataHall(datacenter_id=datacenter_id, **payload.model_dump())
    db.add(hall)
    await commit_inventory(db)
    await db.refresh(hall)
    return hall


@router.get("/data-halls/{data_hall_id}", response_model=DataHallRead)
async def read_hall(hall: DataHall = Depends(get_hall)):
    return hall


@router.patch("/data-halls/{data_hall_id}", response_model=DataHallRead)
async def update_hall(payload: DataHallCreate, hall: DataHall = Depends(get_hall), db: AsyncSession = Depends(get_db)):
    hall.name = payload.name
    await commit_inventory(db)
    await db.refresh(hall)
    return hall


@router.delete("/data-halls/{data_hall_id}", status_code=204)
async def delete_hall(hall: DataHall = Depends(get_hall), db: AsyncSession = Depends(get_db)):
    await db.delete(hall)
    await commit_inventory(db)


@router.get("/data-halls/{data_hall_id}/floor", response_model=DataHallFloorRead)
async def hall_floor(data_hall_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataHall).where(DataHall.id == data_hall_id).options(selectinload(DataHall.racks), selectinload(DataHall.datacenter)))
    hall = result.scalar_one_or_none()
    if hall is None:
        raise HTTPException(status_code=404, detail="Data hall not found")
    return DataHallFloorRead(id=hall.id, name=hall.name, datacenter_id=hall.datacenter_id, datacenter_name=hall.datacenter.name, racks=hall.racks)
