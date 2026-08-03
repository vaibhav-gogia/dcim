import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class System(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "systems"

    rack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("racks.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Lowest U slot occupied, counting from 1 at the bottom of the rack.
    u_position: Mapped[int] = mapped_column(Integer, nullable=False)
    u_height: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    system_type: Mapped[str] = mapped_column(String(32), default="server", nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)

    bmc_driver_type: Mapped[str] = mapped_column(String(32), default="simulated", nullable=False)
    bmc_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    power_state: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    power_state_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rack: Mapped["Rack"] = relationship(back_populates="systems")
    power_connections: Mapped[list["PowerConnection"]] = relationship(
        back_populates="system", cascade="all, delete-orphan"
    )
