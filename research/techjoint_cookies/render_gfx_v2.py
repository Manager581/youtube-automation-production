#!/usr/bin/env python3
"""v2 graphics: ONE register of small static captions (white, sentence case, soft shadow, bottom-left) — the
silent-recipe convention from the competitor pool (a little calm / Pinch of Warmth) — plus the existing recipe card.
No pills, no timers, no word pops, no title pop. Output: assets/techjoint_cookies/gfx_v2/*.png + gfx_manifest.json."""
import json, os, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "assets", "techjoint_cookies", "gfx_v2")
V1 = os.path.join(REPO, "assets", "techjoint_cookies", "gfx")
os.makedirs(OUT, exist_ok=True)
AV = "/System/Library/Fonts/Avenir Next.ttc"
W, H = 1920, 1080
AMBER = (232, 168, 84, 235)


def font(size, face="medium"):
    idx = {"bold": 0, "demi": 2, "medium": 5, "regular": 7, "heavy": 8}[face]
    return ImageFont.truetype(AV, size, index=idx)


def caption(text, size=38, face="medium", accent_prefix=None):
    """Plain white text with a soft dark shadow (legible on bright counters). accent_prefix renders 'rule #n' in amber."""
    f = font(size, face)
    tmp = Image.new("RGBA", (10, 10)); d = ImageDraw.Draw(tmp)
    parts = [(accent_prefix, AMBER), (text, (255, 255, 255, 240))] if accent_prefix else [(text, (255, 255, 255, 240))]
    widths = []; bb = None
    for t, _ in parts:
        b = d.textbbox((0, 0), t, font=f); widths.append(b[2] - b[0]); bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), 0, max(bb[3], b[3]))
    gap = 14 if accent_prefix else 0
    tw = sum(widths) + gap * (len(parts) - 1); th = bb[3] - bb[1]
    pad = 24
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    # shadow layer
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    x = pad
    for (t, col), w in zip(parts, widths):
        ds.text((x - bb[0] + 2, pad - bb[1] + 3), t, font=f, fill=(0, 0, 0, 150)); x += w + gap
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(sh)
    x = pad
    for (t, col), w in zip(parts, widths):
        d.text((x - bb[0], pad - bb[1]), t, font=f, fill=col); x += w + gap
    return sh


SPEC = {
    # key: (text, accent_prefix, anchor)
    "hook_claim": ("crispy outside · gooey inside", None, "bl"),
    "cap_choc":   ("way too much chocolate", None, "bl"),
    "rule1":      ("brown the butter", "rule #1", "bl"),
    "toffee":     ("smells like toffee", None, "bl"),
    "cool10":     ("cool 10 min", None, "bl"),
    "sugars":     ("1 cup brown · ½ cup white", None, "bl"),
    "rule2":      ("one extra yolk", "rule #2", "bl"),
    "flour":      ("2¼ cups flour", None, "bl"),
    "soda":       ("1 tsp baking soda · ¾ tsp salt", None, "bl"),
    "stop":       ("stop here — no dry flour", None, "bl"),
    "choc":       ("1½ cups chocolate — half chopped, half chips", None, "bl"),
    "scoop":      ("big scoops — about 3 tbsp", None, "bl"),
    "rule3":      ("chill the dough", "rule #3", "bl"),
    "chill30":    ("30 min minimum", None, "bl"),
    "temp":       ("375 °F / 190 °C · 10–12 min", None, "bl"),
    "bake":       ("pull them when the edges are golden and the middle still looks underdone", None, "bl"),
    "rest":       ("5 min — the hardest part", None, "bl"),
}

man = {}
for key, (text, acc, anchor) in SPEC.items():
    size = 44 if acc else 38
    img = caption(text, size=size, face="demi" if acc else "medium", accent_prefix=acc)
    p = os.path.join(OUT, f"{key}.png"); img.save(p)
    M = 80
    x, y = M, H - img.height - M + 10
    man[key] = {"file": os.path.relpath(p, REPO), "w": img.width, "h": img.height, "x": x, "y": y, "kind": "caption", "text": text}
# recipe card: reuse the v1 PNG + placement
v1man = json.load(open(os.path.join(V1, "gfx_manifest.json")))
shutil.copy(os.path.join(REPO, v1man["card"]["file"]), os.path.join(OUT, "card.png"))
man["card"] = dict(v1man["card"]); man["card"]["file"] = os.path.relpath(os.path.join(OUT, "card.png"), REPO)
json.dump(man, open(os.path.join(OUT, "gfx_manifest.json"), "w"), indent=1, ensure_ascii=False)
print(f"rendered {len(man)} graphics -> {OUT}")
