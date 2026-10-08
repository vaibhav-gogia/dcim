import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import commit_inventory, get_db, get_pdu_or_404
from app.models.pdu import PDU
from app.models.rack import Rack
from app.models.pdu_outlet import PDUOutlet
from app.schemas.pdu import PDUCreate, PDURead, PDUUpdate

router = APIRouter(tags=["pdus"])


@router.post("/racks/{rack_id}/pdus", response_model=PDURead, status_code=201)
async def create_pdu(rack_id: uuid.UUID, payload: PDUCreate, db: AsyncSession = Depends(get_db)):
    if await db.get(Rack, rack_id) is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    pdu = PDU(rack_id=rack_id, **payload.model_dump())
    db.add(pdu)
    await db.flush()
    for outlet_number in range(1, pdu.outlet_count + 1):
        db.add(PDUOutlet(pdu_id=pdu.id, outlet_number=outlet_number, state="off"))
    await commit_inventory(db)
    await db.refresh(pdu)
    return pdu


@router.get("/pdus/{pdu_id}", response_model=PDURead)
async def get_pdu(pdu: PDU = Depends(get_pdu_or_404)):
    return pdu


@router.patch("/pdus/{pdu_id}", response_model=PDURead)
async def update_pdu(payload: PDUUpdate, pdu: PDU = Depends(get_pdu_or_404), db: AsyncSession = Depends(get_db)):
    updates = payload.model_dump(exclude_unset=True, exclude={"outlet_count"})
    for field, value in updates.items():
        setattr(pdu, field, value)
    await commit_inventory(db)
    await db.refresh(pdu)
    return pdu


@router.delete("/pdus/{pdu_id}", status_code=204)
async def delete_pdu(pdu: PDU = Depends(get_pdu_or_404), db: AsyncSession = Depends(get_db)):
    await db.delete(pdu)
    await commit_inventory(db)
