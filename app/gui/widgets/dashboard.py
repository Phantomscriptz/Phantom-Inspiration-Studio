from PySide6.QtWidgets import (
    QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout,
    QWidget, QStackedWidget, QScrollArea, QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

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


class LivePreviewPanel(QFrame):
    """Shows the newest scene while a render is being assembled."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setStyleSheet("""
            QFrame { background: #16161a; border: 1px solid #303038; border-radius: 8px; }
            QLabel { border: none; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("👁️ Live scene preview")
        title.setStyleSheet("color: #ddd; font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        self.stage = QLabel("Waiting for a render…")
        self.stage.setWordWrap(True)
        self.stage.setStyleSheet("color: #6ea8fe; font-size: 11px;")
        layout.addWidget(self.stage)

        self.image = QLabel("Your generated visual will appear here.")
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setWordWrap(True)
        self.image.setMinimumSize(220, 390)
        self.image.setStyleSheet("background: #0c0c0f; color: #777; border-radius: 6px; padding: 8px;")
        layout.addWidget(self.image, 1)

        self.narration = QLabel("")
        self.narration.setWordWrap(True)
        self.narration.setMaximumHeight(82)
        self.narration.setStyleSheet("color: #c8c8cc; font-size: 11px; padding: 4px;")
        layout.addWidget(self.narration)

    def show_scene(self, scene: int, total: int, image_path: str, narration: str):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.stage.setText(f"Scene {scene} of {total} generated (preview unavailable)")
            return
        target = self.image.size()
        self.image.setPixmap(pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.stage.setText(f"Scene {scene} of {total} generated")
        self.narration.setText(f"“{narration.strip()}”" if narration.strip() else "")

    def set_status(self, status: str):
        """Keep the preview useful before the first visual exists."""
        self.stage.setText(status)
        if self.image.pixmap() is None:
            self.image.setText(f"{status}\n\nThe first generated scene will appear here.")

    def resizeEvent(self, event):
        current = self.image.pixmap()
        if current and not current.isNull():
            self.image.setPixmap(current.scaled(self.image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)


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
        self.live_preview = LivePreviewPanel()
        log_console = QSplitter(Qt.Horizontal)
        log_console.setChildrenCollapsible(False)
        log_console.addWidget(self.log_panel)
        log_console.addWidget(self.live_preview)
        log_console.setStretchFactor(0, 3)
        log_console.setStretchFactor(1, 2)
        log_console.setSizes([760, 360])
        self.tab_stack.addWidget(log_console)                   # index 2

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

    def update_live_preview(self, scene: int, total: int, image_path: str, narration: str):
        """Receive a worker signal once each AI scene is ready."""
        self.live_preview.show_scene(scene, total, image_path, narration)

    def set_preview_status(self, status: str):
        self.live_preview.set_status(status)

    def update_stat(self, key: str, value: str):
        if key in self.stats_cards:
            self.stats_cards[key].set_value(value)

    def save_settings(self):
        self.content_settings.save()
