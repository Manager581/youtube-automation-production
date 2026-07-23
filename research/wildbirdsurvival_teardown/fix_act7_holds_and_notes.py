#!/usr/bin/env python3
"""Fix two ACT7 defects that would fail the ship gate. Run with --dry first.

DEFECT 1 — the plan fails the real style gate on holds.
`gate_shots.py` counts holds as `dur >= 10`; `gate_style_wbs.py` -- the actual ship
criterion, derived from the measured winner bands -- counts `dur > 10`. S083 and
S085 are EXACTLY 10.0 s, so they satisfy the internal gate but not the ship gate,
leaving 10 qualifying holds against a required 12 (winners run 13-21).

Fix: nudge two interior boundaries by 0.5 s. Nothing else moves.
  S082/S083 boundary 430.0 -> 429.5   (S082 11.5->11.0, S083 10.0->10.5)
  S085/S086 boundary 454.0 -> 454.5   (S085 10.0->10.5, S086 12.0->11.5)
All four shots stay above 10 s, so BOTH gate definitions now count 12 holds.
Chosen because these four are the only neighbours with slack: the runtime stays
480 s, the shot count stays 88 (so the mean is arithmetically unchanged at
480/88 = 5.4545), the median sits far below at 4.50, no shot approaches the 3 s
fast-cut boundary, and S085's in_s stays pinned at 444.0 -- the deliberate ACT7
landing on the VO line "The seabird keeps its egg" that the defect triage set.

DEFECT 2 — stale ACT7 coverage notes produce holes.
ACT7 was re-timed (6/10/6/11/7/10) but its coverage notes were not updated, so
they still describe producing 8.00 s clips for slots of 10.0/10.0/12.0 s -- a 2 s,
2 s and 4 s hole. S084 also carries an 8.00 s note despite being 4.0 s, under
Grok's 6.04 s cap, needing no coverage at all.
(Checked and NOT stale: S011/S013/S016 state raw totals then reconcile to the slot;
S022/S027/S044/S048 are duration-agnostic boilerplate; S012/S087/S088 over-produce
slightly, which is benign because you trim.)

  venv/bin/python research/wildbirdsurvival_teardown/fix_act7_holds_and_notes.py [--dry]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "ep02_shots.json")
RUNTIME = 480.0
CAP = 6.041667

# id -> (new_in, new_out)
RETIME = {
    "S082": (418.5, 429.5),
    "S083": (429.5, 440.0),
    "S085": (444.0, 454.5),
    "S086": (454.5, 466.0),
}

TWO_GEN = ("Exceeds Grok's 6.04 s cap. Cover with TWO near-identical gens from the SAME seed and "
           "identical prompt (different rolls), each trimmed to {half:.2f} s and joined on an "
           "invisible match-cut at a wind lull with the booby's head static "
           "({half:.2f} + {half:.2f} = {total:.1f} s exactly, both inside the 6.04 s cap - no "
           "retime needed). Do NOT single-gen retime this one: reaching {total:.1f} s from one "
           "6.04 s gen needs {ratio:.2f}x, and the breathing rhythm slows visibly below ~0.9x. "
           "Frame-strip both gens before assembly.")

NOTES = {}
for sid, (a, b) in RETIME.items():
    total = round(b - a, 2)
    # the speed a single 6.04 s gen would have to run at to fill the slot
    single_gen_ratio = CAP / total
    NOTES[sid] = TWO_GEN.format(half=total / 2, total=total, ratio=single_gen_ratio)

# S085 keeps its specific artifact warning; S083 keeps its "settling motion" context
NOTES["S085"] += (" Trim the last 12 frames of each gen BEFORE joining - grit clip #9 went "
                  "slightly awkward in the booby's posture in the final ~1 s. Frame-strip "
                  "mandatory: this is the flagged egg object-permanence class.")
NOTES["S083"] += (" All motion here is settling/landing/wind, so the match-cut is easy to hide; "
                  "reject any gen where a finch changes count across the seam.")
NOTES["S086"] += (" Frame-strip mandatory - the blood-thread artifact is the one proven failure "
                  "mode of the whole pipeline, and the fly is a small fast element that can morph.")

DROP_NOTE = ["S084"]  # 4.0 s, under the cap: no coverage needed


def main(dry):
    j = json.load(open(SHOTS))
    shots = {s["id"]: s for s in j["shots"]}
    changes = []

    for sid, (a, b) in RETIME.items():
        s = shots[sid]
        old = (s["in_s"], s["out_s"], s["dur_s"])
        s["in_s"], s["out_s"] = a, b
        s["dur_s"] = round(b - a, 3)
        changes.append(f"  {sid}: {old[0]}-{old[1]} ({old[2]}s) -> {a}-{b} ({s['dur_s']}s)")

    for sid, note in NOTES.items():
        shots[sid]["coverage_note"] = note
        changes.append(f"  {sid}: coverage_note rewritten for its real {shots[sid]['dur_s']}s slot")

    for sid in DROP_NOTE:
        if shots[sid].pop("coverage_note", None) is not None:
            changes.append(f"  {sid}: dropped coverage_note ({shots[sid]['dur_s']}s is under the cap)")

    print("\n".join(changes))

    # --- validate before writing -------------------------------------------
    ordered = sorted(j["shots"], key=lambda s: s["in_s"])
    problems = []
    for i, s in enumerate(ordered):
        if abs(s["out_s"] - s["in_s"] - s["dur_s"]) > 1e-6:
            problems.append(f"{s['id']} dur != out-in")
        if i and abs(s["in_s"] - ordered[i - 1]["out_s"]) > 1e-6:
            problems.append(f"gap/overlap between {ordered[i-1]['id']} and {s['id']}")
    if abs(ordered[0]["in_s"]) > 1e-6 or abs(ordered[-1]["out_s"] - RUNTIME) > 1e-6:
        problems.append("span is no longer 0 -> 480")
    if len(ordered) != 88:
        problems.append(f"shot count changed to {len(ordered)}")

    durs = sorted(s["dur_s"] for s in ordered)
    holds_strict = sum(1 for d in durs if d > 10)
    holds_loose = sum(1 for d in durs if d >= 10)
    fast = sum(1 for d in durs if d < 3)
    mean = sum(durs) / len(durs)
    med = durs[len(durs) // 2] if len(durs) % 2 else (durs[len(durs)//2 - 1] + durs[len(durs)//2]) / 2

    print(f"\n  holds >10 (ship gate): {holds_strict}   holds >=10 (internal): {holds_loose}")
    print(f"  mean {mean:.4f}  median {med}  fast(<3s) {fast}")

    if problems:
        print("\nREFUSING TO WRITE — validation failed:")
        for p in problems:
            print("   " + p)
        return 1
    if holds_strict < 12:
        print(f"\nREFUSING TO WRITE — still only {holds_strict} holds >10 s")
        return 1

    if dry:
        print("\n(dry run — not written)")
        return 0
    json.dump(j, open(SHOTS, "w"), indent=1)
    print(f"\nwrote {SHOTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--dry" in sys.argv))
