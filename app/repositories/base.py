"""Generic repository — all SQL lives here, never in GUI."""
from __future__ import annotations

from typing import Generic, TypeVar
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model = None  # type: ignore

    def __init__(self, db: Session):
        self.db = db

    def get(self, id_: int) -> T | None:
        return self.db.get(self.model, id_)

    def list(self, limit: int = 200, offset: int = 0, only_active: bool = True) -> list[T]:
        q = self.db.query(self.model)
        if only_active and hasattr(self.model, "is_active"):
            q = q.filter(self.model.is_active.is_(True))
        return q.order_by(self.model.id.desc()).limit(limit).offset(offset).all()

    def count(self, only_active: bool = True) -> int:
        q = self.db.query(self.model)
        if only_active and hasattr(self.model, "is_active"):
            q = q.filter(self.model.is_active.is_(True))
        return q.count()

    def add(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: T, soft: bool = True) -> None:
        from app.database.models import utcnow
        if soft and hasattr(obj, "deleted_at"):
            obj.is_active = False  # type: ignore
            obj.deleted_at = utcnow()  # type: ignore
            self.db.flush()
        else:
            self.db.delete(obj)
            self.db.flush()
