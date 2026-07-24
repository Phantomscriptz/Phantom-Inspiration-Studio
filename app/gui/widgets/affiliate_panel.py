"""Affiliate/Referral panel — manage third-party revenue streams in video descriptions.

Each affiliate has:
- Enable/disable toggle
- Popup config dialog (shown on first enable) with setup instructions
- Referral link input
- Revenue stats display
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QCheckBox, QLineEdit, QPushButton, QTextEdit,
    QDialog, QDialogButtonBox, QScrollArea, QFrame, QApplication,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from app.config.settings import SettingsManager


# ============================================================================
# Affiliate catalog — defines all available revenue partners
# ============================================================================
AFFILIATE_CATALOG = {
    "elevenlabs": {
        "name": "ElevenLabs",
        "icon": "🎙️",
        "category": "AI Voice",
        "description": "AI voice generation. Earn 22% commission on Starter/Creator/Pro/Scale for 12 months.",
        "setup_url": "https://elevenlabs.io/affiliates",
        "setup_instructions": (
            "1. Go to elevenlabs.io/affiliates\n"
            "2. Sign up for the affiliate program (free)\n"
            "3. Connect via PartnerStack\n"
            "4. Copy your unique referral link\n"
            "5. Paste it below\n\n"
            "💰 22% on Starter/Creator/Pro/Scale plans\n"
            "💰 11% on Business tier plans\n"
            "📅 Monthly payouts via PartnerStack"
        ),
    },
    "runwayml": {
        "name": "RunwayML",
        "icon": "🎬",
        "category": "AI Video",
        "description": "AI video generation tools. Earn commission on referrals.",
        "setup_url": "https://runwayml.com",
        "setup_instructions": (
            "1. Go to runwayml.com\n"
            "2. Look for 'Affiliates' in footer\n"
            "3. Apply for the affiliate program\n"
            "4. Get your unique referral link\n"
            "5. Paste it below"
        ),
    },
    "midjourney": {
        "name": "Midjourney",
        "icon": "🎨",
        "category": "AI Image",
        "description": "AI image generation. Earn commission on referrals.",
        "setup_url": "https://midjourney.com",
        "setup_instructions": (
            "1. Go to midjourney.com\n"
            "2. Check for affiliate/partner program\n"
            "3. Apply if available\n"
            "4. Get your referral link\n"
            "5. Paste it below"
        ),
    },
    "propellerads": {
        "name": "PropellerAds",
        "icon": "💰",
        "category": "Ad Network",
        "description": "Popunder/interstitial ads. Earn from ad impressions on landing pages.",
        "setup_url": "https://propellerads.com/publishers/",
        "setup_instructions": (
            "1. Go to propellerads.com/publishers\n"
            "2. Sign up as a publisher\n"
            "3. Get your publisher ID\n"
            "4. Paste your referral link below\n\n"
            "💰 Earn from popunder/interstitial ads"
        ),
    },
}


class AffiliateSetupDialog(QDialog):
    """Popup dialog for configuring an affiliate referral link."""

    def __init__(self, affiliate_key: str, current_url: str = "", parent=None):
        super().__init__(parent)
        self.affiliate_key = affiliate_key
        info = AFFILIATE_CATALOG.get(affiliate_key, {})
        self.setWindowTitle(f"Setup: {info.get('name', affiliate_key)}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: #ddd; }
            QLabel { color: #ddd; }
            QTextEdit {
                background: #2d2d30; color: #ccc;
                border: 1px solid #444; border-radius: 4px;
                padding: 8px; font-family: 'Consolas', monospace; font-size: 12px;
            }
            QLineEdit {
                background: #2d2d30; color: white;
                border: 1px solid #5B9BD5; border-radius: 4px;
                padding: 8px; font-size: 13px;
            }
            QPushButton {
                background: #5B9BD5; color: white; border: none;
                border-radius: 4px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #7BB8E8; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel(f"{info.get('icon', '🔗')} {info.get('name', affiliate_key)} Setup")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #5B9BD5;")
        layout.addWidget(header)

        instructions_label = QLabel("Setup Instructions:")
        instructions_label.setStyleSheet("font-weight: bold; color: #aaa;")
        layout.addWidget(instructions_label)

        instructions_text = QTextEdit()
        instructions_text.setPlainText(info.get("setup_instructions", "Enter your referral link below."))
        instructions_text.setReadOnly(True)
        instructions_text.setMaximumHeight(150)
        layout.addWidget(instructions_text)

        open_btn = QPushButton(f"🌐 Open {info.get('name', 'Website')} Setup Page")
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(info.get("setup_url", "")))
        )
        layout.addWidget(open_btn)

        layout.addSpacing(8)

        link_label = QLabel("Your Referral Link:")
        link_label.setStyleSheet("font-weight: bold; color: #aaa;")
        layout.addWidget(link_label)

        self.link_input = QLineEdit(current_url)
        self.link_input.setPlaceholderText("https://your-referral-link.com/...")
        layout.addWidget(self.link_input)

        warning = QLabel(
            "⚠️ Your referral link will be appended to ALL video descriptions when enabled."
        )
        warning.setStyleSheet("color: #fbbf24; font-size: 11px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_referral_url(self) -> str:
        return self.link_input.text().strip()


class AffiliateCard(QFrame):
    """A single affiliate card with enable toggle and config button."""

    def __init__(self, key: str, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.key = key
        self.settings = settings
        info = AFFILIATE_CATALOG.get(key, {})
        current = settings.get(f"affiliates.{key}", {})

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #252526; border: 1px solid #333;
                border-radius: 8px; padding: 8px;
            }
            QFrame:hover { border-color: #5B9BD5; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        top_row = QHBoxLayout()

        icon_label = QLabel(info.get("icon", "🔗"))
        icon_label.setStyleSheet("font-size: 24px;")
        top_row.addWidget(icon_label)

        name_col = QVBoxLayout()
        name_label = QLabel(info.get("name", key))
        name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #eee;")
        name_col.addWidget(name_label)
        cat_label = QLabel(info.get("category", ""))
        cat_label.setStyleSheet("color: #5B9BD5; font-size: 11px;")
        name_col.addWidget(cat_label)
        top_row.addLayout(name_col)
        top_row.addStretch()

        self.enable_cb = QCheckBox("Enable")
        self.enable_cb.setChecked(current.get("enabled", False))
        self.enable_cb.setStyleSheet("color: #ddd; font-size: 12px;")
        self.enable_cb.toggled.connect(self._on_toggled)
        top_row.addWidget(self.enable_cb)

        self.config_btn = QPushButton("⚙️ Configure")
        self.config_btn.setStyleSheet("""
            QPushButton {
                background: #333; color: #aaa; border: 1px solid #555;
                border-radius: 4px; padding: 4px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #444; color: #ddd; }
        """)
        self.config_btn.clicked.connect(self._open_config)
        top_row.addWidget(self.config_btn)

        layout.addLayout(top_row)

        desc = QLabel(info.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(desc)

        url = current.get("referral_url", "")
        self.url_label = QLabel(
            f"🔗 {url[:60]}{'...' if len(url) > 60 else ''}" if url else ""
        )
        self.url_label.setStyleSheet("color: #6a9955; font-size: 10px; font-family: Consolas;")
        self.url_label.setWordWrap(True)
        if url:
            layout.addWidget(self.url_label)

    def _on_toggled(self, checked: bool):
        self.settings.set(f"affiliates.{self.key}.enabled", checked)
        if checked:
            current_url = self.settings.get(f"affiliates.{self.key}.referral_url", "")
            if not current_url:
                self._open_config()
                if not self.settings.get(f"affiliates.{self.key}.referral_url", ""):
                    self.enable_cb.setChecked(False)

    def _open_config(self):
        current_url = self.settings.get(f"affiliates.{self.key}.referral_url", "")
        dialog = AffiliateSetupDialog(self.key, current_url, self.window())
        if dialog.exec() == QDialog.Accepted:
            url = dialog.get_referral_url()
            self.settings.set(f"affiliates.{self.key}.referral_url", url)
            display = f"🔗 {url[:60]}{'...' if len(url) > 60 else ''}" if url else ""
            self.url_label.setText(display)
            if url and not self.url_label.isVisible():
                self.url_label.setVisible(True)
            elif not url:
                self.url_label.setVisible(False)


class AffiliatePanel(QWidget):
    """Panel for managing affiliate/referral links added to video descriptions."""

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("💰 Revenue & Affiliates")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #fbbf24;")
        layout.addWidget(header)

        desc = QLabel(
            "Earn money from your videos. Enable affiliate links to auto-append to descriptions, "
            "or connect ad networks for direct revenue."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        self._cards = {}
        for key in AFFILIATE_CATALOG:
            card = AffiliateCard(key, self.settings)
            self._cards[key] = card
            scroll_layout.addWidget(card)

        # Custom affiliate
        custom_frame = QFrame()
        custom_frame.setFrameShape(QFrame.StyledPanel)
        custom_frame.setStyleSheet("""
            QFrame {
                background: #252526; border: 1px dashed #555;
                border-radius: 8px; padding: 12px;
            }
        """)
        custom_layout = QVBoxLayout(custom_frame)

        custom_header = QLabel("➕ Custom Referral Link")
        custom_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #aaa;")
        custom_layout.addWidget(custom_header)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.custom_name = QLineEdit()
        self.custom_name.setPlaceholderText("e.g., My Service")
        self.custom_name.setStyleSheet(
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 6px;"
        )
        name_row.addWidget(self.custom_name)
        custom_layout.addLayout(name_row)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("URL:"))
        self.custom_url = QLineEdit()
        self.custom_url.setPlaceholderText("https://example.com/?ref=you")
        self.custom_url.setStyleSheet(
            "background: #2d2d30; color: white; border: 1px solid #444;"
            "border-radius: 4px; padding: 6px;"
        )
        url_row.addWidget(self.custom_url)
        custom_layout.addLayout(url_row)

        add_btn = QPushButton("+ Add Custom Link")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6; color: white; border: none;
                border-radius: 6px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        add_btn.clicked.connect(self._add_custom)
        custom_layout.addWidget(add_btn)

        scroll_layout.addWidget(custom_frame)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _add_custom(self):
        name = self.custom_name.text().strip()
        url = self.custom_url.text().strip()
        if not name or not url:
            return

        key = name.lower().replace(" ", "_")
        cfg = {"enabled": True, "referral_url": url, "description": f"Custom: {name}"}

        affiliates = self.settings.get("affiliates", {})
        affiliates[key] = cfg
        self.settings.set("affiliates", affiliates)

        card = AffiliateCard(key, self.settings)
        self._cards[key] = card

        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_content = scroll_area.widget()
            lay = scroll_content.layout()
            lay.insertWidget(lay.count() - 2, card)

        self.custom_name.clear()
        self.custom_url.clear()

    def get_enabled_links(self) -> list[dict]:
        return self.settings.get_affiliate_links()
