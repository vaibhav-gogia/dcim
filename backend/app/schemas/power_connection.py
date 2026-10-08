import uuid

from pydantic import BaseModel, ConfigDict, Field


class PowerConnectionCreate(BaseModel):
    pdu_outlet_id: uuid.UUID
    psu_label: str = Field(min_length=1, max_length=32, pattern=r"\S")


class PowerConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    system_id: uuid.UUID
    pdu_outlet_id: uuid.UUID
    psu_label: str | None
