import uuid

from pydantic import BaseModel, ConfigDict


class RackCreate(BaseModel):
    name: str
    u_height: int = 42
    pos_x: float = 0.0
    pos_y: float = 0.0


class RackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    datacenter_id: uuid.UUID
    name: str
    u_height: int
    pos_x: float
    pos_y: float


class FloorRackRead(BaseModel):
    """Slim rack shape for the DC floor view — coordinates only, no live state."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    u_height: int
    pos_x: float
    pos_y: float


class DataCenterFloorRead(BaseModel):
    id: uuid.UUID
    name: str
    racks: list[FloorRackRead]
