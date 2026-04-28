#!/usr/bin/env python3
"""Vision-label every still at ingest. Writes .content.json sidecar per image.

This solves the filename-lies problem upstream. After this runs, downstream
pipeline stages can trust the content metadata instead of the filename.

Idempotent: skips if sidecar exists (unless --force).
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from pipeline_v2.llm import query_claude_vision  # noqa: E402

STILLS_DIR = PROJECT_ROOT / "footage" / "breaking_law" / "stills"

PROMPT = """Look at this image and return ONLY a single JSON object (no prose, no code fence, no explanation).

Fields:
- subject: one concrete sentence describing what is visibly in the image.
- entities: array of proper nouns shown or strongly implied (people, places, companies, events, documents, products). Empty array if none.
- is_ad: true if this frame is a sponsor or commercial (M&M's, State Farm, any brand logo dominating the frame).
- is_reaction_shot: true if it shows podcast hosts at mics, YouTube reactors, or any "creator talking to camera" framing that is NOT the documentary subject itself.
- is_title_card: true if the frame is mostly black/solid background with overlaid text as the primary content.
- is_comment_screenshot: true if a YouTube, Reddit, or other social-media comment UI is visible.
- has_watermark: true if ANY watermark, news-network bug, or third-party logo is visible (KINEMASTER, CapCut, Canva, iStock, Shutterstock, Getty, Adobe Stock, AP, AFP, Reuters, CNN, NBC, FOX, ABC, BBC, etc.). Lower-third name graphics from a different network are watermarks too.
- is_ai_generated: true if the image is obviously AI-generated stock (telltale rendering artifacts, uncanny textures, non-photographic lighting).
- usable_for_documentary: MUST BE FALSE if has_watermark, is_ad, is_reaction_shot, is_comment_screenshot, or is_ai_generated is true — there are no exceptions. Documentary footage cannot ship with someone else's brand on it. True only if the image is clean (no overlays/watermarks) AND directly relevant to its ostensible subject.
- notes: one short sentence explaining the usability judgment.

Return the JSON object only."""


def extract_json(raw: str) -> dict:
    """Extract JSON from CLI response, tolerating code fences."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        # Strip opening fence (with optional "json" tag)
        raw = raw.split("```", 2)[1] if raw.count("```") >= 1 else raw
        if raw.lower().startswith("json"):
            raw = raw[4:]
        # Strip closing fence if present
        if "```" in raw:
            raw = raw.split("```", 1)[0]
        raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last-ditch: find first '{' and last '}'
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {"_error": "bad_json", "_raw": raw[:500]}


def _enforce_disqualifiers(data: dict) -> dict:
    """Defensive: force usable_for_documentary=false if any disqualifying flag
    is true, regardless of what the LLM wrote. Documentary can't ship with
    third-party watermarks, ads, reaction shots, AI slop, or comment UI.
    """
    if "_error" in data:
        return data
    disq_flags = ("has_watermark", "is_ad", "is_reaction_shot",
                  "is_comment_screenshot", "is_ai_generated")
    if any(data.get(f) for f in disq_flags):
        triggered = [f for f in disq_flags if data.get(f)]
        if data.get("usable_for_documentary"):
            data["usable_for_documentary"] = False
            existing_notes = data.get("notes", "")
            data["notes"] = f"AUTO-REJECTED ({', '.join(triggered)}): {existing_notes}".strip(": ")
    return data


def label_still(image_path: Path, force: bool = False) -> dict:
    sidecar = image_path.with_suffix(image_path.suffix + ".content.json")
    if sidecar.exists() and not force:
        # Apply enforcement to existing sidecars too — old sidecars predate the rule
        existing = json.loads(sidecar.read_text())
        enforced = _enforce_disqualifiers(existing)
        if enforced != existing:
            sidecar.write_text(json.dumps(enforced, indent=2))
        return enforced

    raw = query_claude_vision(PROMPT, str(image_path), timeout=90)
    if not raw:
        return {"_error": "empty_response"}

    data = _enforce_disqualifiers(extract_json(raw))
    sidecar.write_text(json.dumps(data, indent=2))
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dir', default=str(STILLS_DIR), help='Directory of stills to label')
    p.add_argument('--force', action='store_true', help='Re-label even if sidecar exists')
    p.add_argument('--limit', type=int, help='Process only first N (for testing)')
    p.add_argument('--only', help='Substring filter for filenames (for testing specific cases)')
    args = p.parse_args()

    stills_dir = Path(args.dir)
    files = sorted(list(stills_dir.glob('*.jpg')) + list(stills_dir.glob('*.png')))
    if args.only:
        files = [f for f in files if args.only in f.name]
    if args.limit:
        files = files[:args.limit]

    print(f"Processing {len(files)} files from {stills_dir}")
    stats = {'labeled': 0, 'skipped': 0, 'errors': 0,
             'unusable': 0, 'ads': 0, 'reactions': 0, 'title_cards': 0,
             'comments': 0, 'watermarked': 0, 'ai_generated': 0}

    for i, img in enumerate(files):
        sidecar = img.with_suffix(img.suffix + ".content.json")
        if sidecar.exists() and not args.force:
            stats['skipped'] += 1
            continue

        result = label_still(img, force=args.force)
        if '_error' in result:
            stats['errors'] += 1
            print(f"  [{i+1}/{len(files)}] ERR  {img.name}: {result.get('_error')}")
            continue

        stats['labeled'] += 1
        if result.get('is_ad'): stats['ads'] += 1
        if result.get('is_reaction_shot'): stats['reactions'] += 1
        if result.get('is_title_card'): stats['title_cards'] += 1
        if result.get('is_comment_screenshot'): stats['comments'] += 1
        if result.get('has_watermark'): stats['watermarked'] += 1
        if result.get('is_ai_generated'): stats['ai_generated'] += 1
        if not result.get('usable_for_documentary', True):
            stats['unusable'] += 1

        flag = '❌' if not result.get('usable_for_documentary', True) else '✅'
        subject = (result.get('subject') or '')[:80]
        print(f"  [{i+1}/{len(files)}] {flag} {img.name}")
        print(f"        {subject}")

    print(f"\n── Stats ──")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
