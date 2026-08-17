"""Thumbnail generator — creates clickbait thumbnails for faceless videos.

Uses Pillow for image composition and Pollinations.ai for AI-generated elements.
Designed to maximize click-through rate (CTR) on YouTube, TikTok, etc.
"""

import subprocess
import random
from pathlib import Path
from typing import Optional
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class ThumbnailGenerator:
    """
    Generate clickbait thumbnails for faceless videos.

    Features:
    - Bold text overlays with outline/shadow
    - Background image generation via Pollinations
    - Niche-specific color schemes and styles
    - YouTube-optimized 1280x720 output

    Usage:
        gen = ThumbnailGenerator()

        # Generate from prompt
        thumb = gen.generate(
            title="THE HAUNTED LIGHTHOUSE",
            niche="scary_stories",
            output="projects/_thumbnails/thumb.jpg",
        )

        # Generate with custom background
        thumb = gen.generate(
            title="10 DARK SECRETS",
            background_image="assets/bg/dark_hallway.jpg",
            output="projects/_thumbnails/thumb.jpg",
        )
    """

    # Niche-specific color schemes
    NICHE_STYLES = {
        "scary_stories": {
            "bg_colors": [(10, 10, 10), (20, 0, 0), (0, 0, 20)],
            "text_color": (255, 255, 255),
            "accent_color": (255, 0, 0),
            "outline_color": (0, 0, 0),
            "style": "dark_red",
        },
        "reddit_stories": {
            "bg_colors": [(255, 69, 0), (30, 30, 30), (50, 50, 50)],
            "text_color": (255, 255, 255),
            "accent_color": (255, 140, 0),
            "outline_color": (0, 0, 0),
            "style": "reddit_orange",
        },
        "motivational": {
            "bg_colors": [(0, 0, 0), (10, 10, 30), (20, 20, 20)],
            "text_color": (255, 215, 0),
            "accent_color": (255, 255, 255),
            "outline_color": (0, 0, 0),
            "style": "gold_on_black",
        },
        "finance": {
            "bg_colors": [(0, 50, 0), (0, 30, 0), (10, 40, 10)],
            "text_color": (255, 255, 255),
            "accent_color": (0, 255, 0),
            "outline_color": (0, 0, 0),
            "style": "money_green",
        },
        "true_crime": {
            "bg_colors": [(20, 0, 0), (10, 0, 0), (30, 0, 0)],
            "text_color": (255, 255, 255),
            "accent_color": (200, 0, 0),
            "outline_color": (0, 0, 0),
            "style": "crime_red",
        },
        "unsolved_murder_mysteries": {
            "bg_colors": [(15, 0, 20), (10, 0, 15), (20, 0, 25)],
            "text_color": (255, 255, 255),
            "accent_color": (180, 0, 255),
            "outline_color": (0, 0, 0),
            "style": "purple_mystery",
        },
        "did_you_know": {
            "bg_colors": [(0, 50, 100), (0, 30, 80), (0, 40, 90)],
            "text_color": (255, 255, 0),
            "accent_color": (255, 255, 255),
            "outline_color": (0, 0, 0),
            "style": "blue_yellow",
        },
        "history": {
            "bg_colors": [(50, 30, 10), (40, 25, 5), (60, 35, 15)],
            "text_color": (255, 220, 150),
            "accent_color": (200, 150, 50),
            "outline_color": (0, 0, 0),
            "style": "sepia",
        },
        "space": {
            "bg_colors": [(0, 0, 20), (5, 0, 30), (0, 0, 15)],
            "text_color": (200, 220, 255),
            "accent_color": (100, 150, 255),
            "outline_color": (0, 0, 0),
            "style": "cosmic",
        },
        "psychology": {
            "bg_colors": [(30, 0, 50), (20, 0, 40), (40, 0, 60)],
            "text_color": (255, 255, 255),
            "accent_color": (200, 100, 255),
            "outline_color": (0, 0, 0),
            "style": "purple_mind",
        },
        "mystery": {
            "bg_colors": [(10, 10, 20), (5, 5, 15), (15, 15, 25)],
            "text_color": (200, 200, 220),
            "accent_color": (100, 150, 255),
            "outline_color": (0, 0, 0),
            "style": "dark_mystery",
        },
        "daily_meditation": {
            "bg_colors": [(20, 60, 80), (15, 50, 70), (25, 65, 85)],
            "text_color": (255, 255, 255),
            "accent_color": (150, 220, 255),
            "outline_color": (0, 30, 50),
            "style": "zen_blue",
        },
    }

    def __init__(self, output_dir: str = "projects/_thumbnails"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        title: str,
        niche: str = "did_you_know",
        background_image: Optional[str] = None,
        output: Optional[str] = None,
        width: int = 1280,
        height: int = 720,
    ) -> str:
        """
        Generate a clickbait thumbnail.

        Args:
            title: Bold text to put on thumbnail (ALL CAPS recommended).
            niche: Content niche for color scheme.
            background_image: Optional background image path.
            output: Output file path.
            width: Thumbnail width (default 1280 for YouTube).
            height: Thumbnail height (default 720 for YouTube).

        Returns:
            Path to generated thumbnail.
        """
        if not HAS_PILLOW:
            raise ImportError("Pillow not installed: pip install Pillow")

        style = self.NICHE_STYLES.get(niche, self.NICHE_STYLES["did_you_know"])

        if output is None:
            safe_title = "".join(c for c in title[:30] if c.isalnum() or c in " _").strip().replace(" ", "_")
            output = str(self.output_dir / f"thumb_{safe_title}.jpg")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create base image
        if background_image and Path(background_image).exists():
            # Use the actual story visual as the focal image rather than a
            # generic gradient.  Crop-to-fill makes vertical short imagery
            # work in a 16:9 long-form thumbnail as well.
            source = Image.open(background_image).convert("RGB")
            scale = max(width / source.width, height / source.height)
            resized = source.resize((int(source.width * scale), int(source.height * scale)), Image.LANCZOS)
            left = max(0, (resized.width - width) // 2)
            top = max(0, (resized.height - height) // 2)
            img = resized.crop((left, top, left + width, top + height))
            img = ImageEnhance.Contrast(img).enhance(1.12)
            img = ImageEnhance.Color(img).enhance(1.08)
        else:
            img = self._create_gradient_bg(width, height, style["bg_colors"])

        draw = ImageDraw.Draw(img)

        # A left-to-right overlay preserves the scene focal point while making
        # a short hook readable at feed size.
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for x in range(int(width * 0.72)):
            alpha = int(205 * (1 - x / (width * 0.78)))
            overlay_draw.line([(x, 0), (x, height)], fill=(0, 0, 0, max(0, alpha)))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Use a concise thumbnail hook, not the entire video title. Long text
        # is unreadable when a viewer is scrolling.
        hook = self._thumbnail_hook(title)
        self._draw_bold_text(
            draw, img, hook,
            width, height,
            style["text_color"],
            style["outline_color"],
            style.get("accent_color"),
        )

        # Save
        img.save(str(output_path), "JPEG", quality=95)
        return str(output_path)

    @staticmethod
    def _thumbnail_hook(title: str) -> str:
        """Create a 2-5 word visual hook from a longer upload title."""
        words = [word.strip(".,:;!?-—") for word in title.split()]
        stop = {"how", "to", "the", "a", "an", "and", "your", "you", "can", "will", "this", "with", "from", "for"}
        important = [word for word in words if word.lower() not in stop]
        return " ".join(important[:5]).upper() or "WATCH THIS"

    def generate_batch(
        self,
        scripts: list[dict],
        niche: str = "did_you_know",
    ) -> list[str]:
        """Generate thumbnails for a batch of scripts."""
        paths = []
        for script in scripts:
            title = script.get("title", "Untitled")
            path = self.generate(title=title, niche=niche)
            paths.append(path)
        return paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_gradient_bg(
        self, width: int, height: int, colors: list[tuple]
    ) -> "Image.Image":
        """Create a gradient background from colors."""
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Use the first color as base, create radial-ish gradient
        base_color = colors[0]
        for y in range(height):
            # Vertical gradient
            ratio = y / height
            r = int(base_color[0] * (1 - ratio * 0.3))
            g = int(base_color[1] * (1 - ratio * 0.3))
            b = int(base_color[2] * (1 - ratio * 0.3))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        return img

    def _draw_bold_text(
        self,
        draw: "ImageDraw.ImageDraw",
        img: "Image.Image",
        text: str,
        width: int,
        height: int,
        text_color: tuple,
        outline_color: tuple,
        accent_color: Optional[tuple] = None,
    ):
        """Draw bold, outlined text centered on the image."""
        # Try to use a large bold font
        font_size = min(width // 8, 80)
        font = self._get_font(font_size)

        # Word wrap if text is long
        lines = self._wrap_text(text, font, width - 100)

        # Calculate total text height
        line_height = font_size + 10
        total_height = len(lines) * line_height

        # Start Y position (centered vertically)
        y = (height - total_height) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2

            # Draw outline (multiple passes for thickness)
            outline_range = 4
            for dx in range(-outline_range, outline_range + 1):
                for dy in range(-outline_range, outline_range + 1):
                    if dx * dx + dy * dy <= outline_range * outline_range:
                        draw.text((x + dx, y + dy), line, font=font, fill=outline_color)

            # Draw main text
            draw.text((x, y), line, font=font, fill=text_color)

            # Draw accent underline
            if accent_color:
                line_y = y + font_size + 2
                draw.rectangle(
                    [x, line_y, x + text_width, line_y + 4],
                    fill=accent_color,
                )

            y += line_height

    def _get_font(self, size: int) -> "ImageFont.FreeTypeFont":
        """Get a bold font, falling back to default."""
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]
        for fp in font_paths:
            try:
                return ImageFont.truetype(fp, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = []

        # Create a temp draw to measure text
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [text]
