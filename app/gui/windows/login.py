"""Secure login dialog."""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
                               QLabel, QHBoxLayout, QApplication, QToolButton)
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, verify_fn, parent=None):
        super().__init__(parent)
        self.verify_fn = verify_fn
        self.username = ""
        self.setWindowTitle("Immobiliare System — Accedi")
        self.setModal(True)
        self.resize(420, 260)
        self.setMinimumSize(420, 260)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)
        t = QLabel("Immobiliare System")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 20px; font-weight: bold;")
        lay.addWidget(t)
        sub = QLabel("Gestione immobiliare professionale")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setObjectName("CardTitle")
        lay.addWidget(sub)
        fl = QFormLayout()
        self.e_user = QLineEdit()
        self.e_user.setPlaceholderText("Nome utente o email")
        self.e_pass = QLineEdit()
        self.e_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.e_pass.setPlaceholderText("Password")
        self.btn_show = QToolButton()
        self.btn_show.setText("👁")
        self.btn_show.setCheckable(True)
        self.btn_show.setToolTip("Mostra/nascondi password")
        self.btn_show.toggled.connect(self._toggle_pw)
        pw_row = QHBoxLayout()
        pw_row.addWidget(self.e_pass, 1)
        pw_row.addWidget(self.btn_show)
        fl.addRow("Utente", self.e_user)
        fl.addRow("Password", pw_row)
        lay.addLayout(fl)
        self.err = QLabel("")
        self.err.setObjectName("LoginError")
        self.err.setWordWrap(True)
        lay.addWidget(self.err)
        row = QHBoxLayout()
        self.b_login = QPushButton("Accedi")
        self.b_login.setDefault(True)
        self.b_login.clicked.connect(self._go)
        row.addStretch(1); row.addWidget(self.b_login)
        lay.addLayout(row)
        self.e_user.returnPressed.connect(self._go)
        self.e_pass.returnPressed.connect(self._go)

    def _toggle_pw(self, checked: bool):
        self.e_pass.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)

    def _go(self):
        u, p = self.e_user.text().strip(), self.e_pass.text()
        if not u or not p:
            self.err.setText("Inserisci utente e password")
            (self.e_user if not u else self.e_pass).setFocus()
            return
        self.b_login.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.verify_fn(u, p)
        except Exception as e:
            self.err.setText(str(e)[:300])
            return
        finally:
            try:
                QApplication.restoreOverrideCursor()
            except Exception:
                pass
            self.b_login.setEnabled(True)
            try:
                self.e_pass.clear()
            except Exception:
                pass
        self.username = u
        self.accept()
