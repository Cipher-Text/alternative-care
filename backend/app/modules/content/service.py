"""Editorial content workflow: draft -> in_review -> published, with admin sign-off."""

import re
import secrets
from uuid import uuid4
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import Article, User
from app.shared.schemas import ArticleCreate, ArticlePublish, ArticleResponse, ArticleUpdate
from app.shared.schemas.article import parse_youtube_id

DEFAULT_REVIEW_INTERVAL_DAYS = 365


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def _overdue(article: Article) -> bool:
    return bool(
        article.status == "published"
        and article.review_due_at
        and article.review_due_at < date.today()
    )


def to_response(article: Article) -> ArticleResponse:
    data = ArticleResponse.model_validate(article)
    data.review_overdue = _overdue(article)
    return data


class ContentService:
    """Authors are doctors or platform staff; only an admin can review, publish or return."""

    def __init__(self, db: AsyncSession, user_id: str, role: str):
        self.db = db
        self.user_id = user_id
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    # ----- helpers --------------------------------------------------------------------------

    async def _unique_slug(self, base: str) -> str:
        base = _slugify(base) or f"article-{secrets.token_hex(4)}"
        slug, n = base, 1
        while (await self.db.execute(select(Article.id).where(Article.slug == slug))).first():
            n += 1
            slug = f"{base}-{n}"
        return slug

    async def _author_name(self) -> str:
        user = (await self.db.execute(select(User).where(User.id == self.user_id))).scalar_one_or_none()
        return (user.full_name if user else None) or "AltCare"

    async def get(self, article_id: str) -> Article:
        article = (
            await self.db.execute(select(Article).where(Article.id == article_id))
        ).scalar_one_or_none()
        # An author must not learn that someone else's draft exists
        if not article or (not self.is_admin and article.author_id != self.user_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
        return article

    def _require_editable(self, article: Article) -> None:
        if self.is_admin:
            return
        if article.status != "draft":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Only a draft can be edited; ask an admin to return it first",
            )

    @staticmethod
    def _require_complete(article: Article) -> None:
        problems = []
        if not (article.title_en or article.title_bn):
            problems.append("a title")
        if not (article.summary_en or article.summary_bn):
            problems.append("a summary")
        if article.kind == "video" and not article.youtube_id:
            problems.append("a YouTube video")
        if article.kind == "article" and not (article.body_en or article.body_bn):
            problems.append("body text")
        if problems:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Needs " + ", ".join(problems) + " before review"
            )

    # ----- authoring ------------------------------------------------------------------------

    async def list_items(self, status_filter: str | None, limit: int, offset: int) -> list[Article]:
        query = select(Article)
        if not self.is_admin:
            query = query.where(Article.author_id == self.user_id)
        if status_filter:
            query = query.where(Article.status == status_filter)
        query = query.order_by(Article.updated_at.desc().nullslast(), Article.created_at.desc())
        return list((await self.db.execute(query.limit(limit).offset(offset))).scalars())

    async def create(self, data: ArticleCreate) -> Article:
        if not (data.title_en or data.title_bn):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A title in at least one language is required")
        fields = data.model_dump(exclude={"slug", "video_url"})
        article = Article(
            id=str(uuid4()),
            slug=await self._unique_slug(data.slug or data.title_en or ""),
            youtube_id=parse_youtube_id(data.video_url) if data.video_url else None,
            author_id=self.user_id,
            author_name=await self._author_name(),
            status="draft",
            created_by=self.user_id,
            updated_by=self.user_id,
            **fields,
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def update(self, article_id: str, data: ArticleUpdate) -> Article:
        article = await self.get(article_id)
        self._require_editable(article)
        changes = data.model_dump(exclude_unset=True)
        if "video_url" in changes:
            url = changes.pop("video_url")
            article.youtube_id = parse_youtube_id(url) if url and url.strip() else None
        if "slug" in changes:
            new_slug = changes.pop("slug")
            if new_slug and new_slug != article.slug:
                if article.status == "published" and not self.is_admin:
                    raise HTTPException(status.HTTP_409_CONFLICT, "A published address cannot be changed")
                clash = (
                    await self.db.execute(
                        select(Article.id).where(Article.slug == new_slug, Article.id != article.id)
                    )
                ).first()
                if clash:
                    raise HTTPException(status.HTTP_409_CONFLICT, "That address is already used")
                article.slug = new_slug
        for field, value in changes.items():
            if isinstance(value, str):
                value = value.strip() or None
            setattr(article, field, value)
        article.updated_by = self.user_id
        article.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def delete(self, article_id: str) -> None:
        article = await self.get(article_id)
        if article.status == "published":
            raise HTTPException(status.HTTP_409_CONFLICT, "Unpublish it before deleting")
        if not self.is_admin and article.status != "draft":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only a draft can be deleted")
        await self.db.delete(article)
        await self.db.commit()

    # ----- workflow -------------------------------------------------------------------------

    async def submit(self, article_id: str) -> Article:
        article = await self.get(article_id)
        if article.status != "draft":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only a draft can be submitted")
        self._require_complete(article)
        article.status = "in_review"
        article.review_note = None
        article.updated_by = self.user_id
        article.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    def _require_admin(self) -> None:
        if not self.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only an admin can review content")

    async def publish(self, article_id: str, data: ArticlePublish) -> Article:
        self._require_admin()
        article = await self.get(article_id)
        if article.status != "in_review":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only an article in review can be published")
        self._require_complete(article)
        now = datetime.now(timezone.utc)
        article.status = "published"
        article.reviewer_id = self.user_id
        article.reviewer_display = data.reviewer_display.strip()
        article.reviewed_at = now
        article.review_due_at = data.review_due_at or (date.today() + timedelta(days=DEFAULT_REVIEW_INTERVAL_DAYS))
        article.review_note = None
        article.published_at = article.published_at or now
        article.updated_by = self.user_id
        article.updated_at = now
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def return_to_author(self, article_id: str, note: str) -> Article:
        self._require_admin()
        article = await self.get(article_id)
        if article.status != "in_review":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only an article in review can be returned")
        article.status = "draft"
        article.review_note = note.strip()
        article.updated_by = self.user_id
        article.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def unpublish(self, article_id: str) -> Article:
        self._require_admin()
        article = await self.get(article_id)
        if article.status != "published":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only a published article can be unpublished")
        article.status = "draft"
        article.updated_by = self.user_id
        article.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(article)
        return article


class PublicContentService:
    """Read-only view of published content for the public site."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_items(
        self, kind: str | None, discipline: str | None, limit: int, offset: int
    ) -> list[Article]:
        query = select(Article).where(Article.status == "published")
        if kind:
            query = query.where(Article.kind == kind)
        if discipline:
            query = query.where(Article.discipline == discipline)
        query = query.order_by(Article.published_at.desc()).limit(limit).offset(offset)
        return list((await self.db.execute(query)).scalars())

    async def get(self, slug: str) -> Article:
        article = (
            await self.db.execute(
                select(Article).where(Article.slug == slug, Article.status == "published")
            )
        ).scalar_one_or_none()
        if not article:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Article not found")
        return article

    async def slugs(self) -> list[tuple[str, datetime | None]]:
        rows = await self.db.execute(
            select(Article.slug, Article.updated_at).where(Article.status == "published")
        )
        return [(r[0], r[1]) for r in rows]
