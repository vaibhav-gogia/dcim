from app.drivers.bmc.base import BMCDriver
from app.drivers.bmc.simulated import SimulatedBMCDriver
from app.drivers.pdu.base import PDUDriver
from app.drivers.pdu.simulated import SimulatedPDUDriver

BMC_DRIVERS: dict[str, BMCDriver] = {
    "simulated": SimulatedBMCDriver(),
}

PDU_DRIVERS: dict[str, PDUDriver] = {
    "simulated": SimulatedPDUDriver(),
}


def get_bmc_driver(driver_type: str) -> BMCDriver:
    try:
        return BMC_DRIVERS[driver_type]
    except KeyError:
        raise ValueError(f"Unknown BMC driver type: {driver_type!r}") from None


def get_pdu_driver(driver_type: str) -> PDUDriver:
    try:
        return PDU_DRIVERS[driver_type]
    except KeyError:
        raise ValueError(f"Unknown PDU driver type: {driver_type!r}") from None
