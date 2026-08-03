import asyncio

from app.drivers.pdu.base import OutletState, PDUDriver, PDUOutletTarget

SWITCH_DELAY_SECS = 0.4


class SimulatedPDUDriver(PDUDriver):
    """Simulates near-instant PDU outlet relay switching with no real hardware."""

    async def get_outlet_state(self, target: PDUOutletTarget) -> OutletState:
        return target.current_state

    async def set_outlet_state(self, target: PDUOutletTarget, state: OutletState) -> OutletState:
        await asyncio.sleep(SWITCH_DELAY_SECS)
        return state

    async def cycle_outlet(self, target: PDUOutletTarget) -> OutletState:
        await asyncio.sleep(SWITCH_DELAY_SECS * 2)
        return OutletState.ON
