"""Fernet encryption for sensitive fields + keyring-backed key storage."""
from __future__ import annotations

from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import settings

SERVICE = "immobiliare-system"
ACCOUNT = "app-encryption-key"


def _fallback_key_file() -> Path:
    p = settings.data_dir / ".fernet.key"
    return p


def get_or_create_key() -> bytes:
    # 1) try keyring
    try:
        import keyring
        existing = keyring.get_password(SERVICE, ACCOUNT)
        if existing:
            return existing.encode()
        key = Fernet.generate_key().decode()
        try:
            keyring.set_password(SERVICE, ACCOUNT, key)
        except Exception:
            pass
        return key.encode()
    except Exception:
        pass
    # 2) fallback file with restricted perms
    kf = _fallback_key_file()
    kf.parent.mkdir(parents=True, exist_ok=True)
    if kf.exists():
        return kf.read_bytes().strip()
    key = Fernet.generate_key()
    kf.write_bytes(key)
    try:
        import os
        os.chmod(kf, 0o600)
    except Exception:
        pass
    return key


def _fernet() -> Fernet:
    return Fernet(get_or_create_key())


def encrypt_text(plain: str) -> str:
    if plain is None:
        return ""
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_text(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Dati cifrati non validi")
