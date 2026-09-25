"""Visits + appointments/calendar + tasks + notifications."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import models as m
from app.repositories.audit import record
from app.security.permissions import require


def _req(user, perm):
    if user is not None:
        require(user, perm)


# ---- Visits ----
def create_visit(db: Session, user, data: dict) -> m.Visit:
    _req(user, "visits.edit")
    if not data.get("property_id") or not data.get("client_id"):
        raise ValueError("Immobile e cliente obbligatori")
    if isinstance(data.get("scheduled_at"), str):
        data["scheduled_at"] = datetime.fromisoformat(data["scheduled_at"])
    v = m.Visit(**data)
    if isinstance(v.status, str):
        v.status = m.VisitStatus(v.status)
    db.add(v); db.flush()
    # mirror calendar appointment
    db.add(m.Appointment(title=f"Visita {v.id} immobile {v.property_id}",
                         atype=m.AppointmentType.VISIT, starts_at=v.scheduled_at,
                         property_id=v.property_id, client_id=v.client_id,
                         agent_id=v.agent_id))
    record(db, user, "create", "visit", str(v.id))
    db.commit(); db.refresh(v)
    return v


def set_visit_status(db: Session, user, vid: int, status: str, follow_up: str = "") -> m.Visit:
    _req(user, "visits.edit")
    v = db.get(m.Visit, vid)
    if not v:
        raise ValueError("Visita non trovata")
    old = str(v.status)
    v.status = m.VisitStatus(status)
    if follow_up:
        v.follow_up = follow_up
    record(db, user, "update", "visit", str(vid), old={"status": old}, new={"status": status})
    db.commit(); db.refresh(v)
    return v


def list_visits(db: Session, upcoming_only: bool = False, limit=200):
    q = db.query(m.Visit)
    if upcoming_only:
        q = q.filter(m.Visit.scheduled_at >= datetime.utcnow(),
                     m.Visit.status.in_([m.VisitStatus.SCHEDULED, m.VisitStatus.CONFIRMED]))
    return q.order_by(m.Visit.scheduled_at.desc()).limit(limit).all()


# ---- Appointments ----
def create_appointment(db: Session, user, data: dict) -> m.Appointment:
    if isinstance(data.get("starts_at"), str):
        data["starts_at"] = datetime.fromisoformat(data["starts_at"])
    if isinstance(data.get("ends_at"), str) and data["ends_at"]:
        data["ends_at"] = datetime.fromisoformat(data["ends_at"])
    a = m.Appointment(**data)
    if isinstance(a.atype, str):
        a.atype = m.AppointmentType(a.atype)
    db.add(a); db.flush()
    record(db, user, "create", "appointment", str(a.id), new={"title": a.title})
    db.commit(); db.refresh(a)
    return a


def list_appointments(db: Session, start: datetime | None = None,
                      end: datetime | None = None, limit=500):
    q = db.query(m.Appointment)
    if start:
        q = q.filter(m.Appointment.starts_at >= start)
    if end:
        q = q.filter(m.Appointment.starts_at <= end)
    return q.order_by(m.Appointment.starts_at).limit(limit).all()


def complete_appointment(db: Session, user, aid: int, done: bool = True) -> None:
    a = db.get(m.Appointment, aid)
    if a:
        a.is_done = done
        record(db, user, "update", "appointment", str(aid), new={"done": done})
        db.commit()


def delete_appointment(db: Session, user, aid: int) -> None:
    a = db.get(m.Appointment, aid)
    if a:
        record(db, user, "delete", "appointment", str(aid))
        db.delete(a); db.commit()


# ---- Tasks ----
def create_task(db: Session, user, data: dict) -> m.Task:
    if isinstance(data.get("due_at"), str) and data["due_at"]:
        data["due_at"] = datetime.fromisoformat(data["due_at"])
    t = m.Task(**data)
    if isinstance(t.status, str):
        t.status = m.TaskStatus(t.status)
    db.add(t); db.flush()
    record(db, user, "create", "task", str(t.id), new={"title": t.title})
    db.commit(); db.refresh(t)
    return t


def set_task_status(db: Session, user, tid: int, status: str) -> None:
    t = db.get(m.Task, tid)
    if t:
        t.status = m.TaskStatus(status)
        record(db, user, "update", "task", str(tid), new={"status": status})
        db.commit()


def list_tasks(db: Session, only_open: bool = False, limit=200):
    q = db.query(m.Task)
    if only_open:
        q = q.filter(m.Task.status.in_([m.TaskStatus.TODO, m.TaskStatus.IN_PROGRESS]))
    return q.order_by(m.Task.id.desc()).limit(limit).all()


# ---- Notifications ----
def notify(db: Session, user_id: int | None, title: str, body: str = "") -> m.Notification:
    n = m.Notification(user_id=user_id, title=title, body=body)
    db.add(n); db.commit(); db.refresh(n)
    return n


def list_notifications(db: Session, user_id: int | None = None, limit=100):
    q = db.query(m.Notification)
    if user_id:
        q = q.filter((m.Notification.user_id == user_id) | (m.Notification.user_id.is_(None)))
    return q.order_by(m.Notification.created_at.desc()).limit(limit).all()


def mark_read(db: Session, nid: int) -> None:
    n = db.get(m.Notification, nid)
    if n:
        n.is_read = True
        db.commit()
