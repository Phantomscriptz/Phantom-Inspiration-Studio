"""Beginner-friendly local setup readiness screen."""

from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QMessageBox, QScrollArea,
)


class SetupPanel(QWidget):
    """Show the actual local prerequisites without pretending they are bundled."""

    def __init__(self, settings, model_manager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.model_manager = model_manager
        self.model_manager.finished.connect(lambda *_args: self.refresh())
        self.model_manager.state_changed.connect(self.refresh)

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(14)

        heading = QLabel("Setup wizard")
        heading.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        self.layout.addWidget(heading)
        note = QLabel(
            "This page checks the tools on this computer. It never reads license keys or sends your account files anywhere. "
            "Install buttons always use the provider's current official installer or the app's selected local model."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #cbd5e1;")
        self.layout.addWidget(note)

        self.core_group = self._group("Core video tools")
        self.core_label = QLabel()
        self.core_label.setWordWrap(True)
        self.core_group.layout().addWidget(self.core_label)
        self.layout.addWidget(self.core_group)

        self.ai_group = self._group("Local AI and speech")
        self.ai_label = QLabel()
        self.ai_label.setWordWrap(True)
        self.ai_group.layout().addWidget(self.ai_label)
        self.install_model_btn = QPushButton("Install selected Ollama model")
        self.install_model_btn.clicked.connect(self._install_selected_model)
        self.ai_group.layout().addWidget(self.install_model_btn)
        self.layout.addWidget(self.ai_group)

        self.optional_group = self._group("Optional professional tools")
        self.optional_label = QLabel()
        self.optional_label.setWordWrap(True)
        self.optional_group.layout().addWidget(self.optional_label)
        self.layout.addWidget(self.optional_group)

        actions = QHBoxLayout()
        refresh = QPushButton("Check again")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        actions.addStretch(1)
        self.layout.addLayout(actions)
        self.layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.refresh()

    @staticmethod
    def _group(title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet(
            "QGroupBox { font-size: 13px; font-weight: bold; color: #ddd; "
            "border: 1px solid #333; border-radius: 8px; margin-top: 12px; padding: 14px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )
        QVBoxLayout(group)
        return group

    @staticmethod
    def _state(ok: bool, label: str, detail: str = "") -> str:
        icon = "✅" if ok else "⚠️"
        return f"{icon} <b>{label}</b>{(' — ' + detail) if detail else ''}"

    def refresh(self):
        ffmpeg = bool(shutil.which("ffmpeg"))
        python = bool(shutil.which("python"))
        whisperx = Path(".venv-whisperx/Scripts/python.exe").exists()
        ollama = bool(shutil.which("ollama"))
        model = self.settings.get("ollama_model", "qwen2.5:14b")
        model_ready = False
        if ollama:
            try:
                from app.ai.providers.ollama_client import OllamaClient
                model_ready = OllamaClient().is_alive() and OllamaClient().model_exists(model)
            except Exception:
                model_ready = False
        self.core_label.setText("<br>".join([
            self._state(python, "Python runtime", "development runtime detected" if python else "missing"),
            self._state(ffmpeg, "FFmpeg", "ready for rendering" if ffmpeg else "missing — install from the official FFmpeg provider"),
        ]))
        self.ai_label.setText("<br>".join([
            self._state(ollama, "Ollama", "installed" if ollama else "missing — install Ollama first"),
            self._state(model_ready, f"Selected model: {model}", "ready" if model_ready else "not installed"),
            self._state(whisperx, "WhisperX alignment environment", "ready" if whisperx else "optional; captions use the built-in timing fallback"),
        ]))
        self.install_model_btn.setEnabled(ollama and not model_ready)
        self.install_model_btn.setToolTip("Downloads the selected Ollama model using the official local Ollama service." if ollama else "Install Ollama first.")

        adobe_root = Path(r"C:\Program Files\Adobe")
        resolve_paths = [
            Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe"),
            Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve\DaVinci Resolve.exe"),
        ]
        adobe = adobe_root.exists()
        resolve = any(path.exists() for path in resolve_paths)
        blender = bool(shutil.which("blender")) or Path(r"C:\Program Files\Blender Foundation").exists()
        self.optional_label.setText("<br>".join([
            self._state(adobe, "Adobe applications", "detected; optional, not required" if adobe else "not detected"),
            self._state(resolve, "DaVinci Resolve", "detected; optional, not required" if resolve else "not detected"),
            self._state(blender, "Blender", "detected; optional, not required" if blender else "not detected"),
            "These applications remain separately licensed. Future integrations can export a review-ready timeline or use a creator-owned template; they are not bundled into Phantom.",
        ]))

    def _install_selected_model(self):
        model = self.settings.get("ollama_model", "qwen2.5:14b")
        answer = QMessageBox.question(
            self, "Install local model", f"Download {model} through Ollama now? This may take several GB.",
            QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel,
        )
        if answer != QMessageBox.Yes:
            return
        self.install_model_btn.setEnabled(False)
        self.install_model_btn.setText("Downloading model — see Settings for progress")
        self.model_manager.install(model)
