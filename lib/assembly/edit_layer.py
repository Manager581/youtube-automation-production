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

def photo_cards_overlay(stills, t_start, each, W=1920, H=1080, card_w=0.46, slide=0.12):
    """Reference grammar: archive stills SLIDE IN as cards over the RUNNING take (no full-frame cut), one every `each` s,
    alternating left/right, each card held until the next replaces it. Returns (extra_inputs, filter_chain_suffix)
    to append to an ffmpeg command whose base video is [0:v]. Cards register as transitions (th 0.1) but not hard cuts."""
    inputs, chain, prev = [], [], "0:v"
    cw = int(W * card_w); ch = int(cw * 9 / 16)
    for i, p in enumerate(stills):
        idx = i + 1; inputs += ["-loop", "1", "-t", f"{each*(len(stills)-i)+0.5:.3f}", "-i", p]
        t0 = t_start + i * each; t1 = t_start + (i + 1) * each + (0 if i == len(stills)-1 else 0.0)
        side = i % 2; x_end = int(W * 0.04) if side == 0 else W - cw - int(W * 0.04); x_start = -cw if side == 0 else W
        y = int(H * 0.12) + (i % 3) * int(H * 0.06)
        x_expr = f"if(lt(t,{t0+slide:.3f}),{x_start}+({x_end}-{x_start})*(t-{t0:.3f})/{slide},{x_end})"
        chain.append(f"[{idx}:v]scale={cw}:{ch},setpts=PTS-STARTPTS+{t0:.3f}/TB[c{idx}]")
        chain.append(f"[{prev}][c{idx}]overlay=x='{x_expr}':y={y}:enable='between(t,{t0:.3f},{t1+each:.3f})'[v{idx}]")
        prev = f"v{idx}"
    return inputs, ";".join(chain), prev

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
    # ONE continuous take 0-12 s: punch-out at 1.375, name cards, archive photos SLIDE IN as cards 3.5-5.9 over the take
    # (no full-frame cut), soft whiteouts at 3.4 / 8.0, push-in at 8.25 eased back, "30 DAYS" leading VO, flash+bloom at 11.5
    base = os.path.join(outdir, "base.mp4")
    vf = ",".join([punch_in(1.6, 1.0, 1.375, 1.375, fps, W, H), text_pop("PIP / WENT SOLO", 1.375, 3.3, 0.3, 72, "h*0.80", "0xE0479E"), text_pop("GRUFF / GOT LEFT", 1.375, 3.3, 0.3, 72, "h*0.88", "0x2FB8D6"), whiteout(3.375, 0.08), whiteout(8.0, 0.08), text_pop("30 DAYS", 8.25 + 0.3, 10.35, 0.3, 140, "h*0.40"), flash(11.5, 0.08, 0.7), flash(11.9, 0.06, 0.5), bloom(11.5, 0.4, 0.25)])
    segment_from_take(take, 0.0, 12.0, vf, base, fps, W, H)
    ins, chain, last = photo_cards_overlay(stills, 3.5, 0.40, W, H)
    A = os.path.join(outdir, "A_cards.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", base] + ins + ["-filter_complex", chain, "-map", f"[{last}]", "-t", "12", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps), A])
    # second pass punch-in 8.25 must apply AFTER cards? cards end 5.9 — punch already baked in base (cards ride the zoomed take, as in the reference)
    B = C = None
    hook = os.path.join(outdir, "hook_edit_layer_demo.mp4"); concat([A], hook)
    # synthetic audio: pulses ~2.7/s so onset metrics are exercised (not a claim about real sound design)
    hooka = hook.replace(".mp4", "_a.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", hook, "-f", "lavfi", "-i", "sine=frequency=220:beep_factor=8:duration=12", "-af", "volume=0.5", "-c:v", "copy", "-c:a", "aac", "-shortest", hooka])
    print("demo hook:", hooka); return hooka

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest": selftest(sys.argv[2])
    else: print(__doc__)

# ---- TEXT v2 (Law 5): a DESIGNED text element — PIL-rendered PNG with stroke + shadow + keyword colour, animated scale-in with overshoot.
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
def text_png(text, out, size=140, color="#FFFFFF", key_color="#FFE433", stroke=10, shadow=12, font=IMPACT):
    """Render text to a transparent PNG. Words wrapped in {braces} take key_color. Returns path."""
    from PIL import Image, ImageDraw, ImageFont
    import re as _re
    fnt = ImageFont.truetype(font if os.path.exists(font) else FONT, size); parts = _re.findall(r"\{[^}]*\}|[^{]+", text)
    words = []
    for pt in parts:
        key = pt.startswith("{"); pt = pt.strip("{}")
        for wd in pt.split(" "):
            if wd: words.append((wd, key))
    space = fnt.getlength(" "); widths = [fnt.getlength(wd) for wd, _ in words]; W = int(sum(widths) + space * (len(words) - 1) + 2 * stroke + shadow + 8); H = int(size * 1.35 + 2 * stroke + shadow)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = stroke + 4; y = stroke
    for (wd, key), wdt in zip(words, widths):
        d.text((x + shadow, y + shadow), wd, font=fnt, fill=(0, 0, 0, 140))
        d.text((x, y), wd, font=fnt, fill=key_color if key else color, stroke_width=stroke, stroke_fill="#000000"); x += wdt + space
    im.save(out); return out
def text_pop2_filter(png_label, vid_label, out_label, t_on, t_off, lead=0.3, y="H*0.72", x="(W-w)/2", pop=1.18, rise=0.16, settle=0.30, shake=0.0):
    """filter_complex fragment: animated scale (overshoot) + overlay window. Text lands `lead` s BEFORE the word (t_on already includes it)."""
    on = t_on - lead
    sc = f"if(lt(t-{on:.3f},0),0.01,if(lt(t-{on:.3f},{rise}),0.55+{pop-0.55}*((t-{on:.3f})/{rise}),if(lt(t-{on:.3f},{settle}),{pop}-({pop}-1.0)*((t-{on:.3f}-{rise})/({settle}-{rise})),1.0)))"
    shk = f"+{shake}*sin(140*(t-{on:.3f}))*lt(t-{on:.3f},0.25)" if shake else ""
    return (f"[{png_label}]scale=w='iw*({sc})':h=-1:eval=frame[{png_label}s];"
            f"[{vid_label}][{png_label}s]overlay=x='{x}':y='{y}-h/2{shk}':enable='between(t,{on:.3f},{t_off:.3f})'[{out_label}]")
def text_pop2_selftest(outdir):
    os.makedirs(outdir, exist_ok=True); png = text_png("{30} DAYS", os.path.join(outdir, "t.png"), size=150); base = os.path.join(outdir, "base.mp4")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x202838:size=1920x1080:rate=24", "-t", "2", base])
    out = os.path.join(outdir, "text2.mp4"); fc = text_pop2_filter("1:v", "0:v", "out", 0.5, 1.8, lead=0.3, shake=6)
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", base, "-loop", "1", "-i", png, "-filter_complex", fc, "-map", "[out]", "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", out]); return out
