"""Editorial guardrails for original, reviewable faceless content.

This module deliberately checks quality and provenance.  It does not try to
simulate human behaviour or work around a platform's enforcement systems.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlparse


FACTUAL_NICHES = {
    "finance", "history", "space", "psychology", "did_you_know",
    "true_crime", "unsolved_murder_mysteries",
}


@dataclass
class QualityReport:
    publish_ready: bool
    warnings: list[str]
    errors: list[str]
    similarity: float = 0.0

    def to_dict(self) -> dict:
        return {
            "publish_ready": self.publish_ready,
            "warnings": self.warnings,
            "errors": self.errors,
            "similarity": round(self.similarity, 3),
        }


class ContentQualityGate:
    """Persist a small editorial history and reject near-duplicate scripts."""

    def __init__(self, history_path: str = "projects/_content_history/editorial_history.json"):
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def evaluate(self, script, require_source_review: bool = True, threshold: float = 0.72,
                 expected_duration_seconds: float | None = None) -> QualityReport:
        warnings: list[str] = []
        errors: list[str] = []
        narration = self._script_text(script)
        spoken_text = f"{getattr(script, 'hook', '').strip()} {narration}".strip()
        references = getattr(script, "references", []) or []
        niche = getattr(script, "niche", "")

        word_count = len(spoken_text.split())
        if word_count < 35:
            errors.append("The narration is too short to deliver meaningful value.")
        if expected_duration_seconds:
            # Voice engines generally speak 2.2--2.6 words per second.  Use a
            # conservative floor so a requested 40-second Short does not
            # render as a 30-second post simply because scene estimates were
            # inflated.
            minimum_words = max(70, round(float(expected_duration_seconds) * 2.25))
            if word_count < minimum_words:
                errors.append(
                    f"The narration has {word_count} words; this format needs at least {minimum_words} words for natural pacing."
                )
        if not getattr(script, "hook", "").strip():
            errors.append("A script needs a clear opening hook.")

        if niche in FACTUAL_NICHES and require_source_review:
            if not references:
                errors.append("Source review is required for this factual niche before publishing.")
            elif not all(self._valid_reference(item) for item in references):
                errors.append("Every source must include a title and a valid http(s) URL.")
        elif niche == "daily_meditation" and self._contains_medical_claim(narration):
            errors.append("Meditation content contains a medical claim; rewrite it or add an approved source and review.")

        best_similarity = self._highest_similarity(script)
        if best_similarity >= threshold:
            errors.append(f"This script is too similar to a previous production ({best_similarity:.0%}). Choose a new angle.")
        elif best_similarity >= threshold * 0.85:
            warnings.append(f"This script overlaps with a prior production ({best_similarity:.0%}); review the hook and angle.")

        return QualityReport(not errors, warnings, errors, best_similarity)

    def record(self, script) -> None:
        entries = self._load()
        entries.append({
            "title": getattr(script, "title", ""),
            "hook": getattr(script, "hook", ""),
            "narration": self._script_text(script),
            "niche": getattr(script, "niche", ""),
            "created_at": getattr(script, "created_at", ""),
        })
        self.history_path.write_text(json.dumps(entries[-250:], indent=2, ensure_ascii=False), encoding="utf-8")

    def _highest_similarity(self, script) -> float:
        candidate = self._normalise(f"{getattr(script, 'title', '')} {getattr(script, 'hook', '')} {self._script_text(script)}")
        if not candidate:
            return 0.0
        return max((SequenceMatcher(None, candidate, self._normalise(f"{entry.get('title', '')} {entry.get('hook', '')} {entry.get('narration', '')}")).ratio() for entry in self._load()), default=0.0)

    def recent_topics(self, niche: str, limit: int = 20) -> list[str]:
        """Return recent titles for the planner to avoid repeating an angle."""
        return [entry.get("title", "") for entry in self._load() if entry.get("niche") == niche][-limit:]

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def _script_text(script) -> str:
        return " ".join(segment.narration.strip() for segment in getattr(script, "segments", []) if segment.narration.strip())

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", value.lower())).strip()

    @staticmethod
    def _valid_reference(value: object) -> bool:
        if not isinstance(value, dict) or not value.get("title"):
            return False
        parsed = urlparse(str(value.get("url", "")))
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _contains_medical_claim(value: str) -> bool:
        return bool(re.search(r"\b(cure|treat|heal|diagnos|therapy|clinical|depression|anxiety)\b", value, re.I))
