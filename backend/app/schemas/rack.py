import uuid

from pydantic import BaseModel, ConfigDict, Field


class RackCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    u_height: int = Field(default=42, ge=1)
    pos_x: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    pos_y: float = Field(default=0.0, ge=0, allow_inf_nan=False)


class RackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    data_hall_id: uuid.UUID
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


class RackPosition(BaseModel):
    id: uuid.UUID
    pos_x: float = Field(ge=0, allow_inf_nan=False)
    pos_y: float = Field(ge=0, allow_inf_nan=False)
    previous_x: float = Field(ge=0, allow_inf_nan=False)
    previous_y: float = Field(ge=0, allow_inf_nan=False)


class HallLayoutUpdate(BaseModel):
    racks: list[RackPosition] = Field(max_length=1000)
