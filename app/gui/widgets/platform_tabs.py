"""Platform tabs — one tab per platform with enable/disable and settings."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QCheckBox, QSpinBox, QGroupBox, QFrame,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QFileDialog, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
import json

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
        self.max_per_day.valueChanged.connect(
            lambda value: self.settings.set(f"platform_limits.{self.platform_key}.max_per_day", value)
        )
        row1.addWidget(self.max_per_day)
        row1.addStretch()
        settings_layout.addLayout(row1)

        # Status info
        self.status_label = QLabel("Status: Not configured")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        self.status_label.setWordWrap(True)
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
        self.auth_btn.clicked.connect(self._authorize)
        self._compact_button(self.auth_btn)

        if self.platform_key in {"youtube_long", "youtube_shorts", "tiktok"}:
            self.import_btn = QPushButton("📁 Import OAuth client JSON")
            self.import_btn.setToolTip("Import the client configuration downloaded from the platform developer portal.")
            self.import_btn.clicked.connect(self._import_oauth_client_json)
            self._compact_button(self.import_btn)
            api_layout.addWidget(self.import_btn)

        if self.platform_key in {"youtube_long", "youtube_shorts", "tiktok", "instagram"}:
            self.disconnect_btn = QPushButton("Disconnect account")
            self.disconnect_btn.setToolTip("Remove this computer's saved account authorization. Your developer client configuration is kept.")
            self.disconnect_btn.setStyleSheet("QPushButton { background: #4b5563; color: white; border-radius: 6px; padding: 8px 16px; } QPushButton:hover { background: #374151; }")
            self.disconnect_btn.clicked.connect(self._disconnect_account)
            self._compact_button(self.disconnect_btn)
            api_layout.addWidget(self.disconnect_btn)

        self.api_info_label = QLabel("First-time setup: click to authorize this platform")
        self.api_info_label.setStyleSheet("color: #888; font-size: 12px;")
        api_layout.addWidget(self.api_info_label)

        audience_row = QHBoxLayout()
        self.audience_label = QLabel("Audience: not synced")
        self.audience_label.setStyleSheet("color: #888; font-size: 12px;")
        audience_row.addWidget(self.audience_label, 1)
        self.sync_audience_btn = QPushButton("Sync audience")
        self.sync_audience_btn.clicked.connect(self._sync_audience)
        self._compact_button(self.sync_audience_btn)
        audience_row.addWidget(self.sync_audience_btn)
        api_layout.addLayout(audience_row)

        # Placeholder for platform-specific buttons (e.g. TikTok Setup Guide)
        self._extra_buttons_layout = QHBoxLayout()
        api_layout.addLayout(self._extra_buttons_layout)

        layout.addWidget(api_group)
        layout.addStretch()

        # Load current values
        self._load_settings()
        self._refresh_connection_status()

    def _load_settings(self):
        enabled = self.settings.get(f"platform_limits.{self.platform_key}.enabled", False)
        max_day = self.settings.get(f"platform_limits.{self.platform_key}.max_per_day", 3)

        self.enabled_cb.setChecked(enabled)
        self.max_per_day.setValue(max_day)

    def _on_enabled_toggled(self, checked: bool):
        self.settings.set(f"platform_limits.{self.platform_key}.enabled", checked)

    def _refresh_connection_status(self):
        """Show local readiness without ever showing secret values."""
        required_files = {
            "youtube_long": ("config/youtube_client_secret.json", "config/youtube_token.json"),
            "youtube_shorts": ("config/youtube_client_secret.json", "config/youtube_token.json"),
            "tiktok": ("config/tiktok_credentials.json", "config/tiktok_token.json"),
            "instagram": ("config/instagram_credentials.json",),
        }
        files = required_files.get(self.platform_key)
        if not files:
            self.update_status("Setup guide required; publisher not verified", False)
            return
        present = [Path(path).exists() for path in files]
        if all(present):
            self.update_status("Credentials found locally (not API-verified)", True)
        elif any(present):
            self.update_status("Credentials incomplete — finish authorization", False)
        else:
            self.update_status("Not connected", False)

    def _authorize(self):
        """Begin only the supported official OAuth flows."""
        try:
            if self.platform_key in {"youtube_long", "youtube_shorts"}:
                from app.publishing.youtube_uploader import YouTubeUploader
                # Creating the service opens the official consent flow when a
                # new or older upload-only token needs permission renewal.
                YouTubeUploader()._get_service()
                self.update_status("Connected for YouTube uploads", True)
            elif self.platform_key == "tiktok":
                from app.publishing.tiktok_uploader import TikTokUploader
                TikTokUploader()._get_access_token()
                self.update_status("TikTok authorization completed", True)
            else:
                self.update_status("Use the setup guide; this publisher is not implemented yet", False)
        except Exception as exc:
                self.update_status(f"Authorization failed: {type(exc).__name__}. See the setup guide for details.", False)

    def _sync_audience(self):
        """Fetch counts only where an official integration is implemented."""
        if self.platform_key in {"youtube_long", "youtube_shorts"}:
            try:
                from app.publishing.youtube_uploader import YouTubeUploader
                stats = YouTubeUploader().get_channel_audience()
                subscribers = stats["subscribers"]
                visible = f"{int(subscribers):,}" if str(subscribers).isdigit() else "hidden by channel"
                self.audience_label.setText(f"Audience: {visible} subscribers • {stats['name']}")
                self.audience_label.setStyleSheet("color: #22c55e; font-size: 12px;")
            except Exception as exc:
                self.audience_label.setText("Audience: re-authorize YouTube, then sync again")
                self.audience_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
        else:
            self.audience_label.setText("Audience: official metric sync is not implemented for this platform yet")
            self.audience_label.setStyleSheet("color: #888; font-size: 12px;")

    @staticmethod
    def _compact_button(button: QPushButton):
        """Prevent action controls from expanding across a wide desktop window."""
        button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        button.setMaximumWidth(300)

    def _disconnect_account(self):
        """Remove only the local OAuth authorization, not the developer client file."""
        token_files = {
            "youtube_long": Path("config/youtube_token.json"),
            "youtube_shorts": Path("config/youtube_token.json"),
            "tiktok": Path("config/tiktok_token.json"),
            "instagram": Path("config/instagram_token.json"),
        }
        token_file = token_files.get(self.platform_key)
        if not token_file:
            return
        answer = QMessageBox.question(
            self,
            "Disconnect account",
            "Remove this computer's saved authorization? You can connect a different account afterward.",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            try:
                token_file.unlink(missing_ok=True)
                self.update_status("Disconnected — click Authorize to connect another account", False)
            except OSError as exc:
                QMessageBox.warning(self, "Disconnect failed", str(exc))

    def _import_oauth_client_json(self):
        """Import a client configuration file without displaying its secret values."""
        source, _ = QFileDialog.getOpenFileName(
            self, "Import OAuth client configuration", "", "JSON files (*.json)"
        )
        if not source:
            return
        try:
            with open(source, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if self.platform_key in {"youtube_long", "youtube_shorts"}:
                valid = isinstance(payload.get("installed") or payload.get("web"), dict)
                destination = Path("config/youtube_client_secret.json")
            else:
                valid = bool(payload.get("client_key") and payload.get("client_secret"))
                destination = Path("config/tiktok_credentials.json")
            if not valid:
                raise ValueError("That file is not a valid client configuration for this platform.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            self.update_status("Client configuration imported; click Authorize", True)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            QMessageBox.warning(self, "Import failed", str(exc))

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
            ("youtube_long", "🎬 YouTube Videos"),
            ("youtube_shorts", "📱 YouTube Shorts"),
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
            "youtube_long": ("#ef4444", "#fff"),
            "youtube_shorts": ("#ff5c5c", "#fff"),
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
            PlatformTab._compact_button(guide_btn)
            guide_btn.clicked.connect(lambda checked, k=key: self._open_guide(k))
            tab.add_extra_button(guide_btn)

            # Update the info label for all platforms
            tab.api_info_label.setText("Click Authorize after completing setup")
            tab.api_info_label.setStyleSheet("color: #888; font-size: 12px;")

    def _open_guide(self, platform_key: str):
        """Open the platform Setup Instructions dialog."""
        from app.dialogs.platform_setup_dialogs import PlatformSetupDialog
        guide_key = "youtube" if platform_key in {"youtube_long", "youtube_shorts"} else platform_key
        dialog = PlatformSetupDialog(guide_key, self)
        dialog.exec()
