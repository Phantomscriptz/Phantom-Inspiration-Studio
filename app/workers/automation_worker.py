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
from app.ai.voice.edge_tts_provider import get_random_english_voice, EdgeTTSProvider
from app.ai.voice.voice_manager import VoiceManager, VoiceConfig
from app.rendering.video_builder import VideoBuilder, VideoConfig
from app.rendering.subtitle_generator import SubtitleGenerator
from app.rendering.thumbnail_generator import ThumbnailGenerator
from app.rendering.audio_mixer import AudioMixer
from app.services.cinematic_broll import CinematicBrollPlanner
from app.services.content_quality import ContentQualityGate
from app.services.whisperx_aligner import WhisperXAligner
from app.publishing.upload_orchestrator import UploadOrchestrator
from app.scheduler.rate_limiter import PLATFORM_RULES
from app.publishing.platform_profiles import (
    VERTICAL_SHORT_PLATFORMS,
    LANDSCAPE_SHORT_PLATFORMS,
    LONG_LANDSCAPE_PLATFORMS,
)
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
        self._quality_gate = None
        self._whisperx_aligner = None

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
        if self.config.get("require_review_before_publish", True):
            # A review run is always one video, even if an older settings file
            # still contains the former unlimited default.
            max_videos = 1

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
            if not enabled_platforms and not self.config.get("require_review_before_publish", True):
                self.log_message.emit("⚠️ No platforms enabled. Waiting...")
                self._sleep_or_stop(30)
                continue

            can_upload_any = self.config.get("require_review_before_publish", True) and not enabled_platforms
            for platform in enabled_platforms:
                can, reason = self._orchestrator.can_upload(platform)
                if can:
                    can_upload_any = True
                    break

            if not can_upload_any:
                self.log_message.emit("⏳ All platforms rate-limited. Waiting 30 min...")
                self._sleep_or_stop(1800)
                continue

            # Build separately rendered workflows. A vertical Short is never a
            # resized copy of the long-form video.
            produced_this_cycle = False
            for video_format, platforms in self._build_workflows(enabled_platforms):
                if self._stopped or (max_videos > 0 and self._videos_produced >= max_videos):
                    break
                if platforms and not any(self._orchestrator.can_upload(platform)[0] for platform in platforms):
                    continue
                try:
                    self._produce_one_video(platforms, video_format)
                    self._videos_produced += 1
                    produced_this_cycle = True
                except Exception as e:
                    self.error_occurred.emit(f"Pipeline error: {e}")
                    self.log_message.emit(f"❌ Pipeline error: {e}")
                    # A bad pipeline step must not silently create a new script
                    # every minute. Stop and let the creator see the real error.
                    self._stopped = True
                    break
            if not produced_this_cycle:
                self._sleep_or_stop(60)
                continue

            # Do not make a completed one- or two-video review run sit idle
            # for the next publishing gap before reporting completion.
            if max_videos > 0 and self._videos_produced >= max_videos:
                self.log_message.emit(f"✅ Reached max videos ({max_videos}). Stopping.")
                break

            # Wait between videos to respect the creator's selected pace.
            gap_min = self.config.get("gap_between_videos_min", 30)
            gap_max = self.config.get("gap_between_videos_max", 120)
            wait_time = max(gap_min, gap_max)
            self.log_message.emit(f"⏳ Waiting {wait_time}s before next video...")
            self._sleep_or_stop(wait_time)

        self.status_change.emit("Stopped")
        self.pipeline_complete.emit(self._videos_produced)
        self.log_message.emit(f"🏁 Automation stopped. Videos produced: {self._videos_produced}")

    # ------------------------------------------------------------------
    # Single video production pipeline
    # ------------------------------------------------------------------

    def _produce_one_video(self, enabled_platforms: list, video_format: str = None):
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

        # A Short uses the same selected channel niche unless there is no
        # selection at all.  Do not silently replace a creator's choice with
        # the old YouTube-Shorts compatibility default.
        if not selected_niches and "youtube_shorts" in enabled_platforms:
            niche = self.config.get("youtube_shorts_niche", "motivational")

        topic = self.config.get("topic", "").strip()
        video_format = video_format or self.config.get("video_format", "short")

        self.log_message.emit(f"\n{'='*50}")
        self.log_message.emit(f"🎬 Producing video #{self._videos_produced + 1}")
        self.log_message.emit(f"{'='*50}")
        allowed_subniches = self.config.get("selected_subniches", {}).get(niche, [])
        self.log_message.emit(f"  Resolved niche: {niche}")
        if allowed_subniches:
            self.log_message.emit(f"  Allowed sub-categories: {', '.join(allowed_subniches)}")

        # --- Step 1: Generate script ---
        self.status_change.emit("Writing script...")
        self.progress_update.emit("Script", 10)
        self.log_message.emit("✍️ Generating script...")

        is_short = video_format in {"short", "vertical_short", "landscape_short"}
        workflow_instruction = (
            "Create a self-contained, distinct short-form angle. Do not summarize or reuse a long-form episode."
            if is_short else
            "Create a complete long-form episode with a different hook, structure, and payoff from any short-form companion."
        )
        if not topic:
            plan = self._script_writer.plan_topic(
                niche=niche,
                video_format="short-form" if is_short else "long-form",
                recent_topics=self._quality_gate.recent_topics(niche),
                enabled_subniches=allowed_subniches,
            )
            topic = plan["topic"]
            workflow_instruction += (
                f"\nEditorial angle: {plan.get('angle', '')}\n"
                f"Viewer promise: {plan.get('viewer_promise', '')}"
            )
            if plan.get("subniche"):
                self.log_message.emit(f"  Planned sub-category: {plan['subniche']}")
            self.log_message.emit(f"  Planned topic: {topic}")

        expected_duration = (
            float(self.config.get("short_duration", 45)) if is_short
            else float(self.config.get("long_duration", 10)) * 60
        )
        script = None
        quality_report = None
        for attempt in range(1, 4):
            retry_instruction = workflow_instruction
            if attempt > 1:
                retry_instruction += (
                    "\nRewrite from scratch. The previous draft was rejected for weak pacing or incomplete value. "
                    "Use a clearer hook, concrete progression, and enough natural narration for the requested length."
                )
                self.log_message.emit(f"  ↻ Rewriting draft ({attempt}/3) after editorial check...")
            script = (
                self._script_writer.write_short_form(
                    topic=topic, niche=niche, duration_seconds=int(expected_duration),
                    extra_instructions=retry_instruction,
                ) if is_short else
                self._script_writer.write_long_form(
                    topic=topic, niche=niche, duration_minutes=int(expected_duration / 60),
                    extra_instructions=retry_instruction,
                )
            )
            quality_report = self._quality_gate.evaluate(
                script,
                require_source_review=self.config.get("require_source_review", True),
                threshold=float(self.config.get("content_similarity_threshold", 0.72)),
                expected_duration_seconds=expected_duration,
            )
            if quality_report.publish_ready:
                break
            if attempt < 3:
                self.log_message.emit("  ⚠️ Draft rejected: " + "; ".join(quality_report.errors))

        if script is None or quality_report is None or not quality_report.publish_ready:
            errors = quality_report.errors if quality_report else ["No script was created."]
            raise RuntimeError("Script quality gate stopped the run: " + "; ".join(errors))

        self.log_message.emit(f"  Title: {script.title}")
        self.log_message.emit(f"  Duration: {script.total_duration_seconds:.1f}s")

        for warning in quality_report.warnings:
            self.log_message.emit(f"  ⚠️ Editorial review: {warning}")
        self._quality_gate.record(script)

        # --- Step 2: Generate images ---
        self.status_change.emit("Generating images...")
        self.progress_update.emit("Images", 30)
        self.log_message.emit("🖼️ Generating images...")

        segments_data = [s.to_dict() if hasattr(s, 'to_dict') else s for s in script.segments]
        # Treat the hook as scene zero so the opening visual, audio, and
        # captions are always aligned instead of leaving an invisible intro.
        hook_scene = {
            "scene_number": 0,
            "narration": script.hook,
            "image_prompt": segments_data[0].get("image_prompt", "cinematic hopeful dawn") if segments_data else "cinematic hopeful dawn",
            "duration_seconds": 3,
            "transition": "cut",
        }
        render_segments = [hook_scene] + segments_data if script.hook else segments_data
        render_config = VideoConfig.for_short() if video_format in {"short", "vertical_short"} else VideoConfig.for_long()
        selected_broll_name = Path(self.config.get("broll_selected_clip", "")).name
        selected_broll_path = Path("assets/stock_videos") / selected_broll_name
        using_single_broll = self.config.get("cinematic_broll", True) and selected_broll_name and selected_broll_path.is_file()
        image_paths = []
        if not using_single_broll:
            image_paths = self._image_manager.generate_from_segments(
                segments=render_segments,
                niche=niche,
                width=render_config.width,
                height=render_config.height,
            )
            self.log_message.emit(f"  Generated {len(image_paths)} images")
            for warning in self._image_manager.last_warnings:
                self.log_message.emit(f"  ⚠️ {warning}")

        visual_paths = image_paths
        visual_plan = []
        if using_single_broll:
            visual_paths, visual_plan = CinematicBrollPlanner().match_segments(
                render_segments, [""] * len(render_segments), niche=niche, selected_clip=selected_broll_name
            )
            motion_count = sum(item["type"] == "licensed_stock_video" for item in visual_plan)
            self.log_message.emit(f"  🎥 B-roll: using one selected clip for the full video ({motion_count} scene references)")
        elif self.config.get("cinematic_broll", True):
            self.log_message.emit("  🎥 B-roll is enabled, but no clip is selected; using generated visuals.")

        # --- Step 3: Generate voiceover ---
        self.status_change.emit("Generating voiceover...")
        self.progress_update.emit("Voice", 45)
        self.log_message.emit("🎤 Generating voiceover...")

        # Resolve voice selection: user pick, random, or niche default
        voice_selected = self.config.get("voice_selected", "random")

        if voice_selected == "random":
            # A coherent channel needs a consistent emotional voice. The
            # niche recommendation is deliberately used instead of randomly
            # jumping accents and vocal styles from video to video.
            voice_id = EdgeTTSProvider.get_voice_for_niche(niche)
            self.log_message.emit(f"  🎙️ Recommended voice selected: {voice_id}")
        else:
            voice_id = voice_selected

        soothing_voice = voice_id in {"en-US-AriaNeural", "en-US-JennyNeural", "en-US-MichelleNeural", "en-GB-ThomasNeural"}

        voice_config = VoiceConfig(
            voice=voice_id,
            rate="-8%" if soothing_voice else "+0%",
            pitch="-2Hz" if soothing_voice else "+0Hz",
            niche=niche,
        )
        audio_paths = self._voice_manager.generate_from_script(
            script_data=script.to_dict(),
            niche=niche,
            voice_config=voice_config,
        )
        self.log_message.emit(f"  Generated {len(audio_paths)} audio segments")
        if self._voice_manager.used_local_fallback:
            self.log_message.emit("  ⚠️ Microsoft neural voice was unavailable; used the local Piper Amy neural fallback for this review render.")

        # --- Step 4: Generate subtitles ---
        self.status_change.emit("Generating subtitles...")
        self.progress_update.emit("Subtitles", 55)

        output_dir = Path(f"projects/_output/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        output_dir.mkdir(parents=True, exist_ok=True)

        srt_path = str(output_dir / "subtitles.srt")
        timed_segments = []
        for index, segment in enumerate(render_segments):
            duration = self._video_builder._get_audio_duration(audio_paths[index]) if index < len(audio_paths) else segment.get("duration_seconds", 3)
            timed_segments.append({**segment, "duration_seconds": duration})
        full_audio = self._voice_manager.last_full_narration_path or str(output_dir / "full_narration.mp3")

        try:
            words = self._whisperx_aligner.align(full_audio, output_dir / "whisperx_words.json")
            self._subtitle_gen.generate_from_word_timestamps(words=words, output=srt_path)
            self.log_message.emit(f"  ✅ WhisperX aligned {len(words)} caption words to narration")
        except Exception as exc:
            # The render still succeeds if a local alignment model is unavailable.
            self._subtitle_gen.generate_from_segments(segments=timed_segments, output=srt_path)
            self.log_message.emit(f"  ⚠️ WhisperX unavailable; used timing fallback: {exc}")

        # --- Step 5: Mix audio ---
        self.status_change.emit("Mixing audio...")
        self.progress_update.emit("Audio", 65)

        mixed_audio = self._audio_mixer.mix_for_niche(
            voiceover=full_audio,
            niche=niche,
            output=str(output_dir / "mixed_audio.mp3"),
        )

        # --- Step 6: Build video ---
        self.status_change.emit("Rendering video...")
        self.progress_update.emit("Render", 75)
        self.log_message.emit("🎞️ Rendering video...")

        builder = VideoBuilder(config=render_config)

        # Real segment audio governs every scene duration. This works for
        # both AI stills and B-roll clips and prevents subtitle drift.
        if using_single_broll:
            video_path = builder.build_looping_broll(
                broll_path=str(selected_broll_path),
                audio=mixed_audio,
                output=str(output_dir / "final_video.mp4"),
                subtitles_file=srt_path,
            )
        else:
            video_path = builder.build_from_visual_segments(
                visual_paths=visual_paths,
                segment_audio_paths=audio_paths,
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
        self.log_message.emit("🧾 Generating title, description, hashtags, and review package...")

        review_platforms = enabled_platforms or ["youtube_shorts"]
        review_metadata = {}
        for platform in review_platforms:
            try:
                metadata = self._script_writer.generate_metadata(script, platform=platform)
                optimized = self._orchestrator.hashtag_optimizer.optimize(
                    platform=platform,
                    niche=niche,
                    title=metadata.title or script.title,
                    narration_excerpt=script.get_full_narration(),
                    extra_hashtags=metadata.hashtags or script.hashtags,
                )
                hashtags = optimized["hashtags"]
                description = metadata.description.strip() or script.description.strip()
                if hashtags and not all(tag in description for tag in hashtags):
                    description = f"{description}\n\n{' '.join(hashtags)}".strip()
                description = self._orchestrator._append_affiliate_links(description, platform, niche)
                review_metadata[platform] = {
                    "title": optimized["title"],
                    "description": description,
                    "hashtags": hashtags,
                    "tags": metadata.tags or script.tags,
                    "thumbnail_prompt": metadata.thumbnail_prompt,
                    "best_posting_time": metadata.best_posting_time,
                }
            except Exception as exc:
                self.log_message.emit(f"⚠️ Metadata fallback for {platform}: {exc}")
                review_metadata[platform] = {
                    "title": script.title,
                    "description": self._orchestrator._append_affiliate_links(script.description, platform),
                    "hashtags": script.hashtags,
                    "tags": script.tags,
                    "thumbnail_prompt": "",
                    "best_posting_time": "",
                }

        review_package = {
            "video_path": str(Path(video_path).resolve()),
            "thumbnail_path": str(Path(thumb_path).resolve()),
            "topic": topic,
            "niche": niche,
            "script": script.to_dict(),
            "references": script.references,
            "quality_report": quality_report.to_dict(),
            "visual_plan": visual_plan,
            "platform_metadata": review_metadata,
        }
        with open(output_dir / "review_package.json", "w", encoding="utf-8") as handle:
            json.dump(review_package, handle, indent=2, ensure_ascii=False)
        visual_credits = self._format_visual_credits(visual_plan)
        if visual_credits:
            (output_dir / "visual_credits.txt").write_text(visual_credits, encoding="utf-8")
        for platform, metadata in review_metadata.items():
            safe_platform = platform.replace("/", "_")
            (output_dir / f"{safe_platform}_title.txt").write_text(metadata["title"], encoding="utf-8")
            (output_dir / f"{safe_platform}_description.txt").write_text(metadata["description"], encoding="utf-8")
        self.log_message.emit(f"  ✅ Review package saved: {output_dir / 'review_package.json'}")

        # --- Step 9: Upload to enabled platforms ---
        if self.config.get("require_review_before_publish", True):
            self.progress_update.emit("Ready for review", 100)
            self.log_message.emit("📝 Video generated for review. Uploads are disabled until you uncheck 'Generate only'.")
            return

        if not quality_report.publish_ready:
            reason = "; ".join(quality_report.errors)
            raise RuntimeError(f"Publishing blocked by editorial review: {reason}")

        unverified_clips = [item for item in visual_plan if item.get("type") == "licensed_stock_video" and not item.get("license_verified")]
        if unverified_clips:
            raise RuntimeError("Publishing blocked: one or more B-roll clips have no saved source and license record.")

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
        self._orchestrator = UploadOrchestrator(settings={
            "platform_limits": self.config.get("platform_limits", {}),
            "affiliate_links": self.config.get("affiliate_links", []),
        })
        self._quality_gate = ContentQualityGate()
        self._whisperx_aligner = WhisperXAligner()

        self.log_message.emit("✅ All components initialized")

    def _build_workflows(self, enabled_platforms: list[str]) -> list[tuple[str, list[str]]]:
        """Group only compatible platforms; each group receives its own render."""
        workflows = []
        vertical = [platform for platform in enabled_platforms if platform in VERTICAL_SHORT_PLATFORMS]
        landscape_short = [platform for platform in enabled_platforms if platform in LANDSCAPE_SHORT_PLATFORMS]
        long_landscape = [platform for platform in enabled_platforms if platform in LONG_LANDSCAPE_PLATFORMS]
        if vertical:
            workflows.append(("vertical_short", vertical))
        if landscape_short:
            workflows.append(("landscape_short", landscape_short))
        if long_landscape:
            # YouTube and Rumble use independent editorial scripts rather
            # than a resized vertical post.
            for platform in long_landscape:
                workflows.append(("long", [platform]))
        if not workflows and self.config.get("require_review_before_publish", True):
            # A creator can make a local review copy before connecting any site.
            workflows.append((self.config.get("video_format", "short"), []))
        return workflows

    @staticmethod
    def _format_visual_credits(visual_plan: list[dict]) -> str:
        entries = []
        seen = set()
        for item in visual_plan:
            if item.get("type") != "licensed_stock_video":
                continue
            key = item.get("visual", "")
            if key in seen:
                continue
            seen.add(key)
            source = item.get("source", "")
            license_name = item.get("license", "")
            creator = item.get("creator", "")
            if source and license_name and not source.startswith("Missing"):
                credit = f"- {Path(key).name}"
                if creator:
                    credit += f" — {creator}"
                credit += f" | {license_name} | {source}"
                entries.append(credit)
        return "Visual credits\n" + "\n".join(entries) + "\n" if entries else ""

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
