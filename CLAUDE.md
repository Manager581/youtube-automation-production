# YouTube Automation Production — Project Guide

Automated business/tech documentary pipeline (ColdFusion / How Money Works style,
with Johnny Harris–style source-driven moments). Owner's cloned voice via F5-TTS.
**MEMORY.md is the live source of truth** (`memory/MEMORY.md`); this file holds the
durable rules. Prior session logs (incl. the old "Secret Scores" video and the
DaVinci-as-assembler era) are archived at `archive/CLAUDE_archive_2026-06-01.md`.

## ⚠️ Hard rules (anti-hallucination — from MEMORY.md)
1. **VERIFY BEFORE CLAIM** — every statement about project state must be preceded by a
   tool call that produced the fact. Prefix any ungrounded claim with "Speculation:".
2. **PROTOTYPE BEFORE PLAN** — any >30-min change needs a 10-min prototype on one real
   on-disk sample first ("here's the proof it worked on beat_0023", not "I think").
3. **NEVER INVENT PARALLEL SOLUTIONS** — before writing any new script/tool, grep the
   codebase, read the relevant `playbook/*.json`, and read the matching tool in
   `pipeline_v2/` or `scripts/`. If the user says "you're inventing," stop and find it.
4. **SHORT SESSIONS** — past ~2h or 2 major decisions, recommend a fresh session.
5. Use `venv/bin/python` (not system python). Always commit + push when work lands.

## ⚠️ Tool Policy (FFmpeg is the engine — DaVinci is optional)
1. **FFmpeg = the assembly/render engine.** `scripts/ffmpeg_production_render.py` builds
   the finished 1080p MP4 (Ken Burns, overlays, chapter cards, music, SFX, clip audio,
   audio mix). This replaced DaVinci after 15+ failed DaVinci-assembler attempts.
2. **DaVinci = optional manual polish only.** Its API CANNOT position clips at arbitrary
   timecodes (`AppendToTimeline` ignores `recordFrame`), so it is NOT the assembler.
3. **FCPXML** is allowed for timeline assembly via `pipeline_v2/fcpxml_builder_v2.py`
   (the OLD `fcpxml_builder.py` has logic bugs — do not use it). FFmpeg is still primary.
4. DaVinci API gotchas (why we don't rely on it): H.264 kills alpha (use ProRes 4444);
   AddFusionComp/AddTransition/Fairlight automation don't work from scripts; bake fades/
   ducking into files first. computer-use MCP can't see DaVinci — use screencapture/osascript.

## Render + QA workflow (the real pipeline)
Single data path: **`storyboards/breaking_law_paper_edit_v14.json` → FFmpeg renderer → MP4 → watcher.**
```bash
# Render (drop --preview for full 1080p; add it for fast 540p)
venv/bin/python scripts/ffmpeg_production_render.py \
  --paper-edit storyboards/breaking_law_paper_edit_v14.json \
  --narration audio/breaking_law/narration.wav \
  --output output/breaking_law_v14_FINAL.mp4

# Auto-QA "watcher" — read its HTML report instead of watching the 23-min render
venv/bin/python scripts/verify_render.py \
  --render output/breaking_law_v14_FINAL.mp4 \
  --paper-edit storyboards/breaking_law_paper_edit_v14.json \
  --alignment audio/breaking_law/narration_alignment_whisperx.json \
  --report output/verify_v14_final.json --skip-vision --whisper-model base
```
`verify_render.py` checks: `not_black` (blackdetect per beat), `coverage_dropped_beats` +
`coverage_timeline_span` (beats lost off the render end / padded-vs-unpadded mismatch),
`narration` (transcribes the render, number-canonicalized so "five billion"=="5 billion"),
`narration_silenced`, `overlay`, `intro_seg*` vs `intro_spec_locked.json`, `vo_*`. It writes
`<name>.json` + `.html`. There are two orchestrators: `scripts/run_pipeline.py` (the render
pipeline: label-stills → paper-edit → realign → render → verify) and `run_pipeline_v2.py`
(38-stage discovery→FCPXML half; its render stage is manual).

## Audio / narration rules (critical)
- **Use `audio/breaking_law/narration.wav`** (unpadded, ~1404.7s / 23.4 min). NEVER use
  `narration_gapped.wav` (caused persistent timecode drift) or `narration_smoothed.wav`
  (voice-smoother bug left it 79% silent).
- Alignments: `narration_alignment.json` (sentence-level, unpadded), `..._whisperx.json`
  (word-level, unpadded — what `realign_paper_edit.py` consumes). `..._padded.json` is the
  OLD padded (1458.7s) timeline — do not align renders to it.
- **Clip audio**: the renderer MUTES narration during a clip's audio window. With the
  unpadded VO (no pauses) that would cut the narrator mid-sentence, so video `play_then_mute`
  beats are set to `clip_audio:"mute"` (clips show silent; VO stays whole). Re-pad a specific
  beat only if its real soundbite is worth a deliberate VO pause.

## Image / asset sourcing rules
- **NO Pexels or Pixabay for images** (Pixabay music only). Sources: YouTube stills, Google
  Images, Wikimedia/Wikipedia, news sites, archives, Chrome screenshots.
- NO original journalism — all public data, court filings, verified reporting.
- Before any render, materialize iCloud "dataless" assets (`st_blocks==0`): force-read the
  referenced files or `brctl download` them, then confirm none remain dataless.

## Playbook (LearnByLeo is PRIMARY; Fern is reference only)
- `playbook/editing.json` (cuts every 5-7s, energy variation, SFX, attention guides),
  `intros.json` (0-15s micro-window), `scripting.json`, `titles_thumbnails.json` (26 tactics),
  `retention_delivery.json`, `ideation.json`, `sources.json`. Loader: `playbook/loader.py`.
- Pauses BEFORE reveals (anticipation); 3s silence at chapter transitions. Cards hold 2.0s.

## Topic scoring
`pipeline_v2/topic_scorer.py` — 8–9 test framework (fresh_perspective, originality,
best_option, title_thumbnail, blind_spot, timeliness, killer_stat, five_second_title, +
source_availability). GO = 85+ with all ≥65. Quality bars: 95+ script, 85+ topic.
Calibration channels: Johnny Harris, Wendover, ColdFusion, How Money Works, More Perfect Union.

## Channel identity
Business/tech documentary. Public data only (SEC, DOJ, court filings) → no original-journalism
risk, RPM $10-25 (vs $5-10 true crime), frequent uploads (topic→video in days). Reference:
ColdFusion, How Money Works, PolyMatter, The Plain Bagel. **Source credits**: always credit
original reporting (on-screen "First reported by [outlet]" + description link) — ethical, fair-
use armor, and goodwill. **Sponsors**: privacy/data-broker tie-ins (Incogni, DeleteMe, Proton,
NordVPN) mid-roll after the Meta/AI-scraping sections. **Fair use**: ≤7s/clip, ≤30s/source,
mute original audio, narration + zoom/crop + text overlay as transformative layers.

## CURRENT VIDEO: "Why Breaking the Law Is Profitable"
- **Thesis**: the law doesn't prevent corporate crime — it *prices* it. Fines are a line item.
- **Script v45** (95+). 7 chapters: FORMULA → DATA → MACHINES → RENT → RECKONING. Cases:
  Ford Pinto (anchor), Wells Fargo, Purdue, Meta/$5B, GDPR, AI scraping, RealPage ($0).
- **Canonical timeline: `storyboards/breaking_law_paper_edit_v14.json`** (253 beats, 1404.7s).
  v14 realigned v13e from the PADDED timeline to the UNPADDED narration (v13e drift made the
  whole video lead the VO and dropped the finale incl. the thesis card). 8-beat cold open.
- **Status (2026-06-01)**: v14 validated on the 540p preview — drift gone (narration 242/11
  vs FINAL's 216 fail), `not_black` 0, coverage checks pass, finale present. Clip-audio muted
  on 15 beats. Full 1080p render + watcher = the last step before upload.
- See `memory/project_qa_watcher.md` for the full v13e→v14 history and open notes.

## Key file locations
- Renderer: `scripts/ffmpeg_production_render.py` · Watcher: `scripts/verify_render.py`
- Realign: `scripts/realign_paper_edit.py` · FCPXML: `pipeline_v2/fcpxml_builder_v2.py`
- Paper edit: `storyboards/breaking_law_paper_edit_v14.json` · Intro: `storyboards/intro_spec_locked.json`
- Narration + alignments: `audio/breaking_law/` · Assets: `footage/breaking_law/`, `assets/breaking_law/`
- Playbook: `playbook/` · Research: `research/` · Pipeline tools: `pipeline_v2/` (v1: `pipeline/`)
