"""Log panel — real-time log output display."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from datetime import datetime


class LogPanel(QWidget):
    """Scrollable log output panel showing real-time pipeline status."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        title = QPushButton("📋 Pipeline Log")
        title.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #aaa;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
                padding: 4px 0;
            }
        """)
        title.setEnabled(False)
        header.addWidget(title)
        header.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #444;
                color: #888;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #333;
                color: #fff;
            }
        """)
        self.clear_btn.clicked.connect(self._clear)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        # Log output
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QTextEdit {
                background: #0d0d0f;
                color: #c0c0c0;
                border: 1px solid #2a2a2e;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        self.output.setMinimumHeight(200)
        layout.addWidget(self.output)

    def log(self, message: str):
        """Append a timestamped log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear(self):
        self.output.clear()

    def set_progress(self, stage: str, percent: int):
        """Update progress display."""
        self.log(f"📊 [{stage}] {percent}%")
