"""Video builder — assembles images + audio + subtitles into final video.

Uses FFmpeg under the hood via subprocess for maximum reliability.
No MoviePy dependency needed for the core pipeline.
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class VideoConfig:
    """Configuration for video rendering."""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    format: str = "mp4"
    codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 23              # Quality (lower = better, 18-28 typical)
    preset: str = "medium"     # ultrafast, fast, medium, slow
    pixel_format: str = "yuv420p"

    # Ken Burns effect
    ken_burns: bool = True
    ken_burns_zoom: float = 1.08   # 8% zoom
    ken_burns_duration: float = 0.5  # seconds for zoom transition

    # Transitions
    transition_duration: float = 0.3

    # Subtitles
    show_subtitles: bool = True
    subtitle_font: str = "Arial"
    subtitle_size: int = 48
    subtitle_color: str = "&HFFFFFF"  # White (ASS format)
    subtitle_outline: int = 3
    subtitle_position: str = "bottom"  # bottom, center, top

    # Background
    bg_color: str = "black"

    @classmethod
    def for_short(cls) -> "VideoConfig":
        """Config optimized for short-form (9:16 vertical)."""
        # FFmpeg/libass scales SRT style values from its subtitle canvas on
        # some Windows builds.  These compact values render as readable
        # mobile captions instead of covering the visual.
        return cls(width=1080, height=1920, fps=30, subtitle_size=11, subtitle_outline=1)

    @classmethod
    def for_long(cls) -> "VideoConfig":
        """Config optimized for long-form (16:9 horizontal)."""
        return cls(width=1920, height=1080, fps=30)

    @classmethod
    def for_tiktok(cls) -> "VideoConfig":
        return cls(width=1080, height=1920, fps=30)

    @classmethod
    def for_youtube_short(cls) -> "VideoConfig":
        return cls(width=1080, height=1920, fps=30)

    @classmethod
    def for_youtube_long(cls) -> "VideoConfig":
        return cls(width=1920, height=1080, fps=30)


class VideoBuilder:
    """
    Builds video from images + audio using FFmpeg.

    Pipeline:
    1. Resize/crop images to target resolution
    2. Apply Ken Burns (zoom pan) effect to each image
    3. Concatenate image clips with transitions
    4. Mix in voiceover audio
    5. Burn subtitles (optional)
    6. Export final video

    Usage:
        builder = VideoBuilder()
        video_path = builder.build(
            images=["scene1.jpg", "scene2.jpg"],
            audio="voiceover.mp3",
            output="final_video.mp4",
        )
    """

    def __init__(self, config: VideoConfig = None):
        self.config = config or VideoConfig()
        self._verify_ffmpeg()

    def _verify_ffmpeg(self):
        """Ensure FFmpeg is available."""
        if not shutil.which("ffmpeg"):
            raise EnvironmentError(
                "FFmpeg not found. Install it:\n"
                "  Windows: winget install ffmpeg\n"
                "  Or download from https://ffmpeg.org/download.html"
            )

    def build(
        self,
        images: list[str],
        audio: Optional[str] = None,
        output: str = "output.mp4",
        subtitles_file: Optional[str] = None,
        durations: Optional[list[float]] = None,
        background_music: Optional[str] = None,
        music_volume: float = 0.15,
    ) -> str:
        """
        Build a complete video from images and audio.

        Args:
            images: List of image file paths.
            audio: Voiceover audio file path.
            output: Output video file path.
            subtitles_file: Optional .srt subtitle file.
            durations: Duration (seconds) per image. If None, auto-calculated.
            background_music: Optional background music file.
            music_volume: Volume for background music (0.0-1.0).

        Returns:
            Path to the rendered video.
        """
        if not images:
            raise ValueError("At least one image is required.")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: Prepare images (resize to target resolution)
        prepared_images = self._prepare_images(images)

        # Step 2: Calculate durations
        if durations is None:
            if audio:
                total_duration = self._get_audio_duration(audio)
                durations = self._distribute_durations(total_duration, len(images))
            else:
                durations = [5.0] * len(images)

        # Step 3: Build individual image clips with Ken Burns
        clip_files = []
        for i, (img, dur) in enumerate(zip(prepared_images, durations)):
            clip_path = str(output_path.parent / f"_clip_{i:03d}.mp4")
            self._make_image_clip(img, dur, clip_path)
            clip_files.append(clip_path)

        # Step 4: Concatenate clips
        concat_path = str(output_path.parent / "_concat.mp4")
        self._concat_clips(clip_files, concat_path)

        # Step 5: Add audio
        if audio:
            with_audio = str(output_path.parent / "_with_audio.mp4")
            self._add_audio(concat_path, audio, with_audio)
            current_video = with_audio
        else:
            current_video = concat_path

        # Step 6: Add background music
        if background_music:
            with_music = str(output_path.parent / "_with_music.mp4")
            self._mix_background_music(current_video, background_music, with_music, music_volume)
            current_video = with_music

        # Step 7: Burn subtitles
        if subtitles_file and self.config.show_subtitles:
            with_subs = str(output_path.parent / "_with_subs.mp4")
            self._burn_subtitles(current_video, subtitles_file, with_subs)
            current_video = with_subs

        # Step 8: Final encode
        if current_video != str(output_path):
            shutil.move(current_video, str(output_path))

        # Cleanup temp files
        self._cleanup(output_path.parent, clip_files, concat_path)

        return str(output_path)

    def build_from_segments(
        self,
        image_paths: list[str],
        audio_paths: list[str],
        output: str = "output.mp4",
        subtitles_file: Optional[str] = None,
    ) -> str:
        """
        Build video from individual segment images + audio files.
        Each segment has its own image and audio that play simultaneously.
        """
        if not image_paths:
            raise ValueError("At least one image is required.")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare images
        prepared = self._prepare_images(image_paths)

        # Get duration of each audio file
        durations = []
        for ap in audio_paths:
            durations.append(self._get_audio_duration(ap))

        # For single-segment or mismatched counts, fall back to basic build
        if len(audio_paths) == 1 and len(image_paths) > 1:
            return self.build(
                images=image_paths,
                audio=audio_paths[0],
                output=output,
                subtitles_file=subtitles_file,
                durations=durations * len(image_paths) if durations else None,
            )

        # Multi-segment: create clips with individual audio
        clip_files = []
        for i, (img, dur) in enumerate(zip(prepared, durations)):
            clip_path = str(output_path.parent / f"_clip_{i:03d}.mp4")

            audio_file = audio_paths[i] if i < len(audio_paths) else None
            self._make_image_clip(img, dur, clip_path, audio_file)
            clip_files.append(clip_path)

        # Concatenate
        concat_path = str(output_path.parent / "_concat.mp4")
        self._concat_clips(clip_files, concat_path)

        # Move to final output
        shutil.move(concat_path, str(output_path))

        # Cleanup
        self._cleanup(output_path.parent, clip_files)

        return str(output_path)

    def build_from_visual_segments(
        self,
        visual_paths: list[str],
        segment_audio_paths: list[str],
        audio: str,
        output: str,
        subtitles_file: Optional[str] = None,
    ) -> str:
        """Render a mix of stills and licensed motion clips per script segment."""
        if not visual_paths or not segment_audio_paths:
            raise ValueError("Visuals and segment audio are required for cinematic rendering.")
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        durations = [self._get_audio_duration(path) for path in segment_audio_paths]
        clip_files = []
        for index, (visual, duration) in enumerate(zip(visual_paths, durations)):
            clip_path = str(output_path.parent / f"_clip_{index:03d}.mp4")
            # Give every non-final scene enough tail to overlap the next one
            # without shortening the final narration-led runtime.
            clip_duration = duration + (self.config.transition_duration if index < len(durations) - 1 else 0)
            if self._is_video_file(visual):
                self._make_video_clip(visual, clip_duration, clip_path)
            else:
                self._make_image_clip(visual, clip_duration, clip_path)
            clip_files.append(clip_path)

        concat_path = str(output_path.parent / "_concat.mp4")
        self._crossfade_clips(clip_files, durations, concat_path)
        with_audio = str(output_path.parent / "_with_audio.mp4")
        self._add_audio(concat_path, audio, with_audio)
        current_video = with_audio
        if subtitles_file and self.config.show_subtitles:
            with_subtitles = str(output_path.parent / "_with_subs.mp4")
            self._burn_subtitles(current_video, subtitles_file, with_subtitles)
            current_video = with_subtitles
        shutil.move(current_video, str(output_path))
        self._cleanup(output_path.parent, clip_files, concat_path)
        return str(output_path)

    def build_looping_broll(
        self,
        broll_path: str,
        audio: str,
        output: str,
        subtitles_file: Optional[str] = None,
    ) -> str:
        """Loop one creator-selected motion clip for the complete narration."""
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        duration = self._get_audio_duration(audio)
        visual_only = str(output_path.parent / "_looping_broll.mp4")
        self._make_video_clip(broll_path, duration, visual_only)
        with_audio = str(output_path.parent / "_with_audio.mp4")
        self._add_audio(visual_only, audio, with_audio)
        current_video = with_audio
        if subtitles_file and self.config.show_subtitles:
            with_subtitles = str(output_path.parent / "_with_subs.mp4")
            self._burn_subtitles(current_video, subtitles_file, with_subtitles)
            current_video = with_subtitles
        shutil.move(current_video, str(output_path))
        self._cleanup(output_path.parent, [visual_only])
        return str(output_path)

    # ------------------------------------------------------------------
    # Internal FFmpeg operations
    # ------------------------------------------------------------------

    def _prepare_images(self, images: list[str]) -> list[str]:
        """Resize and crop images to target resolution."""
        prepared = []
        cfg = self.config

        for i, img_path in enumerate(images):
            out_path = str(Path(img_path).parent / f"_prepared_{i:03d}.jpg")

            cmd = [
                "ffmpeg", "-y", "-i", img_path,
                "-vf", (
                    f"scale={cfg.width}:{cfg.height}:force_original_aspect_ratio=increase,"
                    f"crop={cfg.width}:{cfg.height}"
                ),
                "-q:v", "2",
                out_path,
            ]
            self._run_ffmpeg(cmd)
            prepared.append(out_path)

        return prepared

    def _make_image_clip(
        self,
        image_path: str,
        duration: float,
        output_path: str,
        audio_path: str = None,
    ):
        """Create a video clip from a single image with optional Ken Burns."""
        cfg = self.config
        fps = cfg.fps

        if cfg.ken_burns:
            # Ken Burns: slow zoom in
            zoom_rate = cfg.ken_burns_zoom ** (1 / (duration * fps))
            vf = (
                f"scale={cfg.width * 2}:{cfg.height * 2},"
                f"zoompan=z='min({zoom_rate}\\,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={int(duration * fps)}:s={cfg.width}x{cfg.height}:fps={fps}"
            )
        else:
            vf = f"scale={cfg.width}:{cfg.height},fps={fps}"

        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", image_path, "-t", str(duration)]

        if audio_path:
            cmd.extend(["-i", audio_path])

        cmd.extend([
            "-vf", vf,
            "-c:v", cfg.codec,
            "-pix_fmt", cfg.pixel_format,
            "-crf", str(cfg.crf),
            "-preset", cfg.preset,
        ])

        if audio_path:
            cmd.extend(["-c:a", cfg.audio_codec, "-shortest"])
        else:
            cmd.extend(["-an"])

        cmd.append(output_path)
        self._run_ffmpeg(cmd)

    def _make_video_clip(self, video_path: str, duration: float, output_path: str):
        """Trim/loop a source clip and crop it safely to the target frame."""
        cfg = self.config
        vf = (
            f"scale={cfg.width}:{cfg.height}:force_original_aspect_ratio=increase,"
            f"crop={cfg.width}:{cfg.height},fps={cfg.fps}"
        )
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", video_path,
            "-t", str(duration), "-an", "-vf", vf,
            "-c:v", cfg.codec, "-pix_fmt", cfg.pixel_format,
            "-crf", str(cfg.crf), "-preset", cfg.preset, output_path,
        ]
        self._run_ffmpeg(cmd)

    @staticmethod
    def _is_video_file(path: str) -> bool:
        return Path(path).suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi"}

    def _concat_clips(self, clip_files: list[str], output_path: str):
        """Concatenate multiple video clips."""
        # Create concat list file
        list_path = str(Path(output_path).resolve()) + ".txt"
        with open(list_path, "w") as f:
            for clip in clip_files:
                # FFmpeg interprets relative file entries relative to the list
                # file.  The output directory was therefore duplicated on
                # Windows (``output/output/_clip``). Use forward-slashed
                # absolute paths so every generated clip is found reliably.
                absolute_clip = Path(clip).resolve().as_posix()
                f.write(f"file '{absolute_clip}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            output_path,
        ]
        self._run_ffmpeg(cmd)

        # Remove list file
        Path(list_path).unlink(missing_ok=True)

    def _crossfade_clips(self, clip_files: list[str], scene_durations: list[float], output_path: str):
        """Blend adjacent visual scenes without changing narration duration."""
        if len(clip_files) < 2 or self.config.transition_duration <= 0:
            self._concat_clips(clip_files, output_path)
            return

        transition = min(float(self.config.transition_duration), 0.75)
        inputs: list[str] = []
        for clip in clip_files:
            inputs.extend(["-i", clip])

        # Each non-final input has a small extra tail.  Start the fade after
        # its real narration duration, so the final visual timeline remains
        # exactly the same length as the complete voiceover.
        filters: list[str] = []
        previous = "[0:v]"
        elapsed = float(scene_durations[0])
        for index in range(1, len(clip_files)):
            output_label = f"[v{index}]"
            filters.append(
                f"{previous}[{index}:v]xfade=transition=fade:duration={transition:.3f}:"
                f"offset={elapsed:.3f}{output_label}"
            )
            previous = output_label
            elapsed += float(scene_durations[index])

        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", ";".join(filters),
            "-map", previous,
            "-c:v", self.config.codec,
            "-pix_fmt", self.config.pixel_format,
            "-crf", str(self.config.crf),
            "-preset", self.config.preset,
            output_path,
        ]
        self._run_ffmpeg(cmd)

    def _add_audio(self, video_path: str, audio_path: str, output_path: str):
        """Add voiceover audio to video."""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", self.config.audio_codec,
            "-shortest",
            output_path,
        ]
        self._run_ffmpeg(cmd)

    def _mix_background_music(
        self, video_path: str, music_path: str, output_path: str, volume: float
    ):
        """Mix background music with existing audio."""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex",
            f"[1:a]volume={volume},aloop=loop=-1:size=2e+09[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", self.config.audio_codec,
            output_path,
        ]
        self._run_ffmpeg(cmd)

    def _burn_subtitles(self, video_path: str, sub_path: str, output_path: str):
        """Burn SRT subtitles into video."""
        cfg = self.config
        # FFmpeg filter arguments use ':' as a separator. Escape the Windows
        # drive colon and use forward slashes so it can open the SRT reliably.
        subtitle_path = Path(sub_path).resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
        style = (
            f"FontName={cfg.subtitle_font},"
            f"FontSize={cfg.subtitle_size},"
            f"PrimaryColour={cfg.subtitle_color},"
            f"Outline={cfg.subtitle_outline},"
            "Alignment=2,MarginV=30"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            # SRT has no native play resolution. Without original_size,
            # libass scales FontSize from a legacy 288px canvas and makes
            # otherwise modest mobile captions fill the entire screen.
            "-vf", (
                f"subtitles='{subtitle_path}':original_size={cfg.width}x{cfg.height}:"
                f"force_style='{style}'"
            ),
            "-c:v", cfg.codec,
            "-crf", str(cfg.crf),
            output_path,
        ]
        self._run_ffmpeg(cmd)

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of an audio file in seconds."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())

    def _distribute_durations(self, total: float, count: int) -> list[float]:
        """Distribute total duration evenly across images."""
        per_image = total / count
        return [per_image] * count

    def _run_ffmpeg(self, cmd: list[str]):
        """Run an FFmpeg command."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg error:\n{result.stderr[-500:]}"
            )

    def _cleanup(self, tmp_dir: Path, clip_files: list[str], concat: str = None):
        """Remove temporary files."""
        for f in clip_files:
            Path(f).unlink(missing_ok=True)
        if concat:
            Path(concat).unlink(missing_ok=True)
        # Clean prepared images
        for f in tmp_dir.glob("_prepared_*"):
            f.unlink(missing_ok=True)
        for f in tmp_dir.glob("_with_*"):
            f.unlink(missing_ok=True)
        for f in tmp_dir.glob("_clip_*"):
            f.unlink(missing_ok=True)
