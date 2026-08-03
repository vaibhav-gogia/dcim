from sqlalchemy.ext.asyncio import AsyncSession

from app.drivers.bmc.base import SensorReading
from app.drivers.registry import get_bmc_driver
from app.models.system import System
from app.services.power_service import bmc_target_from_system, resolve_power_state


async def get_system_health(db: AsyncSession, system: System) -> tuple[str, SensorReading]:
    resolved_state = await resolve_power_state(db, system)
    driver = get_bmc_driver(system.bmc_driver_type)
    sensors = await driver.get_sensors(bmc_target_from_system(system))
    return resolved_state.value, sensors
