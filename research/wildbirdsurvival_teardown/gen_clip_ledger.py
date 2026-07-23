#!/usr/bin/env python3
"""Track the EP02 Grok i2v clip grind — always current, never stale.

The seed list has gen_seed_shopping.py; this is its twin for CLIPS. It answers
the only two questions the grind needs: what is done, and what is next.

  venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py         # status + next shot
  venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py --next 5
  venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py --qa    # audit clips on disk

Convention: assets/vampire_finch/clips/<SHOT_ID>.mp4 plus <SHOT_ID>_strip.jpg.
A shot only counts as DONE when both exist -- frame-stripping is mandatory, so a
clip without its strip is deliberately reported as unfinished.
"""
import argparse
import collections
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(REPO, "assets", "vampire_finch")
CLIPS = os.path.join(ASSETS, "clips")
SHOTS = os.path.join(HERE, "ep02_shots.json")
LEDGER = os.path.join(HERE, "EP02_CLIP_LEDGER.md")

# Grok's measured output; a clip far off this was probably mis-generated.
EXPECT_W, EXPECT_H, EXPECT_DUR = 1264, 720, 6.04

# Runs of adjacent shots sharing one seed -- each needs a DISTINCT crop of the
# base still or the cut reads as a glitchy loop (the rough_cut_v1 failure).
SAME_SEED_RUNS = [("S007", "S009"), ("S058", "S061"), ("S080", "S082")]


def clip_path(sid):
    return os.path.join(CLIPS, f"{sid}.mp4")


def strip_path(sid):
    return os.path.join(CLIPS, f"{sid}_strip.jpg")


def status(sid):
    has_clip = os.path.exists(clip_path(sid))
    has_strip = os.path.exists(strip_path(sid))
    if has_clip and has_strip:
        return "done"
    if has_clip:
        return "needs_strip"
    return "todo"


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True)
    vals = [v for v in r.stdout.split() if v]
    try:
        return int(vals[0]), int(vals[1]), float(vals[2])
    except (IndexError, ValueError):
        return None


def in_same_seed_run(sid):
    for a, b in SAME_SEED_RUNS:
        if a <= sid <= b:
            return f"{a}-{b}"
    return None


def load():
    shots = json.load(open(SHOTS))["shots"]
    return sorted(shots, key=lambda s: s["in_s"])


def print_shot(s, n=None):
    tag = in_same_seed_run(s["id"])
    head = f"--- {s['id']}  [{s['in_s']}-{s['out_s']}s, {s['dur_s']}s, {s['size']}]  act {s['act']}"
    print(head)
    print(f"    SEED: {s['seed']}"
          + (f"   ** SAME-SEED RUN {tag}: use a DISTINCT CROP of this still **" if tag else ""))
    if s.get("has_blood"):
        print("    BLOOD SHOT -> the DRY-blood rider is mandatory (already in the prompt)")
    if s.get("physics_risk"):
        print(f"    PHYSICS RISK: {s['physics_risk']}")
    print(f"    PROMPT:\n{s['grok_prompt']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", type=int, default=1, help="how many upcoming shots to print")
    ap.add_argument("--qa", action="store_true", help="audit the clips already on disk")
    args = ap.parse_args()

    shots = load()
    os.makedirs(CLIPS, exist_ok=True)
    st = {s["id"]: status(s["id"]) for s in shots}
    done = [s for s in shots if st[s["id"]] == "done"]
    needs_strip = [s for s in shots if st[s["id"]] == "needs_strip"]
    todo = [s for s in shots if st[s["id"]] == "todo"]

    print(f"=== EP02 CLIP LEDGER — {len(done)}/{len(shots)} done, "
          f"{len(needs_strip)} awaiting frame-strip, {len(todo)} to generate ===")

    if args.qa:
        print("\n--- QA of clips on disk ---")
        bad = 0
        for s in shots:
            p = clip_path(s["id"])
            if not os.path.exists(p):
                continue
            info = probe(p)
            if info is None:
                print(f"  [{s['id']}] UNREADABLE — regenerate")
                bad += 1
                continue
            w, h, d = info
            probs = []
            if (w, h) != (EXPECT_W, EXPECT_H):
                probs.append(f"{w}x{h} not {EXPECT_W}x{EXPECT_H} (720p not re-selected?)")
            if abs(d - EXPECT_DUR) > 0.6:
                probs.append(f"{d:.2f}s not ~{EXPECT_DUR}s")
            if not os.path.exists(strip_path(s["id"])):
                probs.append("NO frame strip")
            if probs:
                print(f"  [{s['id']}] " + "; ".join(probs))
                bad += 1
        print(f"  {'all clips on disk pass' if not bad else str(bad) + ' clip(s) need attention'}")
        return 0

    if needs_strip:
        print("\n!! these have a clip but NO frame strip (frame-stripping is mandatory):")
        for s in needs_strip:
            print(f"   {s['id']}")

    # write the ledger doc
    byact = collections.defaultdict(lambda: [0, 0])
    for s in shots:
        byact[s["act"]][1] += 1
        if st[s["id"]] == "done":
            byact[s["act"]][0] += 1
    L = ["# EP02 — CLIP LEDGER (generated)",
         "_Auto-generated from `ep02_shots.json` by `gen_clip_ledger.py`. Do not hand-edit — re-run it._",
         "",
         f"**{len(done)} / {len(shots)} clips done · {len(needs_strip)} awaiting frame-strip · "
         f"{len(todo)} still to generate.**",
         "",
         "A shot counts as done only when BOTH `<ID>.mp4` and `<ID>_strip.jpg` exist in",
         "`assets/vampire_finch/clips/` — frame-stripping every clip is mandatory, so a clip",
         "without its strip is reported as unfinished on purpose.",
         "",
         "## Progress by act",
         "| Act | Done | Total |", "|---|---:|---:|"]
    for act in sorted(byact):
        d, t = byact[act]
        L.append(f"| {act} | {d} | {t} |")
    L += ["", "## Remaining shots (in timeline order)",
          "| Shot | In-Out | Size | Seed | Blood |", "|---|---|---|---|---|"]
    for s in todo:
        L.append(f"| `{s['id']}` | {s['in_s']}-{s['out_s']}s | {s['size']} | "
                 f"`{s['seed']}` | {'yes' if s.get('has_blood') else ''} |")
    L += ["",
          "⚠️ Same-seed adjacency runs " + ", ".join(f"{a}-{b}" for a, b in SAME_SEED_RUNS)
          + " need a DISTINCT CROP of the base still per shot — re-prompting one frame",
          "produces the glitchy-loop look that got rough_cut_v1 rejected outright."]
    open(LEDGER, "w").write("\n".join(L))
    print(f"\nwrote {os.path.relpath(LEDGER, REPO)}")

    if todo:
        print(f"\n=== NEXT {min(args.next, len(todo))} SHOT(S) ===\n")
        for s in todo[:args.next]:
            print_shot(s)
    else:
        print("\nALL CLIPS DONE — next is the music bed, then assemble.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
