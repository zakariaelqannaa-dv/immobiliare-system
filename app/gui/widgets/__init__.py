"""Reusable widgets: StatCard, SearchBar, EmptyState, Gallery."""
from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QListWidget, QListWidgetItem, QScrollArea,
                               QGridLayout, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        t = QLabel(title); t.setObjectName("CardTitle")
        t.setWordWrap(True)
        self.val = QLabel(value); self.val.setObjectName("CardValue")
        lay.addWidget(t); lay.addWidget(self.val)

    def set_value(self, v: str) -> None:
        self.val.setText(v)


class SearchBar(QWidget):
    searched = Signal(str)

    def __init__(self, placeholder: str = "Cerca...", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setToolTip("Invio per cercare")
        self.edit.setClearButtonEnabled(True)
        btn = QPushButton("Cerca")
        btn.clicked.connect(lambda: self.searched.emit(self.edit.text()))
        self.edit.returnPressed.connect(lambda: self.searched.emit(self.edit.text()))
        lay.addWidget(self.edit, 1)
        lay.addWidget(btn)

    def text(self) -> str:
        return self.edit.text()

    def set_text(self, v: str) -> None:
        self.edit.setText(v)

    def focus_search(self) -> None:
        self.edit.setFocus()
        self.edit.selectAll()


class EmptyState(QLabel):
    def __init__(self, text: str = "Nessun dato", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(64)


class Gallery(QWidget):
    primary_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.inner = QWidget()
        self.grid = QGridLayout(self.inner)
        self.scroll.setWidget(self.inner)
        lay = QVBoxLayout(self)
        lay.addWidget(self.scroll)
        self._items: list[tuple[int, str, bool]] = []

    def set_images(self, items: list[tuple[int, str, bool]]) -> None:
        self._items = items
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not items:
            self.grid.addWidget(EmptyState("Nessuna foto — usa Aggiungi per caricare immagini"))
            return
        for i, (img_id, path, primary) in enumerate(items):
            cell = QFrame()
            cell.setObjectName("Card")
            vl = QVBoxLayout(cell)
            vl.setContentsMargins(8, 8, 8, 8)
            vl.setSpacing(6)
            lab = QLabel()
            lab.setFixedSize(160, 120)
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb = path if Path(path).exists() else ""
            if thumb:
                pm = QPixmap(thumb).scaled(160, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                lab.setPixmap(pm)
            else:
                lab.setText("—")
            cap = QLabel(("★ " if primary else "") + f"#{img_id}")
            if primary:
                cap.setStyleSheet("font-weight: bold; color: #2f80ed;")
            btns = QHBoxLayout()
            b1 = QPushButton("Primaria"); b1.setObjectName("Ghost")
            b1.clicked.connect(lambda _=False, _id=img_id: self.primary_requested.emit(_id))
            b2 = QPushButton("Elimina"); b2.setObjectName("Danger")
            b2.clicked.connect(lambda _=False, _id=img_id: self.delete_requested.emit(_id))
            btns.addWidget(b1); btns.addWidget(b2)
            vl.addWidget(lab); vl.addWidget(cap); vl.addLayout(btns)
            self.grid.addWidget(cell, i // 3, i % 3)
