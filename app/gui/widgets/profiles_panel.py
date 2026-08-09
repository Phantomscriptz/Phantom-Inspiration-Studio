"""Profile chooser for separate creator-owned channel workspaces."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QListWidget, QPushButton, QInputDialog, QMessageBox

from app.services.profile_manager import ProfileManager


class ProfilesPanel(QWidget):
    profile_activated = Signal()

    def __init__(self, parent=None, can_switch=None):
        super().__init__(parent)
        self.manager = ProfileManager()
        self.can_switch = can_switch or (lambda: True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        heading = QLabel("Channel profiles")
        heading.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(heading)

        info = QGroupBox("Channel profiles")
        info_layout = QVBoxLayout(info)
        note = QLabel("Each profile has separate channel settings and local OAuth files. Only one profile is active at a time; review and publish as that channel only.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#cbd5e1;")
        info_layout.addWidget(note)
        layout.addWidget(info)

        profiles_group = QGroupBox("Your profiles")
        profiles_layout = QVBoxLayout(profiles_group)
        self.list = QListWidget()
        self.list.setMinimumHeight(150)
        self.list.setMaximumHeight(210)
        self.list.setStyleSheet("QListWidget { border: 1px solid #3f3f46; border-radius: 6px; padding: 4px; } QListWidget::item { padding: 8px; }")
        profiles_layout.addWidget(self.list)

        row = QHBoxLayout()
        create = QPushButton("Create channel profile")
        create.clicked.connect(self._create)
        activate = QPushButton("Use selected profile")
        activate.clicked.connect(self._activate)
        row.addWidget(create)
        row.addWidget(activate)
        row.addStretch(1)
        profiles_layout.addLayout(row)
        layout.addWidget(profiles_group)

        help_group = QGroupBox("How this works")
        help_layout = QVBoxLayout(help_group)
        help_text = QLabel(
            "Create one profile per genuinely separate channel or brand. A profile keeps its content choices, platform limits, "
            "and local authorization files together. Select a profile, then use Platforms to connect only that profile's accounts."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #cbd5e1;")
        help_layout.addWidget(help_text)
        layout.addWidget(help_group)
        layout.addStretch(1)
        self.refresh()

    def refresh(self):
        active = self.manager.active_id()
        self.list.clear()
        for profile in self.manager.profiles():
            label = profile["name"] + ("  — active" if profile["id"] == active else "")
            self.list.addItem(label)
            self.list.item(self.list.count() - 1).setData(Qt.UserRole, profile["id"])

    def _create(self):
        name, ok = QInputDialog.getText(self, "Create channel profile", "Channel/profile name:")
        if ok and name.strip():
            self.manager.create(name)
            self.refresh()

    def _activate(self):
        item = self.list.currentItem()
        if not item:
            QMessageBox.information(self, "Choose a profile", "Select a channel profile first.")
            return
        profile_id = item.data(Qt.UserRole)
        if profile_id == self.manager.active_id():
            return
        if not self.can_switch():
            QMessageBox.warning(
                self, "Generation active",
                "Stop the current video generation before switching channel profiles.",
            )
            return
        answer = QMessageBox.question(
            self, "Switch channel profile",
            "Switch the active channel settings and its saved local OAuth files now? Any active generation must be stopped first.",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            self.manager.activate(profile_id)
            self.profile_activated.emit()
