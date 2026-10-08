import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    u_position: int = Field(ge=1)
    u_height: int = Field(default=1, ge=1)
    system_type: str = Field(default="server", min_length=1, max_length=32, pattern=r"\S")
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=120)
    bmc_driver_type: str = "simulated"
    bmc_address: str | None = None


class SystemUpdate(BaseModel):
    name: str = Field(default=None, min_length=1, max_length=120, pattern=r"\S")
    u_position: int = Field(default=None, ge=1)
    u_height: int = Field(default=None, ge=1)
    system_type: str = Field(default=None, min_length=1, max_length=32, pattern=r"\S")
    manufacturer: str | None = Field(default=None, max_length=120)
    model: str | None = Field(default=None, max_length=120)
    serial_number: str | None = Field(default=None, max_length=120)


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
    data_hall_id: uuid.UUID
    data_hall_name: str
    datacenter_id: uuid.UUID
    datacenter_name: str
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
