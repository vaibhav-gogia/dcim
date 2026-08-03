from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_outlet_or_404, get_system_with_power_graph_or_404
from app.drivers.pdu.base import OutletState
from app.models.pdu_outlet import PDUOutlet
from app.models.system import System
from app.schemas.pdu import OutletActionResponse
from app.schemas.system import PowerActionResponse
from app.services import power_service

router = APIRouter(tags=["power"])


@router.get("/systems/{system_id}/power", response_model=PowerActionResponse)
async def get_system_power(
    system: System = Depends(get_system_with_power_graph_or_404), db: AsyncSession = Depends(get_db)
):
    state = await power_service.resolve_power_state(db, system)
    return PowerActionResponse(power_state=state.value)


@router.post("/systems/{system_id}/power/on", response_model=PowerActionResponse)
async def power_on(system: System = Depends(get_system_with_power_graph_or_404), db: AsyncSession = Depends(get_db)):
    state = await power_service.power_on_system(db, system)
    return PowerActionResponse(power_state=state.value)


@router.post("/systems/{system_id}/power/off", response_model=PowerActionResponse)
async def power_off(system: System = Depends(get_system_with_power_graph_or_404), db: AsyncSession = Depends(get_db)):
    state = await power_service.power_off_system(db, system)
    return PowerActionResponse(power_state=state.value)


@router.post("/systems/{system_id}/power/cycle", response_model=PowerActionResponse)
async def power_cycle(
    system: System = Depends(get_system_with_power_graph_or_404), db: AsyncSession = Depends(get_db)
):
    state = await power_service.power_cycle_system(db, system)
    return PowerActionResponse(power_state=state.value)


@router.get("/pdus/{pdu_id}/outlets/{outlet_id}", response_model=OutletActionResponse)
async def get_outlet(outlet: PDUOutlet = Depends(get_outlet_or_404)):
    return OutletActionResponse(state=outlet.state)


@router.post("/pdus/{pdu_id}/outlets/{outlet_id}/on", response_model=OutletActionResponse)
async def outlet_on(outlet: PDUOutlet = Depends(get_outlet_or_404), db: AsyncSession = Depends(get_db)):
    state = await power_service.set_outlet_state(db, outlet, OutletState.ON)
    return OutletActionResponse(state=state.value)


@router.post("/pdus/{pdu_id}/outlets/{outlet_id}/off", response_model=OutletActionResponse)
async def outlet_off(outlet: PDUOutlet = Depends(get_outlet_or_404), db: AsyncSession = Depends(get_db)):
    state = await power_service.set_outlet_state(db, outlet, OutletState.OFF)
    return OutletActionResponse(state=state.value)


@router.post("/pdus/{pdu_id}/outlets/{outlet_id}/cycle", response_model=OutletActionResponse)
async def outlet_cycle(outlet: PDUOutlet = Depends(get_outlet_or_404), db: AsyncSession = Depends(get_db)):
    state = await power_service.cycle_outlet(db, outlet)
    return OutletActionResponse(state=state.value)
