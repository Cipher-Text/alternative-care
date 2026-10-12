"""Schemas for the Facebook profile promotion benefit."""

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

FbStatus = Literal["requested", "drafted", "approved", "posted", "rejected", "cancelled"]

_FACEBOOK_HOSTS = {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com", "fb.com", "www.fb.com", "fb.watch"}


class FacebookRequestCreate(BaseModel):
    doctor_note: str | None = Field(None, max_length=1000, description="What to highlight, or preferred timing")


class FacebookChangesRequest(BaseModel):
    comment: str = Field(..., min_length=3, max_length=1000)


class FacebookApprove(BaseModel):
    comment: str | None = Field(None, max_length=1000)


class FacebookRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: FbStatus
    doctor_note: str | None
    draft_text: str | None
    doctor_comment: str | None
    approved_text: str | None
    reject_reason: str | None
    post_url: str | None
    created_at: datetime
    drafted_at: datetime | None
    approved_at: datetime | None
    posted_at: datetime | None


class FacebookSummary(BaseModel):
    """Everything the doctor's page needs: the plan benefit, the quarter's usage, and why a new
    request is or is not possible right now."""

    in_plan: bool
    limit: int | None  # per quarter; None = unlimited
    used: int
    remaining: int | None
    period_start: datetime
    period_end: datetime
    # Machine-readable reasons: not_in_plan, no_public_profile, quota_used, open_request
    blockers: list[str]
    can_request: bool
    profile_path: str | None  # e.g. /practitioners/dr-x when the profile is public
    open_request: FacebookRequestResponse | None
    history: list[FacebookRequestResponse]


class FacebookDraft(BaseModel):
    draft_text: str = Field(..., min_length=20, max_length=3000)


class FacebookReject(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class FacebookPosted(BaseModel):
    post_url: str = Field(..., max_length=500)

    @field_validator("post_url")
    @classmethod
    def _facebook_link(cls, v: str) -> str:
        parsed = urlparse(v.strip())
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in _FACEBOOK_HOSTS:
            raise ValueError("Enter the https link of the Facebook post")
        return v.strip()


class AdminFacebookRequest(FacebookRequestResponse):
    tenant_id: str
    tenant_name: str
    requester_name: str
    # Public profile link (path) if the profile is public right now, so staff can write the post from it
    profile_path: str | None
