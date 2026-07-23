#!/usr/bin/env python3
"""
Episode 02 thumbnail ship gate.

Composites the LOCKED text treatment onto a candidate base image and then
measures the four things the spec actually asserts, instead of eyeballing them:

  1. BLOOD AREA      wound >= 12% of frame area
  2. BLOOD SALIENCE  the wound is the most saturated element in frame
  3. TEXT PLATE      the left third is dark enough that #FFD400 reads on it
  4. 168x94 GATE     at browse size the red survives as a readable mark

Locked text spec (EPISODE_02_VAMPIRE_FINCH_STORYBOARD.md Step 0):
  BLOOD    -> #FFD400 yellow
  FOR EGGS -> white
  heavy condensed sans, 8-10px black outline, stacked 2 lines, left third.

Usage:
  venv/bin/python research/wildbirdsurvival_teardown/thumb_gate.py BASE.png OUTDIR [--tag name]
  venv/bin/python research/wildbirdsurvival_teardown/thumb_gate.py BASE.png OUTDIR --no-text
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

YELLOW = (255, 212, 0)
WHITE = (255, 255, 255)
FONT_PATH = "/System/Library/Fonts/Supplemental/Impact.ttf"

# Gate thresholds, straight from the locked spec.
MIN_BLOOD_AREA_PCT = 12.0
MIN_LEFT_THIRD_DARKNESS = 0.55   # 1.0 = black. yellow needs a dark plate.
MIN_BLOB_PX_AT_168 = 12.0        # a red mark smaller than this vanishes when browsing
GATE_W, GATE_H = 168, 94


def rgb_to_hsv_arr(rgb):
    """Vectorised RGB->HSV. rgb float in 0..1. Returns h(0..360), s(0..1), v(0..1)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    diff = mx - mn
    h = np.zeros_like(mx)
    mask = diff > 1e-6
    # red is max
    idx = mask & (mx == r)
    h[idx] = (60 * ((g[idx] - b[idx]) / diff[idx])) % 360
    idx = mask & (mx == g)
    h[idx] = (60 * ((b[idx] - r[idx]) / diff[idx]) + 120) % 360
    idx = mask & (mx == b)
    h[idx] = (60 * ((r[idx] - g[idx]) / diff[idx]) + 240) % 360
    s = np.zeros_like(mx)
    s[mx > 1e-6] = diff[mx > 1e-6] / mx[mx > 1e-6]
    return h, s, mx


def blood_mask(img):
    """Boolean mask of pixels that read as blood: red hue, meaningfully saturated,
    not so dark they read as shadow."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    h, s, v = rgb_to_hsv_arr(a)
    red_hue = (h <= 20) | (h >= 340)
    return red_hue & (s >= 0.35) & (v >= 0.18), s, v


def largest_blob(mask):
    """Largest 4-connected component size, in pixels. Pure numpy flood fill via
    iterative dilation on labels - fine at these image sizes."""
    if not mask.any():
        return 0, None
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    cur = 0
    best, best_lbl = 0, None
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if labels[y0, x0]:
            continue
        cur += 1
        stack = [(y0, x0)]
        labels[y0, x0] = cur
        size = 0
        while stack:
            y, x = stack.pop()
            size += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = cur
                    stack.append((ny, nx))
        if size > best:
            best, best_lbl = size, cur
    return best, (labels == best_lbl if best_lbl else None)


CAP_RATIO = 0.72          # Impact cap height as a fraction of point size
BLOOD_CAP_FRAC = 0.16     # spec: cap height of BLOOD >= 15% of frame height
BLOOD_REL = 1.10          # spec: BLOOD set ~110% the size of FOR EGGS
MAX_LINE_W = 0.46         # keep the long line inside the left plate


def _type_metrics(W, H):
    """Point sizes for the two lines, per the recovered full type spec."""
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    s_blood = (BLOOD_CAP_FRAC * H) / CAP_RATIO
    s_eggs = s_blood / BLOOD_REL
    # shrink both together if the long line would overrun the plate
    f = ImageFont.truetype(FONT_PATH, int(s_eggs))
    w = probe.textlength("FOR EGGS", font=f)
    if w > W * MAX_LINE_W:
        k = (W * MAX_LINE_W) / w
        s_blood *= k
        s_eggs *= k
    return int(s_blood), int(s_eggs), int(W * 0.035)


def _lines(W, H):
    s_blood, s_eggs, x = _type_metrics(W, H)
    fb = ImageFont.truetype(FONT_PATH, s_blood)
    fe = ImageFont.truetype(FONT_PATH, s_eggs)
    hb, he = s_blood * CAP_RATIO, s_eggs * CAP_RATIO
    total = hb + he * 1.28
    y = H * 0.5 - total / 2
    return [("BLOOD", YELLOW, fb, s_blood, x, int(y)),
            ("FOR EGGS", WHITE, fe, s_eggs, x, int(y + hb * 1.30))], total


def text_box(W, H):
    """The rectangle the type actually occupies, so the darkness metric measures
    the real plate rather than the whole left third."""
    lines, total = _lines(W, H)
    x = lines[0][4]
    y0 = lines[0][5]
    return x, y0, int(W * MAX_LINE_W) + x, int(y0 + total * 1.15)


def add_plate(img, width_frac=0.35, max_opacity=0.55):
    """Recovered spec's fallback: a left-edge linear gradient black->transparent,
    for bases whose left third is not naturally dark enough."""
    img = img.convert("RGB")
    W, H = img.size
    grad = Image.new("L", (W, 1), 0)
    px = grad.load()
    span = max(1, int(W * width_frac))
    for x in range(W):
        px[x, 0] = int(255 * max_opacity * max(0.0, 1.0 - x / span)) if x < span else 0
    mask = grad.resize((W, H))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, mask)


def draw_text_block(img):
    """Burn in the locked 2-line treatment: heavy condensed sans, 8-10px black
    outline PLUS a soft drop shadow at 60% opacity (recovered full spec)."""
    img = img.convert("RGB")
    W, H = img.size
    lines, _ = _lines(W, H)

    # soft drop shadow on its own layer so it can be blurred and faded
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    off = max(3, int(H * 0.006))
    for text, _c, font, size, x, y in lines:
        sd.text((x + off, y + off), text, font=font, fill=(0, 0, 0, 153))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, int(H * 0.005))))
    img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")

    d = ImageDraw.Draw(img)
    for text, colour, font, size, x, y in lines:
        d.text((x, y), text, font=font, fill=colour,
               stroke_width=max(8, int(size * 0.085)), stroke_fill=(0, 0, 0))
    return img


def selective_grade(img, desat=0.13, red_boost=1.18, red_lift=1.06):
    """Recovered spec: desaturate everything except the blood by 10-15%, and keep
    white feather detail below 250. Raises the red's read at browse size without
    adding any more blood to the frame."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    h, s, v = rgb_to_hsv_arr(a)
    red = ((h <= 22) | (h >= 338)) & (s >= 0.22)

    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    out = np.where(red[..., None],
                   np.clip(lum + (a - lum) * red_boost, 0, 1) * red_lift,
                   lum + (a - lum) * (1.0 - desat))
    out = np.clip(out, 0, 1)
    # hold whites off the clip point so feather detail survives
    out = np.clip(out, 0, 250 / 255.0)
    return Image.fromarray((out * 255).astype(np.uint8))


def measure(img, label):
    W, H = img.size
    mask, s, v = blood_mask(img)
    area_pct = 100.0 * mask.sum() / (W * H)

    # salience: mean saturation inside the red mask vs the rest of frame
    if mask.any():
        sal_in = float(s[mask].mean())
        sal_out = float(s[~mask].mean())
    else:
        sal_in = sal_out = 0.0

    # text plate: how dark is the area the type actually sits on
    lum = np.asarray(img.convert("L"), dtype=np.float32) / 255.0
    x0, y0, x1, y1 = text_box(W, H)
    plate = lum[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
    darkness = 1.0 - float(plate.mean()) if plate.size else 0.0
    left_third_darkness = 1.0 - float(lum[:, : W // 3].mean())

    # browse-size survival
    small = img.resize((GATE_W, GATE_H), Image.LANCZOS)
    smask, _, _ = blood_mask(small)
    blob_px, _ = largest_blob(smask)
    small_area_pct = 100.0 * smask.sum() / (GATE_W * GATE_H)

    return {
        "label": label,
        "size": [W, H],
        "blood_area_pct": round(area_pct, 2),
        "blood_sat_mean": round(sal_in, 3),
        "rest_sat_mean": round(sal_out, 3),
        "blood_is_most_saturated": bool(sal_in > sal_out * 1.6 and sal_in > 0.45),
        "text_plate_darkness": round(darkness, 3),
        "left_third_darkness": round(left_third_darkness, 3),
        "at_168x94_red_px": int(smask.sum()),
        "at_168x94_largest_blob_px": int(blob_px),
        "at_168x94_red_area_pct": round(small_area_pct, 2),
    }


def verdict(m):
    checks = [
        ("BLOOD AREA >= %.0f%% of frame" % MIN_BLOOD_AREA_PCT,
         m["blood_area_pct"] >= MIN_BLOOD_AREA_PCT,
         "%.2f%%" % m["blood_area_pct"]),
        ("BLOOD is the most saturated element",
         m["blood_is_most_saturated"],
         "blood sat %.3f vs rest %.3f" % (m["blood_sat_mean"], m["rest_sat_mean"])),
        ("TEXT PLATE dark enough for #FFD400 (>= %.2f)" % MIN_LEFT_THIRD_DARKNESS,
         m["text_plate_darkness"] >= MIN_LEFT_THIRD_DARKNESS,
         "%.3f under type (left third %.3f)" % (m["text_plate_darkness"], m["left_third_darkness"])),
        ("168x94: red survives as a mark (>= %.0f px blob)" % MIN_BLOB_PX_AT_168,
         m["at_168x94_largest_blob_px"] >= MIN_BLOB_PX_AT_168,
         "%d px blob, %d px total" % (m["at_168x94_largest_blob_px"], m["at_168x94_red_px"])),
    ]
    return checks, all(c[1] for c in checks)


def gate_sheet(img, out):
    """1280x720 composite on top, the true 168x94 nearest-upscaled 4x below it.
    Nearest-neighbour adds no information, so the lower panel shows exactly what
    survives at browse size."""
    small = img.resize((GATE_W, GATE_H), Image.LANCZOS)
    blown = small.resize((GATE_W * 4, GATE_H * 4), Image.NEAREST)
    W = max(img.width, blown.width + 40)
    sheet = Image.new("RGB", (W, img.height + blown.height + 90), (24, 24, 26))
    sheet.paste(img, ((W - img.width) // 2, 0))
    sheet.paste(blown, ((W - blown.width) // 2, img.height + 60))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_PATH, 26)
    d.text((20, img.height + 20), "168x94 SHIP GATE  (true browse size, 4x nearest - no detail added)",
           font=f, fill=(255, 212, 0))
    # also paste the true-size chip at top-left of the gate panel
    sheet.paste(small, (20, img.height + 60))
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("outdir")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--no-text", action="store_true", help="measure the plate before text is burned in")
    ap.add_argument("--plate", action="store_true", help="add the left-edge dark gradient fallback before setting type")
    ap.add_argument("--grade", action="store_true", help="selective grade: desaturate non-red 13%, lift the red")
    ap.add_argument("--crop", default=None, help="x,y,w,h crop applied before anything else")
    args = ap.parse_args()

    tag = args.tag or os.path.splitext(os.path.basename(args.base))[0]
    os.makedirs(args.outdir, exist_ok=True)

    img = Image.open(args.base).convert("RGB")
    if args.crop:
        cx, cy, cw, ch = (int(t) for t in args.crop.split(","))
        img = img.crop((cx, cy, cx + cw, cy + ch))
    if args.grade:
        img = selective_grade(img)
    if img.size != (1280, 720):
        img = img.resize((1280, 720), Image.LANCZOS)

    if args.plate:
        img = add_plate(img)
    composed = img if args.no_text else draw_text_block(img)
    comp_path = os.path.join(args.outdir, f"{tag}_composed.png")
    composed.save(comp_path)

    small_path = os.path.join(args.outdir, f"{tag}_168x94.png")
    composed.resize((GATE_W, GATE_H), Image.LANCZOS).save(small_path)

    sheet_path = os.path.join(args.outdir, f"{tag}_GATE.png")
    gate_sheet(composed, sheet_path)

    m = measure(composed, tag)
    checks, ok = verdict(m)

    print(f"\n=== THUMBNAIL SHIP GATE: {tag} ===")
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<48} {detail}")
    print(f"  ---> {'SHIP' if ok else 'RECOMPOSE'}\n")
    print(f"  composed : {comp_path}")
    print(f"  168x94   : {small_path}")
    print(f"  gate sheet: {sheet_path}")

    m["verdict"] = "SHIP" if ok else "RECOMPOSE"
    m["checks"] = [{"check": c[0], "pass": bool(c[1]), "value": c[2]} for c in checks]
    with open(os.path.join(args.outdir, f"{tag}_gate.json"), "w") as fh:
        json.dump(m, fh, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
