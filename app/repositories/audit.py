"""Audit helper used by services."""
from __future__ import annotations

import json
from sqlalchemy.orm import Session
from app.database.models import AuditLog


def _safe(v) -> str:
    try:
        if isinstance(v, dict):
            v = {k: ("***" if "pass" in k.lower() else val) for k, val in v.items()}
            return json.dumps(v, default=str)[:4000]
        return str(v)[:4000]
    except Exception:
        return ""


def record(db: Session, user, action: str, entity: str, entity_id: str = "",
           old=None, new=None, result: str = "ok") -> None:
    db.add(AuditLog(user_id=getattr(user, "id", None),
                    username=getattr(user, "username", "") or "",
                    action=action, entity=entity, entity_id=str(entity_id),
                    old_value=_safe(old) if old is not None else "",
                    new_value=_safe(new) if new is not None else "",
                    result=result))
