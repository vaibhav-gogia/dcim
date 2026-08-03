import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class PDU(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pdus"

    rack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("racks.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    outlet_count: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    driver_type: Mapped[str] = mapped_column(String(32), default="simulated", nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rack: Mapped["Rack"] = relationship(back_populates="pdus")
    outlets: Mapped[list["PDUOutlet"]] = relationship(back_populates="pdu", cascade="all, delete-orphan")
