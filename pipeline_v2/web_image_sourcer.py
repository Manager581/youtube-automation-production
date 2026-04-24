#!/usr/bin/env python3
"""
web_image_sourcer.py — Per-beat image sourcing with Claude-vision verification.

Sources (all free, no paid APIs):
  1. DuckDuckGo Images — aggregates Google/Bing/Wikimedia/web results (primary)
  2. Wikimedia Commons — direct API (fallback)

Removed (project rules):
  - Pexels (generic stock photos, not documentary-appropriate)
  - Pixabay (same)
  - Hardcoded keyword→photo-ID maps (fake search)

Every downloaded candidate is checked with Claude vision against the beat's
intent. Mismatches are flagged so the director can re-query or fall back.

Usage:
    # Single query (smoke test)
    python -m pipeline_v2.web_image_sourcer --query "Yesenia Guitron Wells Fargo" --output images/

    # Source images for specific beats in a paper edit
    python -m pipeline_v2.web_image_sourcer \\
        --paper-edit storyboards/breaking_law_paper_edit_v10.json \\
        --beat beat_0023 --beat beat_0033 \\
        --output images/breaking_law_replacements/
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pipeline_v2.llm import query_claude_vision  # noqa: E402

# Reuse the proven DDG + Wikimedia code from scripts/source_images_free.py
# rather than re-implementing (Rule 1: no parallel solutions)
from source_images_free import (  # noqa: E402
    download_from_ddg,
    download_from_wikimedia,
    MIN_SIZE_BYTES,
)
from pipeline_v2.llm import query_claude  # noqa: E402


# ── Sourcing ────────────────────────────────────────────────────────────────

def source_candidates(query, output_dir, max_candidates=5):
    """Fetch up to `max_candidates` image candidates for a query.

    Tries DDG first (aggregates Google/Bing/Wikimedia). Falls back to direct
    Wikimedia API if DDG returns nothing.

    Returns list of {path: Path, source: str, title: str}.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = re.sub(r'[^a-zA-Z0-9]+', '_', query)[:40].strip('_') or "query"

    candidates = []

    # Primary: DDG
    ddg_paths = download_from_ddg(
        query, output_dir, safe_label,
        count=max_candidates * 3,
        target_saves=max_candidates,
    )
    for p in ddg_paths:
        candidates.append({"path": Path(p), "source": "ddg", "title": ""})

    # Fallback: direct Wikimedia
    if len(candidates) < max_candidates:
        wiki_needed = max_candidates - len(candidates)
        wiki_paths = download_from_wikimedia(
            query, output_dir, safe_label,
            count=wiki_needed,
        )
        for p in wiki_paths:
            candidates.append({"path": Path(p), "source": "wikimedia", "title": ""})

    return candidates


# ── Vision verification ─────────────────────────────────────────────────────

def verify_image(image_path, beat_context):
    """Claude-vision check: does this image fit the beat?

    `beat_context` is free text: narration, editorial intent, subject keywords.
    Returns (bool_ok, reason_text).
    """
    path = Path(image_path)
    if not path.exists() or path.stat().st_size < MIN_SIZE_BYTES:
        return False, f"File missing or too small ({path})"

    prompt = (
        "You are verifying an image for a documentary video.\n\n"
        f"The beat this image will illustrate:\n---\n{beat_context}\n---\n\n"
        "Examine the image. Does it visually support this beat for a viewer?\n"
        "Reject if: the image is an ad, sponsor logo, YouTube comment screenshot, "
        "subscribe/reaction overlay, unrelated stock footage, or wrong subject.\n"
        "Accept if: the image shows the people, places, events, documents, or "
        "concrete visuals the narration refers to.\n\n"
        "Reply with exactly one line: `YES: <reason>` or `NO: <reason>`."
    )

    response = query_claude_vision(prompt, str(path)) or ""
    verdict = response.strip().split("\n", 1)[0]
    ok = verdict.lower().startswith("yes")
    return ok, verdict


# ── Per-beat + per-paper-edit ────────────────────────────────────────────────

def build_query_for_beat(beat):
    """Ask Claude to craft a focused image-search query from the beat.

    Raw narration and director notes contain editorial language ("cut to",
    "establish") and ambiguous names ("Ford" → Doug Ford vs Henry Ford vs
    Ford Motor Co). A short Claude pass produces a query with concrete nouns,
    proper entities, and time-period context that DDG can actually match.
    """
    narration = (beat.get("text") or "").strip()
    narration = re.sub(r"\[[^\]]+\]", " ", narration)
    narration = re.sub(r"\s+", " ", narration)[:400]
    why = (beat.get("why") or "").strip()[:300]
    chapter = (beat.get("chapter") or "").strip()

    prompt = (
        "You are picking a documentary B-roll image via Google/DDG search.\n"
        "Write ONE image-search query of 3–8 words.\n"
        "Rules:\n"
        "  • Use proper nouns (people, companies, places, events).\n"
        "  • Add the year or era when relevant (e.g. 'Ford Pinto 1977').\n"
        "  • Disambiguate common names ('Ford Motor Company', not just 'Ford').\n"
        "  • NO editorial/cinematography terms (cut, freeze, establish, hold).\n"
        "  • NO quotes, NO punctuation, NO explanation — just the query words.\n\n"
        f"Narration: {narration}\n"
        f"Director note: {why}\n"
        f"Chapter: {chapter}\n\n"
        "Query:"
    )
    response = query_claude(prompt, max_tokens=50, timeout=45) or ""
    # Strip quotes, fencing, trailing punctuation
    q = response.strip().strip('"').strip("'").strip('`').strip()
    q = q.split("\n")[0].strip()
    q = re.sub(r'^(query|search):\s*', '', q, flags=re.I)
    q = q[:120]
    if not q:
        # Fallback: narration minus brackets
        q = narration[:100].rstrip('.').rstrip(',')
    return q


def source_for_beat(beat, output_dir, max_candidates=5, verify=True):
    """Source + verify images for one beat. Returns summary dict."""
    query = build_query_for_beat(beat)
    if not query:
        return {"beat_id": beat.get("beat_id"), "query": "", "candidates": []}

    bid = beat.get("beat_id", "beat_unknown")
    beat_dir = Path(output_dir) / bid
    candidates = source_candidates(query, beat_dir, max_candidates=max_candidates)

    beat_context = (
        f"Narration: {beat.get('text', '')}\n"
        f"Director's intent: {beat.get('why', '')}\n"
        f"Chapter: {beat.get('chapter', '')}"
    )

    results = []
    for c in candidates:
        if verify:
            ok, reason = verify_image(c["path"], beat_context)
        else:
            ok, reason = True, "(verification skipped)"
        results.append({
            "file": str(c["path"]),
            "source": c["source"],
            "verified": ok,
            "reason": reason,
        })

    return {
        "beat_id": bid,
        "query": query,
        "candidates": results,
    }


def source_for_paper_edit(paper_edit_path, output_dir, beat_ids=None,
                          max_candidates=5, verify=True):
    """Source images for specific beats (or all) in a paper edit.

    Writes a summary JSON report to <output_dir>/_source_report.json.
    """
    with open(paper_edit_path) as f:
        pe = json.load(f)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    beat_ids = set(beat_ids) if beat_ids else None
    summary = []

    for beat in pe.get("beats", []):
        bid = beat.get("beat_id", "")
        if beat_ids and bid not in beat_ids:
            continue
        result = source_for_beat(beat, output_dir,
                                 max_candidates=max_candidates,
                                 verify=verify)
        summary.append(result)
        verified = sum(1 for c in result["candidates"] if c["verified"])
        print(f"  [{bid}] '{result['query'][:60]}' → {verified}/{len(result['candidates'])} verified")

    report_path = output_dir / "_source_report.json"
    report_path.write_text(json.dumps(summary, indent=2))
    return summary, report_path


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Web image sourcer — DDG + Wikimedia + Claude-vision verification",
    )
    p.add_argument('--query', help='Single search query (smoke test)')
    p.add_argument('--paper-edit', help='Paper edit JSON; source for selected beats')
    p.add_argument('--beat', action='append', default=[],
                   help='Beat ID to process (repeatable). If omitted, all beats.')
    p.add_argument('--output', default='images/', help='Output directory')
    p.add_argument('--max', type=int, default=5, help='Max candidates per query')
    p.add_argument('--no-verify', action='store_true', help='Skip vision verification')
    args = p.parse_args()

    if args.paper_edit:
        summary, report_path = source_for_paper_edit(
            args.paper_edit, args.output,
            beat_ids=args.beat or None,
            max_candidates=args.max,
            verify=not args.no_verify,
        )
        verified = sum(1 for s in summary for c in s["candidates"] if c["verified"])
        total = sum(len(s["candidates"]) for s in summary)
        print(f"\nBeats processed: {len(summary)}")
        print(f"Candidates verified: {verified}/{total}")
        print(f"Report: {report_path}")
        return 0

    if args.query:
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        candidates = source_candidates(args.query, out, max_candidates=args.max)
        print(f"\n{len(candidates)} candidates downloaded for '{args.query}':")
        for c in candidates:
            if args.no_verify:
                print(f"  · {c['path'].name} ({c['source']})")
                continue
            ok, reason = verify_image(c["path"], args.query)
            icon = '✅' if ok else '❌'
            print(f"  {icon} {c['path'].name} ({c['source']}): {reason[:100]}")
        return 0

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
