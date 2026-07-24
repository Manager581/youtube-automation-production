#!/usr/bin/env python3
"""Assemble the wordless vertical Spinosaurus Short from Grok i2v clips.

Built to the measured spec in
research/primeval_atlas_teardown/CAMERA_AND_SOUND_SPEC.md:

  * NO IMPOSED GRADE. Each location keeps its own true palette. We only match
    exposure inside an act. (The reference's "saturation arc" is three real
    environments shot honestly, not a LUT -- copying it as a filter is what
    turned the first attempt to murk.)
  * KEEP THE NATIVE CLIP AUDIO where it is real; only fill where it is dead.
    Measured per clip: reveal -29.3, hero -40.1, wade -52.2 LUFS.
  * THE LOWPASS ARC is the film's best trick and we apply it OURSELVES rather
    than trusting the generator: full band above water, ~800 Hz under, a sweep
    on the dive, a one-frame snap back on the breach.
  * HOLES BEFORE PAYOFFS -- duck to near-silence 0.5-1.0 s before each reveal.
  * Master -15 LUFS, TP -1.5, defend LRA >= 9.

Usage:
  venv/bin/python scripts/assemble_spino_short.py -o output/spino_short_v1.mp4
  venv/bin/python scripts/assemble_spino_short.py --preview
"""
import argparse, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CLIPS = os.path.join(REPO, "assets", "spino_short", "clips")
SFX = os.path.join(REPO, "assets", "sfx")

W, H, FPS = 720, 1280, 24

# act: "bank" (above water, full band) | "under" (lowpass ~800Hz)
# `hole` = seconds into the TRIMMED segment where a payoff lands; the mix ducks
# to near-silence for 0.8 s before it and lifts on the hit.
# gain = per-clip level match. Missing files are skipped with a warning, so this
# is the FULL film order; clips drop in as they finish rendering.
# (The old SP_B08_strike stays banned: its prompt said the water "EXPLODES" and
# Grok rendered a literal detonation. Never explode/blast/burst; never ask for an
# off-screen attacker. Violence = the mosasaur's own shot, then the hero dragged
# down through churning silt with contact off-frame.)
EDIT = [
    dict(id="SPINO_S01_reveal",  act="bank",  tin=0.3, tout=7.3, gain=1.0,
         hole=5.6, hit="underwater/impact_uw.wav",
         note="1  HOOK: the 'sandbar' lifts and becomes the animal."),
    dict(id="SP_B02b_journey",   act="bank",  tin=0.5, tout=7.0, gain=2.0,
         note="2  JOURNEY: tiny in the vast marsh, walking toward the sea."),
    dict(id="SP_B02_wade_sail",  act="bank",  tin=0.5, tout=6.5, gain=6.0,
         note="3  LULL: wades away, only the sail above water. Quiet."),
    dict(id="SP_B04c_sea_entry", act="bank",  tin=0.5, tout=8.0, gain=2.0,
         note="4  INTO THE SEA: through the surf until only the sail shows."),
    dict(id="SP_B05b_living_sea",act="under", tin=0.0, tout=7.5, gain=2.5,
         note="5  A LIVING SEA: fish school parts around it."),
    dict(id="SP_B06_sealife",    act="under", tin=0.0, tout=6.0, gain=2.5,
         note="6  SUPPORTING CAST: jellyfish, squid, turtle. Calm."),
    dict(id="SP_B05_hero",       act="under", tin=0.0, tout=7.8, gain=2.5,
         hole=6.0, hit="underwater/rumble_bed_uw.wav",
         note="7  HERO: eye level, head-on, fills frame."),
    dict(id="SP_B07_threat",     act="under", tin=1.5, tout=7.5, gain=3.0,
         note="8  THREAT: a far larger shape passes in the gloom."),
    dict(id="SP_B09a_mosasaur",  act="under", tin=0.0, tout=4.5, gain=2.5,
         hole=3.8, hit="underwater/impact_uw.wav",
         note="9a MOSASAUR COMMITS: drives down out of frame, jaws opening."),
    dict(id="SP_B09b_dragged",   act="under", tin=0.0, tout=6.5, gain=2.0,
         note="9b DRAGGED DOWN: thrashing silhouette inside churning silt."),
    dict(id="SP_B10_bookend",    act="bank",  tin=0.5, tout=7.0, gain=2.0,
         note="10 BOOKEND: settles into the mud, reads as a ridge again."),
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd[:9])}...\n{r.stderr[-1500:]}")
    return r


def probe(path, entries="format=duration"):
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries,
                           "-of", "csv=p=0", path],
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output",
                    default=os.path.join(REPO, "output", "spino_short_v1.mp4"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-card", action="store_true", help="skip the 4.5 s end card")
    args = ap.parse_args()
    w, h = (540, 960) if args.preview else (W, H)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        segs, t = [], 0.0
        print("Segments (no grade applied -- each location keeps its own palette):")
        for i, e in enumerate(EDIT):
            src = os.path.join(CLIPS, e["id"] + ".mp4")
            if not os.path.exists(src):
                print(f"  !! MISSING {e['id']}")
                continue
            dur = round(e["tout"] - e["tin"], 3)

            v = os.path.join(tmp, f"v{i}.mp4")
            run(["ffmpeg", "-y", "-ss", str(e["tin"]), "-i", src, "-t", str(dur),
                 "-vf", (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                         f"crop={w}:{h},fps={FPS},format=yuv420p"),
                 "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 v, "-loglevel", "error"])

            # audio: keep the NATIVE clip sound. Per-clip gain only (measured
            # levels differ by ~23 dB), the act's filter, and the hole/impact
            # automation. Deliberately NOT loudnorm-per-segment -- that levels
            # every shot to the same loudness and is what killed the dynamics.
            a = os.path.join(tmp, f"a{i}.wav")
            af = f"volume={e.get('gain', 1.0)}"
            if e["act"] == "under":
                af += ",lowpass=f=800,bass=g=4:f=90"      # the underwater filter
            else:
                af += ",highpass=f=45"
            # THE HOLE: duck hard for 0.9 s before a payoff so the hit has
            # something to land against. Reference measures -42.7 dB holes
            # against -12 dB peaks = a 30 dB swing.
            hole = e.get("hole")
            if hole is not None:
                h0 = max(hole - 0.9, 0.0)
                af += f",volume=enable='between(t,{h0},{hole})':volume=0.06"
            run(["ffmpeg", "-y", "-ss", str(e["tin"]), "-i", src, "-t", str(dur),
                 "-vn", "-af", af, "-ar", "48000", "-ac", "2",
                 a, "-loglevel", "error"])

            # THE HIT: a real impact on the payoff frame, so the peak is genuine
            hit = e.get("hit")
            if hole is not None and hit and os.path.exists(os.path.join(SFX, hit)):
                a2 = os.path.join(tmp, f"a{i}h.wav")
                run(["ffmpeg", "-y", "-i", a, "-i", os.path.join(SFX, hit),
                     "-filter_complex",
                     (f"[1:a]volume=1.0,adelay={int(hole*1000)}|{int(hole*1000)}[h];"
                      f"[0:a][h]amix=inputs=2:duration=first:normalize=0[a]"),
                     "-map", "[a]", "-ar", "48000", "-ac", "2",
                     a2, "-loglevel", "error"])
                a = a2

            seg = os.path.join(tmp, f"s{i}.mp4")
            run(["ffmpeg", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                 "-shortest", seg, "-loglevel", "error"])

            segs.append(seg)
            print(f"  [{i+1}] {e['id']:22s} {e['act']:6s} {t:5.1f}-{t+dur:5.1f}s  {e['note']}")
            t += dur

        if not segs:
            sys.exit("no clips found in " + CLIPS)

        # END CARD: the reference holds 4.716 s of black. It uses TRUE digital
        # zero; we use -55 dB room tone instead, because multi-second true zero
        # can interact badly with platform loudness processing.
        if not args.no_card:
            card = os.path.join(tmp, "card.mp4")
            run(["ffmpeg", "-y",
                 "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={FPS}:d=4.5",
                 "-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.0018:r=48000:d=4.5",
                 "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                 card, "-loglevel", "error"])
            segs.append(card)
            t += 4.5
            print(f"  [card] 4.5 s black, -55 dB room tone (not true zero)")

        lst = os.path.join(tmp, "l.txt")
        with open(lst, "w") as f:
            for s in segs:
                f.write(f"file '{s}'\n")
        joined = os.path.join(tmp, "joined.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             joined, "-loglevel", "error"])

        print(f"\nTotal {t:.1f}s across {len(segs)} shots. Mastering to -15 LUFS...")
        run(["ffmpeg", "-y", "-i", joined,
             "-af", "loudnorm=I=-15:TP=-1.5:LRA=10",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             args.output, "-loglevel", "error"])

    print(f"Wrote {args.output}")
    print(f"  {probe(args.output,'stream=width,height,r_frame_rate')}  dur={probe(args.output)}")


if __name__ == "__main__":
    main()
