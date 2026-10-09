"""Authentication: login, lockout, password reset, audit. No plaintext passwords."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.models import User, utcnow
from app.security import password as pwd
from app.security import session as sess


def _audit(db: Session, user: User | None, action: str, result: str = "ok") -> None:
    from app.database.models import AuditLog
    db.add(AuditLog(user_id=user.id if user else None,
                    username=user.username if user else "",
                    action=action, entity="user",
                    entity_id=str(user.id) if user else "",
                    result=result))


def authenticate(db: Session, login: str, password_value: str) -> User:
    login = (login or "").strip()
    user = db.query(User).filter(
        or_(User.username == login, User.email == login)).first()
    now = utcnow()
    if user is None:
        raise ValueError("Credenziali non valide")
    if not user.is_enabled or not user.is_active:
        _audit(db, user, "login", result="denied")
        db.commit()
        raise ValueError("Account disabilitato")
    if user.locked_until and user.locked_until > now:
        _audit(db, user, "login", result="locked")
        db.commit()
        raise ValueError("Account temporaneamente bloccato. Riprova più tardi.")
    if not pwd.verify_password(password_value, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= settings.max_login_attempts:
            user.locked_until = now + timedelta(seconds=settings.lockout_seconds)
            user.failed_attempts = 0
        _audit(db, user, "login", result="failed")
        db.commit()
        raise ValueError("Credenziali non valide")
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    if pwd.needs_rehash(user.password_hash):
        user.password_hash = pwd.hash_password(password_value)
    _audit(db, user, "login", result="ok")
    db.commit()
    db.refresh(user)
    return user


def logout(db: Session, user: User | None) -> None:
    if user is not None:
        _audit(db, user, "logout", result="ok")
        db.commit()
    sess.end_session()


def create_reset_token(db: Session, email: str) -> str:
    user = db.query(User).filter(User.email == email.strip()).first()
    if user is None:
        raise ValueError("Se l'email esiste, riceverai le istruzioni")
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_expires = utcnow() + timedelta(hours=2)
    _audit(db, user, "password_reset_request", result="ok")
    db.commit()
    return token


def reset_password(db: Session, token: str, new_password: str) -> None:
    ok, msg = pwd.validate_strength(new_password)
    if not ok:
        raise ValueError(msg)
    user = db.query(User).filter(User.reset_token == token).first()
    if user is None or not user.reset_expires or user.reset_expires < utcnow():
        raise ValueError("Token non valido o scaduto")
    user.password_hash = pwd.hash_password(new_password)
    user.reset_token = None
    user.reset_expires = None
    _audit(db, user, "password_reset", result="ok")
    db.commit()


def change_password(db: Session, user: User, old: str, new: str) -> None:
    if not pwd.verify_password(old, user.password_hash):
        raise ValueError("Password attuale errata")
    ok, msg = pwd.validate_strength(new)
    if not ok:
        raise ValueError(msg)
    user.password_hash = pwd.hash_password(new)
    _audit(db, user, "password_change", result="ok")
    db.commit()
