#!/usr/bin/env python3
"""
Measure Fern's exact color grade from keyframes.
Outputs precise LUT parameters: brightness, contrast, saturation, channel offsets.
No API calls. Uses Pillow only.
"""
import json, os
from pathlib import Path
from PIL import Image
import numpy as np

FERN_DIR  = Path("analysis/fern")
VIDEO_IDS = ["aVA7aXOH1pk", "wLFY_Zu_O08", "wkVygetgeRY"]
MAX_FRAMES = 50  # sample up to 50 frames per video

def analyze_frame(img_path):
    try:
        img = Image.open(img_path).convert("RGB").resize((320, 180))
        arr = np.array(img, dtype=np.float32)
        r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

        # Luminance
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Channel means (0-255)
        rm, gm, bm = r.mean(), g.mean(), b.mean()

        # Saturation: (max - min) / max per pixel
        mx = np.maximum(np.maximum(r, g), b)
        mn = np.minimum(np.minimum(r, g), b)
        sat = np.where(mx > 0, (mx - mn) / mx, 0).mean()

        # Contrast: std of luminance
        contrast = lum.std()

        # Shadow: mean of darkest 10% pixels
        flat = lum.flatten()
        threshold = np.percentile(flat, 10)
        shadow_mean = flat[flat <= threshold].mean()

        # Highlight: mean of brightest 10% pixels
        threshold_hi = np.percentile(flat, 90)
        highlight_mean = flat[flat >= threshold_hi].mean()

        return {
            "r_mean": round(float(rm), 1),
            "g_mean": round(float(gm), 1),
            "b_mean": round(float(bm), 1),
            "lum_mean": round(float(lum.mean()), 1),
            "saturation": round(float(sat), 3),
            "contrast_std": round(float(contrast), 1),
            "shadow_mean": round(float(shadow_mean), 1),
            "highlight_mean": round(float(highlight_mean), 1),
        }
    except Exception as e:
        return None


if __name__ == "__main__":
    all_metrics = []

    for vid in VIDEO_IDS:
        kf_dir = FERN_DIR / vid / "hybrid_keyframes"
        if not kf_dir.exists():
            print(f"[SKIP] {vid}")
            continue

        frames = sorted(kf_dir.glob("*.jpg"))[:MAX_FRAMES]
        print(f"\n{vid} — sampling {len(frames)} frames...")

        vid_metrics = []
        for f in frames:
            m = analyze_frame(f)
            if m:
                vid_metrics.append(m)

        if not vid_metrics:
            continue

        # Averages
        keys = vid_metrics[0].keys()
        avg  = {k: round(sum(m[k] for m in vid_metrics) / len(vid_metrics), 2) for k in keys}
        all_metrics.append(avg)

        print(f"  R/G/B means:   {avg['r_mean']:.1f} / {avg['g_mean']:.1f} / {avg['b_mean']:.1f}")
        print(f"  Luminance:     {avg['lum_mean']:.1f}")
        print(f"  Saturation:    {avg['saturation']:.3f}  (1.0 = full, 0 = grey)")
        print(f"  Contrast std:  {avg['contrast_std']:.1f}")
        print(f"  Shadow mean:   {avg['shadow_mean']:.1f}  (0=pure black)")
        print(f"  Highlight mean:{avg['highlight_mean']:.1f}  (255=pure white)")

    if all_metrics:
        # Grand average across all videos
        keys = all_metrics[0].keys()
        grand = {k: round(sum(m[k] for m in all_metrics) / len(all_metrics), 2) for k in keys}

        print(f"\n{'='*55}")
        print("GRAND AVERAGE (all videos combined)")
        print(f"{'='*55}")
        print(f"  R/G/B:         {grand['r_mean']} / {grand['g_mean']} / {grand['b_mean']}")
        print(f"  Luminance:     {grand['lum_mean']}")
        print(f"  Saturation:    {grand['saturation']}  (natural=~0.35, Fern should be <0.30)")
        print(f"  Shadow mean:   {grand['shadow_mean']}  (crushed blacks = <20)")
        print(f"  Highlight mean:{grand['highlight_mean']}")

        # Derive FFmpeg filter
        # Normalize: natural image has R≈G≈B≈128, sat≈0.35, lum≈128
        brightness_offset = round((grand['lum_mean'] - 110) / 255, 3)  # relative to dark target
        saturation_ratio  = round(grand['saturation'] / 0.35, 2)        # ratio to natural
        contrast_ratio    = round(grand['contrast_std'] / 55, 2)        # ratio to natural

        # Channel shift: blue bias means b > r
        r_shift = round((grand['r_mean'] - grand['g_mean']) / 255, 3)
        b_shift = round((grand['b_mean'] - grand['g_mean']) / 255, 3)

        print(f"\n  {'='*50}")
        print(f"  DERIVED FFMPEG FILTER:")
        print(f"  eq=contrast={contrast_ratio}:brightness={brightness_offset}:saturation={saturation_ratio}")
        if abs(b_shift) > 0.02 or abs(r_shift) > 0.02:
            print(f"  colorchannelmixer: r_shift={r_shift:.3f}  b_shift={b_shift:.3f}")
            print(f"  (blue channel {'boosted' if b_shift > 0 else 'reduced'} — {'cold teal grade' if b_shift > 0 else 'warm grade'})")

        result = {
            "grand_avg":      grand,
            "per_video":      all_metrics,
            "ffmpeg_filter": {
                "eq": f"eq=contrast={contrast_ratio}:brightness={brightness_offset}:saturation={saturation_ratio}",
                "b_channel_shift": b_shift,
                "r_channel_shift": r_shift,
                "interpretation": "cold_blue_teal" if b_shift > 0.02 else "warm" if r_shift > 0.02 else "neutral",
            }
        }
        out = FERN_DIR / "COLOR_GRADE_FORMULA.json"
        with open(out, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved: {out}")
