from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class OutletState(str, Enum):
    ON = "on"
    OFF = "off"


@dataclass
class PDUOutletTarget:
    outlet_id: str
    pdu_address: str | None
    outlet_number: int
    current_state: OutletState


class PDUDriver(ABC):
    """Interface for direct outlet-level power control on a PDU.

    Unlike BMC power actions, relay switching is effectively instantaneous in real
    hardware, so implementations return the terminal state directly rather than a
    transient one the caller must poll to resolve.
    """

    @abstractmethod
    async def get_outlet_state(self, target: PDUOutletTarget) -> OutletState: ...

    @abstractmethod
    async def set_outlet_state(self, target: PDUOutletTarget, state: OutletState) -> OutletState: ...

    @abstractmethod
    async def cycle_outlet(self, target: PDUOutletTarget) -> OutletState: ...
