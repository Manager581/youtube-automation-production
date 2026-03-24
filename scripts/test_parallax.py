#!/usr/bin/env python3
"""
Test 2.5D parallax effect: Depth Anything V2 + layer-based animation.

Takes a still photo, generates a depth map, then renders a 3D-feeling
camera move where foreground/background move at different speeds.

Model: depth-anything/Depth-Anything-V2-Small-hf (~95MB, runs on MPS)

Usage:
    PYTORCH_ENABLE_MPS_FALLBACK=1 venv/bin/python scripts/test_parallax.py
"""

import os
import sys
import time
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageFilter

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
W, H = 1920, 1080
FPS = 30
DURATION_SEC = 5
TOTAL_FRAMES = FPS * DURATION_SEC

IMAGE_DIR = "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/images"
OUTPUT_DIR = "output"

# Test images (use what we have)
TEST_IMAGES = [
    ("wiki_Frank_Olsen_1910-1953.jpg.jpg", "slow_zoom_in", "Frank Olson portrait"),
    ("wiki_Sidney_Gottlieb_photo.jpg.jpg", "pan_right", "Sidney Gottlieb"),
    ("wiki_Mkultra-lsd-doc.jpg.jpg", "slow_zoom_in", "MKUltra document"),
]


def load_depth_model():
    """Load Depth Anything V2 (small, ~95MB)."""
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"  Device: {device}")

    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForDepthEstimation.from_pretrained(MODEL_ID).to(device)
    model.eval()

    return model, processor, device


def get_depth_map(image: Image.Image, model, processor, device) -> np.ndarray:
    """Generate depth map from image. Returns float32 array [0,1] where 1=far."""
    import torch

    inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        depth = outputs.predicted_depth  # [1, h, w]

    # Resize to image size
    depth = torch.nn.functional.interpolate(
        depth.unsqueeze(1),
        size=(image.height, image.width),
        mode="bicubic",
        align_corners=False,
    ).squeeze().cpu().numpy()

    # Normalize to [0, 1]
    depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    return depth


def render_parallax_frame(
    image: np.ndarray,
    depth: np.ndarray,
    t: float,
    motion_type: str = "slow_zoom_in",
    parallax_strength: float = 40.0,
) -> np.ndarray:
    """
    Render a single parallax frame.

    The trick: shift each pixel by an amount proportional to its depth.
    Nearby pixels (low depth) shift more, far pixels shift less.
    This creates a 3D parallax effect from a 2D image.

    Args:
        image: RGB image as numpy array [H, W, 3]
        depth: Depth map [H, W], 0=near, 1=far
        t: Time from 0.0 to 1.0
        motion_type: Camera motion type
        parallax_strength: How strong the 3D effect is (pixels)
    """
    h, w = image.shape[:2]

    # Define camera motion based on type
    if motion_type == "slow_zoom_in":
        # Zoom toward center with depth parallax
        zoom = 1.0 + t * 0.08  # 8% zoom over duration
        dx = 0.0
        dy = 0.0
    elif motion_type == "slow_zoom_out":
        zoom = 1.08 - t * 0.08
        dx = 0.0
        dy = 0.0
    elif motion_type == "pan_right":
        zoom = 1.02
        dx = t * 60  # pan 60 pixels right
        dy = 0.0
    elif motion_type == "pan_left":
        zoom = 1.02
        dx = -t * 60
        dy = 0.0
    elif motion_type == "drift_up":
        zoom = 1.03
        dx = t * 10
        dy = -t * 30
    else:
        zoom = 1.0 + t * 0.05
        dx = 0.0
        dy = 0.0

    # Invert depth so near=1, far=0 (near objects move MORE)
    near_factor = 1.0 - depth

    # Create displacement maps — near pixels shift more than far pixels
    # This is the core parallax effect
    shift_x = near_factor * dx * parallax_strength / 60.0
    shift_y = near_factor * dy * parallax_strength / 60.0

    # Build sampling coordinates
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    cx, cy = w / 2, h / 2

    # Apply zoom (centered)
    src_x = (xx - cx) / zoom + cx - shift_x + dx * (1.0 - near_factor * 0.5)
    src_y = (yy - cy) / zoom + cy - shift_y + dy * (1.0 - near_factor * 0.5)

    # Clamp to bounds
    src_x = np.clip(src_x, 0, w - 1).astype(np.float32)
    src_y = np.clip(src_y, 0, h - 1).astype(np.float32)

    # Bilinear interpolation
    x0 = np.floor(src_x).astype(int)
    y0 = np.floor(src_y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = src_x - x0
    fy = src_y - y0

    fx3 = fx[:, :, np.newaxis]
    fy3 = fy[:, :, np.newaxis]

    result = (
        image[y0, x0] * (1 - fx3) * (1 - fy3) +
        image[y0, x1] * fx3 * (1 - fy3) +
        image[y1, x0] * (1 - fx3) * fy3 +
        image[y1, x1] * fx3 * fy3
    )

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_color_grade(frame: np.ndarray) -> np.ndarray:
    """Apply Fern-style color grading: desaturated, dark, slightly warm."""
    img = Image.fromarray(frame)

    # Convert to float
    arr = frame.astype(np.float32) / 255.0

    # Reduce brightness (Fern style: brightness 0.368)
    arr *= 0.85

    # Slight desaturation
    gray = np.mean(arr, axis=2, keepdims=True)
    arr = arr * 0.75 + gray * 0.25

    # Warm shift (subtle)
    arr[:, :, 0] *= 1.03  # red up
    arr[:, :, 2] *= 0.95  # blue down

    # Black crush (Fern style: 24.7% black crush)
    arr = np.clip(arr, 0.02, 1.0)

    return np.clip(arr * 255, 0, 255).astype(np.uint8)


def render_parallax_video(
    image_path: str,
    depth_map: np.ndarray,
    output_path: str,
    motion_type: str = "slow_zoom_in",
    label: str = "",
):
    """Render a full parallax video from image + depth map."""
    img = Image.open(image_path).convert("RGB")

    # Resize to output dimensions (cover, center crop)
    aspect_src = img.width / img.height
    aspect_dst = W / H
    if aspect_src > aspect_dst:
        new_h = H + 100  # extra for parallax margin
        new_w = int(new_h * aspect_src)
    else:
        new_w = W + 100
        new_h = int(new_w / aspect_src)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    img = img.crop((left, top, left + W, top + H))
    img_arr = np.array(img)

    # Resize depth map to match
    depth_img = Image.fromarray((depth_map * 255).astype(np.uint8))
    depth_img = depth_img.resize((new_w, new_h), Image.LANCZOS)
    depth_img = depth_img.crop((left, top, left + W, top + H))
    depth_arr = np.array(depth_img).astype(np.float32) / 255.0

    # Render frames
    tmpdir = tempfile.mkdtemp()
    print(f"  Rendering {TOTAL_FRAMES} frames ({DURATION_SEC}s)...")

    for i in range(TOTAL_FRAMES):
        t = i / (TOTAL_FRAMES - 1)  # 0 to 1

        # Ease in/out for smooth motion
        t_eased = 0.5 - 0.5 * np.cos(t * np.pi)

        frame = render_parallax_frame(img_arr, depth_arr, t_eased, motion_type)
        frame = apply_color_grade(frame)

        Image.fromarray(frame).save(os.path.join(tmpdir, f"frame_{i:04d}.png"))

        if (i + 1) % 30 == 0:
            print(f"    {i+1}/{TOTAL_FRAMES} frames")

    # Encode to video
    print(f"  Encoding to {output_path}...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(tmpdir, "frame_%04d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True)

    # Cleanup
    for f in os.listdir(tmpdir):
        os.remove(os.path.join(tmpdir, f))
    os.rmdir(tmpdir)

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  DONE: {output_path} ({size_mb:.1f} MB)")
    else:
        print(f"  ERROR: Failed to encode {output_path}")


def main():
    print("=" * 60)
    print("2.5D PARALLAX TEST — Depth Anything V2")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load model
    print("\n[1] Loading Depth Anything V2 (~95MB model)...")
    start = time.time()
    model, processor, device = load_depth_model()
    print(f"  Loaded in {time.time() - start:.1f}s")

    # Process each test image
    for filename, motion, label in TEST_IMAGES:
        image_path = os.path.join(IMAGE_DIR, filename)
        if not os.path.exists(image_path):
            print(f"\n  SKIP: {filename} not found")
            continue

        print(f"\n[{label}] Processing {filename}...")
        img = Image.open(image_path).convert("RGB")
        print(f"  Image: {img.width}x{img.height}")

        # Generate depth map
        print("  Generating depth map...")
        start = time.time()
        depth = get_depth_map(img, model, processor, device)
        print(f"  Depth map: {depth.shape}, range [{depth.min():.2f}, {depth.max():.2f}] ({time.time() - start:.1f}s)")

        # Save depth map for inspection
        depth_vis = Image.fromarray((depth * 255).astype(np.uint8))
        depth_path = os.path.join(OUTPUT_DIR, f"depth_{filename.split('.')[0]}.png")
        depth_vis.save(depth_path)
        print(f"  Depth map saved: {depth_path}")

        # Render parallax video
        out_name = f"parallax_{filename.split('.')[0]}_{motion}.mp4"
        output_path = os.path.join(OUTPUT_DIR, out_name)

        start = time.time()
        render_parallax_video(image_path, depth, output_path, motion, label)
        print(f"  Render time: {time.time() - start:.1f}s")

    print(f"\n{'=' * 60}")
    print("All parallax tests complete! Check output/ directory.")
    print("=" * 60)


if __name__ == "__main__":
    main()
