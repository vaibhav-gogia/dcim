import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SystemCreate(BaseModel):
    name: str
    u_position: int
    u_height: int = 1
    system_type: str = "server"
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    bmc_driver_type: str = "simulated"
    bmc_address: str | None = None


class SystemUpdate(BaseModel):
    name: str | None = None
    u_position: int | None = None
    u_height: int | None = None
    system_type: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None


class SystemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rack_id: uuid.UUID
    name: str
    u_position: int
    u_height: int
    system_type: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    bmc_driver_type: str
    power_state: str
    power_state_updated_at: datetime | None


class SystemElevationRead(BaseModel):
    """Slim system shape embedded in a rack elevation response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    u_position: int
    u_height: int
    system_type: str
    power_state: str


class RackElevationRead(BaseModel):
    id: uuid.UUID
    name: str
    u_height: int
    systems: list[SystemElevationRead]


class SensorReadingRead(BaseModel):
    temps_c: dict[str, float]
    fans_rpm: dict[str, int]
    psus: dict[str, str]
    read_at: datetime


class SystemHealthRead(BaseModel):
    power_state: str
    temps_c: dict[str, float]
    fans_rpm: dict[str, int]
    psus: dict[str, str]
    read_at: datetime


class PowerActionResponse(BaseModel):
    power_state: str
