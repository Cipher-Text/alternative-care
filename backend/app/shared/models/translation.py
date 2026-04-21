"""Translation model for bilingual support (EN/BN)."""

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Translation(Base):
    """
    Translation key-value pairs for UI strings.
    Platform-level, no tenant_id.
    """

    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Translation key (e.g., "dashboard.welcome")
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Translations
    text_en: Mapped[str] = mapped_column(Text, nullable=False)
    text_bn: Mapped[str] = mapped_column(Text, nullable=False)

    # Category (for organization)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # e.g., "dashboard", "patient", "prescription"

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
