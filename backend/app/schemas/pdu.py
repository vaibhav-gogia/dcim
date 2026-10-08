import uuid

from pydantic import BaseModel, ConfigDict, Field


class PDUCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    outlet_count: int = Field(default=24, ge=1, le=96)
    driver_type: str = Field(default="simulated", pattern="^simulated$")
    address: str | None = Field(default=None, max_length=255)


class PDUUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    address: str | None = Field(default=None, max_length=255)


class PDURead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rack_id: uuid.UUID
    name: str
    outlet_count: int
    driver_type: str
    address: str | None


class PDUOutletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    outlet_number: int
    state: str
    connected_system_id: uuid.UUID | None = None
    connected_system_name: str | None = None


class PDUWithOutletsRead(BaseModel):
    id: uuid.UUID
    name: str
    outlet_count: int
    driver_type: str
    outlets: list[PDUOutletRead]


class OutletActionResponse(BaseModel):
    state: str
