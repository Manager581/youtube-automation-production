#!/usr/bin/env python3
"""Assemble the TechJoint cookie video (1080p24) from:
  shots.json  (timeline + per-shot clip / reuse / durations)
  assets/techjoint_cookies/clips/Cxx.mp4   (Grok i2v, 1264x720, 6s; C28/C36 10s)
  audio/techjoint_cookies/narration.wav + narration.json (whisperx word timings)
  assets/techjoint_cookies/sfx/*.mp3  (Freesound CC0 + Pixabay)
  audio/techjoint_cookies/music/*.mp3 (Pixabay bed)
  assets/techjoint_cookies/gfx/*.png + gfx_manifest.json

Lineage: research/wildbirdsurvival_teardown/assemble_ep02.py (segment+concat, VO blocks at
timecodes, music envelope) + scripts/genesis_overlay_pass.py (timed overlays). The one new
idea here is the timeline SOLVER: each VO block is anchored to a shot; if the spoken block
runs longer than the shots between its anchor and the next anchor, those shots are
stretched (up to their native clip length, then a short freeze) so the VO never spills.

  venv/bin/python research/techjoint_cookies/assemble_cookies.py --preview   # 960x540
  venv/bin/python research/techjoint_cookies/assemble_cookies.py            # 1920x1080
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
SHOTS = os.path.join(HERE, "shots.json")
CLIPS = os.path.join(REPO, "assets", "techjoint_cookies", "clips")
SFX = os.path.join(REPO, "assets", "techjoint_cookies", "sfx")
GFX = os.path.join(REPO, "assets", "techjoint_cookies", "gfx")
NARR = os.path.join(REPO, "audio", "techjoint_cookies", "narration.wav")
NARR_JSON = os.path.join(REPO, "audio", "techjoint_cookies", "narration.json")
MUSIC = os.path.join(REPO, "audio", "techjoint_cookies", "music", "kitchen_sunlight_PaoloArgento.mp3")
FPS = 24

# ---- editorial overrides on top of shots.json -------------------------------------------
# hook flash-forwards: (source clip, in-point)
HOOK_SRC = {"H1": ("C33", 0.0), "H2": ("C29", 0.6), "H3": ("C31", 0.8), "H4": ("C34", 0.4),
            "H5": ("C35", 0.0), "H6": ("C35", 2.0)}
CLIP_IN = {"C12": 0.0}
DUR_OVERRIDE = {"C12": 3.5, "C13": 5.5}          # C12's yolk lands in the wrong bowl after 3.5 s
# VO blocks: (first-word anchor in transcript, anchor shot, lead-in seconds)
VO_BLOCKS = [("crispy", "H1", 0.25), ("here's", "C01", 0.4), ("rule", "C04", 0.4),
             ("both", "C09", 0.4), ("flour,", "C14", 0.4), ("now", "C18", 0.4),
             ("big", "C22", 0.4), ("375,", "C26", 0.4), ("okay,", "C33", 0.6), ("full", "C36", 0.6)]
GAP_AFTER_BLOCK = 0.45   # min silence before the next anchor shot

# SFX events: shot -> list of (sfx_key, offset_s, dur_s, gain)
SFX_EVENTS = {
    "H1": [("cookie_crunch", 0.0, 1.6, 0.7)], "H2": [("tray_rack", 0.0, 1.4, 0.5)],
    "H3": [("sprinkle", 0.1, 1.3, 0.6)], "H4": [("crisp_crunch", 0.0, 1.4, 0.7)],
    "C01": [("bowl_set", 1.2, 1.2, 0.45)], "C03": [("bowl_set", 0.4, 0.8, 0.4)],
    "C04": [("sizzle", 0.0, 5.0, 0.55)], "C05": [("sizzle", 0.0, 5.0, 0.6)],
    "C06": [("sizzle", 0.0, 6.0, 0.95)], "C07": [("pour_liquid", 0.3, 3.5, 0.6)],
    "C09": [("rice_pour", 0.2, 2.5, 0.55)], "C10": [("whisk", 0.0, 4.5, 0.7)],
    "C11": [("egg_crack", 0.5, 2.0, 0.8)], "C13": [("whisk", 0.8, 3.5, 0.5)],
    "C14": [("rice_pour", 0.2, 2.8, 0.5)], "C15": [("sprinkle", 0.3, 2.5, 0.6)],
    "C16": [("stir_bowl", 0.0, 6.0, 0.95)], "C17": [("stir_bowl", 0.0, 3.5, 0.55)],
    "C18": [("chop", 0.2, 4.5, 0.95)], "C19": [("rice_pour", 0.3, 1.8, 0.45)],
    "C20": [("stir_bowl", 0.0, 4.5, 0.6)], "C22": [("pop", 2.6, 0.5, 0.35)],
    "C23": [("tray_laydown", 0.8, 2.0, 0.45)], "C24": [("oven_door", 2.6, 2.2, 0.55)],
    "C25": [("tray_laydown", 0.0, 1.5, 0.4)], "C26": [("knob_spin", 0.4, 1.6, 0.6)],
    "C27": [("tray_rack", 0.0, 3.0, 0.7), ("oven_door", 3.4, 2.2, 0.6)],
    "C28": [("oven_fan", 0.0, 7.0, 0.3)], "C29": [("tray_rack", 0.0, 3.0, 0.7)],
    "C30": [("tray_foley", 0.3, 1.5, 0.9)], "C31": [("sprinkle", 0.2, 2.2, 0.8)],
    "C33": [("cookie_crunch", 0.0, 2.2, 0.85)], "C34": [("crisp_crunch", 0.1, 1.6, 0.9)],
}
# on-screen graphics: (gfx_key, anchor shot, offset_s, dur_s)   ("@word" offsets resolve to VO word time)
GFX_EVENTS = [
    ("title", "H6", 0.0, "end_of_shot"),
    ("ing_butter", "C01", "@butter", "end_of_ing"), ("ing_brown", "C01", "@brown", "end_of_ing"), ("ing_white", "C01", "@white", "end_of_ing"),
    ("ing_egg", "C01", "@egg", "end_of_ing"), ("ing_vanilla", "C01", "@vanilla", "end_of_ing"), ("ing_flour", "C01", "@flour", "end_of_ing"),
    ("ing_soda", "C01", "@baking", "end_of_ing"), ("ing_choc", "C02", "@way", "end_of_ing"),
    ("rule1", "C04", 0.3, 4.0), ("toffee", "C06", 2.0, 3.0), ("cool10", "C08", 0.3, 4.0),
    ("c_brown", "C09", 0.3, 3.2), ("c_white", "C09", 1.6, 2.0),
    ("rule2", "C12", 0.2, 3.5), ("yolk", "C12", 0.8, 3.0),
    ("c_flour", "C14", 0.3, 3.0), ("c_soda", "C15", 0.3, 3.0), ("stop", "C17", 0.3, 3.2),
    ("c_choc", "C19", 0.3, 3.0), ("scoop", "C22", 0.4, 3.5), ("rule3", "C23", 0.3, 4.0),
    ("chill30", "C24", 0.3, 3.5), ("chill_done", "C25", 0.2, 2.6), ("temp", "C26", 0.3, 3.4),
    ("bake", "C28", 0.5, 5.5), ("rest", "C32", 0.3, 3.4),
    ("crispy", "C34", 0.3, 2.4), ("gooey", "C35", 0.3, 2.4), ("card", "C36", 0.3, "end_of_shot"),
]
GFX_SFX = {"title": ("whoosh", 0.8), "crispy": ("pop", 0.5), "gooey": ("pop", 0.5)}
POP_KEYS = {"ing_butter", "ing_brown", "ing_white", "ing_egg", "ing_vanilla", "ing_flour", "ing_soda", "ing_choc",
            "c_brown", "c_white", "yolk", "c_flour", "c_soda", "stop", "c_choc", "scoop", "temp", "rest", "toffee"}
ASMR_HOLDS = {"C06", "C16", "C18", "C33"}   # music dips, SFX foreground
MUSIC_BASE, MUSIC_DIP, MUSIC_CARD = 0.16, 0.10, 0.34
GFX_SLIDE = 18   # px slide-up on graphic pop-in (0 = fade only)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + " ".join(cmd[:14]) + " ...\n" + r.stderr[-2000:])
    return r


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except ValueError: return 0.0


# ---------------------------------------------------------------------------------------
def load_words():
    d = json.load(open(NARR_JSON))
    return [w for s in d["segments"] for w in s.get("words", []) if "start" in w]


def vo_blocks(words):
    """Return list of dicts {anchor_shot, lead, t0, t1, words:[...]} in narration time."""
    idx, blocks = 0, []
    starts = []
    for anchor, shot, lead in VO_BLOCKS:
        a = anchor.lower().strip(" ,.")
        j = next(k for k in range(idx, len(words)) if words[k]["word"].lower().strip(" ,.?!…") == a)
        starts.append((j, shot, lead)); idx = j + 1
    for n, (j, shot, lead) in enumerate(starts):
        k = starts[n + 1][0] if n + 1 < len(starts) else len(words)
        ws = words[j:k]
        blocks.append({"shot": shot, "lead": lead, "t0": max(0.0, ws[0]["start"] - 0.12),
                       "t1": ws[-1]["end"] + 0.25, "words": ws})
    return blocks


def plan_shots():
    d = json.load(open(SHOTS))
    shots = []
    for s in d["shots"]:
        sid = s["id"]
        if sid in HOOK_SRC:
            src, cin = HOOK_SRC[sid]
        else:
            src, cin = sid, CLIP_IN.get(sid, 0.0)
        dur = DUR_OVERRIDE.get(sid, s["dur_s"])
        shots.append({"id": sid, "src": src, "in": cin, "planned": float(dur), "dur": float(dur),
                      "native": probe_dur(os.path.join(CLIPS, f"{src}.mp4")), "act": s["act"]})
    return shots


def solve_timeline(shots, blocks):
    """Stretch shots so each VO block fits between its anchor and the next anchor."""
    order = [s["id"] for s in shots]
    pos = {s["id"]: i for i, s in enumerate(shots)}
    for n, b in enumerate(blocks):
        i0 = pos[b["shot"]]
        i1 = pos[blocks[n + 1]["shot"]] if n + 1 < len(blocks) else len(shots)
        need = b["lead"] + (b["t1"] - b["t0"]) + GAP_AFTER_BLOCK
        span = shots[i0:i1]
        have = sum(s["dur"] for s in span)
        if need > have + 1e-6:
            extra = need - have
            # grow proportionally, capped at the native clip length (minus in-point)
            room = [max(0.0, (s["native"] - s["in"]) - s["dur"]) for s in span]
            total_room = sum(room)
            if total_room > 0:
                for s, r in zip(span, room):
                    s["dur"] += extra * min(1.0, r / total_room) if total_room >= extra else r
            have2 = sum(s["dur"] for s in span)
            if need > have2 + 1e-6:
                span[-1]["dur"] += need - have2          # freeze-extend the last shot of the span
                span[-1]["freeze"] = need - have2
    t = 0.0
    for s in shots:
        s["t0"] = t; t += s["dur"]; s["t1"] = t
    return t


def make_segment(s, out, scale, crf):
    w, h = scale
    clip = os.path.join(CLIPS, f"{s['src']}.mp4")
    have = s["native"]; want = s["dur"]; start = s["in"]
    avail = have - start
    if avail >= want - 0.02:
        vf = (f"trim={start:.3f}:{start + want:.3f},setpts=PTS-STARTPTS,scale={w}:{h}:flags=lanczos,"
              f"unsharp=5:5:0.35,fps={FPS},format=yuv420p")
    else:
        pad = want - avail
        vf = (f"trim={start:.3f}:{have:.3f},setpts=PTS-STARTPTS,scale={w}:{h}:flags=lanczos,unsharp=5:5:0.35,"
              f"fps={FPS},tpad=stop_mode=clone:stop_duration={pad:.3f},format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip, "-an", "-vf", vf, "-t", f"{want:.3f}",
         "-c:v", "libx264", "-crf", str(crf), "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS), out])


def norm_sfx(tmp):
    """Loudness-normalise every SFX once (I=-18) into tmp; returns key->path."""
    out = {}
    for f in sorted(os.listdir(SFX)):
        if not f.endswith(".mp3"): continue
        k = f[:-4]; p = os.path.join(tmp, f"sfx_{k}.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(SFX, f),
             "-af", "loudnorm=I=-18:TP=-2:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo", p])
        out[k] = p
    return out


def build_audio(tmp, shots, blocks, runtime, word_time):
    by_id = {s["id"]: s for s in shots}
    # --- VO: normalise once, then cut blocks and place them
    vo_norm = os.path.join(tmp, "vo_norm.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", NARR,
         "-af", "loudnorm=I=-15:TP=-1.5:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo", vo_norm])
    inputs, chains, mixes, n = [], [], [], 0
    vo_place = []
    for b in blocks:
        s = by_id[b["shot"]]; at = s["t0"] + b["lead"]
        b["at"] = at
        seg = os.path.join(tmp, f"vo_{b['shot']}.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", vo_norm, "-af",
             f"atrim={b['t0']:.3f}:{b['t1']:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,afade=t=out:st={b['t1']-b['t0']-0.08:.3f}:d=0.08", seg])
        inputs += ["-i", seg]
        chains.append(f"[{n}:a]adelay={int(at*1000)}|{int(at*1000)}[a{n}]"); mixes.append(f"[a{n}]"); n += 1
        vo_place.append((b["shot"], round(at, 2), round(at + b["t1"] - b["t0"], 2)))
    # --- SFX events
    sfxp = norm_sfx(tmp)
    events = []
    for sid, evs in SFX_EVENTS.items():
        if sid not in by_id: continue
        for key, off, dur, gain in evs:
            if key not in sfxp: print(f"  !! missing sfx {key}"); continue
            t = by_id[sid]["t0"] + off
            if sid in ASMR_HOLDS: gain = min(1.0, gain * 1.15)
            events.append((key, t, min(dur, by_id[sid]["dur"] - off + 0.4), gain))
    for key, sid, off, dur in GFX_EVENTS:
        if key in GFX_SFX:
            k2, g = GFX_SFX[key]; t = by_id[sid]["t0"] + (off if not isinstance(off, str) else 0.0)
            events.append((k2, t, 1.0, g))
        elif key in POP_KEYS:
            t = word_time(off) if isinstance(off, str) else by_id[sid]["t0"] + off
            events.append(("pop", t, 0.5, 0.3))
    for key, t, dur, gain in events:
        inputs += ["-i", sfxp[key]]
        chains.append(f"[{n}:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0.0,dur-0.25):.3f}:d=0.25,"
                      f"volume={gain:.2f},adelay={int(t*1000)}|{int(t*1000)}[a{n}]"); mixes.append(f"[a{n}]"); n += 1
    # --- music bed with envelope: low under VO, dip in ASMR holds, up on the recipe card
    card = by_id["C36"]; dip = [(by_id[k]["t0"], by_id[k]["t1"]) for k in ASMR_HOLDS if k in by_id]
    env = f"{MUSIC_BASE}"
    for a, bb in dip:
        env = f"if(between(t\\,{a:.2f}\\,{bb:.2f})\\,{MUSIC_DIP}\\,{env})"
    env = f"if(gte(t\\,{card['t0']:.2f})\\,{MUSIC_CARD}\\,{env})"
    env = f"if(gte(t\\,{runtime-2.0:.2f})\\,{MUSIC_CARD}*({runtime:.2f}-t)/2.0\\,{env})"
    inputs += ["-stream_loop", "-1", "-i", MUSIC]
    chains.append(f"[{n}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                  f"loudnorm=I=-20:TP=-2:LRA=11,atrim=0:{runtime:.3f},asetpts=PTS-STARTPTS,"
                  f"volume=eval=frame:volume='{env}'[a{n}]"); mixes.append(f"[a{n}]"); n += 1
    graph = ";".join(chains) + ";" + "".join(mixes) + f"amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{runtime:.3f}," \
            f"alimiter=limit=0.95:attack=5:release=80[outa]"
    out = os.path.join(tmp, "mix.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[outa]", out])
    return out, vo_place, events


def overlay_pass(video_in, video_out, shots, word_time, crf, scale):
    man = json.load(open(os.path.join(GFX, "gfx_manifest.json")))
    by_id = {s["id"]: s for s in shots}
    sx = scale[0] / 1920.0
    inputs = ["-i", video_in]; chain = []; prev = "[0:v]"; k = 1
    for key, sid, off, dur in GFX_EVENTS:
        g = man[key]; s = by_id[sid]
        t0 = word_time(off) if isinstance(off, str) else s["t0"] + off
        if dur == "end_of_shot": d = s["t1"] - t0 - (0.25 if key == "title" else 0.0)
        elif dur == "end_of_ing": d = by_id["C03"]["t0"] - 0.2 - t0
        else: d = float(dur)
        if d <= 0.4: continue
        gw, gh = int(g["w"] * sx), int(g["h"] * sx); gx, gy = int(g["x"] * sx), int(g["y"] * sx)
        fin, fout = 0.28, 0.3
        inputs += ["-loop", "1", "-t", f"{d:.3f}", "-i", os.path.join(REPO, g["file"])]
        chain.append(f"[{k}:v]scale={gw}:{gh},format=rgba,fade=t=in:st=0:d={fin}:alpha=1,"
                     f"fade=t=out:st={max(0.0,d-fout):.3f}:d={fout}:alpha=1,setpts=PTS+{t0:.3f}/TB[g{k}]")
        # pop-in: slide up 18px over the fade-in
        yexpr = f"{gy}+{GFX_SLIDE}*(1-min(1\\,(t-{t0:.3f})/{fin}))"
        chain.append(f"{prev}[g{k}]overlay=x={gx}:y='{yexpr}':enable='between(t\\,{t0:.3f}\\,{t0+d:.3f})'[v{k}]")
        prev = f"[v{k}]"; k += 1
    graph = ";".join(chain)
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", prev,
         "-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), video_out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=os.path.join(REPO, "output", "techjoint_cookies", "cookies_v1.mp4"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--no-gfx", action="store_true")
    ap.add_argument("--variant", default=None, help="e.g. v2 -> loads cookies_v2_config.OVERRIDES")
    args = ap.parse_args()
    if args.variant:
        import importlib
        cfg = importlib.import_module(f"cookies_{args.variant}_config")
        globals().update(cfg.OVERRIDES)
        print(f"variant {args.variant}: {len(cfg.OVERRIDES)} overrides")
    scale = (960, 540) if args.preview else (1920, 1080)

    words = load_words()
    blocks = vo_blocks(words)
    shots = plan_shots()
    runtime = solve_timeline(shots, blocks)

    by_id = {s["id"]: s for s in shots}
    for b in blocks: b["at"] = by_id[b["shot"]]["t0"] + b["lead"]
    def word_time(tag):
        """'@word' -> ABSOLUTE timeline seconds of that VO word (first match in block order)."""
        w = tag[1:].lower()
        for b in blocks:
            for ww in b["words"]:
                if ww["word"].lower().strip(" ,.?!…") == w:
                    return b["at"] + (ww["start"] - b["t0"])
        raise KeyError(tag)

    print(f"runtime {runtime:.2f}s over {len(shots)} shots; VO blocks: {len(blocks)}")
    tmp = tempfile.mkdtemp(prefix="cookies_asm_")
    try:
        listfile = os.path.join(tmp, "segs.txt")
        with open(listfile, "w") as lf:
            for i, s in enumerate(shots):
                seg = os.path.join(tmp, f"{i:03d}_{s['id']}.mp4")
                make_segment(s, seg, scale, args.crf if not args.preview else 23)
                lf.write(f"file '{seg}'\n")
        silent = os.path.join(tmp, "video.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", silent])
        print("  video concat ok")
        audio, vo_place, events = build_audio(tmp, shots, blocks, runtime, word_time)
        print("  audio mix ok")
        vid = silent
        if not args.no_gfx:
            vid = os.path.join(tmp, "video_gfx.mp4")
            overlay_pass(silent, vid, shots, word_time, args.crf if not args.preview else 23, scale)
            print("  overlay pass ok")
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", audio, "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", args.output])
        dur = probe_dur(args.output)
        rep = {"runtime": runtime, "output_dur": dur, "shots": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()} for s in shots],
               "vo_blocks": [{"shot": b["shot"], "at": round(b["at"], 2), "len": round(b["t1"] - b["t0"], 2)} for b in blocks],
               "sfx_events": [(k, round(t, 2), round(d, 2), g) for k, t, d, g in events]}
        json.dump(rep, open(os.path.splitext(args.output)[0] + "_timeline.json", "w"), indent=1)
        print(f"wrote {os.path.relpath(args.output, REPO)}  {dur:.2f}s (solved runtime {runtime:.2f}s)")
        for s in shots:
            flag = f"  +{s['dur']-s['planned']:.1f}s" if s["dur"] > s["planned"] + 0.05 else ""
            print(f"   {s['id']:<4} {s['t0']:7.2f} → {s['t1']:7.2f}  {s['dur']:.2f}s{flag}{'  FREEZE %.1fs' % s['freeze'] if s.get('freeze') else ''}")
        for sh, a, b in vo_place: print(f"   VO {sh}: {a} → {b}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
