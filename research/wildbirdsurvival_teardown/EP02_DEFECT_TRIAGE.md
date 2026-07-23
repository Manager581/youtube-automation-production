# EP02 — defect triage (the 18 act-level / global audit findings)

_2026-07-23. The adversarial pass raised 139 defects. 121 are shot-scoped and are being resolved by
the `ep02-defect-resolve` workflow (verify-against-current then fix). The **18 below are act-level or
multi-shot** and are triaged here by hand. Status is against the CURRENT `ep02_shots.json`, not the old
draft the defects were written against._

## Already resolved by the normalization pass — no action
- **still_wide_island.png tiny-dot seed** (ACT5 S051 ref) — verified: **no shot uses it anymore**; it
  was swapped to `SEED_wide_booby_clear`.
- **ACT4 26-shots-eats-the-mean-budget** (ACT4-GLOBAL) — this was the root cause of the mean-shot
  tightness; the global tune (absorb 4 weak beats) already lifted the whole-video mean to **5.45 s
  (PASS)**. No further ACT4 cut needed.
- **"SEED_finch_portrait still to generate" false claims** (ACT5 notes ×2, ACT4 note 5) — the seed
  **exists on disk now**, and the rendered manifest's seed shopping list is **computed from disk**, so
  the stale per-act NOTES text is superseded. The old NOTES blocks are not re-published.
- **Documentation-accuracy nits** (ACT2 metrics honesty, ACT4 notes 4/8 "fabricated conflict", ACT5
  metrics selective-compliance, ACT7 note 2 "pre-authorised merge lever") — these critique NOTES prose
  from the old per-act drafts. The rendered manifest recomputes every number from the JSON via
  `gate_shots.py`, so those prose blocks no longer ship. Superseded.

## Fixed in the consolidated JSON pass
- **[16] ACT7 cut vs VO at 444 s** — `EP02_SCRIPT_LOCKED.md` puts *"The seabird keeps its egg. The finch
  keeps its life."* at **7:24 = 444 s**, but the S084/S085 boundary sat at 446 s. Re-timed ACT7 to
  **430-440 / 440-444 / 444-454 / 454-466 / 466-473 / 473-480** so the cut lands on the VO line **and**
  ACT7 keeps three 10 s+ holds (10/10/12) — the naïve 446→444 nudge would have dropped a hold and failed
  the ≥12 gate.
- **[0]+[15] the two rider closing-clause contradictions** — applied as a **global rider rewording**
  (below), since both recur across many shots, not just the ones flagged.

## Global rider rewording (applied to every affected prompt)
- **Blood rider** — `"...— only the finch moves."` contradicts any shot where the booby also moves
  (bill-snap, weight-shift, wing-lift). Reworded project-wide to scope the stillness to the stain:
  **`"a DRY matted red bloodstain that does NOT drip, stretch, run, or form any thread/string; the
  stain itself stays completely still while the birds move."`**
- **Anatomy count rider** — `"count stays the same"` contradicts shots where finches legitimately land
  or scatter (the raid, the resolution resettle). Reworded to protect anatomy without freezing arrivals:
  **`"keep exact anatomy, no extra limbs, no morphing, no bird splitting or merging."`**
- **Head-on negation** — where a prompt said *"never turns head-on to camera,"* the audit is right that
  negating the banned phrase can still cue it. Where it reads cleanly the workflow asserts the positive
  (*"head stays in strict side profile"*) instead. Verified by `gate_shots.py` (head-on check still 0).

## Production guidance (not a JSON field — for the shoot)
- **[1]+[14] same-seed adjacency.** Grok i2v begins on the seed's frame 1, so 3-4 consecutive shots from
  the *identical* seed can read as one glitchy take even with different prompted vantages. Current runs:
  **S007-S009** (hero_A), **S058-S061** (egg), **S080-S082** (hero_A). Before generating these runs,
  derive **distinct seed frames** from the base still by local crop/recomposite (the way `A2` was cut
  from `A`) — one per shot, matching each shot's stated framing — rather than re-prompting off one frame.
  For **[14]** specifically, `SEED_wide_booby_clear` is asked for two mutually exclusive camera heights
  (S083 low-at-rock-level, S088 elevated); make **two** seed crops, `SEED_wide_booby_low` and
  `SEED_wide_booby_high`, from the one wide.
- **[4] music-peak consistency.** Three ACT3 shots reference the peak at different timecodes. Pick one:
  the measured reference peak is **139.2 s (0.29×480)**; the locked script's near-silence-at-peak is
  **1:52 = 112 s**. Music is a *hygiene* layer (weak marker), so this only needs to be internally
  consistent — set the bed's single peak at ~2:19 as the storyboard already says and drop the per-shot
  timecodes from the action text.
