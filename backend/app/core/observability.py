"""Logging, error tracking, and request-ID wiring.

Both structlog and sentry-sdk have been declared dependencies since before
this module existed, but nothing ever called structlog.configure() or
sentry_sdk.init() — structlog loggers fell back to unstructured stdlib
logging, and errors were never reported anywhere. See docs/planning/revision-2026-09.md T8.
"""

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog
from fastapi import Request

from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(logger, method_name, event_dict):
    """structlog processor: stamp every log line with the current request ID."""
    request_id = request_id_ctx.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging() -> None:
    """Configure structlog + stdlib logging. Call once at process startup."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # JSON in production (machine-parseable for log aggregation), a readable
    # console renderer everywhere else.
    renderer = (
        structlog.processors.JSONRenderer()
        if settings.ENVIRONMENT == "production"
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def init_sentry() -> None:
    """Initialise Sentry error tracking, if a DSN is configured."""
    if not settings.SENTRY_DSN:
        return

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
    )


async def request_id_middleware(request: Request, call_next):
    """Assign a request ID, bind it to structlog context, echo it back."""
    incoming = request.headers.get("X-Request-ID")
    request_id = incoming or str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response
