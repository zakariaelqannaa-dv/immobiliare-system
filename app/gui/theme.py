"""Light / dark modern QSS themes."""
LIGHT = """
* { font-family: 'Segoe UI', Arial; font-size: 13px; }
QMainWindow, QWidget { background: #f4f6fa; color: #1c2733; }
#Sidebar { background: #1f3a5f; color: white; }
#Sidebar QListWidget { background: #1f3a5f; color: white; border: none; }
#Sidebar QListWidget::item { padding: 10px 14px; border-radius: 6px; }
#Sidebar QListWidget::item:selected { background: #2f80ed; color: white; }
QPushButton { background: #2f80ed; color: white; border: none; padding: 7px 14px; border-radius: 6px; }
QPushButton:hover { background: #2568c7; }
QPushButton#Danger { background: #d64545; }
QPushButton#Ghost { background: #e6ebf2; color: #1c2733; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {
  background: white; border: 1px solid #c9d3e0; border-radius: 6px; padding: 6px; }
QTableWidget { background: white; gridline-color: #e3e9f2; border: 1px solid #d8e0ec; border-radius: 8px; }
QHeaderView::section { background: #e9eef6; padding: 6px; border: none; font-weight: bold; }
QGroupBox { border: 1px solid #d8e0ec; border-radius: 8px; margin-top: 12px; background: white; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
#Card { background: white; border: 1px solid #dfe6f1; border-radius: 10px; }
#CardTitle { color: #5b6b82; font-size: 12px; }
#CardValue { font-size: 20px; font-weight: bold; color: #1f3a5f; }
QStatusBar { background: #e9eef6; }
QToolBar { background: white; border-bottom: 1px solid #dfe6f1; }
"""
DARK = """
* { font-family: 'Segoe UI', Arial; font-size: 13px; }
QMainWindow, QWidget { background: #141a24; color: #e6ebf2; }
#Sidebar { background: #0f1622; }
#Sidebar QListWidget { background: #0f1622; color: #e6ebf2; border: none; }
#Sidebar QListWidget::item { padding: 10px 14px; border-radius: 6px; }
#Sidebar QListWidget::item:selected { background: #2f80ed; }
QPushButton { background: #2f80ed; color: white; border: none; padding: 7px 14px; border-radius: 6px; }
QPushButton#Danger { background: #b03a3a; }
QPushButton#Ghost { background: #243044; color: #e6ebf2; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {
  background: #1d2635; border: 1px solid #33405a; border-radius: 6px; padding: 6px; color: #e6ebf2; }
QTableWidget { background: #1a2230; gridline-color: #2c3a52; border: 1px solid #2c3a52; border-radius: 8px; }
QHeaderView::section { background: #222e44; padding: 6px; border: none; }
QGroupBox { border: 1px solid #2c3a52; border-radius: 8px; margin-top: 12px; background: #1a2230; }
#Card { background: #1a2230; border: 1px solid #2c3a52; border-radius: 10px; }
#CardTitle { color: #9fb0c7; font-size: 12px; }
#CardValue { font-size: 20px; font-weight: bold; color: white; }
QStatusBar { background: #0f1622; }
QToolBar { background: #1a2230; }
"""


def apply_theme(app, name: str) -> None:
    app.setStyleSheet(DARK if name == "dark" else LIGHT)
