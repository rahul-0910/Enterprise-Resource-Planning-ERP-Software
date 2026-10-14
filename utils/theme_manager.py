"""
HOE Billing Software - Theme Manager
"""

LIGHT_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #F5F7FA;
    color: #2D3748;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QMenuBar {
    background-color: #1A2A4A;
    color: white;
    padding: 4px;
    font-size: 13px;
}
QMenuBar::item:selected {
    background-color: #2E5FA3;
    border-radius: 4px;
}
QMenu {
    background-color: white;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #EBF5FB;
    color: #1A2A4A;
}
QPushButton {
    background-color: #1A2A4A;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2E5FA3;
}
QPushButton:pressed {
    background-color: #142240;
}
QPushButton#btn_success {
    background-color: #27AE60;
}
QPushButton#btn_success:hover {
    background-color: #229954;
}
QPushButton#btn_danger {
    background-color: #E74C3C;
}
QPushButton#btn_danger:hover {
    background-color: #C0392B;
}
QPushButton#btn_warning {
    background-color: #F39C12;
    color: white;
}
QPushButton#btn_secondary {
    background-color: #95A5A6;
}
QPushButton#btn_secondary:hover {
    background-color: #7F8C8D;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    border: 1.5px solid #CBD5E0;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: white;
    color: #2D3748;
    font-size: 13px;
    selection-background-color: #BEE3F8;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #1A2A4A;
}
QComboBox {
    border: 1.5px solid #CBD5E0;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: white;
    color: #2D3748;
    font-size: 13px;
    min-width: 120px;
}
QComboBox:focus {
    border-color: #1A2A4A;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    background-color: white;
    selection-background-color: #EBF5FB;
}
QSpinBox, QDoubleSpinBox {
    border: 1.5px solid #CBD5E0;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: white;
    font-size: 13px;
}
QDateEdit {
    border: 1.5px solid #CBD5E0;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: white;
    font-size: 13px;
}
QTableWidget {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: white;
    gridline-color: #EDF2F7;
    font-size: 13px;
    selection-background-color: #EBF5FB;
    selection-color: #1A2A4A;
}
QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #EDF2F7;
}
QTableWidget::item:selected {
    background-color: #EBF5FB;
    color: #1A2A4A;
}
QHeaderView::section {
    background-color: #1A2A4A;
    color: white;
    padding: 10px 12px;
    border: none;
    font-weight: 600;
    font-size: 13px;
}
QHeaderView::section:first {
    border-top-left-radius: 8px;
}
QHeaderView::section:last {
    border-top-right-radius: 8px;
}
QGroupBox {
    border: 1.5px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
    color: #2D3748;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1A2A4A;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 0 8px 8px 8px;
    background-color: white;
}
QTabBar::tab {
    background-color: #EDF2F7;
    color: #718096;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    font-size: 13px;
}
QTabBar::tab:selected {
    background-color: #1A2A4A;
    color: white;
    font-weight: 600;
}
QScrollBar:vertical {
    width: 8px;
    background: #F5F7FA;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #CBD5E0;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #A0AEC0;
}
QScrollBar:horizontal {
    height: 8px;
    background: #F5F7FA;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #CBD5E0;
    border-radius: 4px;
}
QLabel#header_title {
    font-size: 22px;
    font-weight: 700;
    color: #1A2A4A;
}
QLabel#section_title {
    font-size: 16px;
    font-weight: 600;
    color: #2D3748;
}
QStatusBar {
    background-color: #1A2A4A;
    color: white;
    font-size: 12px;
}
QToolTip {
    background-color: #2D3748;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
QCheckBox {
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #CBD5E0;
    border-radius: 4px;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #1A2A4A;
    border-color: #1A2A4A;
}
"""

DARK_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #1A202C;
    color: #E2E8F0;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QMenuBar {
    background-color: #2D3748;
    color: #E2E8F0;
    padding: 4px;
}
QMenuBar::item:selected { background-color: #4A5568; border-radius: 4px; }
QMenu {
    background-color: #2D3748;
    border: 1px solid #4A5568;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { padding: 6px 20px; border-radius: 4px; color: #E2E8F0; }
QMenu::item:selected { background-color: #4A5568; }
QPushButton {
    background-color: #4A5568;
    color: #E2E8F0;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover { background-color: #718096; }
QPushButton#btn_success { background-color: #276749; }
QPushButton#btn_success:hover { background-color: #2F855A; }
QPushButton#btn_danger { background-color: #9B2335; }
QPushButton#btn_danger:hover { background-color: #C53030; }
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
    border: 1.5px solid #4A5568;
    border-radius: 6px;
    padding: 7px 10px;
    background-color: #2D3748;
    color: #E2E8F0;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus { border-color: #718096; }
QComboBox QAbstractItemView {
    background-color: #2D3748;
    border: 1px solid #4A5568;
    color: #E2E8F0;
    selection-background-color: #4A5568;
}
QTableWidget {
    border: 1px solid #4A5568;
    border-radius: 8px;
    background-color: #2D3748;
    gridline-color: #4A5568;
    color: #E2E8F0;
    selection-background-color: #4A5568;
}
QTableWidget::item { padding: 8px 10px; }
QHeaderView::section {
    background-color: #4A5568;
    color: #E2E8F0;
    padding: 10px 12px;
    border: none;
    font-weight: 600;
}
QGroupBox {
    border: 1.5px solid #4A5568;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    color: #E2E8F0;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #A0AEC0; }
QTabWidget::pane { border: 1px solid #4A5568; background-color: #2D3748; }
QTabBar::tab {
    background-color: #4A5568;
    color: #A0AEC0;
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected { background-color: #718096; color: white; font-weight: 600; }
QScrollBar:vertical { width: 8px; background: #2D3748; border-radius: 4px; }
QScrollBar::handle:vertical { background: #4A5568; border-radius: 4px; min-height: 30px; }
QStatusBar { background-color: #2D3748; color: #A0AEC0; }
"""


class ThemeManager:
    def apply_theme(self, app, theme_name="light"):
        if theme_name == "dark":
            app.setStyleSheet(DARK_THEME)
        else:
            app.setStyleSheet(LIGHT_THEME)

    def get_theme_stylesheet(self, theme_name="light"):
        return DARK_THEME if theme_name == "dark" else LIGHT_THEME
