#!/usr/bin/env python3
"""Assemble EP02 from ep02_shots.json + the VO block manifest (+ optional music).

Follows the Dinoverse rough-cut policy: every shot renders a normalised segment,
and a shot with no clip yet renders a LABELLED placeholder instead of blocking the
build. That means a full-length cut exists from day one -- the real VO can be heard
against the real timeline long before all 88 clips are generated, and the assembly
path is proven before the grind rather than after it.

  venv/bin/python research/wildbirdsurvival_teardown/assemble_ep02.py --preview
  venv/bin/python research/wildbirdsurvival_teardown/assemble_ep02.py -o output/ep02_v1.mp4

Video : 1264x720 @ 24fps (Grok's native), h264. Clip audio is always dropped (-an)
        -- the edit rules mute it and the mix is VO + music only.
Audio : the 37 VO blocks dropped at their exact timecodes over a silent 480 s bed,
        plus an optional music bed under them.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
SHOTS = os.path.join(HERE, "ep02_shots.json")
VO = os.path.join(HERE, "ep02_vo_block_manifest.json")
ASSETS = os.path.join(REPO, "assets", "vampire_finch")
CLIPS = os.path.join(ASSETS, "clips")
MUSIC_DIR = os.path.join(REPO, "audio", "vampire_finch", "music")

W, H, FPS = 1264, 720, 24
RUNTIME = 480.0


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{' '.join(cmd[:12])}...\n{r.stderr[-1500:]}")
    return r


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")


def make_segment(shot, out, crf, scale):
    """One normalised segment of exactly shot['dur_s'] seconds."""
    sid, want = shot["id"], shot["dur_s"]
    clip = os.path.join(CLIPS, f"{sid}.mp4")
    w, h = scale

    if os.path.exists(clip):
        have = probe_dur(clip)
        # Grok always returns 6.04 s but most shots ship far less, so WHICH window we
        # take matters more than the length. S004 is 1.4 s and its whole point -- the
        # booby's defensive gape -- happens at ~1.0-2.4 s, so a blind trim=0 would ship
        # the static opening and drop the beat. clip_in names the good window's start.
        start = float(shot.get("clip_in", 0.0) or 0.0)
        if start + want > have + 0.02:
            start = max(0.0, have - want)
        if have >= want - 0.02:
            vf = (f"trim={start:.3f}:{start + want:.3f},setpts=PTS-STARTPTS,"
                  f"scale={w}:{h},fps={FPS},format=yuv420p")
        else:
            # under-covered: play what exists, then hold the last frame. Labelled so
            # nobody mistakes a padded shot for finished coverage.
            pad = want - have
            vf = (f"scale={w}:{h},fps={FPS},"
                  f"tpad=stop_mode=clone:stop_duration={pad:.3f},"
                  f"drawtext=text='{esc(sid)} UNDER-COVERED {pad:.1f}s':x=8:y=h-28:"
                  f"fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,format=yuv420p")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-an",
             "-vf", vf, "-t", f"{want:.3f}",
             "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
             "-pix_fmt", "yuv420p", "-r", str(FPS), out])
        return "clip" if have >= want - 0.02 else "padded"

    # no clip yet -> placeholder from the seed still, else a black slate
    seed = os.path.join(ASSETS, shot["seed"])
    label = f"PLACEHOLDER {sid}  {shot['size']}  {want:.1f}s"
    draw = (f"drawtext=text='{esc(label)}':x=(w-text_w)/2:y=h-40:fontsize=22:"
            f"fontcolor=white:box=1:boxcolor=red@0.65")
    if os.path.exists(seed):
        vf = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
              f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
              f"eq=saturation=0.35:brightness=-0.06,{draw},format=yuv420p")
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", seed,
             "-t", f"{want:.3f}", "-vf", vf, "-c:v", "libx264", "-crf", str(crf),
             "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), out])
        return "placeholder_seed"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"color=c=black:s={w}x{h}:r={FPS}", "-t", f"{want:.3f}",
         "-vf", draw, "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast",
         "-pix_fmt", "yuv420p", out])
    return "placeholder_black"


def build_audio(tmp, music):
    """VO blocks at their timecodes over silence, plus optional music bed."""
    segs = sorted(json.load(open(VO))["segments"], key=lambda s: s["drop_at_s"])
    inputs, filters, mixed = [], [], []
    for i, s in enumerate(segs):
        p = os.path.join(REPO, s["file"])
        if not os.path.exists(p):
            continue
        inputs += ["-i", p]
        filters.append(f"[{len(mixed)}:a]adelay={int(s['drop_at_s']*1000)}|"
                       f"{int(s['drop_at_s']*1000)},aformat=sample_fmts=fltp:"
                       f"sample_rates=48000:channel_layouts=stereo[v{len(mixed)}]")
        mixed.append(f"[v{len(mixed)}]")
    if not mixed:
        raise RuntimeError("no VO block files found — run split_vo_blocks.py")

    n = len(mixed)
    chain = ";".join(filters) + ";" + "".join(mixed) + f"amix=inputs={n}:normalize=0[vo]"
    last = "[vo]"
    if music and os.path.exists(music):
        inputs += ["-i", music]
        chain += (f";[{n}:a]aformat=sample_fmts=fltp:sample_rates=48000:"
                  f"channel_layouts=stereo,volume=-19dB,"
                  f"atrim=0:{RUNTIME},asetpts=PTS-STARTPTS[mus]"
                  f";[vo][mus]amix=inputs=2:normalize=0:duration=first[mixout]")
        last = "[mixout]"
    # The mix ends at its last sample (the final VO block lands ~471.5 s), and -t
    # only truncates — it never extends. Without apad the track is short and the
    # -shortest map then clips the video, losing the closing wind tail.
    chain += f";{last}apad,atrim=0:{RUNTIME},asetpts=PTS-STARTPTS[outa]"
    out = os.path.join(tmp, "mix.m4a")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
         "-filter_complex", chain, "-map", "[outa]",
         "-t", f"{RUNTIME}", "-c:a", "aac", "-b:a", "192k", out])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(REPO, "output", "ep02_rough.mp4"))
    ap.add_argument("--preview", action="store_true", help="half-res, faster")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--music", default=None, help="path to the music bed")
    args = ap.parse_args()

    scale = (W // 2 * 2, H // 2 * 2) if not args.preview else (632, 360)
    shots = sorted(json.load(open(SHOTS))["shots"], key=lambda s: s["in_s"])

    music = args.music
    if music is None and os.path.isdir(MUSIC_DIR):
        cands = [os.path.join(MUSIC_DIR, f) for f in sorted(os.listdir(MUSIC_DIR))
                 if f.lower().endswith((".mp3", ".wav", ".m4a"))]
        music = cands[0] if cands else None

    tmp = tempfile.mkdtemp(prefix="ep02_asm_")
    try:
        kinds, listfile = {}, os.path.join(tmp, "segs.txt")
        with open(listfile, "w") as lf:
            for i, s in enumerate(shots):
                seg = os.path.join(tmp, f"{i:03d}_{s['id']}.mp4")
                kind = make_segment(s, seg, args.crf, scale)
                kinds[kind] = kinds.get(kind, 0) + 1
                lf.write(f"file '{seg}'\n")
                if (i + 1) % 20 == 0:
                    print(f"  … {i+1}/{len(shots)} segments", flush=True)

        print(f"segments: {kinds}")
        silent = os.path.join(tmp, "video.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", listfile, "-c", "copy", silent])

        audio = build_audio(tmp, music)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", audio,
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
             "-b:a", "192k", "-shortest", args.output])

        dur = probe_dur(args.output)
        print(f"\nwrote {os.path.relpath(args.output, REPO)}  {dur:.2f}s "
              f"(target {RUNTIME})  music={'yes' if music else 'NONE'}")
        if abs(dur - RUNTIME) > 1.0:
            print(f"  !! duration is off target by {dur - RUNTIME:+.2f}s")
        real = kinds.get("clip", 0) + kinds.get("padded", 0)
        print(f"  real footage in {real}/{len(shots)} shots; the rest are labelled placeholders")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
