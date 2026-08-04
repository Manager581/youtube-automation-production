# GENESIS OVERVIEW — SHOT LEDGER v2 (post-audit master)

v1 was audited by a 6-agent adversarial pass (4 FAIL / 2 PASS_WITH_FIXES — full findings in the
session audit output; summary below). v2 applies every blocker + should-fix. **This file is the
master; `GENESIS_PROMPT_BOOK.md` is v1 and must have the per-shot DELTAS below applied before any
prompt is pasted.**

**What the audit killed in v1:** uniform 5s metronome (the exact fake rhythm the measured grammar
debunks); cuts placed by clock division instead of whisperx word onsets (Acts 2, 4, 7, 12 all had
the payoff word playing over the WRONG shot); two crops that physically cannot exclude faces
(G039, G046); one crop too small to survive upscale (G023, G035); a divine-figure violation
(G038 "inner glow of the taller figure" = God as a body — breaks the channel's core rule); the
dinosaur payoff stepped on 19s early (G004); missing overlay pass (verse refs = the #1 trust
signal); missing owner sign-off gate before spend.

## RHYTHM MODEL (replaces the metronome)
Two tempos, per grammar R6: **establish holds** (5–8s: act openers G001, G012, G017, G024, G028,
G031, G034, G043, G045, G049) and **word-aligned fast chains** (1.5–2.5s) on the two R3 lists,
with hard cuts snapped to whisperx word onsets. **Assembler rule: EVERY interior cut snaps to the
nearest word onset within 0.3s; every turn-word (but/then/so) inside a span gets a cut (R2).**
Onsets come from `audio/christ_cares/genesis_overview_whisperx.json` at build time — times below
marked ~ are snap targets, not clock divisions.

## STEP 0 — OWNER GATES (nothing generates before these)
1. **Silhouette human policy sign-off** — test cases S11 (Jacob profile) + S13 (brothers' profiles): approve as-is, or order darkened/re-genned variants.
2. **G038 divine-wrestler decision** — Option A (default): re-gen seed so the opponent is a blinding mass of light, no second body. Option B: keep the humanoid wrestler with an on-screen "Genesis 32:24 — 'a Man'" citation. v1's "inner glow of the taller figure" wording is dead either way.
3. **Title reposition** — this 4:35 is the channel trailer/anchor, NOT the "full story/full movie" play: e.g. "All of Genesis in 5 Minutes — The True Account". The 8–20 min chapter episodes are the monetization spine (recon: mid-roll economics + "chapter by chapter" demand gap).
4. **Grok tier check** — confirm plan/limits before a ~50-gen grind; verify max clip length on the first G051 take (8.2s hold needs it, else freeze-tail fallback).

## LEDGER (Δ = delta to apply to PROMPT_BOOK v1 entry)
| Shot | In–Out | Size | Seed | Δ / notes |
|---|---|---|---|---|
| G001 | 0–4.5 | WS | S01a | — |
| G002 | 4.5–9.0 | CU | NEW water_light_cu | — |
| G003 | 9.0–13.5 | XCU | CROP S01b | Δ motion += "the light stays empty — pure light and particles only, no shapes form inside it" |
| G004 | 13.5–~18.42 | WS | **CROP S02 creature-free** (waterfall/valley band) | Δ delete creature-sway clause; sauropods must NOT appear before G007 (day-order + payoff protection) |
| G005c | ~18.42–~20.16 | CU | slice of G002 clip | "Sky and sea" flash — chain starts, no new gens |
| G006c | ~20.16–~22.10 | MS | slice of G007 clip | "Land bursting green" flash |
| G007c | ~22.10–~24.58 | WS | slice of G005 clip (stars — retyped WS, breaks the MS triple) | "Stars flung across the dark" flash |
| G008c | ~24.58–27.0 | MS | slice of G006 clip | "Seas that suddenly swarm" flash |
| G007 | 27.0–32.5 | MS | NEW herds_plain (full clip) | herd small + distant; frame-strip legs/overlaps |
| G008 | 32.5–38.44 | CU | NEW sauropod_neck | Δ no birds clause (or add birds to IMAGE); motion = "head turns slowly, neck sways gently" (pose-preserving — no rise from a risen pose) |
| G009 | 38.44–44.0 | WS | S03 | priority frame-strip (lit skin/hair detail = face-emergence risk) |
| G010 | 44.0–49.5 | XCU | NEW dust_breath | differentiate from G003 (tighter, warmer, denser dust) |
| G011 | 49.5–54.96 | MS | NEW adam_eve_walk | Δ IMAGE += "both figures pure dark featureless silhouettes — no skin, clothing, or body detail discernible"; priority frame-strip |
| G012 | 54.96–~63.4 | WS | S04 | extended hold (theology line lives here) |
| G013 | ~63.4–~69.6 | XCU | NEW serpent_eye | Δ retimed to carry "Then a serpent whispers... 'Has God indeed said...?'"; IMAGE += "pale gray-scaled serpent matching a massive coiled python" (continuity w/ S04) |
| G014 | ~69.6–~71.2 | CU | NEW hand_fruit | "They eat." lands here — 1.6s punch |
| G015 | ~71.2–75.5 | MS | NEW garden_dimming | "everything breaks. Shame. Hiding. Blame." — assembler may micro-slice on the three onsets |
| G016 | 75.5–81.2 | CU | CROP S04 **respec: root-base window ~y470–780** (trunk base + warm fringe IN frame) | motion now matches crop content |
| G017 | 81.2–87.0 | WS | S05 | — |
| G018 | 87.0–93.0 | XCU | CROP S05 shadow-ground | — |
| G019 | 93.0–99.0 | WS | NEW dawn_crack | — |
| G020 | 99.0–105.16 | MS | NEW light_path | Δ IMAGE += "the path stops partway across the terrain, unlit darkness between its end and the glowing horizon" (gives the motion somewhere to go) |
| G021 | 105.16–110.0 | CU | NEW dark_rain_field | — |
| G022a/b | 110.0–114.5 | WS+MS | violence_walk + **violence_mob (owner add 2026-08-04)** | split at word onset ~112.2; mob = solid-black torch crowd (people density per owner) |
| G023 | 114.5–118.92 | MS | **NEW burning_horizon** (replaces crop — v1 crop = 620×60px sliver, unusable) | SURGE shot: fires spread faster, smoke thickens quicker; camera stays restrained |
| G024 | 118.92–124.0 | WS | S07 | Δ restore FULL rider; SURGE: storm at full violence |
| G025a/b | 124.0–~131.3 | WS+CU | **ark_door_family (owner add 2026-08-04)** + CROP window | a: family up the ramp on "One family. One door."; b: window crop on "God Himself shuts them in"; window stays empty |
| G026 | ~131.3–~134.1 | MS | **flood_creatures (owner replacement 2026-08-04)** — sauropods in the swell + distant ark; peaks_submerge = fallback | SURGE; the channel's dino×flood crossover hook lands here |
| G027 | ~134.1–140.36 | WS | NEW rainbow_calm | — |
| G028 | 140.36–146.0 | WS | S08 | — |
| G029 | 146.0–150.5 | MS | CROP S08 base | SURGE: scattering energy |
| G030 | 150.5–155.34 | XCU | NEW one_ember | — |
| G031 | 155.34–161.0 | WS | S09 | — |
| G032 | 161.0–167.0 | MS | NEW desert_ridge | — |
| G033 | 167.0–173.12 | CU | CROP S09 glow-between-doors | Δ figure IS in the crop — governed callback: "the robed man stands motionless, seen from behind, face never visible" |
| G034 | 173.12–179.0 | WS | S10 | — |
| G035 | 179.0–185.5 | MS | **NEW he_believed** (closer from-behind robed figure under starfield; v1 crop = 110px figure, unusable) | rim-lit, featureless |
| G036 | 185.5–191.84 | XCU | NEW starfield_pure | — |
| G037a/b | 191.84–196.5 | WS+MS | **knife_raised (owner add 2026-08-04)** + ram_thicket (STANDING retake) | a: knife over Isaac on "spared on a mountain"; b: ram on "God provides the sacrifice Himself"; both static-strain motion |
| G038 | 196.5–201.0 | WS | **OWNER GATE #2** (Option A: re-gen seed, opponent = blinding light mass; Option B: S11 + on-screen Gen 32:24 cite) | "inner glow of taller figure" wording DELETED both ways; motion = static strain |
| G039 | 201.0–205.28 | CU | **NEW clasped_hands** (style block + "two clasped silhouetted hands and forearms locked against a blazing dawn flare — only hands and forearms, no heads, no bodies"; v1 crop cannot exclude the heads) | — |
| G040 | 205.28–~210.0 | MS | NEW coat_torn | carries "Sold... Enslaved" |
| G041 | ~210.0–~212.0 | CU | NEW pit_up | carries "Slandered. Imprisoned." — 2.0s punch; Δ "brightens slowly" (not harshly); budget 2–3 takes, mandatory frame-strip |
| G042 | ~212.0–~213.7 | XCU | NEW chains_cell | carries "Forgotten." — 1.7s punch (Joseph chain = the R3 burst) |
| G043 | ~213.7–224.5 | WS | S12 | in-point ON "Then raised" (R2 turn-word); long triumphant hold is the R6 contrast |
| G044 | 224.5–229.84 | MS | CROP S12 windows | Δ motion drops "toward the throne below" (off-frame); += "the carved wall reliefs stay completely still" |
| G045 | 229.84–~235.5 | WS | S13 — **OWNER GATE #1** | Δ += "the reclining figure stays completely still"; darken/crush brother profiles if owner orders |
| G046 | ~235.5–241.0 | XCU | CROP S13 **respec: scepter + gripping silhouetted hand, head excluded, framed below the shoulder; upscale before i2v** | Δ motion += "the silhouetted hand stays still; no face or head enters frame" |
| G047 | 241.0–247.5 | WS | S01a reprise | Δ motion phrased as change-in-motion: "the rays soften and slow, the waves gradually subside and settle, camera pulling back very slowly" (frame 1 is stormy — cannot start calm). Optional owner call: pull in-point to ~237.7 so the bookend lands on the word "opens" |
| G048 | 247.5–253.88 | MS | NEW scroll_closed | — |
| G049 | 253.88–260.0 | WS | S14 | — |
| G050a | 260.0–~261.87 | flash | slice G008 clip | "The dinosaurs." — onsets from whisperx, NOT a 1.7s grid |
| G050b | ~261.87–~263.05 | flash | slice G024 clip | "The flood." |
| G050c | ~263.05–~264.38 | flash | **slice G021 clip** (Cain's field — v1's G015 garden was the wrong era) | "Cain's wife." |
| G050d | ~264.38–267.0 | flash | slice G023 clip | "The Nephilim." + breath |
| G051 | 267.0–275.2 | XCU | CROP S14 pages | verify max gen length on THIS take first; freeze-tail on the settling frame if short |

**Counts:** 50 base gens (14 anchors incl. reprise + crops + NEW) — NEW seeds now 26 (v1's 23 + burning_horizon + he_believed + clasped_hands; +1 more if G038 Option A). Flash chain P2 + Joseph chain + G050 = sliced from rendered clips, zero extra gens.

## BUILD ORDER v2
0. **OWNER GATES above — all four resolved first.**
1. Gen 26 NEW seeds in the locked thread → faceless-gate each → contact sheet to owner.
2. Cut CROPs per respec'd windows (incl. upscale where marked) → `gate_crop_distinct`.
3. Grok i2v grind ~50 gens → frame-strip EVERY clip (priority: G009, G011, G025, G038, G041, G045, G046) → faceless+physics gate.
4. Assembler v2: whisperx-snapped cuts (0.3s rule + R2 turn-words), flash chains, micro-slice logic.
5. **Overlay pass (NEW): verse-reference lower-thirds at the 8 NKJV quotes + attribution card** — the accuracy-trust signal + anti-slop craft evidence.
6. Watch + contact sheet BEFORE reporting. Music/SFX pass after owner approves motion.

## Series notes (from audit, so they don't get lost)
- Per-book palette evolution for the chapter series (sameness = the purge trigger); divine-light grammar stays constant.
- Export loop-friendly masters → sleep/ambient 8-hr cut is near-free (recon: #2 demand lane); multilingual dubs = cheap expansion.
- Future Nephilim episode gets a bespoke seed (G050d's burning horizon is a placeholder tease).
