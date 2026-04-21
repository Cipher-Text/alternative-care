"""Bangladesh geographic location models (Division → District → Upazila)."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Division(Base):
    """
    Bangladesh administrative divisions (8 total).
    """

    __tablename__ = "divisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)

    # Geospatial (optional)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class District(Base):
    """
    Bangladesh districts (64 total).
    """

    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    division_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)

    # Geospatial (optional)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)


class Upazila(Base):
    """
    Bangladesh upazilas/sub-districts (490+ total).
    """

    __tablename__ = "upazilas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)

    # Geospatial (optional)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
