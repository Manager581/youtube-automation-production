#!/usr/bin/env python3
"""lib/assembly/audio_mix.py — config-driven audio mix for the shared assembly path (plan S6/S7).
MIX SPEC (JSON): {"duration": 60.0,
  "vo":    [{"file": "L01.mp3", "t": 0.0, "gain_db": 0, "tempo": 1.1}],   # lines at absolute seconds; optional pitch-preserving tempo
  "foley": [{"file": "S001.flac", "t": 0.0, "gain_db": -8, "dur": 2.0}],   # generated foley per segment window (trimmed to dur)
  "sfx":   [{"file": "hit.wav", "t": 11.5, "gain_db": -6}],        # optional library hits
  "music": {"file": "bed.mp3", "gain_db": -16, "duck_db": -8,      # bed; ducked under the VO bus (sidechain)
            "sections": [{"t0": 0, "t1": 30, "gain_db": 0}, {"t0": 30, "t1": 39, "gain_db": -60}]},   # section automation
  "target_lufs": -14, "true_peak": -1.5}
Every op is plain ffmpeg (adelay/volume/amix/sidechaincompress/loudnorm). Usage: audio_mix.py SPEC.json OUT.wav  |  --selftest DIR
"""
import json, os, subprocess, sys, tempfile
def _vol(db): return f"volume={db}dB"
def build(spec, out, stems=True):
    dur = float(spec["duration"]); inputs = []; fc = []; idx = 0
    def add(path): 
        nonlocal idx; inputs.extend(["-i", path]); idx += 1; return idx - 1
    buses = {}
    for bus in ("vo", "foley", "sfx", "ambience"):
        labels = []
        for k, it in enumerate(spec.get(bus, [])):
            i = add(it["file"]); ms = int(round(float(it["t"]) * 1000)); trim = f"atrim=0:{float(it['dur']):.3f}," if it.get("dur") else ""
            tempo = f"atempo={float(it['tempo']):.4f}," if it.get("tempo") and abs(float(it["tempo"]) - 1.0) > 1e-3 else ""   # pitch-preserving pace change (0.5-2.0)
            loop = f"aloop=loop=-1:size=2e9," if it.get("loop") else ""   # ambience beds loop to fill their window
            fc.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,{loop}{tempo}{trim}{_vol(it.get('gain_db',0))},adelay={ms}|{ms}[{bus}{k}]"); labels.append(f"[{bus}{k}]")
        if labels:
            fc.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0:normalize=0,apad=whole_dur={dur:.3f},atrim=0:{dur:.3f}[{bus}]"); buses[bus] = f"[{bus}]"
    m = spec.get("music"); raw_label = None
    if m:
        i = add(m["file"]); expr = "1"
        for s in m.get("sections", []): expr = f"if(between(t,{float(s['t0']):.3f},{float(s['t1']):.3f}),{10**(float(s['gain_db'])/20):.6f},{expr})"
        chain = f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,atrim=0:{dur:.3f},apad=whole_dur={dur:.3f},{_vol(m.get('gain_db',-16))},volume='{expr}':eval=frame"
        if "vo" in buses and m.get("duck_db"):
            fc.append(chain + "[mraw0]"); fc.append("[mraw0]asplit=2[mraw][mraw_st]"); raw_label = "[mraw_st]"; fc.append("[vo]asplit=2[vo][vosc]")
            ratio = 8; thr = 0.05
            fc.append(f"[{ratio and 'mraw'}][vosc]sidechaincompress=threshold={thr}:ratio={ratio}:attack=20:release=400:makeup=1[music]")
        else: fc.append(chain + "[music]")
        buses["music"] = "[music]"
    # STEMS: split every bus so ONE ffmpeg run writes the mix AND per-bus stems (+ nonvo, + pre-duck music_raw). Stems are
    # pre-loudnorm; the watch gate measures the RENDERED buses (levels, holes, hits, coverage), never the spec.
    outs = []; base = os.path.splitext(out)[0]; stem_paths = {}
    if stems:
        non = []
        for bus, lab in list(buses.items()):
            n = lab.strip("[]"); fc.append(f"{lab}asplit=3[{n}][{n}_st][{n}_nv]"); p = f"{base}_stem_{bus}.wav"; outs += ["-map", f"[{n}_st]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", p]; stem_paths[bus] = p
            if bus != "vo": non.append(f"[{n}_nv]")
            else: fc.append(f"[{n}_nv]anullsink")
        if non: fc.append("".join(non) + f"amix=inputs={len(non)}:duration=longest:dropout_transition=0:normalize=0[nonvo]"); p = f"{base}_stem_nonvo.wav"; outs += ["-map", "[nonvo]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", p]; stem_paths["nonvo"] = p
        if raw_label: p = f"{base}_stem_music_raw.wav"; outs += ["-map", raw_label, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", p]; stem_paths["music_raw"] = p
    elif raw_label: fc.append(f"{raw_label}anullsink")
    labels = list(buses.values())
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0:normalize=0,loudnorm=I={spec.get('target_lufs',-14)}:TP={spec.get('true_peak',-1.5)}:LRA=11,atrim=0:{dur:.3f}[out]")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs + ["-filter_complex", ";".join(fc), "-map", "[out]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", out] + outs
    subprocess.run(cmd, check=True)
    if stems:
        rep = {"mix": out, "mix_sha": _sha(out), "spec_sha": _sha_obj(spec), "buses": sorted(buses), "stems": {k: {"path": v, "sha": _sha(v)} for k, v in stem_paths.items()}, "duration": dur}
        json.dump(rep, open(base + "_mix_report.json", "w"), indent=1)
    return out
def _sha(p):
    import hashlib; h = hashlib.sha256(); h.update(open(p, "rb").read()); return h.hexdigest()
def _sha_obj(o):
    import hashlib; return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()
def buses_of(spec): return sorted(b for b in ("vo", "foley", "sfx", "ambience", "music") if spec.get(b))
def check_buses_kept(src_spec, dst_spec):
    """Fail closed when a rewrite (retime etc.) drops a bus the input had (v3 lost its whole design/sfx bus this way)."""
    lost = [b for b in buses_of(src_spec) if b not in buses_of(dst_spec)]
    if lost: raise SystemExit(f"audio_mix.check_buses_kept REFUSED: rewritten mix spec dropped bus(es) {lost}")
def selftest(d):
    os.makedirs(d, exist_ok=True)
    def tone(p, f, sec): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={f}:duration={sec}", "-ar", "48000", p], check=True)
    tone(f"{d}/vo.wav", 440, 2); tone(f"{d}/fo.wav", 200, 1); tone(f"{d}/mu.wav", 110, 12)
    spec = {"duration": 10.0, "vo": [{"file": f"{d}/vo.wav", "t": 3.0}], "foley": [{"file": f"{d}/fo.wav", "t": 1.0, "gain_db": -6, "dur": 1.0}], "music": {"file": f"{d}/mu.wav", "gain_db": -12, "duck_db": -8, "sections": [{"t0": 7, "t1": 10, "gain_db": -60}]}}
    build(spec, f"{d}/mix.wav")
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{d}/mix.wav"], capture_output=True, text=True).stdout.strip()
    print("selftest mix duration", r); return abs(float(r) - 10.0) < 0.1
if __name__ == "__main__":
    if sys.argv[1] == "--selftest": sys.exit(0 if selftest(sys.argv[2]) else 1)
    build(json.load(open(sys.argv[1])), sys.argv[2]); print("mixed", sys.argv[2])
