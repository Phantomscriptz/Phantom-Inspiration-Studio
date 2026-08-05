"""Content settings panel — niche setup popup, voice, automation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QLineEdit, QSpinBox,
    QCheckBox, QPushButton, QDialog, QDialogButtonBox, QScrollArea, QTextEdit, QListView,
    QFileDialog, QMessageBox, QFormLayout, QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QDesktopServices

from app.config.settings import SettingsManager
from app.ai.prompts.script_prompts import NICHES, OPTIONAL_SUBNICHES
from app.ai.voice.edge_tts_provider import ENGLISH_VOICES
from app.ai.providers.ollama_client import get_client
from pathlib import Path
import asyncio
import edge_tts
import json
import shutil


VOICE_SAMPLE_DIR = Path("assets/voice_samples/exact")


def voice_sample_path(voice_id: str) -> Path:
    """Return the cached, exact preview for a configured online voice."""
    safe_name = voice_id.replace("/", "_").replace("\\", "_")
    return (VOICE_SAMPLE_DIR / f"{safe_name}.mp3").resolve()


def has_playable_voice_sample(voice_id: str) -> bool:
    """Only expose previews that were fully downloaded and can be played."""
    try:
        return voice_sample_path(voice_id).stat().st_size > 1024
    except OSError:
        return False


class ExactVoicePreviewWorker(QThread):
    """Download one exact voice preview once, then keep it locally."""
    ready = Signal(str)
    failed = Signal(str)

    def __init__(self, voice_id: str, parent=None):
        super().__init__(parent)
        self.voice_id = voice_id

    def run(self):
        path = voice_sample_path(self.voice_id)
        temporary_path = path.with_suffix(".part")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            asyncio.run(edge_tts.Communicate(
                "This is a five second preview of the selected Phantom voice.",
                voice=self.voice_id,
            ).save(str(temporary_path)))
            if temporary_path.stat().st_size <= 1024:
                raise RuntimeError("The downloaded preview was incomplete.")
            temporary_path.replace(path)
            self.ready.emit(str(path))
        except Exception:
            temporary_path.unlink(missing_ok=True)
            self.failed.emit(
                "Microsoft's voice service is unreachable. Exact accent previews "
                "will work once it is reachable and will then be saved locally."
            )


class BrollAttributionDialog(QDialog):
    """Collect provenance at import time, rather than after a clip is used."""

    def __init__(self, source_file: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import B-roll clip")
        self.setMinimumWidth(560)
        self.setStyleSheet(
            "QDialog { background: #1e1e1e; color: #ddd; } "
            "QLabel { color: #ddd; } "
            "QLineEdit { background: #2d2d30; color: white; border: 1px solid #444; border-radius: 4px; padding: 7px; }"
        )
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Clip: {source_file.name}"))
        note = QLabel("Save the original source page and license now. Live publishing is blocked if this information is missing.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #fbbf24; font-size: 12px;")
        layout.addWidget(note)
        form = QFormLayout()
        self.source = QLineEdit()
        self.source.setPlaceholderText("https://pixabay.com/videos/...")
        self.creator = QLineEdit()
        self.creator.setPlaceholderText("Creator name, if shown on the source page")
        self.license = QLineEdit("Pixabay Content License")
        self.keywords = QLineEdit()
        self.keywords.setPlaceholderText("calm, ocean, reflection, sunrise")
        form.addRow("Source page URL:", self.source)
        form.addRow("Creator credit:", self.creator)
        form.addRow("License:", self.license)
        form.addRow("Visual keywords:", self.keywords)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def metadata(self) -> dict:
        return {
            "source": self.source.text().strip(),
            "creator": self.creator.text().strip(),
            "license": self.license.text().strip(),
            "keywords": [item.strip() for item in self.keywords.text().split(",") if item.strip()],
        }


# ============================================================================
# Niche Setup Popup Dialog
# ============================================================================
class NicheSetupDialog(QDialog):
    """Popup: pick which niches to use, or randomize."""

    def __init__(self, selected_niches: list[str], randomize: bool,
                 selected_subniches: dict[str, list[str]] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Content Niches Setup")
        self.setMinimumWidth(620)
        self.setMinimumHeight(680)
        self._selected_subniches = selected_subniches or {}
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
            "Channel strategy: choose one core niche for one channel. Viewers subscribe "
            "when they know what they will get next. Use separate channels for unrelated "
            "topics such as horror, finance, or history.\n\n"
            "Select the niche for this channel. Randomizing is best only while testing ideas "
            "or when you intentionally operate separate channels."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)

        # Randomize toggle
        self.randomize_cb = QCheckBox("🎲  Randomize niche per video (not recommended for one channel)")
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
            cb.toggled.connect(self._refresh_subniche_enabled)

        self.niche_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        self.subheading = QLabel("Sub-categories — choose the topics this channel is allowed to produce")
        self.subheading.setStyleSheet("font-size: 13px; font-weight: bold; color: #5B9BD5;")
        layout.addWidget(self.subheading)
        self.subniche_tabs = QTabWidget()
        self.subniche_tabs.setMinimumHeight(260)
        self.subniche_tabs.setMaximumHeight(320)
        self._subniche_checks: dict[str, dict[str, QCheckBox]] = {}
        layout.addWidget(self.subniche_tabs)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Apply initial state
        self._on_randomize_toggled(randomize)
        self._refresh_subniche_enabled()

    def _on_randomize_toggled(self, checked: bool):
        """Grey out individual niches and hide sub-topics when randomize is on."""
        for cb in self._niche_checks.values():
            cb.setEnabled(not checked)
            if checked:
                cb.setStyleSheet("QCheckBox { font-size: 12px; color: #555; padding: 6px 4px; }")
            else:
                cb.setStyleSheet("QCheckBox { font-size: 12px; color: #ccc; padding: 6px 4px; }")
        self.subheading.setVisible(not checked)
        self.subniche_tabs.setVisible(not checked)
        self._rebuild_subniche_tabs()

    def _refresh_subniche_enabled(self):
        """Show tabs only for selected channel niches."""
        self._rebuild_subniche_tabs()

    def _remember_subniche_state(self):
        for key, checks in self._subniche_checks.items():
            self._selected_subniches[key] = [name for name, cb in checks.items() if cb.isChecked()]

    def _rebuild_subniche_tabs(self):
        self._remember_subniche_state()
        while self.subniche_tabs.count():
            widget = self.subniche_tabs.widget(0)
            self.subniche_tabs.removeTab(0)
            widget.deleteLater()
        self._subniche_checks = {}
        if self.randomize_cb.isChecked():
            return
        selected = [key for key, cb in self._niche_checks.items() if cb.isChecked()]
        if not selected:
            empty = QLabel("Select at least one main niche above to configure its topic options.")
            empty.setStyleSheet("color: #999; padding: 18px;")
            self.subniche_tabs.addTab(empty, "No niche selected")
            return
        for key in selected:
            self._add_subniche_tab(key)

    def _add_subniche_tab(self, key: str):
        info = NICHES[key]
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        tab_layout = QVBoxLayout(content)
        tab_layout.setContentsMargins(12, 10, 12, 10)
        tab_layout.setSpacing(5)
        tab_layout.addWidget(QLabel("Recommended topic pool — enabled by default"))
        checks: dict[str, QCheckBox] = {}
        recommended = info.get("subniches", [])
        saved = self._selected_subniches.get(key)
        for subniche in recommended:
            checkbox = QCheckBox(subniche.capitalize())
            checkbox.setChecked(subniche in (saved if saved is not None else recommended))
            checkbox.setStyleSheet("QCheckBox { color: #dbeafe; padding: 3px; }")
            tab_layout.addWidget(checkbox)
            checks[subniche] = checkbox
        extras = OPTIONAL_SUBNICHES.get(key, [])
        if extras:
            label = QLabel("More optional topic ideas — off by default")
            label.setStyleSheet("color: #fbbf24; font-weight: bold; padding-top: 10px;")
            tab_layout.addWidget(label)
            for subniche in extras:
                checkbox = QCheckBox(subniche.capitalize())
                checkbox.setChecked(subniche in (saved or []))
                checkbox.setStyleSheet("QCheckBox { color: #bbb; padding: 3px; }")
                tab_layout.addWidget(checkbox)
                checks[subniche] = checkbox
        tab_layout.addStretch()
        tab.setWidget(content)
        self.subniche_tabs.addTab(tab, info["name"])
        self._subniche_checks[key] = checks

    def get_selection(self) -> tuple[list[str], bool, dict[str, list[str]]]:
        """Return selected main niches, random mode, and allowed sub-categories."""
        selected = [k for k, cb in self._niche_checks.items() if cb.isChecked()]
        if self.randomize_cb.isChecked():
            return selected, True, {}
        self._remember_subniche_state()
        selected_subniches = {
            key: [name for name, cb in checks.items() if cb.isChecked()]
            for key, checks in self._subniche_checks.items()
        }
        return selected, False, selected_subniches


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
        self._selected_subniches = self.settings.get("selected_subniches", {})

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
        self.niche_setup_btn.setMinimumSize(150, 36)
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
        self.voice_combo.setStyleSheet(self._voice_combo_style())
        self.voice_combo.setMinimumWidth(430)
        voice_view = QListView(self.voice_combo)
        voice_view.setMinimumWidth(520)
        voice_view.setTextElideMode(Qt.ElideNone)
        self.voice_combo.setView(voice_view)
        verified_voice_count = 0
        for display_name, voice_id, gender, accent, desc in ENGLISH_VOICES:
            if not has_playable_voice_sample(voice_id):
                continue
            self.voice_combo.addItem(display_name, voice_id)
            verified_voice_count += 1
            self.voice_combo.setItemData(
                self.voice_combo.count() - 1,
                f"{display_name}\n{gender} • {accent} accent — {desc}",
                Qt.ToolTipRole,
            )
        self.voice_combo.insertSeparator(verified_voice_count)
        self.voice_combo.insertItem(0, "🎲 Recommended verified voice", "random")
        voice_row.addWidget(self.voice_combo)
        self.preview_btn = QPushButton("▶ Get / play exact sample")
        self.preview_btn.setMinimumHeight(34)
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self._toggle_voice_preview)
        voice_row.addWidget(self.preview_btn)
        voice_row.addStretch()
        voice_layout.addLayout(voice_row)

        self.voice_desc_label = QLabel(f"{verified_voice_count} verified voice samples are available on this computer. Unverified voices are hidden until their sample can be downloaded successfully.")
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

        # --- Visual style ---
        visuals_group = QGroupBox("Visual Style")
        visuals_group.setStyleSheet(self._group_style())
        visuals_layout = QVBoxLayout(visuals_group)
        self.cinematic_broll = QCheckBox("Cinematic B-roll — use licensed local motion clips when they match the script")
        self.cinematic_broll.setStyleSheet("font-size: 12px; color: #d1d5db; padding: 3px;")
        self.cinematic_broll.setToolTip("Uses clips from assets/stock_videos. Unmatched scenes still use generated imagery.")
        visuals_layout.addWidget(self.cinematic_broll)
        visuals_note = QLabel("Zero-budget workflow: download clips you have permission to use, name them descriptively, then add them to the local B-roll folder. Every render saves a visual plan for review.")
        visuals_note.setWordWrap(True)
        visuals_note.setStyleSheet("color: #888; font-size: 12px; padding: 2px 8px;")
        visuals_layout.addWidget(visuals_note)
        self.open_broll_folder_btn = QPushButton("Open B-roll folder")
        self.open_broll_folder_btn.setMinimumHeight(34)
        self.open_broll_folder_btn.setStyleSheet(
            "QPushButton { background: #3b82f6; color: white; border: none; border-radius: 6px; padding: 7px 14px; font-size: 12px; } "
            "QPushButton:hover { background: #2563eb; }"
        )
        self.open_broll_folder_btn.clicked.connect(self._open_broll_folder)
        visuals_layout.addWidget(self.open_broll_folder_btn, alignment=Qt.AlignLeft)
        self.import_broll_btn = QPushButton("Import / credit a B-roll clip")
        self.import_broll_btn.setMinimumHeight(34)
        self.import_broll_btn.setStyleSheet(self.open_broll_folder_btn.styleSheet())
        self.import_broll_btn.clicked.connect(self._import_broll_clip)
        visuals_layout.addWidget(self.import_broll_btn, alignment=Qt.AlignLeft)
        self.broll_library_status = QLabel()
        self.broll_library_status.setStyleSheet("color: #888; font-size: 12px; padding: 2px 8px;")
        visuals_layout.addWidget(self.broll_library_status)
        broll_picker_row = QHBoxLayout()
        broll_picker_row.addWidget(QLabel("Selected B-roll clip:"))
        self.broll_clip_combo = QComboBox()
        self.broll_clip_combo.setStyleSheet(self._combo_style())
        self.broll_clip_combo.setMinimumWidth(360)
        broll_picker_row.addWidget(self.broll_clip_combo, 1)
        visuals_layout.addLayout(broll_picker_row)
        loop_note = QLabel("The selected clip loops behind the entire narration. Use naturally loopable footage; the app cannot make every hard cut invisible.")
        loop_note.setWordWrap(True)
        loop_note.setStyleSheet("color: #888; font-size: 12px; padding: 2px 8px;")
        visuals_layout.addWidget(loop_note)
        self._refresh_broll_status()
        layout.addWidget(visuals_group)

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
        self.install_model_btn.setMinimumHeight(34)
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
        self.gap_min.setRange(10, 86400)
        self.gap_min.setStyleSheet(self._spin_style())
        gap_row.addWidget(self.gap_min)
        gap_row.addWidget(QLabel("to"))
        self.gap_max = QSpinBox()
        self.gap_max.setRange(10, 86400)
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
        dialog = NicheSetupDialog(
            self._selected_niches, self._randomize_niches,
            self._selected_subniches, self,
        )
        if dialog.exec() == QDialog.Accepted:
            self._selected_niches, self._randomize_niches, self._selected_subniches = dialog.get_selection()
            self.settings.set("selected_niches", self._selected_niches)
            self.settings.set("randomize_niches", self._randomize_niches)
            self.settings.set("selected_subniches", self._selected_subniches)
            # Keep the legacy single-niche value aligned for older callers and
            # clear logs/config exports. The worker itself uses selected_niches.
            if self._selected_niches and not self._randomize_niches:
                self.settings.set("niche", self._selected_niches[0])
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
            subcount = len(self._selected_subniches.get(key, NICHES.get(key, {}).get("subniches", [])))
            return f"Selected: {name} — {subcount} sub-categories enabled"
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
        self.preview_btn.setText("▶ Get / play exact sample")
        self.preview_btn.setEnabled(voice_id != "random")
        if voice_id == "random":
            self.voice_desc_label.setText(
                "Phantom uses the channel-appropriate voice recommendation. It does not randomly switch accents between videos."
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
        path = voice_sample_path(voice_id)
        if not has_playable_voice_sample(voice_id):
            self.voice_desc_label.setText("This voice is not verified on this computer yet, so it cannot be previewed or selected.")
            return
        self._play_voice_preview(str(path))

    def _play_voice_preview(self, path: str):
        # Clear the old source first. Some Windows media backends otherwise
        # keep replaying the prior short WAV when the user changes selection.
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.media_player.play()
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("■ Stop exact sample")
        self.voice_desc_label.setText(f"Exact cached preview: {Path(path).name}")

    def _voice_preview_failed(self, message: str):
        self.preview_btn.setEnabled(True)
        self.preview_btn.setText("▶ Get / play exact sample")
        self.voice_desc_label.setText(f"Preview unavailable: {message}")

    def _on_preview_state_changed(self, state):
        if state != QMediaPlayer.PlayingState:
            self.preview_btn.setText("▶ Get / play exact sample")

    def _open_broll_folder(self):
        folder = Path("assets/stock_videos").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _refresh_broll_status(self):
        folder = Path("assets/stock_videos")
        clips = [path for path in folder.glob("*") if path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi"}]
        manifest_path = folder / "manifest.json"
        try:
            records = json.loads(manifest_path.read_text(encoding="utf-8")).get("clips", [])
        except (OSError, json.JSONDecodeError):
            records = []
        verified = sum(bool(item.get("source") and item.get("license")) for item in records)
        self.broll_library_status.setText(f"Library: {len(clips)} clip(s); {verified} have saved source and license details.")
        if hasattr(self, "broll_clip_combo"):
            selected = self.settings.get("broll_selected_clip", "")
            self.broll_clip_combo.blockSignals(True)
            self.broll_clip_combo.clear()
            self.broll_clip_combo.addItem("AI-generated visuals (no B-roll)", "")
            for clip in sorted(clips, key=lambda item: item.name.lower()):
                self.broll_clip_combo.addItem(clip.name, clip.name)
            index = self.broll_clip_combo.findData(selected)
            self.broll_clip_combo.setCurrentIndex(max(index, 0))
            self.broll_clip_combo.blockSignals(False)

    def _import_broll_clip(self):
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Select a licensed B-roll clip",
            str(Path.home()),
            "Video files (*.mp4 *.mov *.mkv *.webm *.avi)",
        )
        if not source:
            return
        source_path = Path(source)
        dialog = BrollAttributionDialog(source_path, self)
        if dialog.exec() != QDialog.Accepted:
            return
        metadata = dialog.metadata()
        if not metadata["source"] or not metadata["license"]:
            QMessageBox.warning(self, "B-roll attribution required", "Enter the source page URL and license before importing this clip.")
            return
        folder = Path("assets/stock_videos").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        source_resolved = source_path.resolve()
        if source_resolved.parent == folder:
            # A clip copied into the library before this feature existed only
            # needs a manifest record. Do not copy it a second time.
            destination = source_resolved
            already_in_library = True
        else:
            destination = folder / source_path.name
            stem, suffix, counter = source_path.stem, source_path.suffix, 2
            while destination.exists():
                destination = folder / f"{stem}_{counter}{suffix}"
                counter += 1
            already_in_library = False
        try:
            if not already_in_library:
                shutil.copy2(source_path, destination)
            manifest_path = folder / "manifest.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                manifest = {"clips": []}
            manifest["clips"] = [
                item for item in manifest.setdefault("clips", [])
                if item.get("filename") != destination.name
            ]
            manifest["clips"].append({"filename": destination.name, **metadata})
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "B-roll import failed", str(exc))
            return
        self._refresh_broll_status()
        action = "Updated credit for" if already_in_library else "Imported"
        QMessageBox.information(self, "B-roll ready", f"{action} {destination.name}. Its source and license details are now saved for review.")

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
        self.cinematic_broll.setChecked(self.settings.get("cinematic_broll", True))
        self._refresh_broll_status()
        self.broll_clip_combo.setEnabled(self.cinematic_broll.isChecked())

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
        self.cinematic_broll.toggled.connect(self._on_broll_toggled)
        self.broll_clip_combo.currentIndexChanged.connect(
            lambda _index: self.settings.set("broll_selected_clip", self.broll_clip_combo.currentData() or "")
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
        self.settings.set("cinematic_broll", self.cinematic_broll.isChecked())
        self.settings.set("broll_selected_clip", self.broll_clip_combo.currentData() or "")

    def _on_broll_toggled(self, checked: bool):
        self.settings.set("cinematic_broll", checked)
        self.broll_clip_combo.setEnabled(checked)

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

    def _voice_combo_style(self):
        return (
            "QComboBox { background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 4px 8px; min-width: 430px; }"
            "QComboBox QAbstractItemView { background: #252526; color: white;"
            "selection-background-color: #3b82f6; selection-color: white;"
            "border: 1px solid #555; outline: 0; }"
        )

    def _spin_style(self):
        return (
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 4px;"
        )
