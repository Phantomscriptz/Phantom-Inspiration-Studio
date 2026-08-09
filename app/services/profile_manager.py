"""Local channel-profile management.

Profiles keep editorial settings and OAuth material isolated on the creator's
computer.  Only one profile is active in the app at once; this is not an
account-rotation or mass-publishing facility.
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path


class ProfileManager:
    CREDENTIAL_FILES = (
        "youtube_client_secret.json", "youtube_token.json",
        "tiktok_credentials.json", "tiktok_token.json",
        "instagram_credentials.json", "instagram_token.json",
        "x_credentials.json", "x_token.json", "rumble_credentials.json",
    )

    def __init__(self, settings_path: str = "config/settings.json", root: str = "profiles"):
        self.settings_path = Path(settings_path)
        self.root = Path(root)
        self.index_path = self.root / "index.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self._ensure_default_profile()

    def profiles(self) -> list[dict]:
        return self._read_index().get("profiles", [])

    def active_id(self) -> str:
        return self._read_index().get("active_id", "default")

    def active_profile(self) -> dict:
        return next((item for item in self.profiles() if item["id"] == self.active_id()), self.profiles()[0])

    def create(self, name: str) -> dict:
        display_name = name.strip() or "New channel"
        profile_id = self._unique_id(display_name)
        profile = {"id": profile_id, "name": display_name, "created_at": datetime.now().isoformat(timespec="seconds")}
        profile_dir = self._profile_dir(profile_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "credentials").mkdir(exist_ok=True)
        shutil.copy2(self.settings_path, profile_dir / "settings.json")
        index = self._read_index()
        index["profiles"].append(profile)
        self._write_index(index)
        return profile

    def activate(self, profile_id: str) -> dict:
        profile = next((item for item in self.profiles() if item["id"] == profile_id), None)
        if not profile:
            raise ValueError("That profile no longer exists.")
        current = self.active_profile()
        self._save_active(current["id"])
        self._clear_active_credentials()
        self._restore_profile(profile_id)
        index = self._read_index()
        index["active_id"] = profile_id
        self._write_index(index)
        return profile

    def _ensure_default_profile(self) -> None:
        if self.index_path.exists():
            return
        profile = {"id": "default", "name": "Default channel", "created_at": datetime.now().isoformat(timespec="seconds")}
        self._profile_dir("default").mkdir(parents=True, exist_ok=True)
        (self._profile_dir("default") / "credentials").mkdir(exist_ok=True)
        if self.settings_path.exists():
            self._save_active("default")
        self._write_index({"active_id": "default", "profiles": [profile]})

    def _save_active(self, profile_id: str) -> None:
        target = self._profile_dir(profile_id)
        target.mkdir(parents=True, exist_ok=True)
        (target / "credentials").mkdir(exist_ok=True)
        if self.settings_path.exists():
            shutil.copy2(self.settings_path, target / "settings.json")
        config_dir = self.settings_path.parent
        for filename in self.CREDENTIAL_FILES:
            source = config_dir / filename
            if source.exists():
                shutil.copy2(source, target / "credentials" / filename)

    def _restore_profile(self, profile_id: str) -> None:
        source_dir = self._profile_dir(profile_id)
        settings_file = source_dir / "settings.json"
        if settings_file.exists():
            shutil.copy2(settings_file, self.settings_path)
        credentials = source_dir / "credentials"
        for filename in self.CREDENTIAL_FILES:
            source = credentials / filename
            if source.exists():
                shutil.copy2(source, self.settings_path.parent / filename)

    def _clear_active_credentials(self) -> None:
        for filename in self.CREDENTIAL_FILES:
            (self.settings_path.parent / filename).unlink(missing_ok=True)

    def _profile_dir(self, profile_id: str) -> Path:
        return self.root / profile_id

    def _read_index(self) -> dict:
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"active_id": "default", "profiles": []}

    def _write_index(self, value: dict) -> None:
        self.index_path.write_text(json.dumps(value, indent=2), encoding="utf-8")

    def _unique_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "channel"
        return f"{slug}-{uuid.uuid4().hex[:8]}"
