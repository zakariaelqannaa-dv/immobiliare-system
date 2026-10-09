"""Visits / Calendar / Contracts(+Sales/Rentals) / Payments / Expenses pages."""
from __future__ import annotations

from datetime import date, datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
                               QTextEdit, QLabel, QDateEdit, QDateTimeEdit)
from PySide6.QtCore import QDate, QDateTime
from app.gui.helpers import fill_table, selected_id, confirm, error, success, info, gate, style_table
from app.gui.widgets import SearchBar
from app.services import schedule_service as sch
from app.services import deal_service as deal
from app.utils.formatting import money, fmt_date


def _qdate(d) -> QDate:
    if isinstance(d, datetime):
        d = d.date()
    if isinstance(d, date):
        return QDate(d.year, d.month, d.day)
    return QDate.currentDate()


class VisitsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Visite</b>"))
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuova visita"); self.b_new.clicked.connect(self._new)
        self.b_conf = QPushButton("Conferma"); self.b_conf.clicked.connect(lambda: self._st("confirmed"))
        self.b_done = QPushButton("Completata"); self.b_done.clicked.connect(lambda: self._st("completed"))
        self.b_canc = QPushButton("Annulla"); self.b_canc.setObjectName("Danger")
        self.b_canc.clicked.connect(lambda: self._st("cancelled"))
        for b in (self.b_new, self.b_conf, self.b_done, self.b_canc):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("visits.edit"))
        db = self.ctx.db()
        try:
            rows = sch.list_visits(db)
            fill_table(self.table, ["ID", "Immobile", "Cliente", "Quando", "Stato"],
                       [[v.id, v.property_id, v.client_id,
                         v.scheduled_at.strftime("%d/%m/%Y %H:%M"), v.status.value] for v in rows],
                       ids=[v.id for v in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Nuova visita")
        fl = QFormLayout(dlg)
        e_prop = QLineEdit(); e_prop.setPlaceholderText("ID immobile")
        e_cli = QLineEdit(); e_cli.setPlaceholderText("ID cliente")
        e_agent = QLineEdit(); e_agent.setPlaceholderText("ID agente (opz.)")
        e_when = QDateTimeEdit(QDateTime.currentDateTime()); e_when.setCalendarPopup(True)
        e_notes = QTextEdit()
        for k, w in [("Immobile ID", e_prop), ("Cliente ID", e_cli), ("Agente ID", e_agent),
                     ("Data/ora", e_when), ("Note", e_notes)]:
            fl.addRow(k, w)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                sch.create_visit(db, self.ctx.current_user(), {
                    "property_id": int(e_prop.text()), "client_id": int(e_cli.text()),
                    "agent_id": int(e_agent.text()) if e_agent.text().strip() else None,
                    "scheduled_at": e_when.dateTime().toPython(),
                    "notes": e_notes.toPlainText()})
                success(self, "Visita creata"); self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _st(self, st: str):
        vid = selected_id(self.table)
        if vid is None:
            return
        db = self.ctx.db()
        try:
            sch.set_visit_status(db, self.ctx.current_user(), vid, st)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class CalendarPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Calendario / Appuntamenti</b>"))
        row = QHBoxLayout()
        b_new = QPushButton("Nuovo appuntamento"); b_new.clicked.connect(self._new)
        b_done = QPushButton("Segna svolto"); b_done.clicked.connect(self._done)
        b_del = QPushButton("Elimina"); b_del.setObjectName("Danger"); b_del.clicked.connect(self._del)
        for b in (b_new, b_done, b_del):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        db = self.ctx.db()
        try:
            rows = sch.list_appointments(db)
            fill_table(self.table, ["ID", "Titolo", "Tipo", "Inizio", "Svolto"],
                       [[a.id, a.title, a.atype.value,
                         a.starts_at.strftime("%d/%m/%Y %H:%M"), "sì" if a.is_done else "no"]
                        for a in rows], ids=[a.id for a in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Appuntamento")
        fl = QFormLayout(dlg)
        e_t = QLineEdit(); e_ty = QComboBox()
        e_ty.addItems(["visit", "meeting", "contract_deadline", "payment_deadline",
                       "task", "reminder", "other"])
        e_when = QDateTimeEdit(QDateTime.currentDateTime()); e_when.setCalendarPopup(True)
        e_notes = QTextEdit()
        for k, w in [("Titolo", e_t), ("Tipo", e_ty), ("Inizio", e_when), ("Note", e_notes)]:
            fl.addRow(k, w)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                sch.create_appointment(db, self.ctx.current_user(), {
                    "title": e_t.text(), "atype": e_ty.currentText(),
                    "starts_at": e_when.dateTime().toPython(), "notes": e_notes.toPlainText()})
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _done(self):
        aid = selected_id(self.table)
        if aid is None:
            return
        db = self.ctx.db()
        try:
            sch.complete_appointment(db, self.ctx.current_user(), aid, True)
            self.refresh()
        finally:
            db.close()

    def _del(self):
        aid = selected_id(self.table)
        if aid is None or not confirm(self, "Eliminare l'appuntamento?"):
            return
        db = self.ctx.db()
        try:
            sch.delete_appointment(db, self.ctx.current_user(), aid)
            self.refresh()
        finally:
            db.close()


class ContractsPage(QWidget):
    kind_filter = ""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        self.lbl = QLabel("<b>Contratti</b>")
        lay.addWidget(self.lbl)
        self.search = SearchBar("Cerca numero contratto..."); self.search.searched.connect(lambda _t: self.refresh())
        lay.addWidget(self.search)
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_act = QPushButton("Attiva"); self.b_act.clicked.connect(lambda: self._st("active"))
        self.b_end = QPushButton("Termina"); self.b_end.clicked.connect(lambda: self._st("terminated"))
        for b in (self.b_new, self.b_act, self.b_end):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("contracts.create"))
        db = self.ctx.db()
        try:
            rows = deal.list_contracts(db, self.kind_filter, self.search.edit.text())
            fill_table(self.table, ["ID", "Numero", "Tipo", "Immobile", "Cliente", "Prezzo", "Stato"],
                       [[c.id, c.number, c.ctype.value, c.property_id, c.client_id,
                         money(c.price), c.status.value] for c in rows],
                       ids=[c.id for c in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Nuovo contratto")
        fl = QFormLayout(dlg)
        e_num = QLineEdit(f"C-{datetime.now():%Y%m%d%H%M}")
        e_ty = QComboBox(); e_ty.addItems(["rental", "sale"])
        if self.kind_filter:
            e_ty.setCurrentText(self.kind_filter)
        e_prop = QLineEdit(); e_cli = QLineEdit(); e_price = QDoubleSpinBox()
        e_price.setMaximum(1e9)
        e_start = QDateEdit(QDate.currentDate()); e_start.setCalendarPopup(True)
        for k, w in [("Numero", e_num), ("Tipo", e_ty), ("Immobile ID", e_prop),
                     ("Cliente ID", e_cli), ("Prezzo", e_price), ("Inizio", e_start)]:
            fl.addRow(k, w)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                deal.create_contract(db, self.ctx.current_user(), {
                    "number": e_num.text().strip(), "ctype": e_ty.currentText(),
                    "property_id": int(e_prop.text()), "client_id": int(e_cli.text()),
                    "price": float(e_price.value()),
                    "start_date": e_start.date().toPython(), "status": "draft"})
                success(self, "Contratto creato"); self.refresh()
            except Exception as e:
                try:
                    db.rollback()
                except Exception:
                    pass
                error(self, str(e))
            finally:
                db.close()

    def _st(self, st: str):
        cid = selected_id(self.table)
        if cid is None:
            return
        db = self.ctx.db()
        try:
            deal.set_contract_status(db, self.ctx.current_user(), cid, st)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class SalesPage(ContractsPage):
    kind_filter = "sale"

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.lbl.setText("<b>Vendite</b>")


class RentalsPage(ContractsPage):
    kind_filter = "rental"

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.lbl.setText("<b>Locazioni</b>")


class PaymentsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Pagamenti</b>"))
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo"); self.b_new.clicked.connect(self._new)
        self.b_paid = QPushButton("Segna pagato"); self.b_paid.clicked.connect(lambda: self._st("paid"))
        self.b_canc = QPushButton("Annulla"); self.b_canc.setObjectName("Danger")
        self.b_canc.clicked.connect(lambda: self._st("cancelled"))
        self.f_status = QComboBox(); self.f_status.addItems(["", "pending", "paid", "late", "cancelled"])
        self.f_status.currentTextChanged.connect(lambda _t: self.refresh())
        for b in (self.b_new, self.b_paid, self.b_canc):
            row.addWidget(b)
        row.addWidget(QLabel("Stato:")); row.addWidget(self.f_status); row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("payments.edit"))
        db = self.ctx.db()
        try:
            deal.refresh_late(db)
            rows = deal.list_payments(db, self.f_status.currentText())
            fill_table(self.table, ["ID", "Contratto", "Importo", "Scadenza", "Stato", "Rif."],
                       [[p.id, p.contract_id, money(p.amount), fmt_date(p.due_date),
                         p.status.value, p.reference or "—"] for p in rows],
                       ids=[p.id for p in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Nuovo pagamento")
        fl = QFormLayout(dlg)
        e_c = QLineEdit(); e_c.setPlaceholderText("ID contratto (opz.)")
        e_a = QDoubleSpinBox(); e_a.setMaximum(1e9)
        e_d = QDateEdit(QDate.currentDate()); e_d.setCalendarPopup(True)
        e_r = QLineEdit(); e_m = QComboBox()
        e_m.addItems(["transfer", "cash", "card", "check", "other"])
        for k, w in [("Contratto ID", e_c), ("Importo", e_a), ("Scadenza", e_d),
                     ("Riferimento", e_r), ("Metodo", e_m)]:
            fl.addRow(k, w)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                deal.create_payment(db, self.ctx.current_user(), {
                    "contract_id": int(e_c.text()) if e_c.text().strip() else None,
                    "amount": float(e_a.value()), "due_date": e_d.date().toPython(),
                    "reference": e_r.text().strip(), "method": e_m.currentText()})
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _st(self, st: str):
        pid = selected_id(self.table)
        if pid is None:
            return
        db = self.ctx.db()
        try:
            deal.set_payment_status(db, self.ctx.current_user(), pid, st)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class ExpensesPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Spese</b>"))
        row = QHBoxLayout()
        b_new = QPushButton("Nuova spesa"); b_new.clicked.connect(self._new)
        b_del = QPushButton("Elimina"); b_del.setObjectName("Danger"); b_del.clicked.connect(self._del)
        row.addWidget(b_new); row.addWidget(b_del); row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        db = self.ctx.db()
        try:
            rows = deal.list_expenses(db)
            fill_table(self.table, ["ID", "Immobile", "Categoria", "Importo", "Data"],
                       [[e.id, e.property_id, e.category, money(e.amount), fmt_date(e.date)]
                        for e in rows], ids=[e.id for e in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Nuova spesa")
        fl = QFormLayout(dlg)
        e_p = QLineEdit(); e_c = QComboBox()
        e_c.addItems(["maintenance", "condo", "tax", "insurance", "utilities", "commission", "other"])
        e_a = QDoubleSpinBox(); e_a.setMaximum(1e9)
        e_d = QDateEdit(QDate.currentDate()); e_d.setCalendarPopup(True)
        e_des = QTextEdit()
        for k, w in [("Immobile ID", e_p), ("Categoria", e_c), ("Importo", e_a),
                     ("Data", e_d), ("Descrizione", e_des)]:
            fl.addRow(k, w)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                deal.create_expense(db, self.ctx.current_user(), {
                    "property_id": int(e_p.text()) if e_p.text().strip() else None,
                    "category": e_c.currentText(), "amount": float(e_a.value()),
                    "date": e_d.date().toPython(), "description": e_des.toPlainText()})
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _del(self):
        eid = selected_id(self.table)
        if eid is None or not confirm(self, "Eliminare la spesa?"):
            return
        db = self.ctx.db()
        try:
            deal.delete_expense(db, self.ctx.current_user(), eid)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()
