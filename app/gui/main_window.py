from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QToolBar,
    QStatusBar,
)
from PySide6.QtGui import QAction

from app.gui.widgets.sidebar import Sidebar
from app.gui.widgets.dashboard import Dashboard

from app.dialogs.new_project_dialog import NewProjectDialog
from app.controllers.project_manager import ProjectManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.project_manager = ProjectManager()

        self.setWindowTitle("Phantom Inspiration Studio")
        self.resize(1600, 900)

        self.create_toolbar()
        self.create_statusbar()
        self.create_ui()

    def create_ui(self):
        """Create the main user interface."""

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        self.sidebar = Sidebar()
        self.dashboard = Dashboard()

        layout.addWidget(self.sidebar)
        layout.addWidget(self.dashboard)

    def create_toolbar(self):
        """Create the application's toolbar."""

        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        self.addToolBar(toolbar)

        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)

        open_action = QAction("Open Project", self)
        settings_action = QAction("Settings", self)

        toolbar.addAction(new_action)
        toolbar.addSeparator()

        toolbar.addAction(open_action)
        toolbar.addSeparator()

        toolbar.addAction(settings_action)

    def create_statusbar(self):
        """Create the status bar."""

        status = QStatusBar()
        status.showMessage("Ready")

        self.setStatusBar(status)

    def new_project(self):
        """Open the New Project dialog."""

        dialog = NewProjectDialog()

        if dialog.exec():

            name = dialog.project_name().strip()

            if not name:
                self.statusBar().showMessage("Project name cannot be empty.")
                return

            self.project_manager.create_project(name)

            self.statusBar().showMessage(
                f"Project '{name}' created successfully."
            )