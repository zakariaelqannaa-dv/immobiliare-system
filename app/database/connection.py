"""SQLAlchemy engine/session factory."""
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.config.settings import settings


def _sqlite_path_from_url(url: str) -> Path | None:
    if url.startswith("sqlite:///"):
        p = url.replace("sqlite:///", "", 1)
        return Path(p)
    return None


_engine = None
_SessionFactory: sessionmaker | None = None


def get_engine(db_url: str | None = None):
    global _engine, _SessionFactory
    url = db_url or settings.db_url
    if _engine is not None and getattr(_engine, "_imm_url", None) == url:
        return _engine
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _engine = create_engine(url, echo=False, future=True, connect_args=connect_args)

    @event.listens_for(_engine, "connect")
    def _fk_on(dbapi_conn, _rec):  # sqlite FK enforcement
        try:
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
        except Exception:
            pass

    _engine._imm_url = url  # type: ignore[attr-defined]
    _SessionFactory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False, class_=Session)
    # ensure parent dir exists for sqlite
    sp = _sqlite_path_from_url(url)
    if sp is not None:
        sp.parent.mkdir(parents=True, exist_ok=True)
    return _engine


def get_session(db_url: str | None = None) -> Session:
    get_engine(db_url)
    assert _SessionFactory is not None
    return _SessionFactory()


def init_db(db_url: str | None = None):
    from app.database.models import Base
    eng = get_engine(db_url)
    Base.metadata.create_all(eng)
    return eng
