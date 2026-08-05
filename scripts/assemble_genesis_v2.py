#!/usr/bin/env python3
"""Assemble the Christ Cares Genesis overview v2: 53 Grok i2v clips + Brian VO.

Replaces the v1 Ken Burns stills assembler (assemble_genesis_pilot.py) per
GENESIS_SHOT_LEDGER.md v2:
  - every interior cut snaps to the nearest whisperx word onset within 0.3s
  - P2 flash chain (G005c-G008c) + G050a-d = slices of already-rendered clips
  - owner-addition splits G022a/b, G025a/b, G037a/b at their word onsets
  - spans longer than a source clip retime the clip (setpts/atempo) to fit;
    spans shorter simply trim the head of the clip
  - every segment is upscaled 720p->1080p with the validated
    lanczos+unsharp=5:5:0.4 pass (grain-survival test on G023, 2026-08-05)
  - native Grok ambience rides under the VO at -12 dB; no music bed yet
    (hymn decision pending owner)

Usage:
  venv/bin/python scripts/assemble_genesis_v2.py -o output/christ_cares_genesis_v2.mp4
"""
import argparse, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
CLIPS = os.path.join(REPO, "assets", "christ_cares", "clips")
NARRATION = os.path.join(REPO, "audio", "christ_cares", "genesis_overview.wav")
ALIGNMENT = os.path.join(REPO, "audio", "christ_cares", "genesis_overview_whisperx.json")

W, H, FPS = 1920, 1080, 30
SNAP = 0.3           # ledger rule: interior cuts snap to nearest onset within 0.3s
SLICE_OFFSET = 2.5   # flash-chain slices start here so they don't repeat the head
AMBIENCE_GAIN = 0.25 # clip native audio under the VO (~-12 dB)

# (shot_id, source_clip, slice_offset) in ledger order; boundaries follow below.
SHOTS = [
    ("G001", "G001", 0.0), ("G002", "G002", 0.0), ("G003", "G003", 0.0),
    ("G004", "G004", 0.0),
    ("G005c", "G002", SLICE_OFFSET), ("G006c", "G007", SLICE_OFFSET),
    ("G007c", "G005", SLICE_OFFSET), ("G008c", "G006", SLICE_OFFSET),
    ("G007", "G007", 0.0), ("G008", "G008", 0.0), ("G009", "G009", 0.0),
    ("G010", "G010", 0.0), ("G011", "G011", 0.0), ("G012", "G012", 0.0),
    ("G013", "G013", 0.0), ("G014", "G014", 0.0), ("G015", "G015", 0.0),
    ("G016", "G016", 0.0), ("G017", "G017", 0.0), ("G018", "G018", 0.0),
    ("G019", "G019", 0.0), ("G020", "G020", 0.0), ("G021", "G021", 0.0),
    ("G022a", "G022a", 0.0), ("G022b", "G022b", 0.0), ("G023", "G023", 0.0),
    ("G024", "G024", 0.0), ("G025a", "G025a", 0.0), ("G025b", "G025b", 0.0),
    ("G026", "G026", 0.0), ("G027", "G027", 0.0), ("G028", "G028", 0.0),
    ("G029", "G029", 0.0), ("G030", "G030", 0.0), ("G031", "G031", 0.0),
    ("G032", "G032", 0.0), ("G033", "G033", 0.0), ("G034", "G034", 0.0),
    ("G035", "G035", 0.0), ("G036", "G036", 0.0), ("G037a", "G037a", 0.0),
    ("G037b", "G037b", 0.0), ("G038", "G038", 0.0), ("G039", "G039", 0.0),
    ("G040", "G040", 0.0), ("G041", "G041", 0.0), ("G042", "G042", 0.0),
    ("G043", "G043", 0.0), ("G044", "G044", 0.0), ("G045", "G045", 0.0),
    ("G046", "G046", 0.0), ("G047", "G047", 0.0), ("G048", "G048", 0.0),
    ("G049", "G049", 0.0),
    ("G050a", "G008", SLICE_OFFSET), ("G050b", "G024", SLICE_OFFSET),
    ("G050c", "G021", SLICE_OFFSET), ("G050d", "G023", SLICE_OFFSET),
    ("G051", "G051", 0.0),
]

# 60 boundaries -> 59 spans (ledger v2 In-Out columns; ~ values are snap targets)
BOUNDARIES = [
    0.0, 4.5, 9.0, 13.5, 18.42, 20.16, 22.10, 24.58, 27.0, 32.5, 38.44, 44.0,
    49.5, 54.96, 63.4, 69.6, 71.2, 75.5, 81.2, 87.0, 93.0, 99.0, 105.16, 110.0,
    112.2, 114.5, 118.92, 124.0, 127.5, 131.3, 134.1, 140.36, 146.0, 150.5,
    155.34, 161.0, 167.0, 173.12, 179.0, 185.5, 191.84, 194.1, 196.5, 201.0,
    205.28, 210.0, 212.0, 213.7, 224.5, 229.84, 235.5, 241.0, 247.5, 253.88,
    260.0, 261.89, 263.11, 264.43, 267.0, 275.2,
]


def run(cmd, timeout=180):
    # -nostdin + hard timeout: a wedged ffmpeg (e.g. blocking on an iCloud
    # dataless read) must fail loudly, never hang the build silently.
    if cmd[0] == "ffmpeg":
        cmd = ["ffmpeg", "-nostdin"] + cmd[1:]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd[:10])}...\n{r.stderr[-1500:]}")
    return r


def materialize(paths):
    """CLAUDE.md render rule: force-read any iCloud-dataless file first."""
    for p in paths:
        if os.stat(p).st_blocks == 0:
            print(f"  hydrating dataless: {p}")
            with open(p, "rb") as f:
                while f.read(1 << 22):
                    pass
        if os.stat(p).st_blocks == 0:
            sys.exit(f"still dataless after force-read: {p}")


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def snap_boundaries(bounds, onsets):
    out = [bounds[0]]
    for t in bounds[1:-1]:
        best = min(onsets, key=lambda o: abs(o - t))
        out.append(best if abs(best - t) <= SNAP else t)
    out.append(bounds[-1])
    for a, b in zip(out, out[1:]):
        if b - a < 0.4:
            sys.exit(f"snapped span collapsed: {a:.2f}->{b:.2f}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(REPO, "output", "christ_cares_genesis_v2.mp4"))
    args = ap.parse_args()

    words = json.load(open(ALIGNMENT))["words"]
    onsets = [w["start"] for w in words]
    bounds = snap_boundaries(BOUNDARIES, onsets)
    spans = list(zip(bounds, bounds[1:]))
    assert len(spans) == len(SHOTS), f"{len(spans)} spans vs {len(SHOTS)} shots"

    clip_paths = {src: os.path.join(CLIPS, f"{src}.mp4") for _, src, _ in SHOTS}
    for src, p in clip_paths.items():
        if not os.path.exists(p):
            sys.exit(f"missing clip: {p}")
    materialize(list(clip_paths.values()) + [NARRATION])
    clip_durs = {src: probe_duration(p) for src, p in clip_paths.items()}

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        seg_paths = []
        for i, ((sid, src, off), (t0, t1)) in enumerate(zip(SHOTS, spans)):
            span = t1 - t0
            avail = clip_durs[src] - off
            factor = span / avail if span > avail else 1.0  # retime only to stretch
            take = span / factor
            seg = os.path.join(td, f"seg_{i:02d}_{sid}.mp4")
            # ffmpeg 8.0 deadlocks when a retimed -vf and -af run in ONE
            # process (scheduler interleave; isolated 2026-08-05 on G012).
            # Build video and audio in separate passes, then copy-mux.
            clip = os.path.join(CLIPS, f"{src}.mp4")
            vf = (f"trim=start={off:.3f}:end={off + take:.3f},setpts=(PTS-STARTPTS)*{factor:.6f},"
                  f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.4:5:5:0.0,fps={FPS},setsar=1")
            af = (f"atrim=start={off:.3f}:end={off + take:.3f},asetpts=PTS-STARTPTS,"
                  + (f"atempo={1.0 / factor:.6f}," if factor > 1.0 else "")
                  + f"apad=pad_dur=1.0,atrim=0:{span:.3f},aresample=48000,aformat=channel_layouts=stereo")
            vseg = os.path.join(td, f"v_{i:02d}.mp4")
            aseg = os.path.join(td, f"a_{i:02d}.m4a")
            run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-an", "-vf", vf,
                 "-t", f"{span:.3f}", "-c:v", "libx264", "-preset", "fast",
                 "-crf", "18", "-pix_fmt", "yuv420p", vseg])
            run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-vn", "-af", af,
                 "-t", f"{span:.3f}", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", aseg])
            run(["ffmpeg", "-y", "-v", "error", "-i", vseg, "-i", aseg,
                 "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", seg])
            seg_paths.append(seg)
            note = f" retime x{factor:.2f}" if factor > 1.0 else ""
            print(f"  seg {i + 1:02d}/{len(SHOTS)} {sid:6s} {t0:7.2f}-{t1:7.2f} ({span:5.2f}s) <- {src}@{off:.1f}{note}")

        concat_list = os.path.join(td, "list.txt")
        with open(concat_list, "w") as f:
            for p in seg_paths:
                f.write(f"file '{p}'\n")
        timeline = os.path.join(td, "timeline.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", timeline])

        total = bounds[-1]
        fade_start = max(0.0, total - 1.0)
        run(["ffmpeg", "-y", "-v", "error", "-i", timeline, "-i", NARRATION,
             "-filter_complex",
             f"[0:a]volume={AMBIENCE_GAIN}[amb];"
             f"[1:a]apad=whole_dur={total:.3f}[vo];"
             f"[vo][amb]amix=inputs=2:duration=first:normalize=0,"
             f"afade=t=out:st={fade_start:.3f}:d=1.0[aout];"
             f"[0:v]fade=t=out:st={fade_start:.3f}:d=1.0[vout]",
             "-map", "[vout]", "-map", "[aout]",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", args.output])

    print(f"wrote {args.output}: {probe_duration(args.output):.2f}s "
          f"(narration {probe_duration(NARRATION):.2f}s)")


if __name__ == "__main__":
    main()
