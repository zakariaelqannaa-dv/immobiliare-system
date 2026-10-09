"""Generic people services: owners, clients, agents."""
from __future__ import annotations

from sqlalchemy.orm import Session
from app.database import models as m
from app.database.models import utcnow
from app.repositories.audit import record
from app.security.permissions import require
from app.utils.duplicates import find_duplicate_person

_DENY = {"id", "created_at", "updated_at", "deleted_at", "is_active"}


def _req(user, perm):
    if user is not None:
        require(user, perm)


# ---- Owners ----
def create_owner(db: Session, user, data: dict) -> m.Owner:
    _req(user, "owners.edit")
    dup = find_duplicate_person(db, m.Owner, data.get("email", ""), data.get("phone", ""))
    if dup:
        raise ValueError(f"Possibile duplicato proprietario: {dup.display_name}")
    clean = {k: v for k, v in data.items() if k not in _DENY and hasattr(m.Owner, k)}
    o = m.Owner(**clean)
    db.add(o)
    try:
        db.flush()
        record(db, user, "create", "owner", str(o.id), new={"name": o.display_name})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(o)
    return o


def update_owner(db: Session, user, oid: int, data: dict) -> m.Owner:
    _req(user, "owners.edit")
    o = db.get(m.Owner, oid)
    if not o:
        raise ValueError("Proprietario non trovato")
    old = {"name": o.display_name}
    for k, v in data.items():
        if hasattr(o, k) and k not in _DENY:
            setattr(o, k, v)
    record(db, user, "update", "owner", str(o.id), old=old, new={"name": o.display_name})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(o)
    return o


def delete_owner(db: Session, user, oid: int) -> None:
    _req(user, "owners.edit")
    o = db.get(m.Owner, oid)
    if not o:
        return
    n = db.query(m.Property).filter(m.Property.owner_id == oid, m.Property.is_active.is_(True)).count()
    if n:
        raise ValueError("Il proprietario ha immobili attivi: archivia prima gli immobili")
    o.is_active = False; o.deleted_at = utcnow()
    record(db, user, "delete", "owner", str(oid), old={"name": o.display_name})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_owners(db: Session, text: str = "", limit=200):
    q = db.query(m.Owner).filter(m.Owner.is_active.is_(True))
    if text:
        like = f"%{text}%"
        from sqlalchemy import or_
        q = q.filter(or_(m.Owner.first_name.ilike(like), m.Owner.last_name.ilike(like),
                         m.Owner.company_name.ilike(like), m.Owner.email.ilike(like),
                         m.Owner.city.ilike(like)))
    return q.order_by(m.Owner.id.desc()).limit(limit).all()


# ---- Clients ----
def create_client(db: Session, user, data: dict) -> m.Client:
    _req(user, "clients.edit")
    dup = find_duplicate_person(db, m.Client, data.get("email", ""), data.get("phone", ""))
    if dup:
        raise ValueError(f"Possibile duplicato cliente: {dup.display_name}")
    if data.get("min_price") and data.get("max_price"):
        try:
            if float(data["min_price"]) > float(data["max_price"]) > 0:
                raise ValueError("Prezzo min superiore al max")
        except ValueError:
            raise
        except Exception:
            pass
    clean = {k: v for k, v in data.items() if k not in _DENY and hasattr(m.Client, k)}
    c = m.Client(**clean)
    db.add(c)
    try:
        db.flush()
        record(db, user, "create", "client", str(c.id), new={"name": c.display_name})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(c)
    return c


def update_client(db: Session, user, cid: int, data: dict) -> m.Client:
    _req(user, "clients.edit")
    c = db.get(m.Client, cid)
    if not c:
        raise ValueError("Cliente non trovato")
    old = {"name": c.display_name}
    for k, v in data.items():
        if hasattr(c, k) and k not in _DENY:
            setattr(c, k, v)
    record(db, user, "update", "client", str(c.id), old=old, new={"name": c.display_name})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(c)
    return c


def delete_client(db: Session, user, cid: int) -> None:
    _req(user, "clients.edit")
    c = db.get(m.Client, cid)
    if not c:
        return
    c.is_active = False; c.deleted_at = utcnow()
    record(db, user, "delete", "client", str(cid), old={"name": c.display_name})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_clients(db: Session, text: str = "", limit=200):
    q = db.query(m.Client).filter(m.Client.is_active.is_(True))
    if text:
        like = f"%{text}%"
        from sqlalchemy import or_
        q = q.filter(or_(m.Client.first_name.ilike(like), m.Client.last_name.ilike(like),
                         m.Client.email.ilike(like), m.Client.phone.ilike(like)))
    return q.order_by(m.Client.id.desc()).limit(limit).all()


def toggle_favorite(db: Session, user, client_id: int, property_id: int) -> bool:
    _req(user, "clients.edit")
    ex = db.query(m.ClientFavorite).filter_by(client_id=client_id, property_id=property_id).first()
    try:
        if ex:
            db.delete(ex)
            db.commit()
            record(db, user, "delete", "favorite", f"{client_id}/{property_id}")
            return False
        db.add(m.ClientFavorite(client_id=client_id, property_id=property_id))
        db.commit()
        record(db, user, "create", "favorite", f"{client_id}/{property_id}")
        return True
    except Exception:
        db.rollback()
        raise


# ---- Agents ----
def create_agent(db: Session, user, data: dict) -> m.Agent:
    _req(user, "agents.edit")
    clean = {k: v for k, v in data.items() if k not in _DENY and hasattr(m.Agent, k)}
    a = m.Agent(**clean)
    db.add(a)
    try:
        db.flush()
        record(db, user, "create", "agent", str(a.id), new={"name": a.display_name})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(a)
    return a


def update_agent(db: Session, user, aid: int, data: dict) -> m.Agent:
    _req(user, "agents.edit")
    a = db.get(m.Agent, aid)
    if not a:
        raise ValueError("Agente non trovato")
    for k, v in data.items():
        if hasattr(a, k) and k not in _DENY:
            setattr(a, k, v)
    record(db, user, "update", "agent", str(a.id), new={"name": a.display_name})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(a)
    return a


def delete_agent(db: Session, user, aid: int) -> None:
    _req(user, "agents.edit")
    a = db.get(m.Agent, aid)
    if not a:
        return
    a.is_active = False; a.deleted_at = utcnow()
    record(db, user, "delete", "agent", str(aid))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_agents(db: Session, text: str = "", limit=200):
    q = db.query(m.Agent).filter(m.Agent.is_active.is_(True))
    if text:
        like = f"%{text}%"
        from sqlalchemy import or_
        q = q.filter(or_(m.Agent.first_name.ilike(like), m.Agent.last_name.ilike(like),
                         m.Agent.email.ilike(like)))
    return q.order_by(m.Agent.id.desc()).limit(limit).all()
