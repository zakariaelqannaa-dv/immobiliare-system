"""Reports / Users / Audit / Backup / Settings pages."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                               QComboBox, QLabel, QFileDialog, QLineEdit, QFormLayout, QDialog,
                               QCheckBox, QListWidget, QTextEdit)
from app.config.settings import settings
from app.gui.helpers import fill_table, selected_id, confirm, error, success, info, gate
from app.services import platform_service as plat
from app.reports.generator import build_pdf
from app.utils.export import export_csv, export_excel


class ReportsPage(QWidget):
    KINDS = ["inventory", "sales", "rentals", "payments_due", "revenue",
             "expenses", "owner_statement", "agent_commissions", "monthly"]

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Report</b>"))
        row = QHBoxLayout()
        self.kind = QComboBox(); self.kind.addItems(self.KINDS)
        b_run = QPushButton("Esegui"); b_run.clicked.connect(self.refresh)
        b_pdf = QPushButton("Esporta PDF"); b_pdf.clicked.connect(lambda: self._export("pdf"))
        b_xls = QPushButton("Esporta Excel"); b_xls.clicked.connect(lambda: self._export("xlsx"))
        b_csv = QPushButton("Esporta CSV"); b_csv.clicked.connect(lambda: self._export("csv"))
        for w in (self.kind, b_run, b_pdf, b_xls, b_csv):
            row.addWidget(w)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        lay.addWidget(self.table, 1)
        self._headers: list[str] = []
        self._rows: list[list] = []

    def refresh(self):
        if not self.ctx.can("reports.view"):
            error(self, "Permesso mancante: reports.view"); return
        db = self.ctx.db()
        try:
            h, r = plat.report_dataset(db, self.kind.currentText())
            self._headers, self._rows = h, r
            fill_table(self.table, h, r)
            # audit export-view
            from app.repositories.audit import record as rec
            rec(db, self.ctx.current_user(), "export", "report",
                self.kind.currentText(), new={"rows": len(r)})
            db.commit()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _export(self, fmt: str):
        if not self._headers:
            info(self, "Esegui prima il report"); return
        f, _ = QFileDialog.getSaveFileName(self, "Salva report", f"report.{fmt}")
        if not f:
            return
        try:
            if fmt == "pdf":
                build_pdf(f, f"Report {self.kind.currentText()}", self._headers, self._rows)
            elif fmt == "xlsx":
                export_excel(f, self._headers, self._rows)
            else:
                export_csv(f, self._headers, self._rows)
            db = self.ctx.db()
            try:
                from app.repositories.audit import record as rec
                rec(db, self.ctx.current_user(), "export", "report",
                    self.kind.currentText(), new={"file": f})
                db.commit()
            finally:
                db.close()
            success(self, f"Report salvato: {f}")
        except Exception as e:
            error(self, str(e))


class UsersPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Utenti e ruoli</b>"))
        row = QHBoxLayout()
        self.b_new = QPushButton("Nuovo utente"); self.b_new.clicked.connect(self._new)
        self.b_dis = QPushButton("Abilita/Disabilita"); self.b_dis.clicked.connect(self._toggle)
        self.b_role = QPushButton("Assegna ruolo"); self.b_role.clicked.connect(self._role)
        for b in (self.b_new, self.b_dis, self.b_role):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.table, 1)

    def refresh(self):
        gate(self.b_new, self.ctx.can("users.manage"))
        db = self.ctx.db()
        try:
            rows = plat.list_users(db)
            fill_table(self.table, ["ID", "Username", "Email", "Nome", "Abilitato", "Ruoli"],
                       [[u.id, u.username, u.email, u.full_name,
                         "sì" if u.is_enabled else "no",
                         ",".join(r.name for r in u.roles)] for u in rows],
                       ids=[u.id for u in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _new(self):
        dlg = QDialog(self); dlg.setWindowTitle("Nuovo utente")
        fl = QFormLayout(dlg)
        e_u = QLineEdit(); e_e = QLineEdit(); e_p = QLineEdit(); e_p.setEchoMode(QLineEdit.EchoMode.Password)
        e_n = QLineEdit(); e_r = QComboBox(); e_r.addItems(["VIEWER", "AGENT", "ACCOUNTANT", "MANAGER", "ADMIN"])
        for k, w in [("Username", e_u), ("Email", e_e), ("Password", e_p),
                     ("Nome", e_n), ("Ruolo", e_r)]:
            fl.addRow(k, w)
        ok = QPushButton("Crea"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                plat.create_user(db, self.ctx.current_user(), e_u.text(), e_e.text(),
                                 e_p.text(), e_n.text(), [e_r.currentText()])
                success(self, "Utente creato"); self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()

    def _toggle(self):
        uid = selected_id(self.table)
        if uid is None:
            return
        db = self.ctx.db()
        try:
            from app.database.models import User
            u = db.get(User, uid)
            plat.set_user_enabled(db, self.ctx.current_user(), uid, not u.is_enabled)
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _role(self):
        uid = selected_id(self.table)
        if uid is None:
            return
        dlg = QDialog(self); dlg.setWindowTitle("Ruolo")
        fl = QFormLayout(dlg)
        e_r = QComboBox(); e_r.addItems(["VIEWER", "AGENT", "ACCOUNTANT", "MANAGER", "ADMIN"])
        fl.addRow("Ruolo", e_r)
        ok = QPushButton("Salva"); ok.clicked.connect(dlg.accept)
        fl.addRow(ok)
        if dlg.exec():
            db = self.ctx.db()
            try:
                plat.set_user_roles(db, self.ctx.current_user(), uid, [e_r.currentText()])
                self.refresh()
            except Exception as e:
                error(self, str(e))
            finally:
                db.close()


class AuditPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Registro audit</b>"))
        self.table = QTableWidget()
        lay.addWidget(self.table, 1)

    def refresh(self):
        if not self.ctx.can("audit.view"):
            error(self, "Permesso mancante: audit.view"); return
        db = self.ctx.db()
        try:
            rows = plat.recent_activity(db, 500)
            fill_table(self.table, ["ID", "Quando", "Utente", "Azione", "Entità", "Esito"],
                       [[a.id, a.at.strftime("%d/%m %H:%M"), a.username,
                         a.action, f"{a.entity}/{a.entity_id}", a.result] for a in rows])
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()


class BackupPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Backup / Ripristino</b>"))
        row = QHBoxLayout()
        self.b_go = QPushButton("Esegui backup"); self.b_go.clicked.connect(self._backup)
        self.b_re = QPushButton("Ripristina selezionato"); self.b_re.setObjectName("Danger")
        self.b_re.clicked.connect(self._restore)
        self.c_enc = QCheckBox("Cifra backup")
        for w in (self.b_go, self.b_re, self.c_enc):
            row.addWidget(w)
        row.addStretch(1)
        lay.addLayout(row)
        self.list = QListWidget()
        lay.addWidget(self.list, 1)

    def refresh(self):
        gate(self.b_go, self.ctx.can("backups.manage"))
        self.list.clear()
        try:
            for p in sorted(settings.backup_dir.glob("immobiliare_*"), reverse=True):
                ok = plat.verify_backup(p)
                self.list.addItem(f"{p.name} — {p.stat().st_size // 1024} KB — "
                                  f"{'valido' if ok else 'NON VALIDO'}")
        except Exception as e:
            error(self, str(e))

    def _backup(self):
        db = self.ctx.db()
        try:
            rec = plat.create_backup(db, self.ctx.current_user(), encrypt=self.c_enc.isChecked())
            success(self, f"Backup creato: {rec.filename}")
            self.refresh()
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()

    def _restore(self):
        it = self.list.currentItem()
        if it is None:
            info(self, "Seleziona un backup"); return
        name = it.text().split(" — ")[0]
        if not confirm(self, f"Ripristinare {name}? L'operazione sostituisce il database."):
            return
        db = self.ctx.db()
        try:
            plat.restore_backup(db, self.ctx.current_user(), name)
            success(self, "Ripristino completato. Riavvia l'applicazione.")
        except Exception as e:
            error(self, str(e))
        finally:
            try:
                db.close()
            except Exception:
                pass


class SettingsPage(QWidget):
    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("<b>Impostazioni</b>"))
        fl = QFormLayout()
        self.e_company = QLineEdit()
        self.e_lang = QComboBox(); self.e_lang.addItems(["it", "en"])
        self.e_theme = QComboBox(); self.e_theme.addItems(["light", "dark"])
        fl.addRow("Azienda", self.e_company)
        fl.addRow("Lingua", self.e_lang)
        fl.addRow("Tema", self.e_theme)
        lay.addLayout(fl)
        b = QPushButton("Salva"); b.clicked.connect(self._save)
        lay.addWidget(b)
        lay.addStretch(1)

    def refresh(self):
        db = self.ctx.db()
        try:
            self.e_company.setText(plat.get_setting(db, "company_name", settings.company_name))
            self.e_lang.setCurrentText(plat.get_setting(db, "language", "it"))
            self.e_theme.setCurrentText(plat.get_setting(db, "theme", "light"))
        finally:
            db.close()

    def _save(self):
        db = self.ctx.db()
        try:
            u = self.ctx.current_user()
            plat.set_setting(db, u, "company_name", self.e_company.text())
            plat.set_setting(db, u, "language", self.e_lang.currentText())
            plat.set_setting(db, u, "theme", self.e_theme.currentText())
            success(self, "Impostazioni salvate (il tema si applica al riavvio o dal menu)")
        except Exception as e:
            error(self, str(e))
        finally:
            db.close()
