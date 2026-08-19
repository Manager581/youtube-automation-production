# TechJoint cookies — v3 handoff (owner notes on v2, 2026-08-19)

## Owner notes on cookies_v2.mp4 (verbatim intent)
1. **Some of the VO is chopped — doesn't make sense.**
2. **Almost none of the SFX line up with what's happening on screen at the right moment, and most don't sound like what's on screen.**
Fix both in a NEW session (owner's instruction). Picture is approved to work on top of; do not regenerate clips for this.

## Likely causes (verify first, then fix)
VO (assemble_cookies.py `vo_blocks()` + `build_audio()`):
- Blocks are cut from the one-pass ElevenLabs take using **whisperx word times**: `t0 = first_word.start − 0.12`, `t1 = last_word.end + 0.25`,
  with afade 0.05/0.08. whisperx word ENDS run early on trailing consonants → block tails clip ("Let's go.", "every time.", "…for ten minutes")
  and block heads can clip the first consonant. v2 also SPLIT the payoff block at "Crispy" and "gooey" (cookies_v2_config VO_BLOCKS) → more cut points.
- Fix: cut at **silence midpoints** (measure the narration waveform, e.g. `silencedetect` or RMS < −45 dB between blocks), not at word stamps;
  pad each block to the next word's start (or ≥0.4 s) instead of +0.25; listen to every block boundary (12 blocks) before rendering; consider
  un-splitting the payoff block (single "okay… every time." block anchored at C33 with C33 stretched so "Crispy" lands on C34 — or keep the
  split only if the cut is in real silence).
SFX (`cookies_v2_config.py` SFX_EVENTS):
- Events are placed at FIXED offsets per shot (e.g. egg_crack at C11+1.2 s) — never aligned to the actual action frame in each clip; several
  library keys are proxies that don't match the visual (rice_pour for sugar/flour, stir_bowl for a silicone spatula fold, tray_laydown for a
  scoop release, oven_fan, pop for the scoop).
- Fix: a per-clip alignment pass — for each of the 46 shots read `assets/techjoint_cookies/clips_v2/strips/<id>_strip.jpg` (2 fps) and note the
  exact action moment(s) (crack, pour start/end, knife hits, scoop release, tray contact, door, snap), then place SFX at those moments;
  source better-matched sounds via the existing fetcher (`pipeline_v2/ambient_bed.py` / Freesound CC0 / Pixabay; recipe in
  `reference_pixabay_freesound_sfx_fetch`): sugar/flour granular pours, metal whisk in glass bowl, silicone spatula fold, knife on wood
  chopping chocolate, cookie-scoop click + dough drop, parchment/tray, fridge seal, oven knob, rack slide, dry crisp snap, soft tear.
- Grok native audio is usable on SOME v2 clips (C18 chop peaks −3 dB, C34 snap −3 dB, C07 pour −14 dB; C33 −62 dB useless): consider mixing the
  synced Grok foley under the library layer where it exists (assembler currently strips all clip audio with `-an` in make_segment).
- Drop/lower anything that doesn't clearly match; fewer, right sounds > many proxies.

## State
- Master: `output/techjoint_cookies/cookies_v2.mp4` (1080p24, 3:15); watch `~/Movies/TechJoint_Cookies_v2_watch.mp4`; timeline JSON
  `output/techjoint_cookies/cookies_v2_timeline.json` (shots t0/t1, VO block placement, SFX events).
- Re-render: `venv/bin/python research/techjoint_cookies/assemble_cookies.py --variant v2 [--preview] -o output/techjoint_cookies/cookies_v3.mp4`
- VO: `audio/techjoint_cookies/narration.wav` + `narration.json` (whisperx words), ONE pass, do not re-roll.
- Clips: `assets/techjoint_cookies/clips_v2/` (+ `strips/`), ledger `research/techjoint_cookies/grok_ledger_v2.tsv`.
- Rules still in force: hands-only, phone-real, close-ups, crispy/gooey, no paid spend without asking, contact-sheet/strip QA before showing,
  reuse existing scripts.
