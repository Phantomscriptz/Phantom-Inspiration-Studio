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
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass
import requests

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google_auth_httplib2 import AuthorizedHttp
    import httplib2
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
        self._credentials = None

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

        # Give media transfers a finite timeout.  The default transport can
        # wait forever on a half-open connection, leaving the user with no
        # progress or usable error message.
        http = AuthorizedHttp(creds, http=httplib2.Http(timeout=90))
        self._service = build("youtube", "v3", http=http, cache_discovery=False)
        self._credentials = creds
        return self._service

    def _upload_resumable_file(
        self,
        video_path: str,
        body: dict,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict:
        """Upload through YouTube's resumable protocol with session recovery.

        A media POST can finish on YouTube while Windows loses the final HTTP
        response.  The resumable protocol gives us a session URL we can query
        after that interruption, so the app never guesses that a title match
        means a video was successfully created.
        """
        if not self._credentials:
            raise RuntimeError("YouTube credentials are not available for upload.")
        if self._credentials.expired and self._credentials.refresh_token:
            self._credentials.refresh(Request())

        source = Path(video_path)
        total_size = source.stat().st_size
        base_headers = {"Authorization": f"Bearer {self._credentials.token}"}
        def report(message: str) -> None:
            if progress_callback:
                progress_callback(message)

        report(f"Preparing secure YouTube upload ({total_size / 1024 / 1024:.1f} MB)...")
        init = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos",
            params={"uploadType": "resumable", "part": "snippet,status"},
            headers={
                **base_headers,
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(total_size),
            },
            data=json.dumps(body),
            timeout=(20, 90),
        )
        init.raise_for_status()
        session_url = init.headers.get("Location")
        if not session_url:
            raise RuntimeError("YouTube did not return a resumable upload session URL.")

        offset = 0
        # YouTube's resumable protocol uses 256 KB-aligned chunks.  The last
        # test proved this connection accepts the first 256 KB of a larger
        # request and then resets, so use the protocol's smallest practical
        # unit rather than repeatedly resending a 1 MB block.
        chunk_size = 256 * 1024
        stalled_recoveries = 0
        max_stalled_recoveries = 4
        report("YouTube accepted the upload session. Uploading in 256 KB chunks...")
        with source.open("rb") as handle:
            while offset < total_size:
                handle.seek(offset)
                chunk = handle.read(min(chunk_size, total_size - offset))
                end = offset + len(chunk) - 1
                try:
                    response = requests.put(
                        session_url,
                        headers={
                            **base_headers,
                            "Content-Type": "video/mp4",
                            "Content-Length": str(len(chunk)),
                            "Content-Range": f"bytes {offset}-{end}/{total_size}",
                        },
                        data=chunk,
                        timeout=(20, 180),
                    )
                except requests.RequestException as exc:
                    # Do not start another upload. Ask this exact session how
                    # many bytes it owns, or whether it already completed.
                    offset, completed = self._query_resumable_session(
                        session_url, total_size, base_headers
                    )
                    if completed:
                        report("YouTube confirmed the completed upload after reconnecting.")
                        return completed
                    if offset < 0:
                        raise RuntimeError(
                            "YouTube upload connection ended and the upload session could not be reconciled. "
                            "No automatic retry was made."
                        ) from exc
                    stalled_recoveries += 1
                    if stalled_recoveries >= max_stalled_recoveries:
                        raise RuntimeError(
                            "YouTube upload stalled after 4 resumable recovery checks. "
                            "No duplicate upload was created; check your connection and try again."
                        ) from exc
                    report(
                        f"Connection interrupted; YouTube retained {offset / 1024 / 1024:.1f} MB. "
                        f"Retrying ({stalled_recoveries}/{max_stalled_recoveries})..."
                    )
                    time.sleep(stalled_recoveries * 2)
                    continue

                if response.status_code in (200, 201):
                    report("YouTube confirmed the completed upload.")
                    return response.json()
                if response.status_code == 308:
                    next_offset = self._next_upload_offset(response.headers.get("Range"), end + 1)
                    if next_offset <= offset:
                        stalled_recoveries += 1
                        if stalled_recoveries >= max_stalled_recoveries:
                            raise RuntimeError(
                                "YouTube did not advance the resumable upload after 4 checks. "
                                "The session was stopped safely to avoid an endless wait."
                            )
                    else:
                        stalled_recoveries = 0
                    offset = next_offset
                    report(
                        f"YouTube upload progress: {min(100, round(offset * 100 / total_size))}% "
                        f"({offset / 1024 / 1024:.1f} / {total_size / 1024 / 1024:.1f} MB)"
                    )
                    continue
                response.raise_for_status()

        raise RuntimeError("YouTube resumable upload ended without a completed video response.")

    @staticmethod
    def _next_upload_offset(range_header: Optional[str], default: int) -> int:
        """Calculate the next byte from YouTube's resumable Range header."""
        if not range_header or "-" not in range_header:
            return default
        try:
            return int(range_header.rsplit("-", 1)[1]) + 1
        except ValueError:
            return default

    def _query_resumable_session(
        self, session_url: str, total_size: int, headers: dict
    ) -> tuple[int, Optional[dict]]:
        """Return next byte offset or the completed video from one session."""
        try:
            response = requests.put(
                session_url,
                headers={
                    **headers,
                    "Content-Length": "0",
                    "Content-Range": f"bytes */{total_size}",
                },
                data=b"",
                timeout=(20, 90),
            )
        except requests.RequestException:
            return -1, None
        if response.status_code in (200, 201):
            return total_size, response.json()
        if response.status_code == 308:
            return self._next_upload_offset(response.headers.get("Range"), 0), None
        return -1, None

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

    def _find_recent_matching_upload(self, title: str, started_at: float) -> Optional[str]:
        """Return a recent matching channel upload after an uncertain timeout.

        A broken connection can occur after YouTube has accepted the bytes but
        before the local client receives the final JSON response.  Reconciling
        against the owner's uploads playlist prevents a retry from creating a
        duplicate video.  This method never changes a YouTube video.
        """
        service = self._get_service()
        channel = service.channels().list(part="contentDetails", mine=True).execute()
        items = channel.get("items", [])
        if not items:
            return None
        uploads_id = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        if not uploads_id:
            return None
        # YouTube can take a moment to expose a newly accepted item, so check
        # the latest few items only.  The title and a short time window make a
        # false match extremely unlikely for this one-video workflow.
        for _ in range(3):
            feed = service.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_id,
                maxResults=10,
            ).execute()
            for item in feed.get("items", []):
                snippet = item.get("snippet", {})
                if snippet.get("title") != title:
                    continue
                published = item.get("contentDetails", {}).get("videoPublishedAt", "")
                # A matching title that was created before this attempt is not
                # sufficient evidence; use its observed upload time as a
                # simple guard without relying on locale-sensitive parsing.
                try:
                    published_at = datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
                except (TypeError, ValueError):
                    published_at = 0
                if published_at >= started_at - 5 * 60:
                    video_id = snippet.get("resourceId", {}).get("videoId")
                    # A playlist row alone is not sufficient proof. Confirm
                    # the actual video resource exists before recording an
                    # upload as successful or applying a posting limit.
                    details = service.videos().list(
                        part="id,status", id=video_id
                    ).execute().get("items", [])
                    if details:
                        return video_id
            time.sleep(5)
        return None

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list[str]] = None,
        thumbnail_path: Optional[str] = None,
        category: str = "22",        # 22 = People & Blogs
        privacy: str = "unlisted",   # public, private, unlisted
        made_for_kids: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
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
        started_at = time.time()
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

            response = self._upload_resumable_file(video_path, body, progress_callback=progress_callback)

            video_id = response["id"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Upload thumbnail if provided
            if thumbnail_path and Path(thumbnail_path).exists():
                if progress_callback:
                    progress_callback("Uploading custom thumbnail...")
                self._upload_thumbnail(service, video_id, thumbnail_path)

            return UploadResult(
                platform="youtube",
                success=True,
                video_url=video_url,
                video_id=video_id,
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            # Treat a transport timeout as "unknown", not as a guaranteed
            # failure.  YouTube may already have accepted the upload, and an
            # automatic retry in that state creates duplicate pending videos.
            error_text = str(e)
            if "timed out" in error_text.lower() or "connection aborted" in error_text.lower():
                try:
                    video_id = self._find_recent_matching_upload(title, started_at)
                    if video_id:
                        print("  YouTube upload response timed out; matching channel upload was reconciled.")
                        return UploadResult(
                            platform="youtube",
                            success=True,
                            video_url=f"https://www.youtube.com/watch?v={video_id}",
                            video_id=video_id,
                            posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                        )
                except Exception:
                    # Preserve the original transport error; reconciliation is
                    # a safety net, never a reason to hide a second failure.
                    pass
            return UploadResult(
                platform="youtube",
                success=False,
                error=error_text,
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
