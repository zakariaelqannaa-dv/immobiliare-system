"""Structured logging — never log passwords, tokens, keys or sensitive PII."""
from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SENSITIVE = re.compile(r"(password|passwd|pwd|secret|token|api[_-]?key|encryption[_-]?key|fernet)", re.IGNORECASE)

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_FILE = BASE_DIR / "data" / "immobiliare.log"


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        if _SENSITIVE.search(msg):
            record.msg = "[REDACTED sensitive log suppressed]"
            record.args = ()
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("immobiliare")
    logger.setLevel(level)
    if logger.handlers:
        for h in logger.handlers:
            try:
                h.setLevel(level)
            except Exception:
                pass
        return logger
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(level)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(level)
    filt = RedactingFilter()
    fh.addFilter(filt)
    sh.addFilter(filt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"immobiliare.{name}")
