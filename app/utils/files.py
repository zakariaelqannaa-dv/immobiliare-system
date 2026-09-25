"""Secure file handling: safe names, type/size validation, thumbnails. No path traversal."""
from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path
from PIL import Image

from app.config.settings import settings

_UNSAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_filename(original: str) -> str:
    name = Path(original).name  # strip directories -> prevents traversal
    name = _UNSAFE.sub("_", name).strip("._") or "file"
    suffix = Path(name).suffix.lower()
    stem = Path(name).stem[:60] or "file"
    return f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"


def validate_upload(path: Path | str, kind: str = "doc") -> Path:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise ValueError("File non trovato")
    size_mb = p.stat().st_size / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise ValueError(f"File troppo grande (max {settings.max_upload_mb} MB)")
    ext = p.suffix.lower()
    if kind == "image":
        if ext not in settings.allowed_image_exts:
            raise ValueError(f"Tipo immagine non consentito: {ext}")
        # verify real image
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception:
            raise ValueError("File immagine non valido")
    else:
        if ext not in settings.allowed_doc_exts:
            raise ValueError(f"Tipo documento non consentito: {ext}")
    return p


def store_photo(src: Path, property_code: str) -> tuple[Path, Path]:
    dest_dir = settings.doc_dir / "photos" / property_code
    dest_dir.mkdir(parents=True, exist_ok=True)
    fname = safe_filename(src.name)
    dest = dest_dir / fname
    dest.write_bytes(Path(src).read_bytes())
    thumb = dest_dir / f"thumb_{fname}"
    try:
        with Image.open(dest) as im:
            im.thumbnail((320, 320))
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im.save(thumb, "JPEG", quality=80)
    except Exception:
        thumb = dest
    return dest, thumb


def store_document(src: Path, subdir: str = "docs") -> Path:
    dest_dir = settings.doc_dir / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    fname = safe_filename(src.name)
    dest = dest_dir / fname
    dest.write_bytes(Path(src).read_bytes())
    return dest


def guess_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"
