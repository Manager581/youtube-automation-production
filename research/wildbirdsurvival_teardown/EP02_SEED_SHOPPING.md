# EP02 — SEED SHOPPING LIST (generated)
_Auto-generated from `ep02_shots.json` by `gen_seed_shopping.py`. Do not hand-edit — re-run it._

**0 base generations + 0 crop/recolor shortcuts still needed; 24 seed(s) already on disk.**

The defect pass grew the seed list because several shots' framings were unreachable from their
assigned seed (Grok i2v begins on the seed's frame 1). Each new seed traces to a seed-capability
defect an agent grounded by opening the actual PNG. Prompts for the original six are in
`EP02_SEED_PROMPTS.md`; write the new ones from each seed's first shot's vantage/action.

## Base generations still needed (do these — highest-leverage first)
| Seed | Shots | First shot vantage (spec source) |
|---|---:|---|

## Crop / recolor shortcuts (cheap — derive from a base gen)
| Seed | Shots | How |
|---|---:|---|

## Already on disk
| Seed | Shots |
|---|---:|
| `hero_still_A_booby_finch.png` | 21 |
| `hero_still_A2_macro_finch_wound.png` | 14 |
| `hero_still_B_egg_nest.png` | 13 |
| `still_booby_eye.png` | 8 |
| `SEED_wide_booby_clear.png` | 5 |
| `SEED_macro_tail.png` | 4 |
| `SEED_mutualism_clean.png` | 3 |
| `SEED_raw_wound.png` | 2 |
| `SEED_finch_portrait_redtip.png` | 2 |
| `SEED_finch_portrait.png` | 2 |
| `SEED_macro_tail_high.png` | 1 |
| `SEED_flank_stain_top.png` | 1 |
| `SEED_mutualism_clean_C.png` | 1 |
| `SEED_spine_two_finch.png` | 1 |
| `SEED_booby_rear_sea.png` | 1 |
| `SEED_booby_from_behind.png` | 1 |
| `SEED_swarm_six.png` | 1 |
| `SEED_wide_two_islands.png` | 1 |
| `SEED_wide_ocean_ots.png` | 1 |
| `SEED_finch_ground.png` | 1 |
| `SEED_pricklypear_top.png` | 1 |
| `SEED_egg_xcu_feet.png` | 1 |
| `SEED_mutualism_clean_B.png` | 1 |
| `SEED_flank_stain.png` | 1 |

⚠️ **Scope note:** more seeds than the original 6. Forcing each shot onto a reachable existing
seed would reintroduce the adjacent-vantage duplication the defect pass removed. The
`SEED_mutualism_clean` A/B/C are *deliberately* distinct poses (Act-4 montage) — don't collapse them.
Also derive distinct seed FRAMES for the same-seed runs (S007-9, S058-61, S080-82) by cropping the
base still, per `EP02_DEFECT_TRIAGE.md`.