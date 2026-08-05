"""Safe bridge to the project's isolated WhisperX runtime."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


class WhisperXAligner:
    """Return word-level narration timings without coupling the desktop app to PyTorch."""

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path(__file__).resolve().parents[2])
        self.python = self.project_root / ".venv-whisperx" / "Scripts" / "python.exe"
        self.runner = Path(__file__).with_name("whisperx_runner.py")

    def is_available(self) -> bool:
        return self.python.is_file() and self.runner.is_file()

    def align(self, audio_path: str | Path, output_json: str | Path, timeout: int = 180) -> list[dict]:
        if not self.is_available():
            raise RuntimeError("WhisperX is not installed. Use the standard caption-timing fallback.")
        result = subprocess.run(
            [str(self.python), str(self.runner), str(Path(audio_path).resolve()), str(Path(output_json).resolve())],
            cwd=str(self.project_root), capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()[-1:]
            raise RuntimeError("WhisperX alignment failed" + (f": {detail[0]}" if detail else ""))
        try:
            return json.loads(Path(output_json).read_text(encoding="utf-8")).get("words", [])
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"WhisperX did not produce readable timings: {exc}") from exc
