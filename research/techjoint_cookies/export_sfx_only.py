#!/usr/bin/env python3
"""SFX-only export of the cookies master for the channel owner's own edit:
same picture, audio = library SFX + Grok native foley ONLY (no VO, no music).

Reuses assemble_cookies' solver so every SFX lands on the same frame as the
master, then remuxes the new mix onto the existing master's video stream
(codec copy — picture untouched). Verifies its event times against the
master's *_timeline.json before rendering.

  venv/bin/python research/techjoint_cookies/export_sfx_only.py             # v3
  venv/bin/python research/techjoint_cookies/export_sfx_only.py --variant v2 --master output/techjoint_cookies/cookies_v2.mp4
"""
import argparse, importlib, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
import assemble_cookies as ac


def build_sfx_only_audio(tmp, shots, runtime):
    """The SFX + CLIP_AUDIO layers of assemble_cookies.build_audio, verbatim; VO and music dropped."""
    by_id = {s["id"]: s for s in shots}
    inputs, chains, mixes, n = [], [], [], 0
    # --- Grok native clip foley (identical to build_audio)
    for sid, spec in (ac.CLIP_AUDIO or {}).items():
        if sid not in by_id: continue
        gain, max_dur = (spec if isinstance(spec, (tuple, list)) else (spec, None))
        s = by_id[sid]
        dur = min(s["dur"], s["native"] - s["in"])
        if max_dur: dur = min(dur, max_dur)
        if dur <= 0.3: continue
        seg = os.path.join(tmp, f"clip_{sid}.wav")
        ac.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s['in']:.3f}", "-t", f"{dur:.3f}",
                "-i", os.path.join(ac.CLIPS, f"{s['src']}.mp4"), "-vn",
                "-af", "loudnorm=I=-18:TP=-2:LRA=9,aformat=sample_rates=48000:channel_layouts=stereo,"
                       f"afade=t=in:d=0.05,afade=t=out:st={max(0.0, dur-0.30):.3f}:d=0.30", seg])
        inputs += ["-i", seg]
        chains.append(f"[{n}:a]volume={gain:.2f},adelay={int(s['t0']*1000)}|{int(s['t0']*1000)}[a{n}]")
        mixes.append(f"[a{n}]"); n += 1
    # --- SFX events (identical to build_audio; GFX_SFX/POP_KEYS are empty in v2/v3)
    sfxp = ac.norm_sfx(tmp)
    events = []
    for sid, evs in ac.SFX_EVENTS.items():
        if sid not in by_id: continue
        for key, off, dur, gain in evs:
            if key not in sfxp: print(f"  !! missing sfx {key}"); continue
            t = by_id[sid]["t0"] + off
            if sid in ac.ASMR_HOLDS: gain = min(1.0, gain * 1.15)
            events.append((key, t, min(dur, by_id[sid]["dur"] - off + 0.4), gain))
    for key, t, dur, gain in events:
        inputs += ["-i", sfxp[key]]
        chains.append(f"[{n}:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0.0,dur-0.25):.3f}:d=0.25,"
                      f"volume={gain:.2f},adelay={int(t*1000)}|{int(t*1000)}[a{n}]"); mixes.append(f"[a{n}]"); n += 1
    graph = ";".join(chains) + ";" + "".join(mixes) + f"amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{runtime:.3f}," \
            f"alimiter=limit=0.95:attack=5:release=80[outa]"
    out = os.path.join(tmp, "sfx_mix.wav")
    ac.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[outa]", out])
    return out, events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="v3")
    ap.add_argument("--master", default=os.path.join(REPO, "output", "techjoint_cookies", "cookies_v3.mp4"))
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    cfg = importlib.import_module(f"cookies_{args.variant}_config")
    for k, v in cfg.OVERRIDES.items():
        setattr(ac, k, v)
    print(f"variant {args.variant}: {len(cfg.OVERRIDES)} overrides")

    words = ac.load_words()
    blocks = ac.vo_blocks(words)          # still needed: the timeline solver stretches shots to fit VO
    shots = ac.plan_shots()
    runtime = ac.solve_timeline(shots, blocks)
    print(f"solved runtime {runtime:.2f}s over {len(shots)} shots")

    # gate: our recomputed SFX times must match the shipped master's timeline JSON
    tl_path = os.path.splitext(args.master)[0] + "_timeline.json"
    master_events = json.load(open(tl_path))["sfx_events"]

    out = args.output or os.path.splitext(args.master)[0] + "_sfx_only.mp4"
    tmp = tempfile.mkdtemp(prefix="cookies_sfx_")
    try:
        audio, events = build_sfx_only_audio(tmp, shots, runtime)
        ours = [[k, round(t, 2), round(d, 2), g] for k, t, d, g in events]
        if ours != [list(e) for e in master_events]:
            raise SystemExit(f"TIMELINE MISMATCH vs {tl_path} — refusing to render.\nours:   {ours}\nmaster: {master_events}")
        print(f"  sfx timeline verified against {os.path.basename(tl_path)} ({len(events)} events)")
        ac.run(["ffmpeg", "-y", "-loglevel", "error", "-i", args.master, "-i", audio,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-movflags", "+faststart", out])
        stem = os.path.splitext(out)[0] + ".wav"
        shutil.copy(audio, stem)
        print(f"wrote {os.path.relpath(out, REPO)}  {ac.probe_dur(out):.2f}s (master {ac.probe_dur(args.master):.2f}s)")
        print(f"wrote {os.path.relpath(stem, REPO)} (bare SFX stem)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
