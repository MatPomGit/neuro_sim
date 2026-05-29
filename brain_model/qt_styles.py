"""Style QSS dla interfejsu PySide6 modelu poznawczego."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

QT_APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f8fafc;
    color: #0f172a;
    font-size: 13px;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QPushButton {
    background: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
}
QPushButton#primaryButton {
    background: #2563eb;
    border-color: #1d4ed8;
    color: #ffffff;
    font-weight: 600;
}
QTabWidget::pane {
    border: 1px solid #94a3b8;
    border-radius: 6px;
    top: -1px;
}
QTabBar::tab {
    background: #e2e8f0;
    border: 1px solid #94a3b8;
    border-bottom-color: #64748b;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 12px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom-color: #ffffff;
    color: #1d4ed8;
}
QTabBar::tab:!selected {
    margin-top: 3px;
}
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #64748b;
    background: #ffffff;
    width: 14px;
    height: 14px;
}
QCheckBox::indicator {
    border-radius: 3px;
}
QRadioButton::indicator {
    border-radius: 7px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background: #2563eb;
    border-color: #1d4ed8;
}
QLabel#headerTitle {
    font-size: 20px;
    font-weight: 700;
}
QLabel#hintLabel {
    color: #475569;
}
QLabel#statusLabel {
    color: #166534;
    font-weight: 600;
}
QLabel#warningStatusLabel {
    color: #b91c1c;
    font-weight: 600;
}
QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px;
}
"""


def apply_qt_styles(app: QApplication) -> None:
    """Zastosuj wspólny arkusz stylów QSS do aplikacji Qt."""
    app.setStyleSheet(QT_APP_STYLESHEET)
