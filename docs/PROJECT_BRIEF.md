# Phantom Inspiration Studio — Project Brief

## Product goal

Build a Windows-first, professional faceless-video creator that helps a creator make original, reviewable short- and long-form content. The initial brand focus is **Original Inspiration / Resilience** and related mindfulness content. Android is a later, separate product rewrite.

The product must help creators produce work worth watching. It must not promise views, followers, monetization, or evade platform rules.

## Core workflow

1. Creator selects a focused niche and permitted sub-topics.
2. A local Ollama model plans an original angle and writes a script.
3. The app generates script-matched visual prompts/images, narration, word-aligned captions, audio mix, thumbnail, and platform-specific metadata.
4. The app writes a review package containing the final video, references, visual plan, credits, title, description, and hashtags.
5. Creator reviews the package. Publishing is off by default and may use only supported official platform APIs.

## Current product principles

- Original scripts, factual-source review where needed, and near-duplicate checks.
- No artificial engagement, bot-evasion behavior, fake followers, or misleading metadata.
- Clear affiliate disclosures; links are opt-in and niche-relevant.
- B-roll is optional. The standard production path is script-matched AI visuals.
- YouTube long-form and Shorts are separate deliverables but share the same channel policies.
- Keep a focused channel; do not randomly mix unrelated niches on one brand.

## Current technical baseline

- Python + PySide6 desktop application.
- Local Ollama for script generation.
- WhisperX installed in `.venv-whisperx` for word-level caption alignment.
- FFmpeg rendering, audio normalization, captions, review packages, storage cleanup.
- Official YouTube OAuth and shared channel-audience sync; other platform integrations remain incomplete.
- Launch locally with `Launch Phantom Inspiration Studio.cmd`.

## Format defaults

| Deliverable | Default |
|---|---|
| YouTube long / Rumble | 1920×1080, 16:9, 30 fps |
| YouTube Shorts / TikTok / Reels / Spotlight | 1080×1920, 9:16, 30 fps |
| X landscape cut | 1920×1080, 16:9, 30 fps |

4K is a later optional long-form profile only when the visual source is truly high-detail.

## Secrets and release safety

- Never commit API keys, OAuth tokens, user clips, generated media, or private credentials.
- Use ignored local config files for secrets.
- Do not publish to GitHub until a secret scan and release review pass.
