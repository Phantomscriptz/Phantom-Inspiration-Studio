"""Voice manager — orchestrates voiceover generation for the full pipeline."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from app.ai.voice.edge_tts_provider import (
    EdgeTTSProvider,
    VOICE_PRESETS,
    NICHE_VOICE_MAP,
)


@dataclass
class VoiceConfig:
    """Configuration for voice generation."""
    voice: str = "en-US-GuyNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    niche: Optional[str] = None

    @classmethod
    def for_niche(cls, niche: str) -> "VoiceConfig":
        """Create a config auto-tuned for a niche."""
        preset_key = NICHE_VOICE_MAP.get(niche, "narrator_male")
        voice = VOICE_PRESETS.get(preset_key, "en-US-GuyNeural")
        return cls(voice=voice, niche=niche)


class VoiceManager:
    """
    High-level voice generation interface.

    Usage:
        manager = VoiceManager()

        # Generate from a script dict
        audio_files = manager.generate_from_script(script.to_dict())

        # Generate with specific voice
        audio = manager.generate("Hello world", voice="en-US-JennyNeural")
    """

    def __init__(self, output_dir: str = "projects/_audio"):
        self.provider = EdgeTTSProvider(output_dir=output_dir)
        self.output_dir = Path(output_dir)
        self.last_full_narration_path: Optional[str] = None

    def generate_from_script(
        self,
        script_data: dict,
        niche: Optional[str] = None,
        voice_config: Optional[VoiceConfig] = None,
    ) -> list[str]:
        """Generate all voiceover audio for a VideoScript dict."""
        if voice_config is None:
            niche = niche or script_data.get("niche", "did_you_know")
            voice_config = VoiceConfig.for_niche(niche)

        segments = script_data.get("segments", [])

        # Create subdirectory for this script
        title_slug = self._slugify(script_data.get("title", "script"))[:50]
        script_audio_dir = self.output_dir / title_slug
        script_audio_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, seg in enumerate(segments, start=1):
            narration = seg.get("narration", "")
            if not narration.strip():
                continue

            output_path = str(script_audio_dir / f"segment_{i:03d}.mp3")
            path = self.provider.generate(
                text=narration,
                voice=voice_config.voice,
                rate=voice_config.rate,
                pitch=voice_config.pitch,
                output_path=output_path,
            )
            paths.append(path)

        # Also generate the full narration as one file
        full_text = script_data.get("hook", "")
        for seg in segments:
            full_text += "\n\n" + seg.get("narration", "")

        full_path = str(script_audio_dir / "full_narration.mp3")
        self.last_full_narration_path = self.provider.generate_full_narration(
            text=full_text,
            output_filename=f"{title_slug}/full_narration.mp3",
            voice=voice_config.voice,
            rate=voice_config.rate,
            pitch=voice_config.pitch,
        )

        return paths

    def generate_single(
        self,
        text: str,
        output_name: str = "voiceover.mp3",
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """Generate a single voiceover audio file."""
        output_path = str(self.output_dir / output_name)
        return self.provider.generate(text, voice, rate, pitch, output_path)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a filesystem-safe slug."""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '_', text)
        return text[:80]
