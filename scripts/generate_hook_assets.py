#!/usr/bin/env python3
"""
Generate custom visual assets for the Frank Olson hook (first 30 seconds).

Assets created:
1. glass_shatter.png — Shattering window with glass shards flying outward
2. hotel_facade_tall.png — Tall hotel building at night (for fast pan-down fall effect)
3. frank_olson_namecard.png — Memorial-style name card (white serif on dark)
4. hotel_window_lit.png — Dark building exterior with single lit window on 10th floor

All output is 1920x1080 (or taller for pan effects), dark palette.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Config ────────────────────────────────────────────────────────────────────

W, H = 1920, 1080
OUT_DIR = Path("footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/hook_assets")

# Colors
NIGHT_SKY     = (8, 10, 18)
BUILDING_DARK = (14, 16, 22)
BUILDING_MID  = (20, 22, 30)
WINDOW_LIT    = (255, 220, 140)      # warm lit window
WINDOW_DIM    = (40, 45, 55)         # dim unlit window
GLASS_WHITE   = (220, 230, 255)      # glass shard color
GLASS_BLUE    = (140, 170, 220)      # glass tint
TEXT_WHITE    = (235, 230, 222)      # warm off-white
TEXT_GREY     = (140, 135, 128)      # secondary text
TEXT_MUTED    = (90, 85, 78)         # tertiary text

# Fonts
FONT_SERIF = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Times New Roman.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]
FONT_SANS = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _add_noise(img, intensity=6):
    """Add subtle film grain."""
    pixels = img.load()
    w, h = img.size
    for _ in range(w * h // 15):
        px = random.randint(0, w - 1)
        py = random.randint(0, h - 1)
        r, g, b = pixels[px, py][:3]
        d = random.randint(-intensity, intensity)
        pixels[px, py] = (
            max(0, min(255, r + d)),
            max(0, min(255, g + d)),
            max(0, min(255, b + d)),
        )
    return img


def _vignette(draw, w, h, strength=80):
    """Draw dark vignette border."""
    for i in range(80):
        alpha = int(strength * (1 - i / 80))
        draw.rectangle([i, i, w - i, h - i], outline=(0, 0, 0))


# ── Asset 1: Glass Shatter ───────────────────────────────────────────────────

def make_glass_shatter():
    """
    Shattering window — glass shards flying outward from center.
    Dark blue-black background with white/blue glass fragments radiating out.
    A dark silhouette figure visible behind the shatter point.
    """
    img = Image.new("RGB", (W, H), NIGHT_SKY)
    draw = ImageDraw.Draw(img)

    # Dark hotel room interior visible through broken window
    # Window frame
    frame_x, frame_y = W // 2, H // 2
    frame_w, frame_h = 600, 500

    # Dark room behind window
    draw.rectangle(
        [frame_x - frame_w // 2, frame_y - frame_h // 2,
         frame_x + frame_w // 2, frame_y + frame_h // 2],
        fill=(6, 6, 10)
    )

    # Window frame border
    for thickness in range(4):
        draw.rectangle(
            [frame_x - frame_w // 2 - thickness, frame_y - frame_h // 2 - thickness,
             frame_x + frame_w // 2 + thickness, frame_y + frame_h // 2 + thickness],
            outline=(35, 35, 45)
        )

    # Venetian blind remnants (partially intact — key forensic detail)
    blind_y_start = frame_y - frame_h // 2 + 20
    for i in range(8):
        y = blind_y_start + i * 25
        if i < 3:  # top blinds still intact
            draw.rectangle(
                [frame_x - frame_w // 2 + 15, y,
                 frame_x + frame_w // 2 - 15, y + 12],
                fill=(45, 42, 38)
            )
        else:  # lower blinds broken/dangling
            offset = random.randint(-30, 30)
            angle_len = random.randint(80, 200)
            draw.line(
                [(frame_x - frame_w // 2 + 15 + offset, y),
                 (frame_x - frame_w // 2 + 15 + offset + angle_len, y + random.randint(5, 30))],
                fill=(45, 42, 38), width=2
            )

    # Glass shards radiating outward from impact point
    impact_x = frame_x + random.randint(-50, 50)
    impact_y = frame_y + random.randint(-30, 30)

    # Large shards
    for _ in range(35):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(30, 350)
        shard_x = impact_x + math.cos(angle) * dist
        shard_y = impact_y + math.sin(angle) * dist

        # Shard shape — elongated triangle
        shard_len = random.randint(15, 80)
        shard_width = random.randint(3, 20)
        shard_angle = angle + random.uniform(-0.3, 0.3)

        points = [
            (shard_x, shard_y),
            (shard_x + math.cos(shard_angle) * shard_len,
             shard_y + math.sin(shard_angle) * shard_len),
            (shard_x + math.cos(shard_angle + 0.5) * shard_width,
             shard_y + math.sin(shard_angle + 0.5) * shard_width),
        ]

        # Color varies from white to blue-white
        brightness = random.randint(160, 255)
        blue_tint = random.randint(0, 40)
        color = (brightness - blue_tint, brightness - blue_tint // 2, brightness)
        draw.polygon(points, fill=color)

    # Small glass particles (dust)
    for _ in range(200):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(10, 400)
        px = int(impact_x + math.cos(angle) * dist)
        py = int(impact_y + math.sin(angle) * dist)
        if 0 <= px < W and 0 <= py < H:
            size = random.randint(1, 4)
            brightness = random.randint(140, 255)
            draw.ellipse([px - size, py - size, px + size, py + size],
                        fill=(brightness, brightness, min(255, brightness + 20)))

    # Crack lines radiating from impact
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        crack_len = random.randint(100, 280)
        points = [(impact_x, impact_y)]
        cx, cy = impact_x, impact_y
        for seg in range(random.randint(3, 8)):
            cx += math.cos(angle + random.uniform(-0.4, 0.4)) * (crack_len // 5)
            cy += math.sin(angle + random.uniform(-0.4, 0.4)) * (crack_len // 5)
            points.append((cx, cy))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]],
                     fill=GLASS_WHITE, width=random.randint(1, 3))

    # Dark silhouette of falling figure (subtle)
    fig_x = impact_x - 20
    fig_y = impact_y + 40
    # Simple falling human shape
    # Head
    draw.ellipse([fig_x - 10, fig_y - 60, fig_x + 10, fig_y - 40], fill=(3, 3, 6))
    # Torso
    draw.rectangle([fig_x - 15, fig_y - 40, fig_x + 15, fig_y + 10], fill=(3, 3, 6))
    # Arms splayed
    draw.line([(fig_x - 15, fig_y - 30), (fig_x - 45, fig_y - 10)], fill=(3, 3, 6), width=6)
    draw.line([(fig_x + 15, fig_y - 30), (fig_x + 45, fig_y - 10)], fill=(3, 3, 6), width=6)
    # Legs
    draw.line([(fig_x - 5, fig_y + 10), (fig_x - 20, fig_y + 50)], fill=(3, 3, 6), width=6)
    draw.line([(fig_x + 5, fig_y + 10), (fig_x + 20, fig_y + 50)], fill=(3, 3, 6), width=6)

    _vignette(draw, W, H, strength=100)
    _add_noise(img, intensity=8)

    out = OUT_DIR / "glass_shatter.png"
    img.save(out, "PNG")
    print(f"  Created: {out} ({img.size[0]}x{img.size[1]})")
    return out


# ── Asset 2: Hotel Facade (tall for pan-down) ────────────────────────────────

def make_hotel_facade_tall():
    """
    Tall hotel building at night — for fast pan_down (the fall effect).
    Image is 1920x5400 (3x height) so Ken Burns can pan from top to bottom.
    """
    tall_h = 5400  # 3x normal height for fast pan
    img = Image.new("RGB", (W, tall_h), NIGHT_SKY)
    draw = ImageDraw.Draw(img)

    # Night sky gradient at top
    for y in range(400):
        factor = y / 400
        r = int(NIGHT_SKY[0] * (1 - factor) + 5 * factor)
        g = int(NIGHT_SKY[1] * (1 - factor) + 5 * factor)
        b = int(NIGHT_SKY[2] * (1 - factor) + 15 * factor)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Main hotel building (center)
    bldg_x = W // 2 - 350
    bldg_w = 700
    bldg_top = 200
    bldg_bottom = tall_h - 200

    # Building body
    draw.rectangle([bldg_x, bldg_top, bldg_x + bldg_w, bldg_bottom],
                   fill=BUILDING_DARK)

    # Building edges (lighter) for depth
    draw.rectangle([bldg_x, bldg_top, bldg_x + 3, bldg_bottom],
                   fill=BUILDING_MID)
    draw.rectangle([bldg_x + bldg_w - 3, bldg_top, bldg_x + bldg_w, bldg_bottom],
                   fill=BUILDING_MID)

    # Art deco details at top
    for i in range(5):
        y = bldg_top + i * 8
        draw.rectangle([bldg_x + 10, y, bldg_x + bldg_w - 10, y + 3],
                       fill=(30, 32, 40))

    # Windows — grid pattern, most dark, some lit
    window_w, window_h = 28, 40
    window_gap_x, window_gap_y = 50, 60
    floor_count = 0

    for wy in range(bldg_top + 100, bldg_bottom - 100, window_gap_y):
        floor_count += 1
        for wx in range(bldg_x + 40, bldg_x + bldg_w - 40, window_gap_x):
            # Most windows dark, some dimly lit, rare bright
            roll = random.random()
            if floor_count == 10 and abs(wx - (bldg_x + bldg_w // 2)) < 60:
                # The 10th floor target window — brightly lit
                color = WINDOW_LIT
            elif roll < 0.08:
                # Bright window
                brightness = random.randint(150, 220)
                color = (brightness, brightness - 20, brightness - 60)
            elif roll < 0.25:
                # Dim window
                color = WINDOW_DIM
            else:
                # Dark window
                color = (18, 20, 26)

            draw.rectangle([wx, wy, wx + window_w, wy + window_h], fill=color)
            # Window frame
            draw.rectangle([wx, wy, wx + window_w, wy + window_h],
                          outline=(25, 27, 35), width=1)

    # Street level at bottom
    street_y = bldg_bottom
    draw.rectangle([0, street_y, W, tall_h], fill=(15, 15, 18))

    # Street lamps
    for lamp_x in [200, 500, 800, 1120, 1420, 1720]:
        # Pole
        draw.line([(lamp_x, street_y - 200), (lamp_x, street_y + 30)],
                 fill=(50, 50, 55), width=3)
        # Light glow
        for r in range(30, 0, -1):
            alpha = int(40 * (r / 30))
            color = (255 - alpha, 200 - alpha, 100 - alpha * 2)
            draw.ellipse([lamp_x - r, street_y - 210 - r,
                         lamp_x + r, street_y - 210 + r],
                        fill=color)

    # Sidewalk
    draw.rectangle([0, street_y + 30, W, street_y + 60], fill=(25, 25, 28))

    # Adjacent buildings (shorter, flanking)
    for side_x, side_w, side_top in [(0, bldg_x - 30, 800), (bldg_x + bldg_w + 30, W, 600)]:
        draw.rectangle([side_x, side_top, side_w, bldg_bottom], fill=(12, 14, 18))
        # Windows
        for wy in range(side_top + 60, bldg_bottom - 60, 55):
            for wx in range(side_x + 20, side_w - 20, 45):
                if random.random() < 0.15:
                    b = random.randint(30, 60)
                    draw.rectangle([wx, wy, wx + 22, wy + 35], fill=(b, b, b + 10))

    _add_noise(img, intensity=5)

    out = OUT_DIR / "hotel_facade_tall.png"
    img.save(out, "PNG")
    print(f"  Created: {out} ({img.size[0]}x{img.size[1]})")
    return out


# ── Asset 3: Hotel Window Lit ─────────────────────────────────────────────────

def make_hotel_window_lit():
    """
    Looking UP at a dark building from street level.
    Single lit window on the 10th floor. Foreboding atmosphere.
    """
    img = Image.new("RGB", (W, H), NIGHT_SKY)
    draw = ImageDraw.Draw(img)

    # Building face — looking up, perspective converging toward top
    bldg_left_bottom = 200
    bldg_right_bottom = W - 200
    bldg_left_top = 450
    bldg_right_top = W - 450

    # Draw building as trapezoid (perspective looking up)
    draw.polygon([
        (bldg_left_bottom, H),
        (bldg_right_bottom, H),
        (bldg_right_top, 50),
        (bldg_left_top, 50),
    ], fill=BUILDING_DARK)

    # Window rows (getting smaller toward top = perspective)
    floors = 13
    for floor in range(floors):
        # Interpolate position for perspective
        t = floor / floors
        y = H - 80 - (H - 130) * t
        row_left = int(bldg_left_bottom + (bldg_left_top - bldg_left_bottom) * t) + 30
        row_right = int(bldg_right_bottom + (bldg_right_top - bldg_right_bottom) * t) - 30
        row_width = row_right - row_left

        win_w = max(8, int(28 * (1 - t * 0.5)))
        win_h = max(10, int(40 * (1 - t * 0.5)))
        win_count = max(3, int(row_width / (win_w + 20)))

        for wi in range(win_count):
            wx = row_left + int((row_width / win_count) * wi + (row_width / win_count - win_w) / 2)

            if floor == 9:  # 10th floor (0-indexed)
                if wi == win_count // 2:  # center window = THE window
                    # Brightly lit — the target
                    draw.rectangle([wx, int(y) - win_h, wx + win_w, int(y)],
                                  fill=WINDOW_LIT)
                    # Glow effect
                    for r in range(20, 0, -1):
                        glow_alpha = int(30 * (r / 20))
                        draw.ellipse([wx - r + win_w // 2, int(y) - win_h // 2 - r,
                                     wx + win_w + r - win_w // 2, int(y) - win_h // 2 + r],
                                    fill=(255 - glow_alpha * 3, 220 - glow_alpha * 3, 140 - glow_alpha * 3))
                else:
                    draw.rectangle([wx, int(y) - win_h, wx + win_w, int(y)],
                                  fill=WINDOW_DIM if random.random() < 0.2 else (18, 20, 26))
            else:
                roll = random.random()
                if roll < 0.06:
                    b = random.randint(100, 180)
                    color = (b, b - 15, b - 40)
                elif roll < 0.2:
                    color = WINDOW_DIM
                else:
                    color = (18, 20, 26)
                draw.rectangle([wx, int(y) - win_h, wx + win_w, int(y)], fill=color)

    # Floor number label near lit window (subtle)
    font_small = _font(FONT_SANS, 14)
    # Find the 10th floor y position
    t10 = 9 / floors
    y10 = H - 80 - (H - 130) * t10

    _vignette(draw, W, H, strength=120)
    _add_noise(img, intensity=8)

    out = OUT_DIR / "hotel_window_lit.png"
    img.save(out, "PNG")
    print(f"  Created: {out} ({img.size[0]}x{img.size[1]})")
    return out


# ── Asset 4: Frank Olson Name Card ────────────────────────────────────────────

def make_frank_olson_namecard():
    """
    Memorial-style name card. White serif on near-black.
    Simple, solemn, powerful.
    """
    img = Image.new("RGB", (W, H), (8, 8, 10))
    draw = ImageDraw.Draw(img)

    # Subtle gradient toward center (lighter)
    for y in range(H):
        for x in range(0, W, 3):
            dist = math.sqrt((x - W / 2) ** 2 + (y - H / 2) ** 2)
            max_dist = math.sqrt((W / 2) ** 2 + (H / 2) ** 2)
            factor = max(0, 1 - dist / max_dist) * 0.15
            r, g, b = img.getpixel((x, y))
            new_val = int(min(255, r + factor * 30))
            draw.point((x, y), fill=(new_val, new_val, new_val + 1))

    # Main name
    name_font = _font(FONT_SERIF, 72)
    name = "FRANK OLSON"
    try:
        bbox = name_font.getbbox(name)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except AttributeError:
        tw, th = len(name) * 40, 72

    name_x = (W - tw) // 2
    name_y = H // 2 - th - 30
    draw.text((name_x, name_y), name, font=name_font, fill=TEXT_WHITE)

    # Thin rule below name
    rule_y = name_y + th + 20
    rule_w = min(tw + 40, 600)
    draw.line([(W // 2 - rule_w // 2, rule_y), (W // 2 + rule_w // 2, rule_y)],
              fill=TEXT_MUTED, width=1)

    # Dates
    date_font = _font(FONT_SERIF, 32)
    dates = "1910 — 1953"
    try:
        bbox = date_font.getbbox(dates)
        dtw = bbox[2] - bbox[0]
    except AttributeError:
        dtw = len(dates) * 18
    draw.text(((W - dtw) // 2, rule_y + 20), dates, font=date_font, fill=TEXT_GREY)

    # Title
    title_font = _font(FONT_SANS, 22)
    title = "U.S. ARMY BIOCHEMIST  •  FORT DETRICK, MARYLAND"
    try:
        bbox = title_font.getbbox(title)
        ttw = bbox[2] - bbox[0]
    except AttributeError:
        ttw = len(title) * 12
    draw.text(((W - ttw) // 2, rule_y + 70), title, font=title_font, fill=TEXT_MUTED)

    _vignette(draw, W, H, strength=60)
    _add_noise(img, intensity=4)

    out = OUT_DIR / "frank_olson_namecard.png"
    img.save(out, "PNG")
    print(f"  Created: {out} ({img.size[0]}x{img.size[1]})")
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating hook assets for first 30 seconds...\n")

    print("[1/4] Glass shatter (the crash moment)...")
    make_glass_shatter()

    print("[2/4] Hotel facade tall (for pan-down fall effect)...")
    make_hotel_facade_tall()

    print("[3/4] Hotel window lit (looking up, single lit window)...")
    make_hotel_window_lit()

    print("[4/4] Frank Olson name card...")
    make_frank_olson_namecard()

    print(f"\nAll assets saved to: {OUT_DIR}")
    print("Next: wire these into the storyboard for the first 30 seconds")


if __name__ == "__main__":
    main()
