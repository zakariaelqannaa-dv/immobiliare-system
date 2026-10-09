"""Contracts, payments, expenses — transactional, status-aware."""
from __future__ import annotations

from datetime import date
from sqlalchemy.orm import Session
from app.database import models as m
from app.repositories.audit import record
from app.security.permissions import require


def _req(user, perm):
    if user is not None:
        require(user, perm)


# ---- Contracts ----
def create_contract(db: Session, user, data: dict) -> m.Contract:
    _req(user, "contracts.create")
    if db.query(m.Contract).filter(m.Contract.number == data.get("number")).first():
        raise ValueError("Numero contratto duplicato")
    prop = db.get(m.Property, int(data["property_id"]))
    if prop is None or not prop.is_active:
        raise ValueError("Immobile non valido")
    c = m.Contract(**data)
    if isinstance(c.ctype, str):
        c.ctype = m.ContractType(c.ctype)
    if isinstance(c.status, str):
        c.status = m.ContractStatus(c.status)
    try:
        db.add(c); db.flush()
        # update property status coherently
        if c.ctype == m.ContractType.SALE and c.status == m.ContractStatus.ACTIVE:
            prop.status = m.PropertyStatus.SOLD
        elif c.ctype == m.ContractType.RENTAL and c.status == m.ContractStatus.ACTIVE:
            prop.status = m.PropertyStatus.RENTED
        record(db, user, "create", "contract", str(c.id), new={"number": c.number})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(c)
    return c


def set_contract_status(db: Session, user, cid: int, status: str) -> m.Contract:
    _req(user, "contracts.edit")
    c = db.get(m.Contract, cid)
    if not c:
        raise ValueError("Contratto non trovato")
    old = str(c.status)
    c.status = m.ContractStatus(status)
    prop = db.get(m.Property, c.property_id)
    try:
        if prop is not None:
            if c.status == m.ContractStatus.ACTIVE:
                prop.status = (m.PropertyStatus.SOLD if c.ctype == m.ContractType.SALE
                               else m.PropertyStatus.RENTED)
            elif c.status in (m.ContractStatus.TERMINATED, m.ContractStatus.EXPIRED,
                              m.ContractStatus.CANCELLED):
                if prop.status in (m.PropertyStatus.SOLD, m.PropertyStatus.RENTED):
                    prop.status = m.PropertyStatus.AVAILABLE
        record(db, user, "update", "contract", str(cid), old={"status": old}, new={"status": status})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(c)
    return c


def list_contracts(db: Session, ctype: str = "", text: str = "", limit=200):
    q = db.query(m.Contract).filter(m.Contract.is_active.is_(True))
    if ctype:
        q = q.filter(m.Contract.ctype == m.ContractType(ctype))
    if text:
        q = q.filter(m.Contract.number.ilike(f"%{text}%"))
    return q.order_by(m.Contract.id.desc()).limit(limit).all()


# ---- Payments ----
def create_payment(db: Session, user, data: dict) -> m.Payment:
    _req(user, "payments.edit")
    if float(data.get("amount", 0)) <= 0:
        raise ValueError("Importo non valido")
    ref = (data.get("reference") or "").strip() or None
    data = {**data, "reference": ref}
    if ref and db.query(m.Payment).filter(
            m.Payment.reference == ref).first():
        raise ValueError("Riferimento pagamento duplicato")
    p = m.Payment(**{k: v for k, v in data.items() if hasattr(m.Payment, k)})
    if isinstance(p.status, str):
        p.status = m.PaymentStatus(p.status)
    # auto late flag
    if p.status == m.PaymentStatus.PENDING and isinstance(p.due_date, date) \
            and p.due_date < date.today():
        p.status = m.PaymentStatus.LATE
    try:
        db.add(p); db.flush()
        record(db, user, "create", "payment", str(p.id), new={"amount": p.amount})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(p)
    return p


def set_payment_status(db: Session, user, pid: int, status: str) -> m.Payment:
    _req(user, "payments.edit")
    p = db.get(m.Payment, pid)
    if not p:
        raise ValueError("Pagamento non trovato")
    old = str(p.status)
    p.status = m.PaymentStatus(status)
    if status == "paid":
        from datetime import date as d
        p.paid_at = d.today()
    record(db, user, "update", "payment", str(pid), old={"status": old}, new={"status": status})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(p)
    return p


def list_payments(db: Session, status: str = "", limit=300):
    q = db.query(m.Payment)
    if status:
        q = q.filter(m.Payment.status == m.PaymentStatus(status))
    return q.order_by(m.Payment.due_date.desc()).limit(limit).all()


def refresh_late(db: Session) -> int:
    n = 0
    try:
        for p in db.query(m.Payment).filter(m.Payment.status == m.PaymentStatus.PENDING).all():
            if isinstance(p.due_date, date) and p.due_date < date.today():
                p.status = m.PaymentStatus.LATE
                n += 1
        if n:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return n


# ---- Expenses ----
def create_expense(db: Session, user, data: dict) -> m.Expense:
    _req(user, "expenses.edit")
    if float(data.get("amount", 0)) <= 0:
        raise ValueError("Importo non valido")
    e = m.Expense(**{k: v for k, v in data.items() if hasattr(m.Expense, k)})
    try:
        db.add(e); db.flush()
        record(db, user, "create", "expense", str(e.id), new={"amount": e.amount})
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(e)
    return e


def list_expenses(db: Session, limit=300):
    return db.query(m.Expense).order_by(m.Expense.date.desc()).limit(limit).all()


def delete_expense(db: Session, user, eid: int) -> None:
    _req(user, "expenses.edit")
    e = db.get(m.Expense, eid)
    if e:
        record(db, user, "delete", "expense", str(eid))
        db.delete(e)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
