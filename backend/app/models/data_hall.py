import uuid
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDPKMixin


class DataHall(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "data_halls"
    __table_args__ = (UniqueConstraint("datacenter_id", "name", name="uq_hall_name_per_dc"),)

    datacenter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("datacenters.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    datacenter: Mapped["DataCenter"] = relationship(back_populates="data_halls")
    racks: Mapped[list["Rack"]] = relationship(back_populates="data_hall", cascade="all, delete-orphan")
