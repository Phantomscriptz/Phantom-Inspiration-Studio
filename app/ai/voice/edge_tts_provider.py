"""Edge-TTS voice provider — free, high-quality Microsoft TTS.

Supports 400+ voices across 70+ languages with natural-sounding output.
No API key required. Runs entirely via Microsoft's free TTS service.
"""

import asyncio
import random
import edge_tts
from pathlib import Path
from typing import Optional


# ============================================================================
# Curated English voices — hand-picked for faceless video narration
# Each entry: (display_name, voice_id, gender, accent, description)
# ============================================================================
ENGLISH_VOICES = [
    # --- US Male ---
    ("🎙️ Guy (US) — Authoritative", "en-US-GuyNeural", "Male", "US", "Deep, confident narrator. Great for facts, finance, true crime."),
    ("🎙️ Brian (US) — Storyteller", "en-US-BrianNeural", "Male", "US", "Warm storytelling voice. Perfect for Reddit stories, mysteries."),
    ("🎙️ Andrew (US) — Energetic", "en-US-AndrewNeural", "Male", "US", "Upbeat and engaging. Ideal for motivational, tech, fitness."),
    ("🎙️ Christopher (US) — Deep", "en-US-ChristopherNeural", "Male", "US", "Deep and commanding. Best for horror, conspiracies, history."),
    ("🎙️ Eric (US) — Conversational", "en-US-EricNeural", "Male", "US", "Friendly and natural. Good for casual, relatable content."),
    ("🎙️ Roger (US) — Professional", "en-US-RogerNeural", "Male", "US", "Clean and professional. Works for finance, education."),
    ("🎙️ Steffan (US) — Clear", "en-US-SteffanNeural", "Male", "US", "Clear articulation. Great for educational content."),
    ("🎙️ Brian Multi (US) — Multilingual", "en-US-BrianMultilingualNeural", "Male", "US", "Brian with multilingual support. Handles code-switching."),
    ("🎙️ Andrew Multi (US) — Multilingual", "en-US-AndrewMultilingualNeural", "Male", "US", "Andrew with multilingual support."),

    # --- US Female ---
    ("🎙️ Jenny (US) — Narrator", "en-US-JennyNeural", "Female", "US", "Classic narrator. Clear, warm, works for almost any niche."),
    ("🎙️ Aria (US) — Soft", "en-US-AriaNeural", "Female", "US", "Gentle and soothing. Great for psychology, meditation, stories."),
    ("🎙️ Emma (US) — Energetic", "en-US-EmmaNeural", "Female", "US", "Lively and expressive. Perfect for did-you-know, fun facts."),
    ("🎙️ Ava (US) — Storyteller", "en-US-AvaNeural", "Female", "US", "Engaging storyteller. Ideal for Reddit stories, drama."),
    ("🎙️ Michelle (US) — Warm", "en-US-MichelleNeural", "Female", "US", "Warm and approachable. Good for lifestyle, wellness content."),
    ("🎙️ Ana (US) — Youthful", "en-US-AnaNeural", "Female", "US", "Young and casual. Works for trending topics, Gen-Z content."),
    ("🎙️ Ava Multi (US) — Multilingual", "en-US-AvaMultilingualNeural", "Female", "US", "Ava with multilingual support."),
    ("🎙️ Emma Multi (US) — Multilingual", "en-US-EmmaMultilingualNeural", "Female", "US", "Emma with multilingual support."),

    # --- UK Male ---
    ("🎙️ Ryan (UK) — Sophisticated", "en-GB-RyanNeural", "Male", "UK", "British accent. Elegant for history, mysteries, philosophy."),
    ("🎙️ Thomas (UK) — Calm", "en-GB-ThomasNeural", "Male", "UK", "Calm British voice. Great for nature, meditation, calming content."),

    # --- UK Female ---
    ("🎙️ Sonia (UK) — Elegant", "en-GB-SoniaNeural", "Female", "UK", "Refined British accent. Perfect for history, documentaries."),
    ("🎙️ Libby (UK) — Friendly", "en-GB-LibbyNeural", "Female", "UK", "Friendly British voice. Good for casual educational content."),
    ("🎙️ Maisie (UK) — Youthful", "en-GB-MaisieNeural", "Female", "UK", "Young British voice. Trending, relatable content."),

    # --- Australia ---
    ("🎙️ Natasha (AU)", "en-AU-NatashaNeural", "Female", "AU", "Australian accent. Friendly, approachable."),

    # --- Canada ---
    ("🎙️ Clara (CA)", "en-CA-ClaraNeural", "Female", "CA", "Canadian accent. Clear, neutral."),
    ("🎙️ Liam (CA)", "en-CA-LiamNeural", "Male", "CA", "Canadian accent. Natural, easy to listen to."),

    # --- India ---
    ("🎙️ Neerja (IN)", "en-IN-NeerjaNeural", "Female", "IN", "Indian English. Clear, professional."),
    ("🎙️ Prabhat (IN)", "en-IN-PrabhatNeural", "Male", "IN", "Indian English. Authoritative."),
]

# Voice presets per content style (backward compat)
VOICE_PRESETS = {
    "narrator_male": "en-US-GuyNeural",
    "narrator_male_deep": "en-US-ChristopherNeural",
    "narrator_male_uk": "en-GB-RyanNeural",
    "storyteller_male": "en-US-BrianNeural",
    "newsreader_male": "en-US-RogerNeural",
    "narrator_female": "en-US-JennyNeural",
    "narrator_female_soft": "en-US-AriaNeural",
    "narrator_female_uk": "en-GB-SoniaNeural",
    "storyteller_female": "en-US-AvaNeural",
    "newsreader_female": "en-US-EmmaNeural",
    "horror_male": "en-US-ChristopherNeural",
    "horror_female": "en-US-AriaNeural",
    "energetic_male": "en-US-AndrewNeural",
    "energetic_female": "en-US-EmmaNeural",
    "calm_male": "en-GB-ThomasNeural",
    "calm_female": "en-US-AriaNeural",
    "deep_male": "en-US-ChristopherNeural",
    "authoritative_male": "en-US-GuyNeural",
}


def get_random_english_voice() -> str:
    """Return a random curated English voice ID."""
    return random.choice(ENGLISH_VOICES)[1]


def get_voice_by_id(voice_id: str) -> Optional[tuple]:
    """Look up a voice by its ID. Returns (display_name, id, gender, accent, desc)."""
    for v in ENGLISH_VOICES:
        if v[1] == voice_id:
            return v
    return None

# Niche-to-voice mapping
NICHE_VOICE_MAP = {
    "scary_stories": "horror_male",
    "reddit_stories": "narrator_male",
    "motivational": "authoritative_male",
    "finance": "narrator_male_deep",
    "true_crime": "storyteller_male",
    "did_you_know": "narrator_female",
    "history": "narrator_male_uk",
    "space": "narrator_female_soft",
    "psychology": "narrator_female",
    "mystery": "horror_male",
    "nature_relaxation": "calm_female",
    "oddly_satisfying": "calm_female",
    "asmr": "calm_female",
    "tech_gadgets": "energetic_male",
    "fitness": "energetic_male",
    "conspiracy": "horror_male",
    "philosophy": "narrator_male_deep",
}


class EdgeTTSProvider:
    """Generate voiceover audio using Edge-TTS (free, no API key)."""

    def __init__(self, output_dir: str = "projects/_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _generate_async(
        self,
        text: str,
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        output_path: Optional[str] = None,
    ) -> str:
        """Generate audio asynchronously."""
        if output_path is None:
            output_path = str(self.output_dir / "voiceover.mp3")

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        await communicate.save(output_path)
        return output_path

    def generate(
        self,
        text: str,
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
        output_path: Optional[str] = None,
    ) -> str:
        """Generate voiceover audio from text.

        Args:
            text: The narration text.
            voice: Edge-TTS voice name (e.g., "en-US-GuyNeural").
            rate: Speech rate adjustment (e.g., "+10%", "-5%").
            pitch: Pitch adjustment (e.g., "+2Hz", "-1Hz").
            output_path: Where to save the MP3 file.

        Returns:
            Path to the generated audio file.
        """
        return asyncio.run(
            self._generate_async(text, voice, rate, pitch, output_path)
        )

    def generate_segments(
        self,
        segments: list[dict],
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> list[str]:
        """
        Generate audio for multiple script segments.

        Args:
            segments: List of dicts with 'narration' and optional 'scene' keys.
            voice: Voice to use.
            rate: Rate adjustment.
            pitch: Pitch adjustment.

        Returns:
            List of file paths for each segment's audio.
        """
        paths = []
        for i, seg in enumerate(segments, start=1):
            narration = seg.get("narration", "")
            if not narration.strip():
                continue

            output_path = str(self.output_dir / f"segment_{i:03d}.mp3")
            path = self.generate(narration, voice, rate, pitch, output_path)
            paths.append(path)

        return paths

    def generate_from_script(self, script_data: dict, niche: str = None) -> list[str]:
        """
        Generate all voiceover audio from a VideoScript dict.

        Auto-selects voice based on niche if not specified.
        """
        # Select voice based on niche
        preset_key = NICHE_VOICE_MAP.get(niche, "narrator_male")
        voice = VOICE_PRESETS.get(preset_key, "en-US-GuyNeural")

        segments = script_data.get("segments", [])
        return self.generate_segments(segments, voice=voice)

    def generate_full_narration(
        self,
        text: str,
        output_filename: str = "full_narration.mp3",
        voice: str = "en-US-GuyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """Generate a single audio file from the full narration text."""
        output_path = str(self.output_dir / output_filename)
        return self.generate(text, voice, rate, pitch, output_path)

    # ------------------------------------------------------------------
    # Voice utilities
    # ------------------------------------------------------------------

    @staticmethod
    async def list_voices(language: str = "en") -> list[dict]:
        """List available voices, optionally filtered by language."""
        voices = await edge_tts.list_voices()
        if language:
            voices = [v for v in voices if v["Locale"].startswith(language)]
        return [
            {
                "name": v["ShortName"],
                "gender": v["Gender"],
                "locale": v["Locale"],
                "friendly_name": v.get("FriendlyName", ""),
            }
            for v in voices
        ]

    @staticmethod
    def get_voice_for_niche(niche: str) -> str:
        """Get the recommended voice for a content niche."""
        preset_key = NICHE_VOICE_MAP.get(niche, "narrator_male")
        return VOICE_PRESETS.get(preset_key, "en-US-GuyNeural")

    @staticmethod
    def available_presets() -> dict:
        """Return all voice presets."""
        return VOICE_PRESETS.copy()
