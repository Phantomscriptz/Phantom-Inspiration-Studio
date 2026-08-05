from PySide6.QtWidgets import (
    QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QWidget, QStackedWidget, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from app.gui.widgets.control_bar import ControlBar
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

    def __init__(self, settings: SettingsManager = None, model_manager=None):
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
            ("💰  Affiliates", 1),
            ("📋  Log", 2),
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

        self.content_settings = ContentSettingsPanel(self.settings, model_manager)
        self.tab_stack.addWidget(self.content_settings)         # index 0

        self.affiliate_panel = AffiliatePanel(self.settings)
        scroll = QScrollArea()
        scroll.setWidget(self.affiliate_panel)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.tab_stack.addWidget(scroll)                        # index 1

        self.log_panel = LogPanel()
        self.tab_stack.addWidget(self.log_panel)                # index 2

        # The configuration panels can exceed a laptop-sized window.  Keep the
        # start controls visible and make only the active content area scroll.
        content_scroll = QScrollArea()
        content_scroll.setWidget(self.tab_stack)
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.NoFrame)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._content_scroll = content_scroll
        layout.addWidget(content_scroll, 1)

        # ── Control Bar (bottom — always visible) ──
        self.control_bar = ControlBar()
        layout.addWidget(self.control_bar)

        # The former four cards repeated information already shown in the
        # control bar and rendered poorly at smaller window heights.
        self.stats_cards = {}

        # Activate first tab
        self._switch_tab(0)

    def _switch_tab(self, index: int):
        """Switch to tab `index` and make only that button checked."""
        self.tab_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._tab_buttons):
            btn.setChecked(i == index)
        # Do not carry a previous settings-panel scroll position into a new
        # tab. It made the beginning of Platform and Log look cut off.
        self._content_scroll.verticalScrollBar().setValue(0)

    def show_log(self):
        """Bring live pipeline activity into view from the first log line."""
        self._switch_tab(2)
        self.log_panel.output.verticalScrollBar().setValue(0)

    def log(self, message: str):
        self.log_panel.log(message)

    def update_stat(self, key: str, value: str):
        if key in self.stats_cards:
            self.stats_cards[key].set_value(value)

    def save_settings(self):
        self.content_settings.save()
