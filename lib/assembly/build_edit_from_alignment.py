#!/usr/bin/env python3
"""build_edit_from_alignment.py — Law 4: the edit is WORD-driven. Forced-aligns every placed VO line (whisperx, existing
run_forced_alignment), maps word times onto the timeline (placement t + word_start/tempo), then rewrites the edit spec:
  - text pops with an "anchor" word land `lead` s BEFORE that word (0.2-0.5 s, reference-measured);
  - every `emphasis` word in the lines manifest gets a punch-in on the segment that is on screen (z 1.0->1.12, 0.12 s);
  - reports ops-per-10 s density in the hook window vs the profile floor.
Usage: build_edit_from_alignment.py --spec S.json --mix M.json --lines VO_LINES_MANIFEST.json --out S_words.json [--lead 0.3] [--ops-floor 20]
Writes <out> and <out>.words.json (the alignment ledger, reused if present)."""
import argparse, json, os, sys
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(REPO, "scripts"))
def align_lines(mix, lines_dir, cache):
    if os.path.exists(cache): return json.load(open(cache))
    from realign_paper_edit import run_forced_alignment
    out = {}
    for v in mix["vo"]:
        lid = v["line"]; txt = os.path.join(lines_dir, lid + ".txt")
        if not os.path.exists(txt): open(txt, "w").write(v.get("text", ""))
        r = run_forced_alignment(v["file"], txt, device="cpu"); tp = float(v.get("tempo", 1.0))
        out[lid] = [{"word": w["word"], "t": round(v["t"] + w["start"] / tp, 3), "end": round(v["t"] + w["end"] / tp, 3)} for w in r["words"] if w.get("start") is not None]
    json.dump(out, open(cache, "w"), indent=1); return out
def norm(w): return "".join(c for c in w.lower() if c.isalnum())
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--spec", required=True); ap.add_argument("--mix", required=True); ap.add_argument("--lines", required=True); ap.add_argument("--out", required=True); ap.add_argument("--lead", type=float, default=0.3); ap.add_argument("--ops-floor", type=float, default=15.8); ap.add_argument("--hook", type=float, default=45.0);  # ops floor = 0.8 x the reference ledger (89 spec-equivalent ops / 45 s = 19.8 per 10 s)
    ap.add_argument("--ledger", help="CLIP_LEDGER.json: rows with subject_peaks let the builder slide each clip's in-point so the ACTION lands on the word (never stretch)"); ap.add_argument("--manifest", help="shot manifest (characters per shot)")
    a = ap.parse_args(); spec = json.load(open(a.spec)); mix = json.load(open(a.mix)); man = {l["id"]: l for l in json.load(open(a.lines))["lines"]}
    for v in mix["vo"]: v["text"] = man.get(v["line"], {}).get("text", "")
    words = align_lines(mix, os.path.dirname(a.lines), a.out + ".words.json")
    segs = spec["segments"]; seg_at = lambda t: next((s for s in segs if s["t_in"] <= t < s["t_out"]), None)
    anchored = 0; punches = 0; missing = []
    for sg in segs:
        for o in sg.get("ops", []):
            if o.get("op") in ("text", "text2") and o.get("anchor"):
                hit = next((w for lid in words for w in words[lid] if norm(w["word"]) == norm(o["anchor"])), None)
                if not hit: missing.append(o["anchor"]); continue
                tgt = seg_at(hit["t"]) or sg
                if tgt is not sg: sg["ops"].remove(o); tgt.setdefault("ops", []).append(o); o["moved_to"] = tgt["shot"]
                o["t_on"] = round(max(0.0, hit["t"] - a.lead - tgt["t_in"]), 3); o["t_off"] = round(min(tgt["t_out"] - tgt["t_in"], o["t_on"] + max(1.2, o.get("t_off", 0) - o.get("t_on", 0))), 3); o["word_t"] = hit["t"]; anchored += 1
    for lid, ws in words.items():
        emph = [norm(e) for e in man.get(lid, {}).get("emphasis", [])]
        for w in ws:
            if norm(w["word"]) in emph:
                sg = seg_at(w["t"])
                if not sg: continue
                sg.setdefault("ops", []).append({"op": "punch", "z0": 1.0, "z1": 1.12, "t0": round(max(0, w["t"] - 0.05 - sg["t_in"]), 3), "t1": round(max(0, w["t"] + 0.07 - sg["t_in"]), 3), "why": f"emphasis '{w['word']}'"}); punches += 1
    # ACTION ON THE WORD (Law 4, reference ledger 23.25/34.125/35.5 s: the clip's physical action lands ON the spoken word). i2v cannot
    # time the action internally, so the builder SLIDES the clip's in-point (t0) so a recorded subject-motion peak = the emphasis word onset.
    action_hits = []; action_miss = []
    if a.ledger and os.path.exists(a.ledger):
        led = json.load(open(a.ledger)).get("clips", {}); import subprocess as _sp
        def _dur(pth): return float(_sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", pth], capture_output=True, text=True).stdout.strip() or 0)
        for lid, ws in words.items():
            emph = [norm(e) for e in man.get(lid, {}).get("emphasis", [])]
            for w in ws:
                if norm(w["word"]) not in emph: continue
                sg = seg_at(w["t"]); row = led.get((sg or {}).get("split_of", (sg or {}).get("shot", "")).split("_")[0]) if sg else None
                peaks = (row or {}).get("subject_peaks") or []
                if not sg or not peaks or sg.get("action_locked"): continue
                slot = sg["t_out"] - sg["t_in"]; rel = w["t"] - sg["t_in"]; clip_len = _dur(row["clip"]) if os.path.exists(row.get("clip", "")) else 0
                cands = [(abs(pk - rel - sg.get("t0", 0.0)), pk - rel) for pk in peaks if 0.0 <= pk - rel and pk - rel + slot <= clip_len + 0.05]
                if not cands: action_miss.append((w["word"], sg["shot"])); continue
                _, t0 = min(cands); sg["t0"] = round(t0, 3); sg["action_locked"] = True; sg["action_on_word"] = {"word": w["word"], "word_t": w["t"], "clip_t0": round(t0, 3), "peak_abs": round(w["t"], 3)}; action_hits.append((w["word"], sg["shot"], round(t0, 2)))
    n_ops = sum(1 for s in segs if s["t_in"] < a.hook) + sum(len(s.get("ops", [])) for s in segs if s["t_in"] < a.hook)
    dens = n_ops / (min(a.hook, segs[-1]["t_out"]) / 10.0)
    spec["word_driven"] = {"anchored_text": anchored, "emphasis_punches": punches, "missing_anchors": missing, "hook_ops_per_10s": round(dens, 1), "floor": a.ops_floor, "action_on_word": action_hits, "action_unplaceable": action_miss, "verdict": "PASS" if dens >= a.ops_floor and not missing else "FAIL"}
    json.dump(spec, open(a.out, "w"), indent=1)
    print(f"word-driven edit: {anchored} text pops anchored to words, {punches} emphasis punch-ins, missing anchors {missing}; action-on-word placed {len(action_hits)} {action_hits[:4]} unplaceable {len(action_miss)}; hook ops/10s = {dens:.1f} (floor {a.ops_floor}) -> {spec['word_driven']['verdict']}")
if __name__ == "__main__": main()
