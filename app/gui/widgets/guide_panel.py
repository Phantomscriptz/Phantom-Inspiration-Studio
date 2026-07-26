"""In-app onboarding, safety information, and recoverable reset controls."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QLabel, QPushButton, QMessageBox


class GuidePanel(QWidget):
    def __init__(self, settings, on_troubleshooting_reset, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.on_troubleshooting_reset = on_troubleshooting_reset
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        overview = QGroupBox("Start here")
        overview_layout = QVBoxLayout(overview)
        text = QLabel(
            "1. Choose a niche, voice, and local model in Settings.\n"
            "2. Confirm FFmpeg and the selected Ollama model in Preflight.\n"
            "3. Connect only platforms you are ready to use.\n"
            "4. Keep Generate-only enabled for your first run, then review the exported video and metadata.\n\n"
            "Original, valuable content and accurate disclosures matter. This app cannot guarantee views, followers, or monetization."
        )
        text.setWordWrap(True)
        text.setStyleSheet("color: #ccc; line-height: 1.4;")
        overview_layout.addWidget(text)
        layout.addWidget(overview)

        reset = QGroupBox("Reset tools")
        reset_layout = QVBoxLayout(reset)
        reset_note = QLabel("These tools never remove OAuth tokens, API/client files, affiliate links, projects, exports, or logs.")
        reset_note.setWordWrap(True)
        reset_note.setStyleSheet("color: #fbbf24;")
        reset_layout.addWidget(reset_note)

        normal_btn = QPushButton("Reset settings to defaults")
        normal_btn.setToolTip("Resets ordinary content and automation choices while keeping accounts and affiliate links.")
        normal_btn.clicked.connect(self._reset_settings)
        reset_layout.addWidget(normal_btn)

        bot_btn = QPushButton("Troubleshooting reset")
        bot_btn.setStyleSheet("QPushButton { background: #7f1d1d; color: white; padding: 8px; border-radius: 5px; } QPushButton:hover { background: #991b1b; }")
        bot_btn.clicked.connect(self._reset_bot)
        reset_layout.addWidget(bot_btn)
        layout.addWidget(reset)

        platforms = QGroupBox("Platform reality check")
        platform_layout = QVBoxLayout(platforms)
        platform_text = QLabel(
            "YouTube, TikTok, Instagram, and Facebook need their official developer permissions.\n"
            "YouTube Shorts and long videos are separate workflows in this app, but still share channel-level policies.\n"
            "Snapchat is manual-only here. Rumble browser automation is not treated as production-ready.\n"
            "Pinterest is a future affiliate-traffic channel; Patreon, Ko-fi, and Gumroad are audience-supported income options."
        )
        platform_text.setWordWrap(True)
        platform_text.setStyleSheet("color: #ccc;")
        platform_layout.addWidget(platform_text)
        layout.addWidget(platforms)
        layout.addStretch()

    def _reset_settings(self):
        answer = QMessageBox.question(self, "Reset settings", "Reset ordinary content and automation choices to defaults? Connected accounts and affiliate links will stay untouched.", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer == QMessageBox.Yes:
            self.settings.reset_user_preferences()
            QMessageBox.information(self, "Settings reset", "Settings were reset. Reopen Settings to see the defaults.")

    def _reset_bot(self):
        answer = QMessageBox.warning(self, "Troubleshooting reset", "This stops current work and clears only temporary app state. It does not delete accounts, affiliate links, projects, exports, or logs. Continue?", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
        if answer == QMessageBox.Yes:
            self.on_troubleshooting_reset()
            QMessageBox.information(self, "Troubleshooting reset complete", "Temporary runtime state was cleared. Your accounts and content files were kept.")
