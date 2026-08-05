from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox

from app.services.storage_manager import StorageManager


class StoragePanel(QWidget):
    """Show space use and offer one carefully scoped cleanup action."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = StorageManager()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        title = QLabel("Storage & Cleanup")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #ccc; font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.summary_label)
        self.refresh_btn = QPushButton("Refresh storage totals")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        self.clear_btn = QPushButton("Delete generated projects and caches")
        self.clear_btn.setStyleSheet("QPushButton { background: #b91c1c; color: white; border: none; border-radius: 6px; padding: 10px 16px; font-weight: bold; } QPushButton:hover { background: #dc2626; }")
        self.clear_btn.clicked.connect(self.clear_generated)
        layout.addWidget(self.clear_btn)
        note = QLabel("This permanently deletes generated videos, thumbnails, audio, temporary images, export copies, render cache, and local upload/history records. It preserves B-roll, voice samples, AI models, settings, OAuth credentials, and your manually created project files.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #fbbf24; font-size: 12px;")
        layout.addWidget(note)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        summary = self.manager.summary()
        self.summary_label.setText(
            f"Generated projects and caches: <b>{self.manager.format_size(summary['generated_bytes'])}</b><br>"
            f"Preserved library, models, and configuration: <b>{self.manager.format_size(summary['preserved_bytes'])}</b>"
        )

    def clear_generated(self):
        summary = self.manager.summary()
        answer = QMessageBox.warning(
            self, "Delete generated media?",
            f"This will permanently remove {self.manager.format_size(summary['generated_bytes'])} of generated videos, audio, images, caches, exports, and local run history.\n\nB-roll, models, credentials, settings, and manual projects will remain. This cannot be undone.",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if answer == QMessageBox.Yes:
            self.manager.clear_generated_media()
            self.refresh()
