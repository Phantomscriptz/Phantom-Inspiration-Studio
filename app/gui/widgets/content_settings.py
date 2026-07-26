"""Content settings panel — niche setup popup, voice, automation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QLineEdit, QSpinBox,
    QCheckBox, QPushButton, QDialog, QDialogButtonBox, QScrollArea, QTextEdit,
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.config.settings import SettingsManager
from app.ai.prompts.script_prompts import NICHES
from app.ai.voice.edge_tts_provider import ENGLISH_VOICES
from app.ai.providers.ollama_client import get_client
from app.ai.voice.edge_tts_provider import EdgeTTSProvider


class VoicePreviewWorker(QThread):
    """Build a short cached voice sample without freezing the interface."""
    ready = Signal(str)
    failed = Signal(str)

    def __init__(self, voice_id: str, parent=None):
        super().__init__(parent)
        self.voice_id = voice_id

    def run(self):
        try:
            from pathlib import Path
            safe_name = self.voice_id.replace("/", "_").replace("\\", "_")
            path = Path("projects/_voice_samples") / f"{safe_name}.mp3"
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                EdgeTTSProvider(output_dir=str(path.parent)).generate(
                    "This is a short Phantom voice preview. Choose the voice that feels right for your channel.",
                    voice=self.voice_id, output_path=str(path),
                )
            self.ready.emit(str(path.resolve()))
        except Exception as exc:
            self.failed.emit(str(exc))


# ============================================================================
# Niche Setup Popup Dialog
# ============================================================================
class NicheSetupDialog(QDialog):
    """Popup: pick which niches to use, or randomize."""

    def __init__(self, selected_niches: list[str], randomize: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Content Niches Setup")
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: #ddd; }
            QLabel  { color: #ddd; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("🎬 Content Niches")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #5B9BD5;")
        layout.addWidget(header)

        desc = QLabel(
            "Select which niches Phantom will create content for.\n"
            "If 'Randomize' is checked, a random niche is picked per video."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)

        # Randomize toggle
        self.randomize_cb = QCheckBox("🎲  Randomize niche per video")
        self.randomize_cb.setChecked(randomize)
        self.randomize_cb.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
        self.randomize_cb.toggled.connect(self._on_randomize_toggled)
        layout.addWidget(self.randomize_cb)

        layout.addSpacing(4)

        # Scrollable niche checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        self.niche_layout = QVBoxLayout(scroll_content)
        self.niche_layout.setSpacing(4)

        self._niche_checks: dict[str, QCheckBox] = {}
        for key, info in NICHES.items():
            cb = QCheckBox(f"  {info['name']}   —   {info.get('tone', '')}   |   RPM {info.get('rpm_range', '?')}")
            cb.setChecked(key in selected_niches)
            cb.setStyleSheet("""
                QCheckBox { font-size: 12px; color: #ccc; padding: 6px 4px; }
                QCheckBox:hover { color: white; }
            """)
            self.niche_layout.addWidget(cb)
            self._niche_checks[key] = cb

        self.niche_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Apply initial state
        self._on_randomize_toggled(randomize)

    def _on_randomize_toggled(self, checked: bool):
        """Grey out individual niches when randomize is on."""
        for cb in self._niche_checks.values():
            cb.setEnabled(not checked)
            if checked:
                cb.setStyleSheet("QCheckBox { font-size: 12px; color: #555; padding: 6px 4px; }")
            else:
                cb.setStyleSheet("QCheckBox { font-size: 12px; color: #ccc; padding: 6px 4px; }")

    def get_selection(self) -> tuple[list[str], bool]:
        """Return (selected_keys, randomize)."""
        selected = [k for k, cb in self._niche_checks.items() if cb.isChecked()]
        return selected, self.randomize_cb.isChecked()


# ============================================================================
# Main Content Settings Panel
# ============================================================================
class ContentSettingsPanel(QWidget):
    """Panel for configuring content generation settings."""

    def __init__(self, settings: SettingsManager, model_manager=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.model_manager = model_manager
        self.preview_worker = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Niche Setup ---
        niche_group = QGroupBox("Content Niche")
        niche_group.setStyleSheet(self._group_style())
        niche_layout = QVBoxLayout(niche_group)

        self._selected_niches = self.settings.get("selected_niches", ["did_you_know"])
        self._randomize_niches = self.settings.get("randomize_niches", False)

        niche_info_row = QHBoxLayout()
        self.niche_label = QLabel(self._format_niche_summary())
        self.niche_label.setStyleSheet("color: #ccc; font-size: 12px;")
        self.niche_label.setWordWrap(True)
        niche_info_row.addWidget(self.niche_label, 1)

        self.niche_setup_btn = QPushButton("⚙  Setup Niches")
        self.niche_setup_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6; color: white; border: none;
                border-radius: 6px; padding: 10px 18px; font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        self.niche_setup_btn.clicked.connect(self._open_niche_setup)
        niche_info_row.addWidget(self.niche_setup_btn)
        niche_layout.addLayout(niche_info_row)

        # Topic input
        niche_layout.addSpacing(6)
        niche_layout.addWidget(QLabel("Topic (leave empty for AI-generated):"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g., The most haunted places in America")
        self.topic_input.setStyleSheet(self._input_style())
        niche_layout.addWidget(self.topic_input)

        layout.addWidget(niche_group)

        # --- Voice Selection ---
        voice_group = QGroupBox("Voice")
        voice_group.setStyleSheet(self._group_style())
        voice_layout = QVBoxLayout(voice_group)

        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet(self._combo_style())
        self.voice_combo.addItem("🎲 Random (pick a different voice each video)", "random")
        self.voice_combo.insertSeparator(1)
        for display_name, voice_id, gender, accent, desc in ENGLISH_VOICES:
            self.voice_combo.addItem(display_name, voice_id)
        voice_row.addWidget(self.voice_combo)
        self.preview_btn = QPushButton("▶ Play sample")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._toggle_voice_preview)
        voice_row.addWidget(self.preview_btn)
        voice_row.addStretch()
        voice_layout.addLayout(voice_row)

        self.voice_desc_label = QLabel("")
        self.voice_desc_label.setStyleSheet("color: #888; font-style: italic; padding: 2px 8px;")
        self.voice_desc_label.setWordWrap(True)
        voice_layout.addWidget(self.voice_desc_label)
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.85)
        self.media_player = QMediaPlayer(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.playbackStateChanged.connect(self._on_preview_state_changed)

        layout.addWidget(voice_group)

        # --- AI Settings (simplified) ---
        ai_group = QGroupBox("AI Model")
        ai_group.setStyleSheet(self._group_style())
        ai_layout = QVBoxLayout(ai_group)

        ai_desc = QLabel(
            "Phantom automatically selects the best AI model for script generation.\n"
            "The local Ollama model (qwen2.5:7b) is fast, free, and produces great scripts."
        )
        ai_desc.setWordWrap(True)
        ai_desc.setStyleSheet("color: #888; font-size: 12px;")
        ai_layout.addWidget(ai_desc)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet(self._combo_style())
        self.model_combo.addItems([
            "qwen2.5:7b (Recommended — fast & free)",
            "qwen2.5:14b (Better quality, slower)",
            "llama3.1:8b (Alternative)",
        ])
        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        ai_layout.addLayout(model_row)

        model_status_row = QHBoxLayout()
        self.model_status = QLabel("Checking local Ollama models…")
        self.model_status.setWordWrap(True)
        self.model_status.setStyleSheet("color: #888; font-size: 12px;")
        model_status_row.addWidget(self.model_status, 1)

        self.install_model_btn = QPushButton("Install selected model")
        self.install_model_btn.setEnabled(False)
        self.install_model_btn.setToolTip("Downloads the selected Ollama model only when it is missing.")
        self.install_model_btn.clicked.connect(self._install_selected_model)
        model_status_row.addWidget(self.install_model_btn)
        ai_layout.addLayout(model_status_row)

        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setVisible(False)
        self.install_log.setMinimumHeight(110)
        self.install_log.setStyleSheet(
            "background: #171717; color: #d1d5db; border: 1px solid #444; "
            "border-radius: 4px; font-family: Consolas, monospace; font-size: 11px;"
        )
        ai_layout.addWidget(self.install_log)

        self._install_output = ""
        if self.model_manager:
            self.model_manager.started.connect(self._on_model_install_started)
            self.model_manager.output.connect(self._read_model_install_output)
            self.model_manager.finished.connect(self._on_model_install_finished)
            self.model_manager.state_changed.connect(self._refresh_model_status)
        self.model_combo.currentIndexChanged.connect(self._refresh_model_status)

        layout.addWidget(ai_group)

        # --- Automation ---
        auto_group = QGroupBox("Automation Limits")
        auto_group.setStyleSheet(self._group_style())
        auto_layout = QVBoxLayout(auto_group)

        max_row = QHBoxLayout()
        max_row.addWidget(QLabel("Max videos per run (0 = unlimited):"))
        self.max_videos = QSpinBox()
        self.max_videos.setRange(0, 999)
        self.max_videos.setStyleSheet(self._spin_style())
        max_row.addWidget(self.max_videos)
        max_row.addStretch()
        auto_layout.addLayout(max_row)

        gap_row = QHBoxLayout()
        gap_row.addWidget(QLabel("Gap between videos (seconds):"))
        self.gap_min = QSpinBox()
        self.gap_min.setRange(10, 3600)
        self.gap_min.setStyleSheet(self._spin_style())
        gap_row.addWidget(self.gap_min)
        gap_row.addWidget(QLabel("to"))
        self.gap_max = QSpinBox()
        self.gap_max.setRange(10, 3600)
        self.gap_max.setStyleSheet(self._spin_style())
        gap_row.addWidget(self.gap_max)
        gap_row.addStretch()
        auto_layout.addLayout(gap_row)

        self.review_before_publish = QCheckBox("Generate only — review each video before publishing")
        self.review_before_publish.setToolTip("When enabled, Start Automation creates the video and metadata but never uploads it.")
        self.review_before_publish.setStyleSheet("font-size: 12px; color: #fbbf24; padding: 4px;")
        auto_layout.addWidget(self.review_before_publish)

        layout.addWidget(auto_group)
        layout.addStretch()

        self._load_settings()
        self._connect_auto_save()
        self._refresh_model_status()

    # ------------------------------------------------------------------
    # Niche setup
    # ------------------------------------------------------------------

    def _open_niche_setup(self):
        dialog = NicheSetupDialog(self._selected_niches, self._randomize_niches, self)
        if dialog.exec() == QDialog.Accepted:
            self._selected_niches, self._randomize_niches = dialog.get_selection()
            self.settings.set("selected_niches", self._selected_niches)
            self.settings.set("randomize_niches", self._randomize_niches)
            self.niche_label.setText(self._format_niche_summary())

    def _format_niche_summary(self) -> str:
        if self._randomize_niches:
            return f"🎲 Randomize — any of {len(NICHES)} niches per video"
        count = len(self._selected_niches)
        if count == 0:
            return "⚠️ No niches selected — click Setup"
        if count == 1:
            key = self._selected_niches[0]
            name = NICHES.get(key, {}).get("name", key)
            return f"Selected: {name}"
        names = [NICHES.get(k, {}).get("name", k) for k in self._selected_niches[:3]]
        extra = count - 3
        txt = ", ".join(names)
        if extra > 0:
            txt += f" +{extra} more"
        return f"Selected ({count}): {txt}"

    # ------------------------------------------------------------------
    # Voice
    # ------------------------------------------------------------------

    def _on_voice_changed(self, index):
        voice_id = self.voice_combo.currentData()
        self.media_player.stop()
        self.preview_btn.setText("▶ Play sample")
        self.preview_btn.setEnabled(voice_id != "random")
        if voice_id == "random":
            self.voice_desc_label.setText(
                "A random voice will be picked for each video — keeps your channel fresh!"
            )
        else:
            for display_name, vid, gender, accent, desc in ENGLISH_VOICES:
                if vid == voice_id:
                    self.voice_desc_label.setText(f"{gender} • {accent} accent — {desc}")
                    break
            else:
                self.voice_desc_label.setText("")

    def _toggle_voice_preview(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.stop()
            return
        voice_id = self.voice_combo.currentData()
        if not voice_id or voice_id == "random":
            return
        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Preparing sample…")
        self.preview_worker = VoicePreviewWorker(voice_id, self)
        self.preview_worker.ready.connect(self._play_voice_preview)
        self.preview_worker.failed.connect(self._voice_preview_failed)
        self.preview_worker.finished.connect(self.preview_worker.deleteLater)
        self.preview_worker.start()

    def _play_voice_preview(self, path: str):
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.media_player.play()
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("■ Stop sample")

    def _voice_preview_failed(self, message: str):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("▶ Play sample")
        self.voice_desc_label.setText(f"Preview unavailable: {message}")

    def _on_preview_state_changed(self, state):
        if state != QMediaPlayer.PlayingState:
            self.preview_btn.setText("▶ Play sample")

    # ------------------------------------------------------------------
    # Ollama model status / installation
    # ------------------------------------------------------------------

    def _selected_model_name(self) -> str:
        return self.model_combo.currentText().split(" (")[0]

    def _refresh_model_status(self):
        model = self._selected_model_name()
        if self.model_manager and self.model_manager.is_running:
            if self.model_manager.model == model:
                self.model_status.setText(f"⬇️ Downloading {model} in the background — you can switch pages.")
                self.model_status.setStyleSheet("color: #60a5fa; font-size: 12px;")
                self.install_model_btn.setEnabled(False)
                self.install_log.setPlainText("\n".join(self.model_manager.log_lines[-16:]))
                self.install_log.setVisible(True)
            else:
                self.model_status.setText(f"⬇️ Downloading {self.model_manager.model} in the background.")
                self.install_model_btn.setEnabled(False)
            return
        try:
            client = get_client()
            if not client.is_alive():
                self.model_status.setText("⚠️ Ollama is not running. Start Ollama, then refresh this page.")
                self.model_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
                self.install_model_btn.setEnabled(False)
                return
            installed = {item.get("name", "") for item in client.list_models()}
            if model in installed:
                self.model_status.setText(f"✅ {model} is installed and ready.")
                self.model_status.setStyleSheet("color: #22c55e; font-size: 12px;")
                self.install_model_btn.setEnabled(False)
            else:
                self.model_status.setText(f"⚠️ {model} is missing. Install it to use this selection.")
                self.model_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
                self.install_model_btn.setEnabled(True)
        except Exception:
            self.model_status.setText("⚠️ Could not check Ollama. Verify that it is installed and running.")
            self.model_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
            self.install_model_btn.setEnabled(False)

    def _install_selected_model(self):
        model = self._selected_model_name()
        if not self.model_manager:
            self.model_status.setText("❌ Model installer is unavailable.")
            return
        self.install_model_btn.setEnabled(False)
        self.model_manager.install(model)

    def _on_model_install_started(self, model: str):
        if model != self._selected_model_name():
            return
        self.model_status.setText(f"⬇️ Downloading {model}. You can switch pages while it runs.")
        self.model_status.setStyleSheet("color: #60a5fa; font-size: 12px;")
        self.install_log.setPlainText("\n".join(self.model_manager.log_lines))
        self.install_log.setVisible(True)

    def _read_model_install_output(self, latest_line: str):
        """Show Ollama's live pull output, including layer and download progress."""
        lines = self.model_manager.log_lines if self.model_manager else []
        self.install_log.setPlainText("\n".join(lines[-16:]))
        scrollbar = self.install_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        if lines:
            self.model_status.setText(f"⬇️ {latest_line}")

    def _on_model_install_finished(self, model, success, message):
        if model != self._selected_model_name():
            return
        if success:
            self.install_log.append("\n✅ Download complete. Verifying installation…")
            self._refresh_model_status()
        else:
            self.install_log.append("\n❌ Ollama exited before the download completed.")
            self.model_status.setText("❌ Model installation failed. Make sure Ollama is running and try again.")
            self.model_status.setStyleSheet("color: #ef4444; font-size: 12px;")
            self.install_model_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_settings(self):
        self.topic_input.setText(self.settings.get("topic", ""))

        model = self.settings.get("ollama_model", "qwen2.5:7b")
        # Match by prefix (handles both old plain names and new "name (desc)" format)
        for i in range(self.model_combo.count()):
            if self.model_combo.itemText(i).startswith(model):
                self.model_combo.setCurrentIndex(i)
                break

        self.max_videos.setValue(self.settings.get("max_videos_per_run", 0))
        self.gap_min.setValue(self.settings.get("gap_between_videos_min", 30))
        self.gap_max.setValue(self.settings.get("gap_between_videos_max", 120))
        self.review_before_publish.setChecked(self.settings.get("require_review_before_publish", True))

        voice_id = self.settings.get("voice_selected", "random")
        idx = self.voice_combo.findData(voice_id)
        if idx >= 0:
            self.voice_combo.setCurrentIndex(idx)
        else:
            self.voice_combo.setCurrentIndex(0)

    def _connect_auto_save(self):
        """Persist each setting immediately after the user changes it."""
        self.topic_input.textChanged.connect(lambda _text: self.settings.set("topic", self.topic_input.text()))
        self.model_combo.currentIndexChanged.connect(
            lambda _index: self.settings.set("ollama_model", self._selected_model_name())
        )
        self.voice_combo.currentIndexChanged.connect(
            lambda _index: self.settings.set("voice_selected", self.voice_combo.currentData())
        )
        self.max_videos.valueChanged.connect(lambda value: self.settings.set("max_videos_per_run", value))
        self.gap_min.valueChanged.connect(lambda value: self.settings.set("gap_between_videos_min", value))
        self.gap_max.valueChanged.connect(lambda value: self.settings.set("gap_between_videos_max", value))
        self.review_before_publish.toggled.connect(
            lambda checked: self.settings.set("require_review_before_publish", checked)
        )

    def save(self):
        self.settings.set("topic", self.topic_input.text())
        # Extract model name before the parenthesis
        model_text = self.model_combo.currentText()
        model_name = model_text.split(" (")[0] if " (" in model_text else model_text
        self.settings.set("ollama_model", model_name)
        self.settings.set("max_videos_per_run", self.max_videos.value())
        self.settings.set("gap_between_videos_min", self.gap_min.value())
        self.settings.set("gap_between_videos_max", self.gap_max.value())
        self.settings.set("voice_selected", self.voice_combo.currentData())
        self.settings.set("require_review_before_publish", self.review_before_publish.isChecked())

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _group_style(self):
        return """
            QGroupBox {
                font-size: 13px; font-weight: bold; color: #ccc;
                border: 1px solid #333; border-radius: 8px;
                margin-top: 12px; padding: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }
        """

    def _input_style(self):
        return (
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 6px;"
        )

    def _combo_style(self):
        return (
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 4px; min-width: 200px;"
        )

    def _spin_style(self):
        return (
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 4px;"
        )
