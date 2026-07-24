"""Automation worker — runs the full video pipeline in a background thread.

This is the engine of Phantom Inspiration Studio. It runs in a QThread so
the UI stays responsive while videos are being generated and uploaded.
"""

import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

from app.ai.agents.script_writer import ScriptWriter
from app.ai.image_gen.image_manager import ImageManager
from app.ai.voice.edge_tts_provider import get_random_english_voice
from app.ai.voice.voice_manager import VoiceManager, VoiceConfig
from app.rendering.video_builder import VideoBuilder, VideoConfig
from app.rendering.subtitle_generator import SubtitleGenerator
from app.rendering.thumbnail_generator import ThumbnailGenerator
from app.rendering.audio_mixer import AudioMixer
from app.publishing.upload_orchestrator import UploadOrchestrator
from app.scheduler.rate_limiter import PLATFORM_RULES
from app.utils.logger import logger


class AutomationWorker(QThread):
    """Background worker that runs the full video automation pipeline."""

    # Signals to communicate with the UI
    log_message = Signal(str)
    progress_update = Signal(str, int)  # stage, percent
    status_change = Signal(str)         # current status text
    video_generated = Signal(str)       # video file path
    upload_complete = Signal(str, bool) # platform, success
    pipeline_complete = Signal(int)     # total videos produced this run
    error_occurred = Signal(str)        # error message

    def __init__(self, config: dict = None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self._mutex = QMutex()
        self._pause_condition = QWaitCondition()
        self._paused = False
        self._stopped = False
        self._videos_produced = 0

        # Lazy-loaded components
        self._script_writer = None
        self._image_manager = None
        self._voice_manager = None
        self._video_builder = None
        self._subtitle_gen = None
        self._thumbnail_gen = None
        self._audio_mixer = None
        self._orchestrator = None

    # ------------------------------------------------------------------
    # Control methods (called from UI thread)
    # ------------------------------------------------------------------

    def stop(self):
        """Signal the worker to stop after current task."""
        self._stopped = True
        self._paused = False
        self._pause_condition.wakeAll()

    def pause(self):
        """Pause the worker."""
        self._paused = True

    def resume(self):
        """Resume the worker."""
        self._paused = False
        self._pause_condition.wakeAll()

    def is_stopped(self):
        return self._stopped

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self):
        """Main automation loop — runs until stopped."""
        self._stopped = False
        self._videos_produced = 0
        max_videos = self.config.get("max_videos_per_run", 0)  # 0 = unlimited

        self.log_message.emit("🚀 Automation engine started")
        self.status_change.emit("Initializing components...")

        try:
            self._init_components()
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize: {e}")
            self.log_message.emit(f"❌ {e}")
            return

        while not self._stopped:
            # Check max videos limit
            if max_videos > 0 and self._videos_produced >= max_videos:
                self.log_message.emit(f"✅ Reached max videos ({max_videos}). Stopping.")
                break

            # Check daily limits for all enabled platforms
            enabled_platforms = self.config.get("enabled_platforms", [])
            if not enabled_platforms:
                self.log_message.emit("⚠️ No platforms enabled. Waiting...")
                self._sleep_or_stop(30)
                continue

            can_upload_any = False
            for platform in enabled_platforms:
                can, reason = self._orchestrator.can_upload(platform)
                if can:
                    can_upload_any = True
                    break

            if not can_upload_any:
                self.log_message.emit("⏳ All platforms rate-limited. Waiting 30 min...")
                self._sleep_or_stop(1800)
                continue

            # --- Produce one video ---
            try:
                self._produce_one_video(enabled_platforms)
                self._videos_produced += 1
            except Exception as e:
                self.error_occurred.emit(f"Pipeline error: {e}")
                self.log_message.emit(f"❌ Pipeline error: {e}")
                self._sleep_or_stop(60)
                continue

            # Wait between videos (randomized to appear human)
            gap_min = self.config.get("gap_between_videos_min", 30)
            gap_max = self.config.get("gap_between_videos_max", 120)
            wait_time = random.randint(gap_min, gap_max)
            self.log_message.emit(f"⏳ Waiting {wait_time}s before next video...")
            self._sleep_or_stop(wait_time)

        self.status_change.emit("Stopped")
        self.pipeline_complete.emit(self._videos_produced)
        self.log_message.emit(f"🏁 Automation stopped. Videos produced: {self._videos_produced}")

    # ------------------------------------------------------------------
    # Single video production pipeline
    # ------------------------------------------------------------------

    def _produce_one_video(self, enabled_platforms: list):
        """Run the full pipeline to produce and upload one video."""
        import random as _random

        # Resolve niche from the new multi-select system
        selected_niches = self.config.get("selected_niches", ["did_you_know"])
        randomize = self.config.get("randomize_niches", False)

        if randomize and selected_niches:
            niche = _random.choice(selected_niches)
        elif selected_niches:
            niche = selected_niches[0]
        else:
            niche = "did_you_know"   # fallback

        topic = self.config.get("topic", "")
        video_format = self.config.get("video_format", "short")  # short or long

        self.log_message.emit(f"\n{'='*50}")
        self.log_message.emit(f"🎬 Producing video #{self._videos_produced + 1}")
        self.log_message.emit(f"{'='*50}")

        # --- Step 1: Generate script ---
        self.status_change.emit("Writing script...")
        self.progress_update.emit("Script", 10)
        self.log_message.emit("✍️ Generating script...")

        if video_format == "short":
            script = self._script_writer.write_short_form(
                topic=topic or f"Amazing {niche.replace('_', ' ')} facts",
                niche=niche,
                duration_seconds=self.config.get("short_duration", 60),
            )
        else:
            script = self._script_writer.write_long_form(
                topic=topic or f"Deep dive into {niche.replace('_', ' ')}",
                niche=niche,
                duration_minutes=self.config.get("long_duration", 10),
            )

        self.log_message.emit(f"  Title: {script.title}")
        self.log_message.emit(f"  Duration: {script.total_duration_seconds:.1f}s")

        # --- Step 2: Generate images ---
        self.status_change.emit("Generating images...")
        self.progress_update.emit("Images", 30)
        self.log_message.emit("🖼️ Generating images...")

        segments_data = [s.to_dict() if hasattr(s, 'to_dict') else s for s in script.segments]
        image_paths = self._image_manager.generate_from_segments(
            segments=segments_data,
            niche=niche,
        )
        self.log_message.emit(f"  Generated {len(image_paths)} images")

        # --- Step 3: Generate voiceover ---
        self.status_change.emit("Generating voiceover...")
        self.progress_update.emit("Voice", 45)
        self.log_message.emit("🎤 Generating voiceover...")

        # Resolve voice selection: user pick, random, or niche default
        voice_selected = self.config.get("voice_selected", "random")

        if voice_selected == "random":
            voice_id = get_random_english_voice()
            self.log_message.emit(f"  🎲 Random voice selected: {voice_id}")
        else:
            voice_id = voice_selected

        voice_config = VoiceConfig(
            voice=voice_id,
            rate="+0%",     # Normal speech rate — always
            pitch="+0Hz",   # Normal pitch — always
            niche=niche,
        )
        audio_paths = self._voice_manager.generate_from_script(
            script_data=script.to_dict(),
            niche=niche,
            voice_config=voice_config,
        )
        self.log_message.emit(f"  Generated {len(audio_paths)} audio segments")

        # --- Step 4: Generate subtitles ---
        self.status_change.emit("Generating subtitles...")
        self.progress_update.emit("Subtitles", 55)

        output_dir = Path(f"projects/_output/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        srt_path = str(output_dir / "subtitles.srt")
        self._subtitle_gen.generate_from_segments(
            segments=segments_data,
            output=srt_path,
        )

        # --- Step 5: Mix audio ---
        self.status_change.emit("Mixing audio...")
        self.progress_update.emit("Audio", 65)

        full_audio = str(output_dir / "full_narration.mp3")
        if audio_paths:
            full_audio = audio_paths[0] if len(audio_paths) == 1 else str(output_dir / "full_narration.mp3")

        mixed_audio = self._audio_mixer.mix_for_niche(
            voiceover=full_audio,
            niche=niche,
            output=str(output_dir / "mixed_audio.mp3"),
        )

        # --- Step 6: Build video ---
        self.status_change.emit("Rendering video...")
        self.progress_update.emit("Render", 75)
        self.log_message.emit("🎞️ Rendering video...")

        video_config = VideoConfig.for_short() if video_format == "short" else VideoConfig.for_long()
        builder = VideoBuilder(config=video_config)

        video_path = builder.build(
            images=image_paths,
            audio=mixed_audio,
            output=str(output_dir / "final_video.mp4"),
            subtitles_file=srt_path,
        )
        self.log_message.emit(f"  ✅ Video rendered: {video_path}")
        self.video_generated.emit(video_path)

        # --- Step 7: Generate thumbnail ---
        self.status_change.emit("Generating thumbnail...")
        self.progress_update.emit("Thumbnail", 85)

        thumb_path = self._thumbnail_gen.generate(
            title=script.title,
            niche=niche,
            output=str(output_dir / "thumbnail.jpg"),
        )

        # --- Step 8: Generate metadata per platform ---
        self.status_change.emit("Optimizing metadata...")
        self.progress_update.emit("Metadata", 90)

        # --- Step 9: Upload to enabled platforms ---
        self.status_change.emit("Uploading...")
        self.progress_update.emit("Upload", 95)

        for platform in enabled_platforms:
            if self._stopped:
                break

            can, reason = self._orchestrator.can_upload(platform)
            if not can:
                self.log_message.emit(f"⏭️ {platform}: {reason}")
                continue

            self.log_message.emit(f"📤 Uploading to {platform}...")

            # Generate platform-specific metadata
            try:
                metadata = self._script_writer.generate_metadata(script, platform=platform)
                meta_title = metadata.title
                meta_desc = metadata.description
                meta_tags = metadata.hashtags
            except Exception:
                meta_title = script.title
                meta_desc = script.description
                meta_tags = script.hashtags

            result = self._orchestrator.upload_single(
                platform=platform,
                video_path=video_path,
                title=meta_title,
                description=meta_desc,
                niche=niche,
                thumbnail_path=thumb_path,
                tags=meta_tags,
            )

            if result.success:
                self.log_message.emit(f"  ✅ {platform}: {result.video_url or 'uploaded'}")
            else:
                self.log_message.emit(f"  ❌ {platform}: {result.error}")

            self.upload_complete.emit(platform, result.success)

            # Small gap between platform uploads
            if not self._stopped:
                self._sleep_or_stop(random.randint(5, 15))

        self.progress_update.emit("Done", 100)
        self.log_message.emit(f"✅ Video #{self._videos_produced + 1} complete!\n")

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_components(self):
        """Initialize all pipeline components."""
        self._script_writer = ScriptWriter(
            model=self.config.get("ollama_model", "qwen2.5:7b")
        )
        self._image_manager = ImageManager()
        self._voice_manager = VoiceManager()
        self._video_builder = VideoBuilder()
        self._subtitle_gen = SubtitleGenerator()
        self._thumbnail_gen = ThumbnailGenerator()
        self._audio_mixer = AudioMixer()
        self._orchestrator = UploadOrchestrator()

        self.log_message.emit("✅ All components initialized")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sleep_or_stop(self, seconds: int):
        """Sleep but check for stop/pause signals."""
        for _ in range(seconds):
            if self._stopped:
                return
            if self._paused:
                self._pause_condition.wait(self._mutex)
            time.sleep(1)
