import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class PDUOutlet(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pdu_outlets"
    __table_args__ = (UniqueConstraint("pdu_id", "outlet_number", name="uq_outlet_number_per_pdu"),)

    pdu_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pdus.id", ondelete="CASCADE"), nullable=False
    )
    outlet_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="off", nullable=False)

    pdu: Mapped["PDU"] = relationship(back_populates="outlets")
    power_connection: Mapped["PowerConnection | None"] = relationship(
        back_populates="pdu_outlet", cascade="all, delete-orphan", single_parent=True
    )
