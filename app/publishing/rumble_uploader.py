"""Rumble uploader — uploads via browser automation.

Since Rumble has no public upload API, this uses Playwright to automate
the upload process through the website, just like a human would.

SETUP REQUIRED:
1. Save your Rumble login credentials to config/rumble_credentials.json
2. Format: {"email": "your@email.com", "password": "your_password"}
"""

import json
import time
from pathlib import Path
from typing import Optional

from app.publishing.upload_orchestrator import UploadResult


class RumbleUploader:
    """
    Upload videos to Rumble via browser automation.

    Rumble has no public upload API, so this automates the website.
    Revenue sharing starts immediately (no minimum threshold).

    Setup:
        Save to config/rumble_credentials.json:
        {"email": "your@email.com", "password": "your_password"}
    """

    LOGIN_URL = "https://rumble.com/login"
    UPLOAD_URL = "https://rumble.com/upload.php"

    def __init__(self, credentials_path: str = "config/rumble_credentials.json"):
        self.credentials_path = Path(credentials_path)

    def _load_credentials(self) -> dict:
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Rumble credentials not found at: {self.credentials_path}\n"
                "Create the file with:\n"
                '{"email": "your@email.com", "password": "your_password"}'
            )
        with open(self.credentials_path) as f:
            return json.load(f)

    def upload(
        self,
        video_path: str,
        title: str = "",
        description: str = "",
        tags: Optional[list[str]] = None,
        thumbnail_path: Optional[str] = None,
        category: str = "entertainment",
        privacy: str = "public",
    ) -> UploadResult:
        """
        Upload a video to Rumble via browser automation.

        Args:
            video_path: Path to video file.
            title: Video title (max 100 chars).
            description: Video description.
            tags: List of tags/keywords.
            thumbnail_path: Optional thumbnail.
            category: Video category.
            privacy: "public" or "private".

        Returns:
            UploadResult with video URL.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return UploadResult(
                platform="rumble",
                success=False,
                error="playwright not installed: pip install playwright && python -m playwright install chromium",
            )

        creds = self._load_credentials()
        video_file = Path(video_path).resolve()

        if not video_file.exists():
            return UploadResult(
                platform="rumble",
                success=False,
                error=f"Video file not found: {video_file}",
            )

        try:
            with sync_playwright() as p:
                # Launch browser (headed so user can see what's happening)
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                )
                page = context.new_page()

                # Step 1: Login
                print("  Logging into Rumble...")
                page.goto(self.LOGIN_URL, wait_until="networkidle")
                time.sleep(2)

                # Fill email
                email_input = page.locator('input[name="account[email]"], input[type="email"], #email')
                email_input.wait_for(timeout=10000)
                email_input.fill(creds["email"])

                # Fill password
                password_input = page.locator('input[name="account[password]"], input[type="password"], #password')
                password_input.fill(creds["password"])

                # Click login button
                login_btn = page.locator('button[type="submit"], input[type="submit"], .login-button')
                login_btn.click()

                # Wait for login to complete
                page.wait_for_load_state("networkidle")
                time.sleep(3)

                # Check if login succeeded
                if "login" in page.url.lower():
                    browser.close()
                    return UploadResult(
                        platform="rumble",
                        success=False,
                        error="Login failed. Check your email and password in config/rumble_credentials.json",
                    )

                print("  Login successful! Navigating to upload page...")

                # Step 2: Go to upload page
                page.goto(self.UPLOAD_URL, wait_until="networkidle")
                time.sleep(2)

                # Step 3: Upload video file
                print(f"  Uploading video: {video_file.name}")
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(str(video_file))

                # Wait for upload to start/process
                print("  Waiting for upload to process...")
                time.sleep(5)

                # Step 4: Fill in title
                if title:
                    title_input = page.locator('input[name="title"], #title, input[placeholder*="title" i]')
                    if title_input.count() > 0:
                        title_input.first.fill(title[:100])
                        print(f"  Title set: {title[:100]}")

                # Step 5: Fill in description
                if description:
                    desc_input = page.locator('textarea[name="description"], #description, textarea')
                    if desc_input.count() > 0:
                        desc_input.first.fill(description[:5000])
                        print(f"  Description set ({len(description)} chars)")

                # Step 6: Set tags
                if tags:
                    tags_input = page.locator('input[name="tags"], #tags, input[placeholder*="tag" i]')
                    if tags_input.count() > 0:
                        tags_input.first.fill(", ".join(tags[:20]))
                        print(f"  Tags set: {', '.join(tags[:5])}")

                # Step 7: Set privacy
                if privacy == "private":
                    private_option = page.locator('text="Private"').first
                    if private_option.count() > 0:
                        private_option.click()
                        print("  Set to private")

                # Step 8: Click publish/upload button
                print("  Publishing...")
                publish_btn = page.locator('button:has-text("Publish"), button:has-text("Upload"), button[type="submit"]:has-text("Publish")')
                if publish_btn.count() > 0:
                    publish_btn.first.click()
                else:
                    # Try finding any primary action button
                    page.locator('.btn-primary, .btn-publish').first.click()

                # Wait for upload to complete
                page.wait_for_load_state("networkidle")
                time.sleep(5)

                # Get the video URL from the page
                video_url = page.url
                if "/video/" in video_url:
                    print(f"  ✅ Upload complete! URL: {video_url}")
                else:
                    video_url = f"https://rumble.com/c/{creds.get('channel', 'phantomInspiration')}"
                    print(f"  ✅ Upload submitted! Check your channel: {video_url}")

                browser.close()

            # Save credentials for next time (remember login)
            self._save_credentials(creds)

            return UploadResult(
                platform="rumble",
                success=True,
                video_id="browser_upload",
                video_url=video_url,
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            return UploadResult(
                platform="rumble",
                success=False,
                error=f"Rumble upload failed: {str(e)}",
            )

    def _save_credentials(self, creds: dict):
        """Save credentials for future uploads."""
        try:
            with open(self.credentials_path, "w") as f:
                json.dump(creds, f, indent=2)
        except Exception:
            pass
