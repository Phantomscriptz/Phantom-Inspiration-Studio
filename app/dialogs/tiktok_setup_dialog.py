"""TikTok Setup Instructions Dialog — step-by-step guide for connecting TikTok."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser,
    QHBoxLayout, QWidget,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices


_INSTRUCTIONS_HTML = """
<style>
    body {
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        color: #ddd;
        line-height: 1.6;
        background: #1e1e1e;
        margin: 0;
        padding: 0;
    }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #3b82f6; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    h3 { color: #f59e0b; font-size: 13px; margin-top: 16px; margin-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note {
        background: #2d2d30;
        border-left: 3px solid #f59e0b;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0 6px 6px 0;
        font-size: 12px;
    }
    .important {
        background: #3b1c1c;
        border-left: 3px solid #ef4444;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0 6px 6px 0;
        font-size: 12px;
        color: #fca5a5;
    }
    .success {
        background: #1c3b1c;
        border-left: 3px solid #22c55e;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 0 6px 6px 0;
        font-size: 12px;
        color: #86efac;
    }
    code {
        background: #2d2d30;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        color: #93c5fd;
    }
    .credential-box {
        background: #2d2d30;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 12px;
    }
    .credential-box b { color: #fff; }
    .skip-note {
        background: #1e1e2e;
        border: 1px dashed #555;
        padding: 10px 14px;
        margin: 12px 0;
        border-radius: 6px;
        font-size: 12px;
        color: #aaa;
    }
</style>

<h1>🎵 TikTok Setup Instructions</h1>
<p style="color:#888; font-size: 12px;">Follow these steps to connect your TikTok account for auto-publishing.</p>

<div class="skip-note">
    <b>⏭️ Advanced users:</b> You can skip this guide and directly edit <code>config/tiktok_credentials.json</code> with your credentials.
</div>

<!-- ─── PHASE 1: TIKTOK ACCOUNT ─── -->
<h2>Phase 1 — Create Your TikTok Account</h2>
<ol>
    <li>
        Go to <a href="https://www.tiktok.com/">https://www.tiktok.com/</a> and register a new account.<br>
        <span style="color:#888;">Use your <b>primary email</b> — this will be your master account.</span>
        <ul>
            <li>If you previously signed in with Google, sign in with Google again.</li>
            <li>If you previously used email/password, use email again.</li>
        </ul>
    </li>
    <li>
        <b>Set your account to Professional or Creator.</b><br>
        <span style="color:#888;">Go to <b>Settings → Account → Switch to Pro Account</b> (or Creator Account).<br>
        This is required — TikTok Developer Portal won't work with a personal account.</span>
    </li>
</ol>

<div class="note">
    💡 <b>Tip:</b> Use a consistent username across TikTok and the Developer Portal. It keeps things clean when you verify your domain later.
</div>

<!-- ─── PHASE 2: DEVELOPER PORTAL ─── -->
<h2>Phase 2 — Create a TikTok Developer App</h2>
<ol>
    <li>
        Go to <a href="https://developers.tiktok.com/">https://developers.tiktok.com/</a> and create an account.<br>
        <span style="color:#888;">Use the <b>same email and username</b> as your TikTok account if possible.</span>
    </li>
    <li>
        Click <b>Developer Portal</b> → <b>Manage Apps</b><br>
        Direct link: <a href="https://developers.tiktok.com/apps">https://developers.tiktok.com/apps</a>
    </li>
    <li>
        Click <b>Create an App</b> → Select <b>Individual</b> → Name your app (anything you want).
    </li>
    <li>
        Upload an <b>avatar</b> (and banner if prompted).<br>
        <span style="color:#888;">No avatar? Use any AI image generator to create one for your app.</span>
    </li>
    <li>
        <b>Category</b> = <code>Entertainment</code><br>
        <b>Description</b> = <code>Automated short-form video publishing tool</code>
    </li>
    <li>
        <b>Platforms:</b> Select <b>Desktop ONLY</b>.<br>
        <span style="color:#888;">Skip the "Products" section for now — you'll come back to it.</span>
    </li>
</ol>

<div class="important">
    ⚠️ <b>If you get an error</b> like "You don't have the right type of account" — go back to Step 1 above and make sure your TikTok account is <b>Professional</b> or <b>Creator</b>.
</div>

<!-- ─── PHASE 3: PRODUCTS & SCOPES ─── -->
<h2>Phase 3 — Add Products & Scopes</h2>
<ol>
    <li>
        Click the red <b>"Add Products"</b> button and add:
        <ul>
            <li><b>Login Kit</b></li>
            <li><b>Content Posting API</b></li>
            <li><b>Share Kit</b></li>
        </ul>
    </li>
    <li>
        Click <b>+ Add Scopes</b> and enable these:
        <ul>
            <li><code>user.info.basic</code></li>
            <li><code>video.publish</code></li>
            <li><code>video.upload</code></li>
            <li><code>user.info.profile</code></li>
            <li><code>user.info.stats</code></li>
        </ul>
    </li>
</ol>

<!-- ─── PHASE 4: LOGIN KIT ─── -->
<h2>Phase 4 — Configure Login Kit</h2>
<ol>
    <li>
        Go to the <b>Login Kit</b> section in your app settings.
    </li>
    <li>
        Select <b>Desktop</b> only.
    </li>
    <li>
        Set the redirect URL to:<br>
        <code>http://localhost:8080/callback</code>
    </li>
</ol>

<!-- ─── PHASE 5: DOMAIN VERIFICATION ─── -->
<h2>Phase 5 — Verify Your Domain (Content Posting API)</h2>
<ol>
    <li>
        Go to the <b>Content Posting API</b> section.
    </li>
    <li>
        Enable <b>Direct Post</b>.
    </li>
    <li>
        Click <b>Verify Domains</b> → <b>Verify Properties</b> → <b>URL Prefix</b>.<br>
        Enter: <code>https://YOURUSERNAME.netlify.app/</code><br>
        <span style="color:#888;">Replace <b>YOURUSERNAME</b> with your actual TikTok username or project name.</span>
    </li>
    <li>
        TikTok will ask you to <b>download a .txt verification file</b>.<br>
        Add this file to the <code>website/</code> folder in this project.
    </li>
</ol>

<div class="note">
    💡 <b>Need help?</b> See this screenshot: <a href="https://i.imgur.com/9mAZZuG.png">https://i.imgur.com/9mAZZuG.png</a>
</div>

<!-- ─── PHASE 6: NETLIFY ─── -->
<h2>Phase 6 — Deploy the Verification Site to Netlify</h2>
<ol>
    <li>
        Go to <a href="https://www.netlify.com/">https://www.netlify.com/</a> and create a free account.
    </li>
    <li>
        Open the <code>website/</code> folder from this project.
    </li>
    <li>
        Drag and drop the <b>entire <code>website/</code> folder</b> onto <b>"Production Deploys"</b> in Netlify.
    </li>
    <li>
        Rename your Netlify project to match what you entered for the Content Posting API:<br>
        <code>https://YOURUSERNAME.netlify.app/</code><br><br>
        <b>Example:</b> <code>https://phantominspiration.netlify.app/</code>
    </li>
    <li>
        Head back to TikTok Developer Portal and click <b>"Verify"</b>. Your domain should now be verified.
    </li>
</ol>

<div class="important">
    ⚠️ <b>IMPORTANT:</b> Edit the <code>index.html</code>, <code>privacy.html</code>, and <code>terms.html</code> files in the <code>website/</code> folder to reflect <b>your</b> project name — not "Phantom Inspiration". Make sure the content matches your app.
</div>

<!-- ─── PHASE 7: APP REVIEW ─── -->
<h2>Phase 7 — App Review Submission</h2>
<ol>
    <li>
        Go to <b>App Review</b> in the TikTok Developer Portal.
    </li>
    <li>
        Fill in the review description with something like:<br>
        <div class="credential-box">
            <b>YOUR_APP_NAME</b> is a desktop application that allows users to create and publish short-form faceless videos to TikTok.<br><br>
            <b>How Content Posting API is used:</b><br>
            • Users authorize the app to publish videos on their behalf<br>
            • The app uploads pre-created MP4 video files to the user's TikTok account<br>
            • Videos are posted with user-provided titles, descriptions, and hashtags<br>
            • Users have full control over what content is published<br><br>
            <b>How Login Kit is used:</b><br>
            • Users authenticate via TikTok's OAuth flow to grant publishing permissions<br>
            • The app stores an access token locally to enable video uploads<br>
            • No user data is collected or stored beyond what is needed for publishing
        </div>
    </li>
    <li>
        Upload a demo video (<code>demo_tiktok_integration.mp4</code> or similar) showing the app in action.
    </li>
    <li>
        Click <b>SAVE</b>.
    </li>
</ol>

<!-- ─── PHASE 8: SANDBOX TESTING ─── -->
<h2>Phase 8 — Sandbox Testing</h2>
<ol>
    <li>
        Click <b>"Sandbox"</b> on the top-left of the Developer Portal.
    </li>
    <li>
        Scroll to <b>Sandbox Settings</b> → <b>Add Account</b> → Add your <b>regular TikTok account</b> (the one you created in Phase 1).
    </li>
    <li>
        Click <b>Save</b>.
    </li>
</ol>

<!-- ─── CREDENTIALS ─── -->
<h2>Your Credentials</h2>
<p style="color:#888;">Copy these into the program's TikTok settings, or edit <code>config/tiktok_credentials.json</code> directly.</p>

<h3>TikTok User Account</h3>
<div class="credential-box">
    <b>Profile URL:</b> <code>https://www.tiktok.com/@YOURUSERNAME</code>
</div>

<h3>Production Credentials (used by the app)</h3>
<div class="credential-box">
    <b>App Name:</b> <code>PhantomInspiration</code><br>
    <b>Client Key:</b> <code>awtxcmdg7wm4ewk8</code><br>
    <b>Client Secret:</b> <code>paOPsWEQNzbeNR0vXpMswusLtsfRtdxt</code>
</div>

<h3>Sandbox Credentials (testing only)</h3>
<div class="credential-box">
    <b>App Name:</b> <code>PhantomInspiration</code><br>
    <b>Client Key:</b> <code>sbawhx194ka9hp9ofo</code><br>
    <b>Client Secret:</b> <code>ecGkPEj3cA0x5v126dswEK32EuYwtEOY</code>
</div>

<div class="success">
    ✅ <b>You're done!</b> Once your app is approved and credentials are in place, the app will handle uploads automatically.
</div>
"""


class TikTokSetupDialog(QDialog):
    """A scrollable dialog with step-by-step TikTok setup instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TikTok Setup Guide")
        self.setMinimumSize(720, 600)
        self.resize(780, 680)
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Browser for rich HTML content
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(_INSTRUCTIONS_HTML)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background: #1e1e1e;
                color: #ddd;
                border: none;
                padding: 24px 32px;
                font-size: 13px;
            }
            QTextBrowser QScrollBar:vertical {
                background: #2d2d30;
                width: 8px;
                border-radius: 4px;
            }
            QTextBrowser QScrollBar::handle:vertical {
                background: #555;
                border-radius: 4px;
                min-height: 30px;
            }
            QTextBrowser QScrollBar::add-line:vertical,
            QTextBrowser QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        layout.addWidget(self.browser)

        # Footer with close button
        footer = QWidget()
        footer.setStyleSheet("background: #252526; padding: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 8, 24, 8)

        footer_text = QLabel("Need help? Visit ")
        footer_text.setStyleSheet("color: #888; font-size: 12px;")
        footer_layout.addWidget(footer_text)

        link_btn = QPushButton("TikTok Developer Docs")
        link_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #60a5fa;
                border: none;
                font-size: 12px;
                text-decoration: underline;
            }
            QPushButton:hover { color: #93c5fd; }
        """)
        link_btn.setCursor(Qt.PointingHandCursor)
        link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://developers.tiktok.com/doc/overview")))
        footer_layout.addWidget(link_btn)

        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)
