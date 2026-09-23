"""Unit tests for platform system email provider selection."""

from unittest import mock

import pytest

from app.core import system_email
from app.core.config import settings
from app.modules.integration.providers.smtp_service import SMTPService


def _clear_all_provider_settings(monkeypatch):
    """Start from a clean slate so one test's settings can't leak into another."""
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "")
    monkeypatch.setattr(settings, "EMAIL_FROM_ADDRESS", "noreply@altcare.health")
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_USERNAME", "")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_HOST", "smtp.mailgun.org")
    monkeypatch.setattr(settings, "SMTP2GO_USERNAME", "")
    monkeypatch.setattr(settings, "SMTP2GO_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)


@pytest.fixture(autouse=True)
def clean_email_settings(monkeypatch):
    _clear_all_provider_settings(monkeypatch)


def test_no_provider_configured_returns_none():
    assert system_email._platform_smtp_service() is None


def test_unknown_provider_returns_none_and_warns(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "not-a-real-provider")
    assert system_email._platform_smtp_service() is None


@pytest.mark.parametrize(
    "provider,configure,expected_host,expected_port,expected_username",
    [
        (
            "sendgrid",
            lambda mp: mp.setattr(settings, "SENDGRID_API_KEY", "SG.abc123"),
            "smtp.sendgrid.net",
            587,
            "apikey",
        ),
        (
            "resend",
            lambda mp: mp.setattr(settings, "RESEND_API_KEY", "re_abc123"),
            "smtp.resend.com",
            587,
            "resend",
        ),
        (
            "smtp2go",
            lambda mp: (
                mp.setattr(settings, "SMTP2GO_USERNAME", "s2g-user"),
                mp.setattr(settings, "SMTP2GO_PASSWORD", "s2g-pass"),
            ),
            "mail.smtp2go.com",
            587,
            "s2g-user",
        ),
    ],
)
def test_provider_builds_expected_smtp_service(
    monkeypatch, provider, configure, expected_host, expected_port, expected_username
):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", provider)
    configure(monkeypatch)

    service = system_email._platform_smtp_service()

    assert isinstance(service, SMTPService)
    assert service.host == expected_host
    assert service.port == expected_port
    assert service.username == expected_username
    assert service.use_tls is True
    assert service.from_email == "noreply@altcare.health"


def test_mailgun_uses_configured_host_for_eu_region(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "mailgun")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_USERNAME", "postmaster@mg.example.com")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_PASSWORD", "mg-pass")
    monkeypatch.setattr(settings, "MAILGUN_SMTP_HOST", "smtp.eu.mailgun.org")

    service = system_email._platform_smtp_service()

    assert service.host == "smtp.eu.mailgun.org"
    assert service.username == "postmaster@mg.example.com"


def test_generic_smtp_respects_use_tls_false(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.internal.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 25)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "relay-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "relay-pass")
    monkeypatch.setattr(settings, "SMTP_USE_TLS", False)

    service = system_email._platform_smtp_service()

    assert service.host == "smtp.internal.example.com"
    assert service.port == 25
    assert service.use_tls is False


@pytest.mark.parametrize(
    "provider,partial_configure",
    [
        ("sendgrid", lambda mp: None),  # SENDGRID_API_KEY left blank
        ("mailgun", lambda mp: mp.setattr(settings, "MAILGUN_SMTP_USERNAME", "user-only")),
        ("smtp2go", lambda mp: mp.setattr(settings, "SMTP2GO_USERNAME", "user-only")),
        ("smtp", lambda mp: mp.setattr(settings, "SMTP_HOST", "host-only")),
    ],
)
def test_provider_with_incomplete_credentials_returns_none(monkeypatch, provider, partial_configure):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", provider)
    partial_configure(monkeypatch)

    assert system_email._platform_smtp_service() is None


def test_send_system_email_task_skips_when_unconfigured():
    result = system_email.send_system_email_task.run(
        recipient="doctor@example.com",
        subject="Test",
        body_text="Test body",
    )
    assert result == {"success": False, "skipped": True}


def test_send_system_email_task_uses_active_provider(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_abc123")

    with mock.patch.object(
        SMTPService,
        "send_email",
        new_callable=mock.AsyncMock,
        return_value={"success": True, "message": "sent"},
    ) as mocked_send:
        result = system_email.send_system_email_task.run(
            recipient="doctor@example.com",
            subject="Verify your email",
            body_html="<p>hi</p>",
            body_text="hi",
        )

    assert result == {"success": True, "message": "sent"}
    mocked_send.assert_called_once_with(
        recipient="doctor@example.com",
        subject="Verify your email",
        body_html="<p>hi</p>",
        body_text="hi",
    )
