from PySide6.QtWidgets import QListWidget, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal


class Sidebar(QWidget):
    """Minimal sidebar — only the nav items that actually do something."""

    nav_changed = Signal(int)  # emitted when user clicks a nav item

    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.setStyleSheet("background: #18181b; border-right: 1px solid #2a2a2e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 12)
        layout.setSpacing(2)

        # Brand
        brand = QLabel("👻 Phantom")
        brand.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #fff; "
            "padding: 8px 10px 16px 10px;"
        )
        layout.addWidget(brand)

        # Nav items — only what we actually use
        self._items = [
            ("🏠  Dashboard", 0),
            ("🌐  Platforms", 1),
            ("📖  Guide", 2),
            ("💾  Storage", 3),
            ("📈  Analytics", 4),
        ]

        self.list = QListWidget()
        self.list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                padding: 0px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 8px;
                color: #888;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #2a2a2e;
                color: #ccc;
            }
        """)

        for label, _idx in self._items:
            self.list.addItem(label)

        self.list.setCurrentRow(0)
        self.list.currentRowChanged.connect(self._on_nav)
        layout.addWidget(self.list, 1)

        # Version
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #444; font-size: 10px; padding: 8px;")
        layout.addWidget(version)

    def _on_nav(self, row: int):
        if 0 <= row < len(self._items):
            self.nav_changed.emit(self._items[row][1])
