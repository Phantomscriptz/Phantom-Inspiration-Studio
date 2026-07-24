"""Quick script to authorize TikTok with PKCE and save the access token."""

import base64
import hashlib
import json
import os
import secrets
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests

CREDS_PATH = "config/tiktok_credentials.json"
TOKEN_PATH = "config/tiktok_token.json"
REDIRECT_URI = "http://localhost:8080/callback"
PORT = 8080

# Load credentials
with open(CREDS_PATH) as f:
    creds = json.load(f)

CLIENT_KEY = creds["client_key"]
CLIENT_SECRET = creds["client_secret"]

# Generate PKCE code verifier and challenge
# TikTok requires: code_verifier 43-128 chars [A-Za-z0-9-._~]
# CRITICAL: TikTok uses HEX encoding of SHA256, NOT base64url!
code_verifier = secrets.token_urlsafe(96)[:128]
digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
code_challenge = digest.hex()  # HEX encoding, NOT base64url!

print(f"\nCode verifier length: {len(code_verifier)}")
print(f"Code challenge (hex): {code_challenge[:30]}...")

# Build auth URL with PKCE
auth_url = (
    f"https://www.tiktok.com/v2/auth/authorize/"
    f"?client_key={CLIENT_KEY}"
    f"&scope=video.upload,video.publish"
    f"&response_type=code"
    f"&redirect_uri={REDIRECT_URI}"
    f"&state=phantomstudio"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
)

print("\n" + "=" * 60)
print("TIKTOK AUTHORIZATION")
print("=" * 60)
print(f"\nOpening TikTok authorization page in your browser...")
print(f"If it doesn't open, visit this URL:\n\n{auth_url}\n")
print("After you authorize, you'll be redirected to localhost:8080")
print("The code will be captured automatically.\n")

# Start local server to capture the callback
class AuthHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            AuthHandler.code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this tab.</p>")
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error = query.get("error", ["unknown"])[0]
            self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())

    def log_message(self, format, *args):
        pass  # Suppress logs

# Open browser
webbrowser.open(auth_url)

# Start server
server = HTTPServer(("localhost", PORT), AuthHandler)
print(f"Waiting for authorization on port {PORT}...")
while AuthHandler.code is None:
    server.handle_request()

auth_code = AuthHandler.code
server.server_close()

print(f"\nGot authorization code: {auth_code[:20]}...")

# Exchange code for token (with PKCE code_verifier)
print("Exchanging code for access token...")

# Try with PKCE first
r = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    },
)

result = r.json()

# If PKCE fails, try without (some sandbox environments don't support PKCE)
if "error" in result and "code_verifier" in result.get("error_description", ""):
    print("PKCE failed, retrying without code_verifier...")
    r = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    result = r.json()

# TikTok returns token at top level (not nested under "data")
if "access_token" in result:
    token = {
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token", ""),
        "expires_at": time.time() + result.get("expires_in", 86400),
        "open_id": result.get("open_id", ""),
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token, f, indent=2)

    print(f"\n{'=' * 60}")
    print("✅ SUCCESS! TikTok token saved!")
    print(f"{'=' * 60}")
    print(f"Token saved to: {TOKEN_PATH}")
    print(f"Expires in: {result.get('expires_in', 'unknown')} seconds")
    print(f"Open ID: {result.get('open_id', 'unknown')}")
    print(f"\nYou can now upload videos to TikTok!")
elif "data" in result and "access_token" in result["data"]:
    token_data = result["data"]
    token = {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "expires_at": time.time() + token_data.get("expires_in", 86400),
        "open_id": token_data.get("open_id", ""),
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token, f, indent=2)

    print(f"\n{'=' * 60}")
    print("✅ SUCCESS! TikTok token saved!")
    print(f"{'=' * 60}")
    print(f"Token saved to: {TOKEN_PATH}")
    print(f"Expires in: {token_data.get('expires_in', 'unknown')} seconds")
    print(f"Open ID: {token_data.get('open_id', 'unknown')}")
    print(f"\nYou can now upload videos to TikTok!")
else:
    print(f"\n❌ ERROR: {r.text}")
