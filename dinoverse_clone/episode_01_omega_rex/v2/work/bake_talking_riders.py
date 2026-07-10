#!/usr/bin/env python3
"""Bake talking-creature riders into STORYBOARD.tsv col 10 (Grok i2v prompt).

Fixes the 2026-07-09 audit findings (work/qa_talking/audit_results.json): Grok
animated the CREATURE mouthing the human dialogue on 14 confirmed + 3 borderline
clips. Owner directive: the line must be delivered by a park guide/keeper, GF,
or Luke — on camera where one is in frame, otherwise as off-camera vlog
narration — and the creature's mouth stays closed.

Mechanism = same as bake_zone8/9_riders.py (surgical row edit, csv reserialize),
but instead of replacing prompts it INSERTS a "Speech:" clause immediately
before the existing "Style:" section, preserving every battle-tested rider.
Also removes S35's self-inflicted "jaw slightly working" phrase.
"""
import csv, io, sys

TSV = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/STORYBOARD.tsv"
SHOT_COL = 1
PROMPT_COL = 9

VO = ("the spoken lines are off-camera vlog narration from the couple behind "
      "the camera - nobody and nothing in frame delivers them. ")

SPEECH = {
    "S13b": "Speech: " + VO + "The mascot's costume head is RIGID with a fixed molded mouth - it never opens, moves, or lip-syncs; the mascot emotes only with arm waves and body language; no bystander mouths the lines.",
    "S19":  "Speech: " + VO + "The Carnotaurus's jaw stays fully CLOSED every frame - it never opens, mouths, or articulates while the line plays; menace comes from the pacing walk and head swing only (its calls are off-screen audio only).",
    "S21":  "Speech: " + VO + "BOTH Carnotaurus - the adult AND the juvenile - keep their jaws fully CLOSED every frame; neither ever opens, mouths, or articulates; the low calls are off-screen audio only.",
    "S25":  "Speech: the KEEPER visibly speaks her line on camera, mouthing the words naturally; GF's reply comes from off-camera. The hatchling's beak stays fully CLOSED the entire clip - it flaps for balance but never opens its beak, mouths, or lip-syncs.",
    "S26":  "Speech: " + VO + "The chick's beak stays fully CLOSED for the entire hop and glide - no opening, mouthing, calling, or lip-sync at any point.",
    "S27":  "Speech: " + VO + "The Quetzalcoatlus's beak stays fully CLOSED every frame as it strides - it never opens, mouths, or articulates; the echoing calls are off-screen audio only.",
    "S28":  "Speech: " + VO + "Every pterosaur's beak stays fully CLOSED in flight - none opens, calls, or mouths; any screech is off-screen audio only.",
    "S30":  "Speech: " + VO + "The pterosaurs gliding inside the dome keep their beaks fully CLOSED every frame - none opens, calls, or mouths the words.",
    "S35":  "Speech: " + VO + "The Dunkleosteus's massive jaw stays fully CLOSED as it glides past - it never opens, works, gapes, or articulates at any point in the clip.",
    "S46":  "Speech: the RANGER visibly speaks his lines on camera, mouthing the words naturally toward Luke; Luke's reply comes from behind the camera. The Utahraptor's jaw stays fully CLOSED every frame - it watches and perches but never opens its mouth, bares its teeth, or mouths along.",
    "S47":  "Speech: " + VO + "All raptors in the pack keep their mouths fully CLOSED every frame - including the one that steps forward; none opens, mouths, or articulates.",
    "S48":  "Speech: " + VO + "Every raptor's jaw stays fully CLOSED for the entire run - mouths never open, pant, or articulate while they sprint.",
    "S49":  "Speech: " + VO + "The raptor's mouth stays fully CLOSED through the entire stare - the menace is in the unblinking eye and stillness, never an open or moving mouth.",
    "S52":  "Speech: " + VO + "The Styracosaurus may chew ONLY while its head is DOWN at the grass; the moment its head rises toward the visitors its beak is fully CLOSED and stays closed - it never mouths, chews air, or articulates with its head up.",
    "S62":  "Speech: the RANGER visibly speaks his lines on camera, mouthing the words naturally; Luke's reply comes from behind the camera. The hatchling NEVER opens its mouth - its jaw stays fully CLOSED every frame (its squeaks are off-screen audio only); no gaping, mouthing, or lip-sync.",
    "S72":  "Speech: " + VO + "The faint pale Indominus in the background closes its mouth within the first half-second and keeps it fully CLOSED for the rest of the clip - it never cycles, mouths, or articulates.",
    "S76":  "Speech: " + VO + "The D-Rex's jaws stay fully CLOSED as it turns its head toward the teens - it never opens its mouth, mouths the words, or roars in this shot.",
}

FIXES = {"S35": [("jaw slightly working, ", "")]}

with open(TSV, newline="") as f:
    lines = f.readlines()

def reserialize(fields):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL,
                   lineterminator="")
    w.writerow(fields)
    return buf.getvalue()

changed, out = {}, []
for line in lines:
    stripped = line.rstrip("\n")
    if not stripped:
        out.append(line); continue
    fields = next(csv.reader([stripped], delimiter="\t", quotechar='"'))
    shot = fields[SHOT_COL] if len(fields) > SHOT_COL else ""
    if shot in SPEECH and shot not in changed:
        p = fields[PROMPT_COL]
        if " Speech: " in p:
            print(f"{shot}: Speech clause already present, skipping"); out.append(line); continue
        if " Style:" not in p:
            print(f"ERROR: {shot} has no Style anchor"); sys.exit(1)
        for old_s, new_s in FIXES.get(shot, []):
            assert old_s in p, f"{shot}: fix anchor missing: {old_s!r}"
            p = p.replace(old_s, new_s)
        old_len = len(fields[PROMPT_COL])
        p = p.replace(" Style:", f" {SPEECH[shot]} Style:", 1)
        fields[PROMPT_COL] = p
        out.append(reserialize(fields) + ("\n" if line.endswith("\n") else ""))
        changed[shot] = (old_len, len(p))
    else:
        out.append(line)

missing = [s for s in SPEECH if s not in changed]
if missing:
    print("ERROR: shots not found/updated:", missing); sys.exit(1)

with open(TSV, "w", newline="") as f:
    f.writelines(out)

for s in SPEECH:
    print(f"{s}: Speech rider baked ({changed[s][0]} -> {changed[s][1]} chars)")
print(f"Done. {len(changed)} rows updated; all others untouched.")
