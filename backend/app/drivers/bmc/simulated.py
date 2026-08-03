import random
from datetime import datetime, timezone

from app.drivers.bmc.base import BMCDriver, BMCTarget, PowerState, SensorReading

BOOT_SECS = 8
SHUTDOWN_SECS = 5
CYCLE_SECS = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _elapsed(target: BMCTarget) -> float:
    if target.power_state_updated_at is None:
        return float("inf")
    updated_at = target.power_state_updated_at
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    return (_now() - updated_at).total_seconds()


class SimulatedBMCDriver(BMCDriver):
    """Simulates BMC power transitions and sensor readings with no real hardware.

    Transitions are resolved lazily on read: a caller sets a transient state
    (BOOTING/SHUTTING_DOWN/CYCLING) with a timestamp, and this driver reports the
    resolved terminal state once enough time has elapsed. This lets the UI show a
    live "booting -> on" transition purely from polling, with no background worker.
    """

    async def get_power_state(self, target: BMCTarget) -> PowerState:
        state = target.current_power_state
        elapsed = _elapsed(target)

        if state == PowerState.BOOTING and elapsed >= BOOT_SECS:
            return PowerState.ON
        if state == PowerState.SHUTTING_DOWN and elapsed >= SHUTDOWN_SECS:
            return PowerState.OFF
        if state == PowerState.CYCLING and elapsed >= CYCLE_SECS:
            return PowerState.ON
        return state

    async def power_on(self, target: BMCTarget) -> PowerState:
        resolved = await self.get_power_state(target)
        if resolved == PowerState.ON:
            return PowerState.ON
        return PowerState.BOOTING

    async def power_off(self, target: BMCTarget, graceful: bool = True) -> PowerState:
        resolved = await self.get_power_state(target)
        if resolved == PowerState.OFF:
            return PowerState.OFF
        return PowerState.SHUTTING_DOWN

    async def power_cycle(self, target: BMCTarget) -> PowerState:
        return PowerState.CYCLING

    async def get_sensors(self, target: BMCTarget) -> SensorReading:
        resolved_state = await self.get_power_state(target)
        seed = int.from_bytes(target.system_id.encode()[:8], "little", signed=False)
        base_rng = random.Random(seed)
        jitter_rng = random.Random()

        is_powered = resolved_state in (PowerState.ON, PowerState.BOOTING, PowerState.CYCLING)

        if is_powered:
            temps_c = {
                "cpu1": round(base_rng.uniform(38, 55) + jitter_rng.uniform(-1.5, 1.5), 1),
                "cpu2": round(base_rng.uniform(38, 55) + jitter_rng.uniform(-1.5, 1.5), 1),
                "inlet": round(base_rng.uniform(20, 27) + jitter_rng.uniform(-0.5, 0.5), 1),
            }
            fans_rpm = {
                f"fan{i}": int(base_rng.uniform(3000, 6000) + jitter_rng.uniform(-100, 100))
                for i in range(1, 5)
            }
            psus = {"psu1": "ok", "psu2": "ok"}
        else:
            temps_c = {"cpu1": 22.0, "cpu2": 22.0, "inlet": 22.0}
            fans_rpm = {f"fan{i}": 0 for i in range(1, 5)}
            psus = {"psu1": "no_input", "psu2": "no_input"}

        return SensorReading(temps_c=temps_c, fans_rpm=fans_rpm, psus=psus, read_at=_now())
