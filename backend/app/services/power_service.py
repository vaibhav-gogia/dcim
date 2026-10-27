from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.power_connection import PowerConnection
from app.models.pdu_outlet import PDUOutlet

from app.drivers.bmc.base import BMCTarget, PowerState
from app.drivers.pdu.base import OutletState, PDUOutletTarget
from app.drivers.registry import get_bmc_driver, get_pdu_driver
from app.models.system import System
from app.audit import settle_system_events


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


async def power_inputs(db: AsyncSession, system: System):
    """No wiring means unknown supply, preserving standalone demo systems."""
    result = await db.execute(select(PowerConnection.psu_label, PDUOutlet.state)
        .join(PDUOutlet, PowerConnection.pdu_outlet_id == PDUOutlet.id)
        .where(PowerConnection.system_id == system.id))
    return result.all()


async def supply_is_lost(db: AsyncSession, system: System) -> bool:
    if system.bmc_driver_type != "simulated":
        return False
    inputs = await power_inputs(db, system)
    return bool(inputs) and not any(state == "on" for _, state in inputs)


async def resolve_power_state(db: AsyncSession, system: System) -> PowerState:
    """Resolve any pending transient state (e.g. booting -> on) and persist if it changed.

    Call this before reading power_state anywhere it's user-visible, since the simulated
    driver only advances state lazily when asked.
    """
    if await supply_is_lost(db, system):
        await _persist_power_state(db, system, PowerState.OFF)
        await settle_system_events(db, system.id, "off", supply_lost=True)
        return PowerState.OFF
    driver = get_bmc_driver(system.bmc_driver_type)
    resolved = await driver.get_power_state(bmc_target_from_system(system))
    await _persist_power_state(db, system, resolved)
    await settle_system_events(db, system.id, resolved.value)
    return resolved


async def power_on_system(db: AsyncSession, system: System) -> PowerState:
    await resolve_power_state(db, system)
    if await supply_is_lost(db, system):
        raise HTTPException(status_code=409, detail="No power available. Turn on a connected PDU outlet first.")
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
    if await supply_is_lost(db, system):
        raise HTTPException(status_code=409, detail="No power available. Turn on a connected PDU outlet first.")
    driver = get_bmc_driver(system.bmc_driver_type)
    new_state = await driver.power_cycle(bmc_target_from_system(system))
    await _persist_power_state(db, system, new_state)
    return new_state


async def set_outlet_state(db: AsyncSession, outlet, state: OutletState) -> OutletState:
    result = await db.execute(select(System).join(PowerConnection, PowerConnection.system_id == System.id)
        .where(PowerConnection.pdu_outlet_id == outlet.id).with_for_update(of=System))
    system = result.scalar_one_or_none()
    pdu_driver = get_pdu_driver(outlet.pdu.driver_type)
    target = PDUOutletTarget(
        outlet_id=str(outlet.id),
        pdu_address=outlet.pdu.address,
        outlet_number=outlet.outlet_number,
        current_state=OutletState(outlet.state),
    )
    new_state = await pdu_driver.set_outlet_state(target, state)
    outlet.state = new_state.value
    await db.flush()
    if system is not None and await supply_is_lost(db, system):
        system.power_state = PowerState.OFF.value
        system.power_state_updated_at = datetime.now(timezone.utc)
    await db.commit()
    if system is not None and system.power_state == "off":
        await settle_system_events(db, system.id, "off", supply_lost=True)
    return new_state


async def cycle_outlet(db: AsyncSession, outlet) -> OutletState:
    # Model the interruption, not just the relay's final ON state. Loss of the
    # last supply stops the server; restoring AC does not imply automatic boot.
    if outlet.pdu.driver_type == "simulated":
        await set_outlet_state(db, outlet, OutletState.OFF)
        return await set_outlet_state(db, outlet, OutletState.ON)
    pdu_driver = get_pdu_driver(outlet.pdu.driver_type)
    target = PDUOutletTarget(outlet_id=str(outlet.id), pdu_address=outlet.pdu.address,
        outlet_number=outlet.outlet_number, current_state=OutletState(outlet.state))
    new_state = await pdu_driver.cycle_outlet(target)
    outlet.state = new_state.value
    await db.commit()
    return new_state
