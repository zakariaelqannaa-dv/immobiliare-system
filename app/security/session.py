"""Session handling with inactivity timeout (single active user per GUI process)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Session:
    user_id: int
    username: str
    last_activity: datetime
    timeout_min: int = 15

    def touch(self) -> None:
        self.last_activity = datetime.utcnow()

    def is_expired(self) -> bool:
        return datetime.utcnow() - self.last_activity > timedelta(minutes=self.timeout_min)


_current: Session | None = None


def start_session(user_id: int, username: str, timeout_min: int = 15) -> Session:
    global _current
    _current = Session(user_id=user_id, username=username,
                       last_activity=datetime.utcnow(), timeout_min=timeout_min)
    return _current


def get_session() -> Session | None:
    global _current
    if _current and _current.is_expired():
        _current = None
    return _current


def touch() -> None:
    s = get_session()
    if s:
        s.touch()


def end_session() -> None:
    global _current
    _current = None
