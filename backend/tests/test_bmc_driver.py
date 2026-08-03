from datetime import datetime, timedelta, timezone

import pytest

from app.drivers.bmc.base import BMCTarget, PowerState
from app.drivers.bmc.simulated import BOOT_SECS, CYCLE_SECS, SHUTDOWN_SECS, SimulatedBMCDriver

driver = SimulatedBMCDriver()


def target(state: PowerState, seconds_ago: float | None) -> BMCTarget:
    updated_at = None if seconds_ago is None else datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    return BMCTarget(system_id="sys-1", bmc_address=None, current_power_state=state, power_state_updated_at=updated_at)


@pytest.mark.asyncio
async def test_power_on_from_off_returns_booting():
    result = await driver.power_on(target(PowerState.OFF, None))
    assert result == PowerState.BOOTING


@pytest.mark.asyncio
async def test_booting_resolves_to_on_after_delay():
    t = target(PowerState.BOOTING, BOOT_SECS + 1)
    assert await driver.get_power_state(t) == PowerState.ON


@pytest.mark.asyncio
async def test_booting_stays_booting_before_delay_elapses():
    t = target(PowerState.BOOTING, BOOT_SECS - 2)
    assert await driver.get_power_state(t) == PowerState.BOOTING


@pytest.mark.asyncio
async def test_power_off_from_on_returns_shutting_down():
    result = await driver.power_off(target(PowerState.ON, None))
    assert result == PowerState.SHUTTING_DOWN


@pytest.mark.asyncio
async def test_shutting_down_resolves_to_off_after_delay():
    t = target(PowerState.SHUTTING_DOWN, SHUTDOWN_SECS + 1)
    assert await driver.get_power_state(t) == PowerState.OFF


@pytest.mark.asyncio
async def test_power_on_when_already_on_is_noop():
    result = await driver.power_on(target(PowerState.ON, None))
    assert result == PowerState.ON


@pytest.mark.asyncio
async def test_cycle_resolves_to_on_after_full_delay():
    t = target(PowerState.CYCLING, CYCLE_SECS + 1)
    assert await driver.get_power_state(t) == PowerState.ON


@pytest.mark.asyncio
async def test_sensors_reflect_powered_off_state():
    t = target(PowerState.OFF, None)
    reading = await driver.get_sensors(t)
    assert all(rpm == 0 for rpm in reading.fans_rpm.values())
    assert all(status == "no_input" for status in reading.psus.values())


@pytest.mark.asyncio
async def test_sensors_reflect_powered_on_state():
    t = target(PowerState.ON, None)
    reading = await driver.get_sensors(t)
    assert all(rpm > 0 for rpm in reading.fans_rpm.values())
    assert all(status == "ok" for status in reading.psus.values())


@pytest.mark.asyncio
async def test_sensor_values_are_stable_for_same_system_id():
    t1 = target(PowerState.ON, None)
    r1 = await driver.get_sensors(t1)
    r2 = await driver.get_sensors(t1)
    # Base values seeded by system_id should stay in the same ballpark across calls
    assert abs(r1.temps_c["cpu1"] - r2.temps_c["cpu1"]) < 3.0
