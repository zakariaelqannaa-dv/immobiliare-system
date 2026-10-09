"""Main window: sidebar + toolbar + stacked content + statusbar + session watchdog."""
from __future__ import annotations

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                               QStackedWidget, QToolBar, QStatusBar, QLabel, QMenu,
                               QPushButton, QApplication)
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QTimer

from app.config.settings import settings
from app.gui.context import AppContext
from app.gui.pages.dashboard import DashboardPage
from app.gui.pages.properties import PropertiesPage
from app.gui.pages.people import OwnersPage, ClientsPage, AgentsPage
from app.gui.pages.operations import (VisitsPage, CalendarPage, ContractsPage, SalesPage,
                                      RentalsPage, PaymentsPage, ExpensesPage)
from app.gui.pages.docs_tasks import DocumentsPage, TasksPage, NotificationsPage
from app.gui.pages.admin import ReportsPage, UsersPage, AuditPage, BackupPage, SettingsPage
from app.gui.helpers import info


NAV = [
    ("dashboard", "🏠 Cruscotto"),
    ("properties", "🏢 Immobili"),
    ("owners", "👤 Proprietari"),
    ("clients", "🤝 Clienti"),
    ("agents", "💼 Agenti"),
    ("visits", "👁 Visite"),
    ("calendar", "📅 Calendario"),
    ("contracts", "📝 Contratti"),
    ("rentals", "🔑 Locazioni"),
    ("sales", "💰 Vendite"),
    ("payments", "💳 Pagamenti"),
    ("expenses", "🧾 Spese"),
    ("documents", "📄 Documenti"),
    ("tasks", "✅ Attività"),
    ("reports", "📊 Report"),
    ("notifications", "🔔 Notifiche"),
    ("users", "👥 Utenti"),
    ("audit", "🛡 Audit log"),
    ("backup", "💾 Backup"),
    ("settings", "⚙ Impostazioni"),
]


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext, username: str, on_logout, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.username = username
        self.on_logout = on_logout
        self.setWindowTitle(f"Immobiliare System — {username}")
        self.resize(1380, 860)

        # toolbar
        tb = QToolBar("Main")
        self.addToolBar(tb)
        self.lbl_user = QLabel(f"👤 {username}")
        tb.addWidget(self.lbl_user)
        tb.addSeparator()
        act_theme = QAction("🌓 Tema", self)
        act_theme.setToolTip("Alterna tema chiaro/scuro")
        act_theme.triggered.connect(self.toggle_theme)
        tb.addAction(act_theme)
        act_logout = QAction("⏻ Esci", self)
        act_logout.triggered.connect(self._logout)
        tb.addAction(act_logout)

        # body
        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        side = QWidget(); side.setObjectName("Sidebar")
        slay = QVBoxLayout(side)
        self.nav = QListWidget()
        for _key, label in NAV:
            self.nav.addItem(label)
        self.nav.setToolTip("Navigazione moduli (Ctrl+1..9 per i primi, F5 aggiorna, Ctrl+F cerca)")
        side_title = QLabel("  IMMOBILIARE")
        side_title.setObjectName("SidebarLabel")
        slay.addWidget(side_title)
        slay.addWidget(self.nav, 1)
        lay.addWidget(side, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)

        self.pages: dict[str, QWidget] = {}
        self._add("dashboard", DashboardPage(ctx, on_goto=self.goto))
        self._add("properties", PropertiesPage(ctx))
        self._add("owners", OwnersPage(ctx))
        self._add("clients", ClientsPage(ctx))
        self._add("agents", AgentsPage(ctx))
        self._add("visits", VisitsPage(ctx))
        self._add("calendar", CalendarPage(ctx))
        self._add("contracts", ContractsPage(ctx))
        self._add("rentals", RentalsPage(ctx))
        self._add("sales", SalesPage(ctx))
        self._add("payments", PaymentsPage(ctx))
        self._add("expenses", ExpensesPage(ctx))
        self._add("documents", DocumentsPage(ctx))
        self._add("tasks", TasksPage(ctx))
        self._add("reports", ReportsPage(ctx))
        self._add("notifications", NotificationsPage(ctx))
        self._add("users", UsersPage(ctx))
        self._add("audit", AuditPage(ctx))
        self._add("backup", BackupPage(ctx))
        self._add("settings", SettingsPage(ctx))

        self.nav.currentRowChanged.connect(self._switch)

        # status bar (created before first switch)
        sb = QStatusBar()
        self.setStatusBar(sb)
        self.status_msg = QLabel("Pronto")
        sb.addWidget(self.status_msg, 1)
        self.nav.setCurrentRow(0)

        # shortcuts
        for i in range(min(9, len(NAV))):
            sc = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            sc.activated.connect(lambda _r=i: self.nav.setCurrentRow(_r))
        sc_refresh = QShortcut(QKeySequence.Refresh, self)  # F5
        sc_refresh.setAutoRepeat(False)
        sc_refresh.activated.connect(self.refresh_current)
        sc_find = QShortcut(QKeySequence.Find, self)  # Ctrl+F
        sc_find.activated.connect(self.focus_search)

        # session watchdog: global activity filter + expire check each 30s
        self.setMouseTracking(True)
        self._theme = "light"
        try:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        except Exception:
            pass
        self.watch = QTimer(self)
        self.watch.timeout.connect(self._check_session)
        self.watch.start(30_000)

    def _add(self, key: str, page: QWidget):
        self.pages[key] = page
        self.stack.addWidget(page)

    def goto(self, key: str):
        keys = [k for k, _ in NAV]
        if key in keys:
            self.nav.setCurrentRow(keys.index(key))

    def _switch(self, row: int):
        keys = [k for k, _ in NAV]
        if 0 <= row < len(keys):
            key = keys[row]
            page = self.pages[key]
            self.stack.setCurrentWidget(page)
            try:
                page.refresh()
                self.status_msg.setText(f"{key} — aggiornato")
            except Exception as e:
                self.status_msg.setText(f"Errore: {str(e)[:120]}")
            from app.security import session as sess
            sess.touch()

    def toggle_theme(self):
        from app.gui.theme import apply_theme
        self._theme = "dark" if self._theme == "light" else "light"
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self._theme)
        self.status_msg.setText(f"Tema: {self._theme}")

    def refresh_current(self):
        row = self.nav.currentRow()
        if row >= 0:
            self._switch(row)

    def focus_search(self):
        page = self.stack.currentWidget()
        bar = getattr(page, "search_bar", None) or getattr(page, "search", None)
        if bar is not None and hasattr(bar, "focus_search"):
            bar.focus_search()
            return
        # fallback: focus first QLineEdit in current page
        try:
            from PySide6.QtWidgets import QLineEdit
            le = page.findChild(QLineEdit)
            if le is not None:
                le.setFocus()
                le.selectAll()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            from PySide6.QtCore import QEvent
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress,
                                QEvent.Type.Wheel):
                from app.security import session as sess
                sess.touch()
        except Exception:
            pass
        return super().eventFilter(obj, event) if hasattr(super(), "eventFilter") else False

    def _check_session(self):
        from app.security import session as sess
        if sess.get_session() is None:
            info(self, "Sessione scaduta per inattività. Effettua di nuovo l'accesso.")
            self._logout()

    def mouseMoveEvent(self, e):
        from app.security import session as sess
        sess.touch()
        super().mouseMoveEvent(e)

    def keyPressEvent(self, e):
        from app.security import session as sess
        sess.touch()
        super().keyPressEvent(e)

    def _logout(self):
        self.on_logout()
        self.close()
