"""Secure login dialog."""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
                               QLabel, QHBoxLayout)
from PySide6.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, verify_fn, parent=None):
        super().__init__(parent)
        self.verify_fn = verify_fn
        self.username = ""
        self.password = ""
        self.setWindowTitle("Immobiliare System — Accedi")
        self.setModal(True)
        self.resize(380, 220)
        lay = QVBoxLayout(self)
        t = QLabel("<h2>Immobiliare System</h2>")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)
        fl = QFormLayout()
        self.e_user = QLineEdit()
        self.e_user.setPlaceholderText("Nome utente o email")
        self.e_pass = QLineEdit()
        self.e_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.e_pass.setPlaceholderText("Password")
        fl.addRow("Utente", self.e_user)
        fl.addRow("Password", self.e_pass)
        lay.addLayout(fl)
        self.err = QLabel("")
        self.err.setStyleSheet("color:#c0392b;")
        self.err.setWordWrap(True)
        lay.addWidget(self.err)
        row = QHBoxLayout()
        b = QPushButton("Accedi")
        b.setDefault(True)
        b.clicked.connect(self._go)
        row.addStretch(1); row.addWidget(b)
        lay.addLayout(row)
        self.e_pass.returnPressed.connect(self._go)

    def _go(self):
        u, p = self.e_user.text().strip(), self.e_pass.text()
        if not u or not p:
            self.err.setText("Inserisci utente e password")
            return
        try:
            self.verify_fn(u, p)
        except Exception as e:
            self.err.setText(str(e)[:300])
            return
        self.username = u
        self.password = p
        self.accept()
