#!/usr/bin/env python3
"""
asset_validator.py -- Pre-render validation for SFX audio and footage images.

Catches bad assets BEFORE they waste hours of render time:
  - SFX: spectral analysis (librosa) ensures each file matches its intended
    sound type. A "rumble" with an 8 kHz centroid is probably mislabeled.
  - Images: resolution/corruption checks always run. If Ollama is available,
    adds vision-model checks for content relevance and era plausibility.

SFX validation is fully offline (no Ollama needed).
Image validation degrades gracefully: Ollama checks are skipped if the
server is not running, with a warning in the report.

Usage (standalone):
    venv/bin/python pipeline/asset_validator.py \\
        --topic frank_olson_cia_scientist_lsd_murder_cover_up

Usage (from pipeline):
    from pipeline.asset_validator import validate_all
    result = validate_all(topic, sfx_dir, images_dir, storyboard_path)
    # result["sfx"]    -> list of per-file dicts
    # result["images"] -> list of per-file dicts
    # result["summary"] -> {sfx_pass, sfx_warn, sfx_fail, img_pass, ...}
"""

import argparse
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

# ── SFX spectral specifications ──────────────────────────────────────────────
# max_centroid_hz: expected spectral centroid ceiling for the type.
# Files with centroid > 2x this value are flagged CRITICAL (wrong content).

SFX_SPECS = {
    "rumble": {
        "max_centroid_hz": 500,
        "min_duration": 2.0,
        "max_duration": 10.0,
        "description": "low-frequency sub-bass rumble",
        # Rumbles: slow swell is normal, sustained energy, low spectral bandwidth
        "max_attack_ms": 3000,      # rumbles can build slowly
        "envelope": "sustained",
        "max_spectral_bw_hz": 2000,
    },
    "impact": {
        "max_centroid_hz": 3000,
        "min_duration": 0.3,
        "max_duration": 3.0,
        "description": "bass thud impact",
        "max_attack_ms": 50,        # must hit hard and fast
        "envelope": "transient",    # sharp attack, quick decay
        "max_spectral_bw_hz": 5000,
    },
    "body_impact": {
        "max_centroid_hz": 3000,
        "min_duration": 0.3,
        "max_duration": 3.0,
        "description": "body fall thud",
        "max_attack_ms": 80,        # sharp but slightly softer than metal impact
        "envelope": "transient",
        "max_spectral_bw_hz": 4000,
    },
    "tension": {
        "max_centroid_hz": 4000,
        "min_duration": 1.0,
        "max_duration": 10.0,
        "description": "sustained tense tone",
        "max_attack_ms": 1000,      # can fade in slowly
        "envelope": "sustained",
        "max_spectral_bw_hz": 5000,
    },
    "glass_shatter": {
        "max_centroid_hz": 8000,
        "min_duration": 0.5,
        "max_duration": 5.0,
        "description": "glass breaking",
        "max_attack_ms": 800,       # window glass shatters slower than dropped glass
        "envelope": "sustained",    # crack + sustained tinkle/debris
        "max_spectral_bw_hz": 10000,
    },
    "shimmer": {
        "max_centroid_hz": 9000,
        "min_duration": 0.5,
        "max_duration": 6.0,
        "description": "high sparkle/shimmer",
        "max_attack_ms": 500,       # can fade in
        "envelope": "sustained",
        "max_spectral_bw_hz": 8000,
    },
    "whoosh": {
        "max_centroid_hz": 5000,
        "min_duration": 0.3,
        "max_duration": 3.0,
        "description": "fast air whoosh",
        "max_attack_ms": 300,       # whooshes build then decay
        "envelope": "sustained",    # energy peaks in middle, not front-loaded
        "max_spectral_bw_hz": 6000,
    },
    "camera_shutter": {
        "max_centroid_hz": 6000,
        "min_duration": 0.2,
        "max_duration": 2.0,
        "description": "mechanical camera click/snap",
        "max_attack_ms": 20,        # instant click
        "envelope": "transient",
        "max_spectral_bw_hz": 8000,
    },
    "paper_rustle": {
        "max_centroid_hz": 8000,
        "min_duration": 0.3,
        "max_duration": 4.0,
        "description": "soft paper handling/filing sound",
        "max_attack_ms": 200,
        "envelope": "sustained",
        "max_spectral_bw_hz": 8000,
    },
    "highlighter": {
        "max_centroid_hz": 7000,
        "min_duration": 0.5,
        "max_duration": 4.0,
        "description": "marker drawn across paper",
        "max_attack_ms": 200,
        "envelope": "sustained",
        "max_spectral_bw_hz": 6000,
    },
}

# Map filename prefixes to SFX type keys.
# "body_impact_01.mp3" -> "body_impact", "rumble_03.mp3" -> "rumble"
# Order matters: longer prefixes checked first so "body_impact" beats "impact".
_PREFIX_ORDER = sorted(SFX_SPECS.keys(), key=len, reverse=True)

OLLAMA_BASE = "http://localhost:11434"
VISION_MODEL = "qwen2.5vl:7b"

# ── Helpers ──────────────────────────────────────────────────────────────────


def _sfx_type_for_file(filename: str) -> str | None:
    """Return the SFX_SPECS key that matches this filename, or None."""
    stem = Path(filename).stem.lower()
    for prefix in _PREFIX_ORDER:
        if stem.startswith(prefix):
            return prefix
    return None


def _ollama_available() -> bool:
    """Quick ping to check if Ollama API is reachable."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def _ollama_vision(image_path: Path, prompt: str) -> str | None:
    """Send an image + prompt to the Ollama vision model. Returns text or None."""
    try:
        img_bytes = image_path.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode("ascii")

        payload = json.dumps({
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{OLLAMA_BASE}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as exc:
        return None


# ── Acoustic Profile Analysis ─────────────────────────────────────────────


def _measure_attack_ms(y: np.ndarray, sr: int) -> float:
    """Measure attack time: ms from start to peak amplitude.

    Uses a short-window RMS envelope to find when the signal first reaches
    90% of its peak energy.  A body impact should peak within ~50ms;
    a rumble can take 500ms+.
    """
    hop = max(1, int(sr * 0.005))  # ~5ms hop
    frame_len = hop * 2
    n_frames = max(1, len(y) // hop)
    env = np.array([
        np.sqrt(np.mean(y[i * hop: i * hop + frame_len] ** 2))
        for i in range(n_frames)
    ])
    if env.max() < 1e-6:
        return float(len(y) / sr * 1000)

    threshold = env.max() * 0.9
    peak_indices = np.where(env >= threshold)[0]
    if len(peak_indices) == 0:
        return float(len(y) / sr * 1000)

    return int(peak_indices[0]) * hop / sr * 1000  # ms


def _measure_envelope_type(y: np.ndarray, sr: int) -> str:
    """Classify envelope as 'transient' or 'sustained'.

    Transient: energy in the first 20% of the file is >60% of total energy.
    Sustained: energy is spread more evenly across the file.
    """
    if len(y) < sr * 0.1:
        return "transient"

    split = int(len(y) * 0.2)
    energy_early = float(np.sum(y[:split] ** 2))
    energy_total = float(np.sum(y ** 2))
    if energy_total < 1e-10:
        return "transient"

    return "transient" if energy_early / energy_total > 0.60 else "sustained"


def _measure_spectral_bandwidth(y: np.ndarray, sr: int) -> float:
    """Mean spectral bandwidth in Hz (spread of energy around centroid)."""
    import librosa
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    return float(np.mean(bw))


# ── SFX Validation ───────────────────────────────────────────────────────────


def validate_sfx(sfx_dir: Path) -> list[dict]:
    """
    Validate every SFX file against its spectral spec.

    Returns a list of result dicts, one per file that matches a known SFX type.
    Each dict: {file, sfx_type, status, centroid_hz, duration, rms, issue}
    Status: PASS / WARN / FAIL / CRITICAL
    """
    import librosa

    sfx_dir = Path(sfx_dir)
    if not sfx_dir.is_dir():
        return [{"file": str(sfx_dir), "sfx_type": None, "status": "FAIL",
                 "centroid_hz": 0, "duration": 0, "rms": 0,
                 "issue": "SFX directory does not exist"}]

    results = []
    # Collect audio files, skip .bak and non-audio
    audio_exts = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    files = sorted(
        f for f in sfx_dir.iterdir()
        if f.is_file() and f.suffix.lower() in audio_exts and ".bak" not in f.name
    )

    for fpath in files:
        sfx_type = _sfx_type_for_file(fpath.name)
        if sfx_type is None:
            # Not a recognized SFX type (e.g. typewriter_key) -- skip
            continue

        spec = SFX_SPECS[sfx_type]
        entry = {
            "file": str(fpath),
            "sfx_type": sfx_type,
            "status": "PASS",
            "centroid_hz": 0.0,
            "duration": 0.0,
            "rms": 0.0,
            "issue": None,
        }

        # 1. Load audio
        try:
            y, sr = librosa.load(fpath, sr=None, mono=True)
        except Exception as exc:
            entry["status"] = "FAIL"
            entry["issue"] = f"Cannot load audio: {exc}"
            results.append(entry)
            continue

        duration = float(len(y) / sr)
        entry["duration"] = round(duration, 2)

        # 2. RMS energy -- silence check
        rms = float(np.sqrt(np.mean(y ** 2)))
        entry["rms"] = round(rms, 5)
        if rms < 0.001:
            entry["status"] = "FAIL"
            entry["issue"] = f"Nearly silent (RMS {rms:.5f} < 0.001)"
            results.append(entry)
            continue

        # 2b. Bitrate check — low bitrate files sound buzzy/distorted
        try:
            import subprocess, json as _json
            _probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(fpath)],
                capture_output=True, text=True, timeout=5)
            _br = int(_json.loads(_probe.stdout).get("format", {}).get("bit_rate", 0))
            entry["bitrate_kbps"] = _br // 1000
            if _br > 0 and _br < 96000:  # under 96kbps = garbage quality
                entry["status"] = "FAIL"
                entry["issue"] = f"Bitrate {_br//1000}kbps — below 96kbps minimum (sounds buzzy)"
                results.append(entry)
                continue
        except Exception:
            pass

        # 3. Spectral centroid
        centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        mean_centroid = float(np.mean(centroids))
        entry["centroid_hz"] = round(mean_centroid, 1)

        # 4. Acoustic profile measurements
        attack_ms = _measure_attack_ms(y, sr)
        envelope = _measure_envelope_type(y, sr)
        spectral_bw = _measure_spectral_bandwidth(y, sr)
        entry["attack_ms"] = round(attack_ms, 1)
        entry["envelope"] = envelope
        entry["spectral_bw_hz"] = round(spectral_bw, 1)

        # Collect all issues (worst status wins)
        issues = []

        # 5. Duration checks
        if duration < spec["min_duration"]:
            issues.append(("WARN",
                f"Too short ({duration:.2f}s < {spec['min_duration']}s)"))
        max_dur = spec.get("max_duration")
        if max_dur and duration > max_dur:
            issues.append(("WARN",
                f"Too long ({duration:.2f}s > {max_dur}s for {spec['description']})"))

        # 6. Centroid check
        max_c = spec["max_centroid_hz"]
        if mean_centroid > max_c * 2:
            issues.append(("FAIL",
                f"Centroid {mean_centroid:.0f}Hz WAY above {max_c}Hz (>2x) "
                f"— wrong content for {spec['description']}"))
        elif mean_centroid > max_c:
            issues.append(("WARN",
                f"Centroid {mean_centroid:.0f}Hz above {max_c}Hz limit"))

        # 7. Attack time check
        max_attack = spec.get("max_attack_ms")
        if max_attack and attack_ms > max_attack * 3:
            issues.append(("FAIL",
                f"Attack {attack_ms:.0f}ms — expected <{max_attack}ms for "
                f"{spec['description']} (>3x too slow)"))
        elif max_attack and attack_ms > max_attack:
            issues.append(("WARN",
                f"Attack {attack_ms:.0f}ms — expected <{max_attack}ms"))

        # 8. Envelope shape check
        expected_env = spec.get("envelope")
        if expected_env and envelope != expected_env:
            # Transient sound that's sustained = mushy/wrong; sustained that's
            # transient = clicky/wrong.  Both are WARN (not FAIL) since the
            # envelope classifier is approximate.
            issues.append(("WARN",
                f"Envelope '{envelope}' — expected '{expected_env}' "
                f"for {spec['description']}"))

        # 9. Spectral bandwidth check
        max_bw = spec.get("max_spectral_bw_hz")
        if max_bw and spectral_bw > max_bw * 2:
            issues.append(("WARN",
                f"Spectral bandwidth {spectral_bw:.0f}Hz — expected <{max_bw}Hz"))

        # Determine final status (worst of all issues)
        _severity = {"PASS": 0, "WARN": 1, "FAIL": 2, "CRITICAL": 3}
        final_status = "PASS"
        for sev, _ in issues:
            if _severity.get(sev, 0) > _severity.get(final_status, 0):
                final_status = sev
        entry["status"] = final_status
        entry["issue"] = " | ".join(msg for _, msg in issues) if issues else None

        results.append(entry)

    return results


def validate_sfx_file(path: Path) -> dict:
    """
    Validate a single SFX file against its full acoustic profile spec.

    Returns dict: {status: PASS/WARN/FAIL, detail: str}
    """
    import librosa

    path = Path(path)
    sfx_type = _sfx_type_for_file(path.name)
    if sfx_type is None:
        return {"status": "PASS", "detail": "unknown SFX type — skipping validation"}

    spec = SFX_SPECS[sfx_type]
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
    except Exception as exc:
        return {"status": "FAIL", "detail": f"Cannot load audio: {exc}"}

    duration = float(len(y) / sr)
    rms = float(np.sqrt(np.mean(y ** 2)))
    if rms < 0.001:
        return {"status": "FAIL", "detail": f"Nearly silent (RMS {rms:.5f})"}

    centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    mean_centroid = float(np.mean(centroids))
    attack_ms = _measure_attack_ms(y, sr)
    envelope = _measure_envelope_type(y, sr)

    issues = []
    max_c = spec["max_centroid_hz"]

    # Centroid
    if mean_centroid > max_c * 2:
        issues.append(("FAIL", f"centroid {mean_centroid:.0f}Hz (max {max_c}Hz)"))
    elif mean_centroid > max_c:
        issues.append(("WARN", f"centroid {mean_centroid:.0f}Hz above {max_c}Hz"))

    # Duration
    max_dur = spec.get("max_duration")
    if max_dur and duration > max_dur:
        issues.append(("WARN", f"too long {duration:.1f}s (max {max_dur}s)"))

    # Attack
    max_attack = spec.get("max_attack_ms")
    if max_attack and attack_ms > max_attack * 3:
        issues.append(("FAIL", f"attack {attack_ms:.0f}ms (max {max_attack}ms)"))
    elif max_attack and attack_ms > max_attack:
        issues.append(("WARN", f"attack {attack_ms:.0f}ms (max {max_attack}ms)"))

    # Envelope
    expected_env = spec.get("envelope")
    if expected_env and envelope != expected_env:
        issues.append(("WARN", f"envelope '{envelope}' not '{expected_env}'"))

    if not issues:
        return {"status": "PASS",
                "detail": f"centroid {mean_centroid:.0f}Hz attack {attack_ms:.0f}ms env={envelope}"}

    _sev = {"PASS": 0, "WARN": 1, "FAIL": 2}
    worst = max(issues, key=lambda x: _sev.get(x[0], 0))
    detail = " | ".join(msg for _, msg in issues)
    return {"status": worst[0], "detail": detail}


# ── Image Validation ─────────────────────────────────────────────────────────


def validate_images(
    images_dir: Path,
    storyboard_path: Path | None = None,
    use_ollama: bool = True,
) -> list[dict]:
    """
    Validate images for resolution, corruption, and optionally content/era.

    Returns list of dicts: {file, status, width, height, issue,
                            ollama_description, era_check}
    """
    from PIL import Image

    images_dir = Path(images_dir)
    if not images_dir.is_dir():
        return [{"file": str(images_dir), "status": "FAIL",
                 "width": 0, "height": 0, "issue": "Images directory does not exist",
                 "ollama_description": None, "era_check": None}]

    # Load storyboard reasoning if available, for relevance matching
    storyboard_reasoning = {}
    if storyboard_path and Path(storyboard_path).exists():
        try:
            sb = json.loads(Path(storyboard_path).read_text())
            segments = sb if isinstance(sb, list) else sb.get("segments", sb.get("scenes", []))
            for seg in segments:
                # Map search_query to show description for matching
                q = seg.get("search_query", "")
                desc = seg.get("show", seg.get("reasoning", ""))
                if q:
                    storyboard_reasoning[q.lower()] = desc
        except Exception:
            pass

    ollama_ok = use_ollama and _ollama_available()

    img_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    files = sorted(
        f for f in images_dir.iterdir()
        if f.is_file() and f.suffix.lower() in img_exts
    )

    results = []
    for fpath in files:
        entry = {
            "file": str(fpath),
            "status": "PASS",
            "width": 0,
            "height": 0,
            "issue": None,
            "ollama_description": None,
            "era_check": None,
        }

        # 1. Open with Pillow -- corruption check
        try:
            img = Image.open(fpath)
            img.verify()  # detects truncation / corruption
            # Re-open after verify (verify closes the file)
            img = Image.open(fpath)
            w, h = img.size
            entry["width"] = w
            entry["height"] = h
        except Exception as exc:
            entry["status"] = "FAIL"
            entry["issue"] = f"Corrupt or unreadable image: {exc}"
            results.append(entry)
            continue

        # 2. Resolution check (>= 720p on the shorter dimension)
        min_dim = min(w, h)
        if min_dim < 720:
            entry["status"] = "WARN"
            entry["issue"] = f"Low resolution ({w}x{h}), shorter side {min_dim}px < 720px"

        # 3. Ollama vision checks (optional)
        if ollama_ok:
            # Content description
            desc = _ollama_vision(
                fpath,
                "Describe this image in one sentence. What does it show?"
            )
            if desc:
                entry["ollama_description"] = desc

            # Era check
            era = _ollama_vision(
                fpath,
                "Does this image appear to be from the 1940s-1970s era, or is it "
                "modern? Reply with just 'vintage' or 'modern' and why in 5 words."
            )
            if era:
                entry["era_check"] = era
                era_lower = era.lower()
                if "modern" in era_lower and entry["status"] == "PASS":
                    entry["status"] = "WARN"
                    entry["issue"] = f"Possibly modern image: {era}"

        results.append(entry)

    return results


# ── Full Validation ──────────────────────────────────────────────────────────


def validate_all(
    topic: str,
    sfx_dir: Path,
    images_dir: Path,
    storyboard_path: Path | None = None,
    use_ollama: bool = True,
) -> dict:
    """
    Run all validations. Returns summary dict:
        sfx:     list of per-file SFX results
        images:  list of per-file image results
        summary: {sfx_pass, sfx_warn, sfx_fail, sfx_critical,
                  img_pass, img_warn, img_fail,
                  has_critical, has_fail}
    """
    sfx_results = validate_sfx(sfx_dir)
    img_results = validate_images(images_dir, storyboard_path, use_ollama=use_ollama)

    def _count(results, status):
        return sum(1 for r in results if r["status"] == status)

    summary = {
        "topic": topic,
        "sfx_total": len(sfx_results),
        "sfx_pass": _count(sfx_results, "PASS"),
        "sfx_warn": _count(sfx_results, "WARN"),
        "sfx_fail": _count(sfx_results, "FAIL"),
        "sfx_critical": _count(sfx_results, "CRITICAL"),
        "img_total": len(img_results),
        "img_pass": _count(img_results, "PASS"),
        "img_warn": _count(img_results, "WARN"),
        "img_fail": _count(img_results, "FAIL"),
        "has_critical": _count(sfx_results, "CRITICAL") > 0,
        "has_fail": (
            _count(sfx_results, "FAIL") + _count(img_results, "FAIL") > 0
        ),
    }

    return {"sfx": sfx_results, "images": img_results, "summary": summary}


# ── CLI Report ───────────────────────────────────────────────────────────────


def _status_marker(status: str) -> str:
    markers = {
        "PASS": "  OK ",
        "WARN": " WARN",
        "FAIL": " FAIL",
        "CRITICAL": " CRIT",
    }
    return markers.get(status, "  ?  ")


def print_report(result: dict) -> None:
    """Print a human-readable validation report."""
    summary = result["summary"]
    topic = summary["topic"]

    print(f"\n{'=' * 72}")
    print(f"  ASSET VALIDATION REPORT -- {topic}")
    print(f"{'=' * 72}")

    # ── SFX section ──
    print(f"\n  SFX FILES  ({summary['sfx_total']} checked)")
    print(f"  {'-' * 50}")
    for r in result["sfx"]:
        name = Path(r["file"]).name
        mark = _status_marker(r["status"])
        line = f"  [{mark}] {name:<30s}"
        if r["centroid_hz"]:
            line += f"  centroid={r['centroid_hz']:>6.0f}Hz"
        if r["duration"]:
            line += f"  dur={r['duration']:.1f}s"
        if r.get("attack_ms") is not None:
            line += f"  atk={r['attack_ms']:.0f}ms"
        if r.get("envelope"):
            line += f"  env={r['envelope']}"
        print(line)
        if r["issue"]:
            print(f"          -> {r['issue']}")

    sfx_ok = summary["sfx_pass"]
    sfx_tot = summary["sfx_total"]
    print(f"\n  SFX: {sfx_ok}/{sfx_tot} PASS, "
          f"{summary['sfx_warn']} WARN, "
          f"{summary['sfx_fail']} FAIL, "
          f"{summary['sfx_critical']} CRITICAL")

    # ── Images section ──
    print(f"\n  IMAGE FILES  ({summary['img_total']} checked)")
    print(f"  {'-' * 50}")
    for r in result["images"]:
        name = Path(r["file"]).name
        mark = _status_marker(r["status"])
        dims = f"{r['width']}x{r['height']}" if r["width"] else "N/A"
        line = f"  [{mark}] {name:<40s} {dims:>10s}"
        print(line)
        if r["issue"]:
            print(f"          -> {r['issue']}")
        if r.get("ollama_description"):
            desc = r["ollama_description"][:80]
            print(f"          >> {desc}")
        if r.get("era_check"):
            print(f"          era: {r['era_check']}")

    img_ok = summary["img_pass"]
    img_tot = summary["img_total"]
    print(f"\n  IMAGES: {img_ok}/{img_tot} PASS, "
          f"{summary['img_warn']} WARN, "
          f"{summary['img_fail']} FAIL")

    # ── Verdict ──
    print(f"\n{'=' * 72}")
    if summary["has_critical"]:
        print("  VERDICT: CRITICAL issues found -- some SFX files are wrong content")
    elif summary["has_fail"]:
        print("  VERDICT: FAIL -- corrupt or invalid assets detected")
    elif summary["sfx_warn"] + summary["img_warn"] > 0:
        print("  VERDICT: PASS with WARNINGS -- review flagged items")
    else:
        print("  VERDICT: ALL PASS")
    print(f"{'=' * 72}\n")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Validate SFX audio and footage images before render."
    )
    parser.add_argument(
        "--topic", required=True,
        help="Topic slug (e.g. frank_olson_cia_scientist_lsd_murder_cover_up)",
    )
    parser.add_argument(
        "--sfx-dir", default=None,
        help="Override SFX directory (default: assets/sfx/)",
    )
    parser.add_argument(
        "--images-dir", default=None,
        help="Override images directory",
    )
    parser.add_argument(
        "--storyboard", default=None,
        help="Override storyboard path",
    )
    parser.add_argument(
        "--no-ollama", action="store_true",
        help="Skip all Ollama vision checks (resolution/corruption only)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw JSON instead of formatted report",
    )
    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    sfx_dir = Path(args.sfx_dir) if args.sfx_dir else project_root / "assets" / "sfx"
    images_dir = (
        Path(args.images_dir) if args.images_dir
        else project_root / "footage" / "fern_clone" / args.topic / "images"
    )
    storyboard_path = (
        Path(args.storyboard) if args.storyboard
        else project_root / "storyboards" / f"{args.topic}.json"
    )

    result = validate_all(
        topic=args.topic,
        sfx_dir=sfx_dir,
        images_dir=images_dir,
        storyboard_path=storyboard_path,
        use_ollama=not args.no_ollama,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_report(result)

    # Exit code 1 if any CRITICAL or FAIL
    if result["summary"]["has_critical"] or result["summary"]["has_fail"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
