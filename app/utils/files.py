"""Secure file handling: safe names, type/size validation, thumbnails. No path traversal."""
from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path
from PIL import Image

from app.config.settings import settings

try:
    Image.MAX_IMAGE_PIXELS = 50_000_000
except Exception:
    pass

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
        # verify real image: load() forces full decode (catches bombs/truncated files)
        try:
            with Image.open(p) as im:
                im.verify()
            with Image.open(p) as im2:
                im2.load()
                w, h = im2.size
                if w * h > Image.MAX_IMAGE_PIXELS:
                    raise ValueError("Immagine troppo grande")
                if im2.format and im2.format.lower() not in ("jpeg", "jpg", "png", "webp"):
                    raise ValueError(f"Formato immagine non consentito: {im2.format}")
        except ValueError:
            raise
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
            im.load()
            im.thumbnail((640, 640))
            if im.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
                im = bg
            elif im.mode != "RGB":
                im = im.convert("RGB")
            im.save(thumb, "JPEG", quality=82, optimize=True)
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
