#!/usr/bin/env python
"""
SELF-VERIFY. Reads VO_SCRIPT_LUKE_REVOICE.md and vo_manifest_v2.json BACK OFF DISK and
re-derives every hash from scratch. Trusts nothing from the build step.

Checks:
  C1  every line's sha256 == sha256(its exact_text)                       (manifest internal)
  C2  every pass's sha256_paste_text == sha256(its paste_text)            (manifest internal)
  C3  every pass's paste_text is exactly its lines joined by the break tag (composition)
  C4  the .md's fenced paste block for each pass hashes to the SAME value (md <-> json)
  C5  every exact_text round-trips back to the TSV under the declared normalizations
  C6  cold-open + GF passes still carry the v1 locked SHAs                (no regression)
  C7  no curly quotes anywhere in any paste text
"""
import csv
import hashlib
import json
import re
import sys

ROOT = "/Users/jefflawrence/Documents/youtube-automation-production"
EP = f"{ROOT}/dinoverse_clone/episode_01_omega_rex"
BASE = f"{EP}/v2/work/vo_prep"
BREAK = '<break time="3.0s" />'

man = json.load(open(f"{BASE}/vo_manifest_v2.json", encoding="utf-8"))
md = open(f"{BASE}/VO_SCRIPT_LUKE_REVOICE.md", encoding="utf-8").read()
v1 = json.load(open(f"{BASE}/vo_manifest.json", encoding="utf-8"))
tsv = {r["Shot"]: r for r in csv.DictReader(open(f"{EP}/STORYBOARD.tsv", newline="",
                                                 encoding="utf-8"), delimiter="\t")}

sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
fails, checks = [], 0


def ck(cond, label):
    global checks
    checks += 1
    if not cond:
        fails.append(label)


# C1 - line hashes
for l in man["lines"]:
    ck(l["sha256"] == sha(l["exact_text"]),
       f"C1 {l['shot']}/{l['speaker']}: line sha mismatch")

# C2 + C3 - pass hashes and composition
lines_by_wav = {}
for l in man["lines"]:
    lines_by_wav.setdefault((l["speaker"], l["wav"]), l)
for p in man["generation_passes"]:
    ck(p["sha256_paste_text"] == sha(p["paste_text"]), f"C2 {p['pass_id']}: pass sha mismatch")
    rebuilt = f"\n\n{BREAK}\n\n".join(
        lines_by_wav[(p["speaker"], w)]["exact_text"] for w in p["segment_order"])
    ck(rebuilt == p["paste_text"], f"C3 {p['pass_id']}: paste_text != lines joined by break tag")
    ck(p["char_count"] == len(p["paste_text"]), f"C2 {p['pass_id']}: char_count wrong")

# C4 - the .md's fenced blocks must hash to the manifest values
#      grab every ``` fence in the md, hash each, and require one match per pass
fences = re.findall(r"^```\n(.*?)\n```$", md, re.S | re.M)
fence_hashes = {sha(f) for f in fences}
for p in man["generation_passes"]:
    ck(p["sha256_paste_text"] in fence_hashes,
       f"C4 {p['pass_id']}: no fenced block in the .md hashes to {p['sha256_paste_text'][:12]}")
    ck(md.count(p["sha256_paste_text"]) >= 1,
       f"C4 {p['pass_id']}: its SHA is not even printed in the .md")

# C5 - exact_text must round-trip back to the TSV under ONLY the declared normalizations
SPK = {
    "LUKE": re.compile(r'LUKE(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
    "GF": re.compile(r'GF(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
    "RANGER": re.compile(r'RANGER(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
}
for l in man["lines"]:
    raw = SPK[l["speaker"]].findall(tsv[l["shot"]]["Dialogue / VO"])
    ck(len(raw) == 1, f"C5 {l['shot']}/{l['speaker']}: TSV turn not uniquely recoverable")
    if len(raw) != 1:
        continue
    ck(raw[0] == l["tsv_verbatim"], f"C5 {l['shot']}/{l['speaker']}: tsv_verbatim drifted")
    # undo the declared normalizations -> must land back on the TSV byte-for-byte
    back = l["exact_text"].replace("…", "...").replace(" — ", " - ")
    if back.endswith("—"):
        back = back[:-1] + "-"
    ck(back == raw[0],
       f"C5 {l['shot']}/{l['speaker']}: does NOT round-trip to the TSV\n"
       f"      tsv:  {raw[0]!r}\n      back: {back!r}")

# C6 - no regression on the two already-locked passes
o = {p["pass_id"]: p["sha256_paste_text"] for p in v1["generation_passes"]}
n = {p["pass_id"]: p["sha256_paste_text"] for p in man["generation_passes"]}
ck(n["PASS_LUKE_COLDOPEN"] == o["PASS_1_LUKE"], "C6 cold-open pass drifted from locked v1")
ck(n["PASS_GF"] == o["PASS_2_GF"], "C6 GF pass drifted from locked v1")

# C7 - no smart quotes anywhere
for p in man["generation_passes"]:
    ck(not any(c in p["paste_text"] for c in "’‘“”"),
       f"C7 {p['pass_id']}: curly quote in paste text")

print(f"{checks} checks run, {len(fails)} failed\n")
for f in fails:
    print("  FAIL", f)
if fails:
    sys.exit(1)

print("ALL PASS — the .md paste blocks and vo_manifest_v2.json hash IDENTICALLY,")
print("           every line round-trips to STORYBOARD.tsv, and the v1 SHAs are intact.\n")
print(f"{'PASS':22s} {'LINES':>5s} {'CHARS':>6s}  SHA-256 of paste text")
for p in man["generation_passes"]:
    print(f"{p['pass_id']:22s} {p['n_lines']:5d} {p['char_count']:6d}  {p['sha256_paste_text']}")
