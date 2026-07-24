"""Instagram Reels uploader — uploads via Meta Graph API.

SETUP REQUIRED:
1. Go to https://developers.facebook.com
2. Create a new app (type: Business)
3. Add "Instagram Graph API" product
4. Create a Page Access Token with instagram_content_publish permission
5. You need an Instagram Business or Creator account linked to a Facebook Page
6. Place token in config/instagram_credentials.json

NO COST — Instagram API is free.
"""

import json
import time
from pathlib import Path
from typing import Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from app.publishing.upload_orchestrator import UploadResult


class InstagramUploader:
    """
    Upload Reels to Instagram via the Graph API.

    Requirements:
        - Instagram Business or Creator account
        - Linked Facebook Page
        - App with instagram_content_publish permission

    Usage:
        uploader = InstagramUploader()
        result = uploader.upload(
            video_path="output.mp4",
            title="My Reel",
            description="Caption with #hashtags",
        )
    """

    GRAPH_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, credentials_path: str = "config/instagram_credentials.json"):
        if not HAS_REQUESTS:
            raise ImportError("requests not installed: pip install requests")

        self.credentials_path = Path(credentials_path)
        self._session = requests.Session()
        self._page_id = None
        self._ig_account_id = None

    def _load_credentials(self) -> dict:
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Instagram credentials not found at: {self.credentials_path}\n"
                "Create the file with:\n"
                '{"access_token": "YOUR_LONG_LIVED_TOKEN", "ig_account_id": "YOUR_IG_BUSINESS_ACCOUNT_ID"}\n\n'
                "Steps:\n"
                "1. Go to https://developers.facebook.com\n"
                "2. Create app > Business type\n"
                "3. Add Instagram Graph API product\n"
                "4. Get Page Access Token from Graph API Explorer\n"
                "5. Exchange for long-lived token\n"
                "6. Get IG Business Account ID from Pages API"
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
        share_to_feed: bool = True,
    ) -> UploadResult:
        """
        Upload a Reel to Instagram.

        Args:
            video_path: Path to the video file (max 90 seconds for Reels).
            title: Not used by IG API (caption is used instead).
            description: Caption text.
            tags: Hashtags to include in caption.
            thumbnail_path: Optional cover image.
            share_to_feed: Whether to share to the main feed.

        Returns:
            UploadResult with media ID and permalink.
        """
        try:
            creds = self._load_credentials()
            access_token = creds["access_token"]
            ig_account_id = creds["ig_account_id"]

            # Build caption with hashtags
            caption = description
            if tags:
                hashtag_str = " ".join(f"#{t.lstrip('#')}" for t in tags[:25])
                caption = f"{caption}\n\n{hashtag_str}" if caption else hashtag_str

            # Step 1: Create media container
            container_url = f"{self.GRAPH_URL}/{ig_account_id}/media"
            container_body = {
                "media_type": "REELS",
                "video_url": self._get_public_url(video_path),  # Must be publicly accessible URL
                "caption": caption[:2200],
                "share_to_feed": share_to_feed,
                "access_token": access_token,
            }

            # Note: Instagram requires a PUBLICLY ACCESSIBLE video URL
            # For local files, you'd need to host them temporarily
            # This is a known limitation of the IG API

            r = self._session.post(container_url, data=container_body)
            r.raise_for_status()
            container_id = r.json()["id"]

            # Step 2: Wait for processing
            status_url = f"{self.GRAPH_URL}/{container_id}"
            status_params = {
                "fields": "status_code",
                "access_token": access_token,
            }

            for _ in range(30):  # Wait up to 5 minutes
                time.sleep(10)
                r = self._session.get(status_url, params=status_params)
                r.raise_for_status()
                status = r.json().get("status_code")
                if status == "FINISHED":
                    break
                elif status == "ERROR":
                    return UploadResult(
                        platform="instagram",
                        success=False,
                        error="Instagram media processing failed",
                    )

            # Step 3: Publish
            publish_url = f"{self.GRAPH_URL}/{ig_account_id}/media_publish"
            publish_body = {
                "creation_id": container_id,
                "access_token": access_token,
            }

            r = self._session.post(publish_url, data=publish_body)
            r.raise_for_status()
            media_id = r.json()["id"]

            return UploadResult(
                platform="instagram",
                success=True,
                video_id=media_id,
                video_url=f"https://www.instagram.com/reel/{media_id}",
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            return UploadResult(
                platform="instagram",
                success=False,
                error=str(e),
            )

    def _get_public_url(self, local_path: str) -> str:
        """
        Convert local path to a public URL.

        NOTE: Instagram REQUIRES a publicly accessible URL.
        For production, you'd upload to a temporary hosting service.
        This is a placeholder — you'll need to set up file hosting.
        """
        # For now, return the local path (won't work in production)
        # TODO: Implement temporary file hosting (e.g., file.io, transfer.sh)
        return f"file://{Path(local_path).absolute()}"
