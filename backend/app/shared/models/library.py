"""Book library and reading progress models."""

from sqlalchemy import Boolean, Float, Integer, String, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.shared.models.base import TenantScopedModel


class Book(TenantScopedModel):
    """Medical books - classical texts for alternative medicine."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Book metadata (bilingual)
    title_en: Mapped[str] = mapped_column(String(500), nullable=False)
    title_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    author: Mapped[str] = mapped_column(String(255), nullable=False)

    # Medical system
    system: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # homeopathy, ayurveda, unani, herbal

    # Description (bilingual)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_bn: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Publication info
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Language
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    # File storage
    epub_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Parsing status
    is_parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_chapters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_sections: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Global vs tenant-specific
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    chapters: Mapped[list["Chapter"]] = relationship(
        "Chapter",
        back_populates="book",
        cascade="all, delete-orphan",
    )


class Chapter(TenantScopedModel):
    """Book chapters."""

    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chapter info (bilingual)
    title_en: Mapped[str] = mapped_column(String(500), nullable=False)
    title_bn: Mapped[str | None] = mapped_column(String(500), nullable=True)

    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Hierarchy (for nested chapters)
    parent_chapter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Content stats
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    book: Mapped["Book"] = relationship("Book", back_populates="chapters")
    sections: Mapped[list["Section"]] = relationship(
        "Section",
        back_populates="chapter",
        cascade="all, delete-orphan",
    )


class Section(TenantScopedModel):
    """Book sections (parsed content chunks for reader and AI)."""

    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Section info
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content (cleaned text)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Stats
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="sections")
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding",
        back_populates="section",
        cascade="all, delete-orphan",
    )


class Embedding(TenantScopedModel):
    """
    Vector embeddings for RAG (Retrieval Augmented Generation).
    Stored in PostgreSQL via pgvector extension.
    """

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)

    # Chunk text (for context in RAG)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Chunk metadata
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Position within section (for overlapping chunks)

    # Relationships
    section: Mapped["Section"] = relationship("Section", back_populates="embeddings")


class ReadingProgress(TenantScopedModel):
    """User reading progress per book."""

    __tablename__ = "reading_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Progress
    current_chapter_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_section_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Percentage (0-100)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Last read position (scroll offset)
    last_scroll_position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Bookmark(TenantScopedModel):
    """User bookmarks within books."""

    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chapter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    section_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Bookmark note
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Highlight(TenantScopedModel):
    """User highlights within books."""

    __tablename__ = "highlights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    section_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Highlighted text
    highlighted_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Position within section
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)

    # Color
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="yellow")

    # Note
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
