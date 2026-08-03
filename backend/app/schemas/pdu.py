import uuid

from pydantic import BaseModel, ConfigDict


class PDUCreate(BaseModel):
    name: str
    outlet_count: int = 24
    driver_type: str = "simulated"
    address: str | None = None


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
