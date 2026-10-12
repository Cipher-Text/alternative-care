"""File storage on any S3-compatible service: Cloudflare R2 in production, MinIO in development.

Two kinds of object, kept apart by key prefix:

- ``public/...``  non-sensitive images (clinic logos). Served straight from ``STORAGE_PUBLIC_BASE_URL``
  (R2: the bucket's public custom domain). Never put patient or clinical data here.
- ``private/...`` everything else. Never public; read through a short-lived signed URL.

Callers use the ``Storage`` interface through ``get_storage()`` so tests can swap in ``MemoryStorage``.
boto3 is synchronous, so every call runs in a worker thread and cannot block the event loop.
"""

import asyncio
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

import structlog
from fastapi import HTTPException, status

from app.core.config import settings

logger = structlog.get_logger()

PUBLIC_PREFIX = "public/"
PRIVATE_PREFIX = "private/"
# One year, immutable: public object keys contain a content hash, so a changed file is a new URL.
PUBLIC_CACHE_CONTROL = "public, max-age=31536000, immutable"


class Storage(Protocol):
    async def put_public(self, key: str, data: bytes, content_type: str) -> str:
        """Store under ``public/`` and return its public URL."""

    async def put_private(self, key: str, data: bytes, content_type: str) -> None:
        """Store under ``private/`` (never public)."""

    async def signed_url(self, key: str, expires_seconds: int = 300) -> str:
        """A time-limited URL for reading a private object."""

    async def delete(self, key: str) -> None:
        """Remove an object. Missing objects are fine."""


def public_url(key: str) -> str:
    return f"{settings.STORAGE_PUBLIC_BASE_URL.rstrip('/')}/{key}"


def key_from_public_url(url: str | None) -> str | None:
    """The object key behind a URL this app issued, or None for anything else (an old or foreign URL)."""
    if not url:
        return None
    base = settings.STORAGE_PUBLIC_BASE_URL.rstrip("/")
    if not url.startswith(base + "/"):
        return None
    key = urlparse(url).path.removeprefix(urlparse(base).path.rstrip("/")).lstrip("/")
    return key if key.startswith(PUBLIC_PREFIX) else None


def _check_key(key: str, prefix: str) -> None:
    if not key.startswith(prefix) or ".." in key or key.startswith("/"):
        raise ValueError(f"storage key must start with {prefix!r} and stay inside it: {key!r}")


class S3Storage:
    """boto3 client with path-style addressing, which both R2 and MinIO accept."""

    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        self.bucket = settings.STORAGE_BUCKET
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.STORAGE_ENDPOINT_URL,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=settings.STORAGE_SECRET_ACCESS_KEY,
            region_name=settings.STORAGE_REGION,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 2, "mode": "standard"},
                connect_timeout=5,
                read_timeout=20,
            ),
        )

    async def _run(self, fn, **kwargs):
        try:
            return await asyncio.to_thread(fn, **kwargs)
        except Exception as exc:  # noqa: BLE001 — botocore raises many types; callers only need "unavailable"
            logger.warning("storage_error", op=getattr(fn, "__name__", "call"), error=type(exc).__name__)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "File storage is not available right now.") from exc

    async def put_public(self, key: str, data: bytes, content_type: str) -> str:
        _check_key(key, PUBLIC_PREFIX)
        await self._run(
            self.client.put_object,
            Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, CacheControl=PUBLIC_CACHE_CONTROL,
        )
        return public_url(key)

    async def put_private(self, key: str, data: bytes, content_type: str) -> None:
        _check_key(key, PRIVATE_PREFIX)
        await self._run(self.client.put_object, Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    async def signed_url(self, key: str, expires_seconds: int = 300) -> str:
        _check_key(key, PRIVATE_PREFIX)
        # Signing is local arithmetic (no network call)
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_seconds
        )

    async def delete(self, key: str) -> None:
        await self._run(self.client.delete_object, Bucket=self.bucket, Key=key)


@dataclass
class StoredObject:
    data: bytes
    content_type: str


class MemoryStorage:
    """In-process stand-in for tests: same behaviour, no network."""

    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}

    async def put_public(self, key: str, data: bytes, content_type: str) -> str:
        _check_key(key, PUBLIC_PREFIX)
        self.objects[key] = StoredObject(data, content_type)
        return public_url(key)

    async def put_private(self, key: str, data: bytes, content_type: str) -> None:
        _check_key(key, PRIVATE_PREFIX)
        self.objects[key] = StoredObject(data, content_type)

    async def signed_url(self, key: str, expires_seconds: int = 300) -> str:
        _check_key(key, PRIVATE_PREFIX)
        return f"https://storage.test/{key}?expires={expires_seconds}"

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)


_storage: Storage | None = None


def get_storage() -> Storage:
    """FastAPI dependency (also callable directly). One client per process."""
    global _storage
    if _storage is None:
        _storage = S3Storage()
    return _storage
