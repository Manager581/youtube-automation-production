# START HERE — paste the block below into a new session

You (the owner) do exactly two things:
1. Open a new Claude Code session in this folder.
2. Paste everything between the lines below as your first message.

Then watch for ONE thing: the session must show you a **contact sheet or a render you can watch** before it says anything is "done." If it claims success without showing you verified output, stop it — that's the exact failure from last session.

------------------------------------------------------------
First, run `venv/bin/python scripts/preflight_ch1.py`. It must print "FOUNDATION INTACT" with 0 red. If anything is red, fix only that — do NOT rebuild from scratch, the foundation exists.

Then read `research/NEXT_SESSION.md` (the top ▶▶▶ block), `research/edit_decision_rulebook.md`, and memory files `feedback_use_existing_asset_library.md` + `feedback_self_verifying_pipeline.md`.

THE WORKING CH1 ALREADY EXISTS: `output/trex_pilot_ch1_body_540p.mp4`, built by `scripts/build_ch1_composites.py` (it splices the moving composites into the VARIED edit — 34 unique assets, ~59% moving, devices on the stats). WATCH IT FIRST and tell me what's wrong with it specifically, then improve THAT. ⛔ Do NOT use or "fix" `scripts/build_ch1_auto.py` — it's a DEPRECATED dead-end router that draws from 4 cutouts and produces the same creature every frame. The fix is `build_ch1_composites`, not the router.

The goal (already mostly met by build_ch1_composites): CH1 must have ALL THREE at once — (1) VARIETY (use the ~36 existing library assets, NOT a tiny cutout pool), (2) MOTION (creature stills composited so they MOVE, never Ken-Burns-on-a-still), (3) DEVICES (the illustrated stats: tape, gauge, scale, speedometer, reticle — already built in composite_beat). AUGMENT the existing varied library; never regenerate visuals from a small pool (NEVER INVENT PARALLEL SOLUTIONS — that's what broke the router).

THE APPROVED STYLE IS A NUMBER, NOT A VIBE. `research/style_bands.json` (sourced from
`research/viral_recreation_spec.md`) is the owner-approved style as machine-checkable bands.
`scripts/gate_style.py --render <mp4> --paper-edit <json>` measures any render against it
(events/min, max event gap, shot length, static share, music coverage, card holds). A render
is NOT done until BOTH gates are green: `gate_ch1.py` (sync/motion/subject) AND `gate_style.py`
(the approved style). Do NOT write a new gate; do NOT redefine "done" in prose — that drift is
exactly what made every handoff produce something the owner never approved. Known current
fails (measured 2026-06-12): CH1 cards held 3.1–4.6s (band ≤2.2s — cards must become ANIMATED
typewriter flashes or chips riding the shot, never full-frame static PNG holds); the music bed
is the Breaking-Law fallback `track_01_tense_ducked.wav` via ffmpeg_production_render.py's
chapter-map default (owner must pick a creature bed); the blessed hook itself measures
21.6 events/min vs the ≥25 band (its event-layer top-up is still queued).

NON-NEGOTIABLE RULES (the owner was burned repeatedly by these being broken):
- I am NOT your QA. Never tell me something is "done," "fixed," or "QA-clean."
- After you build, run BOTH gates AND make a contact sheet (1 frame / ~5s) and LOOK at it yourself. Only show me a render you have ALREADY watched and confirmed is varied + moving + the visual matches the spoken words.
- Do NOT ask me to validate a spec, config, or plan — I can only judge watchable output.
- Every fix reasoned on paper last session was wrong; the render is the only source of truth. Verify by looking, not by claiming.

Start by running preflight and showing me the result.
------------------------------------------------------------
