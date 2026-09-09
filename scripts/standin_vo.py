#!/usr/bin/env python3
"""standin_vo.py — $0 PLACEHOLDER voice for lines that have not been bought yet, so a stand-in render can be MEASURED.

Why this exists: the first-minute stand-in render proves structure, but without VO the watch gate cannot measure
speech_frac, dead_air or cut_on_word_rate — the three numbers that describe what actually went wrong with v3. Six lines
have real takes; the rest are unvoiced until the owner approves the batch. This fills the gap locally, for nothing.

Engine: mlx-community/Chatterbox-TTS-fp16 through scripts/tts_lab_mlx_gen.py (MIT weights, the repo's own shootout winner).
Prototype 2026-09-09: 52 chars in 4.3 s = 12.1 chars/s against the MEASURED ElevenLabs 15.8, so every line is tempo-
normalised to its budgeted duration (chars / lane.speech.chars_per_sec). The normalisation belongs on this placeholder
audio and NEVER on the picture — retime_to_vo refuses picture warps beyond 1.25x for good reason.

THIS AUDIO IS NOT DELIVERABLE. It is not ORB, PIP or GRUFF. Every file is written under a `standin/` directory and the
manifest it writes carries standin: true, so nothing downstream can mistake it for a bought take.

  standin_vo.py --lines LINES.json --lane lane.json --out DIR [--only-missing] [--ref assets/voice/voice_neutral_ref_short.wav]
"""
import argparse, json, os, re, subprocess, sys

MLX = os.path.expanduser("~/tts-lab/mlx/venv/bin/python")
MODEL = "mlx-community/Chatterbox-TTS-fp16"


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True)
    ap.add_argument("--lane", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", default=[], help="reference voice; repeatable — retries rotate through them, since re-running the same ref reproduces the same stumble")
    ap.add_argument("--takes", action="append", default=[], help="dirs holding REAL takes; a line found here is skipped")
    ap.add_argument("--no-normalise", action="store_true")
    ap.add_argument("--max-ratio", type=float, default=2.0, help="refuse a raw take longer than this multiple of its budgeted duration")
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--no-qc", action="store_true", help="skip the whisper read-back of each placeholder line")
    ap.add_argument("--qc-model", default="base")
    ap.add_argument("--max-excess-s", type=float, default=1.25, help="absolute seconds a raw take may exceed its target before the ratio rule bites; separates fixed TTS overhead on short lines from a looping take")
    a = ap.parse_args()
    if not a.ref: a.ref = ["assets/voice/voice_neutral_ref_short.wav", "assets/voice/voice_energized_ref_short.wav", "assets/voice/voice_neutral_ref.wav"]

    if not os.path.exists(MLX):
        print(f"standin_vo REFUSED: local TTS venv missing at {MLX} — no placeholder route, so the stand-in render "
              f"cannot measure speech; say so rather than rendering a silent one."); return 2
    cps = (json.load(open(a.lane)).get("speech") or {}).get("chars_per_sec")
    if not cps:
        print("standin_vo REFUSED: lane.speech.chars_per_sec is not measured; a guessed pace makes the timing proof worthless."); return 2

    M = json.load(open(a.lines))
    os.makedirs(a.out, exist_ok=True)
    rows, skipped = [], []
    for L in M["lines"]:
        # ONLY reuse_audio_from may point at a real take. Line ids are positional (L01, L02, ...) and collide across
        # script versions, so falling back to the id would quietly play v1's L01 over v4's first line.
        real = None
        if L.get("reuse_audio_from"):
            for d in a.takes:
                for ext in (".mp3", ".wav"):
                    p = os.path.join(d, L["reuse_audio_from"] + ext)
                    if os.path.exists(p): real = p; break
                if real: break
            if not real:
                print(f"standin_vo REFUSED: {L['id']} claims reuse_audio_from={L['reuse_audio_from']!r} but no such take "
                      f"exists in {a.takes} — a reuse that cannot be located is a silent hole in the render."); return 1
        if real:
            skipped.append(L["id"]); rows.append({**L, "standin": False, "file": real, "target_s": round(L["chars"] / cps, 2)})
            continue
        txt = os.path.join(a.out, L["id"] + ".txt"); open(txt, "w").write(L["text"] + "\n")
        raw = os.path.join(a.out, L["id"] + "_raw.wav"); final = os.path.join(a.out, L["id"] + ".wav")
        target = L["chars"] / cps
        # Chatterbox sometimes rambles or loops on a short line (one 44-char line came back at 28.7 s). Squeezing that to
        # length at 10x is noise, not a timing stand-in, and it would drag the word onsets the whole edit is built on.
        # Retry, then refuse rather than pretend.
        got = None
        for attempt in range(a.retries + 1):
            ref = a.ref[attempt % len(a.ref)]
            r = subprocess.run([MLX, "scripts/tts_lab_mlx_gen.py", "--model", MODEL, "--text", txt, "--ref", ref, "--out", raw],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(raw):
                print(f"  FAIL {L['id']}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'no output'}"); return 1
            # Trim the model's lead-in/trailing silence before judging it: a 0.9 s line reads as "3.8x too long"
            # when most of the file is breath, and that is a fixed overhead, not a rambling take.
            trimmed = raw + ".trim.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05:"
                            "stop_periods=-1:stop_threshold=-45dB:stop_silence=0.05", trimmed], check=False)
            if os.path.exists(trimmed) and dur(trimmed) > 0.05: os.replace(trimmed, raw)
            elif os.path.exists(trimmed): os.remove(trimmed)
            got = dur(raw)
            # Two ways to be wrong, and only one of them is the model looping: a HIGH RATIO on a very short line is
            # fixed overhead (L06 "Rapport: none." wants 0.89 s and no TTS starts that fast), while a large ABSOLUTE
            # excess is a take that said the line twice (one 44-char line came back 25.9 s long). Refuse only both.
            if got / target <= a.max_ratio or (got - target) <= a.max_excess_s: break
            print(f"  retry {L['id']}: raw {got:.2f}s is {got/target:.1f}x its {target:.2f}s target (cap {a.max_ratio}x) with ref {os.path.basename(ref)} — the model rambled; rotating reference voice")
        if got / target > a.max_ratio and (got - target) > a.max_excess_s:
            print(f"standin_vo REFUSED: {L['id']} still {got/target:.1f}x target ({got - target:.1f}s over) after {a.retries} retries. A line squeezed that "
                  f"hard is unintelligible and would move every word onset downstream. Shorten the line or raise --max-ratio deliberately."); return 1
        ratio = got / target if target > 0 else 1.0
        if a.no_normalise or abs(ratio - 1.0) < 0.02:
            os.replace(raw, final); used = got
        else:   # atempo caps at 2.0 per stage; chain if a line is very far off
            t, chain = ratio, []
            while t > 2.0: chain.append("atempo=2.0"); t /= 2.0
            while t < 0.5: chain.append("atempo=0.5"); t /= 0.5
            chain.append(f"atempo={t:.4f}")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-filter:a", ",".join(chain), final], check=True)
            os.remove(raw); used = dur(final)
        rows.append({**L, "standin": True, "file": final, "ref": ref, "raw_s": round(got, 2), "target_s": round(target, 2),
                     "final_s": round(used, 2), "tempo_ratio": round(ratio, 3)})
        print(f"  {L['id']:12} {L['chars']:3}c  raw {got:5.2f}s -> {used:5.2f}s (target {target:5.2f}s, x{ratio:.2f})")

    # QC the placeholder by EAR, not by duration. A take can land on its budgeted length and still say the wrong words
    # (Chatterbox repeats short phrases: "one hit one hit", "report none none"). Word onsets from a garbled line are
    # onsets for different words, so cut_on_word_rate cannot be trusted on it — record that per line instead of
    # discovering it in the gate.
    if not a.no_qc:
        try:
            import whisper, warnings
            warnings.filterwarnings("ignore")
            wm = whisper.load_model(a.qc_model)
            for row in rows:
                if not row.get("standin"): continue
                heard = wm.transcribe(row["file"], language="en")["text"].strip()
                norm = lambda t: set(re.findall(r"[a-z0-9']+", t.lower()))
                want, got = norm(row["text"]), norm(heard)
                overlap = len(want & got) / max(len(want), 1)
                row["standin_transcript"] = heard
                row["word_overlap"] = round(overlap, 2)
                row["onsets_trustworthy"] = bool(overlap >= 0.7 and len(got) <= len(want) + 2)
            untrusted = [r["id"] for r in rows if r.get("standin") and not r.get("onsets_trustworthy")]
            if untrusted:
                print(f"  QC: {len(untrusted)} placeholder line(s) came back garbled — their word onsets are NOT usable "
                      f"for cut_on_word_rate: {untrusted}")
        except Exception as e:
            print(f"  QC SKIPPED ({e}) — the stand-in's transcript was not checked; do not cite cut_on_word_rate from it")

    out = os.path.join(a.out, "STANDIN_MANIFEST.json")
    json.dump({"_schema": "PLACEHOLDER voice — local Chatterbox, tempo-normalised to the measured chars/s. NOT ORB/PIP/GRUFF, "
                          "NOT deliverable; exists so the stand-in render's speech numbers are measurable.",
               "standin": True, "engine": MODEL, "chars_per_sec": cps, "source_lines": a.lines,
               "real_takes_used": skipped, "lines": rows}, open(out, "w"), indent=1)
    print(f"standin_vo: {sum(1 for r in rows if r['standin'])} placeholder lines, {len(skipped)} real takes reused -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
