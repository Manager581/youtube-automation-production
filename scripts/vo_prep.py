#!/usr/bin/env python3
"""vo_prep.py — GATE 3 mechanics (ElevenLabs ONE-pass rule, subscriptions only, browser-driven).
  chunk  --lines script_lines.json --out DIR            per-voice chunks <=4800 chars, in script order, each with sha256;
                                                        writes VO_MANIFEST.json (voice, chunk, sha, text path, expected words)
  verify --manifest VO_MANIFEST.json --audio DIR        for every chunk: <audio>/<chunk_id>.mp3 exists, whisper transcript
                                                        word-overlap >= --min-overlap (default 0.85); exit 1 on any miss
The chunk text files are what gets pasted into the ElevenLabs textarea (SHA-verify the textarea before Generate).
"""
import argparse, hashlib, json, os, re, subprocess, sys
LIMIT = 4800
def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
def words(s): return re.findall(r"[a-z0-9']+", s.lower())
def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chunk"); c.add_argument("--lines", required=True); c.add_argument("--out", required=True)
    v = sub.add_parser("verify"); v.add_argument("--manifest", required=True); v.add_argument("--audio", required=True); v.add_argument("--min-overlap", type=float, default=0.85); v.add_argument("--model", default="base")
    a = ap.parse_args()
    if a.cmd == "chunk":
        lines = json.load(open(a.lines)); os.makedirs(a.out, exist_ok=True); man = {"limit": LIMIT, "chunks": []}; buf = {}; order = []
        for ln in lines:
            spk = ln.get("speaker", "?").upper(); txt = ln.get("text", "").strip()
            if not txt: continue
            if spk not in buf: buf[spk] = []; order.append(spk)
            buf[spk].append(txt)
        for spk in order:
            cur, idx = "", 1
            def flush():
                nonlocal cur, idx
                if not cur.strip(): return
                cid = f"{spk}_{idx:02d}"; p = os.path.join(a.out, cid + ".txt"); open(p, "w").write(cur.strip() + "\n")
                man["chunks"].append({"id": cid, "voice": spk, "chars": len(cur.strip()), "sha": sha(cur.strip()), "text": p, "words": len(words(cur))}); cur = ""; idx += 1
            for t in buf[spk]:
                if len(cur) + len(t) + 1 > LIMIT: flush()
                cur += t + "\n"
            flush()
        json.dump(man, open(os.path.join(a.out, "VO_MANIFEST.json"), "w"), indent=1)
        tot = sum(c["chars"] for c in man["chunks"]); print(f"vo_prep: {len(man['chunks'])} chunks, {tot} chars, voices={order} -> {a.out}/VO_MANIFEST.json")
        for c in man["chunks"]: print(f"  {c['id']}: {c['chars']} chars, {c['words']} words, sha {c['sha']}")
        return 0
    man = json.load(open(a.manifest)); fails = []
    for c in man["chunks"]:
        mp3 = os.path.join(a.audio, c["id"] + ".mp3"); txt = open(c["text"]).read().strip()
        if sha(txt) != c["sha"]: fails.append(f"{c['id']}: text file changed since lock (sha)"); continue
        if not os.path.exists(mp3): fails.append(f"{c['id']}: audio missing ({mp3})"); continue
        r = subprocess.run([os.path.join(os.path.dirname(sys.executable), "whisper"), mp3, "--model", a.model, "--output_format", "txt", "--output_dir", a.audio, "--fp16", "False"], capture_output=True, text=True)
        tp = os.path.splitext(mp3)[0] + ".txt"
        if not os.path.exists(tp): fails.append(f"{c['id']}: whisper produced no transcript ({r.stderr[-120:]})"); continue
        got = set(words(open(tp).read())); exp = words(txt); ov = sum(1 for w in exp if w in got) / max(1, len(exp))
        print(f"  {'PASS' if ov >= a.min_overlap else 'FAIL'} {c['id']}: word overlap {ov:.2f}")
        if ov < a.min_overlap: fails.append(f"{c['id']}: overlap {ov:.2f} < {a.min_overlap}")
    for f in fails: print("  FAIL", f)
    print("vo_prep verify: " + ("PASS" if not fails else f"FAIL ({len(fails)})")); return 1 if fails else 0
if __name__ == "__main__": sys.exit(main())
