from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class DataCenter(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "datacenters"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    racks: Mapped[list["Rack"]] = relationship(back_populates="datacenter", cascade="all, delete-orphan")
