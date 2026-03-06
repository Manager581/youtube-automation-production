"""
Frame-level parallax renderer with motion graphics overlays.

Renders still images as depth-parallax video segments with:
- Depth Anything V2 depth maps (cached to disk)
- Per-pixel parallax motion (3D Ken Burns)
- Motion graphics: dust particles, scan lines, light leak, vignette
- Pillow-based color grading (numpy, not ffmpeg)
- Typewriter text with blinking cursor

Every segment's visual treatment is driven by storyboard metadata
(narrative_function, intensity, shot_type) — not global statistics.

Usage:
    from pipeline.parallax_renderer import ParallaxEngine, render_segment_frames, frames_to_mp4

    engine = ParallaxEngine()  # loads depth model on first use
    config = SegmentVisualConfig.from_storyboard("tension_build", "tense", "document_photo", "zoom_in", 5.0)
    frames = render_segment_frames(engine, "path/to/image.jpg", 6.0, config, start_time=120.0)
    frames_to_mp4(frames, "output/seg_0042.mp4")
"""

import hashlib
import math
import os
import random
import subprocess

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Output dimensions ────────────────────────────────────────────────────────

W, H, FPS = 1920, 1080, 30
WHITE = (255, 255, 255)


# ── Font Helpers ─────────────────────────────────────────────────────────────

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


# ── Narrative → Visual Style Mapping ─────────────────────────────────────────

STYLE_MAP = {
    "hook_opening":       {"color": "cold",     "particles": True, "particle_intensity": 1.0, "scan_lines": False, "light_leak": False, "vignette": True},
    "context_background": {"color": "neutral",  "particles": True, "particle_intensity": 0.5, "scan_lines": False, "light_leak": False, "vignette": True},
    "character_intro":    {"color": "warm",     "particles": True, "particle_intensity": 0.3, "scan_lines": False, "light_leak": False, "vignette": True},
    "tension_build":      {"color": "dark",     "particles": True, "particle_intensity": 1.2, "scan_lines": False, "light_leak": False, "vignette": True},
    "reveal":             {"color": "vibrant",  "particles": True, "particle_intensity": 0.8, "scan_lines": False, "light_leak": True,  "vignette": True},
    "stakes_moment":      {"color": "dark",     "particles": True, "particle_intensity": 1.0, "scan_lines": False, "light_leak": False, "vignette": True},
    "climax":             {"color": "vibrant",  "particles": True, "particle_intensity": 1.5, "scan_lines": False, "light_leak": True,  "vignette": True},
    "aftermath":          {"color": "archival", "particles": True, "particle_intensity": 0.3, "scan_lines": False, "light_leak": False, "vignette": True},
}

SCAN_LINE_SHOT_TYPES = {
    "document_photo", "archival_footage", "government_document",
    "classified_document", "archival_photo", "historical_photo",
}

MOTION_TYPE_MAP = {
    "zoom_in": "slow_zoom_in",
    "zoom_out": "slow_zoom_out",
    "pan_left": "pan_left",
    "pan_right": "pan_right",
    "pan_up": "pan_up",
    "pan_down": "pan_down",
    "static": "static",
}


@dataclass
class SegmentVisualConfig:
    """Per-segment visual treatment, derived from storyboard metadata."""
    color_style: str = "neutral"
    particles: bool = True
    particle_intensity: float = 0.5
    scan_lines: bool = False
    light_leak: bool = False
    vignette: bool = True
    vignette_strength: float = 0.5
    motion_type: str = "slow_zoom_in"
    motion_speed: float = 3.0
    parallax_strength: float = 50.0
    text_overlay: str | None = None
    text_position: str = "center"
    text_style: str = "typewriter"
    secondary_text: str | None = None

    @classmethod
    def from_storyboard(cls, narrative_function: str, intensity: str,
                        shot_type: str | None, motion_direction: str,
                        zoom_rate_pct_sec: float) -> "SegmentVisualConfig":
        """Build config from storyboard metadata. Every visual decision is story-driven."""
        style = STYLE_MAP.get(narrative_function, STYLE_MAP["context_background"]).copy()

        # Shot-type overrides: archival/document shots get scan lines
        scan = bool(shot_type and shot_type.lower() in SCAN_LINE_SHOT_TYPES)

        # Map motion direction
        mt = MOTION_TYPE_MAP.get(motion_direction, "slow_zoom_in")
        speed = zoom_rate_pct_sec / 1.5 if zoom_rate_pct_sec else 3.0

        # Intensity modulation
        pi = style["particle_intensity"]
        if intensity == "tense":
            pi *= 1.3
        elif intensity == "energized":
            speed *= 1.2

        return cls(
            color_style=style["color"],
            particles=style["particles"],
            particle_intensity=pi,
            scan_lines=scan,
            light_leak=style["light_leak"],
            vignette=style["vignette"],
            motion_type=mt,
            motion_speed=speed,
        )


# ── Depth Model ──────────────────────────────────────────────────────────────

class ParallaxEngine:
    """Manages Depth Anything V2 lifecycle. Load once, reuse for all segments."""

    def __init__(self, cache_dir: str = ".depth_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.processor = None
        self.device = None

    def load_model(self):
        """Lazy-load Depth Anything V2 Small (~95MB)."""
        import torch
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"  Loading Depth Anything V2 on {self.device}...")
        self.processor = AutoImageProcessor.from_pretrained(
            "depth-anything/Depth-Anything-V2-Small-hf")
        self.model = AutoModelForDepthEstimation.from_pretrained(
            "depth-anything/Depth-Anything-V2-Small-hf").to(self.device)
        self.model.eval()
        print("  Depth model loaded.")

    def get_depth_map(self, image: Image.Image, image_path: str) -> np.ndarray:
        """Get depth map with disk caching. Returns float32 [0,1] where 1=far."""
        cache_key = hashlib.md5(image_path.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.npy"

        if cache_file.exists():
            return np.load(str(cache_file))

        if self.model is None:
            self.load_model()

        # Infer at 640x360 for speed
        small = image.resize((640, 360))
        depth = _get_depth_map_raw(small, self.model, self.processor, self.device)

        # Resize depth to full image dims
        depth_img = Image.fromarray((depth * 255).astype(np.uint8))
        depth_full = np.array(
            depth_img.resize(image.size, Image.LANCZOS)
        ).astype(np.float32) / 255.0

        np.save(str(cache_file), depth_full)
        return depth_full


def _get_depth_map_raw(image, model, processor, device):
    """Generate depth map from PIL image. Returns float32 [0,1]."""
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


# ── Parallax Frame Rendering ────────────────────────────────────────────────

def prepare_image(img: Image.Image, margin: int = 100) -> Image.Image:
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


def render_parallax_frame(image_arr, depth_arr, t, motion_type="slow_zoom_in",
                          parallax_strength=50.0, speed=3.0):
    """Render single parallax frame with depth-based layer motion."""
    h, w = image_arr.shape[:2]

    if motion_type == "slow_zoom_in":
        zoom = 1.0 + t * speed * 0.01
        dx, dy = 0.0, 0.0
    elif motion_type == "slow_zoom_out":
        zoom = 1.0 + (1.0 - t) * speed * 0.01
        dx, dy = 0.0, 0.0
    elif motion_type == "pan_right":
        zoom = 1.02
        dx, dy = t * speed * 15, 0.0
    elif motion_type == "pan_left":
        zoom = 1.02
        dx, dy = -t * speed * 15, 0.0
    elif motion_type == "pan_up":
        zoom = 1.02
        dx, dy = 0.0, -t * speed * 15
    elif motion_type == "pan_down":
        zoom = 1.02
        dx, dy = 0.0, t * speed * 15
    elif motion_type == "static":
        zoom = 1.0 + t * 0.005
        dx, dy = t * 2.0, t * 1.0
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

    # Bilinear interpolation
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


# ── Color Grading ────────────────────────────────────────────────────────────

def color_grade(frame, style="neutral"):
    """Apply numpy-based color grading. Style driven by narrative function."""
    arr = frame.astype(np.float32) / 255.0

    if style == "cold":
        arr[:, :, 0] *= 0.85
        arr[:, :, 1] *= 0.95
        arr[:, :, 2] *= 1.15
        arr = _contrast_curve(arr, 1.3)
    elif style == "warm":
        arr[:, :, 0] *= 1.15
        arr[:, :, 1] *= 1.05
        arr[:, :, 2] *= 0.80
        arr = _contrast_curve(arr, 1.2)
    elif style == "archival":
        gray = np.mean(arr, axis=2, keepdims=True)
        arr = arr * 0.5 + gray * 0.5
        arr[:, :, 0] *= 1.10
        arr[:, :, 2] *= 0.90
        arr *= 0.92
    elif style == "dark":
        arr[:, :, 2] *= 1.08
        arr = _contrast_curve(arr, 1.4)
        arr *= 0.85
    elif style == "vibrant":
        arr = _contrast_curve(arr, 1.5)
        gray = np.mean(arr, axis=2, keepdims=True)
        arr = gray + (arr - gray) * 1.4
    else:  # neutral
        arr = _contrast_curve(arr, 1.2)

    return np.clip(arr * 255, 0, 255).astype(np.uint8)


def _contrast_curve(arr, strength=1.3):
    """S-curve contrast centered at 0.5."""
    return 0.5 + (arr - 0.5) * strength


# ── Motion Graphics Overlays ────────────────────────────────────────────────

def add_dust_particles(frame_arr, t, intensity=1.0, seed=42):
    """Floating dust/debris particles — cinematic documentary overlay."""
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

        size = rng.randint(3, 10)
        brightness = rng.randint(180, 255)
        alpha = rng.uniform(0.25, 0.7) * (0.6 + 0.4 * math.sin(t * 3 + phase))
        alpha = max(0, alpha)

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
    """CRT/film scan lines for archival feel."""
    overlay = frame_arr.astype(np.float32)
    overlay[::2, :, :] *= (1.0 - opacity)
    return np.clip(overlay, 0, 255).astype(np.uint8)


def add_light_leak(frame_arr, t, corner="top_right", intensity=0.6):
    """Warm light leak from corner — for reveals and climax moments."""
    h, w = frame_arr.shape[:2]
    overlay = frame_arr.astype(np.float32)

    pulse = 0.6 + 0.4 * math.sin(t * 2.0)
    alpha = intensity * pulse

    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    if corner == "top_right":
        dist = np.sqrt(((xx - w) / w) ** 2 + (yy / h) ** 2)
    elif corner == "top_left":
        dist = np.sqrt((xx / w) ** 2 + (yy / h) ** 2)
    else:
        dist = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)

    mask = np.clip(1.0 - dist * 1.2, 0, 1) * alpha
    mask = mask[:, :, np.newaxis]

    overlay[:, :, 0] += mask[:, :, 0] * 80
    overlay[:, :, 1] += mask[:, :, 0] * 50
    overlay[:, :, 2] += mask[:, :, 0] * 15

    return np.clip(overlay, 0, 255).astype(np.uint8)


def add_vignette(frame_arr, strength=0.6):
    """Darkened corners — draws focus to center."""
    h, w = frame_arr.shape[:2]
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    vignette = 1.0 - np.clip(dist - 0.4, 0, 1) * strength
    vignette = vignette[:, :, np.newaxis]
    return np.clip(frame_arr.astype(np.float32) * vignette, 0, 255).astype(np.uint8)


# ── Typewriter Text ──────────────────────────────────────────────────────────

def render_typewriter_text(frame, text, position, progress, font_size=56,
                           color=WHITE, secondary_text=None, secondary_size=32):
    """Typewriter-style text reveal — one character at a time with blinking cursor."""
    draw = ImageDraw.Draw(frame)
    font = get_font(font_size, bold=True)

    char_progress = min(1.0, progress * 1.15)
    chars_to_show = int(len(text) * char_progress)
    chars_to_show = max(0, min(chars_to_show, len(text)))
    visible_text = text[:chars_to_show]
    if not visible_text:
        return frame

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

    # Blinking cursor
    if chars_to_show < len(text) and (int(progress * 12) % 2 == 0):
        cbbox = draw.textbbox((tx, ty), visible_text, font=font)
        cursor_x = cbbox[2] + 3
        draw.rectangle([cursor_x, ty, cursor_x + int(font_size * 0.55), ty + th], fill=color)

    # Secondary text (appears after main is done)
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


# ── Main Segment Renderer ───────────────────────────────────────────────────

def render_segment_frames(
    engine: ParallaxEngine,
    image_path: str,
    duration_sec: float,
    config: SegmentVisualConfig,
    start_time: float = 0.0,
    focal_point: tuple[float, float] | None = None,
) -> list[np.ndarray]:
    """
    Render a complete segment as a list of numpy frames.

    This is the generalized version of render_beat() from render_hook_30s.py.
    Every visual decision is driven by the SegmentVisualConfig (from storyboard).

    Returns list of (H, W, 3) uint8 arrays.
    """
    img = Image.open(image_path).convert("RGB")
    img = prepare_image(img)
    img_arr = np.array(img)

    depth_arr = engine.get_depth_map(img, image_path)
    # Resize depth to match prepared image
    dep_img = Image.fromarray((depth_arr * 255).astype(np.uint8))
    ih, iw = img_arr.shape[:2]
    dep_img = dep_img.resize((iw, ih), Image.LANCZOS)
    dep_arr = np.array(dep_img).astype(np.float32) / 255.0

    num_frames = int(duration_sec * FPS)
    frames = []

    for i in range(num_frames):
        t = i / max(1, num_frames - 1)
        t_eased = 0.5 - 0.5 * math.cos(t * math.pi)  # sinusoidal ease-in-out

        frame = render_parallax_frame(
            img_arr, dep_arr, t_eased,
            config.motion_type, config.parallax_strength, config.motion_speed
        )

        # Center crop to output dimensions
        fh, fw = frame.shape[:2]
        cy, cx = (fh - H) // 2, (fw - W) // 2
        if cy >= 0 and cx >= 0:
            frame = frame[cy:cy + H, cx:cx + W]
        else:
            frame = np.array(Image.fromarray(frame).resize((W, H), Image.LANCZOS))

        # Color grade
        frame = color_grade(frame, config.color_style)

        # Motion graphics overlays
        abs_t = start_time + i / FPS
        if config.particles:
            frame = add_dust_particles(frame, abs_t, config.particle_intensity,
                                       seed=int(start_time * 10) + 42)
        if config.scan_lines:
            frame = add_scan_lines(frame)
        if config.light_leak:
            frame = add_light_leak(frame, abs_t, corner="top_right")
        if config.vignette:
            frame = add_vignette(frame, config.vignette_strength)

        # Text overlay (typewriter style)
        if config.text_overlay and t >= 0.1:
            tp = min(1.0, (t - 0.1) / 0.3)
            pf = Image.fromarray(frame)
            pf = render_typewriter_text(
                pf, config.text_overlay, config.text_position, tp,
                secondary_text=config.secondary_text
            )
            frame = np.array(pf)

        frames.append(frame)

    return frames


def frames_to_mp4(frames: list[np.ndarray], out_path: str, fps: int = FPS):
    """Encode numpy frames to mp4 via ffmpeg stdin pipe. No temp files per frame."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read().decode()[-500:]
        raise RuntimeError(f"ffmpeg encode error: {err}")
