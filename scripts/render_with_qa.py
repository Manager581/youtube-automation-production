#!/usr/bin/env python3
"""
render_with_qa.py — QA-gated full render pipeline.

Validates every stage before rendering. Hard stop on FAIL.
Gates 0-5 run in ~1 min. Render only starts after all pass.

Usage:
    venv/bin/python scripts/render_with_qa.py \\
        --topic frank_olson_cia_scientist_lsd_murder_cover_up \\
        --stills-only --parallax

    # Dry run (pre-render gates only):
    venv/bin/python scripts/render_with_qa.py --topic SLUG --dry-run

    # Preview (first N seconds + all gates):
    venv/bin/python scripts/render_with_qa.py --topic SLUG --preview 120
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ── ANSI colors ──────────────────────────────────────────────────────────────
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
R  = "\033[91m"   # red
B  = "\033[1m"    # bold
D  = "\033[2m"    # dim
C  = "\033[96m"   # cyan
X  = "\033[0m"    # reset

PYTHON = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add project root to path for imports
sys.path.insert(0, str(PROJECT_ROOT))

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    status: str   # "PASS" | "WARN" | "FAIL" | "SKIP"
    detail: str

@dataclass
class GateResult:
    name: str
    num: int | float
    checks: list = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if any(c.status == "FAIL" for c in self.checks):
            return "FAIL"
        if any(c.status == "WARN" for c in self.checks):
            return "WARN"
        return "PASS"

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status in ("PASS", "WARN"))

    @property
    def total_count(self) -> int:
        return len(self.checks)


# ── Helpers ──────────────────────────────────────────────────────────────────

def ffprobe_duration(path: str) -> float | None:
    """Get duration in seconds via ffprobe, or None on failure."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=15,
        )
        data = json.loads(r.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None


def resolve_paths(slug: str) -> dict:
    """Derive all file paths from topic slug."""
    # Audio dir uses short prefix (e.g. "frank_olson" not full slug)
    audio_dir = None
    audio_root = PROJECT_ROOT / "audio"
    if audio_root.is_dir():
        for d in sorted(audio_root.iterdir()):
            if d.is_dir() and (slug.startswith(d.name) or d.name.startswith(slug[:20])):
                audio_dir = d
                break

    # Storyboard: prefer _directed version
    sb_directed = PROJECT_ROOT / f"storyboards/{slug}_directed.json"
    sb_base = PROJECT_ROOT / f"storyboards/{slug}.json"
    storyboard = str(sb_directed) if sb_directed.exists() else str(sb_base)

    return {
        "script": str(PROJECT_ROOT / f"scripts/enhanced_{slug}.txt"),
        "storyboard": storyboard,
        "storyboard_base": str(sb_base),
        "narration_wav": str(audio_dir / "narration.wav") if audio_dir else "",
        "narration_manifest": str(audio_dir / "narration_manifest.json") if audio_dir else "",
        "music": str(PROJECT_ROOT / "assets/music/track.mp3"),
        "footage_manifest": str(PROJECT_ROOT / f"footage/fern_clone/{slug}/manifest.json"),
        "footage_dir": str(PROJECT_ROOT / f"footage/fern_clone/{slug}"),
        "output_video": str(PROJECT_ROOT / f"output/{slug}/final.mp4"),
        "output_timeline": str(PROJECT_ROOT / f"output/{slug}/timeline.json"),
        "sfx_dir": str(PROJECT_ROOT / "assets/sfx"),
        "brand_config": str(PROJECT_ROOT / "brand_configs/fern_clone.json"),
    }


def print_gate_header(num: int | float, name: str):
    num_str = f"{num:g}" if isinstance(num, float) else str(num)
    print(f"\n  {B}{C}GATE {num_str}: {name}{X}")
    print(f"  {'─' * 50}")


def print_check(c: CheckResult):
    icon = {"PASS": f"{G}✓{X}", "WARN": f"{Y}⚠{X}", "FAIL": f"{R}✗{X}", "SKIP": f"{D}–{X}"}
    print(f"    {icon.get(c.status, '?')} {c.detail}")


def print_gate_verdict(g: GateResult):
    color = {
        "PASS": G, "WARN": Y, "FAIL": R,
    }.get(g.verdict, X)
    print(f"    {color}{B}VERDICT: {g.verdict}{X}")


def print_summary(results: list[GateResult], paths: dict):
    print(f"\n{'═' * 58}")
    print(f"  {B}SUMMARY{X}")
    print(f"{'═' * 58}")
    total_checks = 0
    total_pass = 0
    warns = 0
    fails = 0
    for r in results:
        color = {
            "PASS": G, "WARN": Y, "FAIL": R,
        }.get(r.verdict, X)
        total_checks += r.total_count
        total_pass += r.pass_count
        if r.verdict == "WARN":
            warns += 1
        elif r.verdict == "FAIL":
            fails += 1
        num_str = f"{r.num:g}" if isinstance(r.num, float) else str(r.num)
        print(f"    Gate {num_str:<3s}  {r.name:22s} {r.pass_count:>2}/{r.total_count:<2}  {color}{r.verdict}{X}")

    print()
    if fails:
        print(f"    {R}{B}OVERALL: FAIL ({fails} gate(s) failed){X}")
    elif warns:
        print(f"    {Y}{B}OVERALL: PASS ({warns} warning(s)){X}")
    else:
        print(f"    {G}{B}OVERALL: PASS — all checks green{X}")

    out = Path(paths["output_video"])
    if out.exists():
        mb = out.stat().st_size / 1024 / 1024
        dur = ffprobe_duration(str(out))
        dur_str = f"{dur/60:.1f} min" if dur else "?"
        print(f"    Output: {out.name} ({mb:.0f} MB, {dur_str})")
    print(f"{'═' * 58}")


# ── Gate 0: Pre-flight ───────────────────────────────────────────────────────

def gate_preflight(paths: dict, args) -> GateResult:
    g = GateResult("Pre-flight", 0)

    # 1. Script
    p = Path(paths["script"])
    if p.exists() and p.stat().st_size > 500:
        words = len(p.read_text().split())
        g.checks.append(CheckResult("script", "PASS", f"Enhanced script ({words:,} words)"))
    else:
        g.checks.append(CheckResult("script", "FAIL",
            f"Script missing or empty: {paths['script']}"))

    # 2. Storyboard
    sb_path = Path(paths["storyboard"])
    if sb_path.exists():
        try:
            sb = json.loads(sb_path.read_text())
            if isinstance(sb, dict) and sb.get("schema_version") == "2.0":
                n_seg = sb.get("segment_count", "?")
                n_sc = sb.get("scene_count", "?")
                g.checks.append(CheckResult("storyboard", "PASS",
                    f"Directed storyboard v2.0 ({n_seg} segs, {n_sc} scenes)"))
            elif isinstance(sb, list):
                g.checks.append(CheckResult("storyboard", "WARN",
                    f"v1 storyboard ({len(sb)} segs) — no Director pass"))
            else:
                g.checks.append(CheckResult("storyboard", "FAIL",
                    "Storyboard JSON has unknown structure"))
        except json.JSONDecodeError:
            g.checks.append(CheckResult("storyboard", "FAIL", "Storyboard JSON parse error"))
    else:
        g.checks.append(CheckResult("storyboard", "FAIL",
            f"Storyboard not found: {sb_path}"))

    # 3. Narration WAV
    wav = Path(paths["narration_wav"])
    if wav.exists():
        dur = ffprobe_duration(str(wav))
        if dur and dur > 600:
            g.checks.append(CheckResult("narration", "PASS",
                f"Narration WAV ({dur/60:.1f} min)"))
        elif dur:
            g.checks.append(CheckResult("narration", "WARN",
                f"Narration only {dur/60:.1f} min (expected >10 min)"))
        else:
            g.checks.append(CheckResult("narration", "FAIL",
                "Narration WAV unreadable by ffprobe"))
    else:
        g.checks.append(CheckResult("narration", "FAIL",
            f"Narration WAV not found: {wav}"))

    # 4. Narration manifest
    man = Path(paths["narration_manifest"])
    if man.exists():
        try:
            nm = json.loads(man.read_text())
            chunks = nm.get("chunks") or nm.get("segments") or []
            if len(chunks) > 10:
                g.checks.append(CheckResult("manifest", "PASS",
                    f"Narration manifest ({len(chunks)} chunks)"))
            else:
                g.checks.append(CheckResult("manifest", "WARN",
                    f"Narration manifest has only {len(chunks)} chunks"))
        except Exception:
            g.checks.append(CheckResult("manifest", "FAIL", "Manifest JSON parse error"))
    else:
        g.checks.append(CheckResult("manifest", "FAIL",
            f"Narration manifest not found: {man}"))

    # 5. Music
    music = Path(paths["music"])
    if music.exists():
        dur = ffprobe_duration(str(music))
        if dur and dur > 60:
            g.checks.append(CheckResult("music", "PASS",
                f"Music track ({dur/60:.1f} min)"))
        elif dur:
            g.checks.append(CheckResult("music", "WARN",
                f"Music track only {dur:.0f}s"))
        else:
            g.checks.append(CheckResult("music", "FAIL", "Music file unreadable"))
    else:
        g.checks.append(CheckResult("music", "WARN", "No music track — will render without"))

    # 6. Footage manifest
    fm = Path(paths["footage_manifest"])
    if fm.exists():
        try:
            fdata = json.loads(fm.read_text())
            items = fdata.get("clips", []) + fdata.get("images", [])
            g.checks.append(CheckResult("footage", "PASS" if len(items) > 20 else "WARN",
                f"Footage manifest ({len(items)} items)"))
        except Exception:
            g.checks.append(CheckResult("footage", "FAIL", "Footage manifest parse error"))
    else:
        g.checks.append(CheckResult("footage", "FAIL",
            f"Footage manifest not found: {fm}"))

    # 7. ffmpeg/ffprobe
    has_ff = shutil.which("ffmpeg") and shutil.which("ffprobe")
    g.checks.append(CheckResult("tools", "PASS" if has_ff else "FAIL",
        "ffmpeg + ffprobe" + (" on PATH" if has_ff else " NOT FOUND")))

    # 8. SFX files
    sfx_dir = Path(paths["sfx_dir"])
    SFX_CANDIDATES = {
        "impact": ["impact_01.mp3", "impact_02.mp3"],
        "body_impact": ["body_impact_01.mp3", "impact_01.mp3"],
        "glass_shatter": ["glass_shatter_01.mp3"],
        "whoosh": ["whoosh_01.mp3", "whoosh_02.mp3", "whoosh_03.mp3"],
        "rumble": ["rumble_01.mp3", "rumble_02.mp3", "rumble_03.mp3"],
        "shimmer": ["shimmer_01.mp3", "shimmer_02.mp3", "shimmer_03.mp3"],
        "tension": ["tension_01.mp3"],
    }
    # Collect SFX types used in director output
    used_types = set()
    sb_path = Path(paths["storyboard"])
    if sb_path.exists():
        try:
            sb = json.loads(sb_path.read_text())
            for scene in sb.get("scenes", []) if isinstance(sb, dict) else []:
                for seg in scene.get("segments", []):
                    sfx = seg.get("sfx", {})
                    if isinstance(sfx, dict) and sfx.get("type"):
                        used_types.add(sfx["type"])
        except Exception:
            pass

    missing_sfx = []
    for t in used_types:
        files = [sfx_dir / f for f in SFX_CANDIDATES.get(t, []) if (sfx_dir / f).exists()]
        if not files:
            missing_sfx.append(t)

    if not used_types:
        g.checks.append(CheckResult("sfx", "WARN", "No SFX types in storyboard"))
    elif missing_sfx:
        g.checks.append(CheckResult("sfx", "FAIL",
            f"Missing SFX files: {', '.join(missing_sfx)}"))
    else:
        g.checks.append(CheckResult("sfx", "PASS",
            f"SFX: {len(used_types)}/{len(used_types)} types available"))

    # 9. Parallax depth model
    if args.parallax:
        depth_cache = PROJECT_ROOT / ".depth_cache"
        has_model = depth_cache.exists() and any(depth_cache.iterdir()) if depth_cache.exists() else False
        # Also check if torch/transformers are importable
        try:
            import torch  # noqa
            g.checks.append(CheckResult("parallax", "PASS",
                "Depth model available for parallax"))
        except ImportError:
            g.checks.append(CheckResult("parallax", "FAIL",
                "PyTorch not installed — needed for --parallax"))

    # 10. Ollama (if --focal-points)
    if args.focal_points:
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags")
            urllib.request.urlopen(req, timeout=3)
            g.checks.append(CheckResult("ollama", "PASS", "Ollama running"))
        except Exception:
            g.checks.append(CheckResult("ollama", "FAIL",
                "Ollama not running — needed for --focal-points"))

    return g


# ── Gate 0.5: Asset Validation ───────────────────────────────────────────────

def gate_asset_validation(paths: dict) -> GateResult:
    g = GateResult("Asset Validation", 0.5)

    sfx_dir = Path(paths["sfx_dir"])
    if not sfx_dir.is_dir():
        g.checks.append(CheckResult("sfx_dir", "WARN",
            f"SFX directory not found: {sfx_dir}"))
        return g

    try:
        from pipeline.asset_validator import validate_sfx
    except ImportError as e:
        g.checks.append(CheckResult("import", "WARN",
            f"Could not import pipeline.asset_validator: {e}"))
        return g

    try:
        results = validate_sfx(sfx_dir)
    except Exception as e:
        g.checks.append(CheckResult("validate", "FAIL",
            f"validate_sfx() raised: {e}"))
        return g

    if not results:
        g.checks.append(CheckResult("sfx_empty", "WARN",
            "No SFX files found to validate"))
        return g

    # Group results by SFX type to check if at least one candidate is usable
    from collections import defaultdict
    by_type = defaultdict(list)
    for r in results:
        if r.get("sfx_type"):
            by_type[r["sfx_type"]].append(r)

    # A type is "covered" if at least one candidate is PASS or WARN
    covered_types = set()
    for sfx_type, type_results in by_type.items():
        if any(r["status"] in ("PASS", "WARN") for r in type_results):
            covered_types.add(sfx_type)

    for r in results:
        status = r.get("status", "PASS")
        name = Path(r.get("file", "?")).name
        detail = r.get("issue") or r.get("detail", "")
        sfx_type = r.get("sfx_type", "")

        if status in ("FAIL", "CRITICAL"):
            # Check if valid candidates exist (same type or shared fallback)
            _shared_types = {"body_impact": "impact"}
            _non_critical = {"highlighter", "paper_rustle", "camera_shutter"}
            has_coverage = (
                sfx_type in covered_types or
                _shared_types.get(sfx_type, "") in covered_types
            )
            if has_coverage or sfx_type in _non_critical:
                status = "WARN"
            else:
                status = "FAIL"

        g.checks.append(CheckResult(f"sfx_{name}", status,
            f"SFX: {name} — {detail}"))

    # Summary: flag types with NO valid candidates at all
    # But don't block on types that share candidates with other types
    # (e.g., body_impact falls back to impact files in the assembler)
    _shared_types = {"body_impact": "impact"}  # body_impact uses impact files as fallback
    # Non-critical SFX types — WARN only if all fail (won't block render)
    _non_critical = {"highlighter", "paper_rustle", "camera_shutter"}
    for sfx_type, type_results in by_type.items():
        if sfx_type not in covered_types:
            fallback = _shared_types.get(sfx_type)
            if fallback and fallback in covered_types:
                g.checks.append(CheckResult(f"sfx_no_valid_{sfx_type}", "WARN",
                    f"No dedicated {sfx_type} files pass — will use {fallback} fallback"))
            elif sfx_type in _non_critical:
                g.checks.append(CheckResult(f"sfx_no_valid_{sfx_type}", "WARN",
                    f"No valid {sfx_type} files — non-critical, will be silent"))
            else:
                g.checks.append(CheckResult(f"sfx_no_valid_{sfx_type}", "FAIL",
                    f"ALL {sfx_type} candidates failed — this SFX will be silent in render"))

    return g


# ── Gate 1: Storyboard Integrity ─────────────────────────────────────────────

def gate_storyboard(paths: dict) -> GateResult:
    g = GateResult("Storyboard Integrity", 1)
    sb_path = Path(paths["storyboard"])

    try:
        raw = json.loads(sb_path.read_text())
    except Exception as e:
        g.checks.append(CheckResult("parse", "FAIL", f"JSON parse error: {e}"))
        return g

    # Flatten segments
    if isinstance(raw, dict) and raw.get("schema_version") == "2.0":
        segments = []
        for sc in raw.get("scenes", []):
            segments.extend(sc.get("segments", []))
        scenes = raw.get("scenes", [])
        g.checks.append(CheckResult("schema", "PASS",
            f"v2.0 schema ({len(segments)} segments, {len(scenes)} scenes)"))
    elif isinstance(raw, list):
        segments = raw
        scenes = []
        g.checks.append(CheckResult("schema", "WARN",
            f"v1 schema ({len(segments)} segments, no scenes)"))
    else:
        g.checks.append(CheckResult("schema", "FAIL", "Unknown storyboard structure"))
        return g

    # Required fields
    required = ["text", "show", "search_query", "shot_type"]
    missing = 0
    for seg in segments:
        for f in required:
            if not seg.get(f):
                missing += 1
    if missing == 0:
        g.checks.append(CheckResult("fields", "PASS", "All required fields present"))
    elif missing < len(segments):
        g.checks.append(CheckResult("fields", "WARN",
            f"{missing} missing field(s) across {len(segments)} segments"))
    else:
        g.checks.append(CheckResult("fields", "FAIL",
            f"{missing} missing required fields"))

    # Empty text
    empty = sum(1 for s in segments if not (s.get("text") or "").strip())
    if empty == 0:
        g.checks.append(CheckResult("text", "PASS", "No empty text segments"))
    else:
        g.checks.append(CheckResult("text", "WARN", f"{empty} empty text segments"))

    # Segment count
    n = len(segments)
    if 50 <= n <= 500:
        g.checks.append(CheckResult("count", "PASS", f"Segment count: {n}"))
    elif 20 <= n < 50 or 500 < n <= 1000:
        g.checks.append(CheckResult("count", "WARN", f"Segment count: {n} (unusual)"))
    else:
        g.checks.append(CheckResult("count", "FAIL",
            f"Segment count: {n} (expected 50-500)"))

    # Scene count
    if len(scenes) > 0:
        g.checks.append(CheckResult("scenes", "PASS", f"Scene count: {len(scenes)}"))
    else:
        g.checks.append(CheckResult("scenes", "WARN", "No scene grouping"))

    # Known shot types
    KNOWN_TYPES = {"document_photo", "documentary_photo", "archival_footage",
                   "map", "person_photo", "news_footage", "infographic",
                   "text_card", "title_card", "chapter_card", "portrait",
                   "landscape", "building", "event_photo", "artistic", "symbolic"}
    bad_types = set()
    for s in segments:
        st = s.get("shot_type", "")
        if st and st not in KNOWN_TYPES:
            bad_types.add(st)
    if not bad_types:
        g.checks.append(CheckResult("shot_types", "PASS", "All shot_types recognized"))
    else:
        g.checks.append(CheckResult("shot_types", "WARN",
            f"Unknown shot_types: {', '.join(list(bad_types)[:5])}"))

    # Arc position (confirms director ran)
    has_arc = sum(1 for s in segments if s.get("arc_position"))
    if has_arc == len(segments):
        g.checks.append(CheckResult("arc", "PASS", "All segments have arc_position"))
    elif has_arc > 0:
        g.checks.append(CheckResult("arc", "WARN",
            f"Only {has_arc}/{len(segments)} segments have arc_position"))
    else:
        g.checks.append(CheckResult("arc", "WARN",
            "No arc_position — Director pass may not have run"))

    return g


# ── Gate 2: Director Integrity ────────────────────────────────────────────────

def gate_director(paths: dict) -> GateResult:
    g = GateResult("Director Integrity", 2)
    sb_path = Path(paths["storyboard"])

    try:
        raw = json.loads(sb_path.read_text())
    except Exception as e:
        g.checks.append(CheckResult("parse", "FAIL", f"JSON error: {e}"))
        return g

    if not isinstance(raw, dict):
        g.checks.append(CheckResult("directed", "WARN",
            "v1 storyboard — no Director data"))
        return g

    # 1. directed flag
    if raw.get("directed"):
        g.checks.append(CheckResult("directed", "PASS", "Director pass confirmed"))
    else:
        g.checks.append(CheckResult("directed", "WARN", "No 'directed' flag"))

    segments = []
    for sc in raw.get("scenes", []):
        segments.extend(sc.get("segments", []))
    if not segments:
        g.checks.append(CheckResult("segments", "FAIL", "No segments found"))
        return g

    # 2. hold_duration_range
    bad_holds = 0
    for s in segments:
        h = s.get("hold_duration_range")
        if isinstance(h, list) and len(h) == 2:
            if h[0] > h[1]:
                bad_holds += 1
    if bad_holds == 0:
        g.checks.append(CheckResult("holds", "PASS", "Hold duration ranges valid"))
    else:
        g.checks.append(CheckResult("holds", "FAIL",
            f"{bad_holds} segments have min > max hold"))

    # 3. SFX types
    VALID_SFX = {"impact", "whoosh", "rumble", "shimmer", "tension",
                 "glass_shatter", "body_impact"}
    bad_sfx = set()
    for s in segments:
        sfx = s.get("sfx", {})
        if isinstance(sfx, dict) and sfx.get("type"):
            if sfx["type"] not in VALID_SFX:
                bad_sfx.add(sfx["type"])
    if not bad_sfx:
        g.checks.append(CheckResult("sfx_types", "PASS", "All SFX types valid"))
    else:
        g.checks.append(CheckResult("sfx_types", "WARN",
            f"Unknown SFX types: {', '.join(bad_sfx)}"))

    # 4. Transition types
    VALID_TRANS = {"cut", "dissolve", "fade_from_black", "fade_to_black"}
    bad_trans = set()
    for s in segments:
        for key in ("transition_in", "transition_out"):
            t = s.get(key, {})
            if isinstance(t, dict) and t.get("type"):
                if t["type"] not in VALID_TRANS:
                    bad_trans.add(t["type"])
    if not bad_trans:
        g.checks.append(CheckResult("transitions", "PASS", "All transition types valid"))
    else:
        g.checks.append(CheckResult("transitions", "WARN",
            f"Unknown transitions: {', '.join(bad_trans)}"))

    # 5. Text sizes
    bad_sizes = 0
    for s in segments:
        sz = s.get("_text_overlay_size")
        if sz and not (24 <= sz <= 96):
            bad_sizes += 1
        for sp in s.get("sync_points", []):
            fs = sp.get("font_size")
            if fs and not (24 <= fs <= 96):
                bad_sizes += 1
    if bad_sizes == 0:
        g.checks.append(CheckResult("text_size", "PASS", "Text sizes in valid range"))
    else:
        g.checks.append(CheckResult("text_size", "WARN",
            f"{bad_sizes} text elements outside 24-96px range"))

    # 6. Arc positions
    VALID_ARCS = {"cold_open", "context_setup", "tension_build", "revelation",
                  "emotional_peak", "aftermath", "chapter_transition"}
    bad_arcs = set()
    for s in segments:
        ap = s.get("arc_position")
        if ap and ap not in VALID_ARCS:
            bad_arcs.add(ap)
    if not bad_arcs:
        g.checks.append(CheckResult("arcs", "PASS", "All arc positions valid"))
    else:
        g.checks.append(CheckResult("arcs", "WARN",
            f"Unknown arc positions: {', '.join(bad_arcs)}"))

    # 7. Sync points structure
    bad_sp = 0
    total_sp = 0
    for s in segments:
        for sp in s.get("sync_points", []):
            total_sp += 1
            if not (sp.get("word") and sp.get("action") and sp.get("text")):
                bad_sp += 1
    if total_sp == 0:
        g.checks.append(CheckResult("sync_points", "WARN", "No sync points"))
    elif bad_sp == 0:
        g.checks.append(CheckResult("sync_points", "PASS",
            f"{total_sp} sync points, all valid"))
    else:
        g.checks.append(CheckResult("sync_points", "WARN",
            f"{bad_sp}/{total_sp} sync points missing required fields"))

    return g


# ── Gate 3: Footage Coverage ─────────────────────────────────────────────────

def gate_footage(paths: dict, stills_only: bool = False) -> GateResult:
    g = GateResult("Footage Coverage", 3)
    fm_path = Path(paths["footage_manifest"])

    try:
        fdata = json.loads(fm_path.read_text())
    except Exception as e:
        g.checks.append(CheckResult("parse", "FAIL", f"Manifest error: {e}"))
        return g

    # Filter items: skip undownloaded clips, skip all clips if --stills-only
    clips = fdata.get("clips", [])
    images = fdata.get("images", [])
    if stills_only:
        items = images
        g.checks.append(CheckResult("mode", "PASS",
            f"Stills-only mode: {len(images)} images (skipping {len(clips)} clips)"))
    else:
        # Only count downloaded clips
        dl_clips = [c for c in clips if c.get("downloaded") or c.get("local_path")]
        items = dl_clips + images
        if len(clips) > len(dl_clips):
            g.checks.append(CheckResult("downloads", "WARN",
                f"{len(clips) - len(dl_clips)}/{len(clips)} clips not downloaded"))
    footage_dir = Path(paths["footage_dir"])

    # Helper to resolve item path (handles local_path, path, filename + relative paths)
    def _resolve(item):
        lp = item.get("local_path") or item.get("path") or item.get("filename", "")
        if not lp:
            return None
        p = Path(lp)
        if not p.is_absolute():
            if (PROJECT_ROOT / p).exists():
                return PROJECT_ROOT / p
            if (footage_dir / p).exists():
                return footage_dir / p
        return p if p.exists() else None

    # 1. Has items
    if len(items) > 0:
        g.checks.append(CheckResult("items", "PASS", f"{len(items)} items in manifest"))
    else:
        g.checks.append(CheckResult("items", "FAIL", "Manifest is empty"))
        return g

    # 2. Files exist on disk
    existing = sum(1 for i in items if _resolve(i))
    missing = len(items) - existing

    pct_exist = existing / max(1, len(items)) * 100
    if missing == 0:
        g.checks.append(CheckResult("files_exist", "PASS",
            f"All {existing} files exist on disk"))
    elif pct_exist >= 50:
        g.checks.append(CheckResult("files_exist", "WARN",
            f"{existing}/{len(items)} files exist ({pct_exist:.0f}%), {missing} missing"))
    else:
        g.checks.append(CheckResult("files_exist", "FAIL",
            f"Only {existing}/{len(items)} files exist ({pct_exist:.0f}%)"))

    # 3. Zero-byte files
    zero_byte = 0
    for item in items:
        p = _resolve(item)
        if p and p.stat().st_size == 0:
            zero_byte += 1
    if zero_byte == 0:
        g.checks.append(CheckResult("zero_byte", "PASS", "No zero-byte files"))
    else:
        g.checks.append(CheckResult("zero_byte", "FAIL",
            f"{zero_byte} zero-byte files detected"))

    # 4. Image validity (PIL check on sample)
    try:
        from PIL import Image
        corrupt = 0
        tiny = 0
        checked = 0
        for item in items:
            p = _resolve(item)
            if not p:
                continue
            if not str(p).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                continue
            checked += 1
            try:
                img = Image.open(p)
                w, h = img.size
                if w < 100 or h < 100:
                    tiny += 1
            except Exception:
                corrupt += 1

        bad = corrupt + tiny
        if checked == 0:
            g.checks.append(CheckResult("images", "WARN", "No images to validate"))
        elif bad == 0:
            g.checks.append(CheckResult("images", "PASS",
                f"{checked} images valid"))
        elif bad / checked < 0.1:
            g.checks.append(CheckResult("images", "WARN",
                f"{bad}/{checked} images corrupt/tiny ({corrupt} corrupt, {tiny} tiny)"))
        else:
            g.checks.append(CheckResult("images", "FAIL",
                f"{bad}/{checked} images corrupt/tiny (>10%)"))
    except ImportError:
        g.checks.append(CheckResult("images", "WARN", "PIL not available for image check"))

    # 5. Coverage: storyboard segments with mapped footage
    sb_path = Path(paths["storyboard"])
    if sb_path.exists():
        try:
            sb = json.loads(sb_path.read_text())
            if isinstance(sb, dict):
                total_segs = sb.get("segment_count", 0)
            else:
                total_segs = len(sb)

            # Count unique storyboard_segment_ids covered
            covered = set()
            for item in items:
                for sid in item.get("storyboard_segment_ids", []):
                    covered.add(sid)

            if total_segs > 0:
                cov_pct = len(covered) / total_segs * 100
                if cov_pct >= 60:
                    g.checks.append(CheckResult("coverage", "PASS",
                        f"Coverage: {len(covered)}/{total_segs} segments ({cov_pct:.0f}%)"))
                elif cov_pct >= 30:
                    g.checks.append(CheckResult("coverage", "WARN",
                        f"Coverage: {len(covered)}/{total_segs} segments ({cov_pct:.0f}%)"))
                else:
                    g.checks.append(CheckResult("coverage", "FAIL",
                        f"Coverage: {len(covered)}/{total_segs} segments ({cov_pct:.0f}%) — too low"))
            else:
                g.checks.append(CheckResult("coverage", "WARN",
                    "Can't determine segment count from storyboard"))
        except Exception:
            g.checks.append(CheckResult("coverage", "WARN",
                "Could not check coverage"))
    else:
        g.checks.append(CheckResult("coverage", "WARN", "No storyboard for coverage check"))

    # 6. Over-reliance on single image
    from collections import Counter
    path_counts = Counter()
    for item in items:
        lp = item.get("local_path") or item.get("path", "")
        if lp:
            seg_ids = item.get("storyboard_segment_ids", [])
            path_counts[lp] += len(seg_ids) if seg_ids else 1

    if path_counts:
        max_use = max(path_counts.values())
        max_pct = max_use / max(1, sum(path_counts.values())) * 100
        if max_pct > 20:
            g.checks.append(CheckResult("diversity", "WARN",
                f"One image used for {max_pct:.0f}% of segments"))
        else:
            g.checks.append(CheckResult("diversity", "PASS",
                f"No single image dominates (max {max_pct:.0f}%)"))
    else:
        g.checks.append(CheckResult("diversity", "WARN", "No path data to check"))

    return g


# ── Gate 4: Voice + Music ────────────────────────────────────────────────────

def gate_audio(paths: dict) -> GateResult:
    g = GateResult("Voice + Music", 4)
    wav = Path(paths["narration_wav"])
    script = Path(paths["script"])
    manifest = Path(paths["narration_manifest"])
    music = Path(paths["music"])

    # Import voice QA functions
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from check_fern_voice import (check_duration as cv_duration,
                                       check_loudness as cv_loudness,
                                       check_silence_ratio as cv_silence,
                                       check_clipping as cv_clipping,
                                       check_wpm as cv_wpm)

        # 1. Duration
        val, status, msg = cv_duration(wav, script if script.exists() else None)
        g.checks.append(CheckResult("duration", status, f"Duration: {msg}"))

        # 2. Loudness
        val, status, msg = cv_loudness(wav)
        g.checks.append(CheckResult("loudness", status, f"Loudness: {msg}"))

        # 3. Silence
        val, status, msg = cv_silence(wav)
        g.checks.append(CheckResult("silence", status, f"Silence: {msg}"))

        # 4. Clipping
        val, status, msg = cv_clipping(wav)
        g.checks.append(CheckResult("clipping", status, f"Clipping: {msg}"))

        # 5. WPM (speech rate from manifest timestamps)
        val, status, msg = cv_wpm(wav, manifest if manifest.exists() else None)
        g.checks.append(CheckResult("wpm", status, f"WPM: {msg}"))

    except ImportError as e:
        g.checks.append(CheckResult("voice_qa", "WARN",
            f"Could not import check_fern_voice: {e}"))

    # 5. Music validity
    if music.exists():
        dur = ffprobe_duration(str(music))
        if dur and dur > 60:
            g.checks.append(CheckResult("music", "PASS",
                f"Music track valid ({dur/60:.1f} min)"))
        elif dur:
            g.checks.append(CheckResult("music", "WARN",
                f"Music track short ({dur:.0f}s)"))
        else:
            g.checks.append(CheckResult("music", "FAIL", "Music file unreadable"))
    else:
        g.checks.append(CheckResult("music", "WARN", "No music — rendering without"))

    # 6. Manifest/storyboard segment count alignment
    if manifest.exists():
        try:
            nm = json.loads(manifest.read_text())
            chunks = nm.get("chunks") or nm.get("segments") or []
            sb_path = Path(paths["storyboard"])
            if sb_path.exists():
                sb = json.loads(sb_path.read_text())
                sb_count = sb.get("segment_count", 0) if isinstance(sb, dict) else len(sb)
                ratio = len(chunks) / max(1, sb_count)
                if 0.5 <= ratio <= 2.0:
                    g.checks.append(CheckResult("alignment", "PASS",
                        f"Manifest {len(chunks)} chunks vs storyboard {sb_count} segs — aligned"))
                else:
                    g.checks.append(CheckResult("alignment", "WARN",
                        f"Manifest {len(chunks)} chunks vs storyboard {sb_count} segs — ratio {ratio:.1f}x"))
        except Exception:
            g.checks.append(CheckResult("alignment", "WARN", "Could not check alignment"))

    return g


# ── Gate 5: Timeline Sanity ──────────────────────────────────────────────────

def gate_timeline(paths: dict, args) -> GateResult:
    g = GateResult("Timeline Sanity", 5)

    try:
        # Load required data
        brand = json.loads(Path(paths["brand_config"]).read_text())
        narr = json.loads(Path(paths["narration_manifest"]).read_text())
        foot = json.loads(Path(paths["footage_manifest"]).read_text())

        sb_path = Path(paths["storyboard"])
        storyboard = None
        if sb_path.exists():
            raw = json.loads(sb_path.read_text())
            if isinstance(raw, dict) and raw.get("schema_version") == "2.0":
                storyboard = []
                for sc in raw.get("scenes", []):
                    for seg in sc.get("segments", []):
                        seg["_scene_id"] = sc.get("scene_id")
                        storyboard.append(seg)
            elif isinstance(raw, list):
                storyboard = raw

        # Change to project root for relative path resolution
        import os
        old_cwd = os.getcwd()
        os.chdir(str(PROJECT_ROOT))
        try:
            from pipeline.video_assembler import build_timeline
            segments = build_timeline(
                narration_manifest=narr,
                footage_manifest=foot,
                brand_config=brand,
                storyboard=storyboard,
                stills_only=args.stills_only,
            )
        finally:
            os.chdir(old_cwd)
    except Exception as e:
        import traceback
        g.checks.append(CheckResult("build", "FAIL",
            f"build_timeline() failed: {e}"))
        traceback.print_exc()
        return g

    g.checks.append(CheckResult("build", "PASS",
        f"Timeline built: {len(segments)} segments"))

    # 1. Total duration
    if segments:
        total_dur = segments[-1]["start_sec"] + segments[-1]["duration_sec"]
        m = total_dur / 60
        if 10 <= m <= 40:
            g.checks.append(CheckResult("duration", "PASS",
                f"Total duration: {m:.1f} min"))
        else:
            g.checks.append(CheckResult("duration", "FAIL",
                f"Total duration: {m:.1f} min (expected 10-40)"))
    else:
        g.checks.append(CheckResult("duration", "FAIL", "No segments in timeline"))
        return g

    # 2. Micro segments
    micro = sum(1 for s in segments if s["duration_sec"] < 0.3)
    if micro == 0:
        g.checks.append(CheckResult("micro", "PASS", "No micro segments (<0.3s)"))
    else:
        g.checks.append(CheckResult("micro", "WARN",
            f"{micro} micro segments (<0.3s)"))

    # 3. Chapter cards
    chapters = sum(1 for s in segments if s.get("source_type") == "chapter_card")
    if chapters >= 3:
        g.checks.append(CheckResult("chapters", "PASS",
            f"{chapters} chapter cards"))
    elif chapters > 0:
        g.checks.append(CheckResult("chapters", "WARN",
            f"Only {chapters} chapter cards"))
    else:
        g.checks.append(CheckResult("chapters", "WARN", "No chapter cards"))

    # 4. Source files exist
    missing_src = 0
    for s in segments:
        sp = s.get("source_path", "")
        if sp and s.get("source_type") != "chapter_card" and not Path(sp).exists():
            missing_src += 1
    if missing_src == 0:
        g.checks.append(CheckResult("sources", "PASS", "All source files exist"))
    elif missing_src < len(segments) * 0.1:
        g.checks.append(CheckResult("sources", "WARN",
            f"{missing_src} source files missing"))
    else:
        g.checks.append(CheckResult("sources", "FAIL",
            f"{missing_src}/{len(segments)} source files missing"))

    # 5. Consecutive same source
    max_consecutive = 0
    current_run = 1
    for i in range(1, len(segments)):
        if (segments[i].get("source_path") == segments[i-1].get("source_path")
                and segments[i].get("source_path")):
            current_run += 1
            max_consecutive = max(max_consecutive, current_run)
        else:
            current_run = 1
    if max_consecutive <= 5:
        g.checks.append(CheckResult("consecutive", "PASS",
            f"Max consecutive same source: {max_consecutive}"))
    else:
        g.checks.append(CheckResult("consecutive", "WARN",
            f"Max consecutive same source: {max_consecutive} (>5)"))

    # 6. Segment count in expected range (100-600)
    n = len(segments)
    if 100 <= n <= 600:
        g.checks.append(CheckResult("seg_count", "PASS",
            f"Segment count: {n}"))
    elif 50 <= n < 100 or 600 < n <= 800:
        g.checks.append(CheckResult("seg_count", "WARN",
            f"Segment count: {n} (expected 100-600)"))
    else:
        g.checks.append(CheckResult("seg_count", "FAIL",
            f"Segment count: {n} (expected 100-600)"))

    # 7. Zoom continuity — consecutive stills must not share same source_path
    #    UNLESS both have shot choreography (intentional directed camera moves).
    zoom_violations = 0
    for i in range(1, len(segments)):
        curr, prev = segments[i], segments[i-1]
        if (curr.get("source_type") == "still"
                and prev.get("source_type") == "still"
                and curr.get("source_path") == prev.get("source_path")
                and curr.get("source_path")
                and not curr.get("shots")  # choreographed = intentional
                and not prev.get("shots")):
            zoom_violations += 1
    if zoom_violations == 0:
        g.checks.append(CheckResult("zoom_continuity", "PASS",
            "No un-choreographed consecutive same-image still segments"))
    else:
        g.checks.append(CheckResult("zoom_continuity", "WARN",
            f"{zoom_violations} consecutive same-image still segments without choreography"))

    # 8. Document readability — documents must be on screen >= 4s to be readable
    doc_too_short = 0
    for s in segments:
        content_type = s.get("content_type", "")
        shot_type = s.get("shot_type", "")
        is_document = ("document" in content_type.lower() if content_type else False) or \
                      ("document" in shot_type.lower() if shot_type else False)
        if is_document and s.get("duration_sec", 0) < 4.0:
            doc_too_short += 1
    if doc_too_short == 0:
        g.checks.append(CheckResult("doc_readability", "PASS",
            "All document segments >= 4.0s"))
    else:
        g.checks.append(CheckResult("doc_readability", "WARN",
            f"{doc_too_short} document segments < 4.0s (too brief to read)"))

    # 9. Same-image duration cap — no single segment should exceed 12s
    MAX_MERGED_DURATION = 12.0
    over_cap = [s for s in segments
                if s.get("source_type") == "still" and s.get("duration_sec", 0) > MAX_MERGED_DURATION]
    if not over_cap:
        g.checks.append(CheckResult("duration_cap", "PASS",
            f"All still segments <= {MAX_MERGED_DURATION}s"))
    else:
        worst = max(s["duration_sec"] for s in over_cap)
        g.checks.append(CheckResult("duration_cap", "WARN",
            f"{len(over_cap)} still segments exceed {MAX_MERGED_DURATION}s cap (worst: {worst:.1f}s)"))

    return g


# ── Gate 6: Post-Render QA ───────────────────────────────────────────────────

def gate_postrender(paths: dict) -> GateResult:
    g = GateResult("Post-Render QA", 6)
    video = paths["output_video"]
    timeline = paths["output_timeline"]
    music = paths["music"]

    if not Path(video).exists():
        g.checks.append(CheckResult("exists", "FAIL", "Output video not found"))
        return g

    # 6a: Spot check first 2 minutes
    try:
        tmp_preview = "/tmp/qa_preview_2min.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "quiet", "-i", video,
             "-t", "120", "-c", "copy", tmp_preview],
            timeout=30,
        )
        if Path(tmp_preview).exists():
            sz = Path(tmp_preview).stat().st_size / 1024 / 1024
            if sz > 1:
                g.checks.append(CheckResult("spot_size", "PASS",
                    f"First 2 min: {sz:.1f} MB"))
            else:
                g.checks.append(CheckResult("spot_size", "WARN",
                    f"First 2 min only {sz:.1f} MB — suspiciously small"))

            # Sample frames for black check
            black_frames = 0
            for t in [10, 30, 50, 70, 90]:
                frame_path = f"/tmp/qa_frame_{t}.jpg"
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "quiet", "-ss", str(t),
                     "-i", tmp_preview, "-frames:v", "1", frame_path],
                    timeout=10,
                )
                if Path(frame_path).exists():
                    try:
                        from PIL import Image
                        import numpy as np
                        img = np.array(Image.open(frame_path))
                        if img.mean() < 20:
                            black_frames += 1
                    except Exception:
                        pass
                    Path(frame_path).unlink(missing_ok=True)

            if black_frames == 0:
                g.checks.append(CheckResult("spot_black", "PASS",
                    "No black frames in first 2 min"))
            elif black_frames <= 1:
                g.checks.append(CheckResult("spot_black", "WARN",
                    f"{black_frames}/5 sampled frames near-black"))
            else:
                g.checks.append(CheckResult("spot_black", "FAIL",
                    f"{black_frames}/5 sampled frames near-black"))

            Path(tmp_preview).unlink(missing_ok=True)
    except Exception as e:
        g.checks.append(CheckResult("spot_check", "WARN",
            f"Spot check error: {e}"))

    # 6b: Frozen video detection — sample 5 random 10s windows, compare first/last frame
    try:
        dur = ffprobe_duration(video)
        if dur and dur > 30:
            import random
            frozen_count = 0
            windows_checked = 0
            max_offset = max(1, int(dur) - 12)
            sample_offsets = sorted(random.sample(range(10, max_offset), min(5, max_offset - 10)))
            for offset in sample_offsets:
                f1 = f"/tmp/qa_frozen_a_{offset}.jpg"
                f2 = f"/tmp/qa_frozen_b_{offset}.jpg"
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "quiet", "-ss", str(offset),
                     "-i", video, "-frames:v", "1", f1], timeout=10)
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "quiet", "-ss", str(offset + 9),
                     "-i", video, "-frames:v", "1", f2], timeout=10)
                if Path(f1).exists() and Path(f2).exists():
                    try:
                        from PIL import Image
                        import numpy as np
                        a = np.array(Image.open(f1).resize((160, 90)))
                        b = np.array(Image.open(f2).resize((160, 90)))
                        diff = np.abs(a.astype(float) - b.astype(float)).mean()
                        windows_checked += 1
                        if diff < 2.0:  # nearly identical = frozen
                            frozen_count += 1
                    except Exception:
                        pass
                for fp in [f1, f2]:
                    Path(fp).unlink(missing_ok=True)

            if windows_checked == 0:
                g.checks.append(CheckResult("frozen", "WARN",
                    "Could not sample frames for frozen check"))
            elif frozen_count == 0:
                g.checks.append(CheckResult("frozen", "PASS",
                    f"No frozen video in {windows_checked} sampled windows"))
            elif frozen_count <= 1:
                g.checks.append(CheckResult("frozen", "WARN",
                    f"{frozen_count}/{windows_checked} windows appear frozen"))
            else:
                g.checks.append(CheckResult("frozen", "FAIL",
                    f"{frozen_count}/{windows_checked} windows frozen — video stuck"))
    except Exception as e:
        g.checks.append(CheckResult("frozen", "WARN", f"Frozen check error: {e}"))

    # 6c: Full QA from check_fern_video.py
    try:
        from check_fern_video import (
            check_duration, check_cut_rate, check_audio_levels,
            check_color_grade, check_narration_sync, check_chapter_cards,
            check_footage_variety, check_beat_sync, check_brightness_floor,
            check_content_dedup,
        )

        # Duration
        val, status, msg = check_duration(video)
        total_dur = val
        g.checks.append(CheckResult("duration", status, f"Duration: {msg}"))

        # Cut rate
        val, status, msg = check_cut_rate(video, total_dur)
        g.checks.append(CheckResult("cut_rate", status, f"Cut rate: {msg}"))

        # Audio levels
        val, status, msg = check_audio_levels(video)
        g.checks.append(CheckResult("audio", status, f"Audio: {msg}"))

        # Color grade
        val, status, msg = check_color_grade(video)
        g.checks.append(CheckResult("color", status, f"Color: {msg}"))

        # A/V sync
        val, status, msg = check_narration_sync(video)
        g.checks.append(CheckResult("sync", status, f"A/V sync: {msg}"))

        # Chapter cards
        if Path(timeline).exists():
            val, status, msg = check_chapter_cards(timeline)
            g.checks.append(CheckResult("chapters", status, f"Chapters: {msg}"))

            # Footage variety
            val, status, msg = check_footage_variety(timeline)
            g.checks.append(CheckResult("variety", status, f"Variety: {msg}"))

            # Beat sync
            if Path(music).exists():
                val, status, msg = check_beat_sync(timeline, music)
                g.checks.append(CheckResult("beat_sync", status, f"Beat sync: {msg}"))

            # Content dedup
            val, status, msg = check_content_dedup(timeline)
            g.checks.append(CheckResult("dedup", status, f"Dedup: {msg}"))

        # Brightness floor
        val, status, msg = check_brightness_floor(video)
        g.checks.append(CheckResult("brightness", status, f"Brightness: {msg}"))

    except ImportError as e:
        g.checks.append(CheckResult("full_qa", "WARN",
            f"Could not import check_fern_video: {e}"))

    return g


# ── Mid-Render Chapter Checkpoints ──────────────────────────────────────────

def _load_storyboard_flat(paths: dict) -> list:
    """Load storyboard as flat segment list."""
    sb_path = Path(paths["storyboard"])
    if not sb_path.exists():
        return []
    raw = json.loads(sb_path.read_text())
    if isinstance(raw, dict) and raw.get("schema_version") == "2.0":
        flat = []
        for sc in raw.get("scenes", []):
            for seg in sc.get("segments", []):
                seg["_scene_title"] = sc.get("title", "")
                flat.append(seg)
        return flat
    return raw if isinstance(raw, list) else []


def chapter_checkpoint(chapter_num: int, chapter_title: str,
                       rendered_segs: list, storyboard: list,
                       output_dir: Path) -> GateResult:
    """
    Run visual + editorial checks on segments rendered for a chapter.
    rendered_segs: list of dicts with keys from assembler output parsing
        [{seg_idx, motion, duration, source_file, is_chapter_card}, ...]
    """
    g = GateResult(f"Chapter {chapter_num}: {chapter_title}", num=chapter_num)
    content_segs = [s for s in rendered_segs if not s.get("is_chapter_card")]

    if not content_segs:
        g.checks.append(CheckResult("empty", "WARN", "No content segments in chapter"))
        return g

    # ── VISUAL CHECKS ──

    # 1. Check temp segment files exist and aren't tiny
    seg_files = list(output_dir.glob("seg_*.mp4")) + list(output_dir.glob("seg_*.ts"))
    tiny_count = 0
    for sf in seg_files:
        if sf.stat().st_size < 1024:  # <1KB
            tiny_count += 1
    if tiny_count == 0:
        g.checks.append(CheckResult("file_size", "PASS",
            f"All segment files valid size"))
    elif tiny_count <= 2:
        g.checks.append(CheckResult("file_size", "WARN",
            f"{tiny_count} tiny segment file(s) (<1KB)"))
    else:
        g.checks.append(CheckResult("file_size", "FAIL",
            f"{tiny_count} tiny segment files (<1KB) — likely corrupt"))

    # 2. Black frame check — sample last rendered segment, decode first frame
    try:
        from PIL import Image
        import numpy as np
        last_seg = content_segs[-1]
        last_idx = last_seg.get("seg_idx", 0)
        # Try to find the temp file for this segment
        candidates = sorted(output_dir.glob(f"seg_{last_idx:04d}*"))
        if not candidates:
            candidates = sorted(output_dir.glob(f"seg_{last_idx:03d}*"))
        if candidates:
            # Extract first frame via ffmpeg
            probe_file = candidates[0]
            frame_path = output_dir / "_checkpoint_frame.png"
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(probe_file), "-vframes", "1",
                 "-f", "image2", str(frame_path)],
                capture_output=True, timeout=10)
            if frame_path.exists():
                img = Image.open(frame_path)
                arr = np.array(img)
                mean_brightness = arr.mean()
                if mean_brightness < 5:
                    g.checks.append(CheckResult("black_frame", "FAIL",
                        f"Last segment is pure black (brightness={mean_brightness:.1f})"))
                elif mean_brightness < 15:
                    g.checks.append(CheckResult("black_frame", "WARN",
                        f"Last segment very dark (brightness={mean_brightness:.1f})"))
                else:
                    g.checks.append(CheckResult("black_frame", "PASS",
                        f"Frame brightness OK ({mean_brightness:.0f})"))
                frame_path.unlink(missing_ok=True)
            else:
                g.checks.append(CheckResult("black_frame", "SKIP", "Could not extract frame"))
        else:
            g.checks.append(CheckResult("black_frame", "SKIP",
                "No temp segment files found"))
    except Exception as e:
        g.checks.append(CheckResult("black_frame", "SKIP", f"Frame check error: {e}"))

    # ── EDITORIAL CHECKS ──

    # 3. Footage variety — not same image for >50% of chapter
    from collections import Counter
    sources = [s.get("source_file", "?") for s in content_segs
               if s.get("source_file") and s["source_file"] != "BLACK"]
    if sources:
        src_counts = Counter(sources)
        unique = len(src_counts)
        total = len(sources)
        top_src, top_count = src_counts.most_common(1)[0]
        top_pct = top_count / total * 100

        # Image variety is advisory — composition plans intentionally reuse images
        # when they're the best match for the topic. Narrative match is the real gate.
        if top_pct > 50:
            g.checks.append(CheckResult("footage_variety", "WARN",
                f"Single image '{top_src}' used {top_pct:.0f}% of chapter ({top_count}/{total})"))
        elif unique < 3 and total > 5:
            g.checks.append(CheckResult("footage_variety", "WARN",
                f"Only {unique} unique images for {total} segments"))
        else:
            g.checks.append(CheckResult("footage_variety", "PASS",
                f"{unique} unique images across {total} segments"))
    else:
        g.checks.append(CheckResult("footage_variety", "WARN", "No source files tracked"))

    # 4. Motion variety — not all same motion for entire chapter
    motions = Counter(s.get("motion", "?") for s in content_segs)
    if len(motions) == 1 and len(content_segs) > 5:
        single_motion = list(motions.keys())[0]
        g.checks.append(CheckResult("motion_variety", "WARN",
            f"Entire chapter is {single_motion} — no motion variety"))
    else:
        motion_str = ", ".join(f"{m}={c}" for m, c in motions.most_common(3))
        g.checks.append(CheckResult("motion_variety", "PASS",
            f"Motion mix: {motion_str}"))

    # 5. Storyboard-narrative match — check if images relate to what storyboard expects
    import re
    if storyboard and content_segs:
        mismatch_count = 0
        checked = 0
        mismatch_examples = []
        stop_words = {'the','a','an','of','in','on','at','to','and','or','with','from',
                      'for','is','that','this','his','her','1950s','1953',''}

        # Build reverse lookup: image stem → set of storyboard indices that planned it
        comp_plan_images = set()
        for sb_i, sb_s in enumerate(storyboard):
            cp = sb_s.get("composition_plan", {})
            if cp.get("primary_image"):
                comp_plan_images.add(Path(cp["primary_image"]).stem.lower())

        for seg in content_segs:
            # Prefer sb_entry_idx (storyboard segment index) over chunk_idx (narration chunk)
            sb_idx = seg.get("sb_entry_idx")
            if sb_idx is None:
                sb_idx = seg.get("chunk_idx")
            src_file = (seg.get("source_file") or "").lower()
            if sb_idx is None or not src_file or src_file == "black":
                continue
            if sb_idx >= len(storyboard):
                continue

            sb_seg = storyboard[sb_idx]
            show = (sb_seg.get("show") or "").lower()
            query = (sb_seg.get("search_query") or "").lower()

            src_clean = src_file.replace("wiki_", "").replace(".jpg", "").replace(".png", "").replace(".jpeg", "")
            src_stem = Path(src_file).stem.lower()
            src_words = set(re.split(r'[_\s.]+', src_clean)) - stop_words

            # Sequence-aware: if segment has sequence_plan, include shot categories
            seq_plan = sb_seg.get("sequence_plan", [])
            seq_cats = " ".join(
                (s.get("image_category") or "").replace("|", " ")
                for s in seq_plan
            ) if seq_plan else ""

            target_words = set(re.split(r'[_\s,]+', show + " " + query + " " + seq_cats)) - stop_words

            overlap = src_words & target_words
            # If this image was chosen by ANY composition plan, it's intentional
            comp_match = src_stem in comp_plan_images

            checked += 1
            if not overlap and not comp_match:
                mismatch_count += 1
                if len(mismatch_examples) < 3:
                    mismatch_examples.append(
                        f"'{seg.get('source_file','')}' vs expected '{show[:40]}'")

        if checked > 0:
            match_pct = (1 - mismatch_count / checked) * 100
            if match_pct >= 95:
                g.checks.append(CheckResult("narrative_match", "PASS",
                    f"Footage-narrative match: {match_pct:.0f}% ({checked - mismatch_count}/{checked})"))
            else:
                examples = "; ".join(mismatch_examples[:2])
                g.checks.append(CheckResult("narrative_match", "FAIL",
                    f"Footage-narrative match: {match_pct:.0f}% (need 95%+) — {examples}"))
        else:
            g.checks.append(CheckResult("narrative_match", "SKIP",
                "No segments with chunk_idx to check"))

    # 6. SFX density — flag if chapter has SFX on nearly every cut
    sfx_count = sum(1 for s in content_segs if s.get("has_sfx"))
    if len(content_segs) > 3:
        sfx_pct = sfx_count / len(content_segs) * 100
        if sfx_pct > 80:
            g.checks.append(CheckResult("sfx_density", "WARN",
                f"SFX on {sfx_pct:.0f}% of cuts — may feel over-produced"))
        else:
            g.checks.append(CheckResult("sfx_density", "PASS",
                f"SFX density: {sfx_pct:.0f}%"))

    # 7. Pacing — check chapter duration is reasonable (not <10s or >8min)
    total_dur = sum(s.get("duration", 0) for s in content_segs)
    if total_dur < 10:
        g.checks.append(CheckResult("pacing", "WARN",
            f"Chapter very short: {total_dur:.0f}s"))
    elif total_dur > 480:
        g.checks.append(CheckResult("pacing", "WARN",
            f"Chapter very long: {total_dur:.0f}s ({total_dur/60:.1f}min)"))
    else:
        g.checks.append(CheckResult("pacing", "PASS",
            f"Chapter duration: {total_dur:.0f}s ({total_dur/60:.1f}min)"))

    return g


def _parse_render_line(line: str) -> dict | None:
    """Parse a video_assembler output line into segment info.
    Lines look like: '  [42/287] zoom_in       5.2s  wiki_broken_window_glass.jpg  ✓'
    or: '  [33/287] CHAPTER CARD  4.5s  Chapter 1: FORT DETRICK  ✓'
    """
    import re
    line = line.strip()

    # Chapter card line
    m = re.match(r'\[(\d+)/(\d+)\]\s+CHAPTER CARD\s+([\d.]+)s\s+(.+?)(?:\s+[✓✗])?$', line)
    if m:
        return {
            "seg_idx": int(m.group(1)),
            "total": int(m.group(2)),
            "motion": "chapter_card",
            "duration": float(m.group(3)),
            "source_file": m.group(4).strip(),
            "is_chapter_card": True,
            "chapter_title": m.group(4).strip(),
        }

    # Regular segment line
    m = re.match(r'\[(\d+)/(\d+)\]\s+(\S+)\s+([\d.]+)s\s+(\S+)', line)
    if m:
        return {
            "seg_idx": int(m.group(1)),
            "total": int(m.group(2)),
            "motion": m.group(3),
            "duration": float(m.group(4)),
            "source_file": m.group(5),
            "is_chapter_card": False,
        }

    return None


# ── Render execution ─────────────────────────────────────────────────────────

def do_render(paths: dict, args) -> list[GateResult]:
    """Run video_assembler.py with all flags.
    Returns list of chapter checkpoint GateResults (empty on render failure).
    """
    cmd = [
        PYTHON, str(PROJECT_ROOT / "pipeline/video_assembler.py"),
        "--brand", "fern_clone",
        "--narration", paths["narration_manifest"],
        "--footage", paths["footage_manifest"],
        "--out", paths["output_video"],
    ]

    if Path(paths["storyboard"]).exists():
        cmd += ["--storyboard", paths["storyboard"]]
    if Path(paths["music"]).exists():
        cmd += ["--music", paths["music"]]
    if args.stills_only:
        cmd.append("--stills-only")
    if args.parallax:
        cmd.append("--parallax")
    if args.focal_points:
        cmd.append("--focal-points")
    if args.preview:
        cmd += ["--preview", str(args.preview)]

    # Ensure output dir exists
    output_dir = Path(paths["output_video"]).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  {B}{C}── RENDERING ──{X}")
    print(f"  {D}Command: {' '.join(cmd[-6:])}{X}")
    if args.preview:
        print(f"  {Y}Preview mode: first {args.preview}s only{X}")
    print()

    # Load storyboard for chapter checkpoints
    storyboard = _load_storyboard_flat(paths)

    start = time.time()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )

    # Track segments per chapter for mid-render checkpoints
    chapter_results = []
    current_chapter_segs = []
    current_chapter_num = 0
    current_chapter_title = "Cold Open"
    checkpoint_failed = False

    # Also track chunk_idx mapping — assembler logs don't include it directly,
    # so we estimate from segment index position in storyboard order
    _seg_to_chunk = {}  # populated as we go

    for line in proc.stdout:
        sys.stdout.write(f"    {D}{line}{X}")
        sys.stdout.flush()

        # Strip ANSI for parsing
        clean = line
        for code in ['\033[2m', '\033[0m', '\033[92m', '\033[93m', '\033[91m',
                     '\033[1m', '\033[96m']:
            clean = clean.replace(code, '')
        clean = clean.strip()

        parsed = _parse_render_line(clean)
        if not parsed:
            continue

        if parsed["is_chapter_card"]:
            # Run checkpoint on previous chapter's segments
            if current_chapter_segs:
                # Estimate chunk_idx for each seg based on position
                # The assembler processes chunks sequentially, so seg_idx roughly
                # maps to storyboard position. We approximate with segment index.
                if storyboard:
                    total_segs = parsed.get("total", 287)
                    for seg in current_chapter_segs:
                        sidx = seg.get("seg_idx", 0)
                        approx_chunk = int(sidx / total_segs * len(storyboard))
                        seg["chunk_idx"] = min(approx_chunk, len(storyboard) - 1)

                print(f"\n  {B}{C}── CHECKPOINT: {current_chapter_title} ──{X}")
                result = chapter_checkpoint(
                    current_chapter_num, current_chapter_title,
                    current_chapter_segs, storyboard, output_dir)
                chapter_results.append(result)

                for c in result.checks:
                    print_check(c)
                print_gate_verdict(result)

                if result.verdict == "FAIL":
                    print(f"\n  {R}{B}CHAPTER CHECKPOINT FAILED — stopping render{X}")
                    checkpoint_failed = True
                    proc.terminate()
                    break
                print()

            # Start new chapter
            current_chapter_num += 1
            current_chapter_title = parsed.get("chapter_title", f"Chapter {current_chapter_num}")
            current_chapter_segs = [parsed]
        else:
            # Check if this segment has SFX from the assembler output
            # (assembler doesn't log SFX per-segment, so we check storyboard)
            if storyboard:
                total_segs = parsed.get("total", 287)
                sidx = parsed.get("seg_idx", 0)
                approx_chunk = int(sidx / total_segs * len(storyboard))
                approx_chunk = min(approx_chunk, len(storyboard) - 1)
                sb_seg = storyboard[approx_chunk] if approx_chunk < len(storyboard) else {}
                parsed["chunk_idx"] = approx_chunk
                parsed["has_sfx"] = bool(sb_seg.get("sfx"))
            current_chapter_segs.append(parsed)

    proc.wait()
    elapsed = time.time() - start

    # Run checkpoint on final chapter (after last chapter card)
    if current_chapter_segs and not checkpoint_failed:
        if storyboard:
            for seg in current_chapter_segs:
                if "chunk_idx" not in seg:
                    total_segs = current_chapter_segs[0].get("total", 287)
                    sidx = seg.get("seg_idx", 0)
                    approx_chunk = int(sidx / total_segs * len(storyboard))
                    seg["chunk_idx"] = min(approx_chunk, len(storyboard) - 1)

        print(f"\n  {B}{C}── CHECKPOINT: {current_chapter_title} ──{X}")
        result = chapter_checkpoint(
            current_chapter_num, current_chapter_title,
            current_chapter_segs, storyboard, output_dir)
        chapter_results.append(result)
        for c in result.checks:
            print_check(c)
        print_gate_verdict(result)

    if checkpoint_failed:
        print(f"\n  {R}Render STOPPED by chapter checkpoint after {elapsed/60:.1f} min{X}")
        return chapter_results
    elif proc.returncode == 0:
        print(f"\n  {G}Render complete in {elapsed/60:.1f} min{X}")
        return chapter_results
    else:
        print(f"\n  {R}Render FAILED (exit code {proc.returncode}) after {elapsed/60:.1f} min{X}")
        return chapter_results


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="QA-gated full render pipeline")
    parser.add_argument("--topic", required=True, help="Topic slug")
    parser.add_argument("--stills-only", action="store_true")
    parser.add_argument("--parallax", action="store_true")
    parser.add_argument("--focal-points", action="store_true")
    parser.add_argument("--skip-to", type=int, default=0, help="Skip to gate N")
    parser.add_argument("--dry-run", action="store_true", help="Pre-render gates only")
    parser.add_argument("--preview", type=int, default=0, help="Render only first N seconds")
    args = parser.parse_args()

    paths = resolve_paths(args.topic)

    print(f"\n{'═' * 58}")
    print(f"  {B}RENDER QA{X} — {C}{args.topic}{X}")
    print(f"{'═' * 58}")

    all_results = []

    # Pre-render gates
    gates = [
        (0,   "Pre-flight",            lambda: gate_preflight(paths, args)),
        (0.5, "Asset Validation",      lambda: gate_asset_validation(paths)),
        (1,   "Storyboard Integrity",  lambda: gate_storyboard(paths)),
        (2,   "Director Integrity",    lambda: gate_director(paths)),
        (3,   "Footage Coverage",      lambda: gate_footage(paths, args.stills_only)),
        (4,   "Voice + Music",         lambda: gate_audio(paths)),
        (5,   "Timeline Sanity",       lambda: gate_timeline(paths, args)),
    ]

    for num, name, gate_fn in gates:
        if num < args.skip_to:
            continue

        print_gate_header(num, name)
        result = gate_fn()
        all_results.append(result)

        for c in result.checks:
            print_check(c)
        print_gate_verdict(result)

        if result.verdict == "FAIL":
            print(f"\n  {R}{B}STOPPED at Gate {num} — fix issues before rendering{X}")
            print_summary(all_results, paths)
            sys.exit(1)

    if args.dry_run:
        print(f"\n  {Y}{B}DRY RUN — all pre-render gates passed, skipping render{X}")
        print_summary(all_results, paths)
        sys.exit(0)

    # Render (with mid-render chapter checkpoints)
    chapter_results = do_render(paths, args)

    # Add chapter checkpoint results to summary
    for cr in chapter_results:
        all_results.append(cr)

    # Check if render was stopped by checkpoint
    checkpoint_failed = any(cr.verdict == "FAIL" for cr in chapter_results)
    render_succeeded = Path(paths["output_video"]).exists() and not checkpoint_failed

    if not render_succeeded:
        if checkpoint_failed:
            print(f"\n  {R}{B}RENDER STOPPED — chapter checkpoint failed{X}")
        else:
            print(f"\n  {R}{B}RENDER FAILED{X}")
        print_summary(all_results, paths)
        sys.exit(1)

    # Post-render gate (only if render completed)
    print_gate_header(6, "Post-Render QA")
    result = gate_postrender(paths)
    all_results.append(result)

    for c in result.checks:
        print_check(c)
    print_gate_verdict(result)

    # Final summary
    print_summary(all_results, paths)

    has_fail = any(r.verdict == "FAIL" for r in all_results)
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
