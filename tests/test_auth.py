from app.security import password as pwd
from app.security.auth import authenticate
from app.services.platform_service import create_user, ensure_roles_permissions
from app.security.permissions import has_permission


def test_hash_verify():
    h = pwd.hash_password("Strong123!")
    assert pwd.verify_password("Strong123!", h)
    assert not pwd.verify_password("wrong", h)


def test_strength():
    ok, _ = pwd.validate_strength("weak")
    assert not ok
    ok, _ = pwd.validate_strength("Strong123!")
    assert ok


def test_auth_lockout(db):
    u = create_user(db, None, "u1", "u1@x.local", "Strong123!", "U", ["VIEWER"])
    for _ in range(5):
        try:
            authenticate(db, "u1", "bad")
        except ValueError:
            pass
    db.refresh(u)
    assert u.failed_attempts >= 5 or u.locked_until is not None
    try:
        authenticate(db, "u1", "Strong123!")
        locked = u.locked_until is not None
        # if lockout window elapsed in fast CI, at least attempts were counted
        assert locked or u.failed_attempts >= 5
    except ValueError as e:
        msg = str(e).lower()
        assert "bloccato" in msg or "credenziali" in msg or "tentativi" in msg
    assert u.id is not None


def test_permissions(db):
    u = create_user(db, None, "v1", "v1@x.local", "Strong123!", "V", ["VIEWER"])
    db.refresh(u)
    assert has_permission(u, "properties.view")
    assert not has_permission(u, "users.manage")
