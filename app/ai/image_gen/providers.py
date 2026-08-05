"""Free image generation providers — no API key required.

Supports:
- Pollinations.ai (free cloud API)
- Pexels API (free stock photos)
- Unsplash API (free stock photos)
- Local Stable Diffusion via AUTOMATIC1111 API
- Local Stable Diffusion via ComfyUI API
"""

import base64
import json
import os
import requests
import time
from pathlib import Path
from typing import Optional
from io import BytesIO
from PIL import Image


class PollinationsProvider:
    """
    AI image generation via Pollinations.ai.

    The legacy unauthenticated endpoint is unreliable.  The current API accepts
    a server-side key in an Authorization header; the key is read from an
    ignored local file or environment variable and is never placed in a URL.
    """

    BASE_URL = "https://gen.pollinations.ai/image"

    def __init__(self, output_dir: str = "projects/_images", api_key: str | None = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self.api_key = api_key or self._load_api_key()

    @staticmethod
    def _load_api_key() -> str:
        """Load the local, git-ignored Pollinations key without logging it."""
        if os.environ.get("POLLINATIONS_API_KEY"):
            return os.environ["POLLINATIONS_API_KEY"].strip()
        secrets_path = Path("config/secrets.json")
        try:
            data = json.loads(secrets_path.read_text(encoding="utf-8"))
            return str(data.get("pollinations_api_key", "")).strip()
        except (OSError, ValueError, TypeError):
            return ""

    def generate(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        output_filename: str = None,
        seed: int = None,
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image.
            width: Image width in pixels.
            height: Image height in pixels.
            output_filename: Filename to save as.
            seed: Optional seed for reproducibility.

        Returns:
            Path to the saved image.
        """
        # Build the current authenticated API request.  Keep the credential in
        # a header so it is not saved in error logs, browser history, or output
        # metadata.
        encoded_prompt = requests.utils.quote(prompt)
        url = f"{self.BASE_URL}/{encoded_prompt}"
        params = {"width": width, "height": height, "model": "flux"}
        if seed is not None:
            params["seed"] = seed
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        # Generate filename
        if output_filename is None:
            safe_name = prompt[:50].replace(" ", "_").replace("/", "_")
            output_filename = f"pollinations_{safe_name}.jpg"

        output_path = self.output_dir / output_filename

        # Download with retries
        for attempt in range(3):
            try:
                r = self._session.get(url, params=params, headers=headers, timeout=180, stream=True)
                r.raise_for_status()
                content_type = r.headers.get("Content-Type", "").lower()
                if not content_type.startswith("image/"):
                    raise RuntimeError(f"Pollinations returned {content_type or 'an unexpected response'}")
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return str(output_path)
            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                else:
                    raise RuntimeError(f"Pollinations generation failed: {type(e).__name__}: {e}")

        return str(output_path)

    def generate_batch(
        self,
        prompts: list[str],
        width: int = 1920,
        height: int = 1080,
    ) -> list[str]:
        """Generate multiple images sequentially."""
        paths = []
        for i, prompt in enumerate(prompts, start=1):
            filename = f"scene_{i:03d}.jpg"
            path = self.generate(prompt, width, height, filename)
            paths.append(path)
        return paths


class StockImageProvider:
    """
    Free stock image provider via Pexels API.
    Get a free API key at: https://www.pexels.com/api/
    """

    def __init__(
        self,
        api_key: str = None,
        output_dir: str = "projects/_images",
    ):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()

    def search(
        self,
        query: str,
        count: int = 1,
        orientation: str = "landscape",
    ) -> list[str]:
        """
        Search Pexels for stock images and download them.

        Args:
            query: Search query.
            count: Number of images to download.
            orientation: "landscape", "portrait", or "square".

        Returns:
            List of downloaded file paths.
        """
        if not self.api_key:
            return self._fallback_search(query, count)

        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": count,
            "orientation": orientation,
        }

        r = self._session.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        paths = []
        for i, photo in enumerate(data.get("photos", []), start=1):
            img_url = photo["src"]["large"]
            filename = f"stock_{i:03d}.jpg"
            output_path = self.output_dir / filename

            img_r = self._session.get(img_url, timeout=60)
            img_r.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_r.content)
            paths.append(str(output_path))

        return paths

    def _fallback_search(self, query: str, count: int) -> list[str]:
        """Fallback to Pollinations when no Pexels key is set."""
        poll = PollinationsProvider(str(self.output_dir))
        paths = []
        for i in range(count):
            path = poll.generate(query, output_filename=f"fallback_{i:03d}.jpg")
            paths.append(path)
        return paths


class LocalStableDiffusion:
    """
    Local Stable Diffusion client.
    Supports AUTOMATIC1111 API (default port 7860)
    or ComfyUI API (default port 8188).
    """

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:7860",
        output_dir: str = "projects/_images",
    ):
        self.api_url = api_url.rstrip("/")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()

    def is_running(self) -> bool:
        """Check if the local SD instance is available."""
        try:
            r = self._session.get(f"{self.api_url}/sdapi/v1/options", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality, watermark, text, logo",
        width: int = 1920,
        height: int = 1080,
        steps: int = 25,
        cfg_scale: float = 7.0,
        output_filename: str = None,
    ) -> str:
        """Generate an image using the local AUTOMATIC1111 API."""
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
        }

        r = self._session.post(
            f"{self.api_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()

        # Decode base64 image
        import base64
        img_data = base64.b64decode(data["images"][0])

        if output_filename is None:
            safe_name = prompt[:50].replace(" ", "_").replace("/", "_")
            output_filename = f"sd_{safe_name}.png"

        output_path = self.output_dir / output_filename
        with open(output_path, "wb") as f:
            f.write(img_data)

        return str(output_path)
