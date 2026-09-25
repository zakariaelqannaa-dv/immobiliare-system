"""Formatting helpers: currency, dates."""
from __future__ import annotations

from datetime import date, datetime
from app.config.settings import settings


def money(v: float | None, currency: str | None = None) -> str:
    c = currency or settings.currency
    try:
        return f"{float(v or 0):,.2f} {c}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"0,00 {c}"


def fmt_date(d: date | datetime | None) -> str:
    if not d:
        return "—"
    try:
        return d.strftime(settings.date_format)
    except Exception:
        return str(d)
