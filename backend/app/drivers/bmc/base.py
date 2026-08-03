from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PowerState(str, Enum):
    ON = "on"
    OFF = "off"
    BOOTING = "booting"
    SHUTTING_DOWN = "shutting_down"
    CYCLING = "cycling"
    UNKNOWN = "unknown"


TRANSIENT_STATES = {PowerState.BOOTING, PowerState.SHUTTING_DOWN, PowerState.CYCLING}


@dataclass
class BMCTarget:
    system_id: str
    bmc_address: str | None
    current_power_state: PowerState
    power_state_updated_at: datetime | None


@dataclass
class SensorReading:
    temps_c: dict[str, float]
    fans_rpm: dict[str, int]
    psus: dict[str, str]
    read_at: datetime


class BMCDriver(ABC):
    """Interface for host-level power control and health via a Baseboard Management Controller.

    Implementations are stateless: they take the caller's current view of state and return
    the state that should now be persisted. Callers (the service layer) own persistence, so
    a future real driver (Redfish/IPMI) never has to know about the database.
    """

    @abstractmethod
    async def get_power_state(self, target: BMCTarget) -> PowerState: ...

    @abstractmethod
    async def power_on(self, target: BMCTarget) -> PowerState: ...

    @abstractmethod
    async def power_off(self, target: BMCTarget, graceful: bool = True) -> PowerState: ...

    @abstractmethod
    async def power_cycle(self, target: BMCTarget) -> PowerState: ...

    @abstractmethod
    async def get_sensors(self, target: BMCTarget) -> SensorReading: ...
