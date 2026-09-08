#!/usr/bin/env python3
"""lib/assembly/edit_layer.py — the FREE edit-layer operations the measured hook grammar runs on
(PIPELINE_OVERHAUL_PLAN S6; cost split: ~17 generated setups vs ~120 edit-layer ops in the #1 hook).
All builders return ffmpeg filter fragments or run ffmpeg; nothing here generates pixels with AI.

  punch_in(z0, z1, t0, t1, fps, W, H)   digital zoom on ONE take (zoompan on video, d=1); snap when t1==t0
  whiteout(t, dur=0.10)                 white frames hiding a cut / hard transition
  flash(t, dur=0.08, alpha=0.6)         white flash on a money line
  bloom(t, dur=0.25, amount=0.3)        brightness bloom
  text_pop(text, t_on, t_off, lead, ...) on-screen text that LEADS the spoken word by `lead` s, with a 0.1 s size pop
  photo_stack(stills, each, W, H, fps)  a stack of stills with whiteouts between (renders a segment mp4)
  concat(segments, out)                 concat demuxer, re-encode-free when codecs match
Self-test: python3 lib/assembly/edit_layer.py --selftest OUT_DIR  (synthetic take + stills → 12 s hook → hook_score)
"""
import os, subprocess, sys, tempfile

FONT = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

def punch_in(z0, z1, t0, t1, fps=24, W=1920, H=1080):
    f0, f1 = int(round(t0 * fps)), int(round(max(t1, t0 + 1.0 / fps) * fps))
    z = f"if(lt(in,{f0}),{z0},if(gt(in,{f1}),{z1},{z0}+({z1}-{z0})*(in-{f0})/({f1}-{f0})))"
    return f"zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}"

def whiteout(t, dur=0.10, alpha=0.85):
    """Soft whiteout: hides a cut at scene-th 0.1 (a transition) WITHOUT registering as a hard cut at 0.3 — the reference's
    hidden cuts measure this way (1 hard cut vs 24 transitions in its first 12 s)."""
    return f"drawbox=c=white@{alpha}:t=fill:enable='between(t,{t:.3f},{t+dur:.3f})'"
def flash(t, dur=0.08, alpha=0.6): return f"drawbox=c=white@{alpha}:t=fill:enable='between(t,{t:.3f},{t+dur:.3f})'"
def bloom(t, dur=0.25, amount=0.3): return f"eq=brightness={amount}:enable='between(t,{t:.3f},{t+dur:.3f})'"

def text_pop(text, t_on, t_off, lead=0.3, size=96, y="h*0.72", color="white", pop=1.15):
    on = max(0.0, t_on - lead); esc = text.replace(":", "\\:").replace("'", "\\'")
    big = f"drawtext=fontfile={FONT}:text='{esc}':fontsize={int(size*pop)}:fontcolor={color}:borderw=6:bordercolor=black:x=(w-text_w)/2:y={y}:enable='between(t,{on:.3f},{on+0.10:.3f})'"
    norm = f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor={color}:borderw=6:bordercolor=black:x=(w-text_w)/2:y={y}:enable='between(t,{on+0.10:.3f},{t_off:.3f})'"
    return big + "," + norm

def run(cmd): subprocess.run(cmd, check=True, capture_output=True)

def segment_from_take(take, t0, t1, vf, out, fps=24, W=1920, H=1080):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t0:.3f}", "-t", f"{t1-t0:.3f}", "-i", take, "-vf", f"scale={W}:{H},fps={fps}," + vf if vf else f"scale={W}:{H},fps={fps}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps), out])

def photo_stack(stills, each, out, fps=24, W=1920, H=1080, white=0.08):
    segs = []
    for i, p in enumerate(stills):
        s = out.replace(".mp4", f"_ps{i}.mp4")
        vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={fps}," + whiteout(0.0, white)
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-t", f"{each:.3f}", "-i", p, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps), s]); segs.append(s)
    concat(segs, out); return out

def concat(segments, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        for s in segments: f.write(f"file '{os.path.abspath(s)}'\n")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out]); return out

def selftest(outdir):
    """Manufacture a 12-s hook from ONE synthetic take + 6 stills using only edit-layer ops (no AI), then score it."""
    os.makedirs(outdir, exist_ok=True); fps, W, H = 24, 1920, 1080
    take = os.path.join(outdir, "take.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={W}x{H}:rate={fps}:duration=12", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", take])
    stills = []
    for i, c in enumerate(["0x8a2be2", "0x2fb8d6", "0xe0479e", "0xc9a227", "0x2e8b57", "0xd93b3b"]):
        p = os.path.join(outdir, f"still{i}.png"); run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={c}:size=1280x720", "-vf", f"drawtext=fontfile={FONT}:text='BAND {i+1}':fontsize=120:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2", "-frames:v", "1", p]); stills.append(p)
    # segment A 0-3.375: one take, snap punch-out 1.6x->1.0 at 1.375, name cards at 1.375 (lead 0.3), whiteout at the end (hides the cut into the stack)
    A = os.path.join(outdir, "A.mp4")
    vfA = ",".join([punch_in(1.6, 1.0, 1.375, 1.375, fps, W, H), text_pop("PIP / WENT SOLO", 1.375, 3.3, 0.3, 72, "h*0.80", "0xE0479E"), text_pop("GRUFF / GOT LEFT", 1.375, 3.3, 0.3, 72, "h*0.88", "0x2FB8D6"), whiteout(3.275, 0.10)])
    segment_from_take(take, 0.0, 3.375, vfA, A, fps, W, H)
    # segment B 3.375-5.9: the 6-photo stack (~0.42 s each with whiteouts between)
    B = photo_stack(stills, 0.42, os.path.join(outdir, "B.mp4"), fps, W, H)
    # segment C 5.9-12: same take resumed, split wipe substitute = whiteout at start, push-in 1.0->1.9 at 8.25 (over 0.35 s) then eased back by 10.0, "30 DAYS" leading VO at 8.25, flash+bloom on the money line at 11.5
    C = os.path.join(outdir, "C.mp4"); tC = lambda t: t - 5.9
    vfC = ",".join([whiteout(0.0, 0.08), punch_in(1.0, 1.9, tC(8.25), tC(8.6), fps, W, H), text_pop("30 DAYS", 8.25 - 5.9 + 0.3, tC(10.35), 0.3, 140, "h*0.40"), flash(tC(11.5), 0.08, 0.7), flash(tC(11.9), 0.06, 0.5), bloom(tC(11.5), 0.4, 0.25)])
    segment_from_take(take, 5.9, 12.0, vfC, C, fps, W, H)
    hook = os.path.join(outdir, "hook_edit_layer_demo.mp4"); concat([A, B, C], hook)
    # synthetic audio: pulses ~2.7/s so onset metrics are exercised (not a claim about real sound design)
    hooka = hook.replace(".mp4", "_a.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", hook, "-f", "lavfi", "-i", "sine=frequency=220:beep_factor=8:duration=12", "-af", "volume=0.5", "-c:v", "copy", "-c:a", "aac", "-shortest", hooka])
    print("demo hook:", hooka); return hooka

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest": selftest(sys.argv[2])
    else: print(__doc__)
