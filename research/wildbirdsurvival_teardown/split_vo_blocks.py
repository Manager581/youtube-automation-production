#!/usr/bin/env python3
"""Verify the one-pass EP02 VO against the locked script and split it into blocks.

Silence-threshold splitting does NOT work on this take: silences form a
continuous ramp from 1.0 s down to 0.30 s, so paragraph breaks and ordinary
sentence periods overlap and no cutoff separates them. Instead we align the
known script tokens to whisper's word-level timestamps with difflib, which is
content-aware, then cut in the middle of the gap between adjacent blocks.

Doubles as the whisper verification: a block whose tokens do not align is a
suspected misread and is reported.
"""
import json
import re
import subprocess
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BLOCKS = ROOT / "ep02_vo_blocks.json"
TRANSCRIPT = ROOT / "ep02_vo_transcript_words.json"
SRC = REPO / "audio/vampire_finch/ep02_vo_full_sp95_s74_sb75_m2.mp3"
OUTDIR = REPO / "audio/vampire_finch/blocks"
MANIFEST = ROOT / "ep02_vo_block_manifest.json"

# whisper writes numbers as digits; the script spells them out
NUMWORDS = {"20": "twenty", "10": "ten", "2": "two"}


def norm(tok: str):
    """Lowercase, split hyphens, drop punctuation -> list of comparable tokens.

    Accents are FOLDED (Galapagos), not stripped -- dropping the char outright
    turned "Galapagos" into "galpagos" and produced a phantom mismatch against a
    line the voice actually read correctly.
    """
    tok = tok.replace("’", "'").replace("—", " ").replace("-", " ")
    tok = unicodedata.normalize("NFKD", tok)
    tok = "".join(c for c in tok if not unicodedata.combining(c))
    out = []
    for piece in tok.split():
        piece = re.sub(r"[^a-z0-9']", "", piece.lower()).strip("'")
        if not piece:
            continue
        out.append(NUMWORDS.get(piece, piece))
    return out


def main():
    blocks = json.loads(BLOCKS.read_text(encoding="utf-8"))["blocks_detail"]
    words = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))["words"]

    # flat script tokens, remembering which block each came from
    script_toks, owner = [], []
    for bi, b in enumerate(blocks):
        for t in norm(b["text"]):
            script_toks.append(t)
            owner.append(bi)

    # flat recognised tokens, remembering the source word index for timing
    rec_toks, rec_src = [], []
    for wi, w in enumerate(words):
        for t in norm(w["w"]):
            rec_toks.append(t)
            rec_src.append(wi)

    sm = SequenceMatcher(a=script_toks, b=rec_toks, autojunk=False)
    # script token index -> recognised word index
    mapping = {}
    for a0, b0, size in sm.get_matching_blocks():
        for k in range(size):
            mapping[a0 + k] = rec_src[b0 + k]

    # per-block span + match ratio
    spans = []
    for bi, b in enumerate(blocks):
        idxs = [i for i, o in enumerate(owner) if o == bi]
        hit = [mapping[i] for i in idxs if i in mapping]
        total = len(idxs)
        ratio = len(hit) / total if total else 0.0
        if hit:
            start = words[min(hit)]["s"]
            end = words[max(hit)]["e"]
        else:
            start = end = None
        spans.append({"block": bi, "timecode": b["timecode"], "t": b["t"],
                      "text": b["text"], "words": total,
                      "matched": len(hit), "ratio": round(ratio, 3),
                      "raw_start": start, "raw_end": end})

    # --- verification report -------------------------------------------------
    bad = [s for s in spans if s["ratio"] < 0.85]
    print(f"blocks: {len(spans)}   fully-aligned: "
          f"{sum(1 for s in spans if s['ratio'] == 1.0)}")
    print(f"overall token match: "
          f"{sum(s['matched'] for s in spans)}/{sum(s['words'] for s in spans)}")
    if bad:
        print("\n!! SUSPECT BLOCKS (ratio < 0.85) - read these before accepting:")
        for s in bad:
            print(f"   [{s['timecode']}] ratio {s['ratio']} :: {s['text'][:70]}")
    else:
        print("no suspect blocks - every block aligned to the script")

    # ordering sanity: spans must be monotonic
    for i in range(1, len(spans)):
        if spans[i]["raw_start"] is None or spans[i - 1]["raw_end"] is None:
            continue
        if spans[i]["raw_start"] < spans[i - 1]["raw_end"]:
            print(f"!! ORDER VIOLATION at block {i} ({spans[i]['timecode']})")

    if bad:
        print("\nrefusing to split until suspect blocks are reviewed")
        return 1

    # --- cut points: midpoint of the gap between adjacent blocks -------------
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(SRC)], capture_output=True, text=True
    ).stdout.strip())

    cuts = []
    for i, s in enumerate(spans):
        start = 0.0 if i == 0 else (spans[i - 1]["raw_end"] + s["raw_start"]) / 2
        end = dur if i == len(spans) - 1 else (s["raw_end"] + spans[i + 1]["raw_start"]) / 2
        cuts.append((round(start, 3), round(end, 3)))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, (s, (a, b)) in enumerate(zip(spans, cuts)):
        name = f"vo_{i:02d}_{s['timecode'].replace(':', 'm')}.mp3"
        out = OUTDIR / name
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(SRC), "-ss", f"{a}", "-to", f"{b}",
             "-c", "copy", str(out)], check=True)
        manifest.append({
            "index": i, "file": f"audio/vampire_finch/blocks/{name}",
            "drop_at_s": s["t"], "timecode": s["timecode"],
            "src_in": a, "src_out": b, "duration": round(b - a, 3),
            "text": s["text"], "match_ratio": s["ratio"],
        })

    MANIFEST.write_text(json.dumps({
        "source": "audio/vampire_finch/ep02_vo_full_sp95_s74_sb75_m2.mp3",
        "speed": 0.95, "measured_wpm": 155.2, "source_duration_s": round(dur, 3),
        "blocks": len(manifest), "segments": manifest,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {len(manifest)} segments -> {OUTDIR.relative_to(REPO)}")
    print(f"manifest -> {MANIFEST.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
