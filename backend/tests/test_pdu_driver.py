import pytest

from app.drivers.pdu.base import OutletState, PDUOutletTarget
from app.drivers.pdu.simulated import SimulatedPDUDriver

driver = SimulatedPDUDriver()


def target(state: OutletState) -> PDUOutletTarget:
    return PDUOutletTarget(outlet_id="outlet-1", pdu_address=None, outlet_number=3, current_state=state)


@pytest.mark.asyncio
async def test_set_outlet_on_returns_on():
    result = await driver.set_outlet_state(target(OutletState.OFF), OutletState.ON)
    assert result == OutletState.ON


@pytest.mark.asyncio
async def test_set_outlet_off_returns_off():
    result = await driver.set_outlet_state(target(OutletState.ON), OutletState.OFF)
    assert result == OutletState.OFF


@pytest.mark.asyncio
async def test_cycle_outlet_returns_on():
    result = await driver.cycle_outlet(target(OutletState.ON))
    assert result == OutletState.ON
