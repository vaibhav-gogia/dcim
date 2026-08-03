from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.drivers.bmc.base import BMCTarget, PowerState
from app.drivers.pdu.base import OutletState, PDUOutletTarget
from app.drivers.registry import get_bmc_driver, get_pdu_driver
from app.models.system import System


def bmc_target_from_system(system: System) -> BMCTarget:
    return BMCTarget(
        system_id=str(system.id),
        bmc_address=system.bmc_address,
        current_power_state=PowerState(system.power_state),
        power_state_updated_at=system.power_state_updated_at,
    )


async def _persist_power_state(db: AsyncSession, system: System, state: PowerState) -> None:
    if state.value != system.power_state:
        system.power_state = state.value
        system.power_state_updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(system)


async def resolve_power_state(db: AsyncSession, system: System) -> PowerState:
    """Resolve any pending transient state (e.g. booting -> on) and persist if it changed.

    Call this before reading power_state anywhere it's user-visible, since the simulated
    driver only advances state lazily when asked.
    """
    driver = get_bmc_driver(system.bmc_driver_type)
    resolved = await driver.get_power_state(bmc_target_from_system(system))
    await _persist_power_state(db, system, resolved)
    return resolved


async def _ensure_outlets_on(db: AsyncSession, system: System) -> None:
    """Requires system.power_connections loaded, each with .pdu_outlet.pdu eager-loaded."""
    changed = False
    for connection in system.power_connections:
        outlet = connection.pdu_outlet
        if outlet.state != OutletState.ON.value:
            pdu_driver = get_pdu_driver(outlet.pdu.driver_type)
            target = PDUOutletTarget(
                outlet_id=str(outlet.id),
                pdu_address=outlet.pdu.address,
                outlet_number=outlet.outlet_number,
                current_state=OutletState(outlet.state),
            )
            new_state = await pdu_driver.set_outlet_state(target, OutletState.ON)
            outlet.state = new_state.value
            changed = True
    if changed:
        await db.commit()


async def power_on_system(db: AsyncSession, system: System) -> PowerState:
    await resolve_power_state(db, system)
    await _ensure_outlets_on(db, system)
    driver = get_bmc_driver(system.bmc_driver_type)
    new_state = await driver.power_on(bmc_target_from_system(system))
    await _persist_power_state(db, system, new_state)
    return new_state


async def power_off_system(db: AsyncSession, system: System, graceful: bool = True) -> PowerState:
    await resolve_power_state(db, system)
    driver = get_bmc_driver(system.bmc_driver_type)
    new_state = await driver.power_off(bmc_target_from_system(system), graceful=graceful)
    await _persist_power_state(db, system, new_state)
    return new_state


async def power_cycle_system(db: AsyncSession, system: System) -> PowerState:
    await resolve_power_state(db, system)
    driver = get_bmc_driver(system.bmc_driver_type)
    new_state = await driver.power_cycle(bmc_target_from_system(system))
    await _persist_power_state(db, system, new_state)
    return new_state


async def set_outlet_state(db: AsyncSession, outlet, state: OutletState) -> OutletState:
    pdu_driver = get_pdu_driver(outlet.pdu.driver_type)
    target = PDUOutletTarget(
        outlet_id=str(outlet.id),
        pdu_address=outlet.pdu.address,
        outlet_number=outlet.outlet_number,
        current_state=OutletState(outlet.state),
    )
    new_state = await pdu_driver.set_outlet_state(target, state)
    outlet.state = new_state.value
    await db.commit()
    return new_state


async def cycle_outlet(db: AsyncSession, outlet) -> OutletState:
    pdu_driver = get_pdu_driver(outlet.pdu.driver_type)
    target = PDUOutletTarget(
        outlet_id=str(outlet.id),
        pdu_address=outlet.pdu.address,
        outlet_number=outlet.outlet_number,
        current_state=OutletState(outlet.state),
    )
    new_state = await pdu_driver.cycle_outlet(target)
    outlet.state = new_state.value
    await db.commit()
    return new_state
