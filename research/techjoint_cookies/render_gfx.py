#!/usr/bin/env python3
"""Render the on-screen graphics PNGs for the cookie video (1920x1080 space).

Clean influencer style: white rounded pills, near-black text, soft shadow;
rule banners carry a small amber accent; timers get a ring; recipe card = a
left-55% panel. Output: assets/techjoint_cookies/gfx/<key>.png (RGBA).
Positions are stored in gfx_manifest.json (x,y of the top-left corner).
"""
import json, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "assets", "techjoint_cookies", "gfx")
os.makedirs(OUT, exist_ok=True)

AV = "/System/Library/Fonts/Avenir Next.ttc"
def font(size, face="demi"):
    idx = {"bold": 0, "demi": 2, "medium": 5, "regular": 7, "heavy": 8}[face]
    return ImageFont.truetype(AV, size, index=idx)

INK = (28, 20, 14, 255)
INK2 = (95, 78, 66, 255)
AMBER = (184, 104, 26, 255)
WHITE = (255, 255, 255, 242)
W, H = 1920, 1080


def shadow(img, blur=18, off=(0, 10), alpha=70):
    base = Image.new("RGBA", (img.width + 80, img.height + 80), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    a = img.split()[3].point(lambda v: int(v * alpha / 255))
    sh.putalpha(a)
    base.paste(sh, (40 + off[0], 40 + off[1]), sh)
    base = base.filter(ImageFilter.GaussianBlur(blur))
    base.paste(img, (40, 40), img)
    return base


def pill(text, size=44, face="demi", pad=(34, 18), fill=WHITE, color=INK, accent=None, radius=None):
    f = font(size, face)
    tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    acc_w = (size // 2 + 18) if accent else 0
    w, h = tw + pad[0] * 2 + acc_w, th + pad[1] * 2
    r = radius if radius is not None else h // 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    x = pad[0]
    if accent:
        cy = h // 2; rr = size // 4
        d.ellipse((x, cy - rr, x + 2 * rr, cy + rr), fill=accent)
        x += acc_w
    d.text((x - bbox[0], pad[1] - bbox[1]), text, font=f, fill=color)
    return shadow(img)


def title(text):
    # two-line stacked title: "CRISPY OUTSIDE" / "GOOEY INSIDE"
    a, b = text.split(" · ")
    fa = font(96, "heavy"); fb = font(96, "heavy")
    tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
    ba = d.textbbox((0, 0), a, font=fa); bb = d.textbbox((0, 0), b, font=fb)
    w = max(ba[2] - ba[0], bb[2] - bb[0]) + 120
    h = (ba[3] - ba[1]) + (bb[3] - bb[1]) + 110
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=WHITE)
    y = 40
    d.text(((w - (ba[2] - ba[0])) // 2 - ba[0], y - ba[1]), a, font=fa, fill=INK)
    y += (ba[3] - ba[1]) + 26
    d.text(((w - (bb[2] - bb[0])) // 2 - bb[0], y - bb[1]), b, font=fb, fill=AMBER)
    return shadow(img, blur=28, off=(0, 14), alpha=90)


def timer(text):
    f = font(40, "demi")
    tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ring = 58
    w, h = tw + ring + 34 + 28, max(th + 36, ring + 20)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=WHITE)
    cx, cy = 12 + ring // 2, h // 2
    d.ellipse((cx - ring // 2, cy - ring // 2, cx + ring // 2, cy + ring // 2), outline=(230, 222, 210, 255), width=6)
    d.arc((cx - ring // 2, cy - ring // 2, cx + ring // 2, cy + ring // 2), start=-90, end=200, fill=AMBER, width=6)
    d.text((12 + ring + 16 - bbox[0], (h - th) // 2 - bbox[1]), text, font=f, fill=INK)
    return shadow(img)


def recipe_card():
    w, h = 1000, 1000
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=(255, 255, 255, 236))
    y = 44
    d.text((52, y), "CRISPY OUTSIDE, GOOEY INSIDE", font=font(46, "heavy"), fill=INK); y += 62
    d.text((52, y), "Brown-butter chocolate chip cookies · makes ~14", font=font(27, "medium"), fill=INK2); y += 36
    d.text((52, y), "375°F / 190°C · 10–12 min · chill the dough 30 min", font=font(27, "medium"), fill=INK2); y += 44
    d.line((52, y, w - 52, y), fill=(232, 224, 212, 255), width=3); y += 26
    ing = [
        "1 cup (226 g) butter, browned, cooled 10 min",
        "1 cup (200 g) dark brown sugar, packed",
        "½ cup (100 g) white sugar",
        "1 egg + 1 extra yolk",
        "2 tsp vanilla",
        "2¼ cups (280 g) flour",
        "1 tsp baking soda · ¾ tsp salt",
        "1½ cups (255 g) chocolate — ½ chopped bar, ½ chips",
        "flaky salt to finish",
    ]
    steps = [
        "Brown the butter; cool 10 min.",
        "Whisk in both sugars ~1 min.",
        "Whisk in egg + yolk + vanilla till glossy.",
        "Fold in flour, soda, salt — stop at no dry flour.",
        "Fold in chocolate. Scoop big (~3 Tbsp).",
        "CHILL 30 min. Bake 375°F 10–12 min.",
        "Tap tray, flaky salt, rest 5 min. Pull apart.",
    ]
    fi = font(30, "medium"); fs = font(30, "medium"); fh = font(24, "demi")
    d.text((52, y), "INGREDIENTS", font=fh, fill=AMBER); y += 40
    for s in ing:
        d.ellipse((56, y + 13, 66, y + 23), fill=AMBER)
        d.text((82, y), s, font=fi, fill=INK); y += 42
    y += 14
    d.text((52, y), "METHOD", font=fh, fill=AMBER); y += 40
    for i, s in enumerate(steps, 1):
        d.text((56, y), f"{i}.", font=fs, fill=AMBER)
        d.text((96, y), s, font=fs, fill=INK); y += 42
    return shadow(img, blur=30, off=(0, 16), alpha=90)


SPEC = {
    # key: (kind, text, anchor) ; anchor = where the top-left goes, computed below
    "title":        ("title", "CRISPY OUTSIDE · GOOEY INSIDE", "center"),
    "rule1":        ("banner", "RULE #1 · BROWN THE BUTTER", "bl"),
    "rule2":        ("banner", "RULE #2 · EXTRA YOLK", "bl"),
    "rule3":        ("banner", "RULE #3 · CHILL THE DOUGH", "bl"),
    "ing_butter":   ("pill", "butter", "list0"),
    "ing_brown":    ("pill", "brown sugar", "list1"),
    "ing_white":    ("pill", "white sugar", "list2"),
    "ing_egg":      ("pill", "1 egg + 1 extra yolk", "list3"),
    "ing_vanilla":  ("pill", "vanilla", "list4"),
    "ing_flour":    ("pill", "flour", "list5"),
    "ing_soda":     ("pill", "baking soda + salt", "list6"),
    "ing_choc":     ("pill", "way too much chocolate", "list7"),
    "toffee":       ("pill_s", "smells like toffee", "tr"),
    "cool10":       ("timer", "COOL 10 MIN", "tr"),
    "c_brown":      ("pill_s", "1 cup brown sugar", "tr"),
    "c_white":      ("pill_s", "½ cup white sugar", "tr2"),
    "yolk":         ("pill", "+1 YOLK = gooey centre", "tr"),
    "c_flour":      ("pill_s", "2¼ cups flour", "tr"),
    "c_soda":       ("pill_s", "1 tsp soda · ¾ tsp salt", "tr"),
    "stop":         ("pill", "stop here — no dry flour", "tr"),
    "c_choc":       ("pill_s", "1½ cups chocolate", "tr"),
    "scoop":        ("pill_s", "~3 Tbsp each", "tr"),
    "chill30":      ("timer", "CHILL 30 MIN", "tr"),
    "chill_done":   ("pill_s", "30 MIN — DONE", "tr"),
    "temp":         ("pill", "375°F / 190°C", "tr"),
    "bake":         ("timer", "10–12 MIN", "tr"),
    "rest":         ("pill", "5 MIN — the hardest part", "tr"),
    "crispy":       ("word", "CRISPY", "center"),
    "gooey":        ("word", "GOOEY", "center"),
    "card":         ("card", "", "card"),
}

def render(kind, text):
    if kind == "title": return title(text)
    if kind == "banner": return pill(text, 46, "bold", pad=(38, 20), accent=AMBER, radius=22)
    if kind == "pill": return pill(text, 42, "demi")
    if kind == "pill_s": return pill(text, 36, "medium", pad=(28, 14))
    if kind == "timer": return timer(text)
    if kind == "word": return pill(text, 110, "heavy", pad=(60, 26), color=AMBER)
    if kind == "card": return recipe_card()
    raise ValueError(kind)

def place(anchor, w, h):
    M = 72
    if anchor == "center": return ((W - w) // 2, (H - h) // 2 + 120)
    if anchor == "bl": return (M, H - h - M)
    if anchor == "tr": return (W - w - M, M + 40)
    if anchor == "tr2": return (W - w - M, M + 40 + 96)
    if anchor.startswith("list"):
        i = int(anchor[4:]); return (M, 110 + i * 96)
    if anchor == "card": return (60, (H - h) // 2)
    raise ValueError(anchor)

man = {}
for key, (kind, text, anchor) in SPEC.items():
    img = render(kind, text)
    p = os.path.join(OUT, f"{key}.png"); img.save(p)
    x, y = place(anchor, img.width, img.height)
    man[key] = {"file": os.path.relpath(p, REPO), "w": img.width, "h": img.height, "x": x, "y": y, "kind": kind, "text": text}
json.dump(man, open(os.path.join(OUT, "gfx_manifest.json"), "w"), indent=1, ensure_ascii=False)
print(f"rendered {len(man)} graphics -> {OUT}")
