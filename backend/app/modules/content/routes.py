"""Editorial content authoring API: doctors and admins write, admins review and publish."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, require_role
from app.modules.content.service import ContentService, to_response
from app.shared.schemas import (
    ArticleCreate,
    ArticleListItem,
    ArticlePublish,
    ArticleResponse,
    ArticleReturn,
    ArticleUpdate,
)

router = APIRouter()

# Receptionists and platform operators do not write public content
Author = Annotated[CurrentUser, Depends(require_role("doctor", "admin"))]


def get_service(db: Annotated[AsyncSession, Depends(get_db)], user: Author) -> ContentService:
    return ContentService(db, user_id=user.user_id, role=user.role)


Service = Annotated[ContentService, Depends(get_service)]


@router.get("", response_model=list[ArticleListItem])
async def list_articles(
    service: Service,
    status_filter: str | None = Query(None, alias="status", pattern="^(draft|in_review|published)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Admins see every article; doctors see only their own."""
    from app.modules.content.service import _overdue

    items = await service.list_items(status_filter, limit, offset)
    out = []
    for a in items:
        item = ArticleListItem.model_validate(a)
        item.review_overdue = _overdue(a)
        out.append(item)
    return out


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(data: ArticleCreate, service: Service):
    return to_response(await service.create(data))


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, service: Service):
    return to_response(await service.get(article_id))


@router.patch("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, data: ArticleUpdate, service: Service):
    return to_response(await service.update(article_id, data))


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(article_id: str, service: Service):
    await service.delete(article_id)


@router.post("/{article_id}/submit", response_model=ArticleResponse)
async def submit_article(article_id: str, service: Service):
    """Send a complete draft for review."""
    return to_response(await service.submit(article_id))


@router.post("/{article_id}/publish", response_model=ArticleResponse)
async def publish_article(article_id: str, data: ArticlePublish, service: Service):
    """Admin only: record the reviewer's public credit and publish."""
    return to_response(await service.publish(article_id, data))


@router.post("/{article_id}/return", response_model=ArticleResponse)
async def return_article(article_id: str, data: ArticleReturn, service: Service):
    """Admin only: send back to the author with a note."""
    return to_response(await service.return_to_author(article_id, data.review_note))


@router.post("/{article_id}/unpublish", response_model=ArticleResponse)
async def unpublish_article(article_id: str, service: Service):
    """Admin only: take a published article down (it returns to draft)."""
    return to_response(await service.unpublish(article_id))
