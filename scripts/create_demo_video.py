"""Generate a demo video showing TikTok integration flow for app review."""

import time
from pathlib import Path

try:
    from moviepy import (
        ImageClip, concatenate_videoclips,
    )
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install moviepy: pip install moviepy")
    exit(1)

OUTPUT = "demo_tiktok_integration.mp4"
W, H = 1280, 720
FPS = 24


def make_frame_bg(color=(10, 10, 10)):
    """Create a background frame."""
    img = Image.new("RGB", (W, H), color)
    return img


def draw_centered_text(draw, text, y, font_size=36, fill=(255, 255, 255)):
    """Draw centered text on an image."""
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, fill=fill, font=font)
    return font


def create_title_frame():
    """Scene 1: Title screen."""
    img = make_frame_bg()
    draw = ImageDraw.Draw(img)

    # Title
    draw_centered_text(draw, "Phantom Inspiration Studio", 180, 48, (124, 92, 255))
    draw_centered_text(draw, "TikTok Integration Demo", 260, 36, (200, 200, 200))

    # Subtitle
    draw_centered_text(draw, "AI-Powered Faceless Video Creator", 340, 24, (120, 120, 120))
    draw_centered_text(draw, "Automated Video Publishing to TikTok", 390, 24, (120, 120, 120))

    return img


def create_app_ui_frame():
    """Scene 2: Show app UI with TikTok connect button."""
    img = make_frame_bg()
    draw = ImageDraw.Draw(img)

    # App title bar
    draw.rectangle([(0, 0), (W, 60)], fill=(30, 30, 30))
    draw_centered_text(draw, "Phantom Inspiration Studio", 15, 28, (255, 255, 255))

    # Sidebar
    draw.rectangle([(0, 60), (250, H)], fill=(20, 20, 25))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    sidebar_items = ["Dashboard", "Projects", "Video Creator", "Publishing", "Settings"]
    for i, item in enumerate(sidebar_items):
        y = 100 + i * 45
        color = (124, 92, 255) if item == "Publishing" else (150, 150, 150)
        draw.text((30, y), item, fill=color, font=font)

    # Main content area
    draw_centered_text(draw, "Connected Platforms", 100, 32, (255, 255, 255))

    # Platform cards
    platforms = [
        ("YouTube", (255, 0, 0), "Connected"),
        ("TikTok", (0, 0, 0), "Connect"),
        ("Instagram", (131, 58, 180), "Connect"),
        ("X / Twitter", (29, 161, 242), "Connect"),
    ]

    card_w = 220
    start_x = 300
    for i, (name, color, status) in enumerate(platforms):
        x = start_x + i * (card_w + 20)
        y = 180

        # Card background
        draw.rounded_rectangle([(x, y), (x + card_w, y + 200)], radius=10, fill=(30, 30, 35), outline=(50, 50, 55))

        # Platform color bar
        draw.rectangle([(x, y), (x + card_w, y + 6)], fill=color)

        # Platform name
        try:
            fnt = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
            fnt_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
        except:
            fnt = ImageFont.load_default()
            fnt_sm = fnt

        bbox = draw.textbbox((0, 0), name, font=fnt)
        tw = bbox[2] - bbox[0]
        draw.text((x + (card_w - tw) // 2, y + 30), name, fill=(255, 255, 255), font=fnt)

        # Status / button
        btn_color = (0, 180, 80) if status == "Connected" else (124, 92, 255)
        btn_text = status
        bbox2 = draw.textbbox((0, 0), btn_text, font=fnt_sm)
        btw = bbox2[2] - bbox2[0]
        bx = x + (card_w - btw - 20) // 2
        by = y + 130
        draw.rounded_rectangle([(bx, by), (bx + btw + 20, by + 35)], radius=5, fill=btn_color)
        draw.text((bx + 10, by + 7), btn_text, fill=(255, 255, 255), font=fnt_sm)

    # Highlight TikTok card
    tx = start_x + 1 * (card_w + 20) - 5
    draw.rounded_rectangle([(tx - 3, 177), (tx + card_w + 3, 383)], radius=12, outline=(124, 92, 255), width=3)

    # Arrow pointing to Connect button
    arrow_x = start_x + 1 * (card_w + 20) + card_w // 2
    draw_centered_text(draw, "Click to connect TikTok", 420, 20, (124, 92, 255))

    return img


def create_oauth_frame():
    """Scene 3: TikTok OAuth authorization page."""
    img = make_frame_bg((255, 255, 255))
    draw = ImageDraw.Draw(img)

    # TikTok-style auth page
    draw.rectangle([(0, 0), (W, 80)], fill=(0, 0, 0))
    draw_centered_text(draw, "TikTok", 25, 32, (255, 255, 255))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
        font_lg = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
    except:
        font = ImageFont.load_default()
        font_sm = font
        font_lg = font

    # Auth card
    cx, cy = W // 2, H // 2
    draw.rounded_rectangle([(cx - 250, cy - 180), (cx + 250, cy + 180)], radius=15, fill=(255, 255, 255), outline=(230, 230, 230))

    draw_centered_text(draw, "PhantomInspiration", cy - 150, 28, (0, 0, 0))
    draw_centered_text(draw, "wants to:", cy - 100, 20, (100, 100, 100))

    # Permissions
    perms = [
        "Upload videos to your TikTok account",
        "Post videos on your behalf",
        "Access your basic profile info",
    ]
    for i, perm in enumerate(perms):
        bbox = draw.textbbox((0, 0), perm, font=font_sm)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy - 40 + i * 35), perm, fill=(60, 60, 60), font=font_sm)
        # Checkmark
        draw.text((cx - tw // 2 - 25, cy - 42 + i * 35), "✓", fill=(0, 180, 80), font=font_sm)

    # Authorize button
    draw.rounded_rectangle([(cx - 120, cy + 100), (cx + 120, cy + 145)], radius=8, fill=(0, 0, 0))
    draw_centered_text(draw, "Authorize", cy + 108, 22, (255, 255, 255))

    # Arrow
    draw_centered_text(draw, "User clicks Authorize", cy + 180, 18, (124, 92, 255))

    return img


def create_upload_frame():
    """Scene 4: Video upload in progress."""
    img = make_frame_bg()
    draw = ImageDraw.Draw(img)

    draw_centered_text(draw, "Publishing Video to TikTok", 80, 36, (255, 255, 255))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
    except:
        font = ImageFont.load_default()
        font_sm = font

    # Upload progress card
    cx = W // 2
    draw.rounded_rectangle([(cx - 350, 160), (cx + 350, 350)], radius=12, fill=(25, 25, 30))

    draw.text((cx - 320, 180), "Video: faceless_motivation_001.mp4", fill=(200, 200, 200), font=font)
    draw.text((cx - 320, 210), "Title: 5 Habits That Changed My Life", fill=(200, 200, 200), font=font)
    draw.text((cx - 320, 240), "Tags: #motivation #faceless #shorts", fill=(200, 200, 200), font=font)

    # Progress bar background
    draw.rounded_rectangle([(cx - 320, 290), (cx + 320, 310)], radius=5, fill=(40, 40, 45))
    # Progress bar fill
    draw.rounded_rectangle([(cx - 320, 290), (cx + 200, 310)], radius=5, fill=(124, 92, 255))
    draw.text((cx - 320, 320), "Uploading... 85%", fill=(124, 92, 255), font=font_sm)

    # Steps
    steps = [
        ("1. User authorizes TikTok via Login Kit", True),
        ("2. App receives OAuth access token", True),
        ("3. Video uploaded via Content Posting API", True),
        ("4. Content published to TikTok profile", False),
    ]

    for i, (step, done) in enumerate(steps):
        y = 400 + i * 40
        color = (0, 180, 80) if done else (100, 100, 100)
        prefix = "✓" if done else "○"
        draw.text((cx - 320, y), f"{prefix} {step}", fill=color, font=font)

    return img


def create_success_frame():
    """Scene 5: Success - video published."""
    img = make_frame_bg()
    draw = ImageDraw.Draw(img)

    # Big checkmark circle
    cx, cy = W // 2, H // 2 - 60
    draw.ellipse([(cx - 60, cy - 60), (cx + 60, cy + 60)], fill=(0, 180, 80))
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except:
        font_big = ImageFont.load_default()
        font = font_big
        font_sm = font_big

    # Checkmark
    draw_centered_text(draw, "✓", cy - 40, 60, (255, 255, 255))

    draw_centered_text(draw, "Video Published Successfully!", cy + 90, 32, (255, 255, 255))
    draw_centered_text(draw, "Posted to TikTok via Content Posting API", cy + 140, 20, (150, 150, 150))

    # API details
    details = [
        "Login Kit: User authorized via OAuth 2.0 with PKCE",
        "Content Posting API: Video uploaded via FILE_UPLOAD method",
        "Scopes used: video.upload, video.publish",
        "Privacy: PUBLIC_TO_EVERYONE",
    ]
    for i, detail in enumerate(details):
        draw_centered_text(draw, detail, cy + 190 + i * 30, 14, (100, 180, 100))

    return img


def create_end_frame():
    """Scene 6: End screen."""
    img = make_frame_bg()
    draw = ImageDraw.Draw(img)

    draw_centered_text(draw, "Phantom Inspiration Studio", 220, 44, (124, 92, 255))
    draw_centered_text(draw, "AI-Powered Faceless Video Creator", 290, 24, (150, 150, 150))
    draw_centered_text(draw, "Automated Publishing Across All Platforms", 340, 20, (100, 100, 100))

    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    platforms = "YouTube  •  TikTok  •  Instagram  •  X  •  Rumble  •  Facebook"
    draw_centered_text(draw, platforms, 420, 18, (80, 80, 80))

    return img


def main():
    print("Generating demo video frames...")

    frames = [
        ("Title", create_title_frame(), 3),
        ("App UI", create_app_ui_frame(), 4),
        ("OAuth", create_oauth_frame(), 4),
        ("Upload", create_upload_frame(), 4),
        ("Success", create_success_frame(), 3),
        ("End", create_end_frame(), 3),
    ]

    clips = []
    for name, frame, duration in frames:
        print(f"  Creating {name} scene ({duration}s)...")
        frame_path = Path(f"temp_{name.lower()}.png")
        frame.save(str(frame_path))
        clip = ImageClip(str(frame_path)).with_duration(duration)
        clips.append(clip)

    print("Combining into video...")
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        OUTPUT,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="medium",
        threads=4,
    )

    # Cleanup temp files
    for name, _, _ in frames:
        Path(f"temp_{name.lower()}.png").unlink(missing_ok=True)

    print(f"\n{'=' * 50}")
    print(f"Demo video created: {OUTPUT}")
    print(f"Upload this to TikTok Developer Portal!")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
