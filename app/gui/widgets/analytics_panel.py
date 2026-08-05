"""Channel-first analytics and editorial idea review.

This panel intentionally reports only local/authorized channel data.  It does
not scrape other creators or auto-switch a channel to a random daily trend.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox

from app.ai.prompts.script_prompts import NICHES


class AnalyticsPanel(QWidget):
    """Show authorised audience cache and useful production signals."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Analytics & Topic Review")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(title)
        note = QLabel(
            "Channel-first recommendations: use your authorised performance data to improve your next ideas. "
            "This does not blindly chase daily trends or publish without review."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #cbd5e1;")
        layout.addWidget(note)

        audience = QGroupBox("YouTube audience")
        audience_layout = QVBoxLayout(audience)
        self.audience_label = QLabel()
        self.audience_label.setWordWrap(True)
        audience_layout.addWidget(self.audience_label)
        audience_hint = QLabel("Audience counts refresh hourly in Platforms after YouTube is authorised. Detailed retention, views, and subscriber-gain reports are the next official-API step.")
        audience_hint.setWordWrap(True)
        audience_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        audience_layout.addWidget(audience_hint)
        layout.addWidget(audience)

        production = QGroupBox("Local production health")
        production_layout = QVBoxLayout(production)
        self.production_label = QLabel()
        self.production_label.setWordWrap(True)
        production_layout.addWidget(self.production_label)
        layout.addWidget(production)

        ideas = QGroupBox("Approved topic pool")
        ideas_layout = QVBoxLayout(ideas)
        self.ideas_label = QLabel()
        self.ideas_label.setWordWrap(True)
        self.ideas_label.setStyleSheet("color: #dbeafe;")
        ideas_layout.addWidget(self.ideas_label)
        layout.addWidget(ideas)

        row = QHBoxLayout()
        refresh = QPushButton("Refresh local data")
        refresh.clicked.connect(self.refresh)
        row.addWidget(refresh)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        cached = self.settings.get("audience_cache.youtube", {})
        if cached.get("name"):
            subscribers = cached.get("subscribers", "hidden")
            views = cached.get("views", "0")
            synced = cached.get("synced_at", "unknown time")
            self.audience_label.setText(f"<b>{cached.get('name')}</b><br>{subscribers} subscribers · {views} channel views<br><span style='color:#94a3b8'>Last sync: {synced}</span>")
        else:
            self.audience_label.setText("No authorised YouTube audience data yet. Connect/re-authorise YouTube in Platforms, then choose Sync audience.")

        outputs = list(Path("projects/_output").glob("*/review_package.json")) if Path("projects/_output").exists() else []
        history_path = Path("projects/_content_history/editorial_history.json")
        try:
            history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else []
        except (OSError, json.JSONDecodeError):
            history = []
        self.production_label.setText(
            f"Review packages: <b>{len(outputs)}</b><br>Original script history entries: <b>{len(history)}</b><br>"
            "A complete render is still reviewed before any upload."
        )

        selected = self.settings.get("selected_niches", [self.settings.get("niche", "motivational")])
        selected = selected or ["motivational"]
        lines = []
        for key in selected[:3]:
            info = NICHES.get(key, {})
            enabled = self.settings.get("selected_subniches", {}).get(key) or info.get("subniches", [])
            label = info.get("name", key.replace("_", " ").title())
            lines.append(f"<b>{label}</b>: {', '.join(enabled[:8]) or 'No sub-topics selected'}")
        self.ideas_label.setText("<br><br>".join(lines))
