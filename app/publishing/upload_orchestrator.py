"""Platform upload orchestrator — manages uploads to all supported platforms.

This is the main entry point for uploading videos. It handles:
- Platform selection and routing
- Rate limiting (via RateLimiter)
- Metadata optimization (via HashtagOptimizer)
- Retry logic and error handling
- Upload history tracking
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
from dataclasses import dataclass

from app.scheduler.rate_limiter import RateLimiter, PLATFORM_RULES
from app.publishing.hashtag_optimizer import HashtagOptimizer


@dataclass
class UploadResult:
    """Result of an upload attempt."""
    platform: str
    success: bool
    video_url: Optional[str] = None
    video_id: Optional[str] = None
    error: Optional[str] = None
    posted_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "success": self.success,
            "video_url": self.video_url,
            "video_id": self.video_id,
            "error": self.error,
            "posted_at": self.posted_at,
        }


class UploadOrchestrator:
    """
    Orchestrates video uploads across multiple platforms.

    Usage:
        orch = UploadOrchestrator()

        # Upload to all configured platforms
        results = orch.upload(
            video_path="projects/output/video.mp4",
            thumbnail_path="projects/output/thumb.jpg",
            title="The Haunted Lighthouse",
            description="A mysterious lighthouse...",
            niche="scary_stories",
            platforms=["youtube", "tiktok", "instagram"],
        )

        # Check rate limits before uploading
        can_upload, reason = orch.can_upload("youtube")
    """

    def __init__(self, settings=None):
        limit_overrides = settings.get("platform_limits", {}) if settings else {}
        self.rate_limiter = RateLimiter(limit_overrides=limit_overrides)
        self.affiliate_links = settings.get("affiliate_links", []) if settings else []
        self.hashtag_optimizer = HashtagOptimizer()
        self.history_dir = Path("projects/_upload_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Lazy-load platform uploaders
        self._uploaders = {}

    def can_upload(self, platform: str) -> tuple[bool, str]:
        """Check if we can upload to a platform (respects rate limits)."""
        return self.rate_limiter.can_post(platform)

    def upload(
        self,
        video_path: str,
        title: str,
        description: str,
        niche: str,
        platforms: list[str],
        thumbnail_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        schedule_time: Optional[str] = None,
        preformatted_metadata: bool = False,
        youtube_privacy: str = "unlisted",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> dict[str, UploadResult]:
        """
        Upload a video to multiple platforms.

        Returns dict of {platform: UploadResult}.
        """
        results = {}

        for platform in platforms:
            can, reason = self.can_upload(platform)
            if not can:
                results[platform] = UploadResult(
                    platform=platform,
                    success=False,
                    error=reason,
                )
                continue

            # A reviewed package is the publishing source of truth.  Rewriting
            # it here used to make the uploaded title/description differ from
            # the one the creator had approved.
            if preformatted_metadata:
                optimized = {
                    "title": self.hashtag_optimizer.strip_hashtags(title).strip(),
                    "description": description.strip(),
                    "hashtags": [str(tag).lstrip("#") for tag in (tags or [])],
                }
                if "Creator-tool disclosure:" not in optimized["description"]:
                    optimized["description"] = self._append_affiliate_links(
                        optimized["description"], platform, niche
                    )
            else:
                optimized = self.hashtag_optimizer.optimize(
                    platform=platform,
                    niche=niche,
                    title=title,
                    narration_excerpt=description,
                    extra_hashtags=tags,
                )
                optimized["description"] = self._append_affiliate_links(
                    optimized["description"], platform, niche
                )

            # Try upload
            try:
                uploader = self._get_uploader(platform)
                upload_kwargs = {
                    "video_path": video_path,
                    "title": optimized["title"],
                    "description": optimized["description"],
                    "tags": optimized["hashtags"],
                    # YouTube's custom-thumbnail endpoint is for standard
                    # videos. Shorts use a selected video frame instead, so
                    # never send thumbnail.jpg for a Shorts upload.
                    "thumbnail_path": None if platform == "youtube_shorts" else thumbnail_path,
                }
                # YouTube's official API does not use Studio's browser upload
                # defaults. Pass an explicit creator-safe visibility instead.
                if platform in {"youtube", "youtube_long", "youtube_shorts"}:
                    upload_kwargs["privacy"] = youtube_privacy
                    upload_kwargs["progress_callback"] = progress_callback
                result = uploader.upload(
                    **upload_kwargs,
                )

                if result.success:
                    self.rate_limiter.record_post(platform, title)

                results[platform] = result

            except Exception as e:
                results[platform] = UploadResult(
                    platform=platform,
                    success=False,
                    error=str(e),
                )

        # Save history
        self._save_history(results, title)
        return results

    def upload_single(
        self,
        platform: str,
        video_path: str,
        title: str,
        description: str,
        niche: str,
        thumbnail_path: Optional[str] = None,
        tags: Optional[list[str]] = None,
        preformatted_metadata: bool = False,
        youtube_privacy: str = "unlisted",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> UploadResult:
        """Upload to a single platform."""
        results = self.upload(
            video_path=video_path,
            title=title,
            description=description,
            niche=niche,
            platforms=[platform],
            thumbnail_path=thumbnail_path,
            tags=tags,
            preformatted_metadata=preformatted_metadata,
            youtube_privacy=youtube_privacy,
            progress_callback=progress_callback,
        )
        return results.get(platform, UploadResult(platform=platform, success=False, error="Unknown error"))

    def get_status(self) -> dict:
        """Get upload status for all platforms."""
        return self.rate_limiter.get_all_status()

    def get_history(self, platform: Optional[str] = None) -> list[dict]:
        """Get upload history, optionally filtered by platform."""
        history_file = self.history_dir / "upload_history.json"
        if not history_file.exists():
            return []

        with open(history_file, "r") as f:
            all_history = json.load(f)

        if platform:
            return [h for h in all_history if h.get("platform") == platform]
        return all_history

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_uploader(self, platform: str):
        """Lazy-load the appropriate platform uploader."""
        if platform not in self._uploaders:
            if platform in {"youtube", "youtube_long", "youtube_shorts"}:
                from app.publishing.youtube_uploader import YouTubeUploader
                self._uploaders[platform] = YouTubeUploader()
            elif platform == "tiktok":
                from app.publishing.tiktok_uploader import TikTokUploader
                self._uploaders[platform] = TikTokUploader()
            elif platform == "instagram":
                from app.publishing.instagram_uploader import InstagramUploader
                self._uploaders[platform] = InstagramUploader()
            elif platform == "x_twitter":
                from app.publishing.x_uploader import XUploader
                self._uploaders[platform] = XUploader()
            elif platform == "rumble":
                from app.publishing.rumble_uploader import RumbleUploader
                self._uploaders[platform] = RumbleUploader()
            elif platform == "facebook":
                raise ValueError(
                    "Facebook publishing is not implemented. Do not enable it until a dedicated Graph API publisher is added."
                )
            elif platform == "snapchat":
                # Snapchat has no public upload API — placeholder
                from app.publishing.upload_orchestrator import UploadResult
                class _SnapchatStub:
                    def upload(self, **kwargs):
                        return UploadResult(
                            platform="snapchat",
                            success=False,
                            error="Snapchat has no public upload API. Manual upload required."
                        )
                self._uploaders[platform] = _SnapchatStub()
            else:
                raise ValueError(f"Unsupported platform: {platform}")
        return self._uploaders[platform]

    def _append_affiliate_links(self, description: str, platform: str, niche: str = None) -> str:
        """Add only creator-marked, niche-relevant affiliate links with disclosure."""
        if platform not in {"youtube", "youtube_long", "youtube_shorts", "tiktok", "instagram", "facebook"}:
            return description
        links = [
            item for item in self.affiliate_links
            if item.get("referral_url", "").startswith(("https://", "http://"))
            # An empty niche list means the creator deliberately enabled this
            # resource for the channel as a whole.  A populated list remains
            # an explicit niche restriction.
            and (not item.get("niches") or niche in item.get("niches", []))
        ]
        if not links:
            return description
        lines = ["", "—" * 20, "Creator-tool disclosure: Some links below may be affiliate links. I may earn a commission at no extra cost to you."]
        lines.extend(f"{item.get('name', 'Recommended resource').replace('_', ' ').title()}: {item['referral_url']}" for item in links)
        return f"{description.rstrip()}\n" + "\n".join(lines)

    def _save_history(self, results: dict[str, UploadResult], title: str):
        """Save upload history."""
        history_file = self.history_dir / "upload_history.json"
        history = []
        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)

        for platform, result in results.items():
            history.append({
                "title": title,
                "platform": platform,
                "success": result.success,
                "video_url": result.video_url,
                "video_id": result.video_id,
                "error": result.error,
                "posted_at": result.posted_at or datetime.now().isoformat(),
            })

        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
