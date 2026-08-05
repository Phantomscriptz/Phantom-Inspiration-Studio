from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QStatusBar,
    QMessageBox,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt

from app.gui.widgets.sidebar import Sidebar
from app.gui.widgets.dashboard import Dashboard
from app.config.settings import SettingsManager
from app.workers.automation_worker import AutomationWorker
from app.services.ollama_model_manager import OllamaModelManager
from app.services.preflight import run_preflight


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = SettingsManager()
        self.worker = None
        self.model_manager = OllamaModelManager(self)

        self.setWindowTitle("Phantom Inspiration Studio")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        self.create_statusbar()
        self.create_ui()

        # Stats tracking
        self._videos_total = 0
        self._videos_today = 0
        self._uploaded = 0
        self._errors = 0

    def create_ui(self):
        """Create the main user interface."""
        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.nav_changed.connect(self._on_nav_changed)

        # ── Right-side stacked pages ──
        self.stack = QStackedWidget()

        # Page 0 — Dashboard (stats + control + log)
        self.dashboard = Dashboard(self.settings, self.model_manager)
        self.stack.addWidget(self.dashboard)                    # index 0

        # Page 1 — Platforms. This is the single authoritative platform view.
        platform_page = self._build_platforms_page()
        self.stack.addWidget(platform_page)                     # index 1

        from app.gui.widgets.guide_panel import GuidePanel
        self.guide_panel = GuidePanel(self.settings, self._troubleshooting_reset)
        self.stack.addWidget(self.guide_panel)                  # index 2
        from app.gui.widgets.storage_panel import StoragePanel
        self.storage_panel = StoragePanel()
        self.stack.addWidget(self.storage_panel)                # index 3
        from app.gui.widgets.analytics_panel import AnalyticsPanel
        self.analytics_panel = AnalyticsPanel(self.settings)
        self.stack.addWidget(self.analytics_panel)              # index 4

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)

        # Connect control bar signals
        self.dashboard.control_bar.start_clicked.connect(self._on_start)
        self.dashboard.control_bar.stop_clicked.connect(self._on_stop)

    # ------------------------------------------------------------------
    # Sidebar pages
    # ------------------------------------------------------------------

    def _build_platforms_page(self) -> QWidget:
        """A lightweight platforms config page (reuses platform_tabs)."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 20, 20, 20)
        from app.gui.widgets.platform_tabs import PlatformTabs
        self.platform_tabs = PlatformTabs(self.settings)
        lay.addWidget(self.platform_tabs)
        return page

    def _on_nav_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 4:
            self.analytics_panel.refresh()
        labels = {0: "Dashboard", 1: "Platforms", 2: "Guide", 3: "Storage", 4: "Analytics"}
        self.statusBar().showMessage(f"View: {labels.get(index, '')}")

    def create_statusbar(self):
        """Create the status bar."""
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    # ------------------------------------------------------------------
    # Automation Control
    # ------------------------------------------------------------------

    def _on_start(self):
        """Start the automation pipeline."""
        self.dashboard.save_settings()
        self.platform_tabs.save_all()
        self.dashboard.show_log()

        # Get worker config from settings
        config = self.settings.to_worker_config()
        checks = run_preflight(config)
        blocking = [check for check in checks if check.required and not check.ok]
        if blocking:
            details = "\n".join(f"• {check.label}: {check.detail}" for check in blocking)
            QMessageBox.warning(self, "Preflight check failed", "Fix these before generating a video:\n\n" + details)
            self.dashboard.log("⚠️ Preflight stopped the run: " + "; ".join(check.label for check in blocking))
            return
        warnings = [check for check in checks if not check.required or not check.ok]
        for check in warnings:
            self.dashboard.log(f"ℹ️ Preflight — {check.label}: {check.detail}")

        # Create and start worker
        self.worker = AutomationWorker(config)
        self.worker.log_message.connect(self.dashboard.log)
        self.worker.status_change.connect(self._on_status_change)
        self.worker.progress_update.connect(self.dashboard.log_panel.set_progress)
        self.worker.video_generated.connect(self._on_video_generated)
        self.worker.upload_complete.connect(self._on_upload_complete)
        self.worker.pipeline_complete.connect(self._on_pipeline_complete)
        self.worker.error_occurred.connect(self._on_worker_error)

        self.dashboard.log("🚀 Starting automation pipeline...")
        selected_niches = config.get("selected_niches", [])
        if config.get("randomize_niches"):
            niche_label = "random from " + ", ".join(selected_niches or ["all configured niches"])
        else:
            niche_label = ", ".join(selected_niches or [config.get("niche", "not selected")])
        self.dashboard.log(f"  Niche selection: {niche_label}")
        self.dashboard.log(f"  Format: {config.get('video_format')}")
        self.dashboard.log(f"  Platforms: {', '.join(config.get('enabled_platforms', []))}")
        self.dashboard.log(f"  Max videos: {config.get('max_videos_per_run', 'unlimited')}")

        self.worker.start()

    def _on_stop(self):
        """Stop the automation pipeline."""
        if self.worker and self.worker.isRunning():
            self.dashboard.log("🛑 Stopping automation...")
            self.worker.stop()
            self.worker.wait(5000)
            self.dashboard.control_bar.reset()
            self.statusBar().showMessage("Stopped")

    def _on_status_change(self, status: str):
        self.statusBar().showMessage(status)

    def _on_video_generated(self, path: str):
        self._videos_total += 1
        self._videos_today += 1
        self.dashboard.update_stat("videos_total", str(self._videos_total))
        self.dashboard.update_stat("videos_today", str(self._videos_today))
        self.dashboard.control_bar.update_stats(self._videos_total, self._videos_today)

    def _on_upload_complete(self, platform: str, success: bool):
        if success:
            self._uploaded += 1
            self.dashboard.update_stat("uploaded", str(self._uploaded))
        else:
            self._errors += 1
            self.dashboard.update_stat("errors", str(self._errors))

    def _on_pipeline_complete(self, total: int):
        self.dashboard.control_bar.reset()
        self.dashboard.log(f"🏁 Pipeline complete! {total} videos produced.")
        self.statusBar().showMessage(f"Complete — {total} videos")

    def _on_worker_error(self, error: str):
        self.dashboard.log(f"❌ ERROR: {error}")
        self._errors += 1
        self.dashboard.update_stat("errors", str(self._errors))

    def _troubleshooting_reset(self):
        """Stop active work and remove only disposable runtime-state files."""
        self._on_stop()
        self.settings.clear_temporary_runtime_state()
        self.statusBar().showMessage("Temporary runtime state cleared")

    def closeEvent(self, event):
        """Clean up on close."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()
