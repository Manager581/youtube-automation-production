#!/usr/bin/env python3
"""
Render the first 30 seconds of Frank Olson documentary.

Creates all visuals from scratch (Pillow compositions + real archival photos),
applies parallax depth motion, adds text overlays, and composites with
voice narration + SFX + music using ffmpeg.

NO stock footage. Real photos where they exist, hand-crafted compositions where they don't.

Usage:
    PYTORCH_ENABLE_MPS_FALLBACK=1 venv/bin/python scripts/render_hook_30s.py
"""

import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080
FPS = 30
OUTPUT_PATH = os.path.join(BASE_DIR, "output/frank_olson_hook_30s.mp4")

IMAGE_DIR = os.path.join(
    BASE_DIR,
    "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"
)
SFX_DIR = os.path.join(BASE_DIR, "assets/sfx")
MUSIC_PATH = os.path.join(BASE_DIR, "assets/music/track.mp3")
VOICE_PATH = os.path.join(BASE_DIR, "audio/frank_olson/narration.wav")

# Created images go here
CREATED_DIR = os.path.join(BASE_DIR, "output/hook_assets")


# ── Color Palettes ────────────────────────────────────────────────────────────

NIGHT_BLUE = (10, 12, 28)
COLD_BLUE = (15, 20, 45)
WARM_AMBER = (45, 35, 20)
DARK_BG = (8, 8, 12)
WHITE = (255, 255, 255)
OFF_WHITE = (220, 220, 210)
WINDOW_GLOW = (200, 180, 120)
MOON_BLUE = (80, 100, 160)


# ── Font Helpers ──────────────────────────────────────────────────────────────

def get_font(size, bold=False):
    """Get a serif font, falling back through options."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/NewYork.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def get_mono_font(size):
    """Monospace font for typewriter effect."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Courier.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── Image Creators ────────────────────────────────────────────────────────────
# These create stylized compositions — NOT photorealistic, NOT stock.
# Think: Magnates Media / documentary motion graphics style.

def create_olson_dead(olson_img):
    """Olson portrait with red X's over eyes — 'how he died'."""
    img = olson_img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Eye region — portrait is 768x1024, head slightly turned right
    # Eyes at ~40% from top; left eye ~38% horiz, right eye ~53% horiz
    eye_y = int(h * 0.40)
    left_eye_x = int(w * 0.38)
    right_eye_x = int(w * 0.53)
    x_size = int(w * 0.07)  # size of each X arm (bigger for drama)
    stroke = max(6, int(w * 0.018))
    red = (200, 30, 30)
    for ex, ey in [(left_eye_x, eye_y), (right_eye_x, eye_y)]:
        draw.line([(ex - x_size, ey - x_size), (ex + x_size, ey + x_size)],
                  fill=red, width=stroke)
        draw.line([(ex + x_size, ey - x_size), (ex - x_size, ey + x_size)],
                  fill=red, width=stroke)
    return img

def create_nyc_skyline():
    """Dark 1950s Manhattan skyline at night. City lights glowing."""
    img = Image.new("RGB", (W * 2, H * 2), NIGHT_BLUE)  # 2x for parallax margin
    draw = ImageDraw.Draw(img)
    w2, h2 = W * 2, H * 2

    # Sky gradient (dark blue to slightly lighter at horizon)
    for y in range(h2):
        t = y / h2
        r = int(NIGHT_BLUE[0] + t * 15)
        g = int(NIGHT_BLUE[1] + t * 18)
        b = int(NIGHT_BLUE[2] + t * 25)
        draw.line([(0, y), (w2, y)], fill=(r, g, b))

    # Moon glow (subtle)
    for r_size in range(120, 0, -3):
        alpha = int(15 * (r_size / 120))
        c = (NIGHT_BLUE[0] + alpha, NIGHT_BLUE[1] + alpha + 5, NIGHT_BLUE[2] + alpha + 15)
        draw.ellipse([w2 - 400 - r_size, 100 - r_size, w2 - 400 + r_size, 100 + r_size], fill=c)
    # Moon disc
    draw.ellipse([w2 - 430, 70, w2 - 370, 130], fill=(180, 190, 210))

    # Building silhouettes (irregular NYC skyline)
    horizon = int(h2 * 0.55)
    buildings = []
    x = 0
    rng = random.Random(42)  # Deterministic
    while x < w2:
        bw = rng.randint(30, 120)
        bh = rng.randint(100, 700)
        if rng.random() < 0.15:
            bh = rng.randint(500, 900)
        buildings.append((x, bw, bh))
        x += bw + rng.randint(0, 8)

    for bx, bw, bh in buildings:
        top = horizon - bh
        shade = rng.randint(5, 20)
        draw.rectangle([bx, top, bx + bw, horizon + 200], fill=(shade, shade, shade + 5))

        # Windows (yellow dots)
        for wy in range(top + 15, horizon - 10, 18):
            for wx in range(bx + 6, bx + bw - 6, 14):
                if rng.random() < 0.35:
                    brightness = rng.randint(150, 230)
                    wc = (brightness, brightness - 30, brightness - 80)
                    draw.rectangle([wx, wy, wx + 5, wy + 8], fill=wc)

    # Street level glow
    for y in range(horizon, min(horizon + 80, h2)):
        t = (y - horizon) / 80
        glow = int(20 * (1 - t))
        draw.line([(0, y), (w2, y)],
                  fill=(NIGHT_BLUE[0] + glow, NIGHT_BLUE[1] + glow, NIGHT_BLUE[2] + glow // 2))

    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    return img


def create_hotel_facade():
    """Art deco hotel facade at night. One window lit on the 10th floor."""
    img = Image.new("RGB", (W * 2, H * 2), NIGHT_BLUE)
    draw = ImageDraw.Draw(img)
    w2, h2 = W * 2, H * 2

    bld_left = w2 // 2 - 500
    bld_right = w2 // 2 + 500
    bld_top = 50
    bld_bot = h2

    # Main building body
    draw.rectangle([bld_left, bld_top, bld_right, bld_bot], fill=(18, 18, 22))

    # Art deco vertical lines
    for x in range(bld_left, bld_right, 80):
        draw.line([(x, bld_top), (x, bld_bot)], fill=(25, 25, 30), width=2)

    # Horizontal floor separators
    floor_h = (bld_bot - bld_top) // 14
    for i in range(15):
        y = bld_top + i * floor_h
        draw.line([(bld_left, y), (bld_right, y)], fill=(30, 30, 35), width=2)

    rng = random.Random(99)
    for floor in range(14):
        fy = bld_top + floor * floor_h + 15
        for col in range(12):
            wx = bld_left + 30 + col * 78
            win_w, win_h = 35, floor_h - 30

            if floor == 10 and col == 6:
                # THE LIT WINDOW
                draw.rectangle([wx, fy, wx + win_w, fy + win_h], fill=(200, 170, 100))
                for g in range(40, 0, -2):
                    gc = (NIGHT_BLUE[0] + g // 3, NIGHT_BLUE[1] + g // 3, NIGHT_BLUE[2] + g // 6)
                    draw.rectangle([wx - g, fy - g, wx + win_w + g, fy + win_h + g], outline=gc)
            else:
                if rng.random() < 0.08:
                    c = rng.randint(20, 40)
                    draw.rectangle([wx, fy, wx + win_w, fy + win_h], fill=(c, c - 5, c - 10))
                else:
                    draw.rectangle([wx, fy, wx + win_w, fy + win_h], fill=(12, 12, 16))

    # Art deco ornament at top
    cx = w2 // 2
    draw.polygon([(cx - 60, bld_top), (cx, bld_top - 80), (cx + 60, bld_top)], fill=(25, 25, 30))

    # Hotel sign
    sign_y = bld_top + 2 * floor_h
    font = get_font(48, bold=True)
    draw.text((cx, sign_y), "HOTEL STATLER", fill=(120, 110, 90), font=font, anchor="mm")

    # Street level
    draw.rectangle([0, h2 - 100, w2, h2], fill=(8, 8, 10))
    for sx in range(200, w2, 400):
        draw.ellipse([sx - 15, h2 - 120, sx + 15, h2 - 90], fill=(180, 160, 100))
        draw.line([(sx, h2 - 90), (sx, h2 - 40)], fill=(60, 60, 60), width=4)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    return img


def create_glass_shatter_frames(num_frames=30):
    """Create glass shattering animation frames."""
    frames = []
    rng = random.Random(77)
    num_shards = 40
    shards = []
    for _ in range(num_shards):
        cx = W // 2 + rng.randint(-200, 200)
        cy = H // 2 + rng.randint(-150, 150)
        size = rng.randint(15, 80)
        vx = (cx - W // 2) * 0.05 + rng.uniform(-8, 8)
        vy = (cy - H // 2) * 0.05 + rng.uniform(-5, 10)
        pts = []
        n_pts = rng.randint(3, 6)
        for i in range(n_pts):
            a = (2 * math.pi * i / n_pts) + rng.uniform(-0.5, 0.5)
            r = size * rng.uniform(0.4, 1.0)
            pts.append((r * math.cos(a), r * math.sin(a)))
        launch_delay = rng.uniform(0, 0.15)
        brightness = rng.randint(150, 255)
        shards.append({
            "cx": cx, "cy": cy, "pts": pts, "vx": vx, "vy": vy,
            "rot_speed": rng.uniform(-0.2, 0.2), "size": size,
            "launch": launch_delay, "brightness": brightness,
        })

    for frame_i in range(num_frames):
        t = frame_i / max(1, num_frames - 1)
        img = Image.new("RGB", (W, H), DARK_BG)
        draw = ImageDraw.Draw(img)

        # Window frame
        frame_color = (40, 40, 50)
        for x in [W // 2 - 150, W // 2, W // 2 + 150]:
            draw.line([(x, H // 4), (x, 3 * H // 4)], fill=frame_color, width=6)
        for y in [H // 4, H // 2, 3 * H // 4]:
            draw.line([(W // 2 - 200, y), (W // 2 + 200, y)], fill=frame_color, width=6)

        # Dark silhouette behind glass
        if t < 0.5:
            sa = int(150 * (1 - 2 * t))
            sx, sy = W // 2 + 20, H // 2 - 50
            sc = (sa // 10, sa // 10, sa // 8)
            draw.ellipse([sx - 30, sy - 80, sx + 30, sy - 20], fill=sc)
            draw.rectangle([sx - 25, sy - 20, sx + 25, sy + 80], fill=sc)

        # Flying shards
        for s in shards:
            if t < s["launch"]:
                continue
            ease_t = ((t - s["launch"]) / (1 - s["launch"])) ** 0.7
            x = s["cx"] + s["vx"] * ease_t * 40
            y = s["cy"] + s["vy"] * ease_t * 40 + 200 * ease_t ** 2
            rot = s["rot_speed"] * ease_t * 10

            alpha = max(0, 1.0 - max(0, t - 0.6) / 0.4)
            if alpha <= 0:
                continue

            pts = []
            for px, py in s["pts"]:
                rx = px * math.cos(rot) - py * math.sin(rot) + x
                ry = px * math.sin(rot) + py * math.cos(rot) + y
                pts.append((rx, ry))
            if len(pts) >= 3:
                b = int(s["brightness"] * alpha)
                gc = (b, b, min(255, b + 30))
                draw.polygon(pts, fill=gc, outline=(int(255 * alpha), int(255 * alpha), int(255 * alpha)))

        # Flash at impact
        if frame_i < 3:
            flash = Image.new("RGB", (W, H),
                              (200 - frame_i * 60, 200 - frame_i * 60, 220 - frame_i * 60))
            img = Image.blend(img, flash, 0.3 - frame_i * 0.1)

        frames.append(img)
    return frames


def create_building_fall():
    """Tall building facade for fast downward pan — BRIGHT enough to read."""
    tall_h = H * 6
    img = Image.new("RGB", (W * 2, tall_h), (25, 28, 45))
    draw = ImageDraw.Draw(img)
    w2 = W * 2
    bld_left, bld_right = 150, w2 - 150

    rng = random.Random(55)

    # Building body — dark grey-brown brick, NOT black
    draw.rectangle([bld_left, 0, bld_right, tall_h], fill=(50, 45, 42))

    # Brick texture — visible horizontal lines
    for y in range(0, tall_h, 14):
        shade = rng.randint(42, 60)
        draw.line([(bld_left, y), (bld_right, y)], fill=(shade, shade - 3, shade - 5), width=1)

    # Vertical mortar lines (art deco columns)
    for x in range(bld_left, bld_right, 120):
        draw.line([(x, 0), (x, tall_h)], fill=(60, 55, 52), width=3)

    # Windows — MUCH brighter, more of them lit
    for floor in range(tall_h // 80):
        fy = floor * 80 + 15
        # Floor separator — visible ledge
        draw.rectangle([bld_left, fy - 5, bld_right, fy], fill=(65, 60, 55))
        for col in range((bld_right - bld_left) // 90):
            wx = bld_left + 25 + col * 90
            win_w, win_h = 45, 55
            if rng.random() < 0.3:  # 30% lit (was 12%)
                brightness = rng.randint(120, 200)
                wc = (brightness, brightness - 20, brightness - 60)
                draw.rectangle([wx, fy, wx + win_w, fy + win_h], fill=wc)
                # Window glow halo
                for g in range(8, 0, -2):
                    gc = (wc[0] // 6, wc[1] // 6, wc[2] // 4)
                    draw.rectangle([wx - g, fy - g, wx + win_w + g, fy + win_h + g], outline=gc)
            else:
                # Dark window — still slightly visible
                draw.rectangle([wx, fy, wx + win_w, fy + win_h], fill=(22, 22, 30))
                # Window frame
                draw.rectangle([wx, fy, wx + win_w, fy + win_h], outline=(40, 38, 36))

    # Street at bottom — warm streetlight glow
    street_y = tall_h - 300
    # Sidewalk
    draw.rectangle([0, street_y, w2, tall_h], fill=(35, 33, 30))
    # Road
    draw.rectangle([0, street_y + 80, w2, tall_h], fill=(25, 25, 28))
    # Street lamps with halos
    for sx in range(200, w2, 250):
        # Lamp glow halo (large warm circle)
        for g in range(80, 0, -2):
            alpha = int(40 * (g / 80))
            gc = (alpha + 20, alpha + 15, alpha // 2)
            draw.ellipse([sx - g, street_y - 60 - g, sx + g, street_y - 60 + g], fill=gc)
        # Lamp itself
        draw.ellipse([sx - 12, street_y - 80, sx + 12, street_y - 55], fill=(240, 210, 130))
        # Lamp post
        draw.line([(sx, street_y - 55), (sx, street_y + 30)], fill=(80, 80, 80), width=5)
    # Wet street reflections
    for sx in range(0, w2, 4):
        if rng.random() < 0.1:
            ry = rng.randint(street_y + 80, tall_h - 10)
            b = rng.randint(30, 50)
            draw.point((sx, ry), fill=(b + 10, b + 8, b - 5))

    return img


def create_lab_scene():
    """1950s government laboratory — clearly recognizable as a lab."""
    img = Image.new("RGB", (W * 2, H * 2), (45, 50, 55))
    draw = ImageDraw.Draw(img)
    w2, h2 = W * 2, H * 2
    rng = random.Random(33)

    # Walls — institutional green-grey, clearly visible
    draw.rectangle([0, 0, w2, h2], fill=(55, 60, 58))
    # Horizontal wall tile line at waist height
    tile_y = int(h2 * 0.4)
    draw.rectangle([0, tile_y, w2, tile_y + 6], fill=(70, 75, 72))

    # Fluorescent ceiling lights — bright, institutional
    for lx in [w2 // 4, w2 // 2, 3 * w2 // 4]:
        # Light fixture
        draw.rectangle([lx - 200, 40, lx + 200, 80], fill=(180, 185, 190))
        # Light glow cone downward
        for g in range(200, 0, -4):
            alpha = int(20 * (g / 200))
            gc = (55 + alpha, 60 + alpha, 58 + alpha)
            draw.line([(lx - g, 80 + (200 - g)), (lx + g, 80 + (200 - g))], fill=gc, width=2)

    # Lab bench — large, prominent, dark wood
    bench_y = int(h2 * 0.50)
    bench_h = 50
    draw.rectangle([80, bench_y, w2 - 80, bench_y + bench_h], fill=(80, 65, 50))
    # Bench edge highlight
    draw.rectangle([80, bench_y, w2 - 80, bench_y + 5], fill=(100, 82, 62))
    # Bench legs
    for x in range(200, w2 - 200, 500):
        draw.rectangle([x, bench_y + bench_h, x + 30, h2 - 100], fill=(70, 55, 40))

    # Test tubes in rack — LARGE, colorful, prominent
    rack_x = w2 // 4 - 100
    # Rack frame
    draw.rectangle([rack_x - 20, bench_y - 220, rack_x + 420, bench_y - 200], fill=(90, 90, 95))
    draw.rectangle([rack_x - 20, bench_y - 20, rack_x + 420, bench_y], fill=(90, 90, 95))
    for i in range(12):
        tx = rack_x + i * 35
        tube_h = rng.randint(120, 180)
        # Glass tube outline
        draw.rectangle([tx, bench_y - tube_h, tx + 22, bench_y - 10], outline=(140, 145, 160), width=2)
        # Colored liquid — vivid colors
        lc = rng.choice([
            (100, 180, 70),   # green
            (180, 140, 50),   # amber
            (70, 110, 170),   # blue
            (170, 70, 70),    # red
            (140, 100, 160),  # purple
        ])
        liquid_top = bench_y - tube_h + rng.randint(20, 60)
        draw.rectangle([tx + 2, liquid_top, tx + 20, bench_y - 12], fill=lc)
        # Highlight on glass
        draw.line([(tx + 4, bench_y - tube_h + 5), (tx + 4, bench_y - 15)],
                  fill=(180, 180, 190), width=1)

    # Microscope — LARGE, clearly identifiable
    mx = w2 // 2 + 300
    # Base
    draw.rectangle([mx - 70, bench_y - 30, mx + 70, bench_y], fill=(75, 75, 80))
    # Arm/stand
    draw.rectangle([mx - 10, bench_y - 280, mx + 10, bench_y - 30], fill=(80, 80, 88))
    # Eyepiece
    draw.rectangle([mx - 25, bench_y - 320, mx + 25, bench_y - 280], fill=(90, 90, 98))
    draw.ellipse([mx - 18, bench_y - 340, mx + 18, bench_y - 318], fill=(95, 95, 102))
    # Objective lens
    draw.rectangle([mx - 8, bench_y - 50, mx + 8, bench_y - 30], fill=(85, 85, 92))
    # Stage
    draw.rectangle([mx - 50, bench_y - 80, mx + 50, bench_y - 60], fill=(88, 88, 95))

    # Beakers and flasks — LARGE
    for fx in range(w2 // 2 - 400, w2 // 2 - 50, 100):
        fh = rng.randint(80, 140)
        # Erlenmeyer flask shape
        draw.polygon([(fx - 30, bench_y - 5), (fx - 45, bench_y - fh),
                       (fx + 45, bench_y - fh), (fx + 30, bench_y - 5)],
                      outline=(130, 130, 145), width=2)
        # Liquid inside
        liq_h = int(fh * rng.uniform(0.3, 0.7))
        lc = rng.choice([(90, 160, 60), (160, 120, 40), (60, 100, 150)])
        lx_off = int(15 * liq_h / fh)
        draw.polygon([(fx - 30 + lx_off, bench_y - 5), (fx - 30 + lx_off - 5, bench_y - liq_h),
                       (fx + 30 - lx_off + 5, bench_y - liq_h), (fx + 30 - lx_off, bench_y - 5)],
                      fill=lc)

    # Wall shelf with chemical bottles
    shelf_y = int(h2 * 0.22)
    draw.rectangle([120, shelf_y, w2 - 120, shelf_y + 12], fill=(75, 65, 55))
    for bx in range(180, w2 - 180, 70):
        bh = rng.randint(50, 90)
        bw = rng.randint(25, 40)
        bc = rng.choice([(90, 70, 50), (60, 80, 60), (70, 60, 80), (100, 80, 60)])
        draw.rectangle([bx, shelf_y - bh, bx + bw, shelf_y], fill=bc)
        # Label on bottle
        draw.rectangle([bx + 3, shelf_y - bh + 15, bx + bw - 3, shelf_y - bh + 30],
                       fill=(180, 175, 160))

    # Floor tiles — visible checker pattern
    floor_y = h2 - 250
    for y in range(floor_y, h2, 60):
        for x in range(0, w2, 60):
            shade = 38 + (((x // 60) + (y // 60)) % 2) * 12
            draw.rectangle([x, y, x + 60, y + 60], fill=(shade, shade + 2, shade + 3))

    # "CLASSIFIED" stamp in corner
    font = get_font(80, bold=True)
    draw.text((w2 - 550, h2 - 220), "CLASSIFIED", fill=(120, 30, 30), font=font)

    # "RESTRICTED AREA" sign on wall
    sign_x, sign_y = w2 - 600, int(h2 * 0.12)
    draw.rectangle([sign_x, sign_y, sign_x + 350, sign_y + 80], fill=(160, 40, 40))
    sfont = get_font(36, bold=True)
    draw.text((sign_x + 25, sign_y + 22), "RESTRICTED AREA", fill=(240, 230, 210), font=sfont)

    return img


def create_family_scene():
    """1950s American family — warm tones, house with lit windows."""
    img = Image.new("RGB", (W * 2, H * 2), WARM_AMBER)
    draw = ImageDraw.Draw(img)
    w2, h2 = W * 2, H * 2

    # Warm gradient
    for y in range(h2):
        t = y / h2
        r = int(45 + t * 20)
        g = int(35 + t * 15)
        b = int(20 + t * 5)
        draw.line([(0, y), (w2, y)], fill=(r, g, b))

    # House silhouette
    hx = w2 // 2 - 400
    hy = int(h2 * 0.45)
    draw.rectangle([hx, hy, hx + 600, h2 - 100], fill=(30, 25, 18))
    draw.polygon([(hx - 30, hy), (hx + 300, hy - 200), (hx + 630, hy)], fill=(25, 20, 15))
    draw.rectangle([hx + 450, hy - 250, hx + 500, hy - 100], fill=(28, 23, 16))

    # Lit windows
    windows = [(hx + 80, hy + 60), (hx + 250, hy + 60), (hx + 400, hy + 60),
               (hx + 80, hy + 200), (hx + 250, hy + 200)]
    for wx, wy in windows:
        for g in range(30, 0, -1):
            gc = (min(255, 180 + g * 2), min(255, 150 + g), min(255, 80 + g // 2))
            draw.rectangle([wx - g, wy - g, wx + 80 + g, wy + 60 + g], fill=gc)
        draw.rectangle([wx, wy, wx + 80, wy + 60], fill=(220, 190, 120))
        draw.line([(wx + 40, wy), (wx + 40, wy + 60)], fill=(30, 25, 18), width=3)
        draw.line([(wx, wy + 30), (wx + 80, wy + 30)], fill=(30, 25, 18), width=3)

    # Silhouettes in window — parent with two children
    px, py = hx + 270, hy + 80
    # Adult figure
    draw.ellipse([px - 10, py - 18, px + 10, py - 2], fill=(50, 40, 25))
    draw.rectangle([px - 14, py - 2, px + 14, py + 35], fill=(50, 40, 25))
    # Children figures (smaller, closer together)
    for cx_off in [-35, 35]:
        cx = px + cx_off
        draw.ellipse([cx - 7, py + 8, cx + 7, py + 20], fill=(50, 40, 25))
        draw.rectangle([cx - 9, py + 20, cx + 9, py + 42], fill=(50, 40, 25))

    # Picket fence
    fence_y = h2 - 150
    for fx in range(100, w2 - 100, 30):
        draw.rectangle([fx, fence_y - 50, fx + 8, fence_y], fill=(60, 55, 45))
        draw.polygon([(fx - 2, fence_y - 50), (fx + 4, fence_y - 60), (fx + 10, fence_y - 50)],
                      fill=(60, 55, 45))
    draw.rectangle([100, fence_y - 35, w2 - 100, fence_y - 30], fill=(55, 50, 40))

    # Tree
    tx = 200
    draw.rectangle([tx - 15, hy - 50, tx + 15, h2 - 100], fill=(25, 20, 12))
    draw.ellipse([tx - 120, hy - 300, tx + 120, hy], fill=(28, 22, 14))

    # Stars
    rng = random.Random(11)
    for _ in range(60):
        draw.point((rng.randint(0, w2), rng.randint(0, int(h2 * 0.35))), fill=(180, 170, 140))

    draw.rectangle([0, h2 - 100, w2, h2], fill=(25, 22, 15))
    return img


def create_bedroom_night():
    """1950s children's bedroom at night — dark, quiet, sleeping figures under blankets.
    Completely different composition from the family house exterior."""
    img = Image.new("RGB", (W * 2, H * 2), (12, 14, 25))
    draw = ImageDraw.Draw(img)
    w2, h2 = W * 2, H * 2
    rng = random.Random(67)

    # Dark room with moonlight from window on right
    # Moonlight gradient
    for x in range(w2):
        for y_band in range(0, h2, 40):
            dist_from_window = (w2 - x) / w2
            moonlight = int(8 * (1 - dist_from_window) ** 2)
            y_end = min(y_band + 40, h2)
            draw.rectangle([x, y_band, x + 1, y_end],
                           fill=(12 + moonlight, 14 + moonlight, 25 + moonlight * 2))

    # Window on right wall — pale blue moonlight
    win_x, win_y = w2 - 500, int(h2 * 0.15)
    win_w, win_h = 280, 350
    # Window frame
    draw.rectangle([win_x - 8, win_y - 8, win_x + win_w + 8, win_y + win_h + 8],
                   fill=(35, 30, 28))
    # Window glass — pale blue
    draw.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], fill=(30, 40, 70))
    # Curtains
    draw.rectangle([win_x - 40, win_y - 30, win_x + 20, win_y + win_h + 20], fill=(25, 22, 35))
    draw.rectangle([win_x + win_w - 20, win_y - 30, win_x + win_w + 40, win_y + win_h + 20],
                   fill=(25, 22, 35))
    # Moon visible through window
    moon_x, moon_y = win_x + 80, win_y + 60
    for r in range(50, 0, -1):
        alpha = int(40 * r / 50)
        draw.ellipse([moon_x - r, moon_y - r, moon_x + r, moon_y + r],
                     fill=(30 + alpha, 40 + alpha, 70 + alpha // 2))
    draw.ellipse([moon_x - 20, moon_y - 20, moon_x + 20, moon_y + 20], fill=(160, 170, 200))

    # Light beam from window across floor
    beam_pts = [(win_x + win_w // 2, win_y + win_h),
                (win_x - 300, h2 - 100),
                (win_x + win_w + 100, h2 - 100)]
    for a in range(20, 0, -1):
        c = (12 + a, 14 + a, 25 + a * 2)
        draw.polygon([(p[0], p[1]) for p in beam_pts], fill=c)

    # Two small beds side by side
    floor_y = int(h2 * 0.65)
    for bed_i, bed_x in enumerate([w2 // 4 - 200, w2 // 4 + 350]):
        # Bed frame — dark wood
        draw.rectangle([bed_x, floor_y, bed_x + 400, floor_y + 200], fill=(45, 35, 28))
        # Headboard
        draw.rectangle([bed_x, floor_y - 80, bed_x + 400, floor_y], fill=(55, 42, 32))
        # Pillow — white
        draw.ellipse([bed_x + 30, floor_y - 10, bed_x + 160, floor_y + 40], fill=(140, 135, 125))
        # Blanket — slightly different color per bed
        bc = (60, 55, 80) if bed_i == 0 else (55, 70, 60)
        draw.rectangle([bed_x + 10, floor_y + 30, bed_x + 390, floor_y + 180], fill=bc)
        # Blanket folds
        for fy in range(floor_y + 50, floor_y + 170, 25):
            shade_off = rng.randint(-5, 5)
            draw.line([(bed_x + 20, fy), (bed_x + 380, fy)],
                      fill=(bc[0] + shade_off, bc[1] + shade_off, bc[2] + shade_off), width=2)
        # Small sleeping figure — head on pillow
        head_x = bed_x + 90
        head_y = floor_y + 5
        draw.ellipse([head_x - 18, head_y - 15, head_x + 18, head_y + 15], fill=(120, 100, 85))
        # Hair
        draw.ellipse([head_x - 20, head_y - 18, head_x + 15, head_y + 5], fill=(40, 30, 22))

    # Toy on floor between beds
    toy_x = w2 // 4 + 180
    toy_y = floor_y + 220
    draw.rectangle([toy_x, toy_y, toy_x + 30, toy_y + 30], fill=(100, 45, 45))
    draw.ellipse([toy_x + 40, toy_y + 5, toy_x + 65, toy_y + 30], fill=(80, 80, 120))

    # Wallpaper pattern — faint, childlike
    for wx in range(0, w2, 120):
        for wy in range(0, floor_y - 100, 120):
            if rng.random() < 0.3:
                draw.ellipse([wx, wy, wx + 8, wy + 8], fill=(18, 20, 32))

    # Floor
    draw.rectangle([0, h2 - 100, w2, h2], fill=(30, 25, 20))

    return img


# ── Text Overlay ──────────────────────────────────────────────────────────────

def render_typewriter_text(frame, text, position, progress, font_size=56,
                           color=WHITE, secondary_text=None, secondary_size=32):
    """Render typewriter-style text reveal — ONE character at a time.
    progress: 0.0 to 1.0. Each character appears discretely (no partial).
    Returns (frame, newly_typed_char_index_or_None).
    """
    draw = ImageDraw.Draw(frame)
    font = get_font(font_size, bold=True)

    # Each character gets equal time slice — discrete steps, not smooth
    char_progress = min(1.0, progress * 1.15)  # slight overshoot so last char has dwell time
    chars_to_show = int(len(text) * char_progress)
    chars_to_show = max(0, min(chars_to_show, len(text)))
    visible_text = text[:chars_to_show]
    if not visible_text:
        return frame

    # Previous count for detecting new character
    prev_chars = int(len(text) * max(0, (progress - 1.0 / (FPS * 0.5)) * 1.15))
    prev_chars = max(0, min(prev_chars, len(text)))

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if position == "center":
        tx, ty = (W - tw) // 2, (H - th) // 2
    elif position == "lower_third":
        tx, ty = (W - tw) // 2, int(H * 0.78)
    else:
        tx, ty = (W - tw) // 2, (H - th) // 2

    # Shadow + text
    draw.text((tx + 3, ty + 3), visible_text, fill=(0, 0, 0), font=font)
    draw.text((tx + 1, ty + 1), visible_text, fill=(20, 20, 20), font=font)
    draw.text((tx, ty), visible_text, fill=color, font=font)

    # Cursor — solid block cursor that blinks
    if chars_to_show < len(text) and (int(progress * 12) % 2 == 0):
        cbbox = draw.textbbox((tx, ty), visible_text, font=font)
        cursor_x = cbbox[2] + 3
        draw.rectangle([cursor_x, ty, cursor_x + int(font_size * 0.55), ty + th], fill=color)

    # Secondary text (appears after main text is done)
    if secondary_text and progress > 0.7:
        sp = (progress - 0.7) / 0.3
        sf = get_font(secondary_size)
        sbbox = draw.textbbox((0, 0), secondary_text, font=sf)
        stw = sbbox[2] - sbbox[0]
        stx, sty = (W - stw) // 2, ty + th + 25
        sc = int(len(secondary_text) * min(1.0, sp * 1.3))
        sc = max(0, min(sc, len(secondary_text)))
        sv = secondary_text[:sc]
        sec_color = (color[0] * 3 // 4, color[1] * 3 // 4, color[2] * 3 // 4)
        draw.text((stx + 2, sty + 2), sv, fill=(0, 0, 0), font=sf)
        draw.text((stx, sty), sv, fill=sec_color, font=sf)

    return frame


def render_text_simple(frame, text, position, opacity=1.0, font_size=56,
                       color=WHITE, secondary_text=None, secondary_size=32):
    """Simple text overlay — appears instantly, no typewriter animation.
    opacity: 0.0 to 1.0 for fade-in/out."""
    if opacity <= 0:
        return frame
    draw = ImageDraw.Draw(frame)
    font = get_font(font_size, bold=True)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if position == "center":
        tx, ty = (W - tw) // 2, (H - th) // 2
    elif position == "lower_third":
        tx, ty = (W - tw) // 2, int(H * 0.78)
    else:
        tx, ty = (W - tw) // 2, (H - th) // 2

    op = max(0.0, min(1.0, opacity))
    c = tuple(int(v * op) for v in color)
    sc = tuple(int(v * op) for v in (30, 30, 30))

    # Shadow
    draw.text((tx + 3, ty + 3), text, fill=sc, font=font)
    draw.text((tx + 1, ty + 1), text, fill=sc, font=font)
    draw.text((tx, ty), text, fill=c, font=font)

    if secondary_text and opacity > 0.5:
        sf = get_font(secondary_size)
        sbbox = draw.textbbox((0, 0), secondary_text, font=sf)
        stw = sbbox[2] - sbbox[0]
        stx, sty = (W - stw) // 2, ty + th + 25
        sec_c = tuple(int(v * 0.75 * op) for v in color)
        draw.text((stx + 2, sty + 2), secondary_text, fill=sc, font=sf)
        draw.text((stx, sty), secondary_text, fill=sec_c, font=sf)

    return frame


# ── Parallax Renderer ─────────────────────────────────────────────────────────

def get_depth_map(image, model, processor, device):
    """Generate depth map. Returns float32 [0,1] where 1=far."""
    import torch
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        depth = outputs.predicted_depth
    depth = torch.nn.functional.interpolate(
        depth.unsqueeze(1), size=(image.height, image.width),
        mode="bicubic", align_corners=False
    ).squeeze().cpu().numpy()
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    return depth


def render_parallax_frame(image_arr, depth_arr, t, motion_type="slow_zoom_in",
                          parallax_strength=50.0, speed=3.0):
    """Render single parallax frame with depth-based layer motion."""
    h, w = image_arr.shape[:2]

    if motion_type == "slow_zoom_in":
        zoom = 1.0 + t * speed * 0.01
        dx, dy = 0.0, 0.0
    elif motion_type == "pan_right":
        zoom = 1.02
        dx, dy = t * speed * 15, 0.0
    elif motion_type == "pan_up":
        zoom = 1.02
        dx, dy = 0.0, -t * speed * 15
    else:
        zoom = 1.0 + t * 0.03
        dx, dy = 0.0, 0.0

    near_factor = 1.0 - depth_arr
    shift_x = near_factor * dx * parallax_strength / 60.0
    shift_y = near_factor * dy * parallax_strength / 60.0

    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    cx, cy = w / 2, h / 2

    src_x = (xx - cx) / zoom + cx - shift_x + dx * (1.0 - near_factor * 0.5)
    src_y = (yy - cy) / zoom + cy - shift_y + dy * (1.0 - near_factor * 0.5)

    src_x = np.clip(src_x, 0, w - 1).astype(np.float32)
    src_y = np.clip(src_y, 0, h - 1).astype(np.float32)

    x0 = np.floor(src_x).astype(int)
    y0 = np.floor(src_y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = (src_x - x0)[:, :, np.newaxis]
    fy = (src_y - y0)[:, :, np.newaxis]

    result = (
        image_arr[y0, x0] * (1 - fx) * (1 - fy) +
        image_arr[y0, x1] * fx * (1 - fy) +
        image_arr[y1, x0] * (1 - fx) * fy +
        image_arr[y1, x1] * fx * fy
    )
    return np.clip(result, 0, 255).astype(np.uint8)


def color_grade(frame, style="cold"):
    """Apply color grading — Magnates Media style: BRIGHT, vibrant, high contrast.
    Only archival/document shots get desaturated. Everything else pops."""
    arr = frame.astype(np.float32) / 255.0

    if style == "cold":
        # Night scene — blue-shifted but still BRIGHT and contrasty
        arr[:, :, 0] *= 0.85   # less red
        arr[:, :, 1] *= 0.95   # slightly less green
        arr[:, :, 2] *= 1.15   # boost blue
        # Contrast boost: push darks down, lights up
        arr = _contrast_curve(arr, 1.3)
    elif style == "warm":
        # Family/emotional — amber warmth, inviting, NOT dark
        arr[:, :, 0] *= 1.15   # warm red/orange
        arr[:, :, 1] *= 1.05   # warm green
        arr[:, :, 2] *= 0.80   # less blue
        arr = _contrast_curve(arr, 1.2)
    elif style == "archival":
        # Old photo/document — desaturated sepia but still readable
        gray = np.mean(arr, axis=2, keepdims=True)
        arr = arr * 0.5 + gray * 0.5  # partial desaturation
        arr[:, :, 0] *= 1.10   # slight sepia warmth
        arr[:, :, 2] *= 0.90
        arr *= 0.92
    elif style == "dark":
        # Document/classified — moody but NOT crushed to black
        arr[:, :, 2] *= 1.08   # blue tint
        arr = _contrast_curve(arr, 1.4)  # high contrast
        arr *= 0.85
    elif style == "vibrant":
        # Maximum pop — for key reveals and transitions
        arr = _contrast_curve(arr, 1.5)
        # Saturation boost
        gray = np.mean(arr, axis=2, keepdims=True)
        arr = gray + (arr - gray) * 1.4  # 40% more saturated
    else:  # neutral
        arr = _contrast_curve(arr, 1.2)

    return np.clip(arr * 255, 0, 255).astype(np.uint8)


def _contrast_curve(arr, strength=1.3):
    """S-curve contrast: darks get darker, lights get brighter. No overall dimming."""
    # Sigmoid-based contrast centered at 0.5
    midpoint = 0.5
    return midpoint + (arr - midpoint) * strength


# ── Helpers ───────────────────────────────────────────────────────────────────

def add_dust_particles(frame_arr, t, intensity=1.0, seed=42):
    """Add VISIBLE floating dust/debris particles — cinematic documentary overlay.
    Large enough to actually see at 1080p."""
    h, w = frame_arr.shape[:2]
    rng = random.Random(seed)
    overlay = frame_arr.astype(np.float32)
    n_particles = int(60 * intensity)

    for i in range(n_particles):
        base_x = rng.uniform(0, w)
        base_y = rng.uniform(0, h)
        drift_speed = rng.uniform(0.3, 1.5)
        phase = rng.uniform(0, 2 * math.pi)

        x = int((base_x + math.sin(t * drift_speed + phase) * 120 + t * 30) % w)
        y = int((base_y + math.cos(t * drift_speed * 0.7 + phase) * 80 - t * 20) % h)

        # MUCH bigger: 3-10px radius, visible on 1080p
        size = rng.randint(3, 10)
        brightness = rng.randint(180, 255)
        alpha = rng.uniform(0.25, 0.7) * (0.6 + 0.4 * math.sin(t * 3 + phase))
        alpha = max(0, alpha)

        # Draw with gaussian-like falloff using numpy for speed
        y_lo = max(0, y - size)
        y_hi = min(h, y + size + 1)
        x_lo = max(0, x - size)
        x_hi = min(w, x + size + 1)
        if y_lo >= y_hi or x_lo >= x_hi:
            continue
        yy = np.arange(y_lo, y_hi)[:, None]
        xx = np.arange(x_lo, x_hi)[None, :]
        dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2).astype(np.float32)
        mask = np.clip(1.0 - dist / size, 0, 1) * alpha
        mask = mask[:, :, np.newaxis]
        overlay[y_lo:y_hi, x_lo:x_hi] = (
            overlay[y_lo:y_hi, x_lo:x_hi] * (1 - mask) + brightness * mask
        )

    return np.clip(overlay, 0, 255).astype(np.uint8)


def add_scan_lines(frame_arr, opacity=0.15):
    """Add VISIBLE CRT/film scan lines for archival feel — clearly noticeable."""
    h, w = frame_arr.shape[:2]
    overlay = frame_arr.astype(np.float32)
    # Every 2nd row gets darkened — visible stripe pattern
    overlay[::2, :, :] *= (1.0 - opacity)
    return np.clip(overlay, 0, 255).astype(np.uint8)


def add_light_leak(frame_arr, t, corner="top_right", intensity=0.6):
    """Add VISIBLE warm light leak from corner — bright enough to actually see."""
    h, w = frame_arr.shape[:2]
    overlay = frame_arr.astype(np.float32)

    # Pulsing intensity — higher baseline
    pulse = 0.6 + 0.4 * math.sin(t * 2.0)
    alpha = intensity * pulse

    # Gradient from corner
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    if corner == "top_right":
        dist = np.sqrt(((xx - w) / w) ** 2 + (yy / h) ** 2)
    elif corner == "top_left":
        dist = np.sqrt((xx / w) ** 2 + (yy / h) ** 2)
    else:
        dist = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)

    mask = np.clip(1.0 - dist * 1.2, 0, 1) * alpha
    mask = mask[:, :, np.newaxis]

    # Warm amber leak — MUCH stronger
    overlay[:, :, 0] += mask[:, :, 0] * 80  # red
    overlay[:, :, 1] += mask[:, :, 0] * 50  # green
    overlay[:, :, 2] += mask[:, :, 0] * 15  # touch of blue

    return np.clip(overlay, 0, 255).astype(np.uint8)


def add_vignette(frame_arr, strength=0.6):
    """Add vignette (darkened corners) — clearly visible."""
    h, w = frame_arr.shape[:2]
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    vignette = 1.0 - np.clip(dist - 0.4, 0, 1) * strength
    vignette = vignette[:, :, np.newaxis]
    return np.clip(frame_arr.astype(np.float32) * vignette, 0, 255).astype(np.uint8)


def prepare_image(img, margin=100):
    """Resize/crop to output dims with margin for parallax."""
    tw, th = W + margin * 2, H + margin * 2
    aspect_src = img.width / img.height
    aspect_dst = tw / th
    if aspect_src > aspect_dst:
        new_h = th
        new_w = int(new_h * aspect_src)
    else:
        new_w = tw
        new_h = int(new_w / aspect_src)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    return img.crop((left, top, left + tw, top + th))


def render_beat(img_arr, depth_arr, duration_sec, motion_type, speed,
                color_style, text_overlay=None, text_position="center",
                text_appear_pct=0.1, secondary_text=None, start_time=0.0,
                keystroke_times=None, particles=True, light_leak=False,
                scan_lines=False, vignette=True):
    """Render a complete beat as list of numpy frames.
    If keystroke_times list is provided, appends absolute timestamps for each new char.
    Motion graphics overlays: particles, light_leak, scan_lines, vignette.
    """
    num_frames = int(duration_sec * FPS)
    frames = []

    dep_img = Image.fromarray((depth_arr * 255).astype(np.uint8))
    ih, iw = img_arr.shape[:2]
    dep_img = dep_img.resize((iw, ih), Image.LANCZOS)
    dep_arr = np.array(dep_img).astype(np.float32) / 255.0

    for i in range(num_frames):
        t = i / max(1, num_frames - 1)
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)

        frame = render_parallax_frame(img_arr, dep_arr, t_eased, motion_type, speed=speed)

        # Center crop
        fh, fw = frame.shape[:2]
        cy, cx = (fh - H) // 2, (fw - W) // 2
        if cy >= 0 and cx >= 0:
            frame = frame[cy:cy + H, cx:cx + W]
        else:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))

        frame = color_grade(frame, color_style)

        # Motion graphics overlays
        abs_t = start_time + i / FPS
        if particles:
            frame = add_dust_particles(frame, abs_t, seed=int(start_time * 10) + 42)
        if light_leak:
            frame = add_light_leak(frame, abs_t, corner="top_right")
        if scan_lines:
            frame = add_scan_lines(frame)
        if vignette:
            frame = add_vignette(frame)

        if text_overlay and t >= text_appear_pct:
            tp = min(1.0, (t - text_appear_pct) / 0.3)
            pf = Image.fromarray(frame)
            pf = render_typewriter_text(pf, text_overlay, text_position, tp,
                                        secondary_text=secondary_text)
            frame = np.array(pf)

        frames.append(frame)
    return frames


# ── Typewriter Sound Track ────────────────────────────────────────────────────

def generate_typewriter_track(total_sec):
    """Generate a WAV file with typewriter click sounds at each character reveal time.
    Returns path to the generated WAV."""
    import wave
    import struct

    key_path = os.path.join(SFX_DIR, "typewriter_key.wav")
    if not os.path.exists(key_path):
        return None

    # Load the key click sound
    with wave.open(key_path, 'rb') as wf:
        key_sr = wf.getframerate()
        key_nch = wf.getnchannels()
        key_sw = wf.getsampwidth()
        key_data = wf.readframes(wf.getnframes())
    key_samples = np.frombuffer(key_data, dtype=np.int16).astype(np.float32)

    # Output track at same sample rate
    out_len = int(total_sec * key_sr)
    out = np.zeros(out_len, dtype=np.float32)

    def add_clicks(text, start_sec, type_duration):
        """Add click sounds for each character in text."""
        n_chars = len(text)
        overshoot = 1.15  # matches render_typewriter_text
        for ci in range(n_chars):
            tp = (ci + 0.5) / (n_chars * overshoot)
            t = start_sec + tp * type_duration
            idx = int(t * key_sr)
            end_idx = min(idx + len(key_samples), out_len)
            if idx < out_len and idx >= 0:
                clip_len = end_idx - idx
                out[idx:end_idx] += key_samples[:clip_len] * 0.35  # volume

    # Beat 1 text overlays
    add_clicks("NOVEMBER 28, 1953", 0.31, 0.8)
    add_clicks("NEW YORK CITY", 1.55, 0.5)
    add_clicks("IN THE MORNING", 2.54, 0.6)

    # Beat 6 — Frank Olson reveal
    add_clicks("FRANK OLSON", 12.08, 0.8)
    add_clicks("1910 — 1953", 12.08 + 0.7 * 0.8, 0.3 * 0.8)  # secondary text at 70%

    # Beat 14 — "22 YEARS" (text_appear_pct=0.0, duration=2.11, type over 30%)
    add_clicks("22 YEARS", 25.39, 2.11 * 0.3)

    # Clip to int16 range
    out = np.clip(out, -32768, 32767).astype(np.int16)

    out_path = os.path.join(CREATED_DIR, "typewriter_clicks.wav")
    with wave.open(out_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(key_sr)
        wf.writeframes(out.tobytes())
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("FRANK OLSON HOOK — First 30 Seconds")
    print("=" * 60)

    os.makedirs(CREATED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Load depth model
    print("\n[1/6] Loading Depth Anything V2...")
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    proc = AutoImageProcessor.from_pretrained("depth-anything/Depth-Anything-V2-Small-hf")
    model = AutoModelForDepthEstimation.from_pretrained(
        "depth-anything/Depth-Anything-V2-Small-hf"
    ).to(device)
    model.eval()
    print(f"  Loaded on {device}")

    def get_depth(img):
        return get_depth_map(img, model, proc, device)

    # Create images
    print("\n[2/6] Creating visual assets...")
    t0 = time.time()

    # ── Load ALL real images — NO Pillow-drawn scenes for key moments ──
    print("  Loading real archival photos...")
    nyc_raw = Image.open(os.path.join(IMAGE_DIR, "wiki_nyc_skyline_1950s_night.jpg")).convert("RGB")
    nw, nh = nyc_raw.size
    border = int(nh * 0.07)
    top_bar = int(nh * 0.05)
    nyc = nyc_raw.crop((border, border + top_bar, nw - border, nh - border))
    print(f"  NYC skyline: {nyc.size} (real 1950s postcard)")

    # O'Keeffe "Radiator Building at Night" — art deco NYC building, perfect for hotel
    building = Image.open(os.path.join(IMAGE_DIR, "wiki_art_deco_building_night.jpg")).convert("RGB")
    print(f"  Art deco building: {building.size} (O'Keeffe painting)")

    # Actual Hotel Statler entrance with gold lettering
    hotel_entrance = Image.open(os.path.join(IMAGE_DIR, "wiki_hotel_statler_entrance.jpg")).convert("RGB")
    print(f"  Hotel Statler entrance: {hotel_entrance.size} (real photo)")

    lab = Image.open(os.path.join(IMAGE_DIR, "wiki_bacteriological_laboratory.jpg")).convert("RGB")
    print(f"  Lab wide: {lab.size} (real bacteriological laboratory)")
    lab_equip = Image.open(os.path.join(IMAGE_DIR, "wiki_scientist_laboratory_1940s.jpg")).convert("RGB")
    print(f"  Lab close: {lab_equip.size} (scientist with equipment)")

    olson = Image.open(os.path.join(IMAGE_DIR, "wiki_Frank_Olsen_1910-1953.jpg.jpg")).convert("RGB")
    mkultra = Image.open(os.path.join(IMAGE_DIR, "wiki_Mkultra-lsd-doc.jpg.jpg")).convert("RGB")
    olson_dead = create_olson_dead(olson)

    print("  Building fall (Pillow — tall for vertical pan)...")
    fall = create_building_fall()
    print("  Family scene (Pillow — warm silhouette)...")
    family = create_family_scene()
    print("  Bedroom night scene...")
    bedroom = create_bedroom_night()
    print(f"  Assets loaded in {time.time() - t0:.1f}s")

    # Prepare images for rendering
    print("\n[3/6] Preparing images + depth maps...")
    prepared = {
        "nyc": prepare_image(nyc),
        "building": prepare_image(building),
        "hotel_entrance": prepare_image(hotel_entrance),
        "olson": prepare_image(olson),
        "lab": prepare_image(lab),
        "lab_equip": prepare_image(lab_equip),
        "family": prepare_image(family),
        "bedroom": prepare_image(bedroom),
        "mkultra": prepare_image(mkultra),
        "olson_dead": prepare_image(olson_dead),
    }

    depths = {}
    for name, img in prepared.items():
        print(f"  Depth: {name}...")
        small = img.resize((640, 360))
        depths[name] = get_depth(small)
        dep_img = Image.fromarray((depths[name] * 255).astype(np.uint8))
        depths[name] = np.array(dep_img.resize(img.size, Image.LANCZOS)).astype(np.float32) / 255.0

    arrs = {k: np.array(v) for k, v in prepared.items()}

    # ── Render all beats ──────────────────────────────────────────────────────
    print("\n[4/6] Rendering beats...")
    all_frames = []

    # ─── NARRATION TIMING (silencedetect on original multi-register audio) ───
    # 0.00-0.31  [silence]
    # 0.31-1.32  "November twenty-eight, nineteen fifty-three"
    # 1.55-2.38  "New York City"
    # 2.54-3.33  "3:09 in the morning"
    # 4.06-5.42  [BIG PAUSE]
    # 5.42-7.49  "A man crashes through a closed window on the 10th floor"
    # 7.66-8.99  "of the Hotel Statler"
    # 9.66-11.53 "and falls to his death on the pavement below"
    # 12.08-13.12 "His name is Frank Olson"
    # 13.55-14.82 "He's 43 years old"
    # 15.28-16.42 "A bacteriologist"
    # 16.77-17.83 "A government scientist"
    # 18.15-18.66 "A husband"
    # 19.13-21.39 "The father of three young children"
    # 21.58-22.99 "who are at home asleep in Maryland"
    # 23.44-24.79 "right now, waiting for their dad to come back"
    # 25.39-29.41 "22 years. That's how long this story was kept buried."
    # 29.41-33.01 [end]

    # ── BEAT 1: NYC skyline (0.0 - 4.06s) — pan right across city ──
    # Establishing shot. Text synced to narration.
    print("  [0.0-4.1s] NYC skyline — pan right...")
    n_nyc = int(4.06 * FPS)
    for i in range(n_nyc):
        abs_t = i / FPS
        t = i / max(1, n_nyc - 1)
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)

        frame = render_parallax_frame(arrs["nyc"], depths["nyc"], t_eased,
                                       "pan_right", speed=3.0)
        fh_f, fw_f = frame.shape[:2]
        cy_f, cx_f = (fh_f - H) // 2, (fw_f - W) // 2
        if cy_f >= 0 and cx_f >= 0:
            frame = frame[cy_f:cy_f + H, cx_f:cx_f + W]
        else:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))
        frame = color_grade(frame, "cold")
        frame = add_dust_particles(frame, abs_t, seed=42)
        frame = add_vignette(frame, strength=0.5)

        pil_f = Image.fromarray(frame)
        # Typewriter text — synced to speech, layered (date + city hold together)
        # Date types in at 0.31, stays visible through city + hold
        if abs_t >= 0.31:
            tp_date = min(1.0, (abs_t - 0.31) / 0.8)
            # Draw date slightly above center
            draw = ImageDraw.Draw(pil_f)
            font = get_font(56, bold=True)
            date_text = "NOVEMBER 28, 1953"
            chars_date = max(0, min(len(date_text), int(len(date_text) * min(1.0, tp_date * 1.15))))
            if chars_date > 0:
                vis = date_text[:chars_date]
                bbox = draw.textbbox((0, 0), date_text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                tx = (W - tw) // 2
                ty = H // 2 - th - 15  # above center
                draw.text((tx + 3, ty + 3), vis, fill=(0, 0, 0), font=font)
                draw.text((tx, ty), vis, fill=WHITE, font=font)
                # Cursor
                if chars_date < len(date_text) and (int(tp_date * 12) % 2 == 0):
                    cbbox = draw.textbbox((tx, ty), vis, font=font)
                    draw.rectangle([cbbox[2] + 3, ty, cbbox[2] + 33, ty + th], fill=WHITE)
        # City types in at 1.55, stays visible alongside date
        if abs_t >= 1.55:
            tp_city = min(1.0, (abs_t - 1.55) / 0.5)
            draw = ImageDraw.Draw(pil_f)
            font = get_font(56, bold=True)
            city_text = "NEW YORK CITY"
            chars_city = max(0, min(len(city_text), int(len(city_text) * min(1.0, tp_city * 1.15))))
            if chars_city > 0:
                vis = city_text[:chars_city]
                bbox = draw.textbbox((0, 0), city_text, font=font)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                tx = (W - tw) // 2
                ty = H // 2 + 15  # below center
                draw.text((tx + 3, ty + 3), vis, fill=(0, 0, 0), font=font)
                draw.text((tx, ty), vis, fill=WHITE, font=font)
                if chars_city < len(city_text) and (int(tp_city * 12) % 2 == 0):
                    cbbox = draw.textbbox((tx, ty), vis, font=font)
                    draw.rectangle([cbbox[2] + 3, ty, cbbox[2] + 33, ty + th], fill=WHITE)
        # "IN THE MORNING" — lower third, appears when voice says it, no linger after
        if 2.54 <= abs_t < 3.35:
            tp_morn = min(1.0, (abs_t - 2.54) / 0.5)
            pil_f = render_typewriter_text(pil_f, "IN THE MORNING", "lower_third", tp_morn,
                                            font_size=48)

        all_frames.append(np.array(pil_f))

    # ── BEAT 2: Building at night (4.06 - 5.42s) — tension during silence ──
    # Zoom toward upper windows of dark building. No sound, just dread.
    print("  [4.1-5.4s] Building exterior — ominous silence...")
    all_frames.extend(render_beat(
        arrs["building"], depths["building"], 1.36, "slow_zoom_in", 5.0, "cold",
        start_time=4.06, particles=True, vignette=True
    ))

    # ── BEAT 3: THE CRASH (5.42 - 7.49s) — "crashes through a closed window" ──
    # Flash + shake on building → glass shatter SFX tells the story
    print("  [5.4-7.5s] The crash — flash + shake...")
    n_crash = int(2.07 * FPS)
    rng_shake = random.Random(88)
    for i in range(n_crash):
        t = i / max(1, n_crash - 1)
        abs_t = 5.42 + i / FPS
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)
        frame = render_parallax_frame(arrs["building"], depths["building"], t_eased,
                                       "slow_zoom_in", speed=10.0)
        fh_f, fw_f = frame.shape[:2]
        cy_f, cx_f = (fh_f - H) // 2, (fw_f - W) // 2
        if cy_f >= 0 and cx_f >= 0:
            frame = frame[cy_f:cy_f + H, cx_f:cx_f + W]
        else:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))
        frame = color_grade(frame, "vibrant")
        # Bright white flash at crash moment (first 5 frames)
        if i < 5:
            flash_strength = (5 - i) / 5 * 0.7
            frame = (frame.astype(np.float32) * (1 - flash_strength) + 255 * flash_strength).astype(np.uint8)
        # Camera shake — violent at start, settling
        if t < 0.4:
            shake = int(20 * (1 - t / 0.4))
            frame = np.roll(frame, rng_shake.randint(-shake, shake), axis=1)
            frame = np.roll(frame, rng_shake.randint(-shake, shake), axis=0)
        frame = add_dust_particles(frame, abs_t, intensity=1.5, seed=88)
        frame = add_vignette(frame, strength=0.7)
        all_frames.append(frame)

    # ── BEAT 4: Hotel Statler entrance (7.49 - 9.0s) — "of the Hotel Statler" ──
    # Real photo with gold "HOTEL STATLER" lettering — narrator says the name
    print("  [7.5-9.0s] Hotel Statler entrance...")
    all_frames.extend(render_beat(
        arrs["hotel_entrance"], depths["hotel_entrance"], 1.5, "slow_zoom_in", 3.0, "cold",
        start_time=7.49, particles=True, vignette=True
    ))

    # ── BEAT 5: The fall (9.0 - 11.5s) — "falls to his death on the pavement below" ──
    # Fast downward pan through building — accelerating like gravity
    print("  [9.0-11.5s] The fall — building pan down...")
    fall_prepared = prepare_image(fall, margin=200)
    fall_arr = np.array(fall_prepared)
    n_fall = int(2.5 * FPS)
    fh, fw = fall_arr.shape[:2]
    for i in range(n_fall):
        t = (i / max(1, n_fall - 1)) ** 1.6  # accelerating
        y_off = int(t * max(0, fh - H))
        x_off = (fw - W) // 2
        frame = fall_arr[y_off:y_off + H, x_off:x_off + W]
        if frame.shape[0] < H or frame.shape[1] < W:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))
        frame = color_grade(frame, "cold")
        frame = add_dust_particles(frame, 9.0 + i / FPS, seed=55)
        frame = add_vignette(frame, strength=0.5)
        all_frames.append(frame)

    # ── BEAT 6: "His name is Frank Olson" (11.5 - 13.55s) ──
    # Fade from black to his portrait — the reveal
    print("  [11.5-13.6s] Frank Olson reveal...")
    n_name = int(2.05 * FPS)
    for i in range(n_name):
        t = i / max(1, n_name - 1)
        abs_t = 11.5 + i / FPS
        if t < 0.15:
            frame = np.zeros((H, W, 3), dtype=np.uint8) + 8
        else:
            fade_t = min(1.0, (t - 0.15) / 0.25)
            tp = (t - 0.15) / (1 - 0.15)
            pf = render_parallax_frame(arrs["olson"], depths["olson"], tp * 0.3,
                                       "slow_zoom_in", speed=2.0)
            fhh, fww = pf.shape[:2]
            cy_c, cx_c = (fhh - H) // 2, (fww - W) // 2
            if cy_c >= 0 and cx_c >= 0:
                pf = pf[cy_c:cy_c + H, cx_c:cx_c + W]
            else:
                pf = np.array(Image.fromarray(pf).resize((W, H), Image.LANCZOS))
            pf = color_grade(pf, "archival")
            black = np.zeros_like(pf) + 8
            frame = (black * (1 - fade_t) + pf * fade_t).astype(np.uint8)

        frame = add_dust_particles(frame, abs_t, seed=60)
        frame = add_vignette(frame, strength=0.4)
        pil_f = Image.fromarray(frame)
        if abs_t >= 12.08:
            tp = min(1.0, (abs_t - 12.08) / 0.8)
            pil_f = render_typewriter_text(pil_f, "FRANK OLSON", "center", tp,
                                            font_size=72, secondary_text="1910 — 1953")
        all_frames.append(np.array(pil_f))

    # ── BEAT 7: "He's 43 years old" (13.55 - 15.28s) — Lab pan right + "43" text ──
    print("  [13.6-15.3s] Lab — pan right + '43' text...")
    all_frames.extend(render_beat(
        arrs["lab"], depths["lab"], 1.73, "pan_right", 4.0, "archival",
        text_overlay="43", text_position="center", text_appear_pct=0.2,
        start_time=13.55, scan_lines=True, particles=True
    ))

    # ── BEAT 8: "A bacteriologist" (15.28 - 16.77s) — Lab equipment zoom ──
    print("  [15.3-16.8s] Lab equipment — zoom in...")
    all_frames.extend(render_beat(
        arrs["lab_equip"], depths["lab_equip"], 1.49, "slow_zoom_in", 5.0, "archival",
        start_time=15.28, scan_lines=True, particles=True
    ))

    # ── BEAT 9: "A government scientist" (16.77 - 18.15s) — Lab pan left ──
    print("  [16.8-18.2s] Lab — pan left...")
    all_frames.extend(render_beat(
        arrs["lab"], depths["lab"], 1.38, "pan_right", -5.0, "cold",
        start_time=16.77, scan_lines=True, particles=True
    ))

    # ── BEAT 10: "A husband" (18.15 - 19.13s) — Olson portrait (he IS the husband) ──
    print("  [18.2-19.1s] Olson — 'a husband'...")
    all_frames.extend(render_beat(
        arrs["olson"], depths["olson"], 0.98, "slow_zoom_in", 3.0, "warm",
        start_time=18.15, light_leak=True, particles=True
    ))

    # ── BEAT 11: "The father of three young children" (19.13 - 21.58s) — Family static ──
    # Hold on the family scene — let the words land
    print("  [19.1-21.6s] Family — holding...")
    all_frames.extend(render_beat(
        arrs["family"], depths["family"], 2.45, "pan_right", 2.0, "warm",
        start_time=19.13, light_leak=True, particles=True
    ))

    # ── BEAT 12: "who are at home asleep in Maryland" (21.58 - 23.44s) ──
    # Same family house but cold/dark — nighttime, children sleeping inside
    print("  [21.6-23.4s] Family home at night — 'asleep in Maryland'...")
    all_frames.extend(render_beat(
        arrs["family"], depths["family"], 1.86, "slow_zoom_in", 2.0, "cold",
        start_time=21.58, particles=True, vignette=True
    ))

    # ── BEAT 13: "waiting for their dad to come back" (23.44 - 25.39s) ──
    # Back to Olson — emotional weight, static
    print("  [23.4-25.4s] Olson photo — 'waiting for their dad'...")
    all_frames.extend(render_beat(
        arrs["olson"], depths["olson"], 1.95, "pan_right", 1.5, "warm",
        start_time=23.44, light_leak=True, particles=True
    ))

    # ── BEAT 14: "22 years" (25.39 - 27.5s) — MKUltra document ──
    print("  [25.4-27.5s] MKUltra document — '22 years'...")
    all_frames.extend(render_beat(
        arrs["mkultra"], depths["mkultra"], 2.11, "slow_zoom_in", 3.0, "archival",
        text_overlay="22 YEARS", text_appear_pct=0.0,
        start_time=25.39, scan_lines=True, particles=True
    ))

    # ── BEAT 15: "how he died" (27.5 - 29.41s) — Olson red X eyes, zoom into eye, fade to red ──
    print("  [27.5-29.4s] Olson dead — zoom into eye → fade to red...")
    beat15_dur = 1.91
    beat15_frames = int(beat15_dur * FPS)
    img15 = arrs["olson_dead"]
    dep15 = depths["olson_dead"]
    dep15_img = Image.fromarray((dep15 * 255).astype(np.uint8))
    ih15, iw15 = img15.shape[:2]
    dep15_img = dep15_img.resize((iw15, ih15), Image.LANCZOS)
    dep15_arr = np.array(dep15_img).astype(np.float32) / 255.0
    # Eye target: 40% from top, 45.5% horizontal (center between both eyes)
    eye_cy_frac, eye_cx_frac = 0.40, 0.455
    for i in range(beat15_frames):
        t = i / max(1, beat15_frames - 1)
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)
        # Aggressive zoom: 1.0 → 3.5x over the beat, centering on eyes
        zoom = 1.0 + t_eased * 2.5
        h15, w15 = img15.shape[:2]
        # Shift center toward eyes as we zoom
        target_cx = w15 * eye_cx_frac
        target_cy = h15 * eye_cy_frac
        cx, cy = w15 / 2, h15 / 2
        # Interpolate center toward eye position
        cur_cx = cx + (target_cx - cx) * t_eased
        cur_cy = cy + (target_cy - cy) * t_eased
        yy, xx = np.meshgrid(np.arange(h15), np.arange(w15), indexing='ij')
        near_factor = 1.0 - dep15_arr
        src_x = (xx - cur_cx) / zoom + cur_cx
        src_y = (yy - cur_cy) / zoom + cur_cy
        # Add parallax depth shift
        src_x = src_x - near_factor * 2.0 * t_eased
        src_y = src_y - near_factor * 1.5 * t_eased
        src_x = np.clip(src_x, 0, w15 - 1).astype(np.float32)
        src_y = np.clip(src_y, 0, h15 - 1).astype(np.float32)
        x0 = np.floor(src_x).astype(int)
        y0 = np.floor(src_y).astype(int)
        x1 = np.minimum(x0 + 1, w15 - 1)
        y1 = np.minimum(y0 + 1, h15 - 1)
        fx = (src_x - x0)[:, :, np.newaxis]
        fy = (src_y - y0)[:, :, np.newaxis]
        frame = (
            img15[y0, x0] * (1 - fx) * (1 - fy) +
            img15[y0, x1] * fx * (1 - fy) +
            img15[y1, x0] * (1 - fx) * fy +
            img15[y1, x1] * fx * fy
        )
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        # Center crop to output size
        fh, fw = frame.shape[:2]
        cy_c, cx_c = (fh - H) // 2, (fw - W) // 2
        if cy_c >= 0 and cx_c >= 0:
            frame = frame[cy_c:cy_c + H, cx_c:cx_c + W]
        else:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))
        frame = color_grade(frame, "dark")
        abs_t = 27.5 + i / FPS
        frame = add_scan_lines(frame)
        frame = add_dust_particles(frame, abs_t, seed=275 + 42)
        frame = add_vignette(frame)
        # Fade to red in last 30% of beat
        if t > 0.7:
            red_t = (t - 0.7) / 0.3  # 0→1 over last 30%
            red_t = red_t * red_t  # ease-in (accelerate)
            red_frame = np.full_like(frame, [140, 15, 15], dtype=np.uint8)
            frame = (frame * (1 - red_t) + red_frame * red_t).astype(np.uint8)
        all_frames.append(frame)

    # ── BEAT 16: Red → fade to black (29.41 - 33.0s) ──
    print("  [29.4-33.0s] Red → fade to black...")
    n_fade = int(3.6 * FPS)
    red_screen = np.full((H, W, 3), [140, 15, 15], dtype=np.uint8)
    for i in range(n_fade):
        t = i / max(1, n_fade - 1)
        # First 20%: hold red, then fade to black
        if t < 0.2:
            all_frames.append(red_screen.copy())
        else:
            fade_t = (t - 0.2) / 0.8  # 0→1 over remaining 80%
            fade_t = min(1.0, fade_t * 1.5)  # slightly accelerated
            black = np.full((H, W, 3), 5, dtype=np.uint8)
            frame = (red_screen * (1 - fade_t) + black * fade_t).astype(np.uint8)
            all_frames.append(frame)

    total_sec = len(all_frames) / FPS
    print(f"\n  Total: {len(all_frames)} frames ({total_sec:.1f}s)")

    # Write frames
    print("\n[5/6] Writing frames to disk...")
    tmpdir = tempfile.mkdtemp()
    for i, f in enumerate(all_frames):
        Image.fromarray(f).save(os.path.join(tmpdir, f"frame_{i:05d}.png"))
        if (i + 1) % 150 == 0:
            print(f"  {i+1}/{len(all_frames)}")
    print(f"  {len(all_frames)}/{len(all_frames)} done")

    # Composite with ffmpeg
    print("\n[6/6] Compositing video + audio...")
    video_only = os.path.join(CREATED_DIR, "video_only.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(tmpdir, "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        video_only
    ], capture_output=True)

    # Generate typewriter click track
    print("  Generating typewriter click track...")
    tw_path = generate_typewriter_track(total_sec)

    # Audio mix: voice + music + SFX + typewriter clicks
    audio_inputs = [
        "-i", VOICE_PATH,                                     # [1] voice
        "-i", MUSIC_PATH,                                      # [2] music
        "-i", os.path.join(SFX_DIR, "glass_shatter_01.mp3"),  # [3] @ 5.42s — window crash
        "-i", os.path.join(SFX_DIR, "body_impact_01.mp3"),    # [4] @ 11.0s — hits ground
        "-i", os.path.join(SFX_DIR, "whoosh_01.mp3"),          # [5] @ 4.06s — cut to hotel
        "-i", os.path.join(SFX_DIR, "rumble_01.mp3"),          # [6] @ 25.39s — 22 years
    ]
    filter_parts = [
        f"[1:a]atrim=0:{total_sec},asetpts=PTS-STARTPTS,volume=1.0[voice]",
        f"[2:a]atrim=0:{total_sec},asetpts=PTS-STARTPTS,volume=0.15,afade=t=in:st=0:d=2[music]",
        f"[3:a]volume=0.5,adelay=5420|5420[sfx_glass]",
        f"[4:a]volume=0.3,adelay=11000|11000[sfx_impact]",
        f"[5:a]volume=0.25,adelay=4060|4060[sfx_whoosh]",
        f"[6:a]volume=0.15,adelay=25390|25390[sfx_rumble]",
    ]
    mix_labels = "[voice][music][sfx_glass][sfx_impact][sfx_whoosh][sfx_rumble]"
    num_mix = 6

    # Add typewriter click track if generated
    if tw_path:
        audio_inputs.extend(["-i", tw_path])  # [7] typewriter clicks
        filter_parts.append(f"[7:a]volume=0.6[sfx_type]")
        mix_labels += "[sfx_type]"
        num_mix = 7

    # No dynaudnorm — it was causing volume drift. Just normalize=0.
    filter_str = ";".join(filter_parts) + ";" + (
        f"{mix_labels}amix=inputs={num_mix}:duration=first:dropout_transition=0:normalize=0,"
        f"atrim=0:{total_sec}[audio]"
    )

    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_only,
    ] + audio_inputs + [
        "-filter_complex", filter_str,
        "-map", "0:v", "-map", "[audio]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", str(total_sec),
        OUTPUT_PATH
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Audio mix failed: {result.stderr[-500:]}")
        print(f"  Falling back to voice only...")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_only, "-i", VOICE_PATH,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", str(total_sec), OUTPUT_PATH
        ], capture_output=True)

    # Cleanup
    for f in os.listdir(tmpdir):
        os.remove(os.path.join(tmpdir, f))
    os.rmdir(tmpdir)

    if os.path.exists(OUTPUT_PATH):
        size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
        print(f"\n  DONE: {OUTPUT_PATH} ({size_mb:.1f} MB, {total_sec:.1f}s)")
        print(f"  Open: open {OUTPUT_PATH}")
    else:
        print("\n  ERROR: Output not created")

    print("=" * 60)


if __name__ == "__main__":
    main()
