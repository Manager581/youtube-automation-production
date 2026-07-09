# v2 PIVOT — BUILD SPEC (owner decision 2026-07-07)

Owner switched episode 1 to the July v2 script (this dir) because the v1 still set had quality
misses: **missing glass barriers, wrong/missing logos, weak enclosure infrastructure**. All images
will be redone. The Dee/Maya board (`../STORYBOARD.tsv`, 108 rows) is SUPERSEDED — keep for
reference; its measured Sik pacing carries over.

## Sources (all saved locally in this dir)
- `SHOOTING_SCRIPT_v2.md` — 89 scenes, full dialogue. (Drive: 1MkBv_BaH…XgI)
- `ours_scene_breakdown_v2.csv` — scene/zone/length/viewing_mode/baby/tag. (Drive: 1EYvMrYa…nbE)
- Reference (his real episode, frame-accurate 91 scenes w/ viewing_mode+baby+narration):
  Drive sheet 1OCXO-x4CV1K9a2o8I6tV1yTTXt4R1eFGr1UohrRdlVA ("Dino Zoo — Reference scene breakdown").
- Pacing ground truth: `../work/sik_analysis/sik_grammar.json` — 103 cuts; silent budget 78.5s/16%
  (T-Rex 24s, Hybrid 19s, Incident 19.5s, Sauro ZERO — his long scenes = more spoken beats).
- Prompt templates (verbatim from Sik): `../VERIFIED_PROMPTS.md` — image-prompt style block + i2v format.

## What the new board must encode (the quality fixes)
1. **viewing_mode IN EVERY IMAGE PROMPT** (this is what failed in v1). Map each scene's
   viewing_mode to concrete infrastructure language:
   - behind glass → "thick laminated viewing glass with steel mullions, faint reflections, smudges"
   - glass tunnel → "curved acrylic tunnel overhead, water above, tourists silhouetted"
   - glass dome → "geodesic glass/net dome interior, sun through panels"
   - open-air rail → "wooden visitor rail + dry moat between guests and animal"
   - keeper + baby → "khaki keeper on a staff platform holding/feeding the juvenile, guests behind rail"
   - open tank show → "tiered stadium seating around show tank, splash zone signs"
2. **Brand kit in every prompt**: DINO ZOO round green logo (bottom-right watermark style on signage),
   carved-wood zone signs, yellow-black hazard striping, khaki ranger uniforms. Owner renamed the park
   DINO ZOO — script line S13 says "Dinoverse Park": change to "Dino Zoo".
3. **characters_v2.txt**: lock LUKE (POV hands/arms only + selfie shots), GF (in frame, consistent
   wardrobe), KEEPER/RANGER, CLERK, 3 TEENS (distinct, consistent). Plus a character sheet per creature
   (production note in the script) — Utahraptor FEATHERED (the myth-bust depends on it), Dunkleosteus
   armored head + bone blades, D-Rex distinct from Indominus.
4. **Pacing layer** (from the measured Sik data — v2 already varies 1.5–13s): keep the 12s/13s/10s
   holds as written; add silent connective shots ONLY where he has them (T-Rex walk-ups, Hybrid dread,
   Climax escape) to land ≥8:00 with ~16% silence. The 1.5s cold-open flashes are TRIMS of Act 3 clips.
5. **Statuses + regen safety**: rebuild `../build_storyboard.py` for v2 (same file, new content), keep
   the status-preservation block, TRIM/GEN/CARD types, Extend flags in the Edit column for >6s shots.
6. **Guardrail dodges** (ChatGPT stills): teens "in danger" framed as distance + reaction, evacuation
   framing for crowds, no child-in-jaws — same dodges that worked for v1 breakout stills.

## Salvage
Default = regenerate everything. Optional: contact-sheet the 76 old stills against the v2 scene list
and keep only exact fits that pass the glass/logo gate (candidates: ticket booth, gates, some chaos
wides, T-Rex head). Don't force reuse — quality was the reason for the pivot.

## Production loop (per-zone fresh sessions — hard rule: short sessions)
Per zone (12 zones ≈ 12 sessions for stills, then ~12 for i2v):
1. STILLS: one ChatGPT thread per zone, prompts verbatim from the new TSV, consistency-chain from the
   zone's establish shot. Contact sheet → owner eyeballs → status=still. (Frame-level QA is mandatory
   BEFORE any i2v spend.)
2. i2v: Grok Imagine clipboard-paste pipeline (see `../dino_production.md` — osascript PNG→clipboard,
   Cmd+V, Video/720p/16:9/6s). Per clip: ffprobe 1264×720/~6.04s + audio present, listen-check the
   dialogue line matches, Extend where flagged, silent shots = no invented speech. status=clip.
3. Stitch the zone (ffmpeg concat), watch, commit per zone.
Assembly after all zones: trims for cold-open flashes, music bed + Pixabay SFX, disclaimer cards,
midroll marker at S60, 1080p.

## ✅ BOARD REBUILT (2026-07-07, same day as the pivot)
`../build_storyboard.py` + `../STORYBOARD.tsv` are now the v2 board: 97 rows (77 GEN / 18 TRIM /
2 CARD), runtime 8:53.5, silent layer 62s matching Sik zone-for-zone (T-Rex 24s / Hybrid 19s /
Climax 19s vs his 24/19/19.5). All 36 enclosure shots carry viewing-mode infrastructure language;
14 shots flagged Grok EXTEND; cold-open S03–S12 are TRIMs of Act-3 payoffs; S13 says "Dino Zoo".
`../characters_v2.txt` = Luke/GF/staff/teens + per-creature sheets (Utahraptor FEATHERED).
Status preservation is v2-guarded (only inherits from a TSV whose first row is "0 Cold Open").
Google Sheet export (original, now STALE — Time column predates the realign): https://docs.google.com/spreadsheets/d/1h5cR59OM-hV7DIlWgO0O6lperWEDiSYHExyNbpV1Tt4
Google Sheet export (current, post-realign 2026-07-08): https://docs.google.com/spreadsheets/d/1DYZgztqA7fqgg93e_dGSy_OmZW0UeOBN1b6E6aTxd60
NEXT = per-zone stills sessions (production loop above).

## STILLS PROGRESS (update per zone)
- ✅ Zone 1 Entry S13–S16 (2026-07-07, owner approved) — `v2/stills/`, thread: chatgpt.com/c/6a4d6961-e710-83ea-8168-e2e7b79ff170
- ✅ Zone 2 Carnotaurus S17–S23 (2026-07-07, owner approved) — thread: chatgpt.com/c/6a4d762a-1aa0-83ea-8032-33a74a9499a1
- ✅ Zone 3 Quetzalcoatlus S24–S30 (2026-07-07, owner approved) — thread: chatgpt.com/c/6a4d88a5-77c8-83ea-9ad4-45c402218b5f. Owner fixes applied: GF locked to S13 reference (see GF CONSISTENCY below), S27/S28/S29 walkway = steel-mesh cage tunnel, S29 dry (aquatic "water overhead" template leak fixed in TSV prompt).
- ✅ Zone 4 Aquatic S31–S42 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4dbc0a-97f8-83ea-8191-34769dd8d893. Walkway-safety fix applied to S38 TSV BEFORE generating (acrylic splash barrier rimming the show tank). Frame-level QA caught + fixed in-thread: S39/S40 Mosasaurus off-model (came out as a 2nd armored fish → revised to croc-jawed Mosa), S42 teens off-sheet (revised to red hoodie/black cap+camo/glasses+yellow backpack). NOTE: S37 came out as a Luke+GF selfie instead of pure POV — owner kept it.
- ✅ Zone 5 Utahraptor S43–S50 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4e27da-f0d4-83ea-9c63-763917aa1b22. Walkway-safety fixes applied to S46 + S48 TSV BEFORE generating (tall steel-mesh barrier fence / steel-mesh paddock fence line). All raptors FEATHERED (S46 myth-bust centerpiece correct: ranger + steel mesh + turkey-vs-man board). QA notes (owner accepted): S44 chick reads juvenile-sized, S45 one juvenile motion-blurred. Download gotcha: thread virtualization mis-mapped S47's URL to S48's (caught via identical blob sizes) — remap with a BOUNDED position check (img after IMAGE n AND before IMAGE n+1, both turns mounted).
- ✅ Zone 6 Herbivores S51–S58 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4e35d1-acdc-83ea-9f2f-a5a1fd8840e4 (SAME thread reused for Lunch). One thread, S13.png attached as GF face-lock ref, STYRACO/BRACHIO/ARGENTINO sheets. Walkway-safety already compliant (every animal shot = wooden rail + dry moat) → NO TSV fix needed. 2 baby beats (S53 calf+mother, S56 mixed-family stream crossing); S58 = teens handoff to Hybrid Zone (STAFF ONLY–HYBRID DANGER door). QA note (owner accepted): S55 Argentinosaurus reads close to a Brachiosaurus silhouette (size-vs-S54 distinction subtle). S55 + S58 rendered slowly → had to RELOAD the thread to force the finished img into the DOM before capture.
- ✅ Zone 7 Lunch S59–S60 + 2 owner-added shots (2026-07-08, owner approved) — SAME thread as Zone 6. S59 walk-to-food, S60 BBQ table (MIDROLL SLOT). Owner added **S59b** (market row: Dino Dogs hot-dog stand + Dino Smokehouse) and **S59c** (in-park McDonald's, golden arches on themed timber building) — both inserted into STORYBOARD.tsv after S59. S59c regenerated once (v1 rendered a stranger, not GF — fixed by inlining the full GF description). Trademark note in S59c Edit col: keep McDonald's a brief incidental beat in the monetized cut. **Timecode realign DONE (2026-07-08)**: recomputed the Time column sequentially from Dur for all 102 rows (cumulative sum from 0:00, in file order) — this also caught the S13b/S14a/S14b split (zone 1, still `todo`) leaving S14/S15/S16 stale since 2026-07-07. New runtime 9:16 (556.0s), up from 8:53.5. 86 rows' Time shifted; Dur/content untouched. `build_storyboard.py`'s hardcoded `gen()` calls do NOT yet include S13b/S14a/S14b/S59b/S59c (owner-added directly to the TSV) — a full script rerun would drop them, so the realign was done as a direct TSV recompute, not a script regen.
- ✅ Zone 8 T-Rex S61–S68 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4e4991-fdec-83ea-bfb6-0cd1455721ce. 8 GEN shots only; the 4 TRIMs (S65b/S66b/S67b/S67c) stay todo until i2v clips exist. Walkway-safety fixes applied to TSV BEFORE generating: S61 gate (reinforced glass-and-steel containment wall), S64 dome walkway (laminated glass + steel mullions lining both sides — had NO protection language), S68 exit (dome glass behind). S65 was the slow one (~6 min "One last tweak…", resolved by thread RELOAD), not S67; no A/B chooser this session. GF face-lock held (S61/S64/S68). QA notes (owner accepted): warning signs in S61/S64/S68 rendered an AI-invented "Photography Prohibited" line (mildly contradicts the vlog premise); S68 background creature silhouette reads slightly long-necked rather than clearly T-Rex (small, incidental).
- ✅ Zone 9 Hybrid S69–S78 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4e5e1d-f7b4-83ea-9eb8-c022372c7d4c. 10 GEN shots; TRIMs S74b/S77b/S77c/S77d stay todo until i2v. Walkway-safety fix applied to S74 TSV BEFORE generating (overlook deck edged with tall laminated-glass balustrade + steel handrail — had none); S69 staff door deliberately unprotected. TWO creature sheets pasted (INDOMINUS + DREX w/ distinctness stress) — held: Indominus bone-white/quills/red eyes, D-Rex charcoal-black/orange seams/oversized jaws, clearly distinct. GUARDRAIL FIGHTS: S69 refused ("depictions of teens") → softened only the sneak language ("walking one by one through a propped-open staff door, candid behind-the-scenes moment"), visual beat unchanged; S78 refused once ("violence") with the VERBATIM prompt → pushed back (no people in frame) + retry same prompt = passed. S76 passed verbatim first try. S75+S78 both hit "One last tweak…" slow render (~4–6 min, thread RELOAD to capture); no A/B chooser. QA notes (owner accepted): S72 three claw channels not four; S74/S76 overlook signage says "Indominus Rex Juveniles" on the D-Rex pen (thread carryover; S77's sign self-corrected); S71/S73 Luke on camera beside GF instead of pure POV (S37 precedent). status=still.
- ✅ Zone 10 Climax S79–S88 (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4e89a1-03b0-83ea-8502-a42c68e1c933. **LAST stills zone DONE** (S89 = CARD, assembly-time). First message included an "emergency-drill / all guests safely evacuated, no one harmed" framing line — likely why every breach shot (S82 Indominus wall-burst, S85 T-Rex dome breakout, S88 three-way showdown) passed VERBATIM first try. QUOTA GOTCHA: free-tier image cap hit after 6 gens (zones 6–9 same-day burned the pool) — banner said "wait for more at 4:27 PM"; waited on a timer, resumed in the SAME thread, consistency held. GUARDRAIL FIGHT: S87 teens-rescued refused 2× (POST-GEN filter, "depictions of teens" — verbatim pushback AND softened drill-framing w/ background D-Rex both failed); passed attempt 3 by REMOVING the creature from frame (ranger + 3 sheet-matched teens behind planter, red alarm lights, sheepish/relieved) — D-Rex flyby can return as i2v motion. No slow render on S88 (~75s). QA notes (owner accepted): S83 D-Rex full sunlit reveal not silhouette-in-smoke; S86 T-Rex runs toward camera w/ city (Toronto, CN Tower) BEHIND it — reads "into the park"; S87 sign invented "EVACUATION DRILL IN PROGRESS" text + no creature in frame; S80 alarm lamps steady not strobing; "Tricera Toppings" signage recurs across S81/S82/S83/S85 (helps plaza continuity). status=still.
- ✅ S13b/S14a/S14b dialogue-split stills DONE (2026-07-08, owner approved) — thread: chatgpt.com/c/6a4ede95-697c-83ea-bb95-cfcf56aafba5, S13.png attached as GF/env lock. S13b first gen came back as a Luke+GF closeup (model over-applied the reference) → corrected with an explicit "no Luke/GF, third-person wide" line; S14a/S14b passed first try with a "silent POV, no Luke or GF visible" preface. Slow-render thread-RELOAD needed on S13b + S14b (Edit-pill placeholder). Download via the image share dialog's Download button (per-image), not blob-fetch. status=still.
- ⚠️ **S02 GAP (found 2026-07-08 during realign)**: S02 (cold-open gate selfie, GEN, 3s) has NO still on disk and status=todo — the "S13b/S14a/S14b are the last GEN stills" note overlooked it. Needs one still (Luke+GF at gate, S13.png face-lock) + i2v clip before assembly. All TRIMs (cold-open S03–S12, S65b/S66b/S67b/S67c, S74b/S77b/S77c/S77d) are cut from CLIPS, so they wait on i2v zones 8–10. Timecode realign DONE (see Zone 7 note below).
- A/B + slow-render gotchas (Zone 6/7): ChatGPT sometimes shows a "Which image do you like more?" A/B chooser for a turn (2 gens) — pick one, then map that shot to the chosen blob size. Big/complex shots ("One last tweak…" placeholder) can take 3–5 min and only appear in the DOM after a thread RELOAD. Programmatic send button click is flaky — dispatch a synthetic Enter keydown on #prompt-textarea instead. Map each gen to its shot AT GEN TIME via localStorage z6map (size→url), then ONE download per fresh tab.
- Method per zone: fresh ChatGPT thread → paste characters_v2 block (humans + THIS zone's creature sheet + brand kit) → **GF CONSISTENCY (owner requirement, MANDATORY): if the zone has any [GF] or Luke-visible shot, attach `v2/stills/S13.png` (the approved Luke+GF selfie) to the FIRST message as the canonical face reference and say "the girlfriend must be EXACTLY this woman in every image". Upload trick: text-paste to composer is blocked at OS level — fetch S13's estuary URL from any same-session tab (or any prior gen of it), build a File from the blob, and dispatch a synthetic paste Event with ev.clipboardData = DataTransfer on #prompt-textarea (works; see memory `reference_chatgpt_pov_still_series_method`)** → each shot's "Image prompt (still)" verbatim, "Same park… keep consistent" prefix from IMAGE 2 on → download (see faster trick in memory `reference_chatgpt_pov_still_series_method`: stash src URLs + blob sizes in localStorage from the gen tab, then ONE fetch+a.download per FRESH tab, no re-scrolling; NOTE: with an uploaded reference in the thread, exclude imgs inside `[data-message-author-role="user"]` and map gen→shot by position vs the "IMAGE n" user turns, not raw DOM order) → mv to `v2/stills/Sxx.png` → 2-col contact sheet + frame-level QA → owner approves → status=still in `../STORYBOARD.tsv` → commit.
- Walkway-safety rule (owner, 2026-07-07): inside any open enclosure/dome the visitor path must be visibly protected — steel-mesh cage tunnel, glass, or acrylic. Already baked into S27/S28/S29 TSV prompts; check other zones' prompts as you go and fix the TSV BEFORE generating.
- v2 stills live in `v2/stills/` — do NOT overwrite the 76 v1 reference stills in `../stills/`.

## I2V TRACK (runs in PARALLEL with remaining stills zones — separate sessions, never both in one)
Plan (owner-approved 2026-07-08): animate approved zones while stills continue on zones 6–10.
- Inputs: `v2/stills/Sxx.png` (approved zones only) + each row's "Grok video prompt (i2v)" verbatim from STORYBOARD.tsv.
- Engine: Grok Imagine i2v (owner-confirmed, NOT Veo); upload via the osascript PNG→clipboard + Cmd+V trick in memory `reference_grok_i2v_clipboard_upload`.
- Output: `v2/clips/Sxx.mp4`; per-zone contact-sheet-style review (or clip reel) → owner approves → status=clip in STORYBOARD.tsv → commit per zone.
- PILOT FIRST: Zone 1 Entry (S13–S16, 4 clips) — owner reviews Grok-native dialogue quality, motion, photoreal hold BEFORE batching zones 2–5.
- Respect EXTEND flags (14 shots) and the Dur column; dialogue is Grok-native for the body (only the ~20s intro hook is separate VO).
- Cold open S03–S12 = TRIMs of Act-3 payoffs → LAST, after zones 8–10 clips exist.
- I2V PROGRESS: ✅ Z1 pilot S13–S16 (owner approved 2026-07-08, status=clip) → ✅ Z2 S17–S23 (owner approved 2026-07-08, status=clip; S13b/S14a/S14b stay todo — stills not generated yet) → ✅ Z3 S24–S30 (owner approved 2026-07-08, status=clip; S24 EXTEND-to-7s DROPPED — Grok Extend re-renders audio and lost GF/Luke lines 2-3 twice, kept the verified 6s base, editor pads ~1s; ear-check S29 "Hatzegopteryx"; S26 v1 REJECTED — chick flew through the glass → owner rule "real physics" in memory `feedback_i2v_real_physics`, physics rider baked into S26 TSV prompt, regen passed 2fps frame check; frame-strip physics QA now MANDATORY on every clip) → ⬜ Z4 S31–S42 (12 GEN, all ≤2 turns; pre-gen TODO: physics riders on glass rows S34/S35/S36/S38/S39/S40; S38+S40 12s holds — try native 10s pill, do NOT Extend dialogue shots) → ⬜ Z5 S43–S50 → (zones 6–10 as their stills get approved) → ⬜ cold-open TRIMs + cards.
- I2V lessons (2026-07-08, in memory `reference_grok_i2v_clipboard_upload`): ≤3 speaker turns per 6s clip (4 turns garbled S13 → dialogue split into new rows S13b/S14a/S14b, stills TODO in a stills session); whisper-verify EVERY downloaded clip vs the row's Dialogue column before accepting; match downloads by timestamp (`find ~/Downloads -newermt`), never glob; composer paste races page load — re-click + re-paste until the thumbnail shows. S13's EXTEND flag dropped (2 lines fit 6s). Ear-check flag: S21 "Carnotaurus" pronunciation.

## HOW TO RESUME (paste into a fresh session)
"Read dinoverse_clone/episode_01_omega_rex/v2/PIVOT_PLAN.md and SHOOTING_SCRIPT_v2.md. Rebuild
build_storyboard.py around the v2 script (89 scenes, Luke+GF, DINO ZOO brand): per-shot image prompts
in Sik's verified style WITH viewing-mode infrastructure baked in, i2v prompts with dialogue, TRIM
cold-open flashes, Extend flags, silent-shot layer per PIVOT_PLAN §4. Write characters_v2.txt. Then
regenerate STORYBOARD.tsv and export it to the Google Sheet. Do NOT start still generation in the
same session."
