#!/usr/bin/env python3
"""
say_narrate.py — PLACEHOLDER narrator using macOS `say`.

TEMPORARY stand-in for pipeline/voice_generator.py (F5-TTS cloned voice), used
only while the iCloud-evicted venv is being re-materialized. Produces narration
audio + a narration_manifest.json in the SAME schema voice_generator emits, so
build_dunk_paper_edit.py + the FFmpeg renderer work unchanged. Swap back to the
cloned voice by re-running voice_generator.py once F5-TTS imports cleanly.

Usage:
  python scripts/say_narrate.py --script scripts/dunkleosteus.txt \
    --out audio/dunkleosteus/narration.wav --voice Daniel --rate 168
"""
import argparse, json, re, subprocess, tempfile, wave
from pathlib import Path

PAUSE = {"[BEAT]": 0.30, "[BREATH]": 0.15}


def wav_dur(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="Daniel")
    ap.add_argument("--rate", type=int, default=168)
    ap.add_argument("--sr", type=int, default=44100)
    args = ap.parse_args()

    raw = Path(args.script).read_text()
    raw = re.sub(r"\[VOICE:[a-z]+\]", "", raw)            # drop register tags
    # tokenize into speech text and explicit pauses
    tokens = re.split(r"(\[PAUSE:[0-9.]+\]|\[BEAT\]|\[BREATH\])", raw)

    tmp = Path(tempfile.mkdtemp())
    parts, manifest = [], {"segments": [], "total_duration_sec": 0.0, "out": args.out}
    cursor, sidx = 0.0, 0

    def add_silence(dur):
        nonlocal cursor
        sil = tmp / f"sil_{len(parts):03d}.wav"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        f"anullsrc=r={args.sr}:cl=mono", "-t", f"{dur:.3f}",
                        str(sil)], capture_output=True)
        parts.append(sil)
        manifest["segments"].append({"type": "pause", "start_sec": round(cursor, 3),
                                     "duration_sec": round(dur, 3)})
        cursor += dur

    for tok in tokens:
        if not tok or not tok.strip():
            continue
        m = re.match(r"\[PAUSE:([0-9.]+)\]", tok)
        if m:
            add_silence(float(m.group(1))); continue
        if tok in PAUSE:
            add_silence(PAUSE[tok]); continue
        # speech: split into sentences for finer beat granularity
        sentences = re.split(r"(?<=[.!?])\s+", tok.strip())
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 2:
                continue
            sidx += 1
            aiff = tmp / f"s_{sidx:03d}.aiff"
            wav = tmp / f"s_{sidx:03d}.wav"
            subprocess.run(["say", "-v", args.voice, "-r", str(args.rate),
                            "-o", str(aiff), sent], check=True)
            subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", str(args.sr),
                            "-ac", "1", str(wav)], capture_output=True)
            dur = wav_dur(wav)
            parts.append(wav)
            manifest["segments"].append({
                "type": "speech", "index": sidx,
                "start_sec": round(cursor, 3), "duration_sec": round(dur, 3),
                "end_sec": round(cursor + dur, 3),
                "word_count": len(sent.split()), "voice_register": "placeholder",
                "text": sent,
            })
            cursor += dur

    # concat all parts
    listf = tmp / "list.txt"
    listf.write_text("".join(f"file '{p}'\n" for p in parts))
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listf),
                    "-ar", str(args.sr), "-ac", "1", str(out)], capture_output=True)

    manifest["total_duration_sec"] = round(cursor, 3)
    sp = [s for s in manifest["segments"] if s["type"] == "speech"]
    manifest["word_count_total"] = sum(s["word_count"] for s in sp)
    manifest["avg_wpm"] = round(manifest["word_count_total"] / (cursor / 60), 1) if cursor else 0
    mpath = out.parent / (out.stem + "_manifest.json")
    mpath.write_text(json.dumps(manifest, indent=2))
    print(f"PLACEHOLDER narration: {cursor:.1f}s, {len(sp)} segments, "
          f"{manifest['avg_wpm']} WPM -> {out}")
    print(f"manifest -> {mpath}")


if __name__ == "__main__":
    main()
