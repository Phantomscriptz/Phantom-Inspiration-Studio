"""Canonical production profiles used before an upload is attempted.

Profiles describe a deliverable, not a promise that every platform's current
recommendation will remain unchanged.  Official platform rules still win.
"""

VERTICAL_SHORT_PLATFORMS = {"youtube_shorts", "tiktok", "instagram", "facebook", "snapchat"}
LANDSCAPE_SHORT_PLATFORMS = {"x_twitter"}
LONG_LANDSCAPE_PLATFORMS = {"youtube_long", "rumble"}

PROFILES = {
    "vertical_short": {
        "width": 1080, "height": 1920, "fps": 30,
        "recommended_seconds": 45,
        "description": "Original vertical short for Shorts, Reels, TikTok, Facebook Reels, and Spotlight.",
    },
    "landscape_short": {
        "width": 1920, "height": 1080, "fps": 30,
        "recommended_seconds": 40,
        "description": "Short landscape cut for X.",
    },
    "long": {
        "width": 1920, "height": 1080, "fps": 30,
        "recommended_seconds": 480,
        "description": "Long-form landscape episode for YouTube and Rumble.",
    },
}
