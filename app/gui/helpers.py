"""Shared GUI helpers: toasts, confirms, table fill, permission gating."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QWidget
from PySide6.QtCore import Qt


def info(parent: QWidget, text: str, title: str = "Info") -> None:
    QMessageBox.information(parent, title, text)


def error(parent: QWidget, text: str, title: str = "Errore") -> None:
    # never expose sensitive internals
    safe = str(text)[:800]
    QMessageBox.critical(parent, title, safe)


def success(parent: QWidget, text: str, title: str = "OK") -> None:
    QMessageBox.information(parent, title, text)


def confirm(parent: QWidget, text: str) -> bool:
    r = QMessageBox.question(parent, "Conferma", text,
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    return r == QMessageBox.StandardButton.Yes


def fill_table(table: QTableWidget, headers: list[str], rows: list[list],
               ids: list | None = None) -> None:
    table.clear()
    table.setRowCount(len(rows))
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            it = QTableWidgetItem(str(val))
            it.setFlags(it.flags() ^ Qt.ItemFlag.ItemIsEditable)
            if ids is not None:
                it.setData(Qt.ItemDataRole.UserRole, ids[i])
            table.setItem(i, j, it)
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)


def selected_id(table: QTableWidget) -> int | None:
    r = table.currentRow()
    if r < 0:
        return None
    it = table.item(r, 0)
    if it is None:
        return None
    v = it.data(Qt.ItemDataRole.UserRole)
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def gate(widget, allowed: bool) -> None:
    widget.setEnabled(bool(allowed))
    widget.setToolTip("" if allowed else "Permesso mancante")
