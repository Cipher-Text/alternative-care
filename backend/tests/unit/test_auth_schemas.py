"""Unit tests for authentication schema validation."""

import pytest
from pydantic import ValidationError

from app.modules.auth.schemas import (
    ChangePasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
)


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "alllowercase123",
        "ALLUPPERCASE123",
        "NoNumbersHere",
        "12345678",
    ],
)
def test_register_request_rejects_weak_passwords(password: str) -> None:
    """Register schema must enforce uppercase, lowercase, and numeric chars."""
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="doctor@test.com",
            password=password,
            full_name="Dr. Schema",
            specializations=["homeopathy"],
        )


def test_register_request_accepts_strong_password() -> None:
    """Register schema accepts valid complex passwords."""
    payload = RegisterRequest(
        email="doctor@test.com",
        password="ValidPass123",
        full_name="Dr. Schema",
        specializations=["homeopathy"],
    )
    assert payload.password == "ValidPass123"


@pytest.mark.parametrize("schema_cls", [ResetPasswordRequest, ChangePasswordRequest])
def test_password_change_reset_reject_weak_passwords(schema_cls) -> None:
    """Password reset/change schemas must enforce complexity rules."""
    weak_passwords = [
        "alllowercase123",
        "ALLUPPERCASE123",
        "NoNumbersHere",
        "12345678",
    ]

    for weak in weak_passwords:
        with pytest.raises(ValidationError):
            if schema_cls is ResetPasswordRequest:
                schema_cls(token="reset-token", new_password=weak)
            else:
                schema_cls(current_password="OldPass123", new_password=weak)

