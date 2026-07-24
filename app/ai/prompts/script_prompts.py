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
You write scripts that go VIRAL. Your scripts are:

- HOOK the viewer in the first 2 seconds
- Use short, punchy sentences (great for voiceover)
- Build curiosity gaps and cliffhangers
- Use emotional triggers (fear, wonder, surprise, humor)
- Include visual cues for image/video generation
- End with a strong call to action

You write for SHORT-FORM (15-90s) and LONG-FORM (5-15min) faceless videos.
Your tone adapts to the niche: mysterious for horror, authoritative for finance,
casual for Reddit stories, awe-inspiring for science.

NEVER use the words: "um", "uh", "so basically", "in conclusion".
ALWAYS write as if speaking directly to the viewer."""

METADATA_SYSTEM = """\
You are an expert YouTube/TikTok SEO specialist and social media strategist.
You optimize titles, descriptions, and tags for maximum discoverability and clicks.
You understand platform algorithms and what drives engagement."""

NICHES = {
    "scary_stories": {
        "name": "Scary Stories / Horror",
        "tone": "dark, suspenseful, whispery",
        "audience": "18-34, horror fans",
        "hashtags": ["#scary", "#horror", "#scarystory", "#darkstories", "#nightmares", "#creepy", "#horrorcommunity"],
        "best_times": "8pm-12am",
        "rpm_range": "$5-12",
    },
    "reddit_stories": {
        "name": "Reddit Stories",
        "tone": "casual, conversational, reactive",
        "audience": "18-30, Reddit users",
        "hashtags": ["#reddit", "#redditstories", "#redditread", "#aita", "#tifu", "#relationship", "#drama"],
        "best_times": "12pm-3pm, 7pm-10pm",
        "rpm_range": "$3-8",
    },
    "motivational": {
        "name": "Motivational / Stoicism",
        "tone": "powerful, direct, no-nonsense",
        "audience": "18-35, male-skewed",
        "hashtags": ["#motivation", "#stoicism", "#mindset", "#discipline", "#grindset", "#selfimprovement", "#philosophy"],
        "best_times": "6am-9am, 7pm-9pm",
        "rpm_range": "$8-20",
    },
    "finance": {
        "name": "Finance / Money",
        "tone": "authoritative, educational, urgent",
        "audience": "22-45, aspiring investors",
        "hashtags": ["#money", "#finance", "#investing", "#passiveincome", "#wealth", "#stocks", "#crypto"],
        "best_times": "9am-11am, 6pm-8pm",
        "rpm_range": "$15-30",
    },
    "true_crime": {
        "name": "True Crime",
        "tone": "investigative, gripping, respectful",
        "audience": "20-40, true crime fans",
        "hashtags": ["#truecrime", "#crime", "#mystery", "#unsolved", "#detective", "#criminalmind", "#casefile"],
        "best_times": "7pm-11pm",
        "rpm_range": "$6-15",
    },
    "did_you_know": {
        "name": "Did You Know / Facts",
        "tone": "curious, surprising, educational",
        "audience": "15-35, general",
        "hashtags": ["#didyouknow", "#facts", "#interesting", "#mindblown", "#factsdaily", "#learnontiktok", "#knowledge"],
        "best_times": "11am-1pm, 5pm-8pm",
        "rpm_range": "$3-7",
    },
    "history": {
        "name": "History",
        "tone": "storytelling, dramatic, educational",
        "audience": "20-45, history buffs",
        "hashtags": ["#history", "#historical", "#ancient", "#civilization", "#ww2", "#roman", "#historystory"],
        "best_times": "10am-12pm, 7pm-9pm",
        "rpm_range": "$5-12",
    },
    "space": {
        "name": "Space / Science",
        "tone": "awe-inspiring, cosmic, humbling",
        "audience": "16-40, science enthusiasts",
        "hashtags": ["#space", "#universe", "#nasa", "#cosmos", "#science", "#astronomy", "#blackhole"],
        "best_times": "8pm-11pm",
        "rpm_range": "$5-10",
    },
    "psychology": {
        "name": "Psychology / Human Mind",
        "tone": "fascinating, relatable, insightful",
        "audience": "18-35, self-aware audience",
        "hashtags": ["#psychology", "#humanbehavior", "#mind", "#brain", "#psychologyfacts", "#bodylanguage", "#nlp"],
        "best_times": "12pm-2pm, 8pm-10pm",
        "rpm_range": "$6-14",
    },
    "mystery": {
        "name": "Mysteries / Unexplained",
        "tone": "eerie, questioning, conspiratorial",
        "audience": "18-40, mystery fans",
        "hashtags": ["#mystery", "#unexplained", "#paranormal", "#conspiracy", "#strange", "#unsolved", "#cryptid"],
        "best_times": "9pm-12am",
        "rpm_range": "$5-10",
    },
    "unsolved_murder_mysteries": {
        "name": "Unsolved Murder Mysteries",
        "tone": "investigative, chilling, detail-oriented, respectful of victims",
        "audience": "20-45, true crime enthusiasts",
        "hashtags": ["#unsolvedmystery", "#unsolvedcase", "#murdermystery", "#coldcase", "#truecrimedaily", "#crimecase", "#detective", "#unsolvedcrime"],
        "best_times": "7pm-11pm",
        "rpm_range": "$8-18",
    },
    "daily_meditation": {
        "name": "Daily Meditation / Mindfulness",
        "tone": "calm, soothing, gentle, reassuring, slow-paced",
        "audience": "25-55, wellness seekers, stress relief",
        "hashtags": ["#meditation", "#mindfulness", "#calm", "#innerpeace", "#relax", "#breathwork", "#stressrelief", "#selfcare", "#wellness", "#guidedmeditation"],
        "best_times": "6am-8am, 8pm-10pm",
        "rpm_range": "$4-10",
        "is_storytelling": False,
        "voice_config": {
            "voice": "en-US-NancyNeural",
            "rate": "-25%",
            "pitch": "-2Hz",
        },
    },
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

    return f"""Write a {duration_seconds}-second faceless video script about: "{topic}"

NICHE: {niche_info['name']}
TONE: {niche_info['tone']}
TARGET AUDIENCE: {niche_info['audience']}
STYLE: {style}
{f'EXTRA INSTRUCTIONS: {extra_instructions}' if extra_instructions else ''}

OUTPUT FORMAT (valid JSON):
{{
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
    "emotional_arc": "curiosity → tension → payoff"
}}

RULES:
- Each segment = 1 visual scene with voiceover
- Keep sentences SHORT (5-12 words each) for natural voiceover pacing
- Image prompts must be DESCRIPTIVE (e.g., "dark abandoned hospital hallway with flickering fluorescent lights, fog on the floor, cinematic lighting")
- The hook must create a CURIOSITY GAP — make them NEED to keep watching
- Total duration must be approximately {duration_seconds} seconds
- Write {max(3, duration_seconds // 15)}-{max(5, duration_seconds // 10)} segments
- NO filler words. Every sentence must earn its place.
- CTA should feel natural, not forced."""


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
    "thumbnail_prompt": "AI image prompt for a clickbait thumbnail (if applicable)"
}}

PLATFORM RULES:
- YouTube: Long description with keywords, timestamps, and links. 15-30 tags.
- TikTok: Short punchy title, 3-5 relevant hashtags in description.
- Instagram: 5-10 hashtags, engaging caption, emoji usage.
- X/Twitter: Thread-worthy caption, 1-3 hashtags max.
- Snapchat: Short title, trending sounds reference.

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

TITLE FORMULAS THAT WORK:
1. "I Tried [X] for [Time] — Here's What Happened"
2. "10 [Niche] Facts That Will Change How You Think"
3. "The Dark Truth About [Topic] Nobody Talks About"
4. "Why [Thing] Is Actually Terrifying"
5. "You've Been Lied To About [Topic]"
6. "The [Topic] Story They Don't Want You to Know"
7. "What Happens When [X]? (The Answer Will Shock You)"
8. "[Number] Things About [Topic] That Sound Fake But Are 100% Real"
9. "Nobody Talks About [Topic] and It's Scary"
10. "The Most [Adjective] [Niche] You'll See Today"

RULES:
- Max 100 characters for all platforms
- Create a CURIOSITY GAP (make them NEED to click)
- Avoid pure clickbait — deliver on the promise
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
