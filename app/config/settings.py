"""Central application configuration (env-overridable, no secrets in code)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = Path(__file__).resolve().parents[1]


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


@dataclass
class Settings:
    db_url: str = field(default_factory=lambda: _env("IMMOBILIARE_DB_URL", f"sqlite:///{(BASE_DIR / 'data' / 'immobiliare.db').as_posix()}"))
    language: str = field(default_factory=lambda: _env("IMMOBILIARE_LANGUAGE", "it"))
    theme: str = field(default_factory=lambda: _env("IMMOBILIARE_THEME", "light"))
    backup_dir: Path = field(default_factory=lambda: Path(_env("IMMOBILIARE_BACKUP_DIR", str(BASE_DIR / "backups"))))
    doc_dir: Path = field(default_factory=lambda: Path(_env("IMMOBILIARE_DOC_DIR", str(BASE_DIR / "documents"))))
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    session_timeout_min: int = field(default_factory=lambda: int(_env("IMMOBILIARE_SESSION_TIMEOUT_MIN", "15")))
    max_login_attempts: int = field(default_factory=lambda: int(_env("IMMOBILIARE_MAX_LOGIN_ATTEMPTS", "5")))
    lockout_seconds: int = field(default_factory=lambda: int(_env("IMMOBILIARE_LOCKOUT_SECONDS", "300")))
    company_name: str = field(default_factory=lambda: _env("IMMOBILIARE_COMPANY", "Immobiliare Demo S.r.l."))
    currency: str = field(default_factory=lambda: _env("IMMOBILIARE_CURRENCY", "EUR"))
    date_format: str = field(default_factory=lambda: _env("IMMOBILIARE_DATE_FORMAT", "%d/%m/%Y"))
    max_upload_mb: int = 15
    allowed_image_exts: tuple = (".jpg", ".jpeg", ".png", ".webp")
    allowed_doc_exts: tuple = (".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".csv", ".txt")
    backup_keep: int = 10

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.backup_dir, self.doc_dir):
            p.mkdir(parents=True, exist_ok=True)
        (self.doc_dir / "photos").mkdir(parents=True, exist_ok=True)
        (self.doc_dir / "docs").mkdir(parents=True, exist_ok=True)
        (self.doc_dir / ".gitkeep").touch(exist_ok=True)
        (self.backup_dir / ".gitkeep").touch(exist_ok=True)


settings = Settings()
