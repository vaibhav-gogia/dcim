import uuid

from pydantic import BaseModel, ConfigDict


class DataCenterCreate(BaseModel):
    name: str
    location: str | None = None


class DataCenterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None
