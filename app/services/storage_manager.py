"""Safe accounting and cleanup for disposable generated media."""

from __future__ import annotations

import shutil
from pathlib import Path


class StorageManager:
    GENERATED_DIRECTORIES = (
        Path("projects/_output"), Path("projects/_audio"), Path("projects/_images"),
        Path("projects/_upload_history"), Path("projects/_rate_limits"),
        Path("projects/_content_history"), Path("projects/_test_output"),
        Path("projects/_test_quality"), Path("cache"), Path("exports"),
    )
    PRESERVED_DIRECTORIES = (
        Path("assets/stock_videos"), Path("assets/voice_samples"), Path("models"), Path("config"),
    )

    def summary(self) -> dict:
        generated = sum(self._directory_size(path) for path in self.GENERATED_DIRECTORIES)
        preserved = sum(self._directory_size(path) for path in self.PRESERVED_DIRECTORIES)
        return {"generated_bytes": generated, "preserved_bytes": preserved}

    def clear_generated_media(self) -> list[str]:
        """Delete only reproducible generated artifacts, never credentials/models/B-roll."""
        removed = []
        for path in self.GENERATED_DIRECTORIES:
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed.append(str(path))
        return removed

    @staticmethod
    def _directory_size(path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())

    @staticmethod
    def format_size(value: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{value} B"
            value /= 1024
