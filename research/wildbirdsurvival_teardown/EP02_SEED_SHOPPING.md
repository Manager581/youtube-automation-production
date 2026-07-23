# EP02 — SEED SHOPPING LIST (generated)
_Auto-generated from `ep02_shots.json` by `gen_seed_shopping.py`. Do not hand-edit — re-run it._

**14 base generations + 4 crop/recolor shortcuts still needed; 5 seed(s) already on disk.**

The defect pass grew the seed list because several shots' framings were unreachable from their
assigned seed (Grok i2v begins on the seed's frame 1). Each new seed traces to a seed-capability
defect an agent grounded by opening the actual PNG. Prompts for the original six are in
`EP02_SEED_PROMPTS.md`; write the new ones from each seed's first shot's vantage/action.

## Base generations still needed (do these — highest-leverage first)
| Seed | Shots | First shot vantage (spec source) |
|---|---:|---|
| `SEED_wide_booby_clear.png` | 5 | GROUND LEVEL behind a black foreground boulder, long lens, dark out-of-focus rock edge across the bottom of frame |
| `SEED_macro_tail.png` | 4 | Low, behind and slightly below the second finch at the base of the white tail, looking forward along the length of the t |
| `SEED_mutualism_clean.png` | 3 | locked-off side-on telephoto from the booby's LEFT flank at shoulder height, compressed grey sea horizon behind |
| `SEED_raw_wound.png` | 2 | Straight-down TOP-DOWN, 90° above the wing, looking into the parted white down — the only shot in the act with no finch  |
| `SEED_mutualism_clean_C.png` | 1 | Three-quarter FRONT from just below the booby's shoulder, telephoto, shallow depth of field - on the finch working the c |
| `SEED_spine_two_finch.png` | 1 | from BEHIND AND SLIGHTLY ABOVE THE TAIL, looking FORWARD up the spine |
| `SEED_booby_rear_sea.png` | 1 | from the ledge BEHIND the bird, REAR THREE-QUARTER, looking OVER its back and past its shoulder to open ocean deep in fr |
| `SEED_booby_from_behind.png` | 1 | GROUND LEVEL DIRECTLY BEHIND the bird, which faces away toward the sea, long lens |
| `SEED_swarm_six.png` | 1 | LOCKED-OFF side-on telephoto, absolutely no camera move - the only static hold in the act |
| `SEED_wide_two_islands.png` | 1 | down at rock level ON the lava shelf, long lens compressing the shelf away to a high grey sea horizon; booby side-on fil |
| `SEED_wide_ocean_ots.png` | 1 | OVER-THE-SHOULDER of the booby, from behind and just above its white back, looking out to open ocean |
| `SEED_finch_ground.png` | 1 | WORM'S-EYE from inside a lava crack at ground level, looking up and along it |
| `SEED_mutualism_clean_B.png` | 1 | HIGH and BEHIND the booby's shoulder looking down the length of its white back, shallow DOF, lava thrown out of focus be |
| `SEED_flank_stain.png` | 1 | SIDE-ON macro level with the flank, frame completely filled with plumage - no head, no horizon, no context; the most abs |

## Crop / recolor shortcuts (cheap — derive from a base gen)
| Seed | Shots | How |
|---|---:|---|
| `SEED_finch_portrait_redtip.png` | 2 | RECOLOR the beak tip red on the existing portrait (ChatGPT edit) — base `SEED_finch_portrait.png` |
| `SEED_macro_tail_high.png` | 1 | tighter/higher CROP of the tail generation — base `SEED_macro_tail.png` |
| `SEED_flank_stain_top.png` | 1 | top-down CROP of the flank-stain generation — base `SEED_flank_stain.png` |
| `SEED_pricklypear_top.png` | 1 | top-down CROP of the prickly-pear generation (or generate directly) — base `SEED_pricklypear.png` |

## Already on disk
| Seed | Shots |
|---|---:|
| `hero_still_A_booby_finch.png` | 21 |
| `hero_still_A2_macro_finch_wound.png` | 14 |
| `hero_still_B_egg_nest.png` | 14 |
| `still_booby_eye.png` | 8 |
| `SEED_finch_portrait.png` | 2 |

⚠️ **Scope note:** more seeds than the original 6. Forcing each shot onto a reachable existing
seed would reintroduce the adjacent-vantage duplication the defect pass removed. The
`SEED_mutualism_clean` A/B/C are *deliberately* distinct poses (Act-4 montage) — don't collapse them.
Also derive distinct seed FRAMES for the same-seed runs (S007-9, S058-61, S080-82) by cropping the
base still, per `EP02_DEFECT_TRIAGE.md`.