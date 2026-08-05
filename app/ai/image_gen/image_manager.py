"""Image manager — orchestrates image generation for the video pipeline.

Uses authenticated Pollinations.ai as the primary provider,
with local Stable Diffusion as an optional upgrade.
"""

from pathlib import Path
import hashlib
from typing import Callable, Optional

from app.ai.image_gen.providers import (
    PollinationsProvider,
    StockImageProvider,
    LocalStableDiffusion,
)
from PIL import Image, ImageDraw, ImageFilter


# Image style enhancers per niche
NICHE_STYLE_MODIFIERS = {
    "scary_stories": "dark, cinematic, horror movie lighting, fog, shadows, 8k, photorealistic",
    "reddit_stories": "realistic, urban, everyday life, photorealistic, 8k",
    "motivational": "epic, cinematic, sunrise, mountain peak, dramatic lighting, inspiring, 8k",
    "finance": "professional, corporate, modern city skyline, luxury, clean, 8k",
    "true_crime": "noir, dark, moody, crime scene, detective, cinematic, 8k",
    "did_you_know": "vibrant, colorful, educational, detailed, 8k, photorealistic",
    "history": "ancient, historical, oil painting style, dramatic, epic, 8k",
    "space": "cosmic, nebula, stars, deep space, NASA style, breathtaking, 8k, photorealistic",
    "psychology": "abstract, mind, neural networks, surreal, thought-provoking, 8k",
    "mystery": "enigmatic, foggy, ancient ruins, candles, secret, atmospheric, 8k",
    "nature_relaxation": "serene, peaceful, nature, soft light, zen, beautiful, 8k, photorealistic",
    "oddly_satisfying": "satisfying, symmetrical, perfect, smooth, glossy, colorful, 8k",
}


class ImageManager:
    """
    High-level image generation interface.

    Automatically uses the best available provider:
    1. Local Stable Diffusion (if running)
    2. Pollinations.ai (credentialed, with local review fallback)
    3. Stock images (if API key provided)

    Usage:
        manager = ImageManager()

        # Generate from script segments
        images = manager.generate_from_segments(segments, niche="scary_stories")

        # Single image
        path = manager.generate("A dark haunted house on a hill")
    """

    def __init__(
        self,
        output_dir: str = "projects/_images",
        pexels_api_key: str = None,
        sd_api_url: str = "http://127.0.0.1:7860",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize providers
        self.pollinations = PollinationsProvider(output_dir)
        self.stock = StockImageProvider(pexels_api_key, output_dir)
        self.local_sd = LocalStableDiffusion(sd_api_url, output_dir)

        # Determine best provider
        self._use_local_sd = self.local_sd.is_running()
        self._use_pexels = pexels_api_key is not None
        self.last_warnings: list[str] = []

    def generate(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        niche: str = None,
        output_filename: str = None,
    ) -> str:
        """
        Generate a single image from a prompt.

        Automatically enhances the prompt with niche-specific style.
        """
        # Enhance prompt with style modifiers
        enhanced_prompt = self._enhance_prompt(prompt, niche)

        # Route to best available provider
        try:
            if self._use_local_sd:
                return self.local_sd.generate(
                    enhanced_prompt, width=width, height=height,
                    output_filename=output_filename,
                )
            return self.pollinations.generate(
                enhanced_prompt, width=width, height=height,
                output_filename=output_filename,
            )
        except Exception as exc:
            # A zero-budget cloud provider is not a production dependency.
            # Complete review renders with an unmistakably local visual rather
            # than discarding the entire script and voiceover on HTTP 500.
            message = f"Image provider unavailable ({type(exc).__name__}); used local review visual."
            if message not in self.last_warnings:
                self.last_warnings.append(message)
            return self._create_local_review_visual(
                prompt=enhanced_prompt, width=width, height=height,
                output_filename=output_filename,
            )

    def generate_from_segments(
        self,
        segments: list[dict],
        niche: str = None,
        width: int = 1920,
        height: int = 1080,
        on_scene_ready: Optional[Callable[[int, int, str, str], None]] = None,
    ) -> list[str]:
        """
        Generate images for all script segments.

        Args:
            segments: List of dicts with 'image_prompt' key.
            niche: Content niche for style enhancement.
            width: Image width.
            height: Image height.

        Returns:
            List of generated image file paths.
        """
        paths = []
        self.last_warnings = []
        for i, seg in enumerate(segments, start=1):
            image_prompt = seg.get("image_prompt", "")
            if not image_prompt.strip():
                continue

            filename = f"scene_{i:03d}.jpg"
            path = self.generate(
                image_prompt, width, height, niche, filename
            )
            paths.append(path)
            if on_scene_ready:
                on_scene_ready(i, len(segments), path, str(seg.get("narration", "")))

        return paths

    def _create_local_review_visual(
        self, prompt: str, width: int, height: int, output_filename: str | None
    ) -> str:
        """Create a tasteful abstract fallback without pretending it is AI art."""
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        color_a = tuple(20 + value // 3 for value in digest[:3])
        color_b = tuple(35 + value // 3 for value in digest[3:6])
        image = Image.new("RGB", (width, height), color_a)
        draw = ImageDraw.Draw(image, "RGBA")
        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(int(color_a[i] * (1 - ratio) + color_b[i] * ratio) for i in range(3))
            draw.line((0, y, width, y), fill=(*color, 255))
        for index in range(7):
            radius = int(min(width, height) * (0.12 + index * 0.035))
            x = int(width * (0.15 + (digest[6 + index] / 255) * 0.7))
            y = int(height * (0.12 + (digest[13 + index] / 255) * 0.7))
            glow = (220, 185, 100, max(12, 65 - index * 7))
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=glow)
        image = image.filter(ImageFilter.GaussianBlur(radius=max(2, min(width, height) // 140)))
        filename = output_filename or f"local_review_{digest.hex()[:10]}.jpg"
        output_path = self.output_dir / filename
        image.save(output_path, "JPEG", quality=92)
        return str(output_path)

    def search_stock(
        self, query: str, count: int = 5, orientation: str = "landscape"
    ) -> list[str]:
        """Search for stock images as a supplement or fallback."""
        return self.stock.search(query, count, orientation)

    def _enhance_prompt(self, prompt: str, niche: str = None) -> str:
        """Add style modifiers to a prompt based on the niche."""
        if niche and niche in NICHE_STYLE_MODIFIERS:
            modifier = NICHE_STYLE_MODIFIERS[niche]
            return f"{prompt}, {modifier}"
        return prompt

    def provider_status(self) -> dict:
        """Return the status of all image providers."""
        return {
            "local_sd": self._use_local_sd,
            "pollinations": bool(self.pollinations.api_key),
            "pexels": self._use_pexels,
        }
