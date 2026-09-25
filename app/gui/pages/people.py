"""Owners / Clients (with matching + favorites) / Agents pages."""
from __future__ import annotations

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
                               QSpinBox, QTextEdit, QLabel, QListWidget, QSplitter)
from app.gui.helpers import fill_table, selected_id, confirm, error, success, info, gate
from app.gui.widgets import SearchBar
from app.services import people_service as ps
from app.services import platform_service as plat


class _Form(QDialog):
    def __init__(self, title, fields: list[tuple[str, object]], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        fl = QFormLayout(self)
        self._fields = {}
        for name, widget in fields:
            fl.addRow(name, widget)
            self._fields[name] = widget
        btns = QHBoxLayout()
        ok = QPushButton("Salva"); ok.clicked.connect(self.accept)
        ko = QPushButton("Annulla"); ko.setObjectName("Ghost"); ko.clicked.connect(self.reject)
        btns.addStretch(1); btns.addWidget(ok); btns.addWidget(ko)
        fl.addRow(btns)

    def val(self, name):
        w = self._fields[name]
        if isinstance(w, QLineEdit):
            return w.text().strip()
        if isinstance(w, QTextEdit):
            return w.toPlainText()
        if isinstance(w, QComboBox):
            return w.currentText()
        if isinstance(w, (QDoubleSpinBox, QSpinBox)):
            return w.value()
        return ""


class OwnersPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Proprietari</b>"))
        self.search = SearchBar(); self.search.searched.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_edit = QPushButton("Modifica"); self.b_edit.clicked.connect(self._edit)
        self.b_del = QPushButton("Disattiva"); self.b_del.setObjectName("Danger")
        self.b_del.clicked.connect(self._delete)
        for b in (self.b_new, self.b_edit, self.b_del):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("owners.edit"))
        db = self.ctx.db()
        try:
            rows = ps.list_owners(db, self.search.edit.text())
            fill_table(self.table, ["ID", "Nome", "Email", "Telefono", "Città"],
                       [[o.id, o.display_name, o.email, o.phone, o.city] for o in rows],
                       ids=[o.id for o in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _dialog(self, data=None):
        data = data or {}
        f = _Form("Proprietario", [
            ("Nome", QLineEdit(data.get("first_name", ""))),
            ("Cognome", QLineEdit(data.get("last_name", ""))),
            ("Società", QLineEdit(data.get("company_name", ""))),
            ("Email", QLineEdit(data.get("email", ""))),
            ("Telefono", QLineEdit(data.get("phone", ""))),
            ("Città", QLineEdit(data.get("city", ""))),
            ("Cod. fiscale", QLineEdit(data.get("fiscal_code", ""))),
            ("Note", QTextEdit(data.get("notes", ""))),
        ], self)
        return f

    def _new(self):
        d = self._dialog()
        if d.exec():
            db = self.ctx.db()
            try:
                ps.create_owner(db, self.ctx.current_user(), {
                    "first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                    "company_name": d.val("Società"), "email": d.val("Email"),
                    "phone": d.val("Telefono"), "city": d.val("Città"),
                    "fiscal_code": d.val("Cod. fiscale"), "notes": d.val("Note")})
                success(self, "Proprietario creato"); self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _edit(self):
        oid = selected_id(self.table)
        if oid is None:
            return
        db = self.ctx.db()
        try:
            from app.database.models import Owner
            o = db.get(Owner, oid)
            d = self._dialog({"first_name": o.first_name, "last_name": o.last_name,
                              "company_name": o.company_name, "email": o.email,
                              "phone": o.phone, "city": o.city,
                              "fiscal_code": o.fiscal_code, "notes": o.notes})
            if d.exec():
                ps.update_owner(db, self.ctx.current_user(), oid, {
                    "first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                    "company_name": d.val("Società"), "email": d.val("Email"),
                    "phone": d.val("Telefono"), "city": d.val("Città"),
                    "fiscal_code": d.val("Cod. fiscale"), "notes": d.val("Note")})
                self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _delete(self):
        oid = selected_id(self.table)
        if oid is None or not confirm(self, "Disattivare il proprietario?"):
            return
        db = self.ctx.db()
        try:
            ps.delete_owner(db, self.ctx.current_user(), oid)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class ClientsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Clienti + Matching</b>"))
        self.search = SearchBar(); self.search.searched.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_edit = QPushButton("Modifica"); self.b_edit.clicked.connect(self._edit)
        self.b_match = QPushButton("Trova immobili compatibili")
        self.b_match.clicked.connect(self._match)
        for b in (self.b_new, self.b_edit, self.b_match):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        sp = QSplitter()
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.matches = QListWidget()
        sp.addWidget(self.table); sp.addWidget(self.matches)
        lay.addWidget(sp, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("clients.edit"))
        db = self.ctx.db()
        try:
            rows = ps.list_clients(db, self.search.edit.text())
            fill_table(self.table, ["ID", "Nome", "Email", "Tipo", "Budget max", "Città desiderate"],
                       [[c.id, c.display_name, c.email, c.client_type, c.max_price,
                         c.desired_cities] for c in rows], ids=[c.id for c in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _dialog(self, data=None):
        data = data or {}
        tipo = QComboBox(); tipo.addItems(["buyer", "tenant", "both", "seller"])
        if data.get("client_type"):
            tipo.setCurrentText(data["client_type"])
        mx = QDoubleSpinBox(); mx.setMaximum(1e9); mx.setValue(float(data.get("max_price", 0) or 0))
        mn = QDoubleSpinBox(); mn.setMaximum(1e9); mn.setValue(float(data.get("min_price", 0) or 0))
        ms = QDoubleSpinBox(); ms.setMaximum(1e6); ms.setValue(float(data.get("min_surface", 0) or 0))
        rooms = QSpinBox(); rooms.setMaximum(60); rooms.setValue(int(data.get("desired_rooms", 0) or 0))
        return _Form("Cliente", [
            ("Nome", QLineEdit(data.get("first_name", ""))),
            ("Cognome", QLineEdit(data.get("last_name", ""))),
            ("Email", QLineEdit(data.get("email", ""))),
            ("Telefono", QLineEdit(data.get("phone", ""))),
            ("Tipo cliente", tipo),
            ("Tipo immobile", QLineEdit(data.get("desired_type", ""))),
            ("Budget min", mn), ("Budget max", mx),
            ("Sup. minima", ms), ("Locali desiderati", rooms),
            ("Città (separate da virgola)", QLineEdit(data.get("desired_cities", ""))),
            ("Requisiti", QTextEdit(data.get("requirements", ""))),
            ("Note", QTextEdit(data.get("notes", ""))),
        ], self), tipo, mx, mn, ms, rooms

    def _new(self):
        d, *_ = self._dialog()
        if d.exec():
            db = self.ctx.db()
            try:
                ps.create_client(db, self.ctx.current_user(), {
                    "first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                    "email": d.val("Email"), "phone": d.val("Telefono"),
                    "client_type": d.val("Tipo cliente"), "desired_type": d.val("Tipo immobile"),
                    "min_price": d.val("Budget min"), "max_price": d.val("Budget max"),
                    "min_surface": d.val("Sup. minima"), "desired_rooms": d.val("Locali desiderati"),
                    "desired_cities": d.val("Città (separate da virgola)"),
                    "requirements": d.val("Requisiti"), "notes": d.val("Note")})
                success(self, "Cliente creato"); self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _edit(self):
        cid = selected_id(self.table)
        if cid is None:
            return
        db = self.ctx.db()
        try:
            from app.database.models import Client
            c = db.get(Client, cid)
            d, *_ = self._dialog({"first_name": c.first_name, "last_name": c.last_name,
                                  "email": c.email, "phone": c.phone, "client_type": c.client_type,
                                  "desired_type": c.desired_type, "min_price": c.min_price,
                                  "max_price": c.max_price, "min_surface": c.min_surface,
                                  "desired_rooms": c.desired_rooms,
                                  "desired_cities": c.desired_cities,
                                  "requirements": c.requirements, "notes": c.notes})
            if d.exec():
                ps.update_client(db, self.ctx.current_user(), cid, {
                    "first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                    "email": d.val("Email"), "phone": d.val("Telefono"),
                    "client_type": d.val("Tipo cliente"), "desired_type": d.val("Tipo immobile"),
                    "min_price": d.val("Budget min"), "max_price": d.val("Budget max"),
                    "min_surface": d.val("Sup. minima"), "desired_rooms": d.val("Locali desiderati"),
                    "desired_cities": d.val("Città (separate da virgola)"),
                    "requirements": d.val("Requisiti"), "notes": d.val("Note")})
                self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _match(self):
        cid = selected_id(self.table)
        if cid is None:
            info(self, "Seleziona un cliente"); return
        db = self.ctx.db()
        try:
            res = plat.match_properties_for_client(db, cid)
            self.matches.clear()
            if not res:
                self.matches.addItem("Nessun immobile compatibile")
            for r in res:
                p = r["property"]
                self.matches.addItem(
                    f"[{r['score']:.0f}] {p.code} {p.city} €{p.price:,.0f} — {'; '.join(r['reasons'])}")
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class AgentsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Agenti</b>"))
        self.search = SearchBar(); self.search.searched.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_edit = QPushButton("Modifica"); self.b_edit.clicked.connect(self._edit)
        for b in (self.b_new, self.b_edit):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("agents.edit"))
        db = self.ctx.db()
        try:
            rows = ps.list_agents(db, self.search.edit.text())
            fill_table(self.table, ["ID", "Nome", "Email", "Telefono", "Provv. %"],
                       [[a.id, a.display_name, a.email, a.phone, a.commission_pct] for a in rows],
                       ids=[a.id for a in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        d = _Form("Agente", [("Nome", QLineEdit("")), ("Cognome", QLineEdit("")),
                             ("Email", QLineEdit("")), ("Telefono", QLineEdit(""))], self)
        if d.exec():
            db = self.ctx.db()
            try:
                ps.create_agent(db, self.ctx.current_user(),
                                {"first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                                 "email": d.val("Email"), "phone": d.val("Telefono")})
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _edit(self):
        aid = selected_id(self.table)
        if aid is None:
            return
        db = self.ctx.db()
        try:
            from app.database.models import Agent
            a = db.get(Agent, aid)
            d = _Form("Agente", [("Nome", QLineEdit(a.first_name)),
                                 ("Cognome", QLineEdit(a.last_name)),
                                 ("Email", QLineEdit(a.email)),
                                 ("Telefono", QLineEdit(a.phone))], self)
            if d.exec():
                ps.update_agent(db, self.ctx.current_user(), aid,
                                {"first_name": d.val("Nome"), "last_name": d.val("Cognome"),
                                 "email": d.val("Email"), "phone": d.val("Telefono")})
                self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()
