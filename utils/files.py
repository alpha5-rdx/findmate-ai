"""Local image storage."""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

from config import ALLOWED_IMAGE_EXT, BASE_DIR, MAX_IMAGE_MB, UPLOAD_DIR


def save_image(uploaded) -> tuple[Optional[str], Optional[str]]:
    """Validate and store a Streamlit UploadedFile.

    Returns (relative_path, error). Both None when nothing was uploaded.
    """
    if uploaded is None:
        return None, None
    ext = Path(uploaded.name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return None, f"Unsupported image type '{ext}'. Use PNG, JPG or WEBP."
    data = uploaded.getvalue()
    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        return None, f"Image is larger than {MAX_IMAGE_MB} MB."
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # reject corrupt / non-image content
    except Exception:
        return None, "The uploaded file is not a valid image."
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"  # random name: no path tricks
    target.write_bytes(data)
    return str(target.relative_to(BASE_DIR)), None


def resolve(path: Optional[str]) -> Optional[Path]:
    """Absolute path of a stored image if it still exists."""
    if not path:
        return None
    p = BASE_DIR / path
    return p if p.exists() else None


def remove_image(path: Optional[str]) -> None:
    p = resolve(path)
    if p:
        try:
            p.unlink()
        except OSError:
            pass
