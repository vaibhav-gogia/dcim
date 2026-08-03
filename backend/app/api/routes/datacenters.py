import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_datacenter_or_404, get_db
from app.models.datacenter import DataCenter
from app.schemas.datacenter import DataCenterCreate, DataCenterRead
from app.schemas.rack import DataCenterFloorRead

router = APIRouter(prefix="/datacenters", tags=["datacenters"])


@router.get("", response_model=list[DataCenterRead])
async def list_datacenters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DataCenter))
    return result.scalars().all()


@router.post("", response_model=DataCenterRead, status_code=201)
async def create_datacenter(payload: DataCenterCreate, db: AsyncSession = Depends(get_db)):
    dc = DataCenter(**payload.model_dump())
    db.add(dc)
    await db.commit()
    await db.refresh(dc)
    return dc


@router.get("/{datacenter_id}", response_model=DataCenterRead)
async def get_datacenter(dc: DataCenter = Depends(get_datacenter_or_404)):
    return dc


@router.patch("/{datacenter_id}", response_model=DataCenterRead)
async def update_datacenter(
    payload: DataCenterCreate, dc: DataCenter = Depends(get_datacenter_or_404), db: AsyncSession = Depends(get_db)
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(dc, field, value)
    await db.commit()
    await db.refresh(dc)
    return dc


@router.delete("/{datacenter_id}", status_code=204)
async def delete_datacenter(dc: DataCenter = Depends(get_datacenter_or_404), db: AsyncSession = Depends(get_db)):
    await db.delete(dc)
    await db.commit()


@router.get("/{datacenter_id}/floor", response_model=DataCenterFloorRead)
async def get_datacenter_floor(datacenter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(DataCenter).where(DataCenter.id == datacenter_id).options(selectinload(DataCenter.racks))
    result = await db.execute(stmt)
    dc = result.scalar_one_or_none()
    if dc is None:
        raise HTTPException(status_code=404, detail="Data center not found")
    return DataCenterFloorRead(id=dc.id, name=dc.name, racks=dc.racks)
