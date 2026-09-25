"""Documents / Tasks / Notifications pages."""
from __future__ import annotations

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                               QDialog, QFormLayout, QLineEdit, QComboBox, QLabel, QFileDialog,
                               QTextEdit)
from app.gui.helpers import fill_table, selected_id, confirm, error, success, info
from app.services import platform_service as plat
from app.services import schedule_service as sch


class DocumentsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Documenti</b>"))
        row = QHBoxLayout()
        b_add = QPushButton("Carica documento"); b_add.clicked.connect(self._add)
        b_del = QPushButton("Elimina"); b_del.setObjectName("Danger"); b_del.clicked.connect(self._del)
        row.addWidget(b_add); row.addWidget(b_del); row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        db = self.ctx.db()
        try:
            rows = plat.list_documents(db)
            fill_table(self.table, ["ID", "Entità", "Nome originale", "Categoria", "Bytes"],
                       [[d.id, f"{d.owner_type}/{d.owner_id}", d.original_name,
                         d.category, d.size_bytes] for d in rows],
                       ids=[d.id for d in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _add(self):
        f, _ = QFileDialog.getOpenFileName(self, "Seleziona documento")
        if not f:
            return
        dlg = QDialog(self); dlg.setWindowTitle("Associa documento")
        fl = QFormLayout(dlg)
        e_t = QComboBox(); e_t.addItems(["property", "owner", "client", "contract", "payment"])
        e_id = QLineEdit("1"); e_cat = QComboBox()
        e_cat.addItems(["general", "id", "contract", "invoice", "receipt", "certification"])
        fl.addRow("Entità", e_t); fl.addRow("ID entità", e_id); fl.addRow("Categoria", e_cat)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                plat.add_document(db, self.ctx.current_user(), e_t.currentText(),
                                  int(e_id.text()), f, e_cat.currentText())
                success(self, "Documento salvato"); self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _del(self):
        did = selected_id(self.table)
        if did is None or not confirm(self, "Eliminare il documento?"):
            return
        db = self.ctx.db()
        try:
            plat.delete_document(db, self.ctx.current_user(), did)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class TasksPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Attività</b>"))
        row = QHBoxLayout()
        b_new = QPushButton("Nuova"); b_new.clicked.connect(self._new)
        b_done = QPushButton("Completa"); b_done.clicked.connect(lambda: self._st("done"))
        row.addWidget(b_new); row.addWidget(b_done); row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        db = self.ctx.db()
        try:
            rows = sch.list_tasks(db)
            fill_table(self.table, ["ID", "Titolo", "Scadenza", "Stato", "Priorità"],
                       [[t.id, t.title, str(t.due_at or ""), t.status.value, t.priority]
                        for t in rows], ids=[t.id for t in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Attività")
        fl = QFormLayout(dlg)
        e_t = QLineEdit(); e_d = QTextEdit()
        fl.addRow("Titolo", e_t); fl.addRow("Descrizione", e_d)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                sch.create_task(db, self.ctx.current_user(),
                                {"title": e_t.text(), "description": e_d.toPlainText()})
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _st(self, st: str):
        tid = selected_id(self.table)
        if tid is None:
            return
        db = self.ctx.db()
        try:
            sch.set_task_status(db, self.ctx.current_user(), tid, st)
            self.refresh()
        finally:
            db.close()


class NotificationsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Notifiche</b>"))
        row = QHBoxLayout()
        b_read = QPushButton("Segna letta"); b_read.clicked.connect(self._read)
        row.addWidget(b_read); row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        db = self.ctx.db()
        try:
            u = self.ctx.current_user()
            rows = sch.list_notifications(db, u.id if u else None)
            fill_table(self.table, ["ID", "Titolo", "Letta", "Data"],
                       [[n.id, n.title, "sì" if n.is_read else "no",
                         n.created_at.strftime("%d/%m %H:%M")] for n in rows],
                       ids=[n.id for n in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _read(self):
        nid = selected_id(self.table)
        if nid is None:
            return
        db = self.ctx.db()
        try:
            sch.mark_read(db, nid)
            self.refresh()
        finally:
            db.close()
