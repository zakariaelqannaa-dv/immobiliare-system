"""Argon2id password hashing + strength validation."""
from __future__ import annotations

import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

MIN_LEN = 8
_STRONG = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def hash_password(password: str) -> str:
    if not password or len(password) < MIN_LEN:
        raise ValueError("Password troppo corta (min 8 caratteri)")
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def validate_strength(password: str) -> tuple[bool, str]:
    if len(password) < MIN_LEN:
        return False, "Minimo 8 caratteri"
    if not _STRONG.match(password):
        return False, "Usa maiuscole, minuscole, numeri e simboli"
    return True, "ok"


def needs_rehash(hashed: str) -> bool:
    try:
        return _ph.check_needs_rehash(hashed)
    except Exception:
        return True
