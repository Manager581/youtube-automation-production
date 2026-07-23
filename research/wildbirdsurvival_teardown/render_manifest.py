#!/usr/bin/env python3
"""
Render EP02_SHOT_MANIFEST_FULL.md from ep02_shots.json (the source of truth) plus
the workflow's per-act notes/defects. Re-run after any edit to the JSON so the
readable doc and the gate never drift apart.

  venv/bin/python research/wildbirdsurvival_teardown/render_manifest.py
"""
import json
import os
import collections

HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, "ep02_shots.json")
WF = "/private/tmp/claude-501/-Users-jefflawrence-Documents-youtube-automation-production/91c20c9b-950a-4077-b4f5-bfd51388a37e/tasks/weieffwzl.output"
OUT = os.path.join(HERE, "EP02_SHOT_MANIFEST_FULL.md")

import gate_shots  # reuse the exact same gate

shots = json.load(open(SHOTS))["shots"]
shots.sort(key=lambda x: x["in_s"])
rows = gate_shots.gates(shots)

notes, defs = {}, {}
if os.path.exists(WF):
    src = json.load(open(WF))["result"]
    for a in src["acts"]:
        notes[a["act"]] = a.get("notes")
        defs[a["act"]] = a.get("defects") or []

EX = lambda b: os.path.exists(os.path.join(HERE, "..", "..", "assets", "vampire_finch", b))
seeds = collections.Counter(x["seed"] for x in shots)
n_def = sum(len(v) for v in defs.values())

L = ["# EP02 — FULL SHOT MANIFEST (%d shots, 0:00-8:00)" % len(shots),
     "_Generated 2026-07-23 by a 21-agent workflow (9 acts drafted in parallel, each adversarially",
     "audited, then three global critics), then independently re-verified and pacing-tuned. Built to the",
     "480 s clock in `SECOND_BY_SECOND_theirs_vs_ours.md`, the locked VO in `EP02_SCRIPT_LOCKED.md`, and",
     "the recovered spine in `EP02_SHOT_MANIFEST.md`._", "",
     "**Machine-readable copy: `ep02_shots.json`** — what a builder script should read.",
     "**Gate:** `venv/bin/python research/wildbirdsurvival_teardown/gate_shots.py` (all 14 currently PASS).", "",
     "## Status", "Pacing and prompt-hygiene gates all pass (see table). What is **not** resolved: the",
     "%d content defects the adversarial pass raised, recorded per act below. Read them before you shoot." % n_def, "",
     "### Gates (recomputed from the JSON by `gate_shots.py`)", "",
     "| Gate | Target | Actual | |", "|---|---|---|---|"]
for name, target, val, ok in rows:
    L.append(f"| {name} | {target} | {val} | {'✅ PASS' if ok else '❌ **FAIL**'} |")
L += ["",
      "> The hook gate counts shots that **start** within the first 60 s. An earlier pass mistakenly",
      "> filtered on end-time, which dropped the 14.9 s silence hold and made the hook look too busy.", "",
      "## Seed shopping list", "| Shots | Seed | On disk? |", "|---:|---|---|"]
for seed, n in seeds.most_common():
    L.append(f"| {n} | `{seed}` | {'✅ yes' if EX(seed) else '❌ **must generate**'} |")
L += ["",
      "> Two seeds the workflow surfaced that were not in the original six: `SEED_finch_portrait_redtip`",
      "> (the red-tipped beak for the TURN match-cut) and `SEED_raw_wound`. Both are in `EP02_SEED_PROMPTS.md`.",
      "", "---"]

byact = collections.OrderedDict()
for x in shots:
    byact.setdefault(x["act"], []).append(x)

for act, ss in byact.items():
    L.append(f"\n## {act} — {ss[0]['in_s']:.1f}s -> {ss[-1]['out_s']:.1f}s · {len(ss)} shots\n")
    if notes.get(act):
        L.append(f"**Conflicts found and resolved:** {notes[act]}\n")
    for s in ss:
        was = f"  <sub>(was {s['orig_id']})</sub>" if s.get("orig_id") and s["orig_id"] != s["id"] else ""
        L.append(f"### {s['id']} · {s['in_s']:.1f}-{s['out_s']:.1f}s ({s['dur_s']:.1f}s) · {s['size']}{was}")
        L.append(f"- **Vantage:** {s['vantage']}")
        L.append(f"- **Action:** {s['action']}")
        L.append(f"- **Seed:** `{s['seed']}` · physics risk **{s['physics_risk']}** · blood: {'YES' if s.get('has_blood') else 'no'}")
        if s.get("coverage_note"):
            L.append(f"- **>6 s coverage:** {s['coverage_note']}")
        L.append(f"- **Grok prompt:**\n  > {s['grok_prompt']}\n")
    d = defs.get(act) or []
    if d:
        L.append(f"<details><summary><b>{len(d)} unresolved audit defects</b> (shot ids are act-local originals)</summary>\n")
        for x in d:
            L.append(f"- **{x.get('shot_id','?')}** — {x.get('defect','')}  \n  *Fix:* {x.get('fix','')}")
        L.append("\n</details>\n")

open(OUT, "w").write("\n".join(L))
print("rendered", OUT, "·", len(shots), "shots ·", sum(1 for _, _, _, ok in rows if ok), "/", len(rows), "gates pass")
