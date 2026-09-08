#!/usr/bin/env python3
"""build_composite_seeds.py — per-shot COMPOSITE SEEDS from the locked masters (SUBJECT LOCK made
mechanical): character master → cutout (reuses scripts/make_cutout.py / rembg) → placed on the shot's
set or planet master; writes <out>/<composite_seed_id>.png + .json provenance (master paths + sha256).
No character is ever generated fresh: every seed derives from the hashed masters.
Usage: build_composite_seeds.py --manifest shot_manifest.json --masters DIR --out DIR [--only C001,C002]
Masters dir must hold <master_id>.png for every id in the manifest's seed_masters.
Layout: characters are placed left→right in listing order, scaled by CHAR_H (fraction of frame height).
"""
import argparse, hashlib, json, os, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); CHAR_H = {"PIP": 0.38, "GRUFF": 0.80, "ORB": 0.22, "COUNT": 0.16}
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def kind_of(mid, masters): return next((m.get("kind") for m in masters if m.get("id") == mid), None)
def cutout(master_png, cache_dir):
    os.makedirs(cache_dir, exist_ok=True); out = os.path.join(cache_dir, os.path.basename(master_png).replace(".png", "_cut.png"))
    if not os.path.exists(out):
        r = subprocess.run([sys.executable, os.path.join(HERE, "make_cutout.py"), master_png, out], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out): raise RuntimeError(f"cutout failed for {master_png}: {r.stderr[-300:]}")
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", required=True); ap.add_argument("--masters", required=True); ap.add_argument("--out", required=True); ap.add_argument("--only"); ap.add_argument("--size", default="1920x1080")
    a = ap.parse_args(); m = json.load(open(a.manifest)); W, H = map(int, a.size.split("x")); os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None; done = {}; fails = []
    for s in m["shots"]:
        cid = s.get("composite_seed_id")
        if not cid or cid in done or (only and cid not in only): continue
        refs = s.get("seed_masters", []); chars = [r for r in refs if kind_of(r, m["seed_masters"]) == "character"]
        bgs = [r for r in refs if kind_of(r, m["seed_masters"]) in ("set", "planet")]
        try:
            if not bgs: raise RuntimeError("no set/planet master in seed_masters")
            bg_path = os.path.join(a.masters, bgs[0] + ".png"); bg = Image.open(bg_path).convert("RGBA").resize((W, H)); prov = {"masters": {}}
            for r in refs:
                p = os.path.join(a.masters, r + ".png")
                if not os.path.exists(p): raise RuntimeError(f"master missing: {p}")
                prov["masters"][r] = sha(p)
            for i, r in enumerate(chars):
                who = next((c for c in CHAR_H if r.upper().find(c) >= 0), None); frac = CHAR_H.get(who, 0.5)
                cut = Image.open(cutout(os.path.join(a.masters, r + ".png"), os.path.join(a.out, "_cutouts"))).convert("RGBA")
                h = int(H * frac); w = int(cut.width * h / cut.height); cut = cut.resize((w, h))
                x = int(W * (0.18 + 0.64 * (i / max(1, len(chars) - 1)) if len(chars) > 1 else 0.5) - w // 2); y = int(H * 0.92) - h
                bg.alpha_composite(cut, (max(0, x), max(0, y)))
            out = os.path.join(a.out, cid + ".png"); bg.convert("RGB").save(out); prov.update({"composite": cid, "shot": s.get("id"), "sha": sha(out)})
            json.dump(prov, open(out.replace(".png", ".json"), "w"), indent=1); done[cid] = out
        except Exception as e: fails.append(f"{cid}: {e}")
    print(f"composites: {len(done)} built, {len(fails)} failed")
    for f in fails: print("  FAIL", f)
    sys.exit(1 if fails else 0)
if __name__ == "__main__": main()
