"""Checks that are safe to run before generating a video."""

import importlib.util
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.ai.providers.ollama_client import get_client


@dataclass
class PreflightResult:
    label: str
    ok: bool
    required: bool
    detail: str


def run_preflight(config: dict) -> list[PreflightResult]:
    results: list[PreflightResult] = []
    model = config.get("ollama_model", "qwen2.5:7b")
    try:
        client = get_client()
        model_ok = client.is_alive() and client.model_exists(model)
        detail = f"{model} is ready" if model_ok else f"{model} is not installed or Ollama is not running"
    except Exception:
        model_ok, detail = False, "Ollama could not be contacted"
    results.append(PreflightResult("Local script model", model_ok, True, detail))

    ffmpeg_ok = bool(shutil.which("ffmpeg"))
    results.append(PreflightResult("FFmpeg video renderer", ffmpeg_ok, True,
                                   "Found on PATH" if ffmpeg_ok else "Install FFmpeg before generating video"))

    tts_ok = importlib.util.find_spec("edge_tts") is not None
    results.append(PreflightResult("Voice engine", tts_ok, True,
                                   "Edge TTS package is available" if tts_ok else "edge-tts is missing"))

    enabled = config.get("enabled_platforms", [])
    review_only = config.get("require_review_before_publish", True)
    if not enabled:
        results.append(PreflightResult("Publishing destinations", True, False,
                                       "None selected — this run will only generate files"))
    elif review_only:
        results.append(PreflightResult("Publishing safety", True, False,
                                       "Generate-only mode is on; no uploads will occur"))
    else:
        token_map = {
            "youtube_long": "config/youtube_token.json", "youtube_shorts": "config/youtube_token.json",
            "tiktok": "config/tiktok_token.json", "instagram": "config/instagram_token.json",
        }
        missing = [name for name in enabled if name in token_map and not Path(token_map[name]).exists()]
        results.append(PreflightResult("Publishing connections", not missing, True,
                                       "Missing authorization: " + ", ".join(missing) if missing else "Local authorization found"))
    return results
