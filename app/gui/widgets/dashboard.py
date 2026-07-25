from PySide6.QtWidgets import (
    QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QWidget, QStackedWidget, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from app.gui.widgets.control_bar import ControlBar
from app.gui.widgets.platform_tabs import PlatformTabs
from app.gui.widgets.content_settings import ContentSettingsPanel
from app.gui.widgets.affiliate_panel import AffiliatePanel
from app.gui.widgets.log_panel import LogPanel
from app.config.settings import SettingsManager


class StatCard(QFrame):
    """A single stat card showing a metric."""

    def __init__(self, title: str, value: str = "0", icon: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame {
                border-radius: 8px;
                padding: 6px 12px;
                background: #2D2D30;
                border: 1px solid #3a3a3d;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 4, 12, 4)

        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.icon_label)

        info = QVBoxLayout()
        info.setSpacing(0)
        info.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 10px; color: #888;")
        info.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        info.addWidget(self.value_label)

        layout.addLayout(info, 1)

    def set_value(self, value: str):
        self.value_label.setText(value)


# Tab button style constants
_TAB_BTN_STYLE = """
    QPushButton {
        background: #2d2d30;
        color: #888;
        border: 1px solid #3a3a3d;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 13px;
    }
    QPushButton:hover {
        background: #3a3a3d;
        color: #ccc;
    }
    QPushButton:checked {
        background: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
"""


class Dashboard(QWidget):
    """Main dashboard — the only screen that matters."""

    start_automation = Signal()
    stop_automation = Signal()

    def __init__(self, settings: SettingsManager = None):
        super().__init__()
        self.settings = settings or SettingsManager()

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 8, 16, 8)

        # ── Tab Buttons (top — always visible) ──
        self._tab_buttons: list[QPushButton] = []
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(4)
        tab_layout.setContentsMargins(0, 0, 0, 4)

        tabs = [
            ("⚙  Content", 0),
            ("🌐  Platforms", 1),
            ("💰  Affiliates", 2),
            ("📋  Log", 3),
        ]

        for text, idx in tabs:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(34)
            btn.setStyleSheet(_TAB_BTN_STYLE)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            tab_layout.addWidget(btn)
            self._tab_buttons.append(btn)

        tab_layout.addStretch()
        layout.addLayout(tab_layout)

        # ── Stacked content (one tab at a time) ──
        self.tab_stack = QStackedWidget()

        self.content_settings = ContentSettingsPanel(self.settings)
        self.tab_stack.addWidget(self.content_settings)         # index 0

        self.platform_tabs = PlatformTabs(self.settings)
        self.tab_stack.addWidget(self.platform_tabs)            # index 1

        self.affiliate_panel = AffiliatePanel(self.settings)
        scroll = QScrollArea()
        scroll.setWidget(self.affiliate_panel)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.tab_stack.addWidget(scroll)                        # index 2

        self.log_panel = LogPanel()
        self.tab_stack.addWidget(self.log_panel)                # index 3

        layout.addWidget(self.tab_stack, 1)

        # ── Control Bar (bottom — always visible) ──
        self.control_bar = ControlBar()
        layout.addWidget(self.control_bar)

        # ── Stats Row (bottom — compact) ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(6)
        self.stats_cards = {}
        for key, icon, name, val in [
            ("videos_today", "📹", "Today", "0"),
            ("videos_total", "🎬", "Total", "0"),
            ("uploaded", "📤", "Uploaded", "0"),
            ("errors", "⚠️", "Errors", "0"),
        ]:
            card = StatCard(name, val, icon)
            stats_layout.addWidget(card, 1)
            self.stats_cards[key] = card
        layout.addLayout(stats_layout)

        # Activate first tab
        self._switch_tab(0)

    def _switch_tab(self, index: int):
        """Switch to tab `index` and make only that button checked."""
        self.tab_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._tab_buttons):
            btn.setChecked(i == index)

    def log(self, message: str):
        self.log_panel.log(message)

    def update_stat(self, key: str, value: str):
        if key in self.stats_cards:
            self.stats_cards[key].set_value(value)

    def save_settings(self):
        self.content_settings.save()
        self.platform_tabs.save_all()