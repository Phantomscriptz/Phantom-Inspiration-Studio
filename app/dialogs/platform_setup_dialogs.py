"""Platform Setup Instructions — one dialog per platform with step-by-step guides.

Each guide is a rich HTML page with clickable links, credential boxes, and warnings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser,
    QHBoxLayout, QWidget, QComboBox, QFrame,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QDesktopServices


# ─── Shared Styles ──────────────────────────────────────────────────────────

_DIALOG_STYLE = """
    QDialog { background: #1e1e1e; }
"""

_BROWSER_STYLE = """
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
"""

_FOOTER_STYLE = """
    QPushButton {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 24px;
        font-size: 13px;
    }
    QPushButton:hover { background: #2563eb; }
"""


# ─── YouTube Setup Guide ─────────────────────────────────────────────────────

_YOUTUBE_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #ef4444; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    h3 { color: #f59e0b; font-size: 13px; margin-top: 16px; margin-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
    .credential-box { background: #2d2d30; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 12px; }
    .credential-box b { color: #fff; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; }
    th, td { border: 1px solid #444; padding: 8px 12px; text-align: left; font-size: 12px; }
    th { background: #2d2d30; color: #fff; }
</style>

<h1>🎬 YouTube Setup Guide</h1>
<p style="color:#888; font-size: 12px;">Connect your YouTube/Google account for auto-publishing Shorts and long-form videos.</p>

<h2>Phase 1 — Create a Google Account</h2>
<ol>
    <li>Go to <a href="https://accounts.google.com/signup">https://accounts.google.com/signup</a></li>
    <li>Create a new Google account (or use your existing one).</li>
    <li>Create a <b>YouTube channel</b> at <a href="https://www.youtube.com/create_channel">https://www.youtube.com/create_channel</a></li>
    <li>Choose a channel name that matches your content niche.</li>
</ol>

<h2>Phase 2 — Enable YouTube Data API v3</h2>
<ol>
    <li>Go to <a href="https://console.cloud.google.com/">Google Cloud Console</a></li>
    <li>Create a new project (e.g., "PhantomUploader").</li>
    <li>Go to <b>APIs & Services → Library</b></li>
    <li>Search for <b>"YouTube Data API v3"</b> and click <b>Enable</b>.</li>
</ol>

<h2>Phase 3 — Create OAuth 2.0 Credentials</h2>
<ol>
    <li>Go to <b>APIs & Services → Credentials</b></li>
    <li>Click <b>"+ Create Credentials" → OAuth client ID</b></li>
    <li>If prompted, configure the <b>OAuth consent screen</b> first:
        <ul>
            <li>User Type: <b>External</b></li>
            <li>App name: Your app name</li>
            <li>Add your email as developer contact</li>
        </ul>
    </li>
    <li>For OAuth client ID:
        <ul>
            <li>Application type: <b>Desktop app</b></li>
            <li>Name: "Phantom Studio"</li>
        </ul>
    </li>
    <li>Click <b>Create</b> — you'll get a <b>Client ID</b> and <b>Client Secret</b>.</li>
    <li>Download the JSON file and save it as <code>config/youtube_client_secret.json</code></li>
</ol>

<h2>Phase 4 — YouTube Shorts vs Long-Form</h2>
<table>
    <tr><th>Feature</th><th>YouTube Shorts</th><th>Long-Form</th></tr>
    <tr><td>Length</td><td>≤ 60 seconds</td><td>Any length</td></tr>
    <tr><td>Format</td><td>9:16 vertical</td><td>16:9 horizontal</td></tr>
    <tr><td>RPM</td><td>$0.01–$0.07</td><td>$1–$30</td></tr>
    <tr><td>Growth</td><td>Viral potential</td><td>Slower, evergreen</td></tr>
</table>

<div class="note">
💡 <b>Strategy:</b> Use Shorts for rapid subscriber growth, then funnel viewers to long-form for higher RPM. Phantom can generate both — set video format in Content Settings.
</div>

<h2>Phase 5 — Monetization (YPP)</h2>
<table>
    <tr><th>Tier</th><th>Requirements</th><th>Unlocks</th></tr>
    <tr><td>Fan Funding</td><td>500 subs + 3 uploads + (3,000 hrs OR 3M Shorts views)</td><td>Super Chat, Memberships</td></tr>
    <tr><td>Full Monetization</td><td>1,000 subs + (4,000 hrs OR 10M Shorts views)</td><td>AdSense + Shorts revenue</td></tr>
</table>

<div class="success">✅ Once your OAuth credentials are in <code>config/youtube_client_secret.json</code>, the app will handle uploads automatically.</div>
"""


# ─── Instagram Setup Guide ───────────────────────────────────────────────────

_INSTAGRAM_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #e1306c; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
    .credential-box { background: #2d2d30; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 12px; }
    .credential-box b { color: #fff; }
</style>

<h1>📸 Instagram Setup Guide</h1>
<p style="color:#888; font-size: 12px;">Connect Instagram for auto-publishing Reels and posts.</p>

<h2>Phase 1 — Instagram Business/Creator Account</h2>
<ol>
    <li>Open the Instagram app on your phone.</li>
    <li>Go to <b>Settings → Account → Switch to Professional Account</b></li>
    <li>Choose <b>Creator</b> (or Business).</li>
    <li>Select a category (e.g., "Entertainment").</li>
    <li>Connect to a <b>Facebook Page</b> (required for API access).</li>
</ol>

<div class="important">
⚠️ <b>Required:</b> Instagram API only works with <b>Business</b> or <b>Creator</b> accounts linked to a Facebook Page.
</div>

<h2>Phase 2 — Meta Developer Account</h2>
<ol>
    <li>Go to <a href="https://developers.facebook.com/">https://developers.facebook.com/</a></li>
    <li>Create a developer account (use same email as Facebook).</li>
    <li>Click <b>"My Apps" → "Create App"</b></li>
    <li>Select app type: <b>Business</b></li>
    <li>Enter app name and contact email.</li>
</ol>

<h2>Phase 3 — Add Instagram Graph API</h2>
<ol>
    <li>In your app dashboard, click <b>"Add Products"</b></li>
    <li>Find and add <b>"Instagram Graph API"</b></li>
    <li>Go to <b>Instagram Graph API → Settings</b></li>
    <li>Under <b>Access Tokens</b>, click <b>"Generate Access Token"</b></li>
    <li>Authorize with your Instagram account.</li>
</ol>

<h2>Phase 4 — Required Permissions</h2>
<p>Request these permissions during app review:</p>
<ul>
    <li><code>instagram_basic</code> — Read account info</li>
    <li><code>instagram_content_publish</code> — Publish content</li>
    <li><code>pages_show_list</code> — List connected pages</li>
    <li><code>pages_read_engagement</code> — Read page engagement</li>
</ul>

<h2>Phase 5 — App Review</h2>
<ol>
    <li>Go to <b>App Review → Permissions and Features</b></li>
    <li>Request <code>instagram_content_publish</code> permission.</li>
    <li>Provide a demo video showing your app publishing content.</li>
    <li>Explain how your app uses the data.</li>
</ol>

<div class="note">
💡 <b>Note:</b> You can test in Development mode with your own account before submitting for review.
</div>

<div class="success">✅ Once approved, the app will auto-publish Reels to your Instagram account.</div>
"""


# ─── X/Twitter Setup Guide ───────────────────────────────────────────────────

_TWITTER_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #1d9bf0; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
    .credential-box { background: #2d2d30; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 12px; }
    .credential-box b { color: #fff; }
    table { border-collapse: collapse; width: 100%; margin: 8px 0; }
    th, td { border: 1px solid #444; padding: 8px 12px; text-align: left; font-size: 12px; }
    th { background: #2d2d30; color: #fff; }
</style>

<h1>🐦 X / Twitter Setup Guide</h1>
<p style="color:#888; font-size: 12px;">Connect X/Twitter for auto-posting videos and text.</p>

<h2>Phase 1 — X Developer Account</h2>
<ol>
    <li>Go to <a href="https://developer.x.com/">https://developer.x.com/</a></li>
    <li>Sign in with your X/Twitter account.</li>
    <li>Click <b>"Sign up for a Free account"</b></li>
    <li>Describe your use case: "Automated video publishing for a desktop content creation tool"</li>
    <li>Verify your email address.</li>
</ol>

<h2>Phase 2 — Create a Project & App</h2>
<ol>
    <li>In the Developer Portal, go to <b>Projects & Apps → Overview</b></li>
    <li>Click <b>"Create Project"</b></li>
    <li>Enter project name and description.</li>
    <li>Create an <b>App</b> within the project.</li>
    <li>You'll receive:
        <ul>
            <li><b>API Key</b> (Consumer Key)</li>
            <li><b>API Secret</b> (Consumer Secret)</li>
            <li><b>Bearer Token</b></li>
        </ul>
    </li>
</ol>

<h2>Phase 3 — API Tiers</h2>
<table>
    <tr><th>Tier</th><th>Cost</th><th>Limit</th><th>Best For</th></tr>
    <tr><td>Free</td><td>$0</td><td>1,500 tweets/month</td><td>Testing only</td></tr>
    <tr><td>Basic</td><td>$100/month</td><td>50,000 tweets/month</td><td>Serious automation</td></tr>
    <tr><td>Pro</td><td>$5,000/month</td><td>1,000,000 tweets/month</td><td>Enterprise</td></tr>
</table>

<div class="important">
⚠️ <b>Important:</b> The Free tier is very restrictive. For serious video publishing, you'll need <b>Basic ($100/month)</b>.
</div>

<h2>Phase 4 — Configure OAuth</h2>
<ol>
    <li>Go to your App settings.</li>
    <li>Under <b>User authentication settings</b>, enable <b>OAuth 2.0</b>.</li>
    <li>Set callback URL: <code>http://localhost:8080/callback</code></li>
    <li>Set website URL: your website or GitHub repo.</li>
    <li>Permissions: <b>Read and Write</b></li>
</ol>

<h2>Phase 5 — Video Upload</h2>
<ol>
    <li>X supports video up to <b>512MB</b> / <b>2 minutes 20 seconds</b>.</li>
    <li>For longer videos, you need <b>Pro tier</b> (120 min limit).</li>
    <li>The app uses chunked upload for reliability.</li>
</ol>

<div class="success">✅ Enter your API Key and Secret in the app settings to enable auto-posting.</div>
"""


# ─── Rumble Setup Guide ─────────────────────────────────────────────────────

_RUMBLE_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #85c742; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
    .credential-box { background: #2d2d30; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 12px; }
    .credential-box b { color: #fff; }
</style>

<h1>📺 Rumble Setup Guide</h1>
<p style="color:#888; font-size: 12px;">Connect Rumble for auto-publishing videos.</p>

<div class="important">
⚠️ <b>Note:</b> Rumble does NOT have a public API for video uploads. Phantom uses <b>browser automation</b> (Playwright) to upload videos on your behalf. This means uploads are slightly slower than API-based platforms.
</div>

<h2>Phase 1 — Create a Rumble Account</h2>
<ol>
    <li>Go to <a href="https://rumble.com/">https://rumble.com/</a></li>
    <li>Click <b>"Register"</b> and create an account.</li>
    <li>Verify your email address.</li>
    <li>Complete your channel profile (name, avatar, description).</li>
</ol>

<h2>Phase 2 — Enable Monetization</h2>
<ol>
    <li>Go to <b>Account → Earnings</b></li>
    <li>Rumble offers multiple monetization tiers:
        <ul>
            <li><b>Standard:</b> Free to join, ad revenue share</li>
            <li><b>Exclusive:</b> Higher revenue share, content exclusivity</li>
            <li><b>Enterprise:</b> Custom deals for large creators</li>
        </ul>
    </li>
    <li>Complete the <b>payment setup</b> (PayPal or bank transfer).</li>
</ol>

<h2>Phase 3 — Revenue Share</h2>
<div class="credential-box">
    <b>Rumble Revenue Share:</b><br>
    • Standard: ~60% to creator, 40% to Rumble<br>
    • Exclusive: Higher share (negotiable)<br>
    • Estimated RPM: $1–$10 per 1K views<br>
    • Less competition than YouTube = easier to stand out
</div>

<h2>Phase 4 — Auto-Syndication</h2>
<ol>
    <li>Rumble can <b>auto-syndicate</b> from YouTube and Facebook.</li>
    <li>Go to <b>Account → Linked Accounts</b></li>
    <li>Connect your YouTube and Facebook accounts.</li>
    <li>Videos posted to YouTube will auto-appear on Rumble.</li>
</ol>

<div class="note">
💡 <b>Strategy:</b> Use Rumble as a secondary platform. Focus on YouTube and TikTok first, then let Rumble syndicate your content automatically.
</div>

<div class="success">✅ Rumble is connected. The app will use browser automation to upload videos.</div>
"""


# ─── Snapchat Guide ──────────────────────────────────────────────────────────

_SNAPCHAT_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #fffc00; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
</style>

<h1>👻 Snapchat Spotlight Guide</h1>
<p style="color:#888; font-size: 12px;">Important information about Snapchat content publishing.</p>

<div class="important">
⚠️ <b>Cannot Auto-Upload:</b> Snapchat does NOT have a public API for uploading content to Spotlight. All Spotlight submissions must go through the Snapchat mobile app. Phantom cannot automate this platform.
</div>

<h2>Why Is Snapchat Listed?</h2>
<p>Snapchat Spotlight <b>does pay creators</b> — but only for viral content:</p>
<ul>
    <li><b>Spotlight Payout:</b> $0.001–$0.01 per 1K views (highly variable)</li>
    <li><b>Requirements:</b> 1,000+ followers, content must go viral</li>
    <li><b>Payouts are sporadic</b> — Snapchat decides who gets paid</li>
    <li>Some creators report $100–$1,000+ for viral snaps</li>
</ul>

<h2>Manual Workflow</h2>
<ol>
    <li>Phantom generates your video and saves it to the <code>exports/</code> folder.</li>
    <li>Transfer the video to your phone (USB, cloud, or AirDrop).</li>
    <li>Open Snapchat → Camera → Upload from gallery.</li>
    <li>Add captions, filters, and submit to Spotlight.</li>
</ol>

<h2>Spotlight Tips</h2>
<ul>
    <li><b>Vertical 9:16</b> format required</li>
    <li><b>No watermarks</b> from other platforms</li>
    <li><b>15–60 seconds</b> optimal length</li>
    <li><b>Trending sounds</b> boost visibility</li>
    <li><b>First 3 seconds</b> must hook viewers</li>
</ul>

<div class="note">
💡 <b>Recommendation:</b> Snapchat is low priority for automation. Focus on YouTube, TikTok, and Instagram first. Use Snapchat only if you have viral content worth cross-posting manually.
</div>
"""


# ─── Facebook Setup Guide ────────────────────────────────────────────────────

_FACEBOOK_HTML = """
<style>
    body { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #ddd; line-height: 1.6; }
    h1 { color: #fff; font-size: 20px; margin-bottom: 4px; }
    h2 { color: #1877f2; font-size: 15px; margin-top: 24px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px; }
    ol { padding-left: 22px; }
    li { margin-bottom: 8px; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .note { background: #2d2d30; border-left: 3px solid #f59e0b; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; }
    .important { background: #3b1c1c; border-left: 3px solid #ef4444; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #fca5a5; }
    .success { background: #1c3b1c; border-left: 3px solid #22c55e; padding: 10px 14px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 12px; color: #86efac; }
    code { background: #2d2d30; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #93c5fd; }
    .credential-box { background: #2d2d30; border: 1px solid #444; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 12px; }
    .credential-box b { color: #fff; }
</style>

<h1>👍 Facebook Setup Guide</h1>
<p style="color:#888; font-size: 12px;">Connect Facebook for auto-publishing Reels and videos.</p>

<h2>Phase 1 — Facebook Page</h2>
<ol>
    <li>Go to <a href="https://www.facebook.com/pages/create">https://www.facebook.com/pages/create</a></li>
    <li>Create a new <b>Facebook Page</b> for your content.</li>
    <li>Choose category: <b>Entertainment</b> or <b>Creator</b>.</li>
    <li>Complete the page profile (name, bio, avatar, banner).</li>
</ol>

<h2>Phase 2 — Meta Developer Account</h2>
<ol>
    <li>Go to <a href="https://developers.facebook.com/">https://developers.facebook.com/</a></li>
    <li>Create a developer account (same as Instagram guide).</li>
    <li>Click <b>"My Apps" → "Create App"</b></li>
    <li>Select app type: <b>Business</b></li>
    <li>Add <b>"Facebook Login"</b> product.</li>
</ol>

<h2>Phase 3 — Configure OAuth</h2>
<ol>
    <li>Go to <b>Facebook Login → Settings</b></li>
    <li>Add <b>Valid OAuth Redirect URIs:</b> <code>http://localhost:8080/callback</code></li>
    <li>Enable <b>Client OAuth Login</b></li>
    <li>Enable <b>Web OAuth Login</b></li>
</ol>

<h2>Phase 4 — Required Permissions</h2>
<ul>
    <li><code>pages_manage_posts</code> — Create and manage posts</li>
    <li><code>pages_read_engagement</code> — Read page engagement data</li>
    <li><code>publish_video</code> — Upload and publish videos</li>
    <li><code>pages_show_list</code> — List managed pages</li>
</ul>

<h2>Phase 5 — Video Upload</h2>
<div class="credential-box">
    <b>Facebook Video Requirements:</b><br>
    • Max file size: <b>4GB</b><br>
    • Max length: <b>240 minutes</b><br>
    • Formats: MP4, MOV<br>
    • Aspect ratio: 16:9 (landscape) or 9:16 (Reels)<br>
    • Recommended: 1080p resolution
</div>

<h2>Phase 6 — App Review</h2>
<ol>
    <li>Go to <b>App Review → Permissions and Features</b></li>
    <li>Request <code>pages_manage_posts</code> and <code>publish_video</code>.</li>
    <li>Provide a demo showing your app publishing content.</li>
</ol>

<div class="success">✅ Once approved, the app will auto-publish Reels and videos to your Facebook Page.</div>
"""


# ─── Dialog Builder ──────────────────────────────────────────────────────────

_PLATFORM_GUIDES = {
    "youtube": {"title": "YouTube Setup Guide", "html": _YOUTUBE_HTML, "icon": "🎬", "color": "#ef4444"},
    "instagram": {"title": "Instagram Setup Guide", "html": _INSTAGRAM_HTML, "icon": "📸", "color": "#e1306c"},
    "x_twitter": {"title": "X / Twitter Setup Guide", "html": _TWITTER_HTML, "icon": "🐦", "color": "#1d9bf0"},
    "rumble": {"title": "Rumble Setup Guide", "html": _RUMBLE_HTML, "icon": "📺", "color": "#85c742"},
    "snapchat": {"title": "Snapchat Guide", "html": _SNAPCHAT_HTML, "icon": "👻", "color": "#fffc00"},
    "facebook": {"title": "Facebook Setup Guide", "html": _FACEBOOK_HTML, "icon": "👍", "color": "#1877f2"},
}


class PlatformSetupDialog(QDialog):
    """A scrollable dialog with platform-specific setup instructions."""

    def __init__(self, platform_key: str, parent=None):
        super().__init__(parent)
        info = _PLATFORM_GUIDES.get(platform_key, {})
        self.setWindowTitle(info.get("title", "Setup Guide"))
        self.setMinimumSize(720, 600)
        self.resize(780, 680)
        self.setStyleSheet(_DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Browser for rich HTML content
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(info.get("html", "<p>No guide available.</p>"))
        self.browser.setStyleSheet(_BROWSER_STYLE)
        layout.addWidget(self.browser)

        # Footer
        footer = QWidget()
        footer.setStyleSheet("background: #252526; padding: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 8, 24, 8)

        color = info.get("color", "#3b82f6")
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {'#000' if platform_key == 'snapchat' else 'white'};
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
            }}
            QPushButton:hover {{ opacity: 0.8; }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)
