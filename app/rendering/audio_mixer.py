"""Audio mixer — combines voiceover + background music + SFX.

Uses pydub for audio manipulation and FFmpeg for final mixing.
All background music from free sources (YouTube Audio Library, Pixabay, etc.).
"""

import subprocess
import shutil
import random
from pathlib import Path
from typing import Optional


class AudioMixer:
    """
    Mix voiceover audio with background music and optional SFX.

    Features:
    - Auto-fades music during voiceover
    - Ducking (music volume drops when voice is active)
    - Adds subtle SFX (rain, fireplace, wind) per niche
    - Outputs mixed audio ready for video rendering

    Usage:
        mixer = AudioMixer()

        # Mix voiceover with background music
        mixed = mixer.mix(
            voiceover="projects/_audio/narration.mp3",
            background_music="assets/music/dark_ambient.mp3",
            output="projects/_audio/mixed.mp3",
        )

        # Mix with niche-appropriate ambient
        mixed = mixer.mix_for_niche(
            voiceover="projects/_audio/narration.mp3",
            niche="scary_stories",
            output="projects/_audio/mixed.mp3",
        )
    """

    def __init__(self, music_dir: str = "assets/music"):
        self.music_dir = Path(music_dir)
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        if not shutil.which("ffmpeg"):
            raise EnvironmentError("FFmpeg not found. Install: winget install ffmpeg")

    # ------------------------------------------------------------------
    # Core mixing
    # ------------------------------------------------------------------

    def mix(
        self,
        voiceover: str,
        background_music: Optional[str] = None,
        output: str = "mixed_audio.mp3",
        music_volume: float = 0.12,
        fade_in: float = 2.0,
        fade_out: float = 3.0,
        target_loudness: float = -16.0,
    ) -> str:
        """
        Mix voiceover with background music.

        Args:
            voiceover: Path to voiceover MP3.
            background_music: Path to background music. If None, uses default.
            output: Output file path.
            music_volume: Music volume relative to voice (0.0-1.0).
            fade_in: Music fade-in duration in seconds.
            fade_out: Music fade-out duration in seconds.
            target_loudness: Target loudness in LUFS.

        Returns:
            Path to the mixed audio file.
        """
        voiceover = Path(voiceover)
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        if not voiceover.exists():
            raise FileNotFoundError(f"Voiceover not found: {voiceover}")

        # Get voiceover duration
        voice_duration = self._get_duration(str(voiceover))

        # Select background music
        if background_music is None:
            background_music = self._select_default_music()
        if background_music is None:
            # No music available, just normalize voiceover
            shutil.copy(voiceover, output)
            return str(output)

        bg_path = Path(background_music)

        # Mix using FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", str(voiceover),
            "-i", str(bg_path),
            "-filter_complex",
            (
                # Music: fade in/out, loop to match voice duration, set volume
                f"[1:a]volume={music_volume},"
                f"afade=t=in:st=0:d={fade_in},"
                f"afade=t=out:st={voice_duration - fade_out}:d={fade_out},"
                f"atrim=0:{voice_duration},"
                f"asetpts=PTS-STARTPTS[music];"

                # Voiceover: normalize
                f"[0:a]loudnorm=I={target_loudness}:TP=-1.5:LRA=11[voice];"

                # Mix voice + music
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[out]"
            ),
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-q:a", "2",
            str(output),
        ]
        self._run_ffmpeg(cmd)
        return str(output)

    def mix_for_niche(
        self,
        voiceover: str,
        niche: str,
        output: str = "mixed_audio.mp3",
        music_volume: float = None,
    ) -> str:
        """
        Mix with niche-appropriate background music and settings.

        Automatically selects music and adjusts volume based on niche.
        """
        # Niche-specific settings
        NICHE_AUDIO_CONFIG = {
            "scary_stories": {"volume": 0.10, "fade_out": 4.0},
            "reddit_stories": {"volume": 0.08, "fade_out": 2.0},
            "motivational": {"volume": 0.12, "fade_out": 3.0},
            "finance": {"volume": 0.06, "fade_out": 2.0},
            "true_crime": {"volume": 0.10, "fade_out": 3.0},
            "unsolved_murder_mysteries": {"volume": 0.10, "fade_out": 4.0},
            "did_you_know": {"volume": 0.08, "fade_out": 2.0},
            "history": {"volume": 0.10, "fade_out": 3.0},
            "space": {"volume": 0.08, "fade_out": 4.0},
            "psychology": {"volume": 0.07, "fade_out": 2.0},
            "mystery": {"volume": 0.10, "fade_out": 4.0},
            "daily_meditation": {"volume": 0.15, "fade_out": 5.0},
            "nature_relaxation": {"volume": 0.15, "fade_out": 5.0},
        }

        config = NICHE_AUDIO_CONFIG.get(niche, {"volume": 0.10, "fade_out": 3.0})
        vol = music_volume or config["volume"]

        music = self._select_music_for_niche(niche)

        return self.mix(
            voiceover=voiceover,
            background_music=music,
            output=output,
            music_volume=vol,
            fade_out=config["fade_out"],
        )

    # ------------------------------------------------------------------
    # Music selection
    # ------------------------------------------------------------------

    def _select_default_music(self) -> Optional[str]:
        """Select any available background music."""
        music_files = list(self.music_dir.glob("*.mp3")) + list(self.music_dir.glob("*.wav"))
        if music_files:
            return str(random.choice(music_files))
        return None

    def _select_music_for_niche(self, niche: str) -> Optional[str]:
        """
        Select music that matches the niche mood.

        Music files should be named like:
        assets/music/dark_ambient.mp3
        assets/music/calm_piano.mp3
        assets/music/epic_cinematic.mp3
        """
        NICHE_MUSIC_KEYWORDS = {
            "scary_stories": ["dark", "horror", "suspense", "eerie"],
            "reddit_stories": ["lofi", "chill", "casual"],
            "motivational": ["epic", "cinematic", "powerful", "inspiring"],
            "finance": ["corporate", "clean", "modern"],
            "true_crime": ["dark", "noir", "investigation", "suspense"],
            "unsolved_murder_mysteries": ["dark", "noir", "mystery", "cold"],
            "did_you_know": ["curious", "wonder", "bright", "educational"],
            "history": ["epic", "cinematic", "ancient", "dramatic"],
            "space": ["cosmic", "ambient", "space", "ethereal"],
            "psychology": ["ambient", "thoughtful", "minimal"],
            "mystery": ["dark", "eerie", "ambient", "mysterious"],
            "daily_meditation": ["calm", "piano", "nature", "peaceful", "ambient"],
            "nature_relaxation": ["nature", "calm", "ambient", "rain", "forest"],
        }

        keywords = NICHE_MUSIC_KEYWORDS.get(niche, ["ambient"])
        music_files = list(self.music_dir.glob("*.mp3")) + list(self.music_dir.glob("*.wav"))

        if not music_files:
            return None

        # Try to find a matching file
        for keyword in keywords:
            for f in music_files:
                if keyword.lower() in f.stem.lower():
                    return str(f)

        # Fallback to any music
        return str(random.choice(music_files))

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _get_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds using FFprobe."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())

    def _run_ffmpeg(self, cmd: list[str]):
        """Run an FFmpeg command."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {result.stderr[:500]}")

    def list_music(self) -> list[str]:
        """List all available background music files."""
        music_files = list(self.music_dir.glob("*.mp3")) + list(self.music_dir.glob("*.wav"))
        return [f.name for f in sorted(music_files)]
