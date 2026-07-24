"""TikTok uploader — uploads videos via TikTok Content Posting API.

SETUP REQUIRED:
1. Go to https://developers.tiktok.com
2. Create a developer account (free)
3. Create an app
4. Enable "Content Posting API" scope
5. Get your client_key and client_secret
6. Place them in config/tiktok_credentials.json

NO COST — TikTok API is free for video uploads.
"""

import base64
import hashlib
import json
import secrets
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from app.publishing.upload_orchestrator import UploadResult


class TikTokUploader:
    """
    Upload videos to TikTok via the Content Posting API.

    Setup:
        1. Register at https://developers.tiktok.com
        2. Create an app with Content Posting API access
        3. Save credentials to config/tiktok_credentials.json:
           {"client_key": "xxx", "client_secret": "xxx"}

    Usage:
        uploader = TikTokUploader()
        result = uploader.upload(
            video_path="output.mp4",
            title="My TikTok Video",
            description="Description #hashtag",
            privacy_level="PUBLIC_TO_EVERYONE",
        )
    """

    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
    VIDEO_PUBLISH_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

    PRIVACY_LEVELS = {
        "public": "PUBLIC_TO_EVERYONE",
        "friends": "FRIENDS_ONLY",
        "private": "SELF_ONLY",
    }

    def __init__(self, credentials_path: str = "config/tiktok_credentials.json"):
        if not HAS_REQUESTS:
            raise ImportError("requests not installed: pip install requests")

        self.credentials_path = Path(credentials_path)
        self.token_path = Path("config/tiktok_token.json")
        self._session = requests.Session()
        self._token = None

    def _load_credentials(self) -> dict:
        """Load TikTok API credentials."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"TikTok credentials not found at: {self.credentials_path}\n"
                "Create the file with:\n"
                '{"client_key": "YOUR_CLIENT_KEY", "client_secret": "YOUR_CLIENT_SECRET"}\n\n'
                "Get credentials from: https://developers.tiktok.com"
            )
        with open(self.credentials_path) as f:
            return json.load(f)

    def _get_access_token(self) -> str:
        """Get or refresh access token using PKCE + local server callback."""
        # Load saved token
        if self.token_path.exists():
            with open(self.token_path) as f:
                token_data = json.load(f)
            if token_data.get("expires_at", 0) > time.time():
                return token_data["access_token"]

        creds = self._load_credentials()

        # Generate PKCE code verifier and challenge
        # CRITICAL: TikTok uses HEX encoding of SHA256, NOT base64url!
        code_verifier = secrets.token_urlsafe(96)[:128]
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = digest.hex()  # HEX encoding, NOT base64url!

        # Build auth URL with PKCE
        auth_url = (
            f"{self.AUTH_URL}"
            f"?client_key={creds['client_key']}"
            f"&scope=video.upload,video.publish"
            f"&response_type=code"
            f"&redirect_uri=http://localhost:8080/callback"
            f"&state=phantomstudio"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )

        print(f"\n  Opening browser to authorize TikTok...")
        webbrowser.open(auth_url)

        # Start local server to capture the callback
        redirect_uri = creds.get("redirect_uri", "http://localhost:8080/callback")
        port = int(redirect_uri.split(":")[-1].split("/")[0]) if ":" in redirect_uri else 8080

        auth_code = self._capture_auth_code(port)

        if not auth_code:
            raise RuntimeError("Failed to get authorization code from TikTok.")

        # Exchange code for token (with PKCE code_verifier)
        data = {
            "client_key": creds["client_key"],
            "client_secret": creds["client_secret"],
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }

        r = self._session.post(self.TOKEN_URL, data=data)
        r.raise_for_status()
        result = r.json()

        # TikTok returns token at top level (not nested under "data")
        token_data = result.get("data", result)

        if not token_data.get("access_token"):
            raise RuntimeError(f"Token exchange failed: {r.text}")

        token = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "expires_at": time.time() + token_data.get("expires_in", 86400),
            "open_id": token_data.get("open_id", ""),
        }

        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, "w") as f:
            json.dump(token, f, indent=2)

        print(f"  ✅ TikTok token saved to {self.token_path}")
        return token["access_token"]

    def _capture_auth_code(self, port: int = 8080) -> Optional[str]:
        """Start a local HTTP server to capture the OAuth callback code."""
        class AuthHandler(BaseHTTPRequestHandler):
            code = None

            def do_GET(self):
                query = parse_qs(urlparse(self.path).query)
                if "code" in query:
                    AuthHandler.code = query["code"][0]
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<h1>Authorization successful!</h1>"
                        b"<p>You can close this tab and return to the app.</p>"
                    )
                else:
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    error = query.get("error", ["unknown"])[0]
                    self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())

            def log_message(self, format, *args):
                pass  # Suppress HTTP server logs

        print(f"  Waiting for authorization on port {port}...")
        server = HTTPServer(("localhost", port), AuthHandler)
        while AuthHandler.code is None:
            server.handle_request()
        server.server_close()

        return AuthHandler.code

    def upload(
        self,
        video_path: str,
        title: str = "",
        description: str = "",
        tags: Optional[list[str]] = None,
        thumbnail_path: Optional[str] = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
    ) -> UploadResult:
        """
        Upload a video to TikTok.

        Args:
            video_path: Path to the video file (must be MP4, max 5min).
            title: Video title/caption.
            description: Video description.
            tags: Hashtags to include.
            thumbnail_path: Optional thumbnail.
            privacy_level: PUBLIC_TO_EVERYONE, FRIENDS_ONLY, or SELF_ONLY.
            disable_duet: Disable duets.
            disable_comment: Disable comments.
            disable_stitch: Disable stitches.

        Returns:
            UploadResult with video ID.
        """
        try:
            access_token = self._get_access_token()
            video_path = Path(video_path)

            # Build caption with hashtags
            caption = description
            if tags:
                hashtag_str = " ".join(f"#{t.lstrip('#')}" for t in tags[:10])
                caption = f"{caption}\n\n{hashtag_str}" if caption else hashtag_str

            # Step 1: Initialize video upload
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            init_body = {
                "post_info": {
                    "title": title[:150],
                    "privacy_level": privacy_level,
                    "disable_duet": disable_duet,
                    "disable_comment": disable_comment,
                    "disable_stitch": disable_stitch,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_path.stat().st_size,
                },
            }

            r = self._session.post(self.VIDEO_INIT_URL, json=init_body, headers=headers)
            r.raise_for_status()
            init_data = r.json().get("data", {})

            upload_url = init_data.get("upload_url")
            publish_id = init_data.get("publish_id")

            if not upload_url:
                return UploadResult(
                    platform="tiktok",
                    success=False,
                    error=f"Failed to get upload URL: {r.text}",
                )

            # Step 2: Upload the video file
            with open(video_path, "rb") as f:
                upload_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{video_path.stat().st_size - 1}/{video_path.stat().st_size}",
                }
                r = self._session.put(upload_url, data=f, headers=upload_headers)
                r.raise_for_status()

            # Step 3: Check publish status
            time.sleep(5)  # Wait for processing
            status_headers = {"Authorization": f"Bearer {access_token}"}
            r = self._session.post(
                self.VIDEO_PUBLISH_URL,
                json={"publish_id": publish_id},
                headers=status_headers,
            )
            r.raise_for_status()

            return UploadResult(
                platform="tiktok",
                success=True,
                video_id=publish_id,
                posted_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

        except Exception as e:
            return UploadResult(
                platform="tiktok",
                success=False,
                error=str(e),
            )
