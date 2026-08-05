"""Match script scenes to creator-supplied, licensed stock motion clips."""

import json
import re
from pathlib import Path


VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".avi"}
STOP_WORDS = {"the", "and", "with", "that", "this", "from", "your", "into", "about", "when", "then", "they", "their", "have", "will", "just", "more", "than", "what", "where", "while", "person"}


class CinematicBrollPlanner:
    """Use descriptive filenames and an optional manifest to choose local clips."""

    def __init__(self, library_dir: str = "assets/stock_videos"):
        self.library_dir = Path(library_dir)

    def match_segments(self, segments: list[dict], fallback_visuals: list[str], niche: str = "", selected_clip: str = ""):
        clips, metadata = self._load_library()
        selected_clip_record = self._selected_clip(selected_clip, clips)
        visual_paths, plan = [], []
        for index, segment in enumerate(segments):
            fallback = fallback_visuals[index] if index < len(fallback_visuals) else ""
            keywords = self._keywords(f"{segment.get('image_prompt', '')} {segment.get('narration', '')}")
            best, score = (selected_clip_record, 0) if selected_clip_record else self._best_clip(keywords, clips)
            strategy = "keyword_match"
            if selected_clip_record:
                strategy = "creator_selected_loop"
            elif not best or score == 0:
                best, score = self._calm_fallback(index, clips, niche)
                strategy = "calm_visual_fallback" if best else "generated_image"
            visual = str(best["path"]) if best else fallback
            entry = {
                "segment": index + 1,
                "keywords": sorted(keywords),
                "visual": visual,
                "type": "licensed_stock_video" if best else "generated_image",
                "match_strategy": strategy,
            }
            if best:
                license_verified = bool(best.get("source") and best.get("license"))
                entry.update({
                    "source": best.get("source", "Missing — review required"),
                    "creator": best.get("creator", ""),
                    "license": best.get("license", "Missing — review required"),
                    "license_verified": license_verified,
                    "match_score": score,
                })
            plan.append(entry)
            visual_paths.append(visual)
        return visual_paths, plan

    @staticmethod
    def _selected_clip(selected_clip: str, clips: list[dict]):
        """Resolve a filename only; never allow an arbitrary path from settings."""
        if not selected_clip:
            return None
        return next((clip for clip in clips if clip["path"].name == Path(selected_clip).name), None)

    def _load_library(self):
        self.library_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.library_dir / "manifest.json"
        manifest = {}
        try:
            manifest = {item.get("filename"): item for item in json.loads(manifest_path.read_text(encoding="utf-8")).get("clips", [])}
        except (OSError, json.JSONDecodeError):
            pass
        clips = []
        for path in self.library_dir.rglob("*"):
            if path.suffix.lower() in VIDEO_SUFFIXES:
                details = manifest.get(path.name, {})
                terms = self._keywords(f"{path.stem} {' '.join(details.get('keywords', []))}")
                clips.append({"path": path.resolve(), "keywords": terms, "source": details.get("source"), "creator": details.get("creator"), "license": details.get("license")})
        return clips, manifest

    @staticmethod
    def _keywords(value: str) -> set[str]:
        return {word for word in re.findall(r"[a-z]{3,}", value.lower()) if word not in STOP_WORDS}

    @staticmethod
    def _best_clip(keywords: set[str], clips: list[dict]):
        if not clips:
            return None, 0
        candidate = max(clips, key=lambda clip: len(keywords & clip["keywords"]))
        return candidate, len(keywords & candidate["keywords"])

    @staticmethod
    def _calm_fallback(index: int, clips: list[dict], niche: str):
        """Use a review-visible B-roll fallback for calm inspiration only."""
        if niche not in {"motivational", "daily_meditation", "psychology"}:
            return None, 0
        calm_terms = {"calm", "nature", "water", "ocean", "sunrise", "desert", "boats", "hourglass"}
        candidates = [clip for clip in clips if clip["keywords"] & calm_terms]
        if not candidates:
            return None, 0
        return candidates[index % len(candidates)], 0
