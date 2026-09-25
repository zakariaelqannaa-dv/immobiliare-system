"""Duplicate detection helpers."""
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import models as m


def find_duplicate_property(db: Session, city: str, address: str, surface: float, exclude_id: int = 0):
    q = db.query(m.Property).filter(
        func.lower(m.Property.city) == (city or "").lower(),
        func.lower(m.Property.address) == (address or "").lower(),
    )
    if exclude_id:
        q = q.filter(m.Property.id != exclude_id)
    return q.first()


def find_duplicate_person(db: Session, model, email: str, phone: str, exclude_id: int = 0):
    if email:
        q = db.query(model).filter(func.lower(model.email) == email.lower())
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        hit = q.first()
        if hit:
            return hit
    return None
