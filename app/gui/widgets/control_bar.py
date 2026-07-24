"""Control bar — Start/Stop buttons and status indicator."""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame,
)
from PySide6.QtCore import Qt, Signal, Property
from PySide6.QtGui import QColor, QPainter


class StatusIndicator(QWidget):
    """A small colored circle indicating running/stopped status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._color = QColor(100, 100, 100)  # gray = stopped

    def set_running(self, running: bool):
        self._color = QColor(34, 197, 94) if running else QColor(100, 100, 100)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(1, 1, 14, 14)


class ControlBar(QFrame):
    """Top control bar with Start/Stop buttons and status."""

    start_clicked = Signal()
    stop_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ControlBar {
                background: #1a1a1e;
                border-radius: 12px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        # Status indicator
        self.status_light = StatusIndicator()
        layout.addWidget(self.status_light)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 13px; color: #888; font-weight: 500;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Stats
        self.stats_label = QLabel("Videos: 0 | Today: 0")
        self.stats_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.stats_label)

        layout.addSpacing(20)

        # Start button
        self.start_btn = QPushButton("▶  Start Automation")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.setMinimumWidth(160)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #22c55e;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #16a34a;
            }
            QPushButton:disabled {
                background: #374151;
                color: #6b7280;
            }
        """)
        self.start_btn.clicked.connect(self._on_start)
        layout.addWidget(self.start_btn)

        # Stop button
        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setMinimumHeight(38)
        self.stop_btn.setMinimumWidth(120)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:disabled {
                background: #374151;
                color: #6b7280;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop)
        layout.addWidget(self.stop_btn)

    def _on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_light.set_running(True)
        self.status_label.setText("Running")
        self.status_label.setStyleSheet("font-size: 13px; color: #22c55e; font-weight: 500;")
        self.start_clicked.emit()

    def _on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_light.set_running(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("font-size: 13px; color: #ef4444; font-weight: 500;")
        self.stop_clicked.emit()

    def reset(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_light.set_running(False)
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-size: 13px; color: #888; font-weight: 500;")

    def update_stats(self, total: int, today: int):
        self.stats_label.setText(f"Videos: {total} | Today: {today}")
