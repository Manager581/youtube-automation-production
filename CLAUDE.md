# YouTube Automation Production — Session Handoff

## Project Overview
Automated YouTube documentary video production pipeline. Takes a topic → researches → writes script → generates voice → sources footage → assembles video. Target style: Fern-like documentaries (true crime, mystery, investigative).

## Branch Structure
- **`claude/youtube-automation-ai-01G5Y4v5o8KvedKntNWBzbn3`** — Main working branch (active VS Code development)
- **`backup/pre-learnbyleo`** — Safe snapshot of all work before playbook integration (pushed to GitHub)
- **`feature/learnbyleo-integration`** — Current feature branch with all playbook + pipeline improvements

## What Was Built (feature/learnbyleo-integration)

### 1. YouTube Strategy Playbook (`playbook/`)
Knowledge base extracted from LearnByLeo (7 videos downloaded to `~/Downloads/LearnByLeo/`). Six JSON modules:
- `ideation.json` — Topic selection, 4-test validation, outlier concept transfer
- `scripting.json` — Green/purple formula, water tank pacing, but/therefore flow
- `titles_thumbnails.json` — 26 clickbait tactics, thumbnail design, title optimization
- `intros.json` — Expectation alignment, pacing-to-genre, exceed expectations
- `editing.json` — 4-pillar editing, 6 attention guides, 5-layer sound design, visual continuity
- `retention_delivery.json` — 3-part litmus test, vocal delivery, communication clarity

Python loader at `playbook/loader.py` — any pipeline module can query it:
```python
from playbook.loader import Playbook
pb = Playbook()
data = pb.for_stage("director")
result = pb.score_checklist("scripting", "script_quality", scores)
```

### 2. Pipeline Integrations
- **`pipeline/director.py`** — Added `_playbook_audit()` post-processing pass. Scores energy variation, SFX coverage, cut frequency, focus continuity, graphics animation, attention guides. Expanded CONTENT_SFX_RULES to be topic-agnostic. Expanded revelation triggers.
- **`pipeline/video_assembler.py`** — Added `_playbook_pre_render_qa()` pre-render quality gate. Fixed SFX file mapping (7 missing files), added `import logging`, added black frame warnings.
- **`pipeline/script_structure_analyzer.py`** — Expanded GREEN_PATTERNS from 18→50+, PURPLE_PATTERNS expanded. Replaced Ollama references with Claude Max. Scores scripts against playbook checklists.

### 3. Upstream Tools
- **`pipeline/topic_scorer.py`** — Scores topic ideas against playbook ideation criteria
- **`pipeline/title_thumbnail_evaluator.py`** — Scores pairs against 26 click tactics
- **`pipeline/script_structure_analyzer.py`** — Green/purple, water tank, but/therefore, energy analysis
- **`pipeline/llm.py`** — LLM abstraction: Claude CLI (Max) → Ollama → heuristic fallback

### 4. Secret Scores Video (In Progress)
- Topic: "The Secret Score That Controls Your Life (It's Not Your Credit Score)"
- Research brief: `research/secret_scores_brief.md`
- Script v2: `scripts/raw_secret_scores_v2.txt` — scores 86/100 on structure analyzer
- Script v3: `scripts/raw_secret_scores_v3.txt` — alternative rewrite, scores 83.8/100
- **Blind review scored v2 at 70/100** — see below for details

## Critical Findings

### Blind Script Review (70/100)
Our pattern detector scored the script 86/100. An independent Claude Opus blind review scored it 70/100. Key issues:
- **Second half strength: 5/10** — shifts from showing to telling after Cigna section
- **CTA integration: 5/10** — "what you can do" feels tacked on, not woven into stories
- **Pacing: 6/10** — one gear (revelation → outrage → statistic → repeat)
- **No character callbacks** — introduces Mary, Derek, Kyle, Carmen but never returns to them
- **No tonal break** — 22 minutes of sustained outrage with no release valve
- **No iconic thesis line** — no single quotable sentence that IS the video
- **Fix:** Need final story (current year), weave CTA into stories, add callbacks, write thesis line

Full blind review saved at: `/tmp/blind_script_eval.txt`

### Pipeline Audit Results

| Module | Status | Issue |
|--------|--------|-------|
| Visual Sourcer | Limited | Only Wikimedia Commons in automated pipeline. Multi-source code exists in `scripts/source_images_free.py` but not wired in |
| SFX Rendering | **FIXED** | Was referencing 7 non-existent files. Fixed to map to actual files on disk |
| Ken Burns/Zoom | **FIXED** | Missing `import logging` crashed parallax fallback. Fixed. |
| Document Display | Limitation | Shows docs as full images with zoom. No readable region cropping. |
| Voice Pacing | Works | Per-chunk speed (neutral/tense/energized). Can't vary within a sentence. |
| Final Assembly | Works | Black frames now warn. FFmpeg concat re-encodes (slow but functional). |
| Image Sourcing | Narrow | Wikimedia only. Need multi-source integration. |
| Video Clips | Works | Pipeline supports real video. Clips must be pre-downloaded. |

### Fair Use Research
Saved at: `.claude/worktrees/admiring-dirac/research-fair-use-practices.md`
Key rules for the pipeline:
- Max 3-5 seconds per source clip (7s hard max)
- NEVER show clip without narration overlay (transformative requirement)
- Mute original audio (Content ID is audio-fingerprint driven)
- Add source attribution in lower-third
- At least 2 transformative layers per clip (zoom/crop + narration + text overlay)
- US Government footage is public domain (NASA, military, CSPAN floor proceedings)
- C-SPAN non-floor coverage requires license
- Content ID claim ≠ strike (claim = shared revenue, strike = video removal)

## Production Status: Secret Scores Video

### Completed ✅
1. **Script v4** — Blind review ~80/100. Enhanced with 59 VOICE, 57 PAUSE, 51 BEAT markers
2. **Storyboard + Director** — `storyboards/secret_scores_directed_v2.json` (full editorial pass)
3. **Voice generation** — Narration rendered at 1.5x speed (`~/Desktop/SecretScores_Media/narration_150x.wav`)
4. **67 video clips** — sourced and downloaded to `footage/fern_clone/secret_scores/clips/`
5. **34 visual assets** — logos, data viz stats, news headlines, person placeholders in `~/Desktop/SecretScores_Media/assets/`
6. **Music** — CC0 crime documentary track from Pixabay (`~/Desktop/SecretScores_Media/sfx/music_real_long.wav`)
7. **FFmpeg assembler iterations** — V3 through V12, all committed. V12 = latest FFmpeg render (14.5 min)
8. **DaVinci Resolve Studio 20.3.2** — Purchased, installed, project set up
9. **News overlay** — ABC News-style breaking news overlay (v5) composited in Fusion over intro
10. **Playbook gap analysis** — 17 gaps documented in `PLAYBOOK_GAPS.md`, partially integrated into `playbook/editing.json` and `playbook/intros.json`
11. **Director validator** — `pipeline/director_validator.py` built

### Current Workflow: DaVinci Resolve (NO MORE FFmpeg assembly)
- All editing now happens in DaVinci Resolve Studio, not FFmpeg
- DaVinci project: "Secret Scores", timeline: "Secret Scores FINAL"
- **V1**: 69 clips (intro_clean.mp4 + 68 segments), ~17 min content
- **V2**: 19 overlays (PNG assets at correct segment positions)
- **V3**: 7 additional overlays (SafeRent logo, LexisNexis logo, Kronos logos, Cigna logo, RealPage stat, Kyle Behm callback)
- **A1**: Premix (old) — DISABLED/MUTED
- **A2**: Narration (narration_150x.wav) — 0 dB
- **A3**: Music (music_real_long.wav) — -14 dB
- **A4**: SFX original (24 hits + risers) — -12 dB
- **A5**: SFX 2 (26 additional: tension, shimmer, impact, rumble, whoosh from director notes) — -15 dB
- **Color grade**: CDL applied to all 69 V1 clips (Fern-style: desaturated 0.65, crushed blacks, cool blue shift)
- **Transitions**: Cross dissolves at 8 chapter boundaries
- News overlay v5 composited via Fusion on intro clip

### DaVinci Control Method
- **Computer-use MCP CANNOT see DaVinci Resolve** (bug: reports "not_installed" despite running)
- Use **DaVinci Python scripting API** for timeline ops: `import DaVinciResolveScript as dvr`
- Use **AppleScript/System Events** for menu clicks, page switching. CRITICAL: check for modal dialogs first (`name of window 1`)
- Use **cliclick** (installed via brew) for mouse clicks. Keyboard shortcuts DON'T work for blade/split (focus issue)
- Use **screencapture -x -D 3** to capture DaVinci's display
- **FCPXML export/import** for batch clip splitting (only reliable way to blade clips programmatically)
- If DaVinci hangs: `killall -9 Resolve` then `open "/Applications/DaVinci Resolve/DaVinci Resolve.app"`
- After restart: close "Create New Project" dialog (Esc) before API calls, then `pm.LoadProject("Secret Scores")`
- DaVinci + Photoshop now on same LG monitor (display 3)

### LearnByLeo Playbook Audit (updated 2026-03-27)
**"Secret Scores FAIR USE" timeline — production-ready:**
1. **✅ Cut frequency / Fair use** — 150 clips, ALL ≤7s (except 19.7s intro). 711s tail REMOVED.
2. **✅ Intro** — news_overlay_v5 compositing as ProRes 4444 (alpha) on V2, 19.7s. BREAKING NEWS + LIVE badge.
3. **✅ Chapter transitions** — 8 chapter cards on V3 (THE TENANTS / THE MACHINE / THE DATA / THE DRIVERS / THE WORKERS / THE PATIENTS / THE FUTURE / THE RECKONING). White serif on black, 2s each.
4. **✅ Overlay animations** — 19 Fusion comps with fade-in/fade-out keyframes on V2 overlays.
5. **✅ Color grade** — Enhanced CDL: crushed blacks (-0.03), high contrast (1.08 power), heavy desat (0.55) on 149 clips.
6. **✅ Sound design** — 50 SFX (24 hits/risers + 26 tension/shimmer), Narration 0dB, Music -12dB, 12dB separation.
7. **⚠️ Remaining (UI-only)** — Fairlight sidechain ducking, ResolveFX film grain, typewriter text effects, attention guides.

### What Still Needs Doing in DaVinci (use "Secret Scores FAIR USE" timeline)
1. ~~DELETE untrimmed tail~~ ✅ Removed via FCPXML rebuild
2. ~~Blade long clips~~ ✅ All clips ≤7s via FCPXML rebuild (150 clips)
3. ~~Fix intro overlay~~ ✅ news_overlay_20s.mov (ProRes 4444 alpha) on V2, 19.7s
4. ~~Animate overlays~~ ✅ 19 Fusion comps with fade keyframes
5. ~~Chapter cards~~ ✅ 8 cards on V3, white serif on black, 2s each
6. **Music ducking** — Fairlight sidechain compressor: duck Music under Narration (UI-only)
7. **Vignette + film grain** — Power Windows vignette + ResolveFX film grain (UI-only)
8. **Typewriter text effects** — Fusion-based text reveals on 12 sync points
9. **Attention guides** — Darken/blur surrounds, color shifts, glow on key moments

### Media Locations
- All media: `~/Desktop/SecretScores_Media/`
- Visual assets: `~/Desktop/SecretScores_Media/assets/` (manifest.json has full inventory)
- SFX: `~/Desktop/SecretScores_Media/sfx/`
- Clips: `footage/fern_clone/secret_scores/clips/`
- Narration: `~/Desktop/SecretScores_Media/narration_150x.wav`
- Editorial clip map: `editorial_clip_map_v2.json` (67 segments with timing)

## Tools & Access
- **Claude Max** subscription (Opus available via `claude` CLI)
- **DaVinci Resolve Studio 20.3.2** — Primary editing tool. External scripting API + AppleScript/cliclick for UI. Computer-use MCP cannot see DaVinci (known bug).
- **Adobe Photoshop 2024** — Graphics creation (news overlays, visual assets). Use computer-use MCP.
- **Chrome MCP** — Full browser control (navigate, click, type, screenshot). Tab group ID may change between sessions. Use `tabs_context_mcp` to get current tabs.
- **Computer-use MCP** — Desktop app control (DaVinci, Photoshop, etc.). Chrome is read-only through this tool; use Chrome MCP instead.
- **yt-dlp** — Updated to 2026.3.17, works with `--cookies-from-browser chrome`
- **FFmpeg** — Available for video processing (but DaVinci is primary now)
- **F5-TTS** — Voice generation with cloning
- **Ollama** — Local LLM (qwen3:4b, qwen2.5vl) for vision tasks

## User Preferences
- Use Claude Max (highest version) as #1 LLM option. Only fall back if tokens run out — then PAUSE and notify.
- Do NOT use Pixabay/Pexels for B-roll (user finds them garbage for documentary style).
- Always commit and push changes to GitHub for version control.
- This feature branch (`feature/learnbyleo-integration`) is separate from the main VS Code work.
- User wants the pipeline to work like a real film production: orchestrator controls the whole flow, director makes editorial decisions, verification at every stage.
- Permissions are configured in `~/.claude/settings.json` — broad Bash/Read/Write/Edit/Chrome/computer-use allowed.

## Key File Locations
- Pipeline modules: `pipeline/`
- Playbook: `playbook/`
- Scripts: `scripts/`
- Research: `research/`
- SFX assets: `assets/sfx/`
- Orchestrator: `run_pipeline.py`
- State file: `.pipeline_run.json`
- Brand config: `brand_configs/fern_clone.json`

### Fixes Applied (session 2026-03-27 afternoon)
1. **Chapter cards REORDERED** — were scrambled (MACHINE at 67s, TENANTS at 670s). Now correct:
   TENANTS@56.7s, MACHINE@138.7s, DATA@259.3s, DRIVERS@341.3s, WORKERS@466.8s, PATIENTS@629.3s, FUTURE@813.5s, RECKONING@895.9s
2. **V3 cleaned** — removed 21 junk/duplicate clips from failed asset placements
3. **Music dropped to -20dB** — was -12dB, narration was getting buried. Now music is background bed only.
4. **Director audit** — mapped all 72 director segments vs timeline. Key finding: V1 clips are YouTube B-roll, NOT the director-specified visuals. Director SHOW descriptions need Wikimedia/custom images (not yet sourced).
5. **SFX count validated** — 50 SFX placed (33 director-specified, 17 extra for coverage)

### Director-Verified Wiring (CORRECTED 2026-03-27 evening)
**Critical fix**: discovered director has `_timeline_start_sec` fields with its OWN timing (0-422s).
Mapped to our timeline via scale factor 2.04x (director 0s → timeline 11.8s, director 422s → timeline 872s).
All elements re-placed at director-correct positions:
- **33/33 SFX** placed at director-correct positions (was 29, now all 33 covered)
- **12/12 text reveals** on V4 as ProRes 4444 alpha MOVs (MARY LOUIS, CARMEN ARROYO, ASK DEREK, KYLE BEHM, AND KYLE, AI, NEW, BUT, JANUARY, PHOENIX, MARY LOUIS callback, BUT KYLE)
- **8 chapter cards** on V3 at director-mapped positions (TENANTS@42.6s, MACHINE@105s, DATA@171s, DRIVERS@212s, WORKERS@315s, PATIENTS@480s, FUTURE@585s, RECKONING@695s)
- **63 zoom targets** applied to V1 clips
- **Music ducking**: single pre-mixed WAV (-8dB intro/outro, -24dB under narration)
- **35 vignette clips** on V5 (Multiply 50%)
- **525 film grain clips** on V6 (Overlay 15%, 2s loops)
- **12 dramatic character cards** on V2 (Mary Louis, Carmen Arroyo, Derek Mobley, Kyle Behm + rejection letter + stats + callbacks)

### Segment Coverage Audit
- V2 overlays: covers key segments (character intros, stats, logos)
- SFX: 33/33 ✅
- Text reveals: 12/12 ✅ (incl seg 16 with text=None skipped)
- Chapter cards: 8/8 ✅
- Zoom: 63/72 ✅

### Final Timeline State ("Secret Scores FAIR USE")
| Track | Contents | Count |
|-------|----------|-------|
| V1 | B-roll clips (all ≤7s, zoomed per director) | 150 |
| V2 | Character cards + stat overlays + rejection letter | 25 |
| V3 | Chapter title cards | 8 |
| V4 | Text reveals (ProRes 4444 alpha) | 12 |
| V5 | Vignette overlay (Multiply 50%) | 35 |
| V6 | Film grain (Overlay 15%, 2s loops) | 525 |
| A1 | Narration (0dB) | 1 |
| A2 | Music (ducked: -8dB intro/outro, -24dB bed) | 1 |
| A3 | SFX primary | ~17 |
| A4 | SFX secondary | ~16 |

### Text Reveals + Music Ducking Complete (session 2026-03-27)
- **12 text reveals on V4** — ProRes 4444 alpha, 3s each, correct chronological order
  MARY LOUIS@61.8s, CARMEN ARROYO@277.5s, ASK DEREK@406.2s, KYLE BEHM@459.6s,
  AND KYLE@512.4s, AI@639.5s, NEW YORK CITY@688.0s, BUT HERE IS WHAT HAPPENED@713.8s,
  JANUARY 2026@715.0s, PHOENIX@716.9s, MARY LOUIS (callback)@793.4s, BUT KYLE@829.4s
- **Music ducking via pre-mixed WAV** — single file with FFmpeg volume automation:
  intro 0-11.8s at -8dB (loud, no VO), narration 11.8-872.3s at -24dB (quiet bed),
  outro 872.3+ at -8dB (loud, no VO)
- **Text styling**: white with shadow, lower-third position, underline on names, 64px names/52px locations/72px dates
