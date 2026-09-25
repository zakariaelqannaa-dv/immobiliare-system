from pathlib import Path
from app.services import property_service as psvc
from app.services import platform_service as plat


def test_backup_verify(tmp_path, db, admin, monkeypatch):
    import app.config.settings as st
    monkeypatch.setattr(st.settings, "backup_dir", tmp_path / "bk")
    monkeypatch.setattr(st.settings, "db_url", "sqlite:///:memory:")
    # create a real sqlite file to back up from
    import sqlite3
    src = tmp_path / "src.db"
    con = sqlite3.connect(str(src))
    con.execute("CREATE TABLE t(a INTEGER)")
    con.commit(); con.close()
    monkeypatch.setattr(st.settings, "db_url", f"sqlite:///{src.as_posix()}")
    import app.services.platform_service as P
    orig = P._db_file
    monkeypatch.setattr(P, "_db_file", lambda: src)
    rec = P.create_backup(db, admin, note="test")
    assert rec.id
    assert P.verify_backup(tmp_path / "bk" / rec.filename)
    assert not P.verify_backup(tmp_path / "nope.db")


def test_validation():
    from app.validators.schemas import PropertyIn
    import pydantic
    try:
        PropertyIn(code="x", city="", price=-1)
        assert False
    except pydantic.ValidationError:
        pass
