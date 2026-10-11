"""Editorial content: authoring, review workflow, and what the public can see."""

import pytest

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731
ARTICLE = {
    "title_en": "Understanding Fever",
    "summary_en": "A short overview.",
    "body_en": "## Heading\n\nSome **text**.",
    "discipline": "homeopathy",
    "evidence_label": "traditional_use",
}


async def _create(client, token, **over):
    r = await client.post("/api/v1/articles", json={**ARTICLE, **over}, headers=H(token))
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_doctor_creates_draft_with_generated_slug(client, doctor_token):
    a = await _create(client, doctor_token)
    assert a["status"] == "draft"
    assert a["slug"] == "understanding-fever"
    assert a["author_name"]

    # a second article with the same title gets a distinct address
    b = await _create(client, doctor_token)
    assert b["slug"] == "understanding-fever-2"


@pytest.mark.asyncio
async def test_title_required_in_some_language(client, doctor_token):
    r = await client.post("/api/v1/articles", json={"summary_en": "x"}, headers=H(doctor_token))
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_video_link_is_parsed_and_validated(client, doctor_token):
    a = await _create(
        client, doctor_token, kind="video", video_url="https://youtu.be/dQw4w9WgXcQ?t=5"
    )
    assert a["youtube_id"] == "dQw4w9WgXcQ"
    bad = await client.post(
        "/api/v1/articles", json={**ARTICLE, "video_url": "https://example.com/x"}, headers=H(doctor_token)
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_incomplete_draft_cannot_be_submitted(client, doctor_token):
    a = await _create(client, doctor_token, body_en=None)
    r = await client.post(f"/api/v1/articles/{a['id']}/submit", headers=H(doctor_token))
    assert r.status_code == 422
    assert "body" in r.json()["detail"]


@pytest.mark.asyncio
async def test_full_workflow_publishes_and_exposes_publicly(
    client, doctor_token, admin_access_token
):
    a = await _create(client, doctor_token)
    aid = a["id"]

    # not public while a draft or in review
    assert (await client.get(f"/api/v1/public/articles/{a['slug']}")).status_code == 404
    r = await client.post(f"/api/v1/articles/{aid}/submit", headers=H(doctor_token))
    assert r.json()["status"] == "in_review"
    assert (await client.get(f"/api/v1/public/articles/{a['slug']}")).status_code == 404

    # the author cannot publish their own work
    r = await client.post(
        f"/api/v1/articles/{aid}/publish",
        json={"reviewer_display": "Dr. X, BHMS"},
        headers=H(doctor_token),
    )
    assert r.status_code == 403

    r = await client.post(
        f"/api/v1/articles/{aid}/publish",
        json={"reviewer_display": "Dr. X, BHMS"},
        headers=H(admin_access_token),
    )
    assert r.status_code == 200
    published = r.json()
    assert published["status"] == "published"
    assert published["reviewer_display"] == "Dr. X, BHMS"
    assert published["review_due_at"] and published["published_at"]

    pub = await client.get(f"/api/v1/public/articles/{a['slug']}")
    assert pub.status_code == 200
    body = pub.json()
    assert body["reviewer_display"] == "Dr. X, BHMS"
    assert body["evidence_label"] == "traditional_use"
    assert "author_id" not in body and "review_note" not in body

    listed = (await client.get("/api/v1/public/articles")).json()
    assert [i["slug"] for i in listed] == [a["slug"]]
    assert "body_en" not in listed[0]


@pytest.mark.asyncio
async def test_published_article_is_locked_for_its_author(client, doctor_token, admin_access_token):
    a = await _create(client, doctor_token)
    await client.post(f"/api/v1/articles/{a['id']}/submit", headers=H(doctor_token))
    await client.post(
        f"/api/v1/articles/{a['id']}/publish",
        json={"reviewer_display": "Dr. X"},
        headers=H(admin_access_token),
    )
    r = await client.patch(
        f"/api/v1/articles/{a['id']}", json={"title_en": "Changed"}, headers=H(doctor_token)
    )
    assert r.status_code == 409
    r = await client.delete(f"/api/v1/articles/{a['id']}", headers=H(doctor_token))
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_admin_can_return_with_note_and_unpublish(client, doctor_token, admin_access_token):
    a = await _create(client, doctor_token)
    await client.post(f"/api/v1/articles/{a['id']}/submit", headers=H(doctor_token))

    r = await client.post(
        f"/api/v1/articles/{a['id']}/return", json={"review_note": "Remove the dosing"}, headers=H(admin_access_token)
    )
    assert r.json()["status"] == "draft"
    assert r.json()["review_note"] == "Remove the dosing"

    await client.post(f"/api/v1/articles/{a['id']}/submit", headers=H(doctor_token))
    await client.post(
        f"/api/v1/articles/{a['id']}/publish",
        json={"reviewer_display": "Dr. X"},
        headers=H(admin_access_token),
    )
    r = await client.post(f"/api/v1/articles/{a['id']}/unpublish", headers=H(admin_access_token))
    assert r.json()["status"] == "draft"
    assert (await client.get(f"/api/v1/public/articles/{a['slug']}")).status_code == 404


@pytest.mark.asyncio
async def test_authors_only_see_their_own_articles(
    client, doctor_token, test_access_token_2, admin_access_token
):
    mine = await _create(client, doctor_token)
    theirs = await _create(client, test_access_token_2, title_en="Other Doctor Piece")

    listed = (await client.get("/api/v1/articles", headers=H(doctor_token))).json()
    assert [i["id"] for i in listed] == [mine["id"]]
    assert (await client.get(f"/api/v1/articles/{theirs['id']}", headers=H(doctor_token))).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/articles/{theirs['id']}", json={"title_en": "Hijack"}, headers=H(doctor_token)
        )
    ).status_code == 404

    admin_list = (await client.get("/api/v1/articles", headers=H(admin_access_token))).json()
    assert {i["id"] for i in admin_list} == {mine["id"], theirs["id"]}


@pytest.mark.asyncio
async def test_receptionist_cannot_author(client, db_session, test_tenant):
    import uuid

    from app.core.security import create_access_token, get_password_hash
    from app.shared.models import User

    user = User(
        id=str(uuid.uuid4()), tenant_id=test_tenant.id, email="rec@clinic.com",
        password_hash=get_password_hash("RecPass123"), role="receptionist", full_name="Rec",
        language="en", is_active=True, is_email_verified=True, is_2fa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    token = create_access_token(
        {"sub": user.id, "tenant_id": test_tenant.id, "role": "receptionist", "email": user.email, "plan": "free"}
    )
    r = await client.post("/api/v1/articles", json=ARTICLE, headers=H(token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_public_endpoints_need_no_auth_and_filter(client, doctor_token, admin_access_token):
    for title, disc in (("A Homeopathy Piece", "homeopathy"), ("A Herbal Piece", "herbal")):
        a = await _create(client, doctor_token, title_en=title, discipline=disc)
        await client.post(f"/api/v1/articles/{a['id']}/submit", headers=H(doctor_token))
        await client.post(
            f"/api/v1/articles/{a['id']}/publish",
            json={"reviewer_display": "Dr. X"},
            headers=H(admin_access_token),
        )
    herbal = (await client.get("/api/v1/public/articles", params={"discipline": "herbal"})).json()
    assert [i["title_en"] for i in herbal] == ["A Herbal Piece"]
    assert (await client.get("/api/v1/public/articles", params={"kind": "video"})).json() == []
