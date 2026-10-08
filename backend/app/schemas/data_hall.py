import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.rack import FloorRackRead


class DataHallCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")


class DataHallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    datacenter_id: uuid.UUID
    name: str


class DataHallFloorRead(DataHallRead):
    datacenter_name: str
    racks: list[FloorRackRead]
