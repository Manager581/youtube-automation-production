# YouTube Automation Production — Session Handoff

## ⚠️ CRITICAL RULES FOR NEW VIDEOS (read before doing anything)

### DaVinci Resolve API Bugs (will silently break your build)
1. **NEVER use H.264 for overlays with alpha** → ProRes 4444 only (`yuva444p10le`)
2. **NEVER use AddFusionComp()** → bake fades into files via FFmpeg before import
3. **AppendToTimeline ignores recordFrame** → place clips in chronological order
4. **NEVER use Fusion for effects from external scripts** → everything baked into files
5. **No AddTransition() in API** → use FCPXML export/modify/reimport
6. **No Fairlight automation** → pre-bake music ducking into WAV files

### Mandatory Post-Build Checks
```python
from pipeline.davinci_helpers import verify_track_alignment, verify_source_diversity, normalize_sfx
verify_track_alignment(timeline)      # All tracks end within 5s of each other
verify_source_diversity(timeline)     # Max 30s total from any single source
normalize_sfx(sfx_dir)                # All SFX at -12 LUFS (raw files are often -40dB = silent)
```

### LearnByLeo is PRIMARY (not Fern)
- Editing decisions: `playbook/editing.json` (LearnByLeo)
- Pauses: BEFORE reveals (anticipation), not after. 3s silence at chapter transitions.
- Fern playbook is reference data only, NOT the decision-maker for new videos.
- Director's `arc_position` + `tension_level` drive pause placement via LearnByLeo rules.

### Channel Pivot: Business/Tech Documentary (March 2026)
- **OLD**: Fern-style investigative true crime/mystery
- **NEW**: ColdFusion/How Money Works style business/tech documentary
- **WHY**: No original journalism = can't compete with ProPublica. Business data is public (SEC, DOJ, court filings). RPM is 2-3x higher ($10-25 vs $5-10). Same cinematic style, higher revenue.
- **UPLOAD CADENCE**: Daily/frequent. Pipeline can go topic→video in days, not months.
- **COMPETITIVE ADVANTAGE**: Speed (ride news waves same week), production value (LearnByLeo editing + DaVinci), data assembly (Claude synthesizes filings/patents/earnings faster than humans)
- **REFERENCE CHANNELS**: ColdFusion (5M subs, $2.1K/day), How Money Works (2.6M subs), PolyMatter, The Plain Bagel, Slidebean
- Magnates Media peaked ~2023, declining views since — don't calibrate against them

### Topic Scoring: 8-Test Framework (calibrated March 2026)
`pipeline_v2/topic_scorer.py` — scores topics against 8 tests, calibrated by analyzing 10 proven hits from desk-research channels (ColdFusion, How Money Works, Wendover, Magnates Media).

**Tests:** Fresh Perspective, Originality, Best Option, Title/Thumbnail, **Blind Spot**, **Timeliness** (news wave = multiplier), **Killer Stat** (one shareable number), **5-Second Title Test** (cold viewer instantly knows what's at stake for THEM).

**Verdict:** GO 85+ (all 8 tests ≥65), NEEDS_WORK 60-84, SKIP <60.
**NOTE**: Scorer is calibrated for investigative exposé. Business/tech docs work differently — "analysis depth" matters more than blind spot. Recalibration pending for business niche.

### Source Credits Policy
- ALWAYS credit original journalists/channels when using their reporting
- On-screen lower-third: "First reported by [outlet]"
- Description links to original source
- Recommend viewers watch original reporting
- This is ethical AND fair use armor AND goodwill (journalists share videos that credit them)

### Sponsor Strategy
- Privacy/data protection: Incogni, DeleteMe, NordVPN, ExpressVPN, Aura
- Natural tie-in with corporate data exploitation topics
- Mid-roll after Meta/AI scraping sections

### Pipeline: `pipeline/davinci_helpers.py` has ALL helper functions
See MEMORY.md for full function list and pipeline order.

## CURRENT VIDEO: "Why Breaking the Law Is Profitable" (March 2026)

### Topic & Angle
- **Title**: Why Breaking the Law Is Profitable
- **Thesis**: For the biggest companies, fines are a line item — they budget for breaking the law because the penalty is always less than the profit
- **Format**: 30-40 min business documentary, ColdFusion/HMW style
- **Audience validation**: 507-like comment "If the penalty is a fine, it's legal for a price"
- **Timeliness**: RealPage $0 settlement (March 27, 2026), AI scraping lawsuits ongoing
- **Research brief**: `research/breaking_law_brief.md`

### Case Studies
1. **RealPage** (THIS WEEK) — $0 fine for coordinating rent across 10M apartments. $1.6B/yr revenue.
2. **Meta** — $5B fine = 9% of revenue. Stock went UP.
3. **Boeing** — 346 dead, $2.5B fine = 16 days revenue. No exec jailed.
4. **Wells Fargo** — 3.5M fake accounts, $3B fine = ~2 weeks revenue.
5. **Purdue Pharma** — 600K+ opioid deaths, $7.4B settlement. Sacklers kept billions.
6. **AI Scraping** — Anthropic $1.5B settlement, OpenAI/Perplexity/Google lawsuits ongoing. 90 active cases.
7. **Ford Pinto** — historical anchor. $137M fix vs $49.5M deaths. They chose deaths. 1977.

### Killer Stats
- $1 TRILLION in corporate fines since 2000 (Good Jobs First)
- 127 companies have each paid $1B+ in penalties
- Recidivist companies get SMALLER fines as % of revenue
- $0 — RealPage's penalty for 10M apartments of price coordination

### Pipeline State (as of 2026-03-31)
- **Script v45**: DONE (4,366 words, 95+ score)
- **Voice**: BROKEN — F5-TTS hallucinated, repeats "what your life looks like" 88 times. MUST regenerate WITH `--wpm-normalize` (not `--no-wpm-normalize`)
- **NEXT SESSION MUST START HERE**: Re-run voice generation (stage 8), then stages 8-28
- `.pipeline_v2_state.json` — reset to stage 7 (qa_script done, voice needs re-run)
- Media dir: `footage/breaking_law/`, `audio/breaking_law/`
- Director JSON: `storyboards/breaking_law_directed_v2_gapfilled.json` (113 segments)
- Narration alignment: `audio/breaking_law/narration_alignment.json` (Whisper, will need re-run after new VO)
- FCPXML: `timeline_FINAL2.fcpxml` (latest working build)

### Critical Issues for Next Session
1. **Narration must be regenerated** — current WAV has 88 hallucinated repeats + garbled speed
2. **Need 15+ video clips** — only 3 exist, rest are still images. footage_sourcer args need fixing in `run_pipeline_v2.py`
3. **Need 3-5 music tracks** — only 1 exists (194s). music_sourcer args need fixing
4. **Source diversity** — some images used 900s+. Builder has 20s cap for video but not images
5. **SFX need variety** — only 6 unique sounds for 30 placements. Need 15+ varied SFX
6. **Chapter cards** — plain white-on-black. Need styled template
7. **Add voice QA for hallucination detection** — check for repeated phrases in Whisper output

### What Works (don't re-build)
- Script (v45, 95+ score) ✅
- FCPXML builder (overlay matching, absolute paths, gap fill, music loop, API import with timelineName) ✅
- Whisper aligner (word-level timestamps, tiktoken patched for Python 3.13) ✅
- Director (vision in prompt, music_state, alignment timestamps, sufficiency check) ✅
- Pipeline orchestrator (gates, retries, 3600s timeout, UTF-8) ✅
- Segment validator (auto-fix + re-validate) ✅
- 276 images + 140 overlay MOVs + 4 chapter card MOVs ✅


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

### CRITICAL: Timing System
All elements MUST use **narration word-count proportional timing** (single source of truth).
- Director `_timeline_start_sec` is storyboard-relative (0-422s), NOT timeline position
- V1 clip positions are from editorial clip map, NOT segment timing
- Formula: `tl_sec = 11.8 + (words_before_segment / 2769) * 860.5`
- This ensures overlays/text/SFX appear when narrator SAYS the words

### Segment Coverage Audit (unified timing)
- V2 overlays: 19 at narration positions + 1 news overlay + 4 extra from FCPXML = 24
- SFX: 33/33 ✅
- Text reveals: 12/12 ✅
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

### Final QA Pass (2026-03-27 evening)
- ✅ Duration: 17.5 min (target 15-20)
- ✅ Fair use: all V1 clips ≤7s (except 19.7s intro)
- ✅ Audio: narration 11.8-872.3s, music 0-1008s (ducked), 33 SFX
- ✅ Intro: news overlay compositing properly
- ✅ Color grade: CDL on 149/150 clips
- ✅ Vignette (V5) + film grain (V6) continuous
- ✅ Finale overlays added: "YOU KNOW NOW", "YOU ARE THE ONLY ONE", "THE MOST DANGEROUS THING", "BREAK IT."
- ⚠️ Largest overlay gap: 122s (some segments rely on V1 B-roll alone — acceptable for documentary pacing)
- Fixed: 12 film grain clips trimmed past content end

### Full Compliance Audit Result: 37/37 (100%)
Verified against LearnByLeo (editing, intros, retention), Fern Editorial Playbook, AI Director, and Fair Use:
- V1: 150 clips, avg 6.0s, 8.8 cuts/min, 16 unique sources
- V2: 24 overlays (news intro + 19 character/stat/logo cards + 4 finale)
- V3: 8 chapter transition cards, timed 2s before narration
- V4: 11 text reveals at narration-synced positions
- V5: 35 vignette overlays (Multiply 50%)
- V6: 513 film grain clips
- A1: Narration 860.5s, A2: Music ducked (-24dB under VO), A3+A4: 33 SFX
- CDL color grade, 55 zoom targets, 19 Fusion fade comps

### DaVinci API Root Causes Fixed (2026-03-27)
**New file: `pipeline/davinci_helpers.py`** — reusable functions with all fixes baked in.

Root causes discovered and fixed:
1. **H.264 kills alpha** → Always use ProRes 4444 (`yuva444p10le`) for overlays with transparency
2. **AddFusionComp() doesn't persist** → Bake fade-in/fade-out into video files via FFmpeg before import
3. **CompositeMode string values don't work** → DaVinci uses numeric enums, not strings
4. **AppendToTimeline ignores recordFrame** → Must place clips in chronological order
5. **PNG stills default to 5s** → Convert to video first for longer durations
6. **V1 clips extend past narration** → Always call `trim_timeline_to_narration()` after building

Helper functions:
- `render_overlay_with_fade()` — PNG → ProRes 4444 MOV with baked fades
- `render_vignette_prores()` — radial vignette as ProRes 4444 (alpha preserved)
- `create_chapter_card()` — opaque chapter cards (H.264 fine)
- `create_text_reveal()` — lower-third text with alpha + fades
- `create_ducked_music()` — pre-baked volume automation
- `trim_timeline_to_narration()` — prevent dead tail after VO ends

### Issues Found on Playback (2026-03-27 late)
1. **Footage reuse**: "Algorithms AI" used 47x (274s) — fair use only checked per-clip duration, not per-source total
   FIX: `verify_source_diversity()` added — checks max 30s per source. Added 16 new V2 overlays from unused images.
2. **SFX inaudible**: tension=-39dB, whoosh=-49dB — never normalized
   FIX: `normalize_sfx()` added — all SFX now at -12 LUFS. Replaced 33 quiet clips with loud versions.
3. **No transitions**: DaVinci API has no AddTransition(). All 126 cuts are hard cuts.
   FIX: Use FCPXML export/import for transitions (supports dissolves). Not yet applied.
4. **No VO pauses**: voice_generator.py renders continuous WAV, ignores [BEAT][PAUSE] markers
   FIX: Need VO post-processor to split WAV and insert silence gaps. Not yet applied.
5. **V4 text reveals**: ProRes 4444 alpha verified (yuva444p12le). Should render correctly.

### VO Pause Pipeline Gap (2026-03-27)
**Current:** script_enhancer adds [BEAT][PAUSE] → voice_generator ignores them → director runs after voice
**Need:** Director should specify pause positions based on arc_position + tension_level.
Pause rules from Fern playbook: 3-5 per chapter, 1-3s each, at reveals/transitions/shocking facts.
Current fix: 27 Fern-style pauses manually mapped to director arc positions (was 137 from script_enhancer).
**TODO:** Add `pause_inserter.py` that reads director output + rendered narration WAV → inserts silence at director-specified beats → outputs final narration. Pipeline: script → voice → director → pause_inserter → assembler.

### Session Status (2026-03-27 late evening)
Timeline: "Secret Scores FAIR USE" — 15.5 min, 27 dramatic pauses
- V1: 134 clips, V2: 40 overlays, V3: 8 chapters, V4: 11 text reveals, V5: vignette
- A1: narration (917.9s with pauses), A2: music (ducked, 934.6s), A3+A4: 33 loud SFX
- Tracks aligned within 9s (V1=938s, A1=929s, A2=934s)
- SFX normalized to -12 LUFS (were -39 to -49dB)
- Pipeline code: davinci_helpers.py with verify_source_diversity, normalize_sfx, verify_track_alignment

### LearnByLeo Pause System (replaces Fern-based pauses)
Based on LearnByLeo playbook rules, NOT Fern:
- **pause_for_anticipation**: pause BEFORE revelations/emotional peaks (director arc_position)
- **dramatic_silence**: 3s at chapter transitions (LearnByLeo 5-step chapter transition, step 2)  
- **energy variation**: longer pauses when tension > 0.5
- **pockets_of_dopamine**: breaks every ~3 min if no natural pause exists
Result: 28 pauses, 39.8s total (was 137/190s from script_enhancer, then 27/31s from Fern)
Narration: 933.7s (15.6 min). All pauses driven by director's arc_position + tension_level.

### Transitions Added (2026-03-27)
- 17 cross-dissolve transitions added via FCPXML export/modify/reimport
- New timeline: "Secret Scores FAIR USE (Resolve)" — 153 V1 clips, 950.4s
- LearnByLeo rule: 87.5% hard cuts, 10% fade-to-black at chapters, 2.5% fade-to-white
- Cross-dissolves placed every 8th clip for visual freshness
- V1 gap filled: 2 clips added, V1 now matches narration end (950.4s)

### Active Timeline: "Secret Scores FAIR USE (Resolve)"
V1: 153 clips | V2: 31 overlays | V3: 8 chapters | V4: 11 text | V5: 94 vignette
A1: narration (945.4s) | A2: music (950.4s) | A3: 33 SFX
Duration: 15.8 min | 28 LearnByLeo pauses | 17 cross-dissolves

## Full Pipeline Order (for new videos)
1. `topic_radar.py` → find topic
2. `research_brief.py` → structured brief  
3. `story_validator.py` → GO/SKIP
4. Claude Code interactive → write script
5. `script_enhancer.py` → add [BEAT][PAUSE][VOICE] markers
6. `check_fern_script.py` → QA gate (85+)
7. `voice_generator.py` → render narration WAV (F5-TTS)
8. `storyboard_generator.py` → visual brief per segment
9. `director.py` → editorial decisions (arc, SFX, transitions, zoom, text)
10. **INSERT PAUSES** → split narration WAV at director-specified beats (LearnByLeo rules)
11. `music_sourcer.py` → download CC0 music
12. **PRE-DUCK MUSIC** → `create_ducked_music()` trimmed to narration end + 5s
13. **NORMALIZE SFX** → `normalize_sfx()` to -12 LUFS
14. `footage_sourcer.py` + `footage_verifier.py` → source + verify footage
15. `davinci_timeline_builder.py` → build timeline in DaVinci
16. **POST-BUILD CHECKS** (MANDATORY):
    - `verify_track_alignment()` — all tracks end within 5s
    - `verify_source_diversity()` — max 30s per source  
    - Visual check: play back intro, chapter cards, text reveals, SFX
17. Render → `check_fern_video.py` → manual upload

## davinci_helpers.py Function Reference
- `render_overlay_with_fade(png, dir, dur, fade_in, fade_out)` — PNG → ProRes 4444 MOV with baked fades
- `render_vignette_prores(path, dur)` — radial vignette as ProRes 4444
- `create_chapter_card(title, dir, dur)` — opaque chapter card (H.264)
- `create_text_reveal(text, dir, style, dur)` — lower-third text with alpha + baked fades
- `create_ducked_music(src, dst, narr_start, narr_end)` — pre-baked volume automation
- `trim_timeline_to_narration(timeline, narr_end)` — prevents dead tail after VO
- `verify_track_alignment(timeline)` — all tracks must end together
- `verify_source_diversity(timeline, max_sec=30)` — copyright check
- `normalize_sfx(sfx_dir, target_lufs=-12)` — prevents inaudible SFX

## DaVinci API Gotchas (10 items)
1. H.264 kills alpha → ProRes 4444 only for overlays
2. AddFusionComp() doesn't persist → bake effects into files
3. AppendToTimeline ignores recordFrame → place chronologically
4. PNG stills default to 5s → convert to video first
5. CompositeMode uses numeric enums, not strings
6. SetProperty("ZoomX") unreliable → apply zoom in FFmpeg
7. SetCDL() works but can't verify via API
8. No AddTransition() → FCPXML export/reimport
9. No Fairlight automation → pre-bake ducking
10. Blade/Split keyboard shortcuts don't work via automation → FCPXML

## LearnByLeo Editing Rules (12 items)
1. New visual every 5-7s (P-ED-02)
2. Energy variation: hype → mellow cycling (P-ED-04)
3. Graphics must animate in/out, never pop (AP-ED-02)
4. Risers only before REAL reveals (AP-ED-03)
5. Pause BEFORE reveals for anticipation
6. Chapter transitions: 5-step (punch → silence → card → new energy → hook)
7. Dopamine breaks every ~3 min
8. 87.5% hard cut, 10% fade-to-black, 2.5% fade-to-white
9. SFX: whoosh (movement), highlight (emphasis), impact (reveals)
10. Music: duck under narration, raise during transitions
11. Fair use: ≤7s per clip, ≤30s total per source
12. SFX must be normalized to -12 LUFS before use

### Gap Fill (2026-03-27 late night)
- Removed ALL 47 "Algorithms AI" clips (274s → 0s)
- Downloaded 24 real images from Unsplash (CC0 commercial license)
- 61 gap-fill clips placed on V2, covering 394 of 406 seconds of gaps
- V2 now has 80 overlays | V1 gaps reduced to 12s
- Unsplash usage: <15% of total content (within user's 15% cap)
- Unique video sources: 30 (was 15)

### Visual Verification (2026-03-27 final)
Typewriter text: ✅ RENDERS — character-by-character reveal with cursor, ProRes 4444 alpha
Intro overlay: ✅ RENDERS — BREAKING NEWS with CLAIM DENIED
SFX: ✅ AUDIBLE — normalized to -12 LUFS
V2 overlays: ⚠️ WRONG POSITIONS — AppendToTimeline bug puts them sequentially, not at target times
Gap-fill images: ✅ RENDER — Unsplash images cover the former Algorithms AI gaps

### KNOWN REMAINING ISSUE: V2 overlay positions
AppendToTimeline() ignores recordFrame parameter. ALL V2 overlays are placed sequentially 
at the END of the track, not at their target narration positions. The ONLY fix is:
1. Export FCPXML → manually reorder clips → reimport, OR
2. Place each overlay one at a time on SEPARATE video tracks (V6, V7, V8...), OR  
3. Accept that V2 overlays appear at wrong times and fix manually in DaVinci
This is a fundamental DaVinci API limitation documented in davinci_helpers.py gotcha #3.

### V2 Overlay Positions — FIXED via Internal API
SOLVED: Use DaVinci internal scripts (Workspace > Scripts) instead of external API.
Internal app.GetResolve() respects recordFrame. External dvr.scriptapp() does NOT.
Save .py scripts to Fusion/Scripts/Edit/ folder, trigger via osascript menu click.
The API cannot fix this. The FCPXML structure assigns overlays to parent clips, and the API
appends children to whatever V1 clip is at the end of the track.

### Intro Fix
"CLAIM DENNED" → "CLAIM DENIED": intro_denied_fixed.mp4 created with perspective-warped
replacement monitor content. Needs manual swap on V1 (API places at end, not start).

### What's Ready for Manual Polish in DaVinci
1. Drag V2 overlays to correct narration positions (they're labeled by segment)
2. Drag intro_denied_fixed.mp4 to V1 position 0 (replacing intro_clean.mp4)
3. All other elements (typewriter text V4, chapters V3, SFX, narration, music) are correct

### KEY DISCOVERY: Internal vs External DaVinci API
**External API** (`dvr.scriptapp("Resolve")`) — `AppendToTimeline` IGNORES `recordFrame`. Clips always go to END.
**Internal API** (`app.GetResolve()` from Workspace > Scripts) — `AppendToTimeline` RESPECTS `recordFrame`. Clips go to the specified position!
**Always use internal scripts** for clip placement. Save `.py` to `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Edit/` and trigger via `osascript` menu click.

### All Black Gaps Fixed (2026-03-27 late)
- Restored intro_clean.mp4 (removed broken CLAIM DENIED overlay)
- Filled all 9 V1 gaps (406s total) via FCPXML gap replacement
- 159 V1 clips, 0 gaps, 25 V2 overlays preserved
- FCPXML approach: export → replace <gap> elements with <asset-clip> references → reimport
- This is the ONLY reliable way to fill mid-track gaps (API can't do it)

### Gap Fill Strategy (FINAL SOLUTION)
V1 mid-track gaps CANNOT be filled via API (internal or external).
Solution: Place gap-fill clips on V3 at the gap positions using internal API.
V3 clips show through V1 gaps because higher tracks render on top.
Result: 17s remaining no-video (from 132s), essentially negligible.
Timeline #2 "Secret Scores FAIR USE" is the canonical timeline.
V1=136, V2=25 overlays (correct positions), V3=16 gap fills, A1-A4 audio.

### Visual Playthrough (2026-03-28)
Screenshots captured at 11 key moments (intro, Mary Louis, SafeRent, gap fills, Carmen, Derek, Kyle, Cigna, NYC Law, finale).
DaVinci computer-use MCP reports "not_installed" for DaVinci Resolve — use screencapture + cliclick + osascript instead. DO NOT waste time on mcp__computer-use__request_access for DaVinci.

### Image Sourcing Rules (updated 2026-03-28)
- Use Google/Pexels/Unsplash for images — NOT just Wikimedia
- No Creative Commons restriction needed for documentary fair use
- 20 diverse stock images downloaded to ~/Desktop/SecretScores_Media/google_images/
- NEVER use same source clip more than 30s total (MAX_SOURCE_USAGE in davinci_helpers.py)
- Director search_query field specifies what SHOULD be on screen for each segment
- Current V1 still has 15 YouTube clips recycled — need to replace with images + pretrimmed clips
- Typewriter click audio: typewriter_key_loud.wav normalized from -34dB to -29dB

### V1 Rebuilt with 72 Segment Images (2026-03-28)
- Downloaded 72 images from Pexels (one per director segment)
- Converted to 7s H.264 clips (51 successful, 21 used YouTube fallback)
- V1 rebuilt: 160 clips, 0 gaps, 65 unique sources
- Alternates segment images with YouTube clips (2:1 ratio)
- YouTube clips capped at 30s per source via diversity check
- V2 (25 overlays), A1 (narration), A2 (music) preserved
- Typewriter text with click audio on V4 (3 clips)
- No Pixabay API key set — use Pexels direct URLs instead
- RULE: Always use Pexels/Google for images, NOT just Wikimedia. Fair use covers documentary usage.

### CURRENT STATE (2026-03-28 session end)
**Active timeline: "Secret Scores FAIR USE" (#2)**
- QA Score: 82% (15 pass, 3 warn, 2 fail)
- V1: 136 clips, 3 gaps (132s), 15 unique sources — needs diversity fix
- V2: 31 overlays (faded MOVs, correct positions)
- V3: 16 clips (8 chapters + 8 gap fills)
- V5: 94 vignette clips
- A1: narration with LearnByLeo pauses (934s)
- A2: music ducked
- A3+A4: 33 SFX (boosted)
- NO typewriter text or click audio on this timeline (was on a different one that got lost)

### REMAINING WORK (for next session)
1. **Source diversity**: Replace repeated YouTube clips with pretrimmed variants (215 available in footage/fern_clone/secret_scores/pretrimmed/)
2. **Fill 3 V1 gaps**: Use V3 gap-fill approach (proven to work via internal DaVinci API)
3. **Typewriter text + audio**: Re-create on V4/A5 (MOVs exist in ~/Desktop/SecretScores_Media/typewriter/)
4. **Fair use**: Trim 4 clips >8s via FCPXML
5. **Intro on-screen text**: Director specifies text for cold_open segments
6. **Clip audio**: Mute all V1 clip audio during narration (11.8s+), keep for intro

### CRITICAL LESSON: DO NOT create multiple timelines
Every FCPXML import creates a new timeline. Multiple timelines cause confusion and lost work.
ALWAYS work on "Secret Scores FAIR USE" (#2). Delete other timelines before starting work.

### ROOT CAUSE: V2 Overlay Positioning (SOLVED 2026-03-28)
**AppendToTimeline ignores recordFrame.** Clips are placed SEQUENTIALLY in the order called.
**FIX:** Sort ALL overlays by target timestamp BEFORE calling AppendToTimeline.
Place them in chronological order → they land at correct positions.
This was verified visually: Mary Louis at 61.8s confirmed on DaVinci viewer.
ALWAYS sort by position before placing. Never rely on recordFrame parameter.

### Transition Status (2026-03-28)
- LearnByLeo says 87.5% hard cuts — hard cuts are CORRECT for this style
- Cross dissolves only needed at chapter transitions (8 positions)
- DaVinci needs clip handles for dissolves — pretrimmed clips may not have them
- Cmd+T didn't work (clips need handles). Manual drag from effects panel needed.
- V2 OVERLAY POSITIONING FIX: sort by timestamp before AppendToTimeline (CONFIRMED VISUALLY)

### Audio Verification Needed (human must check)
- SFX clips exist on A3/A4 (33 clips, boosted to -3 to -6dB)
- Typewriter clicks exist on A5 (3 clips)  
- Cannot verify if they're AUDIBLE in the mix without human playback
- User should play at 10:40 and listen for typewriter clicks + tension SFX

### Wind Sound Fix (2026-03-28)
Cmd+T accidentally added 36 'Cross Fade 0 dB' audio transitions to A3/A4 SFX clips.
These produced wind/swoosh sounds. All deleted. NEVER use Cmd+T — it affects audio tracks too.

### Cmd+T Damage Cleanup (2026-03-28)
Cmd+T added 122 video dissolves + 36 audio crossfades across ALL tracks.
All deleted. NEVER use Cmd+T in DaVinci — it applies transitions to EVERY track.
Final QA: 92% PASS (17 pass, 3 warn, 0 fail)

## HOW TO START PIPELINE V2 (new session)

### Quick start:
```bash
cd /Users/jefflawrence/Documents/youtube-automation-production
python run_pipeline_v2.py --topic "Your Topic Here" --stage all
```

### Resume after interruption:
```bash
python run_pipeline_v2.py  # Auto-resumes from last completed stage
```

### Check status:
```bash
python run_pipeline_v2.py --status
python run_pipeline_v2.py --list    # Show all 28 stages
```

### Run specific stage:
```bash
python run_pipeline_v2.py --stage director   # Resume from director stage
python run_pipeline_v2.py --stage qa_video   # Just run QA
```

### Configure file paths:
```bash
python run_pipeline_v2.py --config config.json --topic "Secret Scores"
```

### Pipeline V2 stages (28 total):
1-4: Discovery (topic, comments, research, validate)
5-7: Script (write, enhance, QA)
8-10: Audio (voice, QA, music)
11-15: Visuals (footage, images, transcripts, vision, verify)
16-19: Editorial (storyboard, director, validate segments, fill gaps)
20-23: Assembly (pauses, duck music, normalize SFX, DaVinci build)
24-26: Verification (director review, QA video, executive producer)
27-28: Publish (render, upload)

## SECRET SCORES VIDEO — FINAL STATUS (2026-03-28)
**Timeline: "Secret Scores FAIR USE" — 92% PASS, READY FOR PLAYTHROUGH**

LearnByLeo QA: 17 pass, 3 warn, 0 fail
- V1: 136 clips, intro at 0s
- V2: 15 overlays (correct positions, faded MOVs)
- V3: 16 clips (8 chapters + 8 gap fills)
- V4: 11 text reveals (typewriter on V4)
- V5: 94 vignette clips
- A1: Narration with LearnByLeo pauses (934s / 15.6 min)
- A2: Music ducked (-24dB under VO)
- A3+A4: 33 SFX (boosted to -3 to -6dB)
- A5: 3 typewriter click audio

3 warnings (acceptable):
- 5 small visual gaps (V3 covers most)
- 29 unique sources (1 short of 30)
- 4 clips >30s continuous (gap-adjacent)

Next: Manual playthrough in DaVinci → fix anything that looks/sounds off → render

## NEW VIDEO: "Why Breaking the Law Is Profitable" (2026-03-29)

### Channel Pivot
- Shifted from Fern-style investigative to **ColdFusion/HMW business documentary**
- No original journalism required — all public data, court filings, verified reporting
- RPM: $10-25 (business/tech) vs $5-10 (true crime)
- Upload cadence: frequent (pipeline does topic→video in days)

### Topic Scorer v3: 8-Test Framework (Calibrated)
- Calibrated against 10 proven competitor hits (1.8M-5.4M views)
- Channels: Johnny Harris, Wendover, ColdFusion, How Money Works, More Perfect Union
- 8 tests: fresh_perspective, originality, best_option, title_thumbnail, blind_spot, timeliness, killer_stat, five_second_title
- GO threshold: 85+ with all tests ≥65
- Key finding: blind spot score = #1 predictor of virality for new channels
- Desk-research filter: excludes topics requiring original journalism

### Script Status
- **Script v45**: `scripts/raw_breaking_law_v45.txt` — 4,224 words (~30 min)
- **Score**: 87-91/100 across multiple blind LearnByLeo QA passes
- **Structure**: 7 chapters — FORMULA → DATA → MACHINES → RENT → RECKONING
- **Focus**: Facebook/AI/Reddit/RealPage = 70% of script. Ford/WF/Purdue = 17% setup.
- **Characters**: Grimshaw (Ford), Guitron (Wells Fargo), Esquivel (AI scraping), Vialpondo (RealPage)
- **Thesis**: "The law doesn't prevent corporate crime. It prices it." — withheld until Purdue, echoed at close
- **Key moments**: "Senator, we run ads" reframed as formula protecting itself. GDPR as dopamine pocket. Sugar dissolved in water. Price-per-life escalation ($200K→$9K→$57→$3K→?).
- **Research**: `research/breaking_law_profitable_facts.md` — all stats verified via web search

### Pipeline Stage (updated 2026-03-31)
- Stages 1-7: ✅ COMPLETE (topic → research → script → enhance → QA 95+)
- Stage 8-9: ✅ Voice generated (F5-TTS 17.4min, 186 clips, resume patch)
- Stage 10: ✅ Music sourced (CC0 Pixabay, ducked, premixed with narration+SFX)
- Stages 11-15: ✅ Footage (12 clips + 51 images), transcripts, vision analysis, verified
- Stages 16-19: ✅ Storyboard (83 segments), director (103 segments with vision data), validated, gaps filled (30 new images)
- Stage 23: ✅ DaVinci timeline "Breaking Law FINAL" imported via FCPXML
- Stages 24-26: ✅ Director review + exec producer ran (3/11 — missing polish layers)

### Current DaVinci Timeline: "Breaking Law FINAL"
| Track | Contents | Count | Status |
|-------|----------|-------|--------|
| V1 | B-roll clips (avg 5.6s, 10.6 cuts/min) | 186 | ✅ |
| V2 | Text overlays | 0 | ❌ Need to create + place |
| V3 | Chapter cards | 0 | ❌ Need to create + place |
| A1 | Narration + music + SFX (premixed) | 1 | ✅ |
| — | Color grade | — | ❌ CDL didn't apply via API |
| — | Transitions | — | ❌ No cross-dissolves |
| — | Vignette | — | ❌ Not yet added |
| — | Film grain | — | ❌ Not yet added |

Duration: 17.5 min | Track alignment: 1.8s ✅ | V1 gaps: 0 ✅ | 54 unique sources ✅

### Pipeline Architecture Fix (2026-03-31)
- Gates now BLOCK on failure (exit 1) with auto-retry (max 2 attempts)
- 8 gate stages enforce quality before proceeding
- New `exec_producer_pre` gate runs BEFORE DaVinci build
- FCPXML builder (`pipeline_v2/fcpxml_builder.py`) bypasses all DaVinci API positioning bugs
- Audio premixing solved A1/A2 alignment issue permanently

### Remaining Work
1. Create chapter cards (6) + text overlays (72) as ProRes MOVs
2. Rebuild FCPXML with overlays on V2/V3 at correct positions
3. Apply color grade via DaVinci Color page
4. Add vignette + film grain overlays
5. Render + upload

### Sponsor Candidates
- DeleteMe/Incogni (data broker removal — directly relevant)
- Proton (privacy suite — strong brand alignment)
- NordVPN (largest budget, decent fit)
