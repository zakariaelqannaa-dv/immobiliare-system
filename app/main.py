"""Application entrypoint: python -m app.main"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config.settings import settings
from app.config.logging_config import setup_logging, get_logger
from app.database.connection import init_db, get_session
from app.gui.theme import apply_theme
from app.gui.context import AppContext
from app.gui.windows.login import LoginDialog
from app.gui.windows.main_window import MainWindow
from app.security import session as sess
from app.security.auth import authenticate, logout
from app.services.platform_service import ensure_roles_permissions, get_setting
from app.i18n import set_language

log = get_logger("main")


def ensure_bootstrap() -> None:
    from app.database.models import User
    db = get_session()
    try:
        ensure_roles_permissions(db)
        if db.query(User).count() == 0:
            from app.services.platform_service import create_user
            create_user(db, None, "admin", "admin@immobiliare.local",
                        "Admin123!", "Amministratore", ["ADMIN"])
            log.info("Seeded default admin user")
    finally:
        db.close()


def run_gui() -> int:
    settings.ensure_dirs()
    setup_logging(logging.INFO)
    init_db()
    ensure_bootstrap()

    app = QApplication(sys.argv)
    # theme + language from settings db (fallback to env)
    db = get_session()
    try:
        theme = get_setting(db, "theme", settings.theme)
        lang = get_setting(db, "language", settings.language)
    finally:
        db.close()
    set_language(lang if lang in ("it", "en") else "it")
    apply_theme(app, theme if theme in ("light", "dark") else "light")

    current_uid: dict = {"id": None}

    def verify(u: str, p: str):
        db2 = get_session()
        try:
            user = authenticate(db2, u, p)
            current_uid["id"] = user.id
            sess.start_session(user.id, user.username,
                               timeout_min=settings.session_timeout_min)
        finally:
            db2.close()

    while True:
        dlg = LoginDialog(verify)
        if dlg.exec() == 0:
            return 0
        username = dlg.username

        def make_ctx():
            return AppContext(session_factory=get_session,
                              get_user_id=lambda: current_uid["id"])

        logged_out = {"v": False}

        def on_logout():
            db3 = get_session()
            try:
                from app.database.models import User
                u = db3.get(User, current_uid["id"]) if current_uid["id"] else None
                logout(db3, u)
            finally:
                db3.close()
            current_uid["id"] = None
            logged_out["v"] = True

        win = MainWindow(make_ctx(), username, on_logout)
        win.show()
        app.exec()
        if not logged_out["v"]:
            # window closed without logout -> treat as exit
            break
        # else: session expired / user logged out -> show login again
        if sess.get_session() is None and current_uid["id"] is None:
            continue
        break
    return 0


def main() -> None:
    try:
        raise SystemExit(run_gui())
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
