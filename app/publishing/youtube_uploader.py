"""YouTube uploader — uploads videos via YouTube Data API v3.

SETUP REQUIRED:
1. Go to https://console.cloud.google.com
2. Create a new project (or use existing)
3. Enable "YouTube Data API v3"
4. Create OAuth 2.0 credentials (Desktop App)
5. Download the client_secret.json file
6. Place it in config/youtube_client_secret.json
7. On first upload, you'll be prompted to authorize in your browser
8. Token is saved to config/youtube_token.json

NO COST — YouTube API is free for video uploads.
"""

import json
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False

from app.publishing.upload_orchestrator import UploadResult


# Upload plus the minimal read scope used to display the owner's public channel
# audience count in the app.  Existing upload-only tokens will re-consent once.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


class YouTubeUploader:
    """
    Upload videos to YouTube via the official API.

    Setup:
        1. Create credentials at https://console.cloud.google.com
        2. Enable YouTube Data API v3
        3. Place client_secret.json in config/
        4. First run will open browser for authorization

    Usage:
        uploader = YouTubeUploader()
        result = uploader.upload(
            video_path="output.mp4",
            title="My Video Title",
            description="Video description with hashtags",
            tags=["tag1", "tag2"],
            thumbnail_path="thumb.jpg",
            category="22",  # People & Blogs
            privacy="public",  # public, private, unlisted
        )
    """

    def __init__(
        self,
        client_secret_path: str = "config/youtube_client_secret.json",
        token_path: str = "config/youtube_token.json",
    ):
        if not HAS_GOOGLE_API:
            raise ImportError(
                "Google API libraries not installed.\n"
                "Run: pip install google-api-python-client google-auth google-auth-oauthlib"
            )

        self.client_secret_path = Path(client_secret_path)
        self.token_path = Path(token_path)
        self._service = None

    def _get_service(self):
        """Get authenticated YouTube API service."""
        if self._service:
            return self._service

        creds = None

        # Load existing token
        if self.token_path.exists():
            token_data = json.loads(self.token_path.read_text(encoding="utf-8"))
            granted_scopes = set(token_data.get("scopes", []))
            # The JSON records the scopes actually granted by Google. Passing
            # requested scopes into Credentials alone is not sufficient: an
            # old upload-only refresh token would otherwise fail with a
            # RefreshError when statistics are requested.
            if set(SCOPES).issubset(granted_scopes):
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.client_secret_path.exists():
                    raise FileNotFoundError(
                        f"YouTube client secret not found at: {self.client_secret_path}\n"
                        "Please download it from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com\n"
                        "2. APIs & Services > Credentials\n"
                        "3. Create OAuth 2.0 Client ID (Desktop App)\n"
                        "4. Download JSON and save to config/youtube_client_secret.json"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secret_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next time
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as f:
                f.write(creds.to_json())

        self._service = build("youtube", "v3", credentials=creds)
        return self._service

    def get_channel_audience(self) -> dict:
        """Return current channel counts using the official YouTube API."""
        service = self._get_service()
        response = service.channels().list(part="snippet,statistics", mine=True).execute()
        items = response.get("items", [])
        if not items:
            raise RuntimeError("No YouTube channel was returned for this account.")
        channel = items[0]
        stats = channel.get("statistics", {})
        return {
            "name": channel.get("snippet", {}).get("title", "YouTube channel"),
            "subscribers": stats.get("subscriberCount", "hidden"),
            "views": stats.get("viewCount", "0"),
        }

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list[str]] = None,
        thumbnail_path: Optional[str] = None,
        category: str = "22",        # 22 = People & Blogs
        privacy: str = "public",     # public, private, unlisted
        made_for_kids: bool = False,
    ) -> UploadResult:
        """
        Upload a video to YouTube.

        Args:
            video_path: Path to the video file.
            title: Video title (max 100 chars).
            description: Video description (max 5000 chars).
            tags: List of tags.
            thumbnail_path: Optional thumbnail image path.
            category: YouTube category ID. Default: 22 (People & Blogs).
            privacy: "public", "private", or "unlisted".
            made_for_kids: Whether the video is made for kids.

        Returns:
            UploadResult with video URL and ID.
        """
        try:
            service = self._get_service()

            # Build request body
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": tags[:30] if tags else [],  # Max 30 tags
                    "categoryId": category,
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en",
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": made_for_kids,
                    "embeddable": True,
                    "publicStatsViewable": True,
                },
            }

            # Create media upload
            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=10 * 1024 * 1024,  # 10MB chunks
            )

            # Execute upload
            request = service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"  YouTube upload progress: {int(status.progress() * 100)}%")

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Upload thumbnail if provided
            if thumbnail_path and Path(thumbnail_path).exists():
                self._upload_thumbnail(service, video_id, thumbnail_path)

            return UploadResult(
                platform="youtube",
                success=True,
                video_url=video_url,
                video_id=video_id,
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            return UploadResult(
                platform="youtube",
                success=False,
                error=str(e),
            )

    def _upload_thumbnail(self, service, video_id: str, thumbnail_path: str):
        """Upload a custom thumbnail for a video."""
        try:
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
        except Exception as e:
            print(f"  Warning: Thumbnail upload failed: {e}")

    def get_channel_info(self) -> dict:
        """Get authenticated channel information."""
        service = self._get_service()
        response = service.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True,
        ).execute()

        if response["items"]:
            channel = response["items"][0]
            return {
                "id": channel["id"],
                "title": channel["snippet"]["title"],
                "subscribers": channel["statistics"]["subscriberCount"],
                "videos": channel["statistics"]["videoCount"],
                "views": channel["statistics"]["viewCount"],
            }
        return {}
