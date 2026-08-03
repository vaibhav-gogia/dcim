import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Rack(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "racks"
    __table_args__ = (UniqueConstraint("datacenter_id", "name", name="uq_rack_name_per_dc"),)

    datacenter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("datacenters.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    u_height: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    pos_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pos_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    datacenter: Mapped["DataCenter"] = relationship(back_populates="racks")
    systems: Mapped[list["System"]] = relationship(back_populates="rack", cascade="all, delete-orphan")
    pdus: Mapped[list["PDU"]] = relationship(back_populates="rack", cascade="all, delete-orphan")
