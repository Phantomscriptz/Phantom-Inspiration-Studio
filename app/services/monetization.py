"""Truthful, creator-facing monetization progress information.

This module deliberately distinguishes an *eligibility target* from a promise
of revenue.  Platform programmes, countries, and policy rules change; the
official creator dashboard is always the final authority.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonetizationProgram:
    name: str
    overview: str
    official_url: str
    subscriber_target: int | None = None
    progress_label: str = "subscribers"
    secondary_target: str | None = None


PROGRAMS: dict[str, MonetizationProgram] = {
    "youtube_long": MonetizationProgram(
        name="YouTube Partner Program",
        subscriber_target=1000,
        progress_label="subscribers",
        secondary_target="plus 4,000 valid public watch hours in 12 months OR 10M valid Shorts views in 90 days for ad-revenue sharing.",
        overview="Early fan-funding eligibility can begin at 500 subscribers in eligible regions; full ad-revenue eligibility has higher requirements.",
        official_url="https://support.google.com/youtube/answer/72851",
    ),
    "youtube_shorts": MonetizationProgram(
        name="YouTube Partner Program",
        subscriber_target=1000,
        progress_label="subscribers (shared YouTube channel)",
        secondary_target="plus 10M valid public Shorts views in 90 days OR 4,000 valid public watch hours in 12 months for ad-revenue sharing.",
        overview="Shorts and long-form share one channel and the same subscriber count. Early fan-funding eligibility can begin at 500 subscribers in eligible regions.",
        official_url="https://support.google.com/youtube/answer/72851",
    ),
    "tiktok": MonetizationProgram(
        name="TikTok Creator Rewards",
        subscriber_target=10000,
        progress_label="followers",
        secondary_target="plus 100,000 authentic video views in the last 30 days; country, age, account, and original-content requirements also apply.",
        overview="Availability is regional and the creator must pass TikTok's current eligibility check.",
        official_url="https://support.tiktok.com/en/business-and-creator/creator-rewards-program/creator-rewards-program",
    ),
    "instagram": MonetizationProgram(
        name="Instagram monetization tools",
        overview="Availability varies by country, account type, and product. Use a professional account and check the in-app Professional Dashboard for the current eligibility decision.",
        official_url="https://help.instagram.com/2635536099905516",
    ),
    "facebook": MonetizationProgram(
        name="Facebook Content Monetization",
        overview="Availability and eligibility vary by territory and account. A professional Page/profile should check Monetization Manager for the current decision.",
        official_url="https://www.facebook.com/business/help/169845596919485",
    ),
    "x_twitter": MonetizationProgram(
        name="X Creator Revenue Sharing",
        subscriber_target=500,
        progress_label="verified followers",
        secondary_target="plus an active Premium subscription, 5M organic impressions in the last 3 months, and current regional/policy eligibility.",
        overview="The final eligibility check happens inside X's Monetization settings.",
        official_url="https://help.x.com/en/using-x/creator-revenue-sharing",
    ),
    "rumble": MonetizationProgram(
        name="Rumble creator earnings",
        overview="Earnings depend on the selected licensing/monetization option, content eligibility, and current Rumble terms rather than one universal follower threshold.",
        official_url="https://rumble.support/",
    ),
    "snapchat": MonetizationProgram(
        name="Snapchat creator monetization",
        overview="Snapchat evaluates eligibility through its current monetization programme; requirements and supported regions change, so verify in the Creator Hub before planning around it.",
        official_url="https://help.snapchat.com/hc/en-us/articles/7012333925780-How-do-I-get-paid-for-creating-content-on-Snapchat",
    ),
}


def program_for(platform_key: str) -> MonetizationProgram:
    """Return a platform's public programme summary without guessing metrics."""
    return PROGRAMS.get(platform_key, MonetizationProgram(
        name="Monetization",
        overview="Check this platform's official creator dashboard for current eligibility.",
        official_url="",
    ))


def progress_text(platform_key: str, audience: dict | None = None) -> str:
    """Format an honest progress message from officially synced counts only."""
    program = program_for(platform_key)
    if not program.subscriber_target:
        return "Current account statistics will appear here after an official analytics connection is available."

    raw_count = (audience or {}).get("subscribers")
    try:
        current = int(str(raw_count))
    except (TypeError, ValueError):
        return f"Connect official analytics to calculate progress toward {program.subscriber_target:,} {program.progress_label}."

    remaining = max(0, program.subscriber_target - current)
    if remaining:
        return f"Current: {current:,} {program.progress_label} · {remaining:,} to the {program.subscriber_target:,} target."
    return f"Subscriber/follower target reached ({current:,}). Verify the remaining requirements in the official creator dashboard."
