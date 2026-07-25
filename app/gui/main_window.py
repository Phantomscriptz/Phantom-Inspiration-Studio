from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QToolBar,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from app.gui.widgets.sidebar import Sidebar
from app.gui.widgets.dashboard import Dashboard
from app.config.settings import SettingsManager
from app.workers.automation_worker import AutomationWorker
from app.dialogs.new_project_dialog import NewProjectDialog
from app.controllers.project_manager import ProjectManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.project_manager = ProjectManager()
        self.settings = SettingsManager()
        self.worker = None

        self.setWindowTitle("Phantom Inspiration Studio")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)

        self.create_toolbar()
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
        self.dashboard = Dashboard(self.settings)
        self.stack.addWidget(self.dashboard)                    # index 0

        # Page 1 — Platforms (placeholder; dashboard tabs still accessible)
        platform_page = self._build_platforms_page()
        self.stack.addWidget(platform_page)                     # index 1

        # Page 2 — Settings
        settings_page = self._build_settings_page()
        self.stack.addWidget(settings_page)                     # index 2

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

    def _build_settings_page(self) -> QWidget:
        """A lightweight settings page."""
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 20, 20, 20)
        from app.gui.widgets.content_settings import ContentSettingsPanel
        self.settings_panel = ContentSettingsPanel(self.settings)
        lay.addWidget(self.settings_panel)
        return page

    def _on_nav_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        labels = {0: "Dashboard", 1: "Platforms", 2: "Settings"}
        self.statusBar().showMessage(f"View: {labels.get(index, '')}")

    def create_toolbar(self):
        """Create the application's toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)

        open_action = QAction("Open Project", self)
        save_action = QAction("Save Settings", self)
        save_action.triggered.connect(self._save_settings)

        toolbar.addAction(new_action)
        toolbar.addSeparator()
        toolbar.addAction(open_action)
        toolbar.addSeparator()
        toolbar.addAction(save_action)

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

        # Get worker config from settings
        config = self.settings.to_worker_config()

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
        self.dashboard.log(f"  Niche: {config.get('niche')}")
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

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _save_settings(self):
        self.dashboard.save_settings()
        # Also save settings from the standalone settings panel
        if hasattr(self, 'settings_panel'):
            self.settings_panel.save()
        self.statusBar().showMessage("Settings saved")

    def new_project(self):
        """Open the New Project dialog."""
        dialog = NewProjectDialog()

        if dialog.exec():
            name = dialog.project_name().strip()

            if not name:
                self.statusBar().showMessage("Project name cannot be empty.")
                return

            self.project_manager.create_project(name)
            self.statusBar().showMessage(f"Project '{name}' created successfully.")

    def closeEvent(self, event):
        """Clean up on close."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()