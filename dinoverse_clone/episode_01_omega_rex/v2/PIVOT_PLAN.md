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
Google Sheet export: https://docs.google.com/spreadsheets/d/1h5cR59OM-hV7DIlWgO0O6lperWEDiSYHExyNbpV1Tt4
NEXT = per-zone stills sessions (production loop above).

## STILLS PROGRESS (update per zone)
- ✅ Zone 1 Entry S13–S16 (2026-07-07, owner approved) — `v2/stills/`, thread: chatgpt.com/c/6a4d6961-e710-83ea-8168-e2e7b79ff170
- ✅ Zone 2 Carnotaurus S17–S23 (2026-07-07, owner approved) — thread: chatgpt.com/c/6a4d762a-1aa0-83ea-8032-33a74a9499a1
- ⬜ NEXT = Zone 3 Quetzalcoatlus S24–S30 (7 shots), then Aquatic S31–S42, etc.
- Method per zone: fresh ChatGPT thread → paste characters_v2 block (humans + THIS zone's creature sheet + brand kit) → each shot's "Image prompt (still)" verbatim, "Same park… keep consistent" prefix from IMAGE 2 on → download (see faster trick in memory `reference_chatgpt_pov_still_series_method`: stash src URLs + blob sizes in localStorage from the gen tab, then ONE fetch+a.download per FRESH tab, no re-scrolling) → mv to `v2/stills/Sxx.png` → 2-col contact sheet → owner approves → status=still in `../STORYBOARD.tsv` → commit.
- v2 stills live in `v2/stills/` — do NOT overwrite the 76 v1 reference stills in `../stills/`.

## HOW TO RESUME (paste into a fresh session)
"Read dinoverse_clone/episode_01_omega_rex/v2/PIVOT_PLAN.md and SHOOTING_SCRIPT_v2.md. Rebuild
build_storyboard.py around the v2 script (89 scenes, Luke+GF, DINO ZOO brand): per-shot image prompts
in Sik's verified style WITH viewing-mode infrastructure baked in, i2v prompts with dialogue, TRIM
cold-open flashes, Extend flags, silent-shot layer per PIVOT_PLAN §4. Write characters_v2.txt. Then
regenerate STORYBOARD.tsv and export it to the Google Sheet. Do NOT start still generation in the
same session."
