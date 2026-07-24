"""X / Twitter uploader — uploads via X API v2.

SETUP REQUIRED:
1. Go to https://developer.x.com
2. Apply for a developer account (free tier available)
3. Create a Project and App
4. Enable "OAuth 2.0" with PKCE
5. Add "tweet.write" and "users.read" scopes
6. Place credentials in config/x_credentials.json

FREE TIER: 1,500 tweets/month, 50 requests/15min for media upload.
"""

import json
import time
import webbrowser
import hashlib
import base64
import hmac
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, quote

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from app.publishing.upload_orchestrator import UploadResult


class XUploader:
    """
    Upload videos to X / Twitter via API v2.

    Setup:
        1. Go to https://developer.x.com
        2. Create a free developer account
        3. Create an app with tweet.write scope
        4. Save credentials to config/x_credentials.json:
           {
               "client_id": "YOUR_CLIENT_ID",
               "client_secret": "YOUR_CLIENT_SECRET",
               "redirect_uri": "http://localhost:8080/callback"
           }

    Usage:
        uploader = XUploader()
        result = uploader.upload(
            video_path="output.mp4",
            title="My Tweet",
            description="Tweet text #hashtags",
        )
    """

    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
    TWEET_URL = "https://api.twitter.com/2/tweets"

    def __init__(self, credentials_path: str = "config/x_credentials.json"):
        if not HAS_REQUESTS:
            raise ImportError("requests not installed: pip install requests")

        self.credentials_path = Path(credentials_path)
        self.token_path = Path("config/x_token.json")
        self._session = requests.Session()

    def _load_credentials(self) -> dict:
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"X credentials not found at: {self.credentials_path}\n"
                "Create the file with:\n"
                '{"client_id": "YOUR_CLIENT_ID", "client_secret": "YOUR_CLIENT_SECRET", '
                '"redirect_uri": "http://localhost:8080/callback"}\n\n'
                "Get credentials from: https://developer.x.com"
            )
        with open(self.credentials_path) as f:
            return json.load(f)

    def _get_access_token(self) -> str:
        """Get or refresh OAuth 2.0 access token."""
        if self.token_path.exists():
            with open(self.token_path) as f:
                token_data = json.load(f)
            if token_data.get("expires_at", 0) > time.time():
                return token_data["access_token"]

        creds = self._load_credentials()

        # OAuth 2.0 PKCE flow
        import secrets
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b"=").decode()

        auth_params = {
            "client_id": creds["client_id"],
            "redirect_uri": creds.get("redirect_uri", "http://localhost:8080/callback"),
            "response_type": "code",
            "scope": "tweet.write users.read",
            "state": "phantomstudio",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        auth_url = f"{self.AUTH_URL}?{urlencode(auth_params)}"
        print(f"\n  Open this URL to authorize X:\n  {auth_url}\n")
        webbrowser.open(auth_url)

        auth_code = input("  Paste the authorization code: ").strip()

        # Exchange code for token
        token_body = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": creds.get("redirect_uri", "http://localhost:8080/callback"),
            "client_id": creds["client_id"],
            "code_verifier": code_verifier,
        }

        r = self._session.post(self.TOKEN_URL, data=token_body)
        r.raise_for_status()
        result = r.json()

        token = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "expires_at": time.time() + result.get("expires_in", 7200),
        }

        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, "w") as f:
            json.dump(token, f)

        return token["access_token"]

    def upload(
        self,
        video_path: str,
        title: str = "",
        description: str = "",
        tags: Optional[list[str]] = None,
        thumbnail_path: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a video tweet.

        Args:
            video_path: Path to video (max 512MB, max 140s).
            title: Not used (X tweets don't have titles).
            description: Tweet text (max 280 chars).
            tags: Hashtags to append.

        Returns:
            UploadResult with tweet ID and URL.
        """
        try:
            access_token = self._get_access_token()

            # Build tweet text with hashtags
            tweet_text = description
            if tags:
                hashtag_str = " ".join(f"#{t.lstrip('#')}" for t in tags[:3])
                if len(tweet_text) + len(hashtag_str) + 1 <= 280:
                    tweet_text = f"{tweet_text}\n{hashtag_str}" if tweet_text else hashtag_str
                else:
                    tweet_text = tweet_text[:280]

            # Step 1: Upload video via v1.1 media upload (required for video)
            media_id = self._upload_media(video_path, access_token)

            # Step 2: Create tweet with media
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            tweet_body = {
                "text": tweet_text[:280],
                "media": {"media_ids": [media_id]},
            }

            r = self._session.post(self.TWEET_URL, json=tweet_body, headers=headers)
            r.raise_for_status()
            tweet_data = r.json().get("data", {})

            tweet_id = tweet_data.get("id")
            tweet_url = f"https://x.com/i/status/{tweet_id}"

            return UploadResult(
                platform="x_twitter",
                success=True,
                video_id=tweet_id,
                video_url=tweet_url,
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            return UploadResult(
                platform="x_twitter",
                success=False,
                error=str(e),
            )

    def _upload_media(self, video_path: str, access_token: str) -> str:
        """Upload media file and return media_id (v1.1 API required for video)."""
        headers = {"Authorization": f"Bearer {access_token}"}

        # INIT
        init_data = {
            "command": "INIT",
            "media_type": "video/mp4",
            "total_bytes": Path(video_path).stat().st_size,
            "media_category": "tweet_video",
        }
        r = self._session.post(self.UPLOAD_URL, data=init_data, headers=headers)
        r.raise_for_status()
        media_id = r.json()["media_id_string"]

        # APPEND (chunked upload)
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        with open(video_path, "rb") as f:
            segment_index = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                files = {"media": chunk}
                append_data = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index,
                }
                r = self._session.post(
                    self.UPLOAD_URL, data=append_data, files=files, headers=headers
                )
                r.raise_for_status()
                segment_index += 1

        # FINALIZE
        finalize_data = {
            "command": "FINALIZE",
            "media_id": media_id,
        }
        r = self._session.post(self.UPLOAD_URL, data=finalize_data, headers=headers)
        r.raise_for_status()

        # Wait for processing
        processing_info = r.json().get("processing_info", {})
        while processing_info.get("state") == "processing":
            time.sleep(5)
            check_url = f"{self.UPLOAD_URL}?command=STATUS&media_id={media_id}"
            r = self._session.get(check_url, headers=headers)
            r.raise_for_status()
            processing_info = r.json().get("processing_info", {})

        return media_id
