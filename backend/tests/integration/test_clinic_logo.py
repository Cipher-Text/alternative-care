"""Clinic logo upload: stored in object storage (a fake here), validated by content, doctors only."""

import io

import pytest
from PIL import Image

from app.core.config import settings
from app.core.storage import PUBLIC_PREFIX, key_from_public_url, public_url

H = lambda token: {"Authorization": f"Bearer {token}"}  # noqa: E731


def _image(fmt="PNG", size=(800, 400), color=(10, 120, 80)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format=fmt)
    return out.getvalue()


def _upload(client, token, data, name="logo.png", content_type="image/png"):
    return client.post("/api/v1/tenant/logo", files={"file": (name, data, content_type)}, headers=H(token))


@pytest.mark.asyncio
async def test_doctor_uploads_a_logo_that_is_resized_and_stored_publicly(client, doctor_token, memory_storage, test_tenant):
    r = await _upload(client, doctor_token, _image(size=(2000, 1000)))
    assert r.status_code == 200, r.text
    url = r.json()["logo_url"]
    key = key_from_public_url(url)
    assert key and key.startswith(f"{PUBLIC_PREFIX}tenants/{test_tenant.id}/logo-") and url == public_url(key)

    stored = memory_storage.objects[key]
    assert stored.content_type == "image/png"
    assert Image.open(io.BytesIO(stored.data)).size == (512, 256)  # fits 512px, ratio kept

    # it is what the clinic profile now returns
    assert (await client.get("/api/v1/tenant/profile", headers=H(doctor_token))).json()["logo_url"] == url


@pytest.mark.asyncio
async def test_replacing_the_logo_removes_the_old_file(client, doctor_token, memory_storage):
    first = (await _upload(client, doctor_token, _image(color=(255, 0, 0)))).json()["logo_url"]
    second = (await _upload(client, doctor_token, _image(color=(0, 0, 255)))).json()["logo_url"]
    assert first != second
    assert list(memory_storage.objects) == [key_from_public_url(second)]
    # the same image again is the same file, so nothing is deleted
    assert (await _upload(client, doctor_token, _image(color=(0, 0, 255)))).json()["logo_url"] == second
    assert list(memory_storage.objects) == [key_from_public_url(second)]


@pytest.mark.asyncio
async def test_remove_logo(client, doctor_token, memory_storage):
    await _upload(client, doctor_token, _image())
    r = await client.delete("/api/v1/tenant/logo", headers=H(doctor_token))
    assert r.status_code == 200 and r.json()["logo_url"] is None
    assert memory_storage.objects == {}
    assert (await client.delete("/api/v1/tenant/logo", headers=H(doctor_token))).status_code == 200  # idempotent


@pytest.mark.asyncio
async def test_only_real_images_in_allowed_formats_and_size_are_accepted(client, doctor_token, memory_storage):
    assert (await _upload(client, doctor_token, b"")).status_code == 422
    # a script renamed to .png, and an SVG, are not images we accept
    assert (await _upload(client, doctor_token, b"<script>alert(1)</script>")).status_code == 422
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    assert (await _upload(client, doctor_token, svg, "logo.svg", "image/svg+xml")).status_code == 422
    assert (await _upload(client, doctor_token, _image("GIF"), "logo.gif", "image/gif")).status_code == 422
    assert (await _upload(client, doctor_token, _image("BMP"), "logo.bmp", "image/bmp")).status_code == 422
    # the content decides, not the name or the declared type
    assert (await _upload(client, doctor_token, _image("JPEG"), "logo.png", "text/plain")).status_code == 200
    assert (await _upload(client, doctor_token, _image("WEBP"), "logo.webp", "image/webp")).status_code == 200
    # too large
    assert (await _upload(client, doctor_token, b"\x89PNG" + b"0" * (2 * 1024 * 1024 + 10))).status_code == 413
    # nothing from the refused uploads was stored
    assert len(memory_storage.objects) == 1


@pytest.mark.asyncio
async def test_metadata_in_the_upload_is_not_kept(client, doctor_token, memory_storage):
    image = Image.new("RGB", (100, 100), (1, 2, 3))
    exif = Image.Exif()
    exif[0x010E] = "secret description"  # ImageDescription
    out = io.BytesIO()
    image.save(out, format="JPEG", exif=exif)
    assert b"secret description" in out.getvalue()

    r = await _upload(client, doctor_token, out.getvalue(), "photo.jpg", "image/jpeg")
    assert r.status_code == 200
    (stored,) = memory_storage.objects.values()
    assert b"secret description" not in stored.data


@pytest.mark.asyncio
async def test_only_doctors_and_only_their_own_clinic(client, test_access_token_2, doctor_token, memory_storage, test_tenant, test_tenant_2, db_session):
    assert (await client.post("/api/v1/tenant/logo", files={"file": ("l.png", _image(), "image/png")})).status_code == 401
    # clinic 2's doctor changes clinic 2 only
    r = await _upload(client, test_access_token_2, _image())
    assert r.status_code == 200
    assert f"/tenants/{test_tenant_2.id}/" in r.json()["logo_url"]
    await db_session.refresh(test_tenant)
    assert test_tenant.logo_url is None


@pytest.mark.asyncio
async def test_the_logo_cannot_be_set_to_an_arbitrary_url_through_the_profile(client, doctor_token):
    r = await client.patch("/api/v1/tenant/profile", json={"logo_url": "https://evil.example/track.png"}, headers=H(doctor_token))
    assert r.status_code == 200
    assert r.json()["logo_url"] is None


def test_key_from_public_url_only_trusts_urls_this_app_issued(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PUBLIC_BASE_URL", "https://files.example.com")
    assert key_from_public_url("https://files.example.com/public/tenants/a/logo-1.png") == "public/tenants/a/logo-1.png"
    assert key_from_public_url("https://evil.example/public/tenants/a/logo-1.png") is None
    assert key_from_public_url("https://files.example.com/private/x.png") is None
    assert key_from_public_url(None) is None
    monkeypatch.setattr(settings, "STORAGE_PUBLIC_BASE_URL", "http://localhost:9000/altcare")
    assert key_from_public_url("http://localhost:9000/altcare/public/a.png") == "public/a.png"
