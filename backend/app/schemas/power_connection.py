import uuid

from pydantic import BaseModel, ConfigDict


class PowerConnectionCreate(BaseModel):
    pdu_outlet_id: uuid.UUID
    psu_label: str | None = None


class PowerConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    system_id: uuid.UUID
    pdu_outlet_id: uuid.UUID
    psu_label: str | None
