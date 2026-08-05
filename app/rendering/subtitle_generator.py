"""Subtitle generator — creates SRT files from script segments.

Supports auto-timing based on word count and optional word-level timestamps.
"""

from pathlib import Path
from typing import Optional


class SubtitleGenerator:
    """
    Generate SRT subtitle files from script narration.

    Usage:
        gen = SubtitleGenerator()
        srt_path = gen.generate_from_segments(segments, output="subtitles.srt")
    """

    def __init__(self, words_per_minute: int = 150):
        """
        Args:
            words_per_minute: Speaking speed for timing calculation.
                              Average is 130-170 WPM.
        """
        self.words_per_minute = words_per_minute

    def generate_from_segments(
        self,
        segments: list[dict],
        output: str = "subtitles.srt",
        start_offset: float = 0.0,
    ) -> str:
        """
        Generate SRT file from script segments.

        Args:
            segments: List of dicts with 'narration' and 'duration_seconds'.
            output: Output .srt file path.
            start_offset: Start time offset in seconds.

        Returns:
            Path to the generated SRT file.
        """
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        srt_entries = []
        current_time = start_offset

        for seg in segments:
            narration = seg.get("narration", "")
            duration = seg.get("duration_seconds", 5.0)

            if not narration.strip():
                continue

            # Split narration into subtitle chunks
            chunks = self._split_into_chunks(narration, max_chars=32)

            # Give longer phrases proportionally more screen time. Equal
            # timing made short words linger and long phrases fall behind.
            word_counts = [max(1, len(chunk.split())) for chunk in chunks]
            total_words = sum(word_counts)

            for chunk, word_count in zip(chunks, word_counts):
                start = current_time
                end = current_time + (duration * word_count / total_words)

                srt_entries.append(
                    self._format_srt_entry(
                        index=len(srt_entries) + 1,
                        start=start,
                        end=end,
                        text=chunk,
                    )
                )
                current_time = end

        # Write SRT file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(srt_entries))
            f.write("\n")

        return str(output_path)

    def generate_from_text(
        self,
        text: str,
        total_duration: float,
        output: str = "subtitles.srt",
    ) -> str:
        """
        Generate SRT from a single text block, split evenly by time.

        Useful for short-form content with one narration block.
        """
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Split text into sentences
        sentences = self._split_sentences(text)
        total_words = len(text.split())
        estimated_duration = (total_words / self.words_per_minute) * 60

        # Use provided duration or estimated
        duration = total_duration if total_duration > 0 else estimated_duration

        # Split into chunks for display
        chunks = self._split_into_chunks(text, max_chars=42)
        time_per_chunk = duration / max(len(chunks), 1)

        srt_entries = []
        current_time = 0.0

        for chunk in chunks:
            start = current_time
            end = current_time + time_per_chunk
            srt_entries.append(
                self._format_srt_entry(
                    index=len(srt_entries) + 1,
                    start=start,
                    end=end,
                    text=chunk,
                )
            )
            current_time = end

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(srt_entries))
            f.write("\n")

        return str(output_path)

    def generate_from_word_timestamps(
        self,
        words: list[dict],
        output: str = "subtitles.srt",
        max_words: int = 5,
        max_duration: float = 2.8,
        pause_break: float = 0.55,
    ) -> str:
        """Generate compact captions using real ASR word timestamps."""
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        entries, chunk = [], []

        def flush():
            if not chunk:
                return
            entries.append(self._format_srt_entry(
                len(entries) + 1, float(chunk[0]["start"]), float(chunk[-1]["end"]),
                " ".join(str(item["word"]).strip() for item in chunk),
            ))
            chunk.clear()

        for word in words:
            if not str(word.get("word", "")).strip():
                continue
            if chunk:
                elapsed = float(word["end"]) - float(chunk[0]["start"])
                pause = float(word["start"]) - float(chunk[-1]["end"])
                if len(chunk) >= max_words or elapsed >= max_duration or pause >= pause_break:
                    flush()
            chunk.append(word)
            if str(word["word"]).rstrip().endswith((".", "!", "?")) and len(chunk) >= 2:
                flush()
        flush()
        output_path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")
        return str(output_path)

    def _split_into_chunks(
        self, text: str, max_chars: int = 42
    ) -> list[str]:
        """Split text into display-friendly chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0

        for word in words:
            if current_len + len(word) + 1 > max_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_len = len(word)
            else:
                current_chunk.append(word)
                current_len += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _format_srt_entry(index: int, start: float, end: float, text: str) -> str:
        """Format a single SRT entry."""
        return (
            f"{index}\n"
            f"{_format_time(start)} --> {_format_time(end)}\n"
            f"{text}"
        )


def _format_time(seconds: float) -> str:
    """Format seconds to SRT timestamp (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_from_script(script_data: dict, output: str = "subtitles.srt") -> str:
    """Convenience function to generate SRT from a VideoScript dict."""
    gen = SubtitleGenerator()
    segments = script_data.get("segments", [])
    return gen.generate_from_segments(segments, output)
