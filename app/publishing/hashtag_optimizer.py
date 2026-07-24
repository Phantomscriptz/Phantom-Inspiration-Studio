"""Platform-specific hashtag & metadata optimizer.

Ensures each platform gets the MAXIMUM allowed hashtags with the
best-performing tags for the niche. Research-backed hashtag limits
and strategies per platform.
"""

from typing import Optional


# ============================================================================
# PLATFORM HASHTAG LIMITS (researched, current as of 2026)
# ============================================================================

PLATFORM_HASHTAG_LIMITS = {
    "youtube": {
        "max_hashtags": 15,          # YT allows 15, shows 3 above title
        "optimal_range": (10, 15),   # Use 10-15 for best discoverability
        "description_format": "hashtags_at_bottom",  # Put hashtags at end of description
        "title_hashtags": 0,         # Don't put hashtags in YT titles
        "notes": [
            "YouTube shows first 3 hashtags above the title",
            "Put remaining hashtags in the description",
            "Use a mix of broad and specific tags",
            "Research trending topics in YouTube Trends",
        ],
    },
    "tiktok": {
        "max_hashtags": 10,          # TikTok caption limit
        "optimal_range": (4, 8),     # 4-8 is the sweet spot
        "description_format": "inline_with_caption",  # In the caption
        "title_hashtags": 0,
        "notes": [
            "TikTok: 3-5 hashtags is optimal for the algorithm",
            "Mix trending + niche + broad hashtags",
            "#fyp #foryou #viral still work as boosters",
            "Use TikTok's Creative Center to find trending hashtags",
        ],
    },
    "instagram": {
        "max_hashtags": 30,          # IG allows 30 per post
        "optimal_range": (20, 25),   # 20-25 is the sweet spot (not all 30)
        "description_format": "at_end_of_caption",  # After caption text
        "title_hashtags": 0,
        "notes": [
            "Instagram: Use 20-25 hashtags (not all 30 — looks spammy)",
            "Mix 5 large (1M+), 10 medium (100K-1M), 10 small (<100K)",
            "Use Instagram's suggested hashtags feature",
            "Put hashtags in first comment OR caption (both work)",
        ],
    },
    "facebook": {
        "max_hashtags": 10,
        "optimal_range": (3, 5),     # FB: less is more
        "description_format": "inline_with_caption",
        "title_hashtags": 0,
        "notes": [
            "Facebook doesn't favor hashtags as much",
            "Use 3-5 relevant hashtags max",
            "Focus more on shareability than hashtags",
            "Video length under 3 min performs best on FB",
        ],
    },
    "x_twitter": {
        "max_hashtags": 3,           # X: 1-2 is optimal, 3 max
        "optimal_range": (1, 2),
        "description_format": "inline_in_tweet",
        "title_hashtags": 0,
        "notes": [
            "X/Twitter: More than 2 hashtags REDUCES engagement",
            "Use 1-2 highly relevant hashtags only",
            "Focus on conversation starters, not hashtags",
            "Quote-tweet your own video for more reach",
        ],
    },
    "rumble": {
        "max_hashtags": 10,
        "optimal_range": (5, 8),
        "description_format": "at_end_of_description",
        "title_hashtags": 0,
        "notes": [
            "Rumble: Use 5-8 hashtags in description",
            "Focus on conservative/alternative content tags",
            "Title matters more than hashtags on Rumble",
            "Cross-promote from other platforms",
        ],
    },
    "snapchat": {
        "max_hashtags": 0,           # Snapchat doesn't use hashtags
        "optimal_range": (0, 0),
        "description_format": "none",
        "title_hashtags": 0,
        "notes": [
            "Snapchat Spotlight doesn't use hashtags",
            "Use trending sounds instead for discoverability",
            "Content quality is the only real ranking factor",
            "Under 30 seconds performs best",
        ],
    },
    "pinterest": {
        "max_hashtags": 20,
        "optimal_range": (5, 10),    # Pinterest is a search engine
        "description_format": "in_pin_description",
        "title_hashtags": 0,
        "notes": [
            "Pinterest is a SEARCH ENGINE — keywords > hashtags",
            "Use keyword-rich descriptions (SEO matters most)",
            "Include hashtags but don't overstuff",
            "Pin titles should be keyword-optimized",
        ],
    },
}


# ============================================================================
# NICHE-SPECIFIC HASHTAG BANKS
# ============================================================================

NICHE_HASHTAG_BANKS = {
    "scary_stories": {
        "broad": ["#scary", "#horror", "#creepy", "#scaryvideo", "#nightmare"],
        "niche": ["#scarystory", "#ghoststory", "#darkstories", "#horrorcommunity",
                  "#haunted", "#paranormal", "#scarycontent", "#horrorshorts"],
        "engagement": ["#cantunsee", "#sleep", "#nightmarefuel", "#terrifying"],
    },
    "reddit_stories": {
        "broad": ["#reddit", "#story", "#drama", "#storytime", "#viral"],
        "niche": ["#redditstories", "#redditread", "#aita", "#tifu",
                  "#reddithorror", "#relationship", "#confession", "#redditread"],
        "engagement": ["#ohno", "#waitforit", "#plot twist", "#shocking"],
    },
    "motivational": {
        "broad": ["#motivation", "#success", "#life", "#goals", "#inspiration"],
        "niche": ["#stoicism", "#mindset", "#discipline", "#grindset",
                  "#selfimprovement", "#philosophy", "#marcus Aurelius", "#raremindset"],
        "engagement": ["#grind", "#hustle", "#neverquit", "#warriormindset"],
    },
    "finance": {
        "broad": ["#money", "#business", "#investing", "#wealth", "#success"],
        "niche": ["#passiveincome", "#stocks", "#crypto", "#financialfreedom",
                  "#makemoneyonline", "#sidehustle", "#invest", "#moneymindset"],
        "engagement": ["#rich", "#millionaire", "#bag", "#cashflow"],
    },
    "true_crime": {
        "broad": ["#crime", "#mystery", "#story", "#investigation", "#case"],
        "niche": ["#truecrime", "#truecrimecommunity", "#murder", "#serialkiller",
                  "#casefile", "#criminalmind", "#crimecase", "#unsolved"],
        "engagement": ["#what", "#crazy", "#dark", "#disturbing"],
    },
    "unsolved_murder_mysteries": {
        "broad": ["#mystery", "#crime", "#coldcase", "#unsolved", "#detective"],
        "niche": ["#unsolvedmystery", "#unsolvedcase", "#murdermystery",
                  "#coldcasefiles", "#truecrimedaily", "#crimecase",
                  "#missing", "#forensics", "#whodunit"],
        "engagement": ["#justice", "#casefiles", "#clues", "#evidence"],
    },
    "did_you_know": {
        "broad": ["#facts", "#knowledge", "#learning", "#interesting", "#amazing"],
        "niche": ["#didyouknow", "#factsdaily", "#factcheck", "#mindblown",
                  "#learnontiktok", "#randomfacts", "#factoids", "#knowledgeispower"],
        "engagement": ["#wow", "#unbelievable", "#true", "#real"],
    },
    "history": {
        "broad": ["#history", "#past", "#ancient", "#world", "#story"],
        "niche": ["#historystory", "#worldwar", "#rome", "#civilization",
                  "#historical", "#ww2", "#ancienthistory", "#historicalfacts"],
        "engagement": ["#forgotten", "#before", "#century", "#era"],
    },
    "space": {
        "broad": ["#space", "#science", "#universe", "#nasa", "#cosmos"],
        "niche": ["#astronomy", "#blackhole", "#galaxy", "#planets",
                  "#cosmology", "#deepspace", "#nebula", "#solarsystem"],
        "engagement": ["#mindblown", "#beautiful", "#breathtaking", "#infinity"],
    },
    "psychology": {
        "broad": ["#psychology", "#mind", "#brain", "#behavior", "#human"],
        "niche": ["#humanbehavior", "#psychologyfacts", "#bodylanguage",
                  "#nlp", "#cognitive", "#subconscious", "#emotionalintelligence"],
        "engagement": ["#relatable", "#truth", "#real", "#exposed"],
    },
    "mystery": {
        "broad": ["#mystery", "#unexplained", "#strange", "#weird", "#secret"],
        "niche": ["#paranormal", "#conspiracy", "#cryptid", "#unsolvedmystery",
                  "#supernatural", "#occult", "#enigma", "#mysteriouss"],
        "engagement": ["#disturbing", "#scary", "#deep", "#dark"],
    },
    "daily_meditation": {
        "broad": ["#meditation", "#calm", "#peace", "#relax", "#wellness"],
        "niche": ["#mindfulness", "#guidedmeditation", "#breathwork",
                  "#innerpeace", "#stressrelief", "#selfcare", "#yoga",
                  "#meditacion", "#healing", "#mentalhealth"],
        "engagement": ["#breathe", "#letgo", "#present", "#awareness"],
    },
}


# ============================================================================
# BROAD / TRENDING HASHTAGS (work across all niches)
# ============================================================================

GLOBAL_TRENDING_HASHTAGS = {
    "tiktok": ["#fyp", "#foryou", "#foryoupage", "#viral", "#trending",
               "#xyzbca", "#blowthisup"],
    "instagram": ["#reels", "#reelsinstagram", "#instareels", "#viral",
                  "#trending", "#explore", "#reelsvideo"],
    "youtube": ["#shorts", "#viral", "#trending", "#youtube", "#new"],
    "facebook": ["#reels", "#viral", "#trending"],
    "x_twitter": ["#viral", "#trending"],
    "rumble": ["#viral", "#trending", "#new"],
    "pinterest": ["#trending", "#ideas", "#inspiration"],
}


class HashtagOptimizer:
    """
    Optimizes hashtags, titles, and descriptions per platform.

    Usage:
        optimizer = HashtagOptimizer()

        result = optimizer.optimize(
            platform="youtube",
            niche="scary_stories",
            title="The Haunted Lighthouse",
            narration_excerpt="There's a lighthouse...",
        )
        # result = {
        #     "title": "...",
        #     "description": "...",
        #     "hashtags": [...],
        #     "hashtag_string": "#scary #horror ...",
        # }

    Hashtag Rules:
        - YouTube: Use ALL 15 hashtags (max allowed)
        - Instagram: Use 20-25 hashtags (out of 30 max)
        - TikTok: Use 4-8 hashtags (out of 10 max)
        - X: Use 1-2 hashtags (out of 3 max)
        - Snapchat: No hashtags
        - Pinterest: Use 5-10 hashtags (focus on keywords)
        - Rumble: Use 5-8 hashtags
        - Facebook: Use 3-5 hashtags
    """

    def optimize(
        self,
        platform: str,
        niche: str,
        title: str,
        narration_excerpt: str = "",
        extra_hashtags: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate fully optimized metadata for a specific platform.

        Returns dict with: title, description, hashtags, hashtag_string, tags
        """
        limits = PLATFORM_HASHTAG_LIMITS.get(platform, PLATFORM_HASHTAG_LIMITS["youtube"])
        max_tags = limits["max_hashtags"]
        optimal_min, optimal_max = limits["optimal_range"]

        # Build hashtag pool
        niche_bank = NICHE_HASHTAG_BANKS.get(niche, {})
        global_tags = GLOBAL_TRENDING_HASHTAGS.get(platform, [])

        pool = []
        pool.extend(niche_bank.get("broad", []))
        pool.extend(niche_bank.get("niche", []))
        pool.extend(niche_bank.get("engagement", []))
        pool.extend(global_tags)
        if extra_hashtags:
            pool.extend(extra_hashtags)

        # Deduplicate
        seen = set()
        unique_pool = []
        for tag in pool:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_pool.append(tag)

        # Select optimal count
        if max_tags == 0:
            selected = []
        else:
            # Prioritize: niche-specific first, then broad, then engagement, then global
            selected = unique_pool[:optimal_max]

        # Build hashtag string
        hashtag_string = " ".join(selected) if selected else ""

        # Build description
        description = self._build_description(
            platform, title, narration_excerpt, selected, niche
        )

        # Platform-specific title optimization
        optimized_title = self._optimize_title(platform, title)

        return {
            "title": optimized_title,
            "description": description,
            "hashtags": selected,
            "hashtag_string": hashtag_string,
            "tags": selected,  # Same as hashtags for most platforms
            "hashtag_count": len(selected),
            "max_allowed": max_tags,
            "platform_notes": limits["notes"],
        }

    def get_max_hashtags(self, platform: str) -> int:
        """Get the maximum allowed hashtags for a platform."""
        return PLATFORM_HASHTAG_LIMITS.get(platform, {}).get("max_hashtags", 0)

    def get_platform_rules(self, platform: str) -> dict:
        """Get full platform hashtag rules."""
        return PLATFORM_HASHTAG_LIMITS.get(platform, {})

    def _build_description(
        self,
        platform: str,
        title: str,
        narration_excerpt: str,
        hashtags: list[str],
        niche: str,
    ) -> str:
        """Build a platform-optimized description."""
        limits = PLATFORM_HASHTAG_LIMITS.get(platform, {})
        fmt = limits.get("description_format", "at_end_of_caption")
        hashtag_str = " ".join(hashtags)

        if platform == "youtube":
            desc = (
                f"{title}\n\n"
                f"{narration_excerpt[:200]}\n\n"
                f"{'—' * 20}\n"
                f"🔔 Subscribe for more {niche.replace('_', ' ')} content!\n"
                f"👍 Like if this gave you chills\n"
                f"💬 Drop a comment with your theory\n\n"
                f"{hashtag_str}\n\n"
                f"#PhantomInspiration #PhantomScriptz"
            )
        elif platform == "tiktok":
            desc = (
                f"{narration_excerpt[:150]}\n\n"
                f"{hashtag_str}"
            )
        elif platform == "instagram":
            desc = (
                f"{narration_excerpt[:200]}\n\n"
                f"{'—' * 15}\n"
                f"🔔 Follow for daily {niche.replace('_', ' ')}\n"
                f"👍 Double tap if you're brave enough\n"
                f"💬 Tag someone who needs to see this\n\n"
                f"{hashtag_str}"
            )
        elif platform == "x_twitter":
            # X: keep it short and punchy
            desc = (
                f"{narration_excerpt[:200]}\n\n"
                f"{hashtag_str}"
            )
        elif platform == "facebook":
            desc = (
                f"{narration_excerpt[:200]}\n\n"
                f"Like & Share if you found this interesting!\n\n"
                f"{hashtag_str}"
            )
        elif platform == "rumble":
            desc = (
                f"{title}\n\n"
                f"{narration_excerpt[:300]}\n\n"
                f"Subscribe and support independent content!\n\n"
                f"{hashtag_str}"
            )
        elif platform == "pinterest":
            desc = (
                f"{title} — {narration_excerpt[:150]}\n\n"
                f"{hashtag_str}"
            )
        else:
            desc = f"{narration_excerpt[:200]}\n\n{hashtag_str}"

        return desc.strip()

    def _optimize_title(self, platform: str, title: str) -> str:
        """Optimize title for the platform."""
        limits = PLATFORM_HASHTAG_LIMITS.get(platform, {})
        max_len = {
            "youtube": 100,
            "tiktok": 150,
            "instagram": 2200,
            "facebook": 255,
            "x_twitter": 280,
            "rumble": 100,
            "snapchat": 255,
            "pinterest": 100,
        }.get(platform, 100)

        if len(title) > max_len:
            title = title[:max_len - 3] + "..."

        return title
