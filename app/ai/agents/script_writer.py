"""ScriptWriter agent — generates viral faceless video scripts via Ollama.

This is the brain of Phantom Inspiration Studio's content pipeline.
"""

import json
from typing import Optional

from app.ai.providers.ollama_client import get_client
from app.ai.prompts.script_prompts import (
    SCRIPT_WRITER_SYSTEM,
    METADATA_SYSTEM,
    NICHES,
    short_form_script_prompt,
    long_form_script_prompt,
    metadata_prompt,
    title_generator_prompt,
    full_content_plan_prompt,
    niche_analysis_prompt,
)
from app.ai.models.script import (
    VideoScript,
    VideoFormat,
    ContentNiche,
    ScriptSegment,
    ContentMetadata,
    ContentPlan,
)


class ScriptWriter:
    """
    AI-powered script generator for faceless videos.

    Usage:
        writer = ScriptWriter()

        # Short-form script
        script = writer.write_short_form(
            topic="The most haunted place in America",
            niche="scary_stories",
            duration_seconds=60,
        )

        # Long-form script
        script = writer.write_long_form(
            topic="The mystery of the Dyatlov Pass",
            niche="true_crime",
            duration_minutes=10,
        )

        # Generate metadata for a platform
        metadata = writer.generate_metadata(script, platform="youtube")

        # Generate a full content plan
        plans = writer.generate_content_plan(niche="finance", count=5)
    """

    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.client = get_client()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _ensure_server(self):
        """Verify the Ollama server is reachable."""
        if not self.client.is_alive():
            raise ConnectionError(
                "Ollama server is not running. "
                "Start it with: ollama serve"
            )

    def _parse_json_response(self, raw: str) -> dict:
        """Safely parse a JSON response, stripping markdown fences if present."""
        text = raw.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

    # ------------------------------------------------------------------
    # SHORT-FORM SCRIPT
    # ------------------------------------------------------------------

    def write_short_form(
        self,
        topic: str,
        niche: str = "did_you_know",
        duration_seconds: int = 60,
        style: str = "engaging",
        extra_instructions: Optional[str] = None,
    ) -> VideoScript:
        """
        Generate a short-form video script (15-90 seconds).

        Returns a VideoScript with parsed segments.
        """
        self._ensure_server()

        prompt = short_form_script_prompt(
            topic=topic,
            niche=niche,
            duration_seconds=duration_seconds,
            style=style,
            extra_instructions=extra_instructions,
        )

        raw = self.client.generate(
            prompt=prompt,
            system=SCRIPT_WRITER_SYSTEM,
            temperature=0.85,
            num_predict=4096,
            format="json",
        )

        data = self._parse_json_response(raw)
        return self._build_script(data, niche, "short_form")

    # ------------------------------------------------------------------
    # LONG-FORM SCRIPT
    # ------------------------------------------------------------------

    def write_long_form(
        self,
        topic: str,
        niche: str = "scary_stories",
        duration_minutes: int = 10,
        style: str = "immersive",
        extra_instructions: Optional[str] = None,
    ) -> VideoScript:
        """
        Generate a long-form video script (5-15 minutes).

        Returns a VideoScript with parsed segments.
        """
        self._ensure_server()

        prompt = long_form_script_prompt(
            topic=topic,
            niche=niche,
            duration_minutes=duration_minutes,
            style=style,
            extra_instructions=extra_instructions,
        )

        raw = self.client.generate(
            prompt=prompt,
            system=SCRIPT_WRITER_SYSTEM,
            temperature=0.8,
            num_predict=8192,
            format="json",
        )

        data = self._parse_json_response(raw)
        return self._build_script(data, niche, "long_form")

    # ------------------------------------------------------------------
    # METADATA GENERATION
    # ------------------------------------------------------------------

    def generate_metadata(
        self,
        script: VideoScript,
        platform: str = "youtube",
    ) -> ContentMetadata:
        """Generate platform-specific metadata for a script."""
        self._ensure_server()

        prompt = metadata_prompt(
            script_title=script.title,
            niche=script.niche,
            platform=platform,
            full_narration=script.get_full_narration()[:800],
        )

        raw = self.client.generate(
            prompt=prompt,
            system=METADATA_SYSTEM,
            temperature=0.7,
            num_predict=2048,
            format="json",
        )

        data = self._parse_json_response(raw)

        niche_info = NICHES.get(script.niche, {})

        return ContentMetadata(
            platform=platform,
            title=data.get("title", script.title),
            description=data.get("description", ""),
            hashtags=data.get("hashtags", []),
            tags=data.get("tags", []),
            thumbnail_prompt=data.get("thumbnail_prompt", ""),
            best_posting_time=niche_info.get("best_times", ""),
            category=niche_info.get("name", ""),
        )

    # ------------------------------------------------------------------
    # TITLE GENERATOR
    # ------------------------------------------------------------------

    def generate_titles(
        self,
        topic: str,
        niche: str = "did_you_know",
        count: int = 10,
    ) -> list[dict]:
        """Generate multiple title options for a video topic."""
        self._ensure_server()

        prompt = title_generator_prompt(topic=topic, niche=niche, count=count)

        raw = self.client.generate(
            prompt=prompt,
            system=METADATA_SYSTEM,
            temperature=0.9,
            num_predict=2048,
            format="json",
        )

        data = self._parse_json_response(raw)
        return data.get("titles", [])

    # ------------------------------------------------------------------
    # FULL CONTENT PLAN
    # ------------------------------------------------------------------

    def generate_content_plan(
        self,
        niche: str,
        platform: str = "youtube",
        count: int = 3,
    ) -> list[dict]:
        """Generate complete content plans with topics, hooks, and metadata."""
        self._ensure_server()

        prompt = full_content_plan_prompt(
            niche=niche, platform=platform, count=count
        )

        raw = self.client.generate(
            prompt=prompt,
            system=SCRIPT_WRITER_SYSTEM + "\n\n" + METADATA_SYSTEM,
            temperature=0.85,
            num_predict=4096,
            format="json",
        )

        data = self._parse_json_response(raw)
        return data.get("plans", [])

    # ------------------------------------------------------------------
    # NICHE ANALYSIS
    # ------------------------------------------------------------------

    def analyze_niche(self, niche: str) -> dict:
        """Get a deep analysis of a content niche."""
        self._ensure_server()

        prompt = niche_analysis_prompt(niche)

        raw = self.client.generate(
            prompt=prompt,
            system=METADATA_SYSTEM,
            temperature=0.7,
            num_predict=3000,
            format="json",
        )

        return self._parse_json_response(raw)

    # ------------------------------------------------------------------
    # INTERNAL: Build VideoScript from parsed data
    # ------------------------------------------------------------------

    def _build_script(self, data: dict, niche: str, format_type: str) -> VideoScript:
        """Convert raw parsed JSON into a VideoScript object."""
        segments = []
        for i, seg in enumerate(data.get("segments", []), start=1):
            segments.append(
                ScriptSegment(
                    scene_number=seg.get("scene", i),
                    narration=seg.get("narration", ""),
                    image_prompt=seg.get("image_prompt", ""),
                    duration_seconds=seg.get("duration_seconds", 10),
                    transition=seg.get("transition", "cut"),
                )
            )

        # Try to extract a title from the data, or derive from hook
        title = data.get("title", "")
        if not title:
            hook = data.get("hook", "")
            title = hook[:80] if hook else "Untitled Script"

        niche_info = NICHES.get(niche, {})

        script = VideoScript(
            title=title,
            description=data.get("description", ""),
            niche=niche,
            format=format_type,
            segments=segments,
            total_duration_seconds=sum(s.duration_seconds for s in segments),
            tags=data.get("tags", []),
            hashtags=data.get("hashtags", niche_info.get("hashtags", [])),
            hook=data.get("hook", ""),
            cta=data.get("cta", ""),
        )

        return script

    # ------------------------------------------------------------------
    # UTILITY: List available niches
    # ------------------------------------------------------------------

    @staticmethod
    def available_niches() -> dict:
        """Return all available content niches with metadata."""
        return {
            key: {
                "name": val["name"],
                "audience": val["audience"],
                "rpm": val["rpm_range"],
                "best_times": val["best_times"],
            }
            for key, val in NICHES.items()
        }
