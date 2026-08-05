"""Standalone WhisperX worker run by the dedicated Python 3.11 environment.

This module deliberately avoids importing the desktop app so the app can stay
on Python 3.14 while WhisperX uses its supported dependency stack.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Align narration with WhisperX")
    parser.add_argument("audio")
    parser.add_argument("output")
    parser.add_argument("--model", default="tiny")
    args = parser.parse_args()

    import whisperx

    device = "cuda"
    model = whisperx.load_model(args.model, device, compute_type="float16")
    audio = whisperx.load_audio(args.audio)
    result = model.transcribe(audio, batch_size=4, language="en")
    align_model, metadata = whisperx.load_align_model(language_code="en", device=device)
    aligned = whisperx.align(
        result["segments"], align_model, metadata, audio, device,
        return_char_alignments=False,
    )
    words = [word for segment in aligned.get("segments", []) for word in segment.get("words", [])
             if word.get("word") and word.get("start") is not None and word.get("end") is not None]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"language": result.get("language", "en"), "words": words}, indent=2), encoding="utf-8")
    print(f"Aligned {len(words)} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
