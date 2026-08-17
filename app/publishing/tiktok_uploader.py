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
import math
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
    CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
    UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024

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
            if token_data.get("refresh_token"):
                refreshed = self._refresh_access_token(token_data)
                if refreshed:
                    return refreshed

        creds = self._load_credentials()

        redirect_uri = creds.get("redirect_uri", "http://localhost:8080/callback").rstrip("/")
        parsed_redirect = urlparse(redirect_uri)
        if (
            parsed_redirect.scheme not in {"http", "https"}
            or parsed_redirect.hostname not in {"localhost", "127.0.0.1", "::1"}
            or not parsed_redirect.port
            or "*" in redirect_uri
        ):
            raise ValueError(
                "TikTok Desktop Login Kit needs a fixed localhost callback URL, for example "
                "http://localhost:8080/callback. Register that exact same URL in the Developer Portal."
            )

        # Generate PKCE code verifier and challenge
        # CRITICAL: TikTok uses HEX encoding of SHA256, NOT base64url!
        code_verifier = secrets.token_urlsafe(96)[:128]
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = digest.hex()  # HEX encoding, NOT base64url!

        # Build auth URL with PKCE
        oauth_state = secrets.token_urlsafe(24)
        auth_url = f"{self.AUTH_URL}?" + urlencode({
            "client_key": creds["client_key"],
            # Keep this exactly aligned with the scopes selected in the
            # Developer Portal. video.upload is bundled with the Content
            # Posting API and is required for the file-transfer path.
            "scope": "user.info.basic,user.info.stats,video.upload,video.publish",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": oauth_state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })

        print(f"\n  Opening browser to authorize TikTok...")
        webbrowser.open(auth_url)

        # Start local server to capture the callback
        auth_code = self._capture_auth_code(
            parsed_redirect.port, parsed_redirect.hostname, expected_state=oauth_state
        )

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

    def _refresh_access_token(self, token_data: dict) -> Optional[str]:
        """Refresh an expired user token without requiring another browser login."""
        try:
            creds = self._load_credentials()
            response = self._session.post(
                self.TOKEN_URL,
                data={
                    "client_key": creds["client_key"],
                    "client_secret": creds["client_secret"],
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"],
                },
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json().get("data", response.json())
            access_token = payload.get("access_token")
            if not access_token:
                return None
            token_data.update({
                "access_token": access_token,
                "refresh_token": payload.get("refresh_token", token_data["refresh_token"]),
                "expires_at": time.time() + payload.get("expires_in", 86400),
                "open_id": payload.get("open_id", token_data.get("open_id", "")),
            })
            with open(self.token_path, "w") as handle:
                json.dump(token_data, handle, indent=2)
            return access_token
        except Exception:
            # OAuth will fall back to the interactive, user-approved browser flow.
            return None

    def _capture_auth_code(
        self, port: int = 8080, host: str = "localhost", expected_state: str = ""
    ) -> Optional[str]:
        """Start a local HTTP server to capture the OAuth callback code."""
        class AuthHandler(BaseHTTPRequestHandler):
            code = None

            def do_GET(self):
                query = parse_qs(urlparse(self.path).query)
                received_state = query.get("state", [""])[0]
                if "code" in query and secrets.compare_digest(received_state, expected_state):
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
                    error = query.get("error", ["invalid callback state"])[0]
                    self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())

            def log_message(self, format, *args):
                pass  # Suppress HTTP server logs

        print(f"  Waiting for authorization on port {port}...")
        server = HTTPServer((host, port), AuthHandler)
        while AuthHandler.code is None:
            server.handle_request()
        server.server_close()

        return AuthHandler.code

    def get_creator_info(self, access_token: Optional[str] = None) -> dict:
        """Return TikTok's current posting options for the connected creator.

        TikTok requires clients to query this immediately before Direct Post so
        the app can present only the privacy and interaction settings that the
        creator's account actually supports.
        """
        access_token = access_token or self._get_access_token()
        response = self._session.post(
            self.CREATOR_INFO_URL,
            json={},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        error = payload.get("error", {})
        if error.get("code") not in (None, "ok", 0):
            raise RuntimeError(error.get("message") or "TikTok rejected the creator-info request.")
        return payload.get("data", {})

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
        is_aigc: bool = True,
        creator_approved: bool = False,
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
            if not creator_approved:
                return UploadResult(
                    platform="tiktok",
                    success=False,
                    error="TikTok publishing needs your explicit approval in the TikTok platform tab.",
                )

            access_token = self._get_access_token()
            video_path = Path(video_path)
            if not video_path.is_file():
                raise FileNotFoundError(f"TikTok video not found: {video_path}")

            creator_info = self.get_creator_info(access_token)
            allowed_privacy = creator_info.get("privacy_level_options") or []
            # Apps still in review may be restricted to SELF_ONLY.  Never
            # silently change a creator's desired visibility.
            if privacy_level not in allowed_privacy:
                supported = ", ".join(allowed_privacy) or "none returned by TikTok"
                return UploadResult(
                    platform="tiktok",
                    success=False,
                    error=(f"TikTok does not currently allow {privacy_level} for this account. "
                           f"Available options: {supported}."),
                )

            # Build caption with hashtags
            caption = description
            if tags:
                hashtag_str = " ".join(f"#{t.lstrip('#')}" for t in tags[:10])
                caption = f"{caption}\n\n{hashtag_str}" if caption else hashtag_str

            video_size = video_path.stat().st_size
            chunk_size = min(self.UPLOAD_CHUNK_SIZE, video_size)
            total_chunks = max(1, math.ceil(video_size / chunk_size))

            # Step 1: Initialize a Direct Post upload.  The title field is
            # TikTok's caption, so it intentionally contains the short-form
            # description and relevant hashtags rather than a hidden filename.
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            init_body = {
                "post_info": {
                    "title": caption[:2200],
                    "privacy_level": privacy_level,
                    "disable_duet": disable_duet or bool(creator_info.get("duet_disabled")),
                    "disable_comment": disable_comment or bool(creator_info.get("comment_disabled")),
                    "disable_stitch": disable_stitch or bool(creator_info.get("stitch_disabled")),
                    # All media created by this pipeline is AI-assisted.  This
                    # label is a transparent platform disclosure, not a claim
                    # about whether a creator edited the final package.
                    "is_aigc": bool(is_aigc),
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunks,
                },
            }

            r = self._session.post(self.VIDEO_INIT_URL, json=init_body, headers=headers, timeout=30)
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

            # Step 2: Upload in the exact chunk layout declared above.  This
            # works for a small review MP4 and avoids loading a future longer
            # export into memory all at once.
            with open(video_path, "rb") as f:
                for chunk_index in range(total_chunks):
                    start = chunk_index * chunk_size
                    chunk = f.read(chunk_size)
                    end = start + len(chunk) - 1
                    upload_headers = {
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes {start}-{end}/{video_size}",
                    }
                    r = self._session.put(upload_url, data=chunk, headers=upload_headers, timeout=120)
                    r.raise_for_status()

            # Step 3: Check publish status
            time.sleep(5)  # Wait for processing
            status_headers = {"Authorization": f"Bearer {access_token}"}
            r = self._session.post(
                self.VIDEO_PUBLISH_URL,
                json={"publish_id": publish_id},
                headers=status_headers,
                timeout=30,
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
