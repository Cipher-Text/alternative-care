"""Editorial content schemas."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Kind = Literal["article", "video"]
Discipline = Literal["general", "homeopathy", "ayurveda", "unani", "herbal"]
Evidence = Literal["general_info", "traditional_use", "limited_evidence", "studied"]
Status = Literal["draft", "in_review", "published"]

_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YT_URL = re.compile(
    r"^(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})(?:[?&#/].*)?$"
)


def parse_youtube_id(value: str) -> str:
    """Accept a YouTube URL (watch / youtu.be / embed / shorts) or a bare 11-character id."""
    value = value.strip()
    if _YT_ID.match(value):
        return value
    match = _YT_URL.match(value)
    if not match:
        raise ValueError("Not a valid YouTube link or video id")
    return match.group(1)


class ArticleFields(BaseModel):
    kind: Kind = "article"
    discipline: Discipline = "general"
    evidence_label: Evidence = "general_info"
    title_en: str | None = Field(None, max_length=300)
    title_bn: str | None = Field(None, max_length=300)
    summary_en: str | None = Field(None, max_length=1000)
    summary_bn: str | None = Field(None, max_length=1000)
    body_en: str | None = Field(None, max_length=60000)
    body_bn: str | None = Field(None, max_length=60000)
    video_url: str | None = Field(None, description="YouTube link or video id")

    @field_validator("title_en", "title_bn", "summary_en", "summary_bn", "body_en", "body_bn", "video_url")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("video_url")
    @classmethod
    def _valid_video(cls, v: str | None) -> str | None:
        if v is not None:
            parse_youtube_id(v)
        return v


class ArticleCreate(ArticleFields):
    slug: str | None = Field(None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)


class ArticleUpdate(BaseModel):
    kind: Kind | None = None
    discipline: Discipline | None = None
    evidence_label: Evidence | None = None
    title_en: str | None = Field(None, max_length=300)
    title_bn: str | None = Field(None, max_length=300)
    summary_en: str | None = Field(None, max_length=1000)
    summary_bn: str | None = Field(None, max_length=1000)
    body_en: str | None = Field(None, max_length=60000)
    body_bn: str | None = Field(None, max_length=60000)
    video_url: str | None = None
    slug: str | None = Field(None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)

    @field_validator("video_url")
    @classmethod
    def _valid_video(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            parse_youtube_id(v)
        return v


class ArticlePublish(BaseModel):
    reviewer_display: str = Field(..., min_length=2, max_length=255, description="Public credit, e.g. 'Dr. A. Rahman, BHMS'")
    review_due_at: date | None = Field(None, description="When it must be re-reviewed; defaults to a year out")


class ArticleReturn(BaseModel):
    review_note: str = Field(..., min_length=3, max_length=2000)


class ArticleResponse(BaseModel):
    """Full article for the authoring screens."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    kind: str
    discipline: str
    evidence_label: str
    status: str
    title_en: str | None
    title_bn: str | None
    summary_en: str | None
    summary_bn: str | None
    body_en: str | None
    body_bn: str | None
    youtube_id: str | None
    author_id: str
    author_name: str
    reviewer_display: str | None
    reviewed_at: datetime | None
    review_note: str | None
    review_due_at: date | None
    review_overdue: bool = False
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime | None


class ArticleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    kind: str
    discipline: str
    status: str
    title_en: str | None
    title_bn: str | None
    author_name: str
    review_overdue: bool = False
    updated_at: datetime | None
    created_at: datetime


class PublicArticleItem(BaseModel):
    """List card on the public site: no body."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    kind: str
    discipline: str
    evidence_label: str
    title_en: str | None
    title_bn: str | None
    summary_en: str | None
    summary_bn: str | None
    youtube_id: str | None
    author_name: str
    published_at: datetime | None


class PublicArticle(PublicArticleItem):
    body_en: str | None
    body_bn: str | None
    reviewer_display: str | None
    reviewed_at: datetime | None
    review_due_at: date | None
