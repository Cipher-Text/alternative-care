"""Editorial content (articles and curated videos) — Phase 1 of the public-site strategy."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseAuditModel

ARTICLE_STATUSES = ("draft", "in_review", "published")
ARTICLE_KINDS = ("article", "video")
ARTICLE_DISCIPLINES = ("general", "homeopathy", "ayurveda", "unani", "herbal")
EVIDENCE_LABELS = ("general_info", "traditional_use", "limited_evidence", "studied")


class Article(BaseAuditModel):
    """
    A piece of public editorial content. Not tenant-scoped: it is platform content written by
    doctors or staff, published only after a platform admin has reviewed it.

    Workflow: draft -> in_review -> published (an admin can return it to draft with a note).
    Bilingual: at least one of the two languages must be filled; the public site falls back to
    the other when the reader's language is missing.
    """

    __tablename__ = "articles"
    __table_args__ = (
        CheckConstraint("status IN ('draft','in_review','published')", name="ck_articles_status"),
        CheckConstraint("kind IN ('article','video')", name="ck_articles_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)

    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="article")
    discipline: Mapped[str] = mapped_column(String(20), nullable=False, default="general", index=True)
    # general_info | traditional_use | limited_evidence | studied
    evidence_label: Mapped[str] = mapped_column(String(20), nullable=False, default="general_info")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    title_en: Mapped[str | None] = mapped_column(String(300), nullable=True)
    title_bn: Mapped[str | None] = mapped_column(String(300), nullable=True)
    summary_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_bn: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Markdown. Rendered without raw HTML.
    body_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # YouTube video id (kind='video', or an article with an embedded video)
    youtube_id: Mapped[str | None] = mapped_column(String(20), nullable=True)

    author_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Review sign-off: who, how they should be credited publicly, and when
    reviewer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewer_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_due_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
