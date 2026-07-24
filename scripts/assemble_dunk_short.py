#!/usr/bin/env python3
"""Assemble the wordless vertical Dunkleosteus Short from Grok clips.

Built to the grammar measured in research/primeval_atlas_teardown/GROUND_TRUTH.md:
  * ONE COLOUR WORLD PER ACT  -- each act is graded into a single narrow hue band so
    hard cuts between unrelated 10 s Grok generations read as continuous drift.
    (This is the finding that makes discontinuous AI clips cut invisibly.)
  * 3-act saturation arc      -- muted gloom -> saturated open water -> muted again.
  * Contact staged dark       -- the strike beat is graded down, not up.
  * Sound design, NO score by default -- ambience bed everywhere, music only under
    the saturated act, violence carried by SFX. Silence before the reveal + strike.
  * Soft-in over the first ~1.25 s rather than a front-loaded bang.

Usage:
  venv/bin/python scripts/assemble_dunk_short.py -o output/dunk_short_v1.mp4
  venv/bin/python scripts/assemble_dunk_short.py --preview      # fast 540p check

Video: 720x1280 @ 24 fps (Grok native), h264.
Audio: built here. Grok's own clip audio came back near-silent (-50 LUFS) so it is
       dropped and replaced; if a future batch has real clip audio, set KEEP_CLIP_AUDIO.
"""
import argparse, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CLIPS = os.path.join(REPO, "assets", "dunk_short", "clips")
SFX = os.path.join(REPO, "assets", "sfx")
MUSIC = os.path.join(REPO, "assets", "dino_music", "dark_tension.mp3")

W, H, FPS = 720, 1280, 24
KEEP_CLIP_AUDIO = False

# act -> (saturation, gamma, r/g/b balance) : the single colour world per act
ACT_GRADE = {
    "gloom":     dict(sat=0.72, gamma=0.94, rw=0.94, gw=1.02, bw=1.06),
    "open":      dict(sat=1.08, gamma=1.14, rw=0.94, gw=1.03, bw=1.08),
    "dark":      dict(sat=0.60, gamma=0.74, rw=0.92, gw=1.00, bw=1.05),
    "aftermath": dict(sat=0.68, gamma=0.92, rw=0.96, gw=1.02, bw=1.02),
}

# The edit. in/out are seconds within each 10.04 s Grok clip.
EDIT = [
    dict(id="DUNK_S01", act="gloom",     tin=0.4, tout=10.0, note="WORLD - the puzzle, held still"),
    dict(id="DUNK_S02", act="gloom",     tin=0.0, tout=9.8, note="REVEAL - the terrain opens"),
    dict(id="DUNK_S03b", act="gloom",    tin=0.2, tout=8.6, note="BLADES - the title payoff (re-roll, no orange glow)"),
    dict(id="DUNK_S04", act="gloom",     tin=0.3, tout=9.9, note="SCALE - rises, glides over camera"),
    dict(id="DUNK_S05b", act="open",     tin=0.0, tout=10.0, note="ACT BREAK - the animal in open water (re-roll, in-world)"),
    dict(id="DUNK_S06b", act="dark",     tin=0.0, tout=6.5, note="THE STRIKE - dark, short, occluded (re-roll, armoured head)"),
    dict(id="DUNK_S07", act="aftermath", tin=0.0, tout=10.0, note="BOOKEND - becomes terrain again"),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd[:10])}...\n{r.stderr[-2000:]}")
    return r


def probe(path, entries="format=duration"):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries,
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return r.stdout.strip()


def grade_filter(act):
    g = ACT_GRADE[act]
    return (f"eq=saturation={g['sat']}:gamma={g['gamma']},"
            f"colorbalance=rs=-0.04:bs=0.06,"
            f"colorchannelmixer=rr={g['rw']}:gg={g['gw']}:bb={g['bw']}")


def build_segments(tmp, width, height):
    segs, t = [], 0.0
    for i, e in enumerate(EDIT):
        src = os.path.join(CLIPS, e["id"] + ".mp4")
        if not os.path.exists(src):
            print(f"  !! MISSING {e['id']} -- skipped", flush=True)
            continue
        dur = round(e["tout"] - e["tin"], 3)
        out = os.path.join(tmp, f"seg{i:02d}.mp4")
        vf = (f"{grade_filter(e['act'])},"
              f"scale={width}:{height}:force_original_aspect_ratio=increase,"
              f"crop={width}:{height},fps={FPS},format=yuv420p")
        cmd = ["ffmpeg", "-y", "-ss", str(e["tin"]), "-i", src, "-t", str(dur),
               "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "18", out, "-loglevel", "error"]
        run(cmd)
        segs.append(dict(path=out, start=t, dur=dur, **e))
        print(f"  [{i+1}/{len(EDIT)}] {e['id']:10s} {e['act']:9s} {t:5.1f}-{t+dur:5.1f}s  {e['note']}")
        t += dur
    return segs, t


def build_audio(tmp, segs, total):
    """Ambience bed everywhere + music only under the 'open' act + impacts.
    Silence (a hush) is created by ducking the bed just before reveal and strike."""
    rumble = os.path.join(SFX, "underwater", "rumble_bed_uw.wav")
    impact = os.path.join(SFX, "underwater", "impact_uw.wav")
    whoosh = os.path.join(SFX, "underwater", "whoosh_uw.wav")

    inputs, filters, mixes = [], [], []
    idx = 0

    # 1) looped underwater ambience bed across the whole piece, soft-in over 1.25 s
    inputs += ["-stream_loop", "-1", "-i", rumble]
    dark_seg = next((s for s in segs if s["act"] == "dark"), None)
    hush = ""
    if dark_seg:
        h0 = max(dark_seg["start"] - 1.4, 0.0)
        hush = (f",volume=enable='between(t,{h0},{dark_seg['start']})':volume=0.18")
    filters.append(f"[{idx}:a]atrim=0:{total},asetpts=N/SR/TB,volume=0.85{hush},"
                   f"afade=t=in:st=0:d=1.25,afade=t=out:st={total-2.0}:d=2.0[bed]")
    mixes.append("[bed]")
    idx += 1

    # 2) music ONLY under the saturated 'open' act (and a little into the strike)
    open_seg = next((s for s in segs if s["act"] == "open"), None)
    if open_seg and os.path.exists(MUSIC):
        m_start = open_seg["start"] - 1.5
        m_dur = open_seg["dur"] + 7.0
        inputs += ["-i", MUSIC]
        filters.append(
            f"[{idx}:a]atrim=20:{20+m_dur},asetpts=N/SR/TB,volume=0.30,"
            f"afade=t=in:st=0:d=2.0,afade=t=out:st={m_dur-3.0}:d=3.0,"
            f"adelay={int(max(m_start,0)*1000)}|{int(max(m_start,0)*1000)}[mus]")
        mixes.append("[mus]")
        idx += 1

    # 3) impact on the REVEAL (S02) and the STRIKE (S06); whoosh on the rise (S04)
    hits = []
    for s in segs:
        if s["id"] == "DUNK_S02":
            hits.append((impact, s["start"] + 1.6, 0.9))
        if s["id"] == "DUNK_S04":
            hits.append((whoosh, s["start"] + 0.8, 0.6))
        if s["act"] == "dark":
            hits.append((impact, s["start"] + 0.4, 1.0))
    for path, at, vol in hits:
        if not os.path.exists(path):
            continue
        inputs += ["-i", path]
        filters.append(f"[{idx}:a]volume={vol},adelay={int(at*1000)}|{int(at*1000)}[h{idx}]")
        mixes.append(f"[h{idx}]")
        idx += 1

    out = os.path.join(tmp, "mix.wav")
    fc = ";".join(filters) + ";" + "".join(mixes) + \
         f"amix=inputs={len(mixes)}:duration=first:normalize=0,alimiter=limit=0.95[a]"
    run(["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", "[a]",
         "-t", str(total), "-ar", "48000", "-ac", "2", out, "-loglevel", "error"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(REPO, "output", "dunk_short_v1.mp4"))
    ap.add_argument("--preview", action="store_true", help="fast 540-wide check")
    args = ap.parse_args()

    width, height = (540, 960) if args.preview else (W, H)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        print("Building segments (one colour world per act):")
        segs, total = build_segments(tmp, width, height)
        if not segs:
            sys.exit("no segments built -- are the clips in assets/dunk_short/clips?")
        print(f"\nTotal runtime: {total:.2f}s across {len(segs)} shots")

        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as f:
            for s in segs:
                f.write(f"file '{s['path']}'\n")
        silent = os.path.join(tmp, "video.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c", "copy", silent, "-loglevel", "error"])

        print("Building audio (ambience bed + music under the open act + impacts)...")
        mix = build_audio(tmp, segs, total)

        print("Mastering to -15 LUFS...")
        run(["ffmpeg", "-y", "-i", silent, "-i", mix,
             "-map", "0:v", "-map", "1:a",
             "-af", "loudnorm=I=-15:TP=-1.5:LRA=10",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-shortest", args.output, "-loglevel", "error"])

    print(f"\nWrote {args.output}")
    print(f"  {probe(args.output, 'stream=width,height,r_frame_rate')}  dur={probe(args.output)}")


if __name__ == "__main__":
    main()
