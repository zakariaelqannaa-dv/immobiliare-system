import pytest
from app.database.connection import init_db, get_session
from app.services.platform_service import ensure_roles_permissions, create_user


@pytest.fixture()
def db(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 't.db').as_posix()}"
    monkeypatch.setenv("IMMOBILIARE_DB_URL", url)
    import app.database.connection as conn
    conn._engine = None
    conn._SessionFactory = None
    init_db(url)
    s = get_session(url)
    ensure_roles_permissions(s)
    # bind session factory used by services? services receive session directly
    yield s
    s.close()


@pytest.fixture()
def admin(db):
    u = create_user(db, None, "admin", "a@x.local", "Admin123!", "Admin", ["ADMIN"])
    return u
