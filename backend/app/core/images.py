"""Uploaded images: validate by content, never by the filename or the browser's content type.

The upload is decoded and re-encoded, which drops EXIF/GPS metadata and anything hidden in the file, and
caps the size so a logo is never a multi-megabyte photo.
"""

import hashlib
import io

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_SOURCE_PIXELS = 25_000_000  # refuse decompression bombs before decoding
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}  # not SVG (scripts) and not GIF (animation)


def _refuse(message: str, code: int = status.HTTP_422_UNPROCESSABLE_ENTITY) -> HTTPException:
    return HTTPException(code, message)


def process_logo(raw: bytes, max_side: int = 512) -> tuple[bytes, str]:
    """Return (png bytes, content hash) for a clinic logo, or raise 413/422."""
    if not raw:
        raise _refuse("The file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise _refuse(f"The image is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    try:
        probe = Image.open(io.BytesIO(raw))
        if probe.format not in ALLOWED_FORMATS:
            raise _refuse("Use a PNG, JPEG or WebP image.")
        if probe.width * probe.height > MAX_SOURCE_PIXELS:
            raise _refuse("The image has too many pixels. Use a smaller one.")
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image)  # honour phone-camera rotation before the metadata is dropped
        image.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise _refuse("This file is not a valid image.") from None

    image = image.convert("RGBA")
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    data = out.getvalue()
    return data, hashlib.sha256(data).hexdigest()[:16]
