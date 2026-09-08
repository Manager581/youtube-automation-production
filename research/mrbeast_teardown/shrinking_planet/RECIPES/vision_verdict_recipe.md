# Vision verdict recipe (GATE 5 bank-time + GATE 6 story-tier) — standing in-session procedure

Runs under the Claude subscription as session labor (no metered APIs). Every session runs it IDENTICALLY.
Inputs: a clip's 8 fps strip (`scripts/clip_bank.py add` makes it), its composite seed PNG, its manifest row.

## Per clip (bank time) — answer each with YES/NO, evidence = frame indices on the strip
1. IDENTITY — same creature as the locked master? (silhouette, colour code: PIP magenta + yellow scarf; GRUFF cyan fur, mouth covered, brass goggle on forehead; ORB chrome sphere + gold halo, NO arms; COUNT black cube, one antenna). Any extra limb/face/costume change = NO.
2. ACTION — does the manifest's `i2v_prompt` motion actually happen? (not merely "looks like the seed")
3. DIRECTION — motion plays FORWARD (water falls down, dust settles, the rear-up rises then holds). Compare frame k vs k+1 at ≥2 points. (The backwards-cookie lesson.)
4. PHYSICS — no interpenetration, no teleport, no morph mid-shot; planet horizon consistent with the row's `planet_m` class.
5. TEXT/ARTIFACTS — no baked-in text, watermark, extra creature, human.
6. CONTINUITY — THE COUNT's displayed number (if visible) == row `count_display`; day-consistent state (no costume change).
Verdict: PASS only if 1–6 all YES. Record: `scripts/clip_bank.py verdict --ledger L --shot S --pass|--fail --note "<which question failed + frame idx>" --by "session <date>"`. FAIL → regenerate (max 3 rolls; then re-plan the shot).

## Per beat (story tier, on the assembled render) — from `scripts/render_review_packet.py` output
For each shot strip in STORY_PACKET.jpg: does the PLANNED beat (label: beat / characters / planet size / loop tags) visibly occur inside its window? Any title-claim contradiction on screen? Record in story_verdicts.json (PASS/FAIL + note). Escalate contact/occlusion beats to 0.5 s steps (the S88 lesson).

## Fan-out rule
≤12 clips per inspector; adversarial second pass on every PASS for hero shots; disagreements adjudicated at native resolution (10 fps re-extract). Never skip a clip because metrics looked fine — the killer defect classes had no cheap-metric precursor.
