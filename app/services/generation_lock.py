"""Cross-process guard for the local generation pipeline.

Ollama can only serve so much local GPU/CPU work at once.  Two copies of the
desktop app otherwise look frozen while one request queues behind the other.
This lock makes that state explicit and cleans up stale locks after a crash.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


class GenerationLock:
    def __init__(self, path: str = "projects/_runtime/generation.lock"):
        self.path = Path(path)
        self.held = False

    def acquire(self) -> tuple[bool, str]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and not self._owner_is_running():
            self.path.unlink(missing_ok=True)
        try:
            with self.path.open("x", encoding="utf-8") as handle:
                json.dump({"pid": os.getpid(), "started_at": datetime.now().isoformat()}, handle)
            self.held = True
            return True, ""
        except FileExistsError:
            return False, "Another Phantom generation is already using the local AI model. Wait for it to finish, then run one test at a time."

    def release(self) -> None:
        if self.held:
            self.path.unlink(missing_ok=True)
            self.held = False

    def _owner_is_running(self) -> bool:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            pid = int(payload.get("pid", 0))
            if pid <= 0:
                return False
            os.kill(pid, 0)
            return True
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False
