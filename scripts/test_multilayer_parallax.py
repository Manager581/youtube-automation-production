#!/usr/bin/env python3
"""
Multi-layer parallax prototype.

Splits an image into discrete depth layers, inpaints gaps,
moves each layer independently, and composites with atmospheric
elements between layers for a living 2.5D scene.

Usage:
    venv/bin/python scripts/test_multilayer_parallax.py
"""

import math
import os
import subprocess
import sys

import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.parallax_renderer import ParallaxEngine, get_font, color_grade, add_vignette

# ── Config ─────────────────────────────────────────────────────────────────

W, H, FPS = 1920, 1080, 30
NUM_LAYERS = 4          # background, mid-far, mid-near, foreground
FEATHER_PX = 12         # edge softness between layers
DURATION_SEC = 8.0      # test clip length

IMG_DIR = "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"
OUT_PATH = "output/test_multilayer_composite.mp4"


# ── Layer Extraction ───────────────────────────────────────────────────────

def extract_layers(image_arr, depth_arr, num_layers=4, feather=12):
    """
    Split image into discrete depth layers with feathered alpha masks.

    Returns list of (layer_rgba, depth_band_center) from back to front.
    Each layer_rgba is (H, W, 4) with alpha from the feathered depth mask.
    """
    h, w = image_arr.shape[:2]
    layers = []

    # Create depth thresholds
    thresholds = np.linspace(0, 1, num_layers + 1)

    for i in range(num_layers):
        lo, hi = thresholds[i], thresholds[i + 1]
        band_center = (lo + hi) / 2.0

        # Hard mask for this depth band
        mask = ((depth_arr >= lo) & (depth_arr < hi)).astype(np.float32)

        # Feather edges with gaussian blur
        if feather > 0:
            mask = cv2.GaussianBlur(mask, (0, 0), feather)

        # Create RGBA layer
        layer_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        layer_rgba[:, :, :3] = image_arr
        layer_rgba[:, :, 3] = (mask * 255).astype(np.uint8)

        layers.append((layer_rgba, band_center))

    return layers


def inpaint_layer(layer_rgba, original_image=None):
    """
    Fill ONLY the holes in a layer — keep existing pixels perfectly sharp.

    Uses heavily blurred original to fill gaps, with a soft edge transition
    so the fill blends naturally where foreground was removed.
    """
    rgb = layer_rgba[:, :, :3].copy()
    alpha = layer_rgba[:, :, 3]

    # Mask: where this layer has no content (holes to fill)
    hole_mask = (alpha < 30).astype(np.float32)

    if np.sum(hole_mask) < 100:
        result = layer_rgba.copy()
        result[:, :, 3] = 255
        return result

    # Create fill content from blurred original
    source = original_image if original_image is not None else rgb
    blurred_fill = cv2.GaussianBlur(source, (0, 0), 30)

    # Soften the hole edge so the fill blends smoothly at borders
    soft_mask = cv2.GaussianBlur(hole_mask, (0, 0), 15)
    soft_mask3 = soft_mask[:, :, np.newaxis]

    # Composite: sharp original where we have content, blurred fill in holes
    filled = rgb.astype(np.float32) * (1 - soft_mask3) + blurred_fill.astype(np.float32) * soft_mask3

    result = layer_rgba.copy()
    result[:, :, :3] = np.clip(filled, 0, 255).astype(np.uint8)
    result[:, :, 3] = 255

    return result


# ── Atmospheric Elements ──────────────────────────────────────────────────

def create_fog_layer(w, h, t, density=0.15):
    """
    Create a semi-transparent fog/haze layer that drifts slowly.
    Adds depth between layers.
    """
    fog = np.zeros((h, w, 4), dtype=np.float32)

    # Generate smooth noise using overlapping circles
    rng = np.random.RandomState(42)
    n_blobs = 30
    for _ in range(n_blobs):
        cx = int((rng.uniform(0, w) + t * 15) % w)
        cy = int(rng.uniform(h * 0.3, h * 0.9))  # fog hugs lower 2/3
        radius = rng.randint(150, 400)

        yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)
        blob = np.clip(1.0 - dist / radius, 0, 1) ** 2

        fog[:, :, 0] += blob * 200  # warm-ish fog
        fog[:, :, 1] += blob * 195
        fog[:, :, 2] += blob * 190
        fog[:, :, 3] += blob * 255 * density

    return np.clip(fog, 0, 255).astype(np.uint8)


def create_ground_elements(w, h, t, seed=123):
    """
    Create foreground ground-level elements (grass blades, debris)
    that sway gently. These go in the very front layer.
    """
    layer = np.zeros((h, w, 4), dtype=np.uint8)
    rng = np.random.RandomState(seed)

    n_blades = 80
    for i in range(n_blades):
        # Grass blades rising from bottom edge
        base_x = rng.randint(0, w)
        blade_h = rng.randint(40, 150)
        blade_w = rng.randint(2, 5)

        # Sway with wind
        sway = math.sin(t * 1.5 + i * 0.3) * 15

        # Green tones (slightly varied)
        g = rng.randint(60, 120)
        r = rng.randint(20, 50)
        b = rng.randint(15, 40)
        alpha_val = rng.randint(100, 200)

        # Draw blade as a curved line from bottom
        for dy in range(blade_h):
            frac = dy / blade_h
            x = int(base_x + sway * frac * frac)  # quadratic sway
            y = h - 1 - dy
            if 0 <= y < h and 0 <= x < w:
                x_lo = max(0, x - blade_w)
                x_hi = min(w, x + blade_w + 1)
                # Taper: thinner at top
                local_w = max(1, int(blade_w * (1 - frac * 0.7)))
                x_lo = max(0, x - local_w)
                x_hi = min(w, x + local_w + 1)

                fade = 1.0 - frac * 0.6  # dimmer at tip
                layer[y, x_lo:x_hi, 0] = int(r * fade)
                layer[y, x_lo:x_hi, 1] = int(g * fade)
                layer[y, x_lo:x_hi, 2] = int(b * fade)
                layer[y, x_lo:x_hi, 3] = int(alpha_val * fade * (1 - frac * 0.3))

    # Blur slightly for softness
    layer_rgb = cv2.GaussianBlur(layer[:, :, :3], (3, 3), 1)
    layer_a = cv2.GaussianBlur(layer[:, :, 3], (3, 3), 1)
    layer[:, :, :3] = layer_rgb
    layer[:, :, 3] = layer_a

    return layer


# ── Multi-Layer Compositing ───────────────────────────────────────────────

def offset_layer(layer_rgba, dx, dy):
    """Translate a layer by (dx, dy) pixels using affine transform."""
    h, w = layer_rgba.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(layer_rgba, M, (w, h),
                          borderMode=cv2.BORDER_REFLECT_101)


def composite_rgba_over(base, overlay):
    """Alpha-composite overlay onto base. Both are (H, W, 4) uint8."""
    if overlay.shape[2] < 4:
        return base

    alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0

    result = base.copy().astype(np.float32)
    result[:, :, :3] = result[:, :, :3] * (1 - alpha) + overlay[:, :, :3].astype(np.float32) * alpha
    result[:, :, 3] = np.clip(result[:, :, 3].astype(np.float32) + overlay[:, :, 3].astype(np.float32), 0, 255)

    return result.astype(np.uint8)


def render_multilayer_frame(layers_inpainted, depth_centers, t, motion_type="slow_zoom_in",
                             speed=3.0, fog_enabled=True, ground_enabled=True):
    """
    Render one frame with independent layer motion + atmospheric elements.

    layers_inpainted: list of (H, W, 4) RGBA arrays, back-to-front
    depth_centers: list of floats, depth band center for each layer
    t: normalized time [0, 1]

    Returns (H, W, 3) RGB frame.
    """
    h, w = layers_inpainted[0].shape[:2]

    # Compute per-layer motion amounts
    # Back layers move LESS (farther away), front layers move MORE
    if motion_type == "slow_zoom_in":
        base_scale = t * speed * 0.025
    elif motion_type == "slow_zoom_out":
        base_scale = (1 - t) * speed * 0.025
    else:
        base_scale = t * speed * 0.015

    # Direction offsets — BIG motion for visible parallax
    if motion_type in ("pan_right", "pan_left"):
        sign = 1 if motion_type == "pan_right" else -1
        base_dx = sign * t * speed * 50
        base_dy = 0
    elif motion_type in ("pan_up", "pan_down"):
        sign = -1 if motion_type == "pan_up" else 1
        base_dx = 0
        base_dy = sign * t * speed * 50
    else:
        base_dx, base_dy = 0, 0

    # Start with empty canvas
    canvas = np.zeros((h, w, 4), dtype=np.uint8)

    num_layers = len(layers_inpainted)

    for idx, (layer, depth_center) in enumerate(zip(layers_inpainted, depth_centers)):
        # Parallax factor: near layers (depth_center → 0) move MORE
        # far layers (depth_center → 1) move LESS
        nearness = 1.0 - depth_center
        parallax_factor = 0.1 + nearness * 2.4  # range [0.1, 2.5] — dramatic separation

        # Compute this layer's offset
        dx = base_dx * parallax_factor
        dy = base_dy * parallax_factor

        # Start with translation
        shifted = offset_layer(layer, dx, dy)

        # For zoom: scale each layer from center — near layers scale MORE
        if "zoom" in motion_type:
            layer_scale = 1.0 + base_scale * parallax_factor
            M_scale = cv2.getRotationMatrix2D((w / 2, h / 2), 0, layer_scale)
            shifted = cv2.warpAffine(shifted, M_scale, (w, h),
                                      borderMode=cv2.BORDER_REFLECT_101)
        canvas = composite_rgba_over(canvas, shifted)

        # Add fog between layers 1 and 2 (mid-depth atmospheric haze)
        if fog_enabled and idx == num_layers // 2 - 1:
            fog = create_fog_layer(w, h, t * 5.0, density=0.08)
            fog_shifted = offset_layer(fog, dx * 0.5, dy * 0.5)
            canvas = composite_rgba_over(canvas, fog_shifted)

    # Add ground elements in very front
    if ground_enabled:
        ground = create_ground_elements(w, h, t * 5.0)
        # Ground moves the most (closest to camera)
        g_dx = base_dx * 2.0
        g_dy = base_dy * 2.0
        ground = offset_layer(ground, g_dx, g_dy)
        canvas = composite_rgba_over(canvas, ground)

    return canvas[:, :, :3]


# ── Multi-Image Scene Builder ─────────────────────────────────────────────

def extract_subject(image_arr, depth_arr, threshold=0.55):
    """
    Extract foreground subject from image using depth map.
    Returns RGBA with alpha mask where subject is opaque.
    """
    h, w = image_arr.shape[:2]

    # Subject = near pixels (low depth value = close to camera)
    # Depth Anything: 0=far, 1=near (after our normalization)
    mask = (depth_arr > threshold).astype(np.float32)

    # Clean up mask: remove small noise, smooth edges
    mask_u8 = (mask * 255).astype(np.uint8)
    kernel = np.ones((7, 7), np.uint8)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_CLOSE, kernel)
    mask_u8 = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)

    # Feather edges
    mask_smooth = cv2.GaussianBlur(mask_u8, (0, 0), 5).astype(np.float32) / 255.0

    # Create RGBA
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = image_arr
    rgba[:, :, 3] = (mask_smooth * 255).astype(np.uint8)

    return rgba


def place_on_canvas(image, canvas_w, canvas_h, x_center, y_bottom, scale=1.0):
    """Place an RGBA image on a canvas at specified position."""
    h, w = image.shape[:2]
    new_w, new_h = int(w * scale), int(h * scale)
    if new_w < 1 or new_h < 1:
        return np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    x_start = x_center - new_w // 2
    y_start = y_bottom - new_h

    # Clamp to canvas
    src_x0 = max(0, -x_start)
    src_y0 = max(0, -y_start)
    dst_x0 = max(0, x_start)
    dst_y0 = max(0, y_start)
    copy_w = min(new_w - src_x0, canvas_w - dst_x0)
    copy_h = min(new_h - src_y0, canvas_h - dst_y0)

    if copy_w > 0 and copy_h > 0:
        canvas[dst_y0:dst_y0 + copy_h, dst_x0:dst_x0 + copy_w] = \
            resized[src_y0:src_y0 + copy_h, src_x0:src_x0 + copy_w]

    return canvas


def render_composite_frame(layers, t, motion_type="pan_right"):
    """
    Render one frame of a multi-image composite scene.

    layers: list of (rgba_array, parallax_speed, base_x_offset) tuples
            ordered back-to-front
    t: normalized time [0, 1]
    """
    h, w = layers[0][0].shape[:2]
    canvas = np.zeros((h, w, 4), dtype=np.uint8)

    for rgba, speed, x_off in layers:
        # Each layer moves at its own speed
        if motion_type == "pan_right":
            dx = t * speed
            dy = 0
        elif motion_type == "pan_left":
            dx = -t * speed
            dy = 0
        else:
            dx = t * speed * 0.3
            dy = 0

        shifted = offset_layer(rgba, dx + x_off, dy)
        canvas = composite_rgba_over(canvas, shifted)

    return canvas[:, :, :3]


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("Multi-image composite parallax")
    print("=" * 60)

    engine = ParallaxEngine()
    canvas_w, canvas_h = W + 500, H + 300  # Extra room for motion

    # ── LAYER 1 (FAR BACK): Hotel Statler entrance ──
    print("\n  Layer 1: Hotel Statler (background)")
    bg_path = f"{IMG_DIR}/wiki_hotel_statler_entrance.jpg"
    bg_img = Image.open(bg_path).convert("RGB")
    # Scale to fill canvas
    bg_scale = max(canvas_w / bg_img.width, canvas_h / bg_img.height) * 1.15
    bg_img = bg_img.resize((int(bg_img.width * bg_scale), int(bg_img.height * bg_scale)), Image.LANCZOS)
    # Center crop
    left = (bg_img.width - canvas_w) // 2
    top = (bg_img.height - canvas_h) // 2
    bg_img = bg_img.crop((left, top, left + canvas_w, top + canvas_h))
    bg_arr = np.array(bg_img)
    # Make it a full RGBA (fully opaque)
    bg_rgba = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    bg_rgba[:, :, :3] = bg_arr
    bg_rgba[:, :, 3] = 255
    print(f"    Size: {canvas_w}x{canvas_h}")

    # ── LAYER 2 (MID): Atmospheric haze ──
    # (built per-frame in render loop)

    # ── LAYER 3 (MID-NEAR): Frank Olson portrait ──
    print("\n  Layer 2: Frank Olson (foreground subject)")
    fg_path = f"{IMG_DIR}/wiki_Frank_Olsen_1910-1953.jpg.jpg"
    fg_img = Image.open(fg_path).convert("RGB")
    fg_arr = np.array(fg_img)

    # Get depth map to extract subject
    fg_depth = engine.get_depth_map(fg_img, fg_path + "_subject")
    dep_pil = Image.fromarray((fg_depth * 255).astype(np.uint8))
    dep_pil = dep_pil.resize((fg_arr.shape[1], fg_arr.shape[0]), Image.LANCZOS)
    fg_depth_full = np.array(dep_pil).astype(np.float32) / 255.0

    # Extract subject (person)
    subject_rgba = extract_subject(fg_arr, fg_depth_full, threshold=0.45)
    cv2.imwrite("/tmp/subject_extracted.png", cv2.cvtColor(subject_rgba, cv2.COLOR_RGBA2BGRA))
    print(f"    Subject extracted (alpha coverage: {np.mean(subject_rgba[:,:,3] > 30)*100:.1f}%)")

    # Place subject on canvas — right-of-center, showing head+shoulders
    # Target: subject fills ~60% of frame height
    target_h = int(canvas_h * 0.65)
    subject_scale = target_h / subject_rgba.shape[0]
    subject_on_canvas = place_on_canvas(
        subject_rgba, canvas_w, canvas_h,
        x_center=int(canvas_w * 0.58),
        y_bottom=int(canvas_h * 0.95),
        scale=subject_scale,
    )
    print(f"    Placed on canvas (scale={subject_scale:.2f}x, 58% x, 95% y)")

    # ── LAYER 4 (VERY NEAR): Dust particles (built per-frame) ──

    # ── Render ──
    num_frames = int(DURATION_SEC * FPS)
    print(f"\n  Rendering {num_frames} frames ({DURATION_SEC}s @ {FPS}fps)...")
    print(f"  Motion: lateral pan (background slow, subject fast)")

    frames = []
    for fi in range(num_frames):
        t = fi / max(1, num_frames - 1)
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)

        # Build layers with different parallax speeds (px total travel)
        scene_layers = [
            (bg_rgba,             20, 0),    # background: barely moves (20px)
            (subject_on_canvas,   120, 0),   # subject: moves MUCH more (120px)
        ]

        frame = render_composite_frame(scene_layers, t_eased, "pan_right")

        # Center crop to output
        fh, fw = frame.shape[:2]
        cy, cx = (fh - H) // 2, (fw - W) // 2
        frame = frame[cy:cy + H, cx:cx + W]

        # Add fog between layers (mid-depth haze)
        fog = create_fog_layer(W, H, t_eased * 5.0, density=0.05)
        fog_rgb = fog[:, :, :3]
        fog_alpha = fog[:, :, 3:4].astype(np.float32) / 255.0
        frame = (frame.astype(np.float32) * (1 - fog_alpha) + fog_rgb.astype(np.float32) * fog_alpha)
        frame = np.clip(frame, 0, 255).astype(np.uint8)

        # Color grade
        frame = color_grade(frame, "cold")

        # Dust particles
        abs_t = fi / FPS
        from pipeline.parallax_renderer import add_dust_particles as add_dust
        frame = add_dust(frame, abs_t, intensity=0.8, seed=42)

        # Vignette
        frame = add_vignette(frame, 0.6)

        frames.append(frame)

        if (fi + 1) % 30 == 0:
            print(f"    Frame {fi + 1}/{num_frames}")

    # Save mid-frame
    cv2.imwrite("/tmp/multilayer_frame_mid.jpg",
                cv2.cvtColor(frames[num_frames // 2], cv2.COLOR_RGB2BGR))
    print(f"  Mid-frame saved to /tmp/multilayer_frame_mid.jpg")

    # Encode
    print(f"\n  Encoding to {OUT_PATH}...")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
        "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        OUT_PATH,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        print(f"  ERROR: {proc.stderr.read().decode()[-300:]}")
    else:
        size_mb = os.path.getsize(OUT_PATH) / 1024 / 1024
        print(f"  Done! {OUT_PATH} ({size_mb:.1f}MB)")
        print(f"\n  Open with: open {OUT_PATH}")


if __name__ == "__main__":
    main()
