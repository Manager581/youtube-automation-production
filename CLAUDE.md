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

## What Was Completed This Session

### All Done ✅
1. **Script v4 rewrite** — Blind review 70→80. Added: Diane's story (callback), shoe-size tonal break, thesis line, CTA woven into stories.
2. **Chrome-powered visual sourcer** (`pipeline/web_image_sourcer.py`) — Searches government archives + web, verifies with Claude Vision, downloads best matches. No Pixabay/Pexels.
3. **Clip verifier** (`pipeline/clip_verifier.py`) — Extracts frames at intervals, Claude Vision confirms content match. Finds best 3-5s segment.
4. **Fair use guard** (`pipeline/fair_use_guard.py`) — Max 5s clips, mandatory narration, mute source audio, 2+ transformative layers, attribution logging.
5. **Orchestrator wiring** — Playbook quality gates at qa_script, director, footage, and assemble stages.
6. **Bug fixes** — SFX file mapping (7 missing files), logging import, black frame warnings.

## What's Still Not Done

### Pipeline Progress on Secret Scores
- `scripts/raw_secret_scores_v4.txt` — Final script (blind review ~80/100)
- `scripts/enhanced_secret_scores.txt` — Enhanced with 59 VOICE, 57 PAUSE, 51 BEAT markers
- `storyboards/secret_scores.json` — Generated (in progress or complete)
- `storyboards/secret_scores_directed.json` — Director pass (pending)
- Voice, footage, assembly — Not yet run

### Modules Switched from Ollama to Claude Max
- `pipeline/script_enhancer.py` — `enhance_script()` uses Claude Opus primary
- `pipeline/storyboard_generator.py` — `_llm_generate()` uses Claude Haiku primary
- Both fall back to Ollama only if Claude CLI fails

### Next Session Should Do
1. **Complete storyboard + director pass** if not finished this session
2. **Run voice generation** on enhanced script
3. **Source footage** using web_image_sourcer + standard sourcer
4. **Assemble video** — first end-to-end render
5. **Final verification loop** — Scene-by-scene review before export
6. **SFX library expansion** — Download more CC0 SFX to fill gaps
7. **Merge decision** — When ready, merge `feature/learnbyleo-integration` into main working branch

## Tools & Access
- **Claude Max** subscription (Opus available via `claude` CLI)
- **Chrome MCP** — Full browser control (navigate, click, type, screenshot). Tab group ID may change between sessions. Use `tabs_context_mcp` to get current tabs.
- **Computer-use MCP** — Desktop app control (Slack, etc.). Chrome is read-only through this tool; use Chrome MCP instead.
- **yt-dlp** — Updated to 2026.3.17, works with `--cookies-from-browser chrome`
- **FFmpeg** — Available for video processing
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
