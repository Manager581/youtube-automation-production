#!/usr/bin/env python3
"""
Create custom composed visuals for key dramatic segments.
Uses PIL compositing with existing assets — similar to create_olson_dead() in hook.

These show WHAT IS HAPPENING, not just a stock photo.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"
MANIFEST_PATH = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/manifest.json"
WIKI_DIR = PROJECT_ROOT / "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/wikimedia"

# Target size for compositions
W, H = 1920, 1080


def load_img(name):
    """Load image from images/ or wikimedia/ dir."""
    for d in [IMG_DIR, WIKI_DIR]:
        for f in d.iterdir():
            if name in f.name.lower() and f.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                return Image.open(f).convert("RGB")
    return None


def darken(img, factor=0.4):
    """Darken an image."""
    return ImageEnhance.Brightness(img).enhance(factor)


def add_red_tint(img, strength=0.15):
    """Add subtle red color shift."""
    arr = np.array(img, dtype=np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * (1 + strength), 0, 255)
    arr[:, :, 1] = arr[:, :, 1] * (1 - strength * 0.3)
    arr[:, :, 2] = arr[:, :, 2] * (1 - strength * 0.5)
    return Image.fromarray(arr.astype(np.uint8))


def add_vignette(img, strength=0.7):
    """Add dark vignette overlay."""
    w, h = img.size
    arr = np.array(img, dtype=np.float32)
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    vignette = 1.0 - (dist / max_dist) * strength
    vignette = np.clip(vignette, 0, 1)
    arr *= vignette[:, :, np.newaxis]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def add_film_grain(img, intensity=25):
    """Add film grain noise."""
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, intensity, arr.shape)
    arr = np.clip(arr + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def fit_to_canvas(img, w=W, h=H):
    """Resize and crop image to fill canvas."""
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


def get_font(size=60, bold=True):
    """Get a good font, fallback chain."""
    fonts = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFCompact.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ═══════════════════════════════════════════════════════
# COMPOSITION FUNCTIONS
# ═══════════════════════════════════════════════════════

def create_drugging_scene():
    """Seg 53: Hand dropping substance into drink.
    Compose: dark cocktail scene + ominous overlay."""
    base = load_img("cocktail")
    if not base:
        base = Image.new("RGB", (W, H), (20, 15, 10))
    base = fit_to_canvas(base)
    base = darken(base, 0.35)
    base = add_red_tint(base, 0.1)

    draw = ImageDraw.Draw(base)
    # Add a glowing drop effect in center (the substance being dropped)
    cx, cy = W // 2, H // 3
    for r in range(30, 0, -1):
        alpha = int(80 * (r / 30))
        color = (200, 200, 100, alpha)  # yellowish glow
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(200 - r * 3, 200 - r * 4, 50 + r))

    base = add_vignette(base, 0.8)
    base = add_film_grain(base, 20)
    return base


def create_distressed_man():
    """Segs 58-59: Man in psychological distress.
    Compose: dark room + Olson portrait with motion blur + red tint."""
    olson = load_img("frank_olsen")
    if not olson:
        olson = Image.new("RGB", (W, H), (30, 20, 15))
    olson = fit_to_canvas(olson)
    olson = darken(olson, 0.3)

    # Motion blur effect (simulate disorientation)
    blurred = olson.filter(ImageFilter.GaussianBlur(radius=8))
    arr_orig = np.array(olson, dtype=np.float32)
    arr_blur = np.array(blurred, dtype=np.float32)
    # Blend: keep center sharp, edges blurred
    Y, X = np.ogrid[:H, :W]
    cx, cy = W // 2, H * 0.4
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_d = np.sqrt((W / 2) ** 2 + (H / 2) ** 2)
    blend = np.clip(dist / (max_d * 0.5), 0, 1)[:, :, np.newaxis]
    result = arr_orig * (1 - blend) + arr_blur * blend

    img = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    img = add_red_tint(img, 0.2)
    img = add_vignette(img, 0.85)
    img = add_film_grain(img, 30)
    return img


def create_shattered_window():
    """Seg 92: Window shattered outward from inside.
    Compose: broken glass + hotel night + dramatic lighting."""
    glass = load_img("broken_window")
    if not glass:
        glass = Image.new("RGB", (W, H), (10, 10, 15))
    glass = fit_to_canvas(glass)
    glass = darken(glass, 0.4)

    # Add streaks of light coming through (the city lights outside)
    draw = ImageDraw.Draw(glass)
    import random
    random.seed(42)
    for _ in range(15):
        x = random.randint(W // 4, 3 * W // 4)
        y1 = random.randint(0, H // 3)
        y2 = y1 + random.randint(100, 400)
        w = random.randint(2, 6)
        brightness = random.randint(60, 120)
        draw.line([(x, y1), (x + random.randint(-20, 20), y2)],
                  fill=(brightness, brightness + 20, brightness + 40), width=w)

    glass = add_vignette(glass, 0.9)
    glass = add_film_grain(glass, 25)
    return glass


def create_forensic_evidence():
    """Segs 93, 124-125, 127: Forensic examination findings.
    Compose: dark clinical scene + document overlay + red accent."""
    base = load_img("forensic")
    if not base:
        base = Image.new("RGB", (W, H), (20, 25, 20))
    base = fit_to_canvas(base)
    base = darken(base, 0.45)

    # Add document overlay on right side
    doc = load_img("declassifiedmkultra")
    if doc:
        doc = doc.resize((500, 650), Image.LANCZOS)
        doc = ImageEnhance.Brightness(doc).enhance(0.6)
        # Tilt slightly
        doc = doc.rotate(-5, expand=True, fillcolor=(0, 0, 0))
        base.paste(doc, (W - 550, H // 2 - 300))

    base = add_red_tint(base, 0.12)
    base = add_vignette(base, 0.75)
    base = add_film_grain(base, 20)
    return base


def create_silence_coverup():
    """Seg 94: Silence/suppression.
    Compose: CIA doc + heavy redaction marks + dark."""
    doc = load_img("declassifiedmkultra") or load_img("mkultra-lsd")
    if not doc:
        doc = Image.new("RGB", (W, H), (40, 35, 30))
    doc = fit_to_canvas(doc)
    doc = darken(doc, 0.5)

    draw = ImageDraw.Draw(doc)
    # Draw heavy black redaction bars across the document
    import random
    random.seed(94)
    for _ in range(8):
        y = random.randint(100, H - 200)
        x1 = random.randint(100, W // 3)
        x2 = random.randint(W // 2, W - 100)
        h = random.randint(25, 50)
        draw.rectangle([x1, y, x2, y + h], fill=(5, 5, 5))

    # Add "CLASSIFIED" stamp
    font = get_font(80)
    draw.text((W // 2 - 200, H // 2 - 50), "CLASSIFIED",
              fill=(150, 20, 20), font=font)

    doc = add_vignette(doc, 0.8)
    doc = add_film_grain(doc, 15)
    return doc


def create_truth_revealed():
    """Seg 103: Truth coming to light.
    Compose: document emerging from darkness into light."""
    doc = load_img("mkultra-lsd") or load_img("declassifiedmkultra")
    if not doc:
        doc = Image.new("RGB", (W, H), (40, 35, 25))
    doc = fit_to_canvas(doc)

    # Dramatic lighting: bright center, dark edges
    arr = np.array(doc, dtype=np.float32)
    Y, X = np.ogrid[:H, :W]
    cx, cy = W * 0.45, H * 0.4
    dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    max_d = max(W, H) * 0.4
    light = np.clip(1.0 - (dist / max_d) * 0.8, 0.15, 1.0)
    arr *= light[:, :, np.newaxis]
    # Warm the light center
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)

    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img = add_film_grain(img, 15)
    return img


def create_skull_hematoma():
    """Seg 124: Cranial hematoma evidence.
    Compose: dark forensic/medical scene + highlighted impact area."""
    base = load_img("forensic")
    if not base:
        base = Image.new("RGB", (W, H), (15, 20, 15))
    base = fit_to_canvas(base)
    base = darken(base, 0.35)

    draw = ImageDraw.Draw(base)
    # Draw a glowing red impact area (the hematoma)
    cx, cy = int(W * 0.55), int(H * 0.35)
    for r in range(60, 0, -2):
        intensity = int(180 * (1 - r / 60))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(intensity, int(intensity * 0.15), int(intensity * 0.1)))

    base = add_vignette(base, 0.85)
    base = add_film_grain(base, 25)
    return base


def create_murder_scene():
    """Seg 129: Violence — someone hit him and put him through the window.
    Compose: shattered window + hotel night + red accent."""
    glass = load_img("broken_window")
    hotel = load_img("hotel_statler") or load_img("hotel_night")

    if glass and hotel:
        glass = fit_to_canvas(glass)
        hotel = fit_to_canvas(hotel)
        # Blend: glass in foreground, hotel in background
        arr_g = np.array(glass, dtype=np.float32)
        arr_h = np.array(hotel, dtype=np.float32)
        result = arr_g * 0.6 + arr_h * 0.4
        base = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    elif glass:
        base = fit_to_canvas(glass)
    else:
        base = Image.new("RGB", (W, H), (15, 10, 10))

    base = darken(base, 0.35)
    base = add_red_tint(base, 0.25)
    base = add_vignette(base, 0.9)
    base = add_film_grain(base, 30)
    return base


def create_time_passing():
    """Segs 98, 148: Years passing, decades of silence.
    Compose: layered dates fading into each other."""
    base = Image.new("RGB", (W, H), (10, 8, 6))
    draw = ImageDraw.Draw(base)

    font_large = get_font(120)
    font_med = get_font(60)

    # Draw years fading across the image
    years = ["1953", "1975", "1994", "2002", "2017", "2024"]
    for i, year in enumerate(years):
        x = int(W * (i + 0.5) / len(years)) - 80
        y = H // 2 - 60 + (i % 2) * 40
        # Fade: earlier years dimmer
        brightness = int(40 + (i / len(years)) * 150)
        draw.text((x, y), year, fill=(brightness, brightness - 10, brightness - 20),
                  font=font_large)

    # Add subtle document texture behind
    doc = load_img("declassifiedmkultra")
    if doc:
        doc = fit_to_canvas(doc)
        doc = darken(doc, 0.15)
        arr_base = np.array(base, dtype=np.float32)
        arr_doc = np.array(doc, dtype=np.float32)
        result = np.maximum(arr_base, arr_doc * 0.3)
        base = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))

    base = add_vignette(base, 0.6)
    base = add_film_grain(base, 20)
    return base


def create_homicide_conclusion():
    """Seg 127: 'Frank Olson had not died from a fall — he had been murdered.'
    Compose: Olson portrait + heavy red tint + 'HOMICIDE' stamp."""
    olson = load_img("frank_olsen")
    if not olson:
        olson = Image.new("RGB", (W, H), (30, 20, 15))
    olson = fit_to_canvas(olson)
    olson = darken(olson, 0.4)
    olson = add_red_tint(olson, 0.3)

    draw = ImageDraw.Draw(olson)
    font = get_font(100)
    # Stamp "HOMICIDE" at an angle
    txt_img = Image.new("RGBA", (700, 150), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((10, 10), "HOMICIDE", fill=(200, 30, 20, 200), font=font)
    txt_img = txt_img.rotate(15, expand=True)
    # Paste with alpha
    olson.paste(Image.new("RGB", txt_img.size, (200, 30, 20)),
                (W // 2 - 350, H // 2 - 100), txt_img.split()[-1])

    olson = add_vignette(olson, 0.85)
    olson = add_film_grain(olson, 25)
    return olson


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

COMPOSITIONS = {
    "dramatic_drugging.jpg": (create_drugging_scene, [53]),
    "dramatic_distressed.jpg": (create_distressed_man, [58, 59, 76]),
    "dramatic_shattered_window.jpg": (create_shattered_window, [92, 128]),
    "dramatic_forensic.jpg": (create_forensic_evidence, [93, 125]),
    "dramatic_silence.jpg": (create_silence_coverup, [94, 95, 115, 141, 145]),
    "dramatic_truth.jpg": (create_truth_revealed, [103, 152, 153, 154]),
    "dramatic_hematoma.jpg": (create_skull_hematoma, [124]),
    "dramatic_homicide.jpg": (create_homicide_conclusion, [127]),
    "dramatic_murder.jpg": (create_murder_scene, [129]),
    "dramatic_time_passing.jpg": (create_time_passing, [98, 148]),
}


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Creating {len(COMPOSITIONS)} dramatic compositions...")
    created = 0

    for filename, (func, seg_ids) in COMPOSITIONS.items():
        dest = IMG_DIR / filename
        print(f"\n  [{filename}] segs {seg_ids}")
        try:
            img = func()
            img.save(dest, quality=95)
            sz = dest.stat().st_size
            print(f"    [OK] {sz:,}B ({img.size[0]}x{img.size[1]})")
            created += 1
        except Exception as e:
            print(f"    [ERROR] {e}")

    # Update manifest
    print(f"\nUpdating manifest...")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    for filename, (_, seg_ids) in COMPOSITIONS.items():
        img_path = f"images/{filename}"
        # Remove these segments from other entries
        for entry in manifest["images"]:
            entry["storyboard_segment_ids"] = [
                s for s in entry.get("storyboard_segment_ids", [])
                if s not in seg_ids
            ]
        # Add new entry
        manifest["images"].append({
            "filename": img_path,
            "source": "custom_composition",
            "storyboard_segment_ids": seg_ids,
        })

    # Clean empty entries
    manifest["images"] = [e for e in manifest["images"] if e.get("storyboard_segment_ids")]

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nCreated: {created}/{len(COMPOSITIONS)}")
    print(f"Manifest updated: {len(manifest['images'])} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
