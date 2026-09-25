"""Dependency-injection context shared by all pages (no globals for business state)."""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
from sqlalchemy.orm import Session
from app.security.permissions import has_permission


@dataclass
class AppContext:
    session_factory: Callable[[], Session]
    get_user_id: Callable[[], int | None]

    def db(self) -> Session:
        return self.session_factory()

    def current_user(self):
        from app.database.models import User
        uid = self.get_user_id()
        if uid is None:
            return None
        db = self.db()
        try:
            u = db.get(User, uid)
            db.expunge_all()
            return u
        finally:
            db.close()

    def can(self, perm: str) -> bool:
        u = self.current_user()
        return has_permission(u, perm) if u else False
