from PySide6.QtWidgets import QApplication


def load_dark_theme(app: QApplication):

    app.setStyleSheet("""
QMainWindow {
    background: #202124;
}

QWidget {
    background: #202124;
    color: #e0e0e0;
    font-size: 10pt;
    font-family: "Segoe UI", "SF Pro Display", -apple-system, sans-serif;
}

QToolBar {
    background: #1a1a1e;
    spacing: 8px;
    border: none;
    border-bottom: 1px solid #2a2a2e;
    padding: 4px 8px;
}

QStatusBar {
    background: #1a1a1e;
    color: #888;
    border-top: 1px solid #2a2a2e;
    font-size: 11px;
}

QPushButton {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 12pt;
    font-weight: 500;
}

QPushButton:hover {
    background: #2563eb;
}

QPushButton:pressed {
    background: #1d4ed8;
}

QPushButton:disabled {
    background: #374151;
    color: #6b7280;
}

QFrame {
    background: #2d2d30;
    border-radius: 12px;
}

QLabel {
    color: #e0e0e0;
    background: transparent;
}

QLineEdit {
    background: #2d2d30;
    color: #e0e0e0;
    border: 1px solid #3a3a3d;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}

QLineEdit:focus {
    border-color: #3b82f6;
}

QTextEdit {
    background: #0d0d0f;
    color: #c0c0c0;
    border: 1px solid #2a2a2e;
    border-radius: 8px;
    padding: 8px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 12px;
}

QComboBox {
    background: #2d2d30;
    color: #e0e0e0;
    border: 1px solid #3a3a3d;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #3b82f6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background: #2d2d30;
    color: #e0e0e0;
    border: 1px solid #3a3a3d;
    selection-background-color: #3b82f6;
}

QSpinBox {
    background: #2d2d30;
    color: #e0e0e0;
    border: 1px solid #3a3a3d;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

QCheckBox {
    color: #e0e0e0;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #555;
    background: #2d2d30;
}

QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}

QScrollBar:vertical {
    background: #1a1a1e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3a3a3d;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QGroupBox {
    font-size: 13px;
    font-weight: bold;
    color: #ccc;
    border: 1px solid #333;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 16px 16px 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QTabWidget::pane {
    border: 1px solid #333;
    border-radius: 8px;
    background: #202124;
    padding: 8px;
}

QTabBar::tab {
    background: #2d2d30;
    color: #888;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background: #3b82f6;
    color: white;
}

QTabBar::tab:hover {
    background: #3a3a3d;
}

QScrollArea {
    border: none;
    background: transparent;
}

QLabel{
    color:white;
}
""")