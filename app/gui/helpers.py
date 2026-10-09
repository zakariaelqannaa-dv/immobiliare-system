"""Shared GUI helpers: toasts, confirms, table fill, permission gating."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QWidget, QAbstractItemView
from PySide6.QtCore import Qt


def info(parent: QWidget, text: str, title: str = "Info") -> None:
    QMessageBox.information(parent, title, text)


def error(parent: QWidget, text: str, title: str = "Errore") -> None:
    # never expose sensitive internals
    safe = str(text)[:800]
    QMessageBox.critical(parent, title, safe)


def success(parent: QWidget | None, text: str, title: str = "OK") -> None:
    # Non-blocking style: if parent is a QMainWindow with statusBar, prefer that.
    # Kept as modal for compatibility when no status bar is available.
    try:
        win = parent.window() if parent is not None else None
        sb = win.statusBar() if win is not None and hasattr(win, "statusBar") else None
        if sb is not None:
            sb.showMessage(text, 3000)
            return
    except Exception:
        pass
    if parent is not None:
        QMessageBox.information(parent, title, text)


def status(parent: QWidget, text: str, timeout: int = 3000) -> None:
    """Show a non-modal status message instead of a popup."""
    try:
        win = parent.window() if parent is not None else None
        sb = win.statusBar() if win is not None and hasattr(win, "statusBar") else None
        if sb is not None:
            sb.showMessage(text, timeout)
            return
    except Exception:
        pass
    info(parent, text)


def confirm(parent: QWidget, text: str) -> bool:
    r = QMessageBox.question(parent, "Conferma", text,
                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    return r == QMessageBox.StandardButton.Yes


def style_table(table: QTableWidget) -> None:
    """Apply consistent feel-good table defaults. Call once after creating a table."""
    table.setAlternatingRowColors(True)
    table.setSortingEnabled(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    try:
        table.verticalHeader().setVisible(False)
    except Exception:
        pass
    table.setWordWrap(False)
    table.horizontalHeader().setStretchLastSection(True)


def fill_table(table: QTableWidget, headers: list[str], rows: list[list],
               ids: list | None = None) -> None:
    try:
        style_table(table)
    except Exception:
        pass
    # preserve scroll / selection across refreshes to avoid column jump
    h_scroll = v_scroll = current = None
    try:
        h_scroll = table.horizontalScrollBar().value()
        v_scroll = table.verticalScrollBar().value()
        current = table.currentRow()
    except Exception:
        pass
    sorting = False
    try:
        sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
    except Exception:
        pass
    table.clear()
    table.setRowCount(len(rows))
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            it = QTableWidgetItem(str(val))
            it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if ids is not None and j == 0:
                it.setData(Qt.ItemDataRole.UserRole, ids[i])
            table.setItem(i, j, it)
    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    try:
        table.setSortingEnabled(sorting)
    except Exception:
        pass
    try:
        if h_scroll is not None:
            table.horizontalScrollBar().setValue(h_scroll)
        if v_scroll is not None:
            table.verticalScrollBar().setValue(v_scroll)
        if current is not None and current < table.rowCount():
            table.setCurrentCell(current, 0)
    except Exception:
        pass


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
