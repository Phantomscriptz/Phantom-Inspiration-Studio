from pathlib import Path
import json
import os
from typing import Optional


class SettingsManager:
    """Central settings manager for the entire application."""

    def __init__(self):
        self.settings_path = Path("config/settings.json")
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        self.defaults = {
            # General
            "theme": "dark",
            "projects_folder": "projects",
            "exports_folder": "exports",

            # Content
            "niche": "did_you_know",
            "topic": "",
            "video_format": "short",          # short or long
            "short_duration": 60,             # seconds
            "long_duration": 10,              # minutes
            "youtube_shorts_niche": "motivational",
            "selected_niches": ["did_you_know"],
            "randomize_niches": False,
            "selected_subniches": {},
            "language": "en",

            # Video quality
            "resolution": "1920x1080",
            "fps": 30,
            "video_codec": "libx264",
            "crf": 23,

            # AI
            "ollama_model": "qwen2.5:7b",
            "ollama_url": "http://localhost:11434",
            "script_temperature": 0.85,

            # Voice
            "voice_selected": "random",       # "random" or a voice_id like "en-US-GuyNeural"

            # Image
            "image_provider": "pollinations", # pollinations, pexels, local_sd
            "pexels_api_key": "",
            "local_sd_url": "http://127.0.0.1:7860",
            "cinematic_broll": True,
            "broll_selected_clip": "",

            # Automation
            "max_videos_per_run": 1,          # one reviewable production at a time
            "gap_between_videos_min": 43200,  # editorial scheduling, not activity simulation
            "gap_between_videos_max": 43200,
            "auto_start": False,

            # Platform daily limits (overrides rate_limiter defaults)
            "platform_limits": {
                "youtube_long": {"enabled": False, "max_per_day": 1},
                "youtube_shorts": {"enabled": False, "max_per_day": 1},
                "tiktok": {"enabled": False, "max_per_day": 1},
                "instagram": {"enabled": False, "max_per_day": 1},
                "x_twitter": {"enabled": False, "max_per_day": 1},
                "rumble": {"enabled": False, "max_per_day": 1},
                "facebook": {"enabled": False, "max_per_day": 1},
                "snapchat": {"enabled": False, "max_per_day": 1},
            },

            # Affiliate / Referral links
            "affiliates": {
                "elevenlabs": {
                    "enabled": False,
                    "referral_url": "",
                    "description": "AI voice generation. 22% commission for 12 months.",
                },
                "runwayml": {
                    "enabled": False,
                    "referral_url": "",
                    "description": "AI video generation tools.",
                },
                "midjourney": {
                    "enabled": False,
                    "referral_url": "",
                    "description": "AI image generation.",
                },
                "propellerads": {
                    "enabled": False,
                    "referral_url": "",
                    "description": "Ad network for popunder/interstitial revenue.",
                },
            },

            # Publishing controls
            "require_review_before_publish": True,
            "require_source_review": True,
            "content_similarity_threshold": 0.72,
        }

        self.settings = {}
        self.load()

    def load(self):
        if not self.settings_path.exists():
            self.settings = self.defaults.copy()
            self.save()
            return

        with open(self.settings_path, "r") as f:
            loaded = json.load(f)

        # Migrate the former single YouTube destination into long-form. Shorts
        # require an explicit opt-in because they are a separate workflow.
        limits = loaded.get("platform_limits", {})
        legacy_youtube = limits.pop("youtube", None)
        if legacy_youtube and "youtube_long" not in limits:
            limits["youtube_long"] = legacy_youtube

        # Merge with defaults so new keys are always present
        self.settings = self.defaults.copy()
        self._deep_merge(self.settings, loaded)

    def save(self):
        with open(self.settings_path, "w") as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, default=None):
        """Get a setting by dot-notation key, e.g. 'platform_limits.youtube.enabled'."""
        keys = key.split(".")
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key, value):
        """Set a setting by dot-notation key."""
        keys = key.split(".")
        target = self.settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save()

    def get_enabled_platforms(self) -> list[str]:
        """Return list of platforms that are enabled."""
        limits = self.get("platform_limits", {})
        return [p for p, cfg in limits.items() if cfg.get("enabled", False)]

    def get_platform_limit(self, platform: str, key: str, default=None):
        """Get a specific limit for a platform."""
        return self.get(f"platform_limits.{platform}.{key}", default)

    def get_affiliate_links(self) -> list[dict]:
        """Return list of enabled affiliate links."""
        affiliates = self.get("affiliates", {})
        return [
            {"name": name, **cfg}
            for name, cfg in affiliates.items()
            if cfg.get("enabled", False)
        ]

    def to_worker_config(self) -> dict:
        """Convert settings to a config dict for AutomationWorker."""
        return {
            "niche": self.get("niche"),
            "selected_niches": self.get("selected_niches", ["did_you_know"]),
            "randomize_niches": self.get("randomize_niches", False),
            "selected_subniches": self.get("selected_subniches", {}),
            "topic": self.get("topic"),
            "video_format": self.get("video_format", "short"),
            "short_duration": self.get("short_duration"),
            "long_duration": self.get("long_duration"),
            "ollama_model": self.get("ollama_model"),
            "voice_selected": self.get("voice_selected", "random"),
            "cinematic_broll": self.get("cinematic_broll", True),
            "broll_selected_clip": self.get("broll_selected_clip", ""),
            "youtube_shorts_niche": self.get("youtube_shorts_niche", "motivational"),
            "require_review_before_publish": self.get("require_review_before_publish", True),
            "max_videos_per_run": self.get("max_videos_per_run"),
            "gap_between_videos_min": self.get("gap_between_videos_min"),
            "gap_between_videos_max": self.get("gap_between_videos_max"),
            "enabled_platforms": self.get_enabled_platforms(),
            "platform_limits": self.get("platform_limits", {}),
            "affiliate_links": self.get_affiliate_links(),
        }

    def reset_user_preferences(self):
        """Reset safe, user-editable choices without touching credentials or affiliates."""
        keys = {
            "niche", "topic", "video_format", "short_duration", "long_duration",
            "youtube_shorts_niche", "language", "resolution", "fps", "video_codec",
            "crf", "ollama_model", "script_temperature", "voice_selected", "cinematic_broll",
            "image_provider", "local_sd_url", "max_videos_per_run",
            "gap_between_videos_min", "gap_between_videos_max", "auto_start",
            "require_review_before_publish",
        }
        for key in keys:
            self.settings[key] = self.defaults[key]
        self.settings.pop("selected_niches", None)
        self.settings.pop("randomize_niches", None)
        self.settings.pop("selected_subniches", None)
        self.save()

    def clear_temporary_runtime_state(self):
        """Clear only known temporary state files; never delete user content."""
        for filename in ("automation_state.json", "pending_jobs.json", "last_run.json"):
            path = Path("cache") / filename
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        """Recursively merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                SettingsManager._deep_merge(base[key], value)
            else:
                base[key] = value
