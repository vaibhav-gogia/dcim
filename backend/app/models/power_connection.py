import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class PowerConnection(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "power_connections"

    system_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("systems.id", ondelete="CASCADE"), nullable=False
    )
    pdu_outlet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pdu_outlets.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    psu_label: Mapped[str | None] = mapped_column(String(32), nullable=True)

    system: Mapped["System"] = relationship(back_populates="power_connections")
    pdu_outlet: Mapped["PDUOutlet"] = relationship(back_populates="power_connection")
