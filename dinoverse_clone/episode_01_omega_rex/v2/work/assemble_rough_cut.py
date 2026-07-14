#!/usr/bin/env python3
"""Rough-cut assembler for Dinoverse v2 (episode_01_omega_rex).

Reads ../STORYBOARD.tsv in row order and renders one normalized segment per
shot (1264x720, 24fps, h264 crf18, aac 48k stereo), then concats them into
work/rough_cut/rough_cut_v1.mp4.

Segment rules (rough-cut policy — see PIVOT_PLAN 'Assembly after all zones'):
- CARD  -> drawtext card (S01 disclaimer, S89 end card).
- GEN with an approved clip on disk -> FULL clip (no board-duration trims yet:
  trimming dialogue blind risks cutting lines; S60/S74/S75 trims happen in the
  final edit). Original audio kept.
- GEN without a clip -> still placeholder at board duration (Z10 S79-S88, S73
  whose roll-1 was rejected), or a black slate if no still exists (S02).
- TRIM silent (S65b/S66b/S67b/S67c/S74b/S77b/S77d) -> muted segment of the
  source clip (ambience/SFX come at final mix).
- TRIM flash (cold open S03-S12, S77c) -> muted 1.5s/2s/1s peak segment of the
  source clip; if the source clip doesn't exist yet, the source STILL flashes
  as a placeholder.
Placeholders carry a corner label so nobody mistakes them for finals.
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

V2 = Path(__file__).resolve().parents[1]
TSV = V2.parent / "STORYBOARD.tsv"
CLIPS = V2 / "clips"
STILLS = V2 / "stills"
OUT = V2 / "work" / "rough_cut"
SEGS = OUT / "segments"

GREEN = "0x2ecc40"

# TRIM shot -> (source shot, offset_s or None for auto, mute)
# offset None = centered for flashes / tail-6s for 6s-silent from 10s sources.
TRIM_SRC = {
    "S03": "S80", "S04": "S48", "S05": "S38", "S06": "S36", "S07": "S67",
    "S08": "S84", "S09": "S82", "S10": "S83", "S11": "S69", "S12": "S88",
    "S65b": "S65", "S66b": "S66", "S67b": "S67", "S67c": "S65",
    "S74b": "S74", "S77b": "S77", "S77c": "S73", "S77d": "S76",
}
# Hand-picked flash offsets (S67 roar peaks ~t6.0 per Z8 QA notes).
FLASH_OFFSET = {"S07": 5.2}
# Shots whose clip exists but is NOT approved (owner rejected roll 1).
REJECTED_CLIPS = set()  # S73 roll 2 approved 2026-07-13

# v2 policy: GEN clips trim to board duration IFF the clip's audio (speech/SFX)
# ends before the cut point — measured via silencedetect and frozen in
# trim_plan_v2.json (see PIVOT_PLAN §I2V TRACK 2026-07-13). Everything else
# still plays full length; those trims stay deferred to the final edit.
import json as _json
_plan_path = Path(__file__).resolve().parent / "rough_cut" / "trim_plan_v2.json"
TRIM_PLAN = _json.loads(_plan_path.read_text()) if _plan_path.exists() else {}

# v3: cold-open flashes carry NATIVE source audio from a speech-free window
# (whisper word-timestamps + RMS pick, frozen in flash_audio_plan.json).
# S12 has no speech-free window in S88 (VO spans 0-4.96s) -> borrows S85's
# roar audio under the S88 visual (temp SFX; final mix replaces).
_fa_path = Path(__file__).resolve().parent / "rough_cut" / "flash_audio_plan.json"
FLASH_PLAN = _json.loads(_fa_path.read_text()) if _fa_path.exists() else {}

# v4: the 8 silent "dread-stack" TRIMs literally replay already-seen clips
# MUTED (only one 6s take exists per source), which reads as broken repeats —
# owner flagged "endless repeats just with and without sound." Dropped from the
# rough cut; a real dread beat needs distinct alt-angle gens (later decision).
# Also kills the doubled empty-pit before the D-Rex reveal (S74 + S74b).
DROP_SHOTS = {"S65b", "S66b", "S67b", "S67c", "S74b", "S77b", "S77c", "S77d"}

CARDS = {
    "S01": [
        ("DINO ZOO", GREEN, 110, -60),
        ("AI-generated for entertainment", "white", 36, 80),
    ],
    "S89": [
        ("Comment which dino you'd survive.", "white", 52, -50),
        ("Subscribe — part two if this hits.", GREEN, 44, 50),
    ],
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FFMPEG FAIL ({' '.join(map(str, cmd[:6]))}...):\n{r.stderr[-2000:]}")


def enc_args():
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "aac", "-b:a", "128k",
            "-video_track_timescale", "24000"]


def drawtext(text, color, size, dy):
    safe = text.replace("'", "’").replace(":", "\\:")
    return (f"drawtext=text='{safe}':fontcolor={color}:fontsize={size}"
            f":x=(w-text_w)/2:y=(h-text_h)/2+({dy}):font=Helvetica")


def label_filter(tag):
    return (f"drawtext=text='{tag}':fontcolor=yellow:fontsize=28:x=20:y=20"
            f":box=1:boxcolor=black@0.6:boxborderw=8:font=Helvetica")


def clip_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def seg_card(shot, dur, out):
    vf = ",".join(drawtext(t, c, s, dy) for t, c, s, dy in CARDS[shot])
    run(["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=c=black:s=1264x720:r=24:d={dur}",
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-t", str(dur), "-vf", vf, "-map", "0:v", "-map", "1:a",
         *enc_args(), "-shortest", str(out)])


def seg_slate(shot, dur, out, note):
    vf = drawtext(f"{shot} — {note}", "white", 48, 0)
    run(["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=c=0x202020:s=1264x720:r=24:d={dur}",
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-t", str(dur), "-vf", vf, "-map", "0:v", "-map", "1:a",
         *enc_args(), "-shortest", str(out)])


def seg_still(shot, still, dur, out, tag):
    vf = ("scale=1264:720:force_original_aspect_ratio=increase,"
          "crop=1264:720," + label_filter(tag))
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(dur),
         "-i", str(still),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-t", str(dur), "-vf", vf, "-map", "0:v", "-map", "1:a",
         *enc_args(), "-shortest", str(out)])


def seg_clip_full(clip, out):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(clip),
         "-map", "0:v:0", "-map", "0:a:0", *enc_args(), str(out)])


def seg_clip_boardtrim(clip, dur, out):
    # head-anchored trim, native audio kept (audio verified to end before dur)
    run(["ffmpeg", "-y", "-v", "error", "-t", str(dur), "-i", str(clip),
         "-t", str(dur), "-map", "0:v:0", "-map", "0:a:0",
         *enc_args(), str(out)])


def seg_clip_muted(clip, offset, dur, out):
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(offset), "-t", str(dur),
         "-i", str(clip),
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-t", str(dur), "-map", "0:v:0", "-map", "1:a",
         *enc_args(), "-shortest", str(out)])


def seg_flash_audio(vclip, voff, dur, out, aclip=None, aoff=None):
    # video from vclip@voff; audio from the same window (or aclip@aoff),
    # with short fades so hard flash cuts don't click.
    aclip = aclip or vclip
    aoff = voff if aoff is None else aoff
    fade = f"afade=t=in:d=0.06,afade=t=out:st={dur - 0.08:.2f}:d=0.08"
    run(["ffmpeg", "-y", "-v", "error",
         "-ss", str(voff), "-t", str(dur), "-i", str(vclip),
         "-ss", str(aoff), "-t", str(dur), "-i", str(aclip),
         "-map", "0:v:0", "-map", "1:a:0", "-af", fade,
         *enc_args(), "-shortest", str(out)])


def parse_dur(s):
    m = re.match(r"([\d.]+)s", s.strip())
    return float(m.group(1)) if m else 6.0


def main():
    SEGS.mkdir(parents=True, exist_ok=True)
    rows = list(csv.reader(TSV.open(), delimiter="\t"))[1:]
    manifest, files = [], []

    for r in rows:
        shot, dur_s, ctype = r[1], parse_dur(r[3]), r[13]
        if shot in DROP_SHOTS:
            continue
        out = SEGS / f"{shot}.mp4"
        clip = CLIPS / f"{shot}.mp4"
        still = STILLS / f"{shot}.png"

        if ctype == "CARD":
            seg_card(shot, dur_s, out)
            kind = "CARD"
        elif ctype == "TRIM":
            src_clip = CLIPS / f"{TRIM_SRC[shot]}.mp4"
            src_still = STILLS / f"{TRIM_SRC[shot]}.png"
            src_ok = src_clip.exists() and TRIM_SRC[shot] not in REJECTED_CLIPS
            if src_ok and shot in FLASH_PLAN:
                fp = FLASH_PLAN[shot]
                aclip = CLIPS / f"{fp['audio_src']}.mp4" if "audio_src" in fp else None
                seg_flash_audio(src_clip, fp["offset"], dur_s, out,
                                aclip=aclip, aoff=fp.get("audio_offset"))
                kind = f"FLASH<-{TRIM_SRC[shot]}@{fp['offset']:.1f}s+audio"
            elif src_ok:
                total = clip_dur(src_clip)
                off = FLASH_OFFSET.get(shot)
                if off is None:
                    # silent 6s trims: tail of the source; flashes: centered
                    off = max(0.0, total - dur_s) if dur_s >= 6 else max(0.0, (total - dur_s) / 2)
                seg_clip_muted(src_clip, off, dur_s, out)
                kind = f"TRIM<-{TRIM_SRC[shot]}@{off:.1f}s"
            elif src_still.exists():
                seg_still(shot, src_still, dur_s, out,
                          f"{shot} PLACEHOLDER (still {TRIM_SRC[shot]})")
                kind = f"STILL-PLACEHOLDER<-{TRIM_SRC[shot]}"
            else:
                seg_slate(shot, dur_s, out, "source pending")
                kind = "SLATE"
        else:  # GEN
            if clip.exists() and shot not in REJECTED_CLIPS:
                if TRIM_PLAN.get(shot, {}).get("trim"):
                    seg_clip_boardtrim(clip, dur_s, out)
                    kind = f"CLIP(trim {TRIM_PLAN[shot]['clip']}->{dur_s}s)"
                else:
                    seg_clip_full(clip, out)
                    dur_s = clip_dur(out)
                    kind = "CLIP(full)"
            elif still.exists():
                seg_still(shot, still, dur_s, out, f"{shot} PLACEHOLDER (i2v pending)")
                kind = "STILL-PLACEHOLDER"
            else:
                seg_slate(shot, dur_s, out, "clip + still pending")
                kind = "SLATE"

        manifest.append((shot, kind, dur_s))
        files.append(out)

    listfile = OUT / "concat_list.txt"
    listfile.write_text("".join(f"file '{f}'\n" for f in files))
    final = OUT / "rough_cut_v6.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(listfile), "-c", "copy", str(final)])

    total = 0.0
    print(f"{'shot':7} {'kind':34} dur    starts@")
    for shot, kind, d in manifest:
        print(f"{shot:7} {kind:34} {d:5.1f}  {int(total)//60}:{total % 60:04.1f}")
        total += d
    n_ph = sum(1 for _, k, _ in manifest if "PLACEHOLDER" in k or k == "SLATE")
    print(f"\nTOTAL {int(total)//60}:{total % 60:04.1f}  ({len(manifest)} shots, "
          f"{n_ph} placeholders/slates)\n-> {final}")


if __name__ == "__main__":
    main()
