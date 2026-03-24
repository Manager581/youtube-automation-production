#!/usr/bin/env python3
"""
Storyboard Viewer — generates a self-contained HTML storyboard viewer and opens it in the browser.

Usage:
    venv/bin/python scripts/view_storyboard.py --topic frank_olson_cia_scientist_lsd_murder_cover_up
"""

import argparse
import base64
import html
import json
import os
import sys
import webbrowser
from io import BytesIO
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: venv/bin/pip install Pillow")
    sys.exit(1)


THUMB_W = 120
THUMB_H = 68  # 16:9

MOTION_ICONS = {
    "zoom_in": "&#8599;",    # ↗
    "zoom_out": "&#8601;",   # ↙
    "pan_right": "&#8594;",  # →
    "pan_left": "&#8592;",   # ←
    "pan_up": "&#8593;",     # ↑
    "pan_down": "&#8595;",   # ↓
    "static": "&#9679;",     # ●
}

SFX_COLORS = {
    "glass_shatter": "#ff4444",
    "body_impact": "#ff8800",
    "impact": "#ff8800",
    "tension": "#4488ff",
    "rumble": "#aa44ff",
    "shimmer": "#ffcc00",
    "whoosh": "#44cc44",
}

TRANSITION_ICONS = {
    "fade_from_black": "&#9632;&#8594;",   # ■→
    "fade_to_black": "&#8594;&#9632;",     # →■
    "dissolve": "&#8776;",                 # ≈
    "cut": "&#9474;",                      # │
}

# Scene color palette (alternating)
SCENE_COLORS = [
    "rgba(100, 60, 60, 0.25)",
    "rgba(60, 80, 100, 0.25)",
    "rgba(60, 100, 60, 0.25)",
    "rgba(100, 80, 60, 0.25)",
    "rgba(80, 60, 100, 0.25)",
    "rgba(60, 100, 100, 0.25)",
    "rgba(100, 100, 60, 0.25)",
    "rgba(100, 60, 100, 0.25)",
]


def make_thumbnail_b64(image_path: Path) -> str:
    """Load image, resize to thumbnail, return base64 JPEG."""
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        # Pad to exact size with black
        thumb = Image.new("RGB", (THUMB_W, THUMB_H), (20, 20, 20))
        x_off = (THUMB_W - img.width) // 2
        y_off = (THUMB_H - img.height) // 2
        thumb.paste(img, (x_off, y_off))
        buf = BytesIO()
        thumb.save(buf, format="JPEG", quality=40)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def make_fullsize_b64(image_path: Path) -> str:
    """Load image, resize to max 600px wide, return base64 JPEG."""
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        if img.width > 600:
            ratio = 600 / img.width
            img = img.resize((600, int(img.height * ratio)), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return ""


def get_image_path(composition_plan: dict, images_dir: Path) -> Path | None:
    """Extract image path from composition plan."""
    if not composition_plan:
        return None
    primary = composition_plan.get("primary_image", "")
    if not primary:
        return None
    # Strip leading "images/" prefix
    filename = primary.replace("images/", "")
    path = images_dir / filename
    if path.exists():
        return path
    return None


def tension_color(level: float) -> str:
    """Return color for tension level 0-1."""
    if level < 0.3:
        r, g, b = 68, 204, 68
    elif level < 0.6:
        r = int(68 + (255 - 68) * ((level - 0.3) / 0.3))
        g = int(204 - (204 - 180) * ((level - 0.3) / 0.3))
        b = 68
    else:
        r = 255
        g = int(180 - 180 * ((level - 0.6) / 0.4))
        b = 68
    return f"rgb({r},{g},{b})"


def build_html(storyboard: dict, images_dir: Path, timeline: list | None) -> str:
    """Build the complete HTML viewer."""

    scenes = storyboard.get("scenes", [])

    # Collect all segments flat + scene info
    all_segments = []
    scene_boundaries = []  # (start_idx, scene_id, scene_name, narrative_arc, color)
    global_idx = 0

    for si, scene in enumerate(scenes):
        scene_start = global_idx
        color = SCENE_COLORS[si % len(SCENE_COLORS)]
        for seg in scene.get("segments", []):
            seg["_scene_idx"] = si
            seg["_global_idx"] = global_idx
            seg["_scene_id"] = scene.get("scene_id", f"scene_{si}")
            all_segments.append(seg)
            global_idx += 1
        scene_boundaries.append({
            "start": scene_start,
            "end": global_idx - 1,
            "scene_id": scene.get("scene_id", ""),
            "scene_name": scene.get("scene_name", "")[:60],
            "narrative_arc": scene.get("narrative_arc", ""),
            "color": color,
        })

    # Build timeline lookup (segment index -> duration)
    duration_lookup = {}
    if timeline:
        for entry in timeline:
            idx = entry.get("sb_entry_idx")
            if idx is not None:
                duration_lookup[idx] = entry.get("duration_sec", 0)

    # Stats
    total_segments = len(all_segments)
    total_scenes = len(scenes)
    chapter_breaks = sum(1 for s in all_segments if s.get("is_chapter_break"))
    total_chapters = chapter_breaks + 1

    sfx_counts = {}
    text_overlay_count = 0
    unique_images = set()
    total_duration = 0.0

    # Pre-generate thumbnails and full images
    thumbnails = {}  # global_idx -> b64
    fullimages = {}  # global_idx -> b64
    image_names = {}  # global_idx -> filename

    for seg in all_segments:
        idx = seg["_global_idx"]
        sfx = seg.get("sfx")
        if sfx:
            sfx_type = sfx.get("type", "unknown") if isinstance(sfx, dict) else str(sfx)
            sfx_counts[sfx_type] = sfx_counts.get(sfx_type, 0) + 1

        if seg.get("_text_overlay"):
            text_overlay_count += 1

        # Duration
        dur = duration_lookup.get(idx, 0)
        if dur == 0:
            hold = seg.get("hold_duration_range", [3, 5])
            dur = (hold[0] + hold[1]) / 2 if hold else 3.5
        total_duration += dur

        # Image
        comp = seg.get("composition_plan", {})
        img_path = get_image_path(comp, images_dir)
        if img_path:
            unique_images.add(img_path.name)
            image_names[idx] = img_path.name
            thumbnails[idx] = make_thumbnail_b64(img_path)
            fullimages[idx] = make_fullsize_b64(img_path)
        else:
            primary = comp.get("primary_image", "") if comp else ""
            image_names[idx] = primary.replace("images/", "") if primary else "none"

    # Build segment data for JS
    segments_js = []
    for seg in all_segments:
        idx = seg["_global_idx"]
        sfx = seg.get("sfx")
        sfx_type = None
        sfx_motivation = ""
        if sfx:
            if isinstance(sfx, dict):
                sfx_type = sfx.get("type")
                sfx_motivation = sfx.get("motivation", "")
            else:
                sfx_type = str(sfx)

        dur = duration_lookup.get(idx, 0)
        if dur == 0:
            hold = seg.get("hold_duration_range", [3, 5])
            dur = round((hold[0] + hold[1]) / 2, 1) if hold else 3.5

        trans_in = seg.get("transition_in", {})
        trans_out = seg.get("transition_out", {})
        comp = seg.get("composition_plan", {}) or {}
        zoom_target = seg.get("zoom_target", {}) or {}

        segments_js.append({
            "idx": idx,
            "scene_idx": seg["_scene_idx"],
            "scene_id": seg["_scene_id"],
            "text": seg.get("text", ""),
            "emotion": seg.get("emotion", ""),
            "shot_type": seg.get("shot_type", ""),
            "motion": seg.get("motion_direction", "static"),
            "arc_position": seg.get("arc_position", ""),
            "tension_level": seg.get("tension_level", 0),
            "sfx_type": sfx_type,
            "sfx_motivation": sfx_motivation,
            "text_overlay": seg.get("_text_overlay"),
            "text_overlay_size": seg.get("_text_overlay_size"),
            "text_overlay_style": seg.get("_text_overlay_style"),
            "is_chapter_break": seg.get("is_chapter_break", False),
            "duration": dur,
            "transition_in": trans_in.get("type", "cut") if trans_in else "cut",
            "transition_out": trans_out.get("type", "cut") if trans_out else "cut",
            "thumb_b64": thumbnails.get(idx, ""),
            "full_b64": fullimages.get(idx, ""),
            "image_name": image_names.get(idx, ""),
            "show": seg.get("show", ""),
            "focal_element": seg.get("focal_element", ""),
            "reasoning": comp.get("reasoning", ""),
            "color_grade": comp.get("color_grade", ""),
            "overlay": comp.get("overlay", ""),
            "zoom_target": zoom_target.get("motivation", ""),
            "zoom_rate": seg.get("zoom_rate_pct_sec", 0),
            "sync_points": seg.get("sync_points", []),
            "cut_motivation": seg.get("cut_motivation", ""),
            "narrative_function": seg.get("narrative_function", ""),
            "hold_range": seg.get("hold_duration_range", []),
        })

    # Scene boundaries for JS
    scenes_js = scene_boundaries

    # Stats for the top bar
    stats = {
        "total_segments": total_segments,
        "total_scenes": total_scenes,
        "total_chapters": total_chapters,
        "sfx_counts": sfx_counts,
        "text_overlay_count": text_overlay_count,
        "total_duration_sec": round(total_duration, 1),
        "total_duration_min": f"{int(total_duration // 60)}:{int(total_duration % 60):02d}",
        "unique_images": len(unique_images),
    }

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Storyboard Viewer</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a1e; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 13px; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }}

/* Stats bar */
#stats-bar {{
    background: #25252a; border-bottom: 1px solid #3a3a40; padding: 8px 16px;
    display: flex; gap: 20px; align-items: center; flex-wrap: wrap; flex-shrink: 0;
}}
.stat {{ display: flex; align-items: center; gap: 4px; }}
.stat-label {{ color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
.stat-value {{ color: #fff; font-weight: 600; font-size: 14px; }}
.sfx-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}

/* Main layout */
#main {{ display: flex; flex: 1; overflow: hidden; }}

/* Timeline area */
#timeline-area {{
    flex: 1; display: flex; flex-direction: column; overflow: hidden;
}}

/* Tension arc */
#tension-arc {{
    height: 60px; flex-shrink: 0; background: #1e1e22; border-bottom: 1px solid #333;
    position: relative; overflow: hidden;
}}
#tension-arc svg {{ width: 100%; height: 100%; }}

/* Scene labels */
#scene-labels {{
    height: 28px; flex-shrink: 0; background: #1e1e22;
    overflow: hidden; position: relative;
}}
#scene-labels-inner {{
    display: flex; height: 100%; white-space: nowrap;
}}
.scene-label {{
    font-size: 10px; color: #aaa; padding: 4px 6px; border-right: 1px solid #333;
    overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center;
    flex-shrink: 0;
}}

/* Card strip */
#card-strip-wrapper {{
    flex: 1; overflow-x: auto; overflow-y: hidden;
}}
#card-strip {{
    display: flex; padding: 8px 8px 8px 8px; gap: 3px; height: 100%; align-items: flex-start;
}}

/* Segment card */
.seg-card {{
    width: 120px; min-width: 120px; flex-shrink: 0;
    background: #28282e; border-radius: 4px; cursor: pointer;
    border: 1px solid #3a3a40; transition: border-color 0.15s;
    display: flex; flex-direction: column; overflow: hidden;
}}
.seg-card:hover {{ border-color: #6a6aff; }}
.seg-card.selected {{ border-color: #8888ff; box-shadow: 0 0 8px rgba(100,100,255,0.3); }}

.card-thumb {{
    width: 120px; height: 68px; background: #111; position: relative;
    overflow: hidden;
}}
.card-thumb img {{ width: 100%; height: 100%; object-fit: cover; }}
.card-thumb .placeholder {{
    width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
    font-size: 9px; color: #555; text-align: center; padding: 4px;
}}

/* Badges on thumbnail */
.badge-row {{
    position: absolute; top: 2px; left: 2px; display: flex; gap: 2px;
}}
.sfx-badge {{
    width: 12px; height: 12px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-size: 7px;
}}
.text-badge {{
    background: rgba(255,255,255,0.2); color: #fff; font-size: 8px;
    padding: 1px 3px; border-radius: 2px; font-weight: 700;
}}
.motion-icon {{
    position: absolute; bottom: 2px; right: 2px;
    background: rgba(0,0,0,0.6); color: #ccc; font-size: 14px;
    padding: 0 3px; border-radius: 2px; line-height: 1.2;
}}
.transition-icon {{
    position: absolute; top: 2px; right: 2px;
    background: rgba(0,0,0,0.5); color: #999; font-size: 8px;
    padding: 1px 2px; border-radius: 2px;
}}

/* Card info */
.card-info {{
    padding: 4px 6px; flex: 1;
}}
.card-idx {{ font-size: 10px; color: #666; }}
.card-dur {{ font-size: 10px; color: #888; float: right; }}
.card-text {{ font-size: 9px; color: #aaa; margin-top: 2px; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
.card-arc {{ font-size: 8px; color: #666; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }}

/* Chapter break divider */
.chapter-break {{
    width: 4px; min-width: 4px; flex-shrink: 0; background: #ff4444;
    border-radius: 2px; align-self: stretch; margin: 0 2px;
}}

/* Detail panel */
#detail-panel {{
    width: 360px; min-width: 360px; background: #222228; border-left: 1px solid #3a3a40;
    overflow-y: auto; flex-shrink: 0; padding: 16px; display: none;
}}
#detail-panel.visible {{ display: block; }}
#detail-panel h3 {{ color: #fff; font-size: 15px; margin-bottom: 12px; }}
#detail-image {{ max-width: 100%; border-radius: 4px; margin-bottom: 12px; }}
#detail-text {{ color: #ddd; font-size: 13px; line-height: 1.5; margin-bottom: 16px; font-style: italic; }}
.detail-section {{ margin-bottom: 12px; }}
.detail-section h4 {{ color: #888; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.detail-section .value {{ color: #ccc; font-size: 12px; line-height: 1.4; }}
.detail-tag {{
    display: inline-block; background: #333; color: #bbb; padding: 2px 6px;
    border-radius: 3px; font-size: 11px; margin: 2px 2px 2px 0;
}}
.detail-tag.sfx {{ background: #442222; color: #ff8888; }}
.detail-tag.arc {{ background: #224444; color: #88cccc; }}
.detail-tag.motion {{ background: #334422; color: #bbcc88; }}

/* Scrollbar styling */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: #1a1a1e; }}
::-webkit-scrollbar-thumb {{ background: #444; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #555; }}
</style>
</head>
<body>

<!-- Stats Bar -->
<div id="stats-bar">
    <div class="stat"><span class="stat-label">Segments</span><span class="stat-value">{stats['total_segments']}</span></div>
    <div class="stat"><span class="stat-label">Scenes</span><span class="stat-value">{stats['total_scenes']}</span></div>
    <div class="stat"><span class="stat-label">Chapters</span><span class="stat-value">{stats['total_chapters']}</span></div>
    <div class="stat"><span class="stat-label">Duration</span><span class="stat-value">{stats['total_duration_min']}</span></div>
    <div class="stat"><span class="stat-label">Images</span><span class="stat-value">{stats['unique_images']}/{stats['total_segments']}</span></div>
    <div class="stat"><span class="stat-label">Text Overlays</span><span class="stat-value">{stats['text_overlay_count']}</span></div>
    <div class="stat" style="margin-left: auto;"><span class="stat-label">SFX:</span>
        {' '.join(f'<span class="sfx-dot" style="background:{SFX_COLORS.get(k,"#888")}" title="{k}"></span><span style="color:#999;font-size:11px">{v}</span>' for k, v in sorted(sfx_counts.items()))}
    </div>
</div>

<!-- Main Layout -->
<div id="main">
    <div id="timeline-area">
        <!-- Tension Arc -->
        <div id="tension-arc"><svg id="tension-svg" preserveAspectRatio="none"></svg></div>
        <!-- Scene Labels -->
        <div id="scene-labels"><div id="scene-labels-inner"></div></div>
        <!-- Card Strip -->
        <div id="card-strip-wrapper"><div id="card-strip"></div></div>
    </div>
    <!-- Detail Panel -->
    <div id="detail-panel">
        <h3 id="detail-title">Select a segment</h3>
        <img id="detail-image" style="display:none" />
        <div id="detail-text"></div>
        <div id="detail-meta"></div>
    </div>
</div>

<script>
const SEGMENTS = {json.dumps(segments_js, ensure_ascii=False)};
const SCENES = {json.dumps(scenes_js, ensure_ascii=False)};

const MOTION_ICONS = {json.dumps(MOTION_ICONS)};
const SFX_COLORS = {json.dumps(SFX_COLORS)};
const TRANSITION_ICONS = {json.dumps(TRANSITION_ICONS)};

const cardStrip = document.getElementById('card-strip');
const sceneLabelsInner = document.getElementById('scene-labels-inner');
const detailPanel = document.getElementById('detail-panel');
const cardStripWrapper = document.getElementById('card-strip-wrapper');

// Card width including gap
const CARD_W = 123; // 120 + 3 gap
const BREAK_W = 8;  // chapter break width

// Build cards
let selectedIdx = -1;

SEGMENTS.forEach((seg, i) => {{
    // Insert chapter break divider
    if (seg.is_chapter_break) {{
        const brk = document.createElement('div');
        brk.className = 'chapter-break';
        brk.title = 'Chapter Break';
        cardStrip.appendChild(brk);
    }}

    const card = document.createElement('div');
    card.className = 'seg-card';
    card.id = 'card-' + seg.idx;
    card.style.background = SCENES[seg.scene_idx].color.replace('0.25', '0.15');
    card.style.borderColor = SCENES[seg.scene_idx].color.replace('0.25', '0.4');

    // Thumbnail
    let thumbHtml = '';
    if (seg.thumb_b64) {{
        thumbHtml = `<img src="data:image/jpeg;base64,${{seg.thumb_b64}}" alt="" />`;
    }} else {{
        thumbHtml = `<div class="placeholder">${{seg.image_name || 'no image'}}</div>`;
    }}

    // Badges
    let badges = '';
    if (seg.sfx_type) {{
        const col = SFX_COLORS[seg.sfx_type] || '#888';
        badges += `<div class="sfx-badge" style="background:${{col}}" title="${{seg.sfx_type}}"></div>`;
    }}
    if (seg.text_overlay) {{
        badges += `<div class="text-badge" title="${{escH(seg.text_overlay)}}">T</div>`;
    }}

    // Motion icon
    const motionHtml = MOTION_ICONS[seg.motion] || MOTION_ICONS['static'];

    // Transition icon
    const transIcon = TRANSITION_ICONS[seg.transition_in] || '';

    card.innerHTML = `
        <div class="card-thumb">
            ${{thumbHtml}}
            <div class="badge-row">${{badges}}</div>
            <div class="motion-icon">${{motionHtml}}</div>
            ${{transIcon ? `<div class="transition-icon">${{transIcon}}</div>` : ''}}
        </div>
        <div class="card-info">
            <span class="card-idx">#${{seg.idx}}</span>
            <span class="card-dur">${{seg.duration.toFixed(1)}}s</span>
            <div class="card-text">${{escH(seg.text.substring(0, 100))}}</div>
            <div class="card-arc">${{seg.arc_position}}</div>
        </div>
    `;

    card.addEventListener('click', () => showDetail(seg.idx));
    cardStrip.appendChild(card);
}});

// Scene labels
SCENES.forEach(sc => {{
    const lbl = document.createElement('div');
    lbl.className = 'scene-label';
    const count = sc.end - sc.start + 1;
    lbl.style.width = (count * CARD_W) + 'px';
    lbl.style.background = sc.color;
    lbl.innerHTML = `<span style="font-weight:600;color:#ccc">${{escH(sc.scene_id)}}</span>&nbsp;<span style="color:#777">${{sc.narrative_arc}}</span>`;
    lbl.title = sc.scene_name;
    sceneLabelsInner.appendChild(lbl);
}});

// Sync horizontal scroll between labels, tension arc, and card strip
cardStripWrapper.addEventListener('scroll', () => {{
    document.getElementById('scene-labels').scrollLeft = cardStripWrapper.scrollLeft;
    // Tension arc scroll synced via viewBox update
    updateTensionViewBox();
}});

// Build tension arc SVG
function buildTensionArc() {{
    const svg = document.getElementById('tension-svg');
    const totalW = SEGMENTS.length * CARD_W;
    svg.setAttribute('viewBox', `0 0 ${{totalW}} 60`);
    svg.style.width = totalW + 'px';
    // Parent needs to scroll too
    document.getElementById('tension-arc').style.overflowX = 'hidden';

    // Build path
    let pathD = '';
    let prevArc = '';
    let labels = [];

    SEGMENTS.forEach((seg, i) => {{
        const x = i * CARD_W + CARD_W / 2;
        const y = 55 - seg.tension_level * 48; // 55 = bottom, 7 = top
        if (i === 0) pathD += `M${{x}},${{y}}`;
        else pathD += ` L${{x}},${{y}}`;

        // Arc position labels at transitions
        if (seg.arc_position !== prevArc) {{
            labels.push({{ x, y: 10, text: seg.arc_position }});
            prevArc = seg.arc_position;
        }}
    }});

    // Gradient fill
    let fillD = pathD + ` L${{(SEGMENTS.length - 1) * CARD_W + CARD_W / 2}},58 L${{CARD_W / 2}},58 Z`;

    // Build color stops for gradient based on tension levels
    let gradStops = '';
    SEGMENTS.forEach((seg, i) => {{
        const pct = (i / Math.max(SEGMENTS.length - 1, 1) * 100).toFixed(1);
        const col = tensionColor(seg.tension_level);
        gradStops += `<stop offset="${{pct}}%" stop-color="${{col}}" />`;
    }});

    svg.innerHTML = `
        <defs>
            <linearGradient id="tgrad" x1="0%" y1="0%" x2="100%" y2="0%">
                ${{gradStops}}
            </linearGradient>
        </defs>
        <path d="${{fillD}}" fill="url(#tgrad)" opacity="0.25" />
        <path d="${{pathD}}" fill="none" stroke="url(#tgrad)" stroke-width="2" />
        ${{labels.map(l => `<text x="${{l.x}}" y="${{l.y}}" fill="#666" font-size="8" text-anchor="middle" font-family="sans-serif">${{l.text}}</text>`).join('')}}
    `;
}}

function tensionColor(level) {{
    if (level < 0.3) return '#44cc44';
    if (level < 0.6) {{
        const t = (level - 0.3) / 0.3;
        const r = Math.round(68 + (255 - 68) * t);
        const g = Math.round(204 - 24 * t);
        return `rgb(${{r}},${{g}},68)`;
    }}
    const t = (level - 0.6) / 0.4;
    const g = Math.round(180 - 180 * t);
    return `rgb(255,${{g}},68)`;
}}

function updateTensionViewBox() {{
    const svg = document.getElementById('tension-svg');
    const scroll = cardStripWrapper.scrollLeft;
    const visW = cardStripWrapper.clientWidth;
    const totalW = SEGMENTS.length * CARD_W;
    svg.parentElement.scrollLeft = scroll;
}}

// Actually, let tension arc scroll in sync
document.getElementById('tension-arc').style.overflowX = 'hidden';
const tensionSvg = document.getElementById('tension-svg');

cardStripWrapper.addEventListener('scroll', () => {{
    const sl = cardStripWrapper.scrollLeft;
    document.getElementById('scene-labels').scrollLeft = sl;
    document.getElementById('tension-arc').scrollLeft = sl;
}});

buildTensionArc();

// Detail panel
function showDetail(idx) {{
    const seg = SEGMENTS[idx];
    if (!seg) return;

    // Deselect previous
    if (selectedIdx >= 0) {{
        const prev = document.getElementById('card-' + selectedIdx);
        if (prev) prev.classList.remove('selected');
    }}
    selectedIdx = idx;
    document.getElementById('card-' + idx).classList.add('selected');

    detailPanel.classList.add('visible');

    document.getElementById('detail-title').textContent = `Segment #${{idx}} \u2014 ${{seg.arc_position}}`;

    const img = document.getElementById('detail-image');
    if (seg.full_b64) {{
        img.src = 'data:image/jpeg;base64,' + seg.full_b64;
        img.style.display = 'block';
    }} else {{
        img.style.display = 'none';
    }}

    document.getElementById('detail-text').textContent = seg.text;

    let meta = '';

    // Tags row
    meta += '<div style="margin-bottom:10px">';
    meta += `<span class="detail-tag arc">${{seg.arc_position}}</span>`;
    meta += `<span class="detail-tag motion">${{seg.motion}}</span>`;
    meta += `<span class="detail-tag">${{seg.shot_type}}</span>`;
    meta += `<span class="detail-tag">${{seg.emotion}}</span>`;
    if (seg.sfx_type) meta += `<span class="detail-tag sfx">${{seg.sfx_type}}</span>`;
    meta += '</div>';

    // Show description
    if (seg.show) {{
        meta += `<div class="detail-section"><h4>Visual Description</h4><div class="value">${{escH(seg.show)}}</div></div>`;
    }}

    // Focal element
    if (seg.focal_element) {{
        meta += `<div class="detail-section"><h4>Focal Element</h4><div class="value">${{escH(seg.focal_element)}}</div></div>`;
    }}

    // Composition reasoning
    if (seg.reasoning) {{
        meta += `<div class="detail-section"><h4>Composition Reasoning</h4><div class="value">${{escH(seg.reasoning)}}</div></div>`;
    }}

    // Text overlay
    if (seg.text_overlay) {{
        meta += `<div class="detail-section"><h4>Text Overlay</h4><div class="value" style="color:#ffcc44">${{escH(seg.text_overlay)}}</div>`;
        if (seg.text_overlay_size) meta += `<div class="value" style="font-size:11px;color:#888">${{seg.text_overlay_size}}px ${{seg.text_overlay_style || ''}}</div>`;
        meta += '</div>';
    }}

    // SFX
    if (seg.sfx_type) {{
        meta += `<div class="detail-section"><h4>SFX</h4><div class="value"><span style="color:${{SFX_COLORS[seg.sfx_type] || '#888'}}">${{seg.sfx_type}}</span>`;
        if (seg.sfx_motivation) meta += ` \u2014 ${{escH(seg.sfx_motivation)}}`;
        meta += '</div></div>';
    }}

    // Motion details
    meta += `<div class="detail-section"><h4>Motion</h4><div class="value">${{seg.motion}} @ ${{seg.zoom_rate.toFixed(1)}}%/s</div>`;
    if (seg.zoom_target) meta += `<div class="value" style="font-size:11px;color:#888">Target: ${{escH(seg.zoom_target)}}</div>`;
    meta += '</div>';

    // Timing
    meta += `<div class="detail-section"><h4>Timing</h4><div class="value">Duration: ${{seg.duration.toFixed(1)}}s`;
    if (seg.hold_range && seg.hold_range.length === 2) meta += ` (range: ${{seg.hold_range[0]}}\u2013${{seg.hold_range[1]}}s)`;
    meta += `</div><div class="value">Transition in: ${{seg.transition_in}} | out: ${{seg.transition_out}}</div></div>`;

    // Cut motivation + narrative function
    meta += `<div class="detail-section"><h4>Editorial</h4><div class="value">Cut: ${{escH(seg.cut_motivation || 'none')}} | Function: ${{escH(seg.narrative_function || 'none')}}</div></div>`;

    // Color grade + overlay
    meta += `<div class="detail-section"><h4>Color / Atmosphere</h4><div class="value">${{escH(seg.color_grade || 'none')}} | ${{escH(seg.overlay || 'none')}}</div></div>`;

    // Image name
    meta += `<div class="detail-section"><h4>Image</h4><div class="value" style="font-size:11px;color:#777">${{escH(seg.image_name)}}</div></div>`;

    // Sync points
    if (seg.sync_points && seg.sync_points.length > 0) {{
        meta += `<div class="detail-section"><h4>Sync Points</h4>`;
        seg.sync_points.forEach(sp => {{
            meta += `<div class="value" style="font-size:11px">@ "${{escH(sp.word)}}" \u2192 ${{escH(sp.action)}}`;
            if (sp.text) meta += `: "${{escH(sp.text)}}"`;
            meta += '</div>';
        }});
        meta += '</div>';
    }}

    document.getElementById('detail-meta').innerHTML = meta;
}}

function escH(s) {{
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
}}

// Keyboard navigation
document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight') {{
        e.preventDefault();
        showDetail(Math.min(selectedIdx + 1, SEGMENTS.length - 1));
        scrollToCard(selectedIdx);
    }} else if (e.key === 'ArrowLeft') {{
        e.preventDefault();
        showDetail(Math.max(selectedIdx - 1, 0));
        scrollToCard(selectedIdx);
    }} else if (e.key === 'Escape') {{
        detailPanel.classList.remove('visible');
        if (selectedIdx >= 0) {{
            document.getElementById('card-' + selectedIdx).classList.remove('selected');
            selectedIdx = -1;
        }}
    }}
}});

function scrollToCard(idx) {{
    const card = document.getElementById('card-' + idx);
    if (card) {{
        card.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
    }}
}}
</script>
</body>
</html>"""

    return html_out


def main():
    parser = argparse.ArgumentParser(description="Generate HTML storyboard viewer")
    parser.add_argument("--topic", required=True, help="Topic slug (e.g. frank_olson_cia_scientist_lsd_murder_cover_up)")
    parser.add_argument("--output", default="/tmp/storyboard_viewer.html", help="Output HTML path")
    args = parser.parse_args()

    topic = args.topic
    storyboard_path = PROJECT_ROOT / "storyboards" / f"{topic}_directed.json"
    images_dir = PROJECT_ROOT / "footage" / "fern_clone" / topic / "images"
    timeline_path = PROJECT_ROOT / "output" / topic / "timeline.json"

    # Fallback: try non-directed storyboard
    if not storyboard_path.exists():
        storyboard_path = PROJECT_ROOT / "storyboards" / f"{topic}.json"

    if not storyboard_path.exists():
        print(f"ERROR: Storyboard not found: {storyboard_path}")
        sys.exit(1)

    print(f"Loading storyboard: {storyboard_path}")
    with open(storyboard_path) as f:
        storyboard = json.load(f)

    # Handle v1 storyboards (flat segment list, no scenes)
    if "scenes" not in storyboard:
        segments = storyboard.get("segments", storyboard.get("storyboard", []))
        storyboard["scenes"] = [{"scene_id": "all", "scene_name": "Full Video", "narrative_arc": "unknown", "segments": segments}]

    timeline = None
    if timeline_path.exists():
        print(f"Loading timeline: {timeline_path}")
        with open(timeline_path) as f:
            timeline = json.load(f)

    if not images_dir.exists():
        print(f"WARNING: Images directory not found: {images_dir}")
        images_dir = Path("/dev/null")  # Will just produce empty thumbnails

    seg_count = sum(len(sc.get("segments", [])) for sc in storyboard["scenes"])
    print(f"Building viewer for {seg_count} segments across {len(storyboard['scenes'])} scenes...")
    print(f"Images dir: {images_dir}")

    html_content = build_html(storyboard, images_dir, timeline)

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        f.write(html_content)

    size_kb = output_path.stat().st_size / 1024
    print(f"Wrote {output_path} ({size_kb:.0f} KB)")

    webbrowser.open(f"file://{output_path}")
    print("Opened in browser.")


if __name__ == "__main__":
    main()
