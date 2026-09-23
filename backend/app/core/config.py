"""Application configuration using Pydantic Settings."""

import logging
import sys
from functools import lru_cache
from typing import Any

from pydantic import PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "altcare"
    MINIO_USE_SSL: bool = False

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption (Fernet)
    INTEGRATION_ENCRYPTION_KEY: str

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """
        SECURITY: Validate required security settings at startup.

        Fails fast if critical secrets are missing or weak.
        """
        errors = []

        # Validate SECRET_KEY
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            errors.append(
                "SECRET_KEY must be set and at least 32 characters long. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # Validate INTEGRATION_ENCRYPTION_KEY (Fernet requires 32 url-safe base64-encoded bytes)
        if not self.INTEGRATION_ENCRYPTION_KEY or len(self.INTEGRATION_ENCRYPTION_KEY) < 32:
            errors.append(
                "INTEGRATION_ENCRYPTION_KEY must be set and at least 32 characters long. "
                "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        # Validate DATABASE_URL
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL must be set")

        # Warn about default MinIO credentials in production
        if self.ENVIRONMENT == "production":
            if self.MINIO_ACCESS_KEY == "minioadmin" or self.MINIO_SECRET_KEY == "minioadmin":
                errors.append(
                    "SECURITY WARNING: Using default MinIO credentials in production! "
                    "Change MINIO_ACCESS_KEY and MINIO_SECRET_KEY immediately."
                )

            # Warn about weak rate limits in production
            if self.RATE_LIMIT_LOGIN_PER_MINUTE > 10:
                logger.warning(
                    f"RATE_LIMIT_LOGIN_PER_MINUTE={self.RATE_LIMIT_LOGIN_PER_MINUTE} "
                    "is high for production (recommended: 5-10)"
                )

        if errors:
            error_msg = "\n❌ SECURITY CONFIGURATION ERRORS:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            raise ValueError("Critical security configuration missing. See errors above.")

        return self

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Platform system email (password reset, email verification) — sent via
    # SMTP relay, not each provider's HTTP API, so no extra SDK dependency
    # is needed (see app/core/system_email.py). Set EMAIL_PROVIDER to pick
    # which one is active; only that provider's credentials need to be set.
    # Empty EMAIL_PROVIDER means "no email provider configured" — emails
    # are skipped with a logged warning instead of failing the request.
    EMAIL_PROVIDER: str = ""  # "sendgrid" | "resend" | "mailgun" | "smtp2go" | "smtp"
    EMAIL_FROM_ADDRESS: str = "noreply@altcare.health"

    SENDGRID_API_KEY: str = ""

    RESEND_API_KEY: str = ""

    # Mailgun SMTP credentials are per-domain, generated in the Mailgun
    # dashboard — not the general Mailgun API key. Host differs by region:
    # smtp.mailgun.org (US, default) or smtp.eu.mailgun.org (EU domains).
    MAILGUN_SMTP_USERNAME: str = ""
    MAILGUN_SMTP_PASSWORD: str = ""
    MAILGUN_SMTP_HOST: str = "smtp.mailgun.org"

    # SMTP2GO credentials come from Sending > SMTP Users in their dashboard.
    SMTP2GO_USERNAME: str = ""
    SMTP2GO_PASSWORD: str = ""

    # Generic fallback for any provider not named above (EMAIL_PROVIDER=smtp).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    # Frontend base URL — used to build links in platform emails (password
    # reset, email verification). Not the same as CORS_ORIGINS: that's a list.
    FRONTEND_URL: str = "http://localhost:3000"

    # Google Sign-In — verifies ID tokens minted by Google Identity Services
    # on the frontend (see app/core/security.py:verify_google_id_token).
    # This is the OAuth Client ID (Web application type), not a secret — it
    # is also sent to the frontend to initialize the Google button.
    GOOGLE_CLIENT_ID: str = ""

    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Payment (SSLCommerz)
    SSLCOMMERZ_STORE_ID: str = ""
    SSLCOMMERZ_STORE_PASSWORD: str = ""
    SSLCOMMERZ_IS_SANDBOX: bool = True

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # bKash Payment Gateway
    BKASH_APP_KEY: str = ""
    BKASH_APP_SECRET: str = ""
    BKASH_USERNAME: str = ""
    BKASH_PASSWORD: str = ""
    BKASH_BASE_URL: str = "https://tokenized.sandbox.bka.sh/v1.2.0-beta"
    BKASH_IS_SANDBOX: bool = True

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Sentry
    SENTRY_DSN: str = ""

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_KEY_PREFIX: str = "altcare"
    RATE_LIMIT_AI_PER_HOUR: int = 20
    RATE_LIMIT_AI_WINDOW_SECONDS: int = 3600

    # Security headers
    SECURITY_HEADERS_ENABLED: bool = True
    SECURITY_CSP_POLICY: str = (
        # SECURITY: Balanced CSP policy - strict but functional
        # Allows Next.js, API calls, and necessary resources
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Next.js needs eval for HMR in dev
        "style-src 'self' 'unsafe-inline'; "  # Tailwind inline styles
        "img-src 'self' data: blob:; "  # Images, data URLs, blobs
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:* ws://localhost:*; "  # API + WebSocket for dev
        "frame-ancestors 'none'; "  # Prevent clickjacking
        "base-uri 'self'; "
        "form-action 'self'"
    )
    SECURITY_HSTS_ENABLED: bool = True
    SECURITY_HSTS_MAX_AGE: int = 31536000
    SECURITY_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURITY_HSTS_PRELOAD: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore


settings = get_settings()
