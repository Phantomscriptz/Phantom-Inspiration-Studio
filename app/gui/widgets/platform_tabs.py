"""Platform tabs — one tab per platform with enable/disable and settings."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QCheckBox, QSpinBox, QGroupBox, QFrame,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QFileDialog, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize, QThread, QTimer
from PySide6.QtGui import QIcon
from pathlib import Path
import json
from datetime import datetime

from app.config.settings import SettingsManager
from app.services.monetization import program_for, progress_text


class YouTubeAudienceSyncWorker(QThread):
    """Fetch channel statistics without freezing the desktop interface."""

    succeeded = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            from app.publishing.youtube_uploader import YouTubeUploader
            self.succeeded.emit(YouTubeUploader().get_channel_audience())
        except Exception as exc:  # shown only for a user-requested sync
            self.failed.emit(type(exc).__name__)


class PlatformTab(QWidget):
    """Individual platform configuration tab."""

    audience_sync_requested = Signal(bool)

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

        # Direct Post is a creator action, not a background toggle.  TikTok
        # review requires that the app visibly asks for permission before a
        # post is submitted, and this confirmation is intentionally reset when
        # the platform form is rebuilt.
        self.tiktok_post_approval = None
        if self.platform_key == "tiktok":
            self.tiktok_post_approval = QCheckBox(
                "I reviewed this TikTok post and approve a private AI-labeled upload"
            )
            self.tiktok_post_approval.setToolTip(
                "Required only when Generate-only is off. TikTok posts begin as private during app review."
            )
            self.tiktok_post_approval.toggled.connect(
                lambda checked: self.settings.set("tiktok_creator_approved", checked)
            )
            settings_layout.addWidget(self.tiktok_post_approval)

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
        api_layout.setSpacing(10)

        # Keep the primary account actions on one deliberate row.  The former
        # vertical stack could be compressed by Qt on some Windows themes,
        # making the buttons overlap and hiding their labels.
        # A fixed-height container prevents the help text below it from being
        # painted into the same visual band on Windows/Qt styles.
        actions_row = QWidget()
        actions_row.setMinimumHeight(42)
        actions_row.setMaximumHeight(42)
        self._account_actions_layout = QHBoxLayout(actions_row)
        self._account_actions_layout.setContentsMargins(0, 0, 0, 4)
        self._account_actions_layout.setSpacing(8)
        api_layout.addWidget(actions_row)

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
        self._account_actions_layout.addWidget(self.auth_btn)
        self.auth_btn.clicked.connect(self._authorize)
        self._compact_button(self.auth_btn)

        if self.platform_key in {"youtube_long", "youtube_shorts", "tiktok"}:
            self.import_btn = QPushButton("📁 Import OAuth client JSON")
            self.import_btn.setToolTip("Import the client configuration downloaded from the platform developer portal.")
            self.import_btn.clicked.connect(self._import_oauth_client_json)
            self._compact_button(self.import_btn)
            self._account_actions_layout.addWidget(self.import_btn)

        if self.platform_key in {"youtube_long", "youtube_shorts", "tiktok", "instagram"}:
            self.disconnect_btn = QPushButton("Disconnect account")
            self.disconnect_btn.setToolTip("Remove this computer's saved account authorization. Your developer client configuration is kept.")
            self.disconnect_btn.setStyleSheet("QPushButton { background: #4b5563; color: white; border-radius: 6px; padding: 8px 16px; } QPushButton:hover { background: #374151; }")
            self.disconnect_btn.clicked.connect(self._disconnect_account)
            self._compact_button(self.disconnect_btn)
            self._account_actions_layout.addWidget(self.disconnect_btn)

        self._account_actions_layout.addStretch(1)

        # Do not place a helper label directly below this row.  A few Windows
        # Qt styles paint the label into the final pixels of the button row.
        # The same instruction lives in the button tooltip and Setup Guide.
        api_group.setToolTip(
            "Import the official client JSON where required, then click Authorize. "
            "Use Setup Guide for step-by-step instructions."
        )

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
        self._extra_buttons_layout.setSpacing(8)
        api_layout.addLayout(self._extra_buttons_layout)

        layout.addWidget(api_group)

        # Monetization is useful context, but it must never be represented as
        # guaranteed income.  Only metrics retrieved through a supported,
        # official connection are used for progress calculations.
        monetization = QGroupBox("Monetization progress")
        monetization.setStyleSheet(api_group.styleSheet())
        monetization_layout = QVBoxLayout(monetization)
        self.monetization_label = QLabel()
        self.monetization_label.setWordWrap(True)
        self.monetization_label.setOpenExternalLinks(True)
        self.monetization_label.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        monetization_layout.addWidget(self.monetization_label)
        layout.addWidget(monetization)

        # The platform form is deliberately compact. Use the remaining space
        # to explain its status instead of leaving a blank, confusing panel.
        readiness = QGroupBox("Publishing readiness")
        readiness.setStyleSheet(api_group.styleSheet())
        readiness_layout = QVBoxLayout(readiness)
        self.readiness_label = QLabel()
        self.readiness_label.setWordWrap(True)
        self.readiness_label.setStyleSheet("color: #aaa; font-size: 12px; line-height: 1.4;")
        readiness_layout.addWidget(self.readiness_label)
        layout.addWidget(readiness)
        layout.addStretch()

        # Load current values
        self._load_settings()
        self._refresh_connection_status()
        self._refresh_readiness()
        self._refresh_monetization()

    def _load_settings(self):
        enabled = self.settings.get(f"platform_limits.{self.platform_key}.enabled", False)
        max_day = self.settings.get(f"platform_limits.{self.platform_key}.max_per_day", 3)

        self.enabled_cb.setChecked(enabled)
        self.max_per_day.setValue(max_day)
        if self.tiktok_post_approval:
            self.tiktok_post_approval.setChecked(self.settings.get("tiktok_creator_approved", False))

    def _on_enabled_toggled(self, checked: bool):
        self.settings.set(f"platform_limits.{self.platform_key}.enabled", checked)
        self._refresh_readiness()

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
            message = type(exc).__name__
            if message == "RefreshError":
                message = "Saved Google permission expired — click Authorize and approve the Google prompt"
            self.update_status(f"Authorization failed: {message}. See the setup guide for details.", False)

    def _sync_audience(self):
        """Ask the owning tab panel to perform a non-blocking metric refresh."""
        if self.platform_key in {"youtube_long", "youtube_shorts"}:
            self.audience_sync_requested.emit(True)
        else:
            self.audience_label.setText("Audience: official metric sync is not implemented for this platform yet")
            self.audience_label.setStyleSheet("color: #888; font-size: 12px;")

    @staticmethod
    def _compact_button(button: QPushButton):
        """Keep actions readable without allowing them to fill the whole tab.

        A Maximum/Fixed policy alone can collapse controls to a thin bar on
        some Windows/Qt style combinations.  Explicit dimensions preserve the
        text and make the action affordance usable for new customers.
        """
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        button.setMinimumHeight(36)
        button.setMaximumHeight(36)
        # Do not force every action to 230 px: a three-button OAuth row then
        # overflows smaller Windows displays.  The layout keeps each label at
        # its natural readable width and shares the remaining row space.
        button.setMinimumWidth(145)
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
        if self.tiktok_post_approval:
            self.settings.set("tiktok_creator_approved", self.tiktok_post_approval.isChecked())

    def update_status(self, status_text: str, is_ok: bool = False):
        color = "#22c55e" if is_ok else "#888"
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._refresh_readiness()

    def _refresh_readiness(self):
        """Turn unused panel space into a useful, honest next-step summary."""
        if not hasattr(self, "readiness_label"):
            return
        enabled = self.enabled_cb.isChecked()
        status = self.status_label.text().replace("Status: ", "")
        if self.platform_key in {"youtube_long", "youtube_shorts"}:
            capability = "Official YouTube upload and audience sync are available after OAuth authorization."
        elif self.platform_key == "tiktok":
            capability = "TikTok publishing requires an approved official developer app and authorization."
        else:
            capability = "This destination is shown for planning and setup; its production publisher is not verified yet."
        state = "Enabled for a future reviewed upload." if enabled else "Disabled — no uploads will be sent here."
        self.readiness_label.setText(f"Current state: {state}\nConnection: {status}\n\n{capability}\n\nUse Generate-only until you have reviewed a complete video and its metadata.")

    def _refresh_monetization(self, audience: dict | None = None):
        """Show the creator's progress without claiming eligibility or income."""
        program = program_for(self.platform_key)
        audience = audience or {}
        progress = progress_text(self.platform_key, audience)
        link = (
            f'<a href="{program.official_url}" style="color:#60a5fa;">Open official eligibility details</a>'
            if program.official_url else ""
        )
        extra = f"<br><br>{program.secondary_target}" if program.secondary_target else ""
        self.monetization_label.setText(
            f"<b>{program.name}</b><br>{progress}{extra}<br><br>"
            f"{program.overview}<br><span style='color:#94a3b8'>Eligibility is not a revenue guarantee; platform review and programme terms apply.</span><br>{link}"
        )

    def add_extra_button(self, button: QPushButton):
        """Add a button to the API Connection section (e.g. Setup Guide)."""
        self._extra_buttons_layout.addWidget(button)


class PlatformTabs(QTabWidget):
    """Tab widget with one tab per supported platform."""

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.tabs = {}
        self._audience_worker = None
        self._audience_timer = QTimer(self)
        self._audience_timer.setInterval(60 * 60 * 1000)  # once per hour
        self._audience_timer.timeout.connect(self.sync_youtube_audience)

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
                padding: 7px 9px;
                margin-right: 2px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
            }
            QTabBar::tab:hover {
                background: #3a3a3d;
            }
        """)

        # Brand icons make the destination clear without relying on emoji
        # rendering, which varies between Windows installations.
        # Resolve from the project package rather than the process working
        # directory. A packaged build may omit optional icons, so only create
        # a QIcon when the source asset is actually present; Qt otherwise
        # emits one warning per unavailable SVG on every startup.
        project_root = Path(__file__).resolve().parents[3]
        icon_dir = project_root / "assets" / "platform_icons"
        # Compact names keep every destination visible on a standard laptop
        # window. The full destination name remains available as a tooltip.
        platforms = [
            ("youtube_long", "YouTube", "youtube.svg", "YouTube Videos"),
            ("youtube_shorts", "YouTube Shorts", "youtube_shorts.svg", "YouTube Shorts"),
            ("tiktok", "TikTok", "tiktok.svg", "TikTok"),
            ("instagram", "Instagram", "instagram.svg", "Instagram"),
            ("x_twitter", "X", "x.svg", "X / Twitter"),
            ("rumble", "Rumble", "rumble.svg", "Rumble"),
            ("facebook", "Facebook", "facebook.svg", "Facebook"),
            ("snapchat", "Snapchat", "snapchat.svg", "Snapchat"),
        ]
        self.setIconSize(QSize(16, 16))
        self.tabBar().setUsesScrollButtons(False)

        for key, short_name, icon_name, full_name in platforms:
            tab = PlatformTab(key, full_name, settings)
            tab.audience_sync_requested.connect(self.sync_youtube_audience)
            icon_path = icon_dir / icon_name
            icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
            index = self.addTab(tab, icon, short_name)
            self.setTabToolTip(index, full_name)
            self.tabs[key] = tab

        # ── Add Setup Guide buttons to all platforms ──
        self._add_all_guide_buttons()
        self._restore_cached_youtube_audience()
        self._audience_timer.start()
        # A saved authorization can be refreshed shortly after launch. This
        # uses the cache if offline and never blocks the UI.
        QTimer.singleShot(1500, self.sync_youtube_audience)

    def save_all(self):
        """Save all tab settings."""
        for tab in self.tabs.values():
            tab.save()

    def get_enabled_platforms(self) -> list[str]:
        """Get list of enabled platform keys."""
        return [key for key, tab in self.tabs.items() if tab.enabled_cb.isChecked()]

    def _restore_cached_youtube_audience(self):
        cached = self.settings.get("audience_cache.youtube", {})
        if cached.get("name"):
            self._apply_youtube_audience(cached, cached=True)

    def sync_youtube_audience(self, user_requested: bool = False):
        """Refresh shared channel-level YouTube counts in a worker thread."""
        if self._audience_worker and self._audience_worker.isRunning():
            return
        if not self._youtube_token_has_audience_scope():
            if user_requested:
                self._show_youtube_sync_needed()
            return
        if user_requested:
            for key in ("youtube_long", "youtube_shorts"):
                self.tabs[key].audience_label.setText("Audience: syncing…")
                self.tabs[key].audience_label.setStyleSheet("color: #60a5fa; font-size: 12px;")
        self._audience_worker = YouTubeAudienceSyncWorker(self)
        self._audience_worker.succeeded.connect(self._on_youtube_audience_synced)
        self._audience_worker.failed.connect(
            lambda _error: self._show_youtube_sync_needed() if user_requested else None
        )
        self._audience_worker.finished.connect(self._clear_audience_worker)
        self._audience_worker.start()

    @staticmethod
    def _youtube_token_has_audience_scope() -> bool:
        """Avoid opening an OAuth consent page from a background timer."""
        token_path = Path("config/youtube_token.json")
        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
            scopes = set(payload.get("scopes", []))
            return {
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
            }.issubset(scopes)
        except (OSError, json.JSONDecodeError):
            return False

    def _on_youtube_audience_synced(self, stats: dict):
        payload = {
            "name": stats.get("name", "YouTube channel"),
            "subscribers": str(stats.get("subscribers", "hidden")),
            "views": str(stats.get("views", "0")),
            "synced_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        self.settings.set("audience_cache.youtube", payload)
        self._apply_youtube_audience(payload)

    def _apply_youtube_audience(self, stats: dict, cached: bool = False):
        raw_subscribers = str(stats.get("subscribers", "hidden"))
        subscribers = f"{int(raw_subscribers):,}" if raw_subscribers.isdigit() else "hidden by channel"
        raw_views = str(stats.get("views", "0"))
        views = f"{int(raw_views):,}" if raw_views.isdigit() else raw_views
        suffix = " (cached)" if cached else ""
        for key in ("youtube_long", "youtube_shorts"):
            self.tabs[key].audience_label.setText(
                f"Audience: {subscribers} subscribers • {views} channel views • {stats.get('name', 'YouTube channel')}{suffix}"
            )
            self.tabs[key].audience_label.setStyleSheet("color: #22c55e; font-size: 12px;")
            self.tabs[key]._refresh_monetization(stats)

    def _show_youtube_sync_needed(self):
        for key in ("youtube_long", "youtube_shorts"):
            self.tabs[key].audience_label.setText("Audience: re-authorize YouTube, then sync again")
            self.tabs[key].audience_label.setStyleSheet("color: #f59e0b; font-size: 12px;")

    def _clear_audience_worker(self):
        if self._audience_worker:
            self._audience_worker.deleteLater()
        self._audience_worker = None

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

    def _open_guide(self, platform_key: str):
        """Open the platform Setup Instructions dialog."""
        from app.dialogs.platform_setup_dialogs import PlatformSetupDialog
        guide_key = "youtube" if platform_key in {"youtube_long", "youtube_shorts"} else platform_key
        dialog = PlatformSetupDialog(guide_key, self)
        dialog.exec()
