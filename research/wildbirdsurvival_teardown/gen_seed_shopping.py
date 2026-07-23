#!/usr/bin/env python3
"""
Generate EP02_SEED_SHOPPING.md from ep02_shots.json — always current, never stale.
Groups the seed variants and marks crop/recolor shortcuts so the shoot knows the
true number of base generations.

  venv/bin/python research/wildbirdsurvival_teardown/gen_seed_shopping.py
"""
import json
import os
import collections

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "..", "assets", "vampire_finch")
EX = lambda b: os.path.exists(os.path.join(ASSETS, b))

# variant -> (base, how-to-make). A shortcut is a crop/recolor of a base gen.
SHORTCUT = {
    "SEED_macro_tail_high.png": ("SEED_macro_tail.png", "tighter/higher CROP of the tail generation"),
    "SEED_flank_stain_top.png": ("SEED_flank_stain.png", "top-down CROP of the flank-stain generation"),
    "SEED_finch_portrait_redtip.png": ("SEED_finch_portrait.png", "RECOLOR the beak tip red on the existing portrait (ChatGPT edit)"),
    "SEED_pricklypear_top.png": ("SEED_pricklypear.png", "top-down CROP of the prickly-pear generation (or generate directly)"),
}


def main():
    j = json.load(open(os.path.join(HERE, "ep02_shots.json")))
    byseed = collections.defaultdict(list)
    for s in sorted(j["shots"], key=lambda x: x["in_s"]):
        byseed[s["seed"]].append(s)

    on_disk = sorted((s for s in byseed if EX(s)), key=lambda z: -len(byseed[z]))
    shortcuts = sorted((s for s in byseed if not EX(s) and s in SHORTCUT), key=lambda z: -len(byseed[z]))
    generate = sorted((s for s in byseed if not EX(s) and s not in SHORTCUT), key=lambda z: -len(byseed[z]))

    L = ["# EP02 — SEED SHOPPING LIST (generated)",
         "_Auto-generated from `ep02_shots.json` by `gen_seed_shopping.py`. Do not hand-edit — re-run it._",
         "",
         f"**{len(generate)} base generations + {len(shortcuts)} crop/recolor shortcuts still needed; "
         f"{len(on_disk)} seed(s) already on disk.**",
         "",
         "The defect pass grew the seed list because several shots' framings were unreachable from their",
         "assigned seed (Grok i2v begins on the seed's frame 1). Each new seed traces to a seed-capability",
         "defect an agent grounded by opening the actual PNG. Prompts for the original six are in",
         "`EP02_SEED_PROMPTS.md`; write the new ones from each seed's first shot's vantage/action.",
         "",
         "## Base generations still needed (do these — highest-leverage first)",
         "| Seed | Shots | First shot vantage (spec source) |",
         "|---|---:|---|"]
    for s in generate:
        first = byseed[s][0]
        L.append(f"| `{s}` | {len(byseed[s])} | {first['vantage'][:120]} |")
    L += ["", "## Crop / recolor shortcuts (cheap — derive from a base gen)",
          "| Seed | Shots | How |", "|---|---:|---|"]
    for s in shortcuts:
        L.append(f"| `{s}` | {len(byseed[s])} | {SHORTCUT[s][1]} — base `{SHORTCUT[s][0]}` |")
    L += ["", "## Already on disk",
          "| Seed | Shots |", "|---|---:|"]
    for s in on_disk:
        L.append(f"| `{s}` | {len(byseed[s])} |")
    L += ["",
          "⚠️ **Scope note:** more seeds than the original 6. Forcing each shot onto a reachable existing",
          "seed would reintroduce the adjacent-vantage duplication the defect pass removed. The",
          "`SEED_mutualism_clean` A/B/C are *deliberately* distinct poses (Act-4 montage) — don't collapse them.",
          "Also derive distinct seed FRAMES for the same-seed runs (S007-9, S058-61, S080-82) by cropping the",
          "base still, per `EP02_DEFECT_TRIAGE.md`."]

    out = os.path.join(HERE, "EP02_SEED_SHOPPING.md")
    open(out, "w").write("\n".join(L))
    print(f"wrote {out}: {len(generate)} to generate, {len(shortcuts)} shortcuts, {len(on_disk)} on disk")


if __name__ == "__main__":
    main()
