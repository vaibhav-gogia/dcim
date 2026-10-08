import uuid

from pydantic import BaseModel, ConfigDict, Field


class DataCenterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")
    location: str | None = Field(default=None, max_length=255)


class DataCenterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location: str | None
