# Next session — Track B: fix the quality blockers the watcher catches

Paste the block below into a fresh session to pick up where we left off.

---

```
Track B for the Breaking Law video pipeline: fix the quality blockers the auto-QA
watcher now catches. Working dir: /Users/jefflawrence/Documents/youtube-automation-production
(branch realpage-standalone). Read CLAUDE.md + MEMORY.md + memory/project_qa_watcher.md
first — they carry full context.

WHAT'S ALREADY DONE (last session, commit 25f6af4, pushed):
scripts/verify_render.py is now the auto-QA "watcher." It catches what I used to
miss by eye. Run it and read the HTML report instead of watching the render:
  venv/bin/python scripts/verify_render.py \
    --render output/breaking_law_v13e_preview.mp4 \
    --paper-edit storyboards/breaking_law_paper_edit_v13e.json \
    --report output/verify_v13e_watcher.json --skip-vision --whisper-model base
It writes verify_v13e_watcher.json + .html (+ _frames/ screenshots). On v13e it
flags 54 critical: 49 black-frame + 5 intro-protocol.

WHAT TO FIX THIS SESSION (root-caused, not yet fixed):
1. RENDERER DROPS BEATS TO BLACK under parallel load. scripts/ffmpeg_production_render.py
   (~lines 389-413) substitutes a `color=c=black` segment when a per-segment encode
   returns nonzero or times out. Segments encode fine in isolation, so it's a
   concurrency/resource issue. Fix = retry the failed segment (serial / software
   libx264) BEFORE falling back to black. This is the #1 blocker — kills 49 beats.
2. LOCKED INTRO NOT INJECTED. The v13e paper edit diverged from the approved
   storyboards/intro_spec_locked.json (wrong clips, the rejected "$5B card" overlay
   is back, Ford Pinto clip-audio dropped). Fix = inject the locked intro at build time.
3. Regenerate VO only if the watcher's vo_* checks flag real problems.

HARD RULES (from MEMORY.md): VERIFY BEFORE CLAIM (a tool call must precede every
state claim — re-check the line numbers above, they may have shifted). PROTOTYPE
BEFORE PLAN (>30min work needs a 10-min real-sample prototype first). Use venv/bin/python.
NEVER invent parallel solutions — grep + read the existing pipeline_v2/ tool first.

START HERE: prototype the renderer retry fix on ONE currently-black segment (pick a
beat_id from the watcher's critical list, e.g. beat_0055), prove a serial/software
retry produces a non-black segment, THEN wire it into the renderer. After each fix,
re-render and re-run the watcher — not_black criticals should fall toward 0 and
intro_seg* should go green. Confirm with me before a full 24-min re-render.
```
