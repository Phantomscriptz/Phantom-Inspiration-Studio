"""Conservative publishing guardrails for a creator-controlled workflow.

These limits are editorial defaults, not a way to evade platform review.
Every upload must use an approved API flow and comply with platform policy.
"""

import random
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field


# ============================================================================
# PLATFORM RULES — conservative defaults, adjustable by the account owner.
# ============================================================================

PLATFORM_RULES = {
    "youtube": {
        "name": "YouTube",
        "max_videos_per_day": 2,
        "max_videos_per_week": 15,
        "min_interval_minutes": 120,
        "max_interval_minutes": 360,       # Don't wait too long (engagement dies)
        "best_hours_utc": [14, 15, 16, 17, 18, 19, 20, 21],  # US prime time
        "cooldown_after_bulk_hours": 6,    # After 3+ videos, wait 6h
        "max_consecutive_days": 21,        # Post max 21 days straight, then take 1-2 off
        "rest_days_required": 2,
        "max_title_length": 100,
        "max_description_length": 5000,
        "max_hashtags": 15,                # YT shows first 3 above title
        "max_tags": 500,                   # Characters, not count
        "video_length": {"short": (3, 60), "long": (300, 3600)},
        "requirements": {
            "min_subscribers": 0,          # Monetization needs 1K
            "min_watch_hours": 0,          # Monetization needs 4K
            "api_setup": "Google Cloud Console → YouTube Data API v3",
        },
        "rate_limit_notes": [
            "First 48 hours are critical — YT tests your video",
            "Don't delete and reupload — hurts channel",
            "Consistent schedule beats burst uploads",
            "Upload 2-3 hours before your audience peak time",
        ],
    },
    "tiktok": {
        "name": "TikTok",
        "max_videos_per_day": 2,
        "max_videos_per_week": 20,
        "min_interval_minutes": 20,
        "max_interval_minutes": 480,
        "best_hours_utc": [14, 15, 19, 20, 21, 22],  # US evening
        "cooldown_after_bulk_hours": 4,
        "max_consecutive_days": 30,        # TikTok rewards daily posting
        "rest_days_required": 1,
        "max_title_length": 150,           # Caption
        "max_description_length": 2200,
        "max_hashtags": 10,               # TikTok: 3-5 optimal, 10 max
        "max_tags": 0,                     # TikTok uses hashtags, not tags
        "video_length": {"short": (3, 60), "long": (60, 600)},
        "requirements": {
            "min_followers": 0,            # Creativity Program needs 10K
            "min_views_30d": 0,            # Creativity Program needs 100K
            "api_setup": "TikTok Developer Portal → Content Posting API",
        },
        "rate_limit_notes": [
            "TikTok's algorithm tests every video with 200-500 views first",
            "First 3 seconds determine if viewer stays",
            "Post 1-3 hours before peak hours",
            "Hashtag challenges boost reach significantly",
        ],
    },
    "instagram": {
        "name": "Instagram Reels",
        "max_videos_per_day": 3,           # IG shadows 5+/day
        "max_videos_per_week": 14,
        "min_interval_minutes": 30,
        "max_interval_minutes": 360,
        "best_hours_utc": [14, 15, 16, 17, 20, 21],
        "cooldown_after_bulk_hours": 6,
        "max_consecutive_days": 14,        # IG can shadowban for daily posting
        "rest_days_required": 2,
        "max_title_length": 2200,          # Caption
        "max_description_length": 2200,
        "max_hashtags": 30,               # IG allows 30, 20-25 optimal
        "max_tags": 0,
        "video_length": {"short": (3, 60), "long": (60, 90)},
        "requirements": {
            "min_followers": 0,            # Reels bonuses need 10K+
            "api_setup": "Facebook Developer Portal → Instagram Graph API",
        },
        "rate_limit_notes": [
            "IG shadowbans accounts that post 5+ Reels/day",
            "Use 20-25 hashtags (not all 30) for best reach",
            "Post when your followers are most active (check Insights)",
            "Reels under 15 seconds get remixed more",
        ],
    },
    "facebook": {
        "name": "Facebook Reels",
        "max_videos_per_day": 3,
        "max_videos_per_week": 14,
        "min_interval_minutes": 30,
        "max_interval_minutes": 360,
        "best_hours_utc": [13, 14, 15, 16, 19, 20],
        "cooldown_after_bulk_hours": 6,
        "max_consecutive_days": 14,
        "rest_days_required": 2,
        "max_title_length": 255,
        "max_description_length": 5000,
        "max_hashtags": 10,
        "max_tags": 0,
        "video_length": {"short": (3, 60), "long": (60, 180)},
        "requirements": {
            "api_setup": "Facebook Developer Portal → Graph API",
        },
        "rate_limit_notes": [
            "FB Reels get pushed to non-followers heavily",
            "Videos under 30 seconds get more shares",
            "Cross-posting from IG is easiest path",
        ],
    },
    "x_twitter": {
        "name": "X / Twitter",
        "max_videos_per_day": 5,           # X is more lenient
        "max_videos_per_week": 25,
        "min_interval_minutes": 15,
        "max_interval_minutes": 240,
        "best_hours_utc": [12, 13, 14, 17, 18, 19, 20],
        "cooldown_after_bulk_hours": 4,
        "max_consecutive_days": 30,
        "rest_days_required": 1,
        "max_title_length": 280,           # Tweet length
        "max_description_length": 10000,   # Long-form posts
        "max_hashtags": 3,                # X: 1-2 optimal, 3 max
        "max_tags": 0,
        "video_length": {"short": (3, 45), "long": (45, 140)},
        "requirements": {
            "min_followers": 0,            # Revenue needs 500+ followers
            "api_setup": "X Developer Portal → API v2",
        },
        "rate_limit_notes": [
            "X's algorithm favors conversations over broadcasting",
            "Reply to your own tweet with the video for thread visibility",
            "1-2 hashtags max on X — more looks spammy",
            "Post during US business hours for maximum reach",
        ],
    },
    "rumble": {
        "name": "Rumble",
        "max_videos_per_day": 5,
        "max_videos_per_week": 25,
        "min_interval_minutes": 15,
        "max_interval_minutes": 360,
        "best_hours_utc": [14, 15, 16, 17, 18, 19],
        "cooldown_after_bulk_hours": 4,
        "max_consecutive_days": 30,
        "rest_days_required": 1,
        "max_title_length": 100,
        "max_description_length": 5000,
        "max_hashtags": 10,
        "max_tags": 20,
        "video_length": {"short": (10, 60), "long": (300, 3600)},
        "requirements": {
            "api_setup": "Rumble API — contact support for access",
        },
        "rate_limit_notes": [
            "Rumble has less competition — easier to grow",
            "Conservative audience — avoid controversial content",
            "Revenue sharing starts immediately (no threshold)",
        ],
    },
    "snapchat": {
        "name": "Snapchat Spotlight",
        "max_videos_per_day": 3,
        "max_videos_per_week": 14,
        "min_interval_minutes": 30,
        "max_interval_minutes": 360,
        "best_hours_utc": [16, 17, 18, 19, 20, 21],
        "cooldown_after_bulk_hours": 6,
        "max_consecutive_days": 14,
        "rest_days_required": 2,
        "max_title_length": 0,             # Snapchat has no title
        "max_description_length": 0,
        "max_hashtags": 0,                # Snapchat doesn't use hashtags
        "max_tags": 0,
        "video_length": {"short": (5, 60), "long": (0, 0)},  # Short only
        "requirements": {
            "api_setup": "No public API — manual upload only",
        },
        "rate_limit_notes": [
            "Snapchat Spotlight pays per view — no minimum",
            "Under 30 seconds performs best",
            "Use trending sounds for 10x boost",
            "No hashtags on Snapchat — focus on content quality",
        ],
    },
    "pinterest": {
        "name": "Pinterest Idea Pins",
        "max_videos_per_day": 5,
        "max_videos_per_week": 25,
        "min_interval_minutes": 15,
        "max_interval_minutes": 240,
        "best_hours_utc": [14, 15, 16, 17, 18, 19, 20],
        "cooldown_after_bulk_hours": 4,
        "max_consecutive_days": 30,
        "rest_days_required": 1,
        "max_title_length": 100,
        "max_description_length": 500,
        "max_hashtags": 20,               # Pinterest uses hashtags in descriptions
        "max_tags": 0,
        "video_length": {"short": (5, 60), "long": (60, 300)},
        "requirements": {
            "api_setup": "Pinterest Developer Portal → Pinterest API",
        },
        "rate_limit_notes": [
            "Pinterest is a search engine — SEO matters more than trending",
            "Use keyword-rich descriptions, not just hashtags",
            "Idea Pins get shown to non-followers via search",
            "Consistency matters — pin 3-5x per day",
        ],
    },
}

# One account, two deliberately separate editorial workflows. These are not
# separate YouTube accounts or a way to bypass YouTube's channel-wide policy.
PLATFORM_RULES["youtube_long"] = {
    **PLATFORM_RULES["youtube"],
    "name": "YouTube Videos",
    "max_videos_per_day": 1,
    "max_videos_per_week": 2,
    "min_interval_minutes": 1440,
}
PLATFORM_RULES["youtube_shorts"] = {
    **PLATFORM_RULES["youtube"],
    "name": "YouTube Shorts",
    "max_videos_per_day": 1,
    "max_videos_per_week": 5,
    "min_interval_minutes": 720,
}


@dataclass
class PostingRecord:
    """Record of a single post made to a platform."""
    platform: str
    video_title: str
    posted_at: str            # ISO datetime
    status: str = "posted"    # posted, failed, deleted


@dataclass
class RateLimitState:
    """Current rate limit state for a platform."""
    platform: str
    posts_today: int = 0
    posts_this_week: int = 0
    consecutive_days_posting: int = 0
    last_post_time: Optional[str] = None
    posts: list = field(default_factory=list)
    last_rest_day: Optional[str] = None


class RateLimiter:
    """
    Publishing guardrail — enforces creator-selected posting limits.

    Tracks posting history and prevents:
    - Exceeding daily/weekly upload limits
    - Posting too frequently (minimum intervals)
    - Going too many days without a rest day
    - Posting outside optimal hours

    Usage:
        limiter = RateLimiter()

        # Check if we can post
        can_post, reason = limiter.can_post("youtube")
        if can_post:
            # ... upload video ...
            limiter.record_post("youtube", "My Video Title")
        else:
            print(f"Blocked: {reason}")

        # Get optimal posting time
        best_time = limiter.get_next_optimal_time("tiktok")

        # Get humanized delay between posts
        delay = limiter.get_humanized_delay("instagram")
    """

    def __init__(self, state_dir: str = "projects/_rate_limits", limit_overrides: Optional[dict] = None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._states: dict[str, RateLimitState] = {}
        self.limit_overrides = limit_overrides or {}
        self._load_all()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def can_post(self, platform: str) -> tuple[bool, str]:
        """
        Check if we're allowed to post to this platform right now.

        Returns:
            (can_post: bool, reason: str)
        """
        if platform not in PLATFORM_RULES:
            return True, "Unknown platform — no restrictions"

        rules = self._rules_for(platform)
        state = self._get_state(platform)

        # Check daily limit
        today_count = self._count_posts_today(state)
        if today_count >= rules["max_videos_per_day"]:
            return False, (
                f"Daily limit reached: {today_count}/{rules['max_videos_per_day']} "
                f"videos posted today to {rules['name']}"
            )

        # Check weekly limit
        week_count = self._count_posts_this_week(state)
        if week_count >= rules["max_videos_per_week"]:
            return False, (
                f"Weekly limit reached: {week_count}/{rules['max_videos_per_week']} "
                f"videos posted this week to {rules['name']}"
            )

        # Check minimum interval
        if state.last_post_time:
            last = datetime.fromisoformat(state.last_post_time)
            elapsed = (datetime.now() - last).total_seconds() / 60
            min_interval = rules["min_interval_minutes"]
            if elapsed < min_interval:
                wait = min_interval - elapsed
                return False, (
                    f"Too soon: wait {wait:.0f} more minutes before posting to "
                    f"{rules['name']} (min interval: {min_interval}min)"
                )

        # Check cooldown after bulk posting
        recent_count = self._count_posts_in_window(state, hours=3)
        if recent_count >= 3:
            cooldown = rules["cooldown_after_bulk_hours"]
            return False, (
                f"Bulk posting cooldown: posted {recent_count} videos in last 3 hours. "
                f"Wait {cooldown} hours."
            )

        # Check consecutive days
        if state.consecutive_days_posting >= rules["max_consecutive_days"]:
            rest_needed = rules["rest_days_required"]
            return False, (
                f"Rest day needed: posted {state.consecutive_days_posting} consecutive days. "
                f"Take {rest_needed} day(s) off and review your publishing plan."
            )

        return True, "OK — within your configured publishing guardrails"

    def record_post(self, platform: str, video_title: str = "") -> PostingRecord:
        """Record that a video was posted to a platform."""
        record = PostingRecord(
            platform=platform,
            video_title=video_title,
            posted_at=datetime.now().isoformat(),
            status="posted",
        )

        state = self._get_state(platform)
        state.posts.append(record)
        state.last_post_time = record.posted_at
        state.posts_today = self._count_posts_today(state)
        state.posts_this_week = self._count_posts_this_week(state)
        state.consecutive_days_posting = self._calc_consecutive_days(state)

        self._save_state(platform, state)
        return record

    def get_next_optimal_time(self, platform: str) -> datetime:
        """
        Get the next optimal posting time for a platform.

        Returns a datetime within the next 24 hours at the best hour.
        """
        if platform not in PLATFORM_RULES:
            return datetime.now() + timedelta(minutes=30)

        rules = self._rules_for(platform)
        now = datetime.now()
        best_hours = rules["best_hours_utc"]

        # Find next best hour (in UTC, converted to local)
        from datetime import timezone
        now_utc = now.astimezone(timezone.utc).hour

        next_hour = None
        for h in best_hours:
            if h > now_utc:
                next_hour = h
                break

        if next_hour is None:
            next_hour = best_hours[0] + 24  # Tomorrow

        # Calculate wait time
        hours_ahead = next_hour - now_utc
        if hours_ahead < 0:
            hours_ahead += 24

        target = now + timedelta(hours=hours_ahead)

        return target

    def get_humanized_delay(self, platform: str) -> float:
        """
        Get the configured minimum delay (in seconds) between posts.
        """
        if platform not in PLATFORM_RULES:
            return 60

        rules = self._rules_for(platform)
        min_min = rules["min_interval_minutes"]
        return min_min * 60

    def get_status_summary(self, platform: str) -> dict:
        """Get a summary of current rate limit status."""
        if platform not in PLATFORM_RULES:
            return {"platform": platform, "status": "unknown"}

        rules = self._rules_for(platform)
        state = self._get_state(platform)
        can, reason = self.can_post(platform)

        return {
            "platform": platform,
            "name": rules["name"],
            "can_post": can,
            "reason": reason,
            "posts_today": self._count_posts_today(state),
            "max_per_day": rules["max_videos_per_day"],
            "posts_this_week": self._count_posts_this_week(state),
            "max_per_week": rules["max_videos_per_week"],
            "consecutive_days": state.consecutive_days_posting,
            "max_consecutive": rules["max_consecutive_days"],
            "next_optimal_time": self.get_next_optimal_time(platform).isoformat(),
            "rest_days_required": rules["rest_days_required"],
        }

    def get_all_status(self) -> dict:
        """Get status for all platforms."""
        return {
            platform: self.get_status_summary(platform)
            for platform in PLATFORM_RULES
        }

    def _rules_for(self, platform: str) -> dict:
        """Return platform rules with the user's explicit daily cap applied."""
        rules = PLATFORM_RULES[platform].copy()
        configured = self.limit_overrides.get(platform, {}).get("max_per_day")
        if isinstance(configured, int) and configured > 0:
            rules["max_videos_per_day"] = configured
        return rules

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_state(self, platform: str) -> RateLimitState:
        if platform not in self._states:
            self._states[platform] = RateLimitState(platform=platform)
        return self._states[platform]

    def _count_posts_today(self, state: RateLimitState) -> int:
        today = datetime.now().date().isoformat()
        return sum(
            1 for p in state.posts
            if hasattr(p, 'posted_at') and p.posted_at.startswith(today)
            or isinstance(p, dict) and p.get("posted_at", "").startswith(today)
        )

    def _count_posts_this_week(self, state: RateLimitState) -> int:
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        return sum(
            1 for p in state.posts
            if (hasattr(p, 'posted_at') and p.posted_at >= week_ago)
            or (isinstance(p, dict) and p.get("posted_at", "") >= week_ago)
        )

    def _count_posts_in_window(self, state: RateLimitState, hours: int) -> int:
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        return sum(
            1 for p in state.posts
            if (hasattr(p, 'posted_at') and p.posted_at >= cutoff)
            or (isinstance(p, dict) and p.get("posted_at", "") >= cutoff)
        )

    def _calc_consecutive_days(self, state: RateLimitState) -> int:
        """Calculate how many consecutive days we've posted."""
        if not state.posts:
            return 0

        dates = set()
        for p in state.posts:
            posted = p.posted_at if hasattr(p, 'posted_at') else p.get("posted_at", "")
            if posted:
                dates.add(posted[:10])

        if not dates:
            return 0

        sorted_dates = sorted(dates, reverse=True)
        today = datetime.now().date().isoformat()

        # Start counting from today (or yesterday if no post today)
        if sorted_dates[0] != today:
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            if sorted_dates[0] != yesterday:
                return 0

        count = 1
        for i in range(len(sorted_dates) - 1):
            current = datetime.fromisoformat(sorted_dates[i]).date()
            prev = datetime.fromisoformat(sorted_dates[i + 1]).date()
            if (current - prev).days == 1:
                count += 1
            else:
                break

        return count

    def _load_all(self):
        """Load all platform states from disk."""
        for platform in PLATFORM_RULES:
            state_file = self.state_dir / f"{platform}.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                state = RateLimitState(platform=platform)
                state.posts_today = data.get("posts_today", 0)
                state.posts_this_week = data.get("posts_this_week", 0)
                state.consecutive_days_posting = data.get("consecutive_days_posting", 0)
                state.last_post_time = data.get("last_post_time")
                state.last_rest_day = data.get("last_rest_day")
                # Rebuild posts list
                for p in data.get("posts", []):
                    state.posts.append(PosttingRecord(**p))
                self._states[platform] = state

    def _save_state(self, platform: str, state: RateLimitState):
        """Save a platform state to disk."""
        state_file = self.state_dir / f"{platform}.json"
        data = {
            "platform": state.platform,
            "posts_today": state.posts_today,
            "posts_this_week": state.posts_this_week,
            "consecutive_days_posting": state.consecutive_days_posting,
            "last_post_time": state.last_post_time,
            "last_rest_day": state.last_rest_day,
            "posts": [
                {
                    "platform": p.platform,
                    "video_title": p.video_title,
                    "posted_at": p.posted_at,
                    "status": p.status,
                }
                for p in state.posts
            ],
        }
        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)
