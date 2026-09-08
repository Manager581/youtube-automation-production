#!/usr/bin/env python3
"""render_review_packet.py — S8 story-tier packet (deterministic half): for every manifest shot, cut the RENDER at that
shot's window into an 8 fps filmstrip and label it with what the plan says should be there (beat, description, characters,
planet size, loop tags). The in-session vision pass then answers ONE question per tile — does the planned beat appear in
its window? — and records it via scripts/clip_bank.py-style verdicts into <out>/story_verdicts.json (PENDING rows created).
Usage: render_review_packet.py --manifest M.json --render preview.mp4 --out DIR [--fps 8] [--cols 6]
"""
import argparse, json, os, subprocess, sys
def tc(s):
    m, sec = s.split(":"); return int(m) * 60 + float(sec)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True); ap.add_argument("--render", required=True); ap.add_argument("--out", required=True); ap.add_argument("--fps", type=int, default=8); ap.add_argument("--cols", type=int, default=6)
    a = ap.parse_args(); m = json.load(open(a.manifest)); os.makedirs(a.out, exist_ok=True); tiles = []; labels = []; verdicts = {}
    for s in sorted(m["shots"], key=lambda s: tc(s["t_in"])):
        t0, t1 = tc(s["t_in"]), tc(s["t_out"]); n = max(1, int((t1 - t0) * a.fps + 0.999)); rows = max(1, (n + 7) // 8)
        tile = os.path.join(a.out, f"{s['id']}_strip.jpg")
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t0:.3f}", "-t", f"{t1-t0:.3f}", "-i", a.render, "-vf", f"fps={a.fps},scale=200:-1,tile=8x{rows}", "-frames:v", "1", tile], capture_output=True, text=True)
        if r.returncode != 0: print(f"  FAIL {s['id']}: {r.stderr[-120:]}"); continue
        tiles.append(tile); lab = f"{s['id']} {s.get('beat','')} {s['t_in']}-{s['t_out']} | {','.join(s.get('characters',[]))} | {s.get('planet_m','?')}m | {' '.join(s.get('loops',[]))}"; labels.append(lab)
        verdicts[s["id"]] = {"expected": (s.get("i2v_prompt") or s.get("vantage") or "")[:200], "window": [s["t_in"], s["t_out"]], "strip": tile, "verdict": "PENDING"}
    if tiles: subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "contact_sheet.py"), os.path.join(a.out, "STORY_PACKET.jpg")] + tiles + ["--cols", str(a.cols), "--tile", "300", "--labels", ",".join(l.replace(",", ";") for l in labels)], check=True)
    json.dump(verdicts, open(os.path.join(a.out, "story_verdicts.json"), "w"), indent=1)
    print(f"packet: {len(tiles)} shot strips + STORY_PACKET.jpg + story_verdicts.json ({len(verdicts)} PENDING) in {a.out}")
if __name__ == "__main__": main()
