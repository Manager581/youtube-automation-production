# NEXT SESSION — Dunkleosteus build (Spinosnack-style)

**Status: research + pipeline DONE and validated. Next job = assemble the full video to spec.**

## Paste this to start the new session
> Read `research/NEXT_SESSION.md` and `research/spinosnack_winning_formula.md`. We've validated the Spinosnack formula and proven every pipeline piece. Now build the full "I Simulated A Dunkleosteus In The Modern Ocean, It Was Brutal" video to the validated spec: generate ~15–20 ChatGPT photoreal creature stills → LTX image-to-video each → assemble to `scripts/dunkleosteus_v2.txt` (voice = `audio/dunkleosteus/narration_v2_clean.wav`) with ~5s cuts, unified teal grade, the ink thumbnail, and the next-creature CTA. Use the direct `.nosync` venv paths.

## What's already done (don't redo)
- **Data analysis** → `research/spinosnack_winning_formula.md` (+ raw `spinosnack_analysis_report.json`). 13 videos, top vs bottom. **Packaging beats execution ~376×.**
- **Validated formula:** original creature (not movie IP) · 2nd-person POV survival-sim · **ink-horror thumbnail + ONE red doom-word** (13/13 predictor — NOT glossy/versus) · brandless stat-stack cold open + POV flip <15s + ≥2 open loops + title-answer withheld · ~195 WPM, 18–26 min · wall-to-wall music · **CTA teases next creature** (series flywheel) · high motion/fast cuts are table stakes, NOT the edge.
- **Photoreal visual pipeline PROVEN:** ChatGPT still → LTX i2v → photoreal motion. Example asset: `footage/dunkleosteus/dunk_i2v_hero.mp4` from `assets/dunkleosteus/chatgpt_dunk_hero_01.png`.
- **Script v2 (on-spec):** `scripts/dunkleosteus_v2.txt`
- **Cloned narration v2 (clean, 157s):** `audio/dunkleosteus/narration_v2_clean.wav` (+ `_manifest.json`)
- **Ink-horror thumbnail v1:** `footage/dunkleosteus/thumbnail_inkhorror_v2.jpg`
- **Environment fixed:** venvs rebuilt + iCloud-excluded. Reliable now.

## The build plan (the actual next work)
1. **Shot list:** ~15–20 hero scenes from the v2 script beats (hatch / cold / first strike / the looming threat / etc.) + the existing storyboard `storyboards/dunkleosteus_storyboard.json`.
2. **Stills:** generate each in **ChatGPT** (photoreal, cinematic, teal deep-ocean, 16:9) via Claude-in-Chrome on chatgpt.com → download → `assets/dunkleosteus/`.
3. **Motion:** LTX i2v each still → `footage/dunkleosteus/` (see command below). Serialize on MPS.
4. **Paper edit:** `scripts/build_dunk_paper_edit.py` (clip mode) against `narration_v2_clean_manifest.json`. Aim ~5s beats (don't over-cut). Boomerang-loop short clips to cover beats (`scripts/exclude...` no — see transcript for the loop step) OR generate ~5s clips.
5. **Render:** `scripts/ffmpeg_production_render.py --paper-edit ... --narration audio/dunkleosteus/narration_v2_clean.wav` → then teal-grade post-pass (params below).
6. **QA:** `scripts/verify_render.py`.
7. **Thumbnail:** refine `thumbnail_inkhorror_v2.jpg` in Photoshop (sharper crosshatch, red eye-glow) — or regenerate over a better ChatGPT head.
8. **CTA:** already in v2 script (tease next creature + community vote).

## CRITICAL conventions / gotchas (or it breaks)
- **Use direct `.nosync` venv paths** (iCloud renames the convenience symlinks):
  - main: `venv.nosync/bin/python`  ·  LTX: `tools/ltx-video/ltx_env.nosync/bin/python`
- **MPS = one torch job at a time.** Run F5-TTS on CPU (`F5_DEVICE=cpu`) so LTX gets MPS. Two MPS jobs deadlock.
- **F5-TTS voice:** short ref `assets/voice/voice_neutral_ref_short.wav`, **single register** (NOT the long story refs `voice_neutral.wav` etc. — they bleed old scripts into the output).
- **LTX i2v command** (from `tools/ltx-video`):
  ```bash
  cd tools/ltx-video && PYTORCH_ENABLE_MPS_FALLBACK=1 ltx_env.nosync/bin/python -u inference.py \
    --prompt "<motion desc>" --conditioning_media_paths <abs/path/still.png> --conditioning_start_frames 0 \
    --height 448 --width 768 --num_frames 97 --frame_rate 24 --seed N \
    --pipeline_config configs/ltxv-2b-minimal.yaml --output_path <abs/out_dir>
  # NOTE: --output_path is a DIRECTORY; the mp4 lands inside as video_output_*.mp4
  ```
- **ChatGPT:** desktop app won't launch; use **chatgpt.com via the Chrome extension** (Claude-in-Chrome). Logged-in Plus account. Download via the share dialog's Download button → lands in ~/Downloads.
- **Teal grade post-pass:**
  ```
  -vf "colorbalance=rs=-0.06:gs=0.04:bs=0.12:rm=-0.04:gm=0.02:bm=0.06:rh=-0.05:bh=0.08,eq=contrast=1.12:saturation=1.08:gamma=0.96,vignette=PI/4.5"
  ```
- Old `output/dunkleosteus_*.mp4` are EARLIER proofs (placeholder/stills/abstract-2B). The new build supersedes them.

## Key files
- Formula: `research/spinosnack_winning_formula.md` · Script: `scripts/dunkleosteus_v2.txt` · Voice: `audio/dunkleosteus/narration_v2_clean.wav`
- Hero still: `assets/dunkleosteus/chatgpt_dunk_hero_01.png` · i2v example: `footage/dunkleosteus/dunk_i2v_hero.mp4` · Thumb: `footage/dunkleosteus/thumbnail_inkhorror_v2.jpg`
- Tools: `scripts/gen_dunk_clips.py` (LTX batch, now uses ltx_env.nosync) · `scripts/build_dunk_paper_edit.py` · `scripts/ffmpeg_production_render.py` · `scripts/verify_render.py`
- Repro: `requirements.txt` + `requirements_ltx_env.txt` (install with `--no-deps`; ltx torch pinned to stable 2.8.0)
- Memory: `memory/project_spinosnack_creature_channel.md`, `project_icloud_venv_eviction.md`, `project_mps_serialize_torch_jobs.md`
