"""Base page + Dashboard page."""
from __future__ import annotations

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QListWidget,
                               QHBoxLayout, QPushButton)
from app.gui.widgets import StatCard
from app.gui.helpers import error
from app.services import platform_service as plat
from app.utils.formatting import money


class BasePage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx

    def refresh(self) -> None:
        pass


class DashboardPage(BasePage):
    def __init__(self, ctx, on_goto=None, parent=None):
        super().__init__(ctx, parent)
        self.on_goto = on_goto or (lambda _name: None)
        lay = QVBoxLayout(self)
        title = QLabel("Cruscotto"); title.setStyleSheet("font-size:20px;font-weight:bold;")
        lay.addWidget(title)
        self.grid = QGridLayout()
        lay.addLayout(self.grid)
        self.cards: dict[str, StatCard] = {}
        defs = ["Immobili totali", "Disponibili", "In vendita", "In locazione",
                "Venduti", "Locati", "Clienti attivi", "Visite imminenti",
                "Pagamenti pending", "Pagamenti in ritardo", "Ricavi mese", "Spese mese"]
        for i, name in enumerate(defs):
            c = StatCard(name)
            self.cards[name] = c
            self.grid.addWidget(c, i // 4, i % 4)
        mid = QHBoxLayout()
        self.recent = QListWidget()
        self.appts = QListWidget()
        self.props = QListWidget()
        for w, t in ((self.recent, "Attività recente"), (self.appts, "Prossimi appuntamenti"),
                     (self.props, "Immobili recenti")):
            box = QVBoxLayout()
            box.addWidget(QLabel(f"<b>{t}</b>"))
            box.addWidget(w)
            mid.addLayout(box)
        lay.addLayout(mid, 1)
        btns = QHBoxLayout()
        for key, label in (("properties", "Vai a Immobili"), ("payments", "Vai a Pagamenti"),
                           ("reports", "Vai a Report")):
            b = QPushButton(label); b.setObjectName("Ghost")
            b.clicked.connect(lambda _=False, k=key: self.on_goto(k))
            btns.addWidget(b)
        btns.addStretch(1)
        lay.addLayout(btns)

    def refresh(self) -> None:
        db = self.ctx.db()
        try:
            s = plat.dashboard_stats(db)
            mapping = {"Immobili totali": s["total"], "Disponibili": s["available"],
                       "In vendita": s["sale"], "In locazione": s["rent"],
                       "Venduti": s["sold"], "Locati": s["rented"],
                       "Clienti attivi": s["clients"], "Visite imminenti": s["upcoming_visits"],
                       "Pagamenti pending": s["pending_payments"],
                       "Pagamenti in ritardo": s["late_payments"],
                       "Ricavi mese": money(s["revenue"]), "Spese mese": money(s["expenses"])}
            for k, v in mapping.items():
                self.cards[k].set_value(str(v))
            self.recent.clear()
            for a in plat.recent_activity(db, 12):
                self.recent.addItem(f"{a.at:%d/%m %H:%M} · {a.username} · {a.action} {a.entity}")
            self.appts.clear()
            for a in plat.upcoming_appointments(db, 12):
                self.appts.addItem(f"{a.starts_at:%d/%m %H:%M} · {a.title}")
            self.props.clear()
            for p in plat.recent_properties(db, 12):
                self.props.addItem(f"{p.code} · {p.city} · {money(p.price)}")
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()
