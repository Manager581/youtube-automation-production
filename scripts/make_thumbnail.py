#!/usr/bin/env python3
"""Generate YouTube thumbnails for 'Why Breaking the Law Is Profitable'.

Produces 3 variants so user can pick:
  v1: Zuckerberg smiling + "HE GAINED $1.1 BILLION" + fine context
  v2: Fine bar chart + "CRIME DOES PAY" text
  v3: Facebook stock chart going up + "$5 BILLION FINE" text

YouTube thumbnails: 1280x720, under 2MB, bold readable at 246x138 preview size.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

PROJECT_ROOT = Path(__file__).parent.parent
OUT_DIR = PROJECT_ROOT / "output" / "thumbnails"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ZUCK_PORTRAIT = PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "web" / "zuckerberg_portrait_wiki.jpg"
FB_STOCK = PROJECT_ROOT / "footage" / "breaking_law" / "images_v2" / "web" / "facebook_stock_july_2019_annotated.jpg"
FB_FINE_CLIP = PROJECT_ROOT / "footage" / "breaking_law" / "stills" / "Facebook_FTC_5_billion_dollar_fine_still_8s.jpg"

WIDTH, HEIGHT = 1280, 720

# Try to find decent fonts
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]


def get_font(size, bold=True):
    """Find a bold font."""
    # Impact is classic YouTube thumbnail font — use it first
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_stroked_text(draw, xy, text, font, fill="white", stroke_fill="black",
                     stroke_width=6, anchor="lt"):
    """Draw text with a thick outline for readability."""
    draw.text(xy, text, font=font, fill=fill, anchor=anchor,
              stroke_width=stroke_width, stroke_fill=stroke_fill)


def fit_cover(img, target_w, target_h):
    """Resize + crop image to exactly target size (cover behavior)."""
    src_ratio = img.width / img.height
    tgt_ratio = target_w / target_h
    if src_ratio > tgt_ratio:
        new_h = target_h
        new_w = int(target_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(target_w / src_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


# ─── v1: Zuckerberg + "HE GAINED $1.1 BILLION" ──────────────────────────

def thumbnail_v1():
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 15))

    # Left side: big text (60% of width)
    # Right side: Zuckerberg portrait (40%)
    text_w = int(WIDTH * 0.6)
    portrait_w = WIDTH - text_w

    # Load and fit portrait
    portrait = Image.open(ZUCK_PORTRAIT).convert("RGB")
    portrait = fit_cover(portrait, portrait_w, HEIGHT)
    canvas.paste(portrait, (text_w, 0))

    # Gradient overlay on the left for contrast
    gradient = Image.new("L", (text_w, HEIGHT), 0)
    gd = ImageDraw.Draw(gradient)
    for x in range(text_w):
        shade = int(255 * min(1.0, (text_w - x) / text_w + 0.3))
        gd.line([(x, 0), (x, HEIGHT)], fill=shade)
    black = Image.new("RGB", (text_w, HEIGHT), (0, 0, 0))
    canvas.paste(black, (0, 0), gradient)

    draw = ImageDraw.Draw(canvas)

    # Big number
    num_font = get_font(160)
    subtitle_font = get_font(58)
    small_font = get_font(40)

    # "+$1.1B" in green
    draw_stroked_text(draw, (50, 150), "+$1.1B", num_font,
                      fill=(0, 255, 130), stroke_width=8)

    # "HE MADE" above the number
    draw_stroked_text(draw, (55, 80), "HE MADE", subtitle_font,
                      fill="white", stroke_width=5)

    # Subtitle
    draw_stroked_text(draw, (50, 350), "THE DAY HE WAS", subtitle_font,
                      fill="white", stroke_width=5)
    draw_stroked_text(draw, (50, 410), "FINED $5 BILLION", subtitle_font,
                      fill=(255, 70, 80), stroke_width=5)

    # Channel tag / hook
    draw_stroked_text(draw, (50, 620), "HOW CRIME PAYS", small_font,
                      fill=(255, 220, 80), stroke_width=4)

    out = OUT_DIR / "thumbnail_v1_zuck.jpg"
    canvas.save(out, "JPEG", quality=92)
    return out


# ─── v2: "CRIME DOES PAY" with bar chart ─────────────────────────────────

def thumbnail_v2():
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (245, 245, 248))
    draw = ImageDraw.Draw(canvas)

    # Big title at top
    big_font = get_font(130)
    draw_stroked_text(draw, (WIDTH // 2, 60), "CRIME PAYS",
                      big_font, fill=(230, 57, 70),
                      stroke_fill="white", stroke_width=8, anchor="mt")

    # Sub under title
    sub_font = get_font(44)
    draw_stroked_text(draw, (WIDTH // 2, 210), "The fine is cheaper than the profit.",
                      sub_font, fill=(30, 30, 30),
                      stroke_fill="white", stroke_width=3, anchor="mt")

    # Bar chart below showing 4 fines
    bar_y = 320
    bar_height_max = 330
    bars = [
        ("FORD\n1977", "$3.5M", 8),       # height as % of max
        ("WELLS FARGO\n2020", "$3B", 40),
        ("FACEBOOK\n2019", "$5B", 65),
        ("PURDUE\n2021", "$7.4B", 100),
    ]
    bar_w = 220
    gap = 60
    total_w = len(bars) * bar_w + (len(bars) - 1) * gap
    start_x = (WIDTH - total_w) // 2

    val_font = get_font(52)
    label_font = get_font(32)

    for i, (label, value, pct) in enumerate(bars):
        x = start_x + i * (bar_w + gap)
        h = int(bar_height_max * pct / 100)
        y_top = bar_y + bar_height_max - h
        color = (230, 57, 70) if i == len(bars) - 1 else (15, 98, 254)
        draw.rectangle([x, y_top, x + bar_w, bar_y + bar_height_max], fill=color)
        # Value on top of bar
        draw_stroked_text(draw, (x + bar_w // 2, y_top - 10), value,
                          val_font, fill=(20, 20, 20),
                          stroke_fill="white", stroke_width=3, anchor="mb")
        # Label below bar
        lines = label.split("\n")
        for j, line in enumerate(lines):
            draw.text((x + bar_w // 2, bar_y + bar_height_max + 20 + j * 40),
                      line, font=label_font, fill=(50, 50, 50), anchor="mt")

    out = OUT_DIR / "thumbnail_v2_chart.jpg"
    canvas.save(out, "JPEG", quality=92)
    return out


# ─── v3: Stock chart + "$5B FINE = STOCK UP" ─────────────────────────────

def thumbnail_v3():
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 15))

    # Load the FB stock chart and use as background
    stock = Image.open(FB_STOCK).convert("RGB")
    stock = fit_cover(stock, WIDTH, HEIGHT)
    # Darken
    enh = ImageEnhance.Brightness(stock)
    stock_dark = enh.enhance(0.45)
    canvas.paste(stock_dark, (0, 0))

    draw = ImageDraw.Draw(canvas)

    big_font = get_font(135)
    sub_font = get_font(64)
    equals_font = get_font(110)

    # Top: "$5 BILLION FINE"
    draw_stroked_text(draw, (WIDTH // 2, 60), "$5 BILLION FINE",
                      big_font, fill=(255, 255, 255),
                      stroke_fill="black", stroke_width=10, anchor="mt")

    # Arrow down
    draw_stroked_text(draw, (WIDTH // 2, 235), "↓",
                      equals_font, fill=(255, 220, 80),
                      stroke_fill="black", stroke_width=8, anchor="mt")

    # Bottom: "STOCK WENT UP"
    draw_stroked_text(draw, (WIDTH // 2, 400), "STOCK WENT UP",
                      big_font, fill=(0, 255, 130),
                      stroke_fill="black", stroke_width=10, anchor="mt")

    draw_stroked_text(draw, (WIDTH // 2, 560), "Why breaking the law is profitable",
                      sub_font, fill="white",
                      stroke_fill="black", stroke_width=5, anchor="mt")

    out = OUT_DIR / "thumbnail_v3_stock.jpg"
    canvas.save(out, "JPEG", quality=92)
    return out


if __name__ == "__main__":
    for fn in [thumbnail_v1, thumbnail_v2, thumbnail_v3]:
        out = fn()
        size_kb = out.stat().st_size / 1024
        print(f"  ✓ {out.name}  ({size_kb:.0f} KB)")
    print(f"\nAll saved to: {OUT_DIR}")
