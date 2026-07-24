"""Platform tabs — one tab per platform with enable/disable and settings."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QCheckBox, QSpinBox, QGroupBox, QFrame,
    QPushButton, QTextEdit, QLineEdit, QComboBox,
)
from PySide6.QtCore import Qt, Signal

from app.config.settings import SettingsManager


class PlatformTab(QWidget):
    """Individual platform configuration tab."""

    def __init__(self, platform_key: str, platform_name: str, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.platform_key = platform_key
        self.platform_name = platform_name
        self.settings = settings

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Enable toggle
        self.enabled_cb = QCheckBox(f"Enable {platform_name} Uploads")
        self.enabled_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        self.enabled_cb.toggled.connect(self._on_enabled_toggled)
        layout.addWidget(self.enabled_cb)

        # Settings group
        settings_group = QGroupBox("Upload Settings")
        settings_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        settings_layout = QVBoxLayout(settings_group)

        # Max per day
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Max videos per day:"))
        self.max_per_day = QSpinBox()
        self.max_per_day.setRange(0, 50)
        self.max_per_day.setStyleSheet("background: #2d2d30; color: white; border: 1px solid #444; border-radius: 4px; padding: 4px;")
        row1.addWidget(self.max_per_day)
        row1.addStretch()
        settings_layout.addLayout(row1)

        # Status info
        self.status_label = QLabel("Status: Not configured")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        settings_layout.addWidget(self.status_label)

        layout.addWidget(settings_group)

        # API Status group
        api_group = QGroupBox("API Connection")
        api_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 12px;
                padding: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        api_layout = QVBoxLayout(api_group)

        self.auth_btn = QPushButton("🔑 Authorize")
        self.auth_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        api_layout.addWidget(self.auth_btn)

        self.api_info_label = QLabel("First-time setup: click to authorize this platform")
        self.api_info_label.setStyleSheet("color: #888; font-size: 12px;")
        api_layout.addWidget(self.api_info_label)

        # Placeholder for platform-specific buttons (e.g. TikTok Setup Guide)
        self._extra_buttons_layout = QHBoxLayout()
        api_layout.addLayout(self._extra_buttons_layout)

        layout.addWidget(api_group)
        layout.addStretch()

        # Load current values
        self._load_settings()

    def _load_settings(self):
        enabled = self.settings.get(f"platform_limits.{self.platform_key}.enabled", False)
        max_day = self.settings.get(f"platform_limits.{self.platform_key}.max_per_day", 3)

        self.enabled_cb.setChecked(enabled)
        self.max_per_day.setValue(max_day)

    def _on_enabled_toggled(self, checked: bool):
        self.settings.set(f"platform_limits.{self.platform_key}.enabled", checked)

    def save(self):
        self.settings.set(f"platform_limits.{self.platform_key}.enabled", self.enabled_cb.isChecked())
        self.settings.set(f"platform_limits.{self.platform_key}.max_per_day", self.max_per_day.value())

    def update_status(self, status_text: str, is_ok: bool = False):
        color = "#22c55e" if is_ok else "#888"
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")

    def add_extra_button(self, button: QPushButton):
        """Add a button to the API Connection section (e.g. Setup Guide)."""
        self._extra_buttons_layout.addWidget(button)


class PlatformTabs(QTabWidget):
    """Tab widget with one tab per supported platform."""

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.tabs = {}

        self.setStyleSheet("""
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
        """)

        platforms = [
            ("youtube", "🎬 YouTube"),
            ("tiktok", "🎵 TikTok"),
            ("instagram", "📸 Instagram"),
            ("x_twitter", "🐦 X / Twitter"),
            ("rumble", "📺 Rumble"),
            ("facebook", "👍 Facebook"),
            ("snapchat", "👻 Snapchat"),
        ]

        for key, name in platforms:
            tab = PlatformTab(key, name, settings)
            self.addTab(tab, name)
            self.tabs[key] = tab

        # ── Add Setup Guide buttons to all platforms ──
        self._add_all_guide_buttons()

    def save_all(self):
        """Save all tab settings."""
        for tab in self.tabs.values():
            tab.save()

    def get_enabled_platforms(self) -> list[str]:
        """Get list of enabled platform keys."""
        return [key for key, tab in self.tabs.items() if tab.enabled_cb.isChecked()]

    def _add_all_guide_buttons(self):
        """Add a Setup Guide button to every platform tab."""
        guide_colors = {
            "youtube": ("#ef4444", "#fff"),
            "tiktok": ("#f59e0b", "#000"),
            "instagram": ("#e1306c", "#fff"),
            "x_twitter": ("#1d9bf0", "#fff"),
            "rumble": ("#85c742", "#000"),
            "facebook": ("#1877f2", "#fff"),
            "snapchat": ("#fffc00", "#000"),
        }

        for key, tab in self.tabs.items():
            bg, fg = guide_colors.get(key, ("#3b82f6", "#fff"))

            guide_btn = QPushButton("📖 Setup Guide")
            guide_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg};
                    color: {fg};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ opacity: 0.85; }}
            """)
            guide_btn.setCursor(Qt.PointingHandCursor)
            guide_btn.clicked.connect(lambda checked, k=key: self._open_guide(k))
            tab.add_extra_button(guide_btn)

            # Update the info label for all platforms
            tab.api_info_label.setText("Click Authorize after completing setup")
            tab.api_info_label.setStyleSheet("color: #888; font-size: 12px;")

    def _open_guide(self, platform_key: str):
        """Open the platform Setup Instructions dialog."""
        from app.dialogs.platform_setup_dialogs import PlatformSetupDialog
        dialog = PlatformSetupDialog(platform_key, self)
        dialog.exec()
