"""Light / dark modern QSS themes."""
LIGHT = """
* { font-family: 'Segoe UI', Arial; font-size: 13px; }
QMainWindow, QWidget { background: #f4f6fa; color: #1c2733; }
#Sidebar { background: #1f3a5f; color: white; }
#Sidebar QListWidget { background: #1f3a5f; color: white; border: none; }
#Sidebar QListWidget::item { padding: 10px 14px; border-radius: 6px; }
#Sidebar QListWidget::item:selected { background: #2f80ed; color: white; }
#Sidebar QListWidget::item:hover { background: #2a4f7e; }
#SidebarLabel { color: white; font-weight: bold; font-size: 13px; padding: 8px 4px; }
QPushButton { background: #2f80ed; color: white; border: none; padding: 7px 14px; border-radius: 6px; }
QPushButton:hover { background: #2568c7; }
QPushButton:pressed { background: #1e56a6; }
QPushButton:disabled { background: #c9d3e0; color: #8a96a8; }
QPushButton#Danger { background: #d64545; }
QPushButton#Danger:hover { background: #b93737; }
QPushButton#Ghost { background: #e6ebf2; color: #1c2733; }
QPushButton#Ghost:hover { background: #d5dde9; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {
  background: white; border: 1px solid #c9d3e0; border-radius: 6px; padding: 6px; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #2f80ed; }
QLineEdit.error, QComboBox.error { border: 1px solid #d64545; background: #fdf0f0; }
QTableWidget { background: white; gridline-color: #e3e9f2; border: 1px solid #d8e0ec;
  border-radius: 8px; alternate-background-color: #f7f9fc; selection-background-color: #2f80ed;
  selection-color: white; }
QTableWidget::item:selected { background: #2f80ed; color: white; }
QHeaderView::section { background: #e9eef6; color: #1c2733; padding: 6px; border: none; font-weight: bold; }
QTabWidget::pane { border: 1px solid #d8e0ec; border-radius: 8px; background: white; }
QTabBar::tab { background: #e9eef6; padding: 6px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: white; font-weight: bold; }
QGroupBox { border: 1px solid #d8e0ec; border-radius: 8px; margin-top: 12px; background: white; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
#Card { background: white; border: 1px solid #dfe6f1; border-radius: 10px; padding: 8px; }
#CardTitle { color: #5b6b82; font-size: 12px; }
#CardValue { font-size: 20px; font-weight: bold; color: #1f3a5f; }
QStatusBar { background: #e9eef6; }
QToolBar { background: white; border-bottom: 1px solid #dfe6f1; }
QToolTip { background: #1f3a5f; color: white; border: none; padding: 4px 8px; }
QMenu { background: white; border: 1px solid #d8e0ec; }
QMenu::item:selected { background: #2f80ed; color: white; }
QScrollBar:vertical { background: #eef2f7; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #c2cede; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #2f80ed; }
QCheckBox, QRadioButton { spacing: 6px; }
QComboBox::drop-down { border: none; width: 22px; }
#LoginError { color: #c0392b; }
"""
DARK = """
* { font-family: 'Segoe UI', Arial; font-size: 13px; }
QMainWindow, QWidget { background: #141a24; color: #e6ebf2; }
#Sidebar { background: #0f1622; color: #e6ebf2; }
#Sidebar QListWidget { background: #0f1622; color: #e6ebf2; border: none; }
#Sidebar QListWidget::item { padding: 10px 14px; border-radius: 6px; }
#Sidebar QListWidget::item:selected { background: #2f80ed; color: white; }
#Sidebar QListWidget::item:hover { background: #1b2740; }
#SidebarLabel { color: #e6ebf2; font-weight: bold; font-size: 13px; padding: 8px 4px; }
QPushButton { background: #2f80ed; color: white; border: none; padding: 7px 14px; border-radius: 6px; }
QPushButton:hover { background: #3b8ff5; }
QPushButton:pressed { background: #2568c7; }
QPushButton:disabled { background: #2a3548; color: #7a8aa0; }
QPushButton#Danger { background: #b03a3a; }
QPushButton#Danger:hover { background: #c34a4a; }
QPushButton#Ghost { background: #243044; color: #e6ebf2; }
QPushButton#Ghost:hover { background: #2e3d55; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {
  background: #1d2635; border: 1px solid #33405a; border-radius: 6px; padding: 6px; color: #e6ebf2; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #2f80ed; }
QLineEdit.error, QComboBox.error { border: 1px solid #d64545; }
QTableWidget { background: #1a2230; gridline-color: #2c3a52; border: 1px solid #2c3a52;
  border-radius: 8px; alternate-background-color: #1e2839; selection-background-color: #2f80ed;
  selection-color: white; }
QTableWidget::item:selected { background: #2f80ed; color: white; }
QHeaderView::section { background: #222e44; color: #e6ebf2; padding: 6px; border: none; font-weight: bold; }
QTabWidget::pane { border: 1px solid #2c3a52; border-radius: 8px; background: #1a2230; }
QTabBar::tab { background: #222e44; color: #e6ebf2; padding: 6px 12px;
  border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #1a2230; font-weight: bold; }
QGroupBox { border: 1px solid #2c3a52; border-radius: 8px; margin-top: 12px; background: #1a2230; }
#Card { background: #1a2230; border: 1px solid #2c3a52; border-radius: 10px; padding: 8px; }
#CardTitle { color: #9fb0c7; font-size: 12px; }
#CardValue { font-size: 20px; font-weight: bold; color: white; }
QStatusBar { background: #0f1622; color: #9fb0c7; }
QToolBar { background: #1a2230; border-bottom: 1px solid #2c3a52; }
QToolTip { background: #e6ebf2; color: #141a24; border: none; padding: 4px 8px; }
QMenu { background: #1a2230; border: 1px solid #2c3a52; color: #e6ebf2; }
QMenu::item:selected { background: #2f80ed; color: white; }
QScrollBar:vertical { background: #141a24; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #33405a; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #2f80ed; }
QCheckBox, QRadioButton { spacing: 6px; }
QComboBox::drop-down { border: none; width: 22px; }
#LoginError { color: #ff8a8a; }
"""


def apply_theme(app, name: str) -> None:
    app.setStyleSheet(DARK if name == "dark" else LIGHT)
