"""Prompt templates for AI script generation.

Each template is designed for qwen2.5:7b (or similar local models) and
returns structured output that can be parsed reliably.
"""

from typing import Optional


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

SCRIPT_WRITER_SYSTEM = """\
You are PhantomScript, an expert faceless video script writer.
You write original scripts designed to earn attention through genuine value. Your scripts are:

- HOOK the viewer in the first 2 seconds
- Use short, punchy sentences (great for voiceover)
- Build curiosity gaps and cliffhangers
- Use emotional triggers (fear, wonder, surprise, humor)
- Include visual cues for image/video generation
- End with a strong call to action

You never promise outcomes, invent facts, imitate a living creator, reuse a
third party's script, or present health, legal, or financial guidance as advice.
For factual claims, use cautious wording unless the supplied topic includes a
verifiable source. The creator must be able to review every script before it is published.

You write for SHORT-FORM (15-90s) and LONG-FORM (5-15min) faceless videos.
Your tone adapts to the niche: mysterious for horror, authoritative for finance,
casual for Reddit stories, awe-inspiring for science.

NEVER use the words: "um", "uh", "so basically", "in conclusion".
ALWAYS write as if speaking directly to the viewer."""

METADATA_SYSTEM = """\
You are an expert YouTube/TikTok SEO specialist and social media strategist.
You optimize titles, descriptions, and tags for maximum discoverability and clicks.
You understand platform metadata conventions. Never claim guaranteed views,
use misleading clickbait, keyword-stuff, or add irrelevant trending hashtags."""

NICHES = {
    "scary_stories": {
        "name": "Scary Stories / Horror",
        "tone": "dark, suspenseful, whispery",
        "audience": "18-34, horror fans",
        "hashtags": ["#scary", "#horror", "#scarystory", "#darkstories", "#nightmares", "#creepy", "#horrorcommunity"],
        "best_times": "8pm-12am",
        "rpm_range": "$5-12",
        "subniches": ["urban legends", "haunted places", "psychological suspense", "campfire fiction", "unexplained encounters", "creepy folklore"],
    },
    "reddit_stories": {
        "name": "Reddit Stories",
        "tone": "casual, conversational, reactive",
        "audience": "18-30, Reddit users",
        "hashtags": ["#reddit", "#redditstories", "#redditread", "#aita", "#tifu", "#relationship", "#drama"],
        "best_times": "12pm-3pm, 7pm-10pm",
        "rpm_range": "$3-8",
        "subniches": ["workplace dilemmas", "friendship conflicts", "family boundaries", "relationship communication", "moral dilemmas", "lighthearted confessions"],
    },
    "motivational": {
        "name": "Original Inspiration / Resilience",
        "tone": "specific, grounded, encouraging, never preachy",
        "audience": "18-35, people building better habits",
        "hashtags": ["#motivation", "#mindset", "#discipline", "#selfimprovement", "#resilience", "#habits", "#inspiration"],
        "best_times": "6am-9am, 7pm-9pm",
        "rpm_range": "$8-20",
        "subniches": [
            "small wins and taking the next doable step",
            "resilience after an ordinary setback",
            "gentle discipline and sustainable habits",
            "confidence without pretending to be fearless",
            "self-respect, boundaries, and inner self-talk",
            "starting again after procrastination or a difficult week",
            "purpose, patience, and long-term progress",
            "rest, recovery, and avoiding burnout without medical claims",
        ],
    },
    "finance": {
        "name": "Finance / Money",
        "tone": "authoritative, educational, urgent",
        "audience": "22-45, aspiring investors",
        "hashtags": ["#money", "#finance", "#investing", "#passiveincome", "#wealth", "#stocks", "#crypto"],
        "best_times": "9am-11am, 6pm-8pm",
        "rpm_range": "$15-30",
        "subniches": ["budgeting basics", "saving habits", "financial literacy", "career income skills", "consumer psychology", "scam awareness"],
    },
    "true_crime": {
        "name": "True Crime",
        "tone": "investigative, gripping, respectful",
        "audience": "20-40, true crime fans",
        "hashtags": ["#truecrime", "#crime", "#mystery", "#unsolved", "#detective", "#criminalmind", "#casefile"],
        "best_times": "7pm-11pm",
        "rpm_range": "$6-15",
        "subniches": ["case timelines", "forensic process", "missing-person awareness", "investigation history", "legal process education", "victim-centered case summaries"],
    },
    "did_you_know": {
        "name": "Did You Know / Facts",
        "tone": "curious, surprising, educational",
        "audience": "15-35, general",
        "hashtags": ["#didyouknow", "#facts", "#interesting", "#mindblown", "#factsdaily", "#learnontiktok", "#knowledge"],
        "best_times": "11am-1pm, 5pm-8pm",
        "rpm_range": "$3-7",
        "subniches": ["everyday science", "nature wonders", "human body basics", "language and culture", "inventions", "surprising history"],
    },
    "history": {
        "name": "History",
        "tone": "storytelling, dramatic, educational",
        "audience": "20-45, history buffs",
        "hashtags": ["#history", "#historical", "#ancient", "#civilization", "#ww2", "#roman", "#historystory"],
        "best_times": "10am-12pm, 7pm-9pm",
        "rpm_range": "$5-12",
        "subniches": ["ancient civilizations", "forgotten inventions", "turning points", "daily life in history", "biographies", "places and landmarks"],
    },
    "space": {
        "name": "Space / Science",
        "tone": "awe-inspiring, cosmic, humbling",
        "audience": "16-40, science enthusiasts",
        "hashtags": ["#space", "#universe", "#nasa", "#cosmos", "#science", "#astronomy", "#blackhole"],
        "best_times": "8pm-11pm",
        "rpm_range": "$5-10",
        "subniches": ["solar system", "astronomy discoveries", "space missions", "cosmic scale", "exoplanets", "physics explainers"],
    },
    "psychology": {
        "name": "Psychology / Human Mind",
        "tone": "fascinating, relatable, insightful",
        "audience": "18-35, self-aware audience",
        "hashtags": ["#psychology", "#humanbehavior", "#mind", "#brain", "#psychologyfacts", "#bodylanguage", "#nlp"],
        "best_times": "12pm-2pm, 8pm-10pm",
        "rpm_range": "$6-14",
        "subniches": ["habits and behavior", "communication", "attention and memory", "social dynamics", "cognitive biases", "emotional literacy"],
    },
    "mystery": {
        "name": "Mysteries / Unexplained",
        "tone": "eerie, questioning, conspiratorial",
        "audience": "18-40, mystery fans",
        "hashtags": ["#mystery", "#unexplained", "#paranormal", "#conspiracy", "#strange", "#unsolved", "#cryptid"],
        "best_times": "9pm-12am",
        "rpm_range": "$5-10",
        "subniches": ["lost places", "historical mysteries", "strange artifacts", "unexplained natural events", "puzzles", "folklore mysteries"],
    },
    "unsolved_murder_mysteries": {
        "name": "Unsolved Murder Mysteries",
        "tone": "investigative, chilling, detail-oriented, respectful of victims",
        "audience": "20-45, true crime enthusiasts",
        "hashtags": ["#unsolvedmystery", "#unsolvedcase", "#murdermystery", "#coldcase", "#truecrimedaily", "#crimecase", "#detective", "#unsolvedcrime"],
        "best_times": "7pm-11pm",
        "rpm_range": "$8-18",
        "subniches": ["case timelines", "cold-case history", "investigative methods", "missing-person cases", "forensic developments", "victim remembrance"],
    },
    "daily_meditation": {
        "name": "Daily Meditation / Mindfulness",
        "tone": "calm, soothing, gentle, reassuring, slow-paced",
        "audience": "25-55, wellness seekers, stress relief",
        "hashtags": ["#meditation", "#mindfulness", "#calm", "#innerpeace", "#relax", "#breathwork", "#stressrelief", "#selfcare", "#wellness", "#guidedmeditation"],
        "best_times": "6am-8am, 8pm-10pm",
        "rpm_range": "$4-10",
        "subniches": [
            "morning grounding", "sleep wind-down", "paced breathing",
            "self-compassion", "stress reset", "mindful focus", "body scan", "gratitude",
        ],
        "is_storytelling": False,
        "voice_config": {
            "voice": "en-US-NancyNeural",
            "rate": "-25%",
            "pitch": "-2Hz",
        },
    },
}

# Extra ideas are deliberately opt-in.  They widen a channel's editorial range
# without silently changing the focused default topic pool.
OPTIONAL_SUBNICHES = {
    "scary_stories": ["quiet dread stories", "technology horror", "survival suspense", "fictional haunted objects"],
    "reddit_stories": ["roommate conflicts", "career turning points", "ethical choices", "community kindness stories"],
    "motivational": ["rebuilding after rejection", "identity-based habits", "overcoming comparison", "courageous conversations"],
    "finance": ["debt literacy", "negotiating pay", "insurance basics", "long-term investing concepts"],
    "true_crime": ["media literacy in cases", "justice-system explainers", "safety education", "case updates with verified sources"],
    "did_you_know": ["food science", "weather and earth", "animals and adaptation", "everyday technology"],
    "history": ["history myths checked", "women in history", "engineering history", "trade and exploration"],
    "space": ["night-sky guides", "space technology", "planetary geology", "science news with sources"],
    "psychology": ["decision making", "conflict repair", "learning strategies", "digital wellbeing"],
    "mystery": ["archaeological puzzles", "maritime mysteries", "lost media", "scientific unknowns"],
    "unsolved_murder_mysteries": ["responsible case updates", "evidence literacy", "historical cold cases", "missing-person resources"],
    "daily_meditation": ["transition rituals", "compassion practice", "nature visualization", "screen-break resets"],
}

# Storytelling niches — these are narrative-driven and get special treatment
STORYTELLING_NICHES = {
    "scary_stories",
    "reddit_stories",
    "true_crime",
    "unsolved_murder_mysteries",
    "history",
    "mystery",
    "did_you_know",
}

# Meditation niches — calm voice, ambient music, no Ken Burns
MEDITATION_NICHES = {
    "daily_meditation",
    "nature_relaxation",
    "asmr",
}


# ============================================================================
# SHORT-FORM SCRIPT PROMPT (15-90 seconds)
# ============================================================================

def short_form_script_prompt(
    topic: str,
    niche: str = "did_you_know",
    duration_seconds: int = 60,
    style: str = "engaging",
    extra_instructions: Optional[str] = None,
) -> str:
    """Generate the user prompt for a short-form video script."""

    niche_info = NICHES.get(niche, NICHES["did_you_know"])

    # Neural narration normally lands around 2.2--2.6 spoken words per
    # second.  A lower budget creates a video whose declared scene lengths
    # look correct but whose actual audio finishes much too early.
    target_words = max(70, round(duration_seconds * 2.25))
    segment_count = max(4, duration_seconds // 12)
    words_per_segment = max(11, round((target_words - 14) / segment_count))

    return f"""Write a {duration_seconds}-second faceless video script about: "{topic}"

NICHE: {niche_info['name']}
TONE: {niche_info['tone']}
TARGET AUDIENCE: {niche_info['audience']}
STYLE: {style}
{f'EXTRA INSTRUCTIONS: {extra_instructions}' if extra_instructions else ''}

OUTPUT FORMAT (valid JSON):
{{
    "title": "A precise, compelling title that stays faithful to the requested topic",
    "hook": "The first 1-2 sentences. Maximum impact. Must stop the scroll.",
    "segments": [
        {{
            "scene": 1,
            "narration": "What the voiceover says for this scene",
            "image_prompt": "Detailed prompt for AI image generation (what the viewer sees)",
            "duration_seconds": 8,
            "transition": "cut"
        }}
    ],
    "cta": "Call to action at the end (follow, like, comment, etc.)",
    "emotional_arc": "curiosity → tension → payoff",
    "references": [{{"title": "Source title", "url": "https://...", "claim": "The exact claim supported"}}],
    "source_review_required": false
}}

RULES:
- Each segment = 1 visual scene with voiceover
- Keep sentences SHORT (5-12 words each) for natural voiceover pacing
- Image prompts must be DESCRIPTIVE (e.g., "dark abandoned hospital hallway with flickering fluorescent lights, fog on the floor, cinematic lighting")
- The hook must create a CURIOSITY GAP — make them NEED to keep watching
- REQUIRED SPOKEN-WORD BUDGET: write at least {target_words} words across the hook and narration. The hook should be 10-16 words; each scene narration should be about {words_per_segment}-{words_per_segment + 5} spoken words. Count only words the voice will say. Do not fake duration with scene labels, image prompts, or punctuation.
- Write {segment_count}-{segment_count + 1} segments.
- Before returning JSON, silently count the hook plus narration words and expand the middle/payoff if below {target_words}.
- NO filler words. Every sentence must earn its place.
- CTA should feel natural, not forced.
- Do not use unverified quotations, generic quote-card wording, or fabricated personal stories.
- Keep the title faithful to the requested topic. Do not add unsupported numbers or generic "Did you know?" framing.
- Make one clear, specific promise in the hook and pay it off before the CTA.
- For factual, history, psychology, crime, science, or finance content: provide real, directly relevant source URLs for every material claim and set source_review_required to true. Never invent a URL.
- For original motivation or meditation with no factual claim: use an empty references array. Never make health-treatment or outcome claims."""


def topic_planner_prompt(
    niche: str, video_format: str, recent_topics: list[str] | None = None,
    enabled_subniches: list[str] | None = None,
) -> str:
    """Create one specific, original angle when the creator leaves Topic blank."""
    info = NICHES.get(niche, NICHES["motivational"])
    subniches = enabled_subniches or info.get("subniches", [])
    recent = "\n".join(f"- {item}" for item in (recent_topics or [])[-20:]) or "- None recorded"
    return f"""Plan ONE original {video_format} video idea for this channel.

NICHE: {info['name']}
SUB-NICHES TO ROTATE: {', '.join(subniches) or 'Use the channel niche'}
RECENT TOPICS — do not repeat their angle, wording, or hook:
{recent}

Return valid JSON only:
{{
  "topic": "A precise, human-sounding topic; not a generic category",
  "angle": "The fresh point of view or situation",
  "viewer_promise": "The specific value the viewer receives",
  "subniche": "One selected sub-niche"
}}

Rules:
- Pick an evergreen, safe, emotionally grounded idea.
- Avoid generic phrases such as 'amazing facts', 'change your life', or 'motivation fades'.
- For inspiration, use a relatable situation and one practical, non-medical takeaway.
- Do not invent facts, statistics, quotations, news, or personal stories."""


# ============================================================================
# LONG-FORM SCRIPT PROMPT (5-15 minutes)
# ============================================================================

def long_form_script_prompt(
    topic: str,
    niche: str = "scary_stories",
    duration_minutes: int = 10,
    style: str = "immersive",
    extra_instructions: Optional[str] = None,
) -> str:
    """Generate the user prompt for a long-form video script."""

    niche_info = NICHES.get(niche, NICHES["scary_stories"])
    num_segments = duration_minutes * 3  # ~3 segments per minute

    return f"""Write a {duration_minutes}-minute faceless video script about: "{topic}"

NICHE: {niche_info['name']}
TONE: {niche_info['tone']}
TARGET AUDIENCE: {niche_info['audience']}
STYLE: {style}
{f'EXTRA INSTRUCTIONS: {extra_instructions}' if extra_instructions else ''}

OUTPUT FORMAT (valid JSON):
{{
    "hook": "The first 2-3 sentences. Must create immediate investment.",
    "segments": [
        {{
            "scene": 1,
            "narration": "A paragraph of narration (3-6 sentences) for this scene",
            "image_prompt": "Detailed prompt for AI image generation",
            "duration_seconds": 30,
            "transition": "cut"
        }}
    ],
    "cta": "Strong call to action",
    "chapter_markers": [
        {{"title": "Chapter name", "timestamp_seconds": 0}},
        {{"title": "Chapter name", "timestamp_seconds": 120}}
    ],
    "emotional_arc": "Setup → Rising action → Climax → Resolution"
}}

RULES:
- Write {num_segments}-{num_segments + 10} segments
- Each segment should have 3-6 sentences of narration
- Include CHAPTER MARKERS with timestamps for YouTube
- Build a clear narrative arc: hook → setup → rising tension → climax → resolution
- Each segment should end on a mini-cliffhanger to maintain retention
- Image prompts must be highly descriptive and atmospheric
- Vary segment lengths: some short (15s) for pacing, some longer (45s) for depth
- Include occasional "direct address" moments: "Now, here's where it gets interesting..."
- The narration should flow NATURALLY when read aloud as voiceover"""


# ============================================================================
# METADATA GENERATION PROMPTS
# ============================================================================

def metadata_prompt(
    script_title: str,
    niche: str,
    platform: str,
    full_narration: str = "",
) -> str:
    """Generate platform-specific metadata (title, description, tags)."""

    niche_info = NICHES.get(niche, NICHES["did_you_know"])

    return f"""Generate optimized metadata for a faceless video.

VIDEO TITLE: "{script_title}"
NICHE: {niche_info['name']}
PLATFORM: {platform}
{f'NARRATION EXCERPT: {full_narration[:500]}...' if full_narration else ''}

OUTPUT FORMAT (valid JSON):
{{
    "title": "Optimized title for {platform} (max 100 chars, click-worthy but not clickbait)",
    "description": "SEO-rich description (150-300 words for YouTube, 2-3 sentences for TikTok/Reels)",
    "hashtags": ["hashtag1", "hashtag2", "..."],
    "tags": ["keyword1", "keyword2", "..."],
    "thumbnail_prompt": "Accurate, compelling visual concept for a thumbnail (if applicable)"
}}

PLATFORM RULES:
- YouTube: Clear description with relevant keywords. Only use real links supplied by the creator; never write "link in bio". Use timestamps only for long-form videos.
- TikTok: Short punchy title, 3-5 relevant hashtags in description.
- Instagram: 5-10 hashtags, engaging caption, emoji usage.
- X/Twitter: Thread-worthy caption, 1-3 hashtags max.
- Snapchat: Short title, trending sounds reference.

Return hashtags with the leading #. Use only relevant hashtags and do not keyword-stuff.
Always include the niche hashtags: {', '.join(niche_info['hashtags'][:5])}
Make the title create CURIOSITY — but don't clickbait."""


# ============================================================================
# TITLE GENERATOR PROMPT
# ============================================================================

def title_generator_prompt(
    topic: str,
    niche: str,
    count: int = 10,
) -> str:
    """Generate multiple title options."""

    niche_info = NICHES.get(niche, NICHES["did_you_know"])

    return f"""Generate {count} viral video titles for a faceless video about: "{topic}"

NICHE: {niche_info['name']}
AUDIENCE: {niche_info['audience']}

OUTPUT FORMAT (valid JSON):
{{
    "titles": [
        {{
            "title": "The title text",
            "style": "curiosity | shock | educational | emotional | question",
            "platforms": ["youtube", "tiktok", "instagram"],
            "score": 8
        }}
    ]
}}

TITLE PATTERNS TO ADAPT (only when truthful for the actual video):
1. "The Small Step That Makes Starting Easier"
2. "Why [Specific Situation] Feels So Hard — and What to Try Next"
3. "A Calmer Way to Handle [Specific Everyday Challenge]"
4. "What [Specific Lesson] Changes About [Specific Situation]"
5. "When [Relatable Moment] Happens, Try This First"
6. "The Part of [Topic] People Often Miss"
7. "[Number] Practical Ways to [Specific, Modest Outcome]"
8. "A Better Question to Ask When You Feel Stuck"
9. "What to Remember After a Difficult Week"
10. "The Quiet Skill Behind [Specific Goal]"

RULES:
- Max 100 characters for all platforms
- Create honest curiosity by naming a relatable tension and a specific payoff.
- Do not use unsupported superlatives, fear bait, fake scarcity, or phrases such as
  "they don't want you to know", "you've been lied to", or "will shock you".
- The title's promise must be answered by the script.
- Each title should target a different psychological trigger"""


# ============================================================================
# CONTENT PLAN PROMPT (full pipeline)
# ============================================================================

def full_content_plan_prompt(
    niche: str,
    platform: str = "youtube",
    count: int = 3,
) -> str:
    """Generate complete content plans: topics + scripts + metadata."""

    niche_info = NICHES.get(niche, NICHES["did_you_know"])

    return f"""Generate {count} complete content plans for faceless videos.

NICHE: {niche_info['name']}
PRIMARY PLATFORM: {platform}
AUDIENCE: {niche_info['audience']}
REVENUE TARGET: {niche_info['rpm_range']} RPM

OUTPUT FORMAT (valid JSON):
{{
    "plans": [
        {{
            "topic": "Specific video topic",
            "title": "Viral title",
            "hook": "Opening 2 sentences of the script",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "emotional_journey": "How the viewer should feel throughout",
            "cta": "Call to action",
            "hashtags": ["#tag1", "#tag2"],
            "best_posting_time": "Day + time",
            "monetization_note": "Why this video will earn money",
            "difficulty": "easy | medium | hard",
            "viral_potential": 8
        }}
    ]
}}

RULES:
- Each topic should be DIFFERENT (no overlap)
- Topics should be trending or evergreen (not time-sensitive unless dated)
- Focus on topics with HIGH RETENTION potential
- Consider what works best on {platform} specifically
- Include at least one "evergreen" topic and one "trending" topic"""


# ============================================================================
# NICHE EXPLORER PROMPT
# ============================================================================

def meditation_script_prompt(
    topic: str = "morning calm breathing",
    duration_minutes: int = 5,
    focus: str = "stress relief",
    extra_instructions: Optional[str] = None,
) -> str:
    """Generate a meditation / mindfulness voiceover script.

    The script is designed for calm, slow pacing with breathing cues.
    Images should be nature-based, slow-moving, and soothing.
    """

    return f"""Write a {duration_minutes}-minute guided meditation voiceover script.

FOCUS: {focus}
TOPIC: {topic}

The script must follow this structure:
1. Opening — Welcome the viewer, set a calm intention (30s)
2. Grounding — Guide them to notice their body, feet on the ground (30s)
3. Breathing exercise — Inhale 4 seconds, hold 4 seconds, exhale 6 seconds (repeat 3-5 cycles)
4. Body scan — Guide awareness from toes to head, releasing tension (1-2 min)
5. Visualization — Peaceful scene (forest, ocean, mountain, etc.) (1 min)
6. Affirmation — 2-3 positive affirmations repeated slowly (30s)
7. Closing — Gently bring them back, thank them, suggest returning tomorrow (30s)

OUTPUT FORMAT (valid JSON):
{{
    "hook": "Opening welcome line",
    "segments": [
        {{
            "scene": 1,
            "narration": "Calm voiceover text. Use '...' for pauses. Use [INHALE] and [EXHALE] for breathing cues.",
            "image_prompt": "Soothing nature image prompt for this scene",
            "duration_seconds": 30,
            "transition": "fade",
            "breathing_cue": false
        }}
    ],
    "cta": "Gentle closing — suggest subscribing for daily meditation",
    "affirmations": ["Affirmation 1", "Affirmation 2"]
}}

CRITICAL RULES:
- Use ELLIPSES (...) for natural pauses in the voiceover
- Use [INHALE] and [EXHALE] markers for breathing guidance
- Keep sentences SHORT and SIMPLE — this is spoken word
- Use present tense: "You are calm" not "You will be calm"
- Every image prompt must be SERENE: nature, soft light, water, sky
- NEVER use words like "hurry", "rush", "quickly", "fast"
- Use words like: gently, slowly, softly, peacefully, calmly, naturally
- The pace should feel like the viewer has ALL the time in the world
- Include a gentle breathing pattern: inhale through nose, hold, exhale through mouth
- Total duration approximately {duration_minutes} minutes"""


def niche_analysis_prompt(niche: str) -> str:
    """Deep-dive analysis of a content niche for monetization."""

    niche_info = NICHES.get(niche, {})

    return f"""Analyze the "{niche}" niche for faceless video content creation.

Provide a comprehensive analysis in valid JSON:

{{
    "niche_name": "{niche}",
    "overview": "2-3 sentence summary",
    "monetization_potential": {{
        "youtube_rpm": "$X-$Y",
        "tiktok_cpm": "$X-$Y",
        "advertiser_demand": "low | medium | high",
        "sponsorship_potential": "low | medium | high"
    }},
    "content_strategy": {{
        "optimal_length_short": "Xs-Ys",
        "optimal_length_long": "Xmin-Ymin",
        "posting_frequency": "X per day/week",
        "best_platforms": ["platform1", "platform2"]
    }},
    "topic_ideas": [
        "Specific video topic 1",
        "Specific video topic 2",
        "Specific video topic 3"
    ],
    "competitor_landscape": "Description of top creators in this niche",
    "differentiation_angle": "How to stand out",
    "risks": ["Potential risk 1", "Potential risk 2"]
}}"""
