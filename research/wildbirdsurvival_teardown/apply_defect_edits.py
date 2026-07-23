#!/usr/bin/env python3
"""
Merge the batch_*_out.json defect-resolution edits into ep02_shots.json, then
re-normalize the riders (so any rewritten grok_prompt stays consistent) and gate.

  venv/bin/python research/wildbirdsurvival_teardown/apply_defect_edits.py [--dry]

Only these fields may change: vantage, action, seed, grok_prompt, physics_risk,
has_blood. Timing (id/in_s/out_s/dur_s) is immutable and any edit touching it is
rejected. Each edited grok_prompt is re-checked for the grit prefix + anatomy
rider (+ blood rider if has_blood); an edit that drops a required clause is
rejected and logged rather than applied.
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, "ep02_shots.json")
GRIT = "real handheld wildlife documentary footage"
ANAT = "no extra limbs"
BLOOD = "does NOT drip"
# seed_crop and clip_in are SOURCE-side fields: which region of the still is fed to i2v,
# and which window of the returned 6.04 s clip ships. Neither touches the timeline, so
# neither can break tiling -- unlike in_s/out_s/dur_s, which stay immutable.
EDITABLE = {"vantage", "action", "seed", "grok_prompt", "physics_risk", "has_blood",
            "coverage_note", "seed_crop", "clip_in"}

NEW_BLOOD = ("a DRY matted red bloodstain that does NOT drip, stretch, run, or form any thread/string; "
             "the stain itself stays completely still while the birds move.")
NEW_ANAT = "keep exact anatomy, no extra limbs, no morphing, no bird splitting or merging."


def main(dry):
    j = json.load(open(SHOTS))
    byid = {s["id"]: s for s in j["shots"]}
    applied = rejected = 0
    log = []

    for f in sorted(glob.glob("/tmp/batch_*_out.json")):
        try:
            rows = json.load(open(f))
        except Exception as e:
            log.append(f"SKIP {f}: unreadable ({e})")
            continue
        for r in rows:
            sid = r.get("id")
            s = byid.get(sid)
            if not s or not r.get("edited"):
                continue
            edits = r.get("edits") or {}
            bad = [k for k in edits if k not in EDITABLE]
            if bad:
                rejected += 1
                log.append(f"REJECT {sid}: tried to edit immutable/unknown {bad}")
                continue
            prompt = edits.get("grok_prompt", s["grok_prompt"])
            has_blood = edits.get("has_blood", s.get("has_blood"))
            problems = []
            if "grok_prompt" in edits:
                if not prompt.startswith(GRIT):
                    problems.append("grit prefix dropped")
                if ANAT not in prompt:
                    problems.append("anatomy rider dropped")
                if has_blood and BLOOD not in prompt:
                    problems.append("blood rider dropped on a blood shot")
            if problems:
                rejected += 1
                log.append(f"REJECT {sid}: {problems}")
                continue
            for k, v in edits.items():
                s[k] = v
            applied += 1
            log.append(f"APPLY  {sid}: {sorted(edits)}")

    # re-normalize riders robustly (case/punctuation-insensitive) so any newly
    # written prompt — including agent output carrying the old forms — matches the
    # canonical clauses. Substring replace, no trailing-punctuation assumption.
    import re
    for s in j["shots"]:
        p = s["grok_prompt"]
        p = re.sub(r"only the finch moves",
                   "the stain itself stays completely still while the birds move", p, flags=re.I)
        p = re.sub(r"count stays the same", "no bird splitting or merging", p, flags=re.I)
        p = re.sub(r";\s*;", ";", p)
        s["grok_prompt"] = p
        # seed naming: bare filename, .png extension, canonical raw-wound name
        v = s["seed"].split("/")[-1]
        if v == "SEED_raw_stain" or v == "SEED_raw_stain.png":
            v = "SEED_raw_wound.png"
        if v.startswith("SEED_") and not v.endswith(".png"):
            v = v + ".png"
        s["seed"] = v

    print("\n".join(log))
    print(f"\napplied {applied}, rejected {rejected}")
    if not dry:
        json.dump(j, open(SHOTS, "w"), indent=1)
        print("wrote", SHOTS)
    else:
        print("(dry run — not written)")


if __name__ == "__main__":
    main("--dry" in sys.argv)
