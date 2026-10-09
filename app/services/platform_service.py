"""Documents, users/roles, settings, dashboard, matching, reports, backup."""
from __future__ import annotations

import json
import shutil
import sqlite3
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database import models as m
from app.database.models import utcnow
from app.repositories.audit import record
from app.security import password as pwd
from app.security.permissions import require, PERMISSIONS, ROLE_PERMS


# ============ Documents ============
def add_document(db: Session, user, owner_type: str, owner_id: int,
                 src_path: str | Path, category: str = "general") -> m.Document:
    if user is not None:
        require(user, "documents.edit")
    from app.utils.files import validate_upload, store_document, guess_mime, safe_filename  # noqa
    src = validate_upload(src_path, kind="doc")
    dest = store_document(src)
    d = m.Document(owner_type=owner_type, owner_id=int(owner_id),
                   original_name=Path(src).name, stored_path=str(dest),
                   mime=guess_mime(dest), size_bytes=dest.stat().st_size, category=category)
    db.add(d); db.flush()
    record(db, user, "create", "document", str(d.id),
           new={"owner": f"{owner_type}/{owner_id}", "name": d.original_name})
    db.commit(); db.refresh(d)
    return d


def list_documents(db: Session, owner_type: str = "", owner_id: int = 0, limit=300):
    q = db.query(m.Document)
    if owner_type:
        q = q.filter(m.Document.owner_type == owner_type)
    if owner_id:
        q = q.filter(m.Document.owner_id == owner_id)
    return q.order_by(m.Document.id.desc()).limit(limit).all()


def delete_document(db: Session, user, did: int) -> None:
    if user is not None:
        require(user, "documents.edit")
    d = db.get(m.Document, did)
    if not d:
        return
    record(db, user, "delete", "document", str(did), old={"name": d.original_name})
    try:
        Path(d.stored_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(d); db.commit()


# ============ Users / Roles ============
def ensure_roles_permissions(db: Session) -> None:
    for code, desc in PERMISSIONS:
        if not db.query(m.Permission).filter_by(code=code).first():
            db.add(m.Permission(code=code, description=desc))
    db.flush()
    for rname, codes in ROLE_PERMS.items():
        role = db.query(m.Role).filter_by(name=rname).first()
        if not role:
            role = m.Role(name=rname, description=rname.title())
            db.add(role); db.flush()
        perms = db.query(m.Permission).filter(m.Permission.code.in_(codes)).all()
        role.permissions = perms
    db.commit()


def create_user(db: Session, admin, username: str, email: str,
                password_value: str, full_name: str = "", roles: list[str] | None = None) -> m.User:
    if admin is not None:
        require(admin, "users.manage")
    ok, msg = pwd.validate_strength(password_value)
    if not ok:
        raise ValueError(msg)
    if db.query(m.User).filter((m.User.username == username) | (m.User.email == email)).first():
        raise ValueError("Utente o email duplicati")
    u = m.User(username=username.strip(), email=email.strip(),
               password_hash=pwd.hash_password(password_value), full_name=full_name)
    if roles:
        u.roles = db.query(m.Role).filter(m.Role.name.in_(roles)).all()
    db.add(u); db.flush()
    record(db, admin, "create", "user", str(u.id), new={"username": username})
    db.commit(); db.refresh(u)
    return u


def set_user_enabled(db: Session, admin, uid: int, enabled: bool) -> None:
    if admin is not None:
        require(admin, "users.manage")
    u = db.get(m.User, uid)
    if u:
        u.is_enabled = enabled
        record(db, admin, "update", "user", str(uid), new={"enabled": enabled})
        db.commit()


def set_user_roles(db: Session, admin, uid: int, roles: list[str]) -> None:
    if admin is not None:
        require(admin, "roles.manage")
    u = db.get(m.User, uid)
    if u:
        u.roles = db.query(m.Role).filter(m.Role.name.in_(roles)).all()
        record(db, admin, "update", "user_roles", str(uid), new={"roles": roles})
        db.commit()


def list_users(db: Session):
    return db.query(m.User).order_by(m.User.id).all()


# ============ Settings ============
def get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.get(m.Setting, key)
    return s.value if s else default


def set_setting(db: Session, user, key: str, value: str) -> None:
    if user is not None:
        require(user, "settings.edit")
    s = db.get(m.Setting, key)
    old = s.value if s else ""
    if s:
        s.value = value
    else:
        db.add(m.Setting(key=key, value=value))
    record(db, user, "update", "setting", key, old={"v": old}, new={"v": value})
    db.commit()


# ============ Dashboard ============
def dashboard_stats(db: Session) -> dict:
    P = m.Property
    base = db.query(P).filter(P.is_active.is_(True))
    def cnt(**kw):
        return base.filter_by(**kw).count()
    total = base.count()
    today = date.today()
    month_start = today.replace(day=1)
    revenue = db.query(func.coalesce(func.sum(m.Payment.amount), 0)).filter(
        m.Payment.status == m.PaymentStatus.PAID,
        m.Payment.paid_at >= month_start).scalar() or 0
    expenses = db.query(func.coalesce(func.sum(m.Expense.amount), 0)).filter(
        m.Expense.date >= month_start).scalar() or 0
    return {
        "total": total,
        "available": cnt(status=m.PropertyStatus.AVAILABLE),
        "sale": base.filter(P.listing.in_([m.ListingType.SALE, m.ListingType.BOTH])).count(),
        "rent": base.filter(P.listing.in_([m.ListingType.RENT, m.ListingType.BOTH])).count(),
        "sold": cnt(status=m.PropertyStatus.SOLD),
        "rented": cnt(status=m.PropertyStatus.RENTED),
        "reserved": cnt(status=m.PropertyStatus.RESERVED),
        "clients": db.query(m.Client).filter(m.Client.is_active.is_(True)).count(),
        "upcoming_visits": db.query(m.Visit).filter(
            m.Visit.scheduled_at >= utcnow(),
            m.Visit.status.in_([m.VisitStatus.SCHEDULED, m.VisitStatus.CONFIRMED])).count(),
        "pending_payments": db.query(m.Payment).filter(
            m.Payment.status == m.PaymentStatus.PENDING).count(),
        "late_payments": db.query(m.Payment).filter(
            m.Payment.status == m.PaymentStatus.LATE).count(),
        "revenue": float(revenue),
        "expenses": float(expenses),
    }


def recent_activity(db: Session, limit=15):
    return db.query(m.AuditLog).order_by(m.AuditLog.id.desc()).limit(limit).all()


def upcoming_appointments(db: Session, limit=10):
    return db.query(m.Appointment).filter(
        m.Appointment.starts_at >= utcnow(),
        m.Appointment.is_done.is_(False)).order_by(
        m.Appointment.starts_at).limit(limit).all()


def recent_properties(db: Session, limit=6):
    return db.query(m.Property).filter(
        m.Property.is_active.is_(True)).order_by(
        m.Property.created_at.desc()).limit(limit).all()


# ============ Matching engine ============
def match_properties_for_client(db: Session, client_id: int, limit: int = 50):
    c = db.get(m.Client, client_id)
    if not c:
        raise ValueError("Cliente non trovato")
    q = db.query(m.Property).filter(m.Property.is_active.is_(True),
                                    m.Property.status == m.PropertyStatus.AVAILABLE)
    if c.desired_type:
        try:
            q = q.filter(m.Property.ptype == m.PropertyType(c.desired_type))
        except ValueError:
            pass
    props = q.limit(500).all()
    scored: list[tuple[float, m.Property, list[str]]] = []
    for p in props:
        score = 0.0
        reasons: list[str] = []
        # price: compare sale price or rent depending on listing
        ref_price = p.price if p.listing in (m.ListingType.SALE, m.ListingType.BOTH) else p.monthly_rent
        max_p = c.max_price or 0
        min_p = c.min_price or 0
        if max_p and ref_price <= max_p:
            score += 30; reasons.append("Prezzo compatibile")
        elif max_p and ref_price <= max_p * 1.1:
            score += 12; reasons.append("Prezzo vicino al budget (+10%)")
        if min_p and ref_price >= min_p:
            score += 5; reasons.append("Prezzo sopra il minimo")
        if c.min_surface and p.surface >= c.min_surface:
            score += 20; reasons.append("Superficie adeguata")
        cities = [x.strip().lower() for x in (c.desired_cities or "").split(",") if x.strip()]
        if cities and p.city.lower() in cities:
            score += 20; reasons.append("Città desiderata")
        if c.desired_type and p.ptype.value == c.desired_type:
            score += 10; reasons.append("Tipologia corrispondente")
        if c.desired_rooms and p.rooms >= c.desired_rooms:
            score += 8; reasons.append("Locali sufficienti")
        if c.desired_bedrooms and p.bedrooms >= c.desired_bedrooms:
            score += 7; reasons.append("Camere sufficienti")
        if score > 0:
            scored.append((score, p, reasons))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "property": p, "reasons": r} for s, p, r in scored[:limit]]


# ============ Reports ============
def report_dataset(db: Session, kind: str):
    today = date.today()
    if kind == "inventory":
        rows = db.query(m.Property).filter(m.Property.is_active.is_(True)).all()
        return (["Codice", "Tipo", "Città", "Prezzo", "Canone", "Mq", "Stato"],
                [[p.code, p.ptype.value, p.city, p.price, p.monthly_rent, p.surface, p.status.value] for p in rows])
    if kind == "sales":
        rows = db.query(m.Contract).filter(m.Contract.ctype == m.ContractType.SALE).all()
        return (["Numero", "Immobile", "Cliente", "Prezzo", "Stato", "Inizio"],
                [[c.number, c.property_id, c.client_id, c.price, c.status.value, str(c.start_date)] for c in rows])
    if kind == "rentals":
        rows = db.query(m.Contract).filter(m.Contract.ctype == m.ContractType.RENTAL).all()
        return (["Numero", "Immobile", "Cliente", "Prezzo", "Stato", "Inizio", "Fine"],
                [[c.number, c.property_id, c.client_id, c.price, c.status.value, str(c.start_date), str(c.end_date)] for c in rows])
    if kind == "payments_due":
        rows = db.query(m.Payment).filter(m.Payment.status.in_(
            [m.PaymentStatus.PENDING, m.PaymentStatus.LATE])).all()
        return (["ID", "Contratto", "Importo", "Scadenza", "Stato", "Riferimento"],
                [[p.id, p.contract_id, p.amount, str(p.due_date), p.status.value, p.reference] for p in rows])
    if kind == "revenue":
        rows = db.query(m.Payment).filter(m.Payment.status == m.PaymentStatus.PAID).all()
        return (["ID", "Importo", "Pagato il", "Riferimento"],
                [[p.id, p.amount, str(p.paid_at), p.reference] for p in rows])
    if kind == "expenses":
        rows = db.query(m.Expense).all()
        return (["ID", "Immobile", "Categoria", "Importo", "Data", "Descrizione"],
                [[e.id, e.property_id, e.category, e.amount, str(e.date), (e.description or "")[:60]] for e in rows])
    if kind == "owner_statement":
        rows = db.query(m.Owner).filter(m.Owner.is_active.is_(True)).all()
        out = []
        for o in rows:
            nprop = db.query(m.Property).filter(m.Property.owner_id == o.id).count()
            out.append([o.id, o.display_name, nprop])
        return (["ID", "Proprietario", "N. immobili"], out)
    if kind == "agent_commissions":
        agents = db.query(m.Agent).filter(m.Agent.is_active.is_(True)).all()
        out = []
        for a in agents:
            contracts = db.query(m.Contract).filter(m.Contract.agent_id == a.id,
                                                    m.Contract.status == m.ContractStatus.ACTIVE).all()
            total = sum(c.price for c in contracts)
            out.append([a.display_name, len(contracts), round(total, 2),
                        round(total * (a.commission_pct or 0) / 100, 2)])
        return (["Agente", "Contratti", "Volume", "Provvigioni"], out)
    # monthly stats
    month_start = today.replace(day=1)
    rev = db.query(func.coalesce(func.sum(m.Payment.amount), 0)).filter(
        m.Payment.status == m.PaymentStatus.PAID, m.Payment.paid_at >= month_start).scalar() or 0
    exp = db.query(func.coalesce(func.sum(m.Expense.amount), 0)).filter(
        m.Expense.date >= month_start).scalar() or 0
    return (["Metrica", "Valore"], [["Ricavi mese", rev], ["Spese mese", exp],
                                    ["Margine", float(rev) - float(exp)]])


# ============ Backup / Restore ============
def _db_file() -> Path | None:
    url = settings.db_url
    if url.startswith("sqlite:///"):
        return Path(url.replace("sqlite:///", "", 1))
    return None


def create_backup(db: Session, user, note: str = "", encrypt: bool = False) -> m.BackupRecord:
    if user is not None:
        require(user, "backups.manage")
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    src = _db_file()
    if src is None or not src.exists():
        raise ValueError("Database SQLite non trovato per il backup")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw = settings.backup_dir / f"immobiliare_{ts}.db"
    # online-safe copy
    dest_conn = sqlite3.connect(str(raw))
    try:
        src_conn = sqlite3.connect(str(src))
        try:
            src_conn.backup(dest_conn)
        finally:
            src_conn.close()
    finally:
        dest_conn.close()
    final = raw
    if encrypt:
        from app.security.encryption import encrypt_text
        import base64
        data = raw.read_bytes()
        token = encrypt_text(base64.b64encode(data).decode())
        final = raw.with_suffix(".db.enc")
        final.write_text(token)
        raw.unlink(missing_ok=True)
    rec = m.BackupRecord(filename=final.name, size_bytes=final.stat().st_size,
                         encrypted=encrypt, note=note)
    db.add(rec)
    record(db, user, "backup", "backup", final.name, new={"note": note})
    db.commit(); db.refresh(rec)
    # rotation
    files = sorted(settings.backup_dir.glob("immobiliare_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[settings.backup_keep:]:
        try:
            old.unlink()
        except Exception:
            pass
    return rec


def verify_backup(path: str | Path) -> bool:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return False
    if p.suffix == ".enc":
        try:
            from app.security.encryption import decrypt_text
            import base64
            raw = base64.b64decode(decrypt_text(p.read_text()))
            if raw[:16] != b"SQLite format 3\x00":
                return False
            return True
        except Exception:
            return False
    try:
        with open(p, "rb") as f:
            return f.read(16) == b"SQLite format 3\x00"
    except Exception:
        return False


def restore_backup(db: Session, user, filename: str) -> None:
    if user is not None:
        require(user, "backups.manage")
    p = settings.backup_dir / Path(filename).name
    if not verify_backup(p):
        raise ValueError("Backup non valido: ripristino annullato")
    src = _db_file()
    assert src is not None
    # resolve payload to temp db file then swap
    if p.suffix == ".enc":
        from app.security.encryption import decrypt_text
        import base64, tempfile
        raw = base64.b64decode(decrypt_text(p.read_text()))
        tmp = Path(tempfile.gettempdir()) / "immobiliare_restore.db"
        tmp.write_bytes(raw)
        payload = tmp
    else:
        payload = p
    # validate tables
    con = sqlite3.connect(str(payload))
    try:
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()
    if "users" not in tables or "properties" not in tables:
        raise ValueError("Backup privo delle tabelle richieste")
    record(db, user, "restore", "backup", p.name)
    db.commit()
    db.close()
    shutil.copy2(payload, src)


def export_audit_json(db: Session, path: str | Path) -> Path:
    rows = db.query(m.AuditLog).order_by(m.AuditLog.id.desc()).limit(5000).all()
    p = Path(path)
    p.write_text(json.dumps([{"at": str(r.at), "user": r.username, "action": r.action,
                              "entity": r.entity, "entity_id": r.entity_id,
                              "result": r.result} for r in rows],
                            ensure_ascii=False, indent=2), encoding="utf-8")
    return p
