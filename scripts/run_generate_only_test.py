"""Run one safe end-to-end Phantom generation without opening the UI.

This is a development verification tool.  It deliberately persists a
YouTube-Shorts-only, generate-only configuration and never uploads anything.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys


# When this file is launched directly, Python places ``scripts`` rather than
# the repository root on sys.path.  Make the development harness independent
# of the caller's current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows background processes can inherit a cp1252 console.  Pipeline logs
# contain status symbols, so write UTF-8 rather than allowing logging itself
# to raise an exception during a render.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config.settings import SettingsManager
from app.workers.automation_worker import AutomationWorker


def main() -> int:
    settings = SettingsManager()
    limits = settings.get("platform_limits", {})
    for platform, values in limits.items():
        values["enabled"] = platform == "youtube_shorts"
    settings.set("platform_limits", limits)
    settings.set("require_review_before_publish", True)
    settings.set("max_videos_per_run", 1)

    config = settings.to_worker_config()
    log_path = Path("logs") / f"generate_only_test_{datetime.now():%Y%m%d_%H%M%S}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def write(message: str) -> None:
        line = f"[{datetime.now():%H:%M:%S}] {message}"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    worker = AutomationWorker(config)
    worker.log_message.connect(write)
    worker.error_occurred.connect(lambda message: write(f"ERROR: {message}"))
    worker.video_generated.connect(lambda path: write(f"VIDEO: {path}"))
    worker.pipeline_complete.connect(lambda count: write(f"COMPLETE: {count} video(s)"))

    write("Starting safe automated test: YouTube Shorts enabled; uploads disabled.")
    worker.run()
    write(f"Log saved: {log_path}")
    return 0 if worker._videos_produced == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
