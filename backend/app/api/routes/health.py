from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_system_or_404
from app.models.system import System
from app.schemas.system import SystemHealthRead
from app.services.health_service import get_system_health

router = APIRouter(tags=["health"])


@router.get("/ping", tags=["meta"])
async def ping():
    return {"status": "ok"}


@router.get("/systems/{system_id}/health", response_model=SystemHealthRead)
async def system_health(system: System = Depends(get_system_or_404), db: AsyncSession = Depends(get_db)):
    power_state, sensors = await get_system_health(db, system)
    return SystemHealthRead(
        power_state=power_state,
        temps_c=sensors.temps_c,
        fans_rpm=sensors.fans_rpm,
        psus=sensors.psus,
        read_at=sensors.read_at,
    )
