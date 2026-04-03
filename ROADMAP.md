# Pipeline V2 Roadmap

## ✅ BUILT (session 2026-03-28)

### Secret Scores Video: 92% PASS, ready for playthrough

### Core Pipeline (21 scripts in pipeline_v2/)
- llm.py — Claude Code CLI (brain, no Ollama)
- script_enhancer.py — [BEAT][PAUSE][VOICE] markers via Claude + scripting.json
- storyboard_generator.py — Visual brief per segment via Claude + editing.json
- director.py — Sees ALL assets, picks EXACT files, controls everything
- transcript_extractor.py — Extract what clips SAY (srt/vtt/yt-dlp)
- vision_analyzer.py — Claude vision on every clip/image frame
- research_agent.py — Auto-source from YouTube/Google/Pexels/Pixabay
- segment_validator.py — Score each segment vs 7 LearnByLeo rules
- gap_resolver.py — Fill footage gaps automatically (closed loop)
- director_review.py — Read DaVinci back, verify decisions executed
- executive_producer.py — 11 cross-reference checks, final gate
- davinci_timeline_builder.py — Reads v3 schema, builds in DaVinci
- davinci_helpers.py — ProRes/fades/typewriter/ducking
- footage_verifier.py — Claude vision verification
- clip_analyzer.py — Best frame selection
- web_image_sourcer.py — Chrome + Google + Pexels (no CC restriction)
- topic_scorer.py — 7-test validation via Claude (calibrated against 10 proven competitor hits)
- title_thumbnail_evaluator.py — 26 clickbait tactics
- production_rules.py — LearnByLeo editing rules
- fair_use_guard.py — Clip duration + source limits

### QA Gates (3 scripts)
- check_learnbyleo_script.py — Script QA (green/purple, pacing, energy)
- check_learnbyleo_voice.py — Voice QA (WPM, LUFS, variation)
- check_learnbyleo_video.py — Video QA (20 checks against DaVinci timeline)

### Orchestrator
- run_pipeline_v2.py — 28 stages, 8 phases, state persistence, Ctrl+C safe

### Closed Loop
```
director → builder → director_review → gap_resolver → research_agent → vision_analyzer → director
```

## ✅ BUILT (session 2026-03-28 evening)

### Topic Scorer v2: 7-Test Framework
- Calibrated by downloading + analyzing transcripts from 10 proven hits (1.8M-5.4M views)
- Channels analyzed: Johnny Harris, Wendover Productions, ColdFusion, More Perfect Union
- 3 new tests added: Blind Spot (9/10 = 3.7M+), Timeliness (news wave multiplier), Killer Stat (one shareable number)
- GO threshold raised to 85+ (was 80+), all 7 tests must score 65+
- Key finding: Blind Spot score is #1 predictor of virality for new channels
- Brand config: `brand_configs/learnbyleo.json` created for topic_radar.py
- Competitor transcripts + analysis: `/tmp/competitor_transcripts/`
- Calibration data embedded in `pipeline_v2/topic_scorer.py` CALIBRATION_EXAMPLES constant

## ✅ BUILT (session 2026-03-29)

### Channel Pivot: Business/Tech Documentary
- Shifted from Fern-style investigative to ColdFusion/HMW business documentary
- Reason: no original journalism = can't compete with ProPublica on investigative. Business data is public.
- RPM: $10-25 (business/tech) vs $5-10 (true crime). 2-3x revenue per view.
- Upload cadence: daily/frequent (pipeline does topic→video in days)
- Reference channels: ColdFusion, How Money Works, PolyMatter, The Plain Bagel, Slidebean

### Topic Scorer v3: 8-Test Framework
- Added 8th test: **5-Second Title Test** — can a cold viewer read the title and instantly know what's at stake for THEM?
- Secret Scores scored 85/100 on title test (highest), validating the test design
- "Broadridge" scored ~30 (nobody knows what it is) — correctly identified as bad topic
- GO threshold: 85+ with all 8 tests ≥65
- Business niche recalibration still pending (blind spot weight should be lower for analysis-depth topics)

### Comment Mining Infrastructure
- Mined 797 comments from HMW "Break The Law" + 1679 from "Find Out Stage"
- Key audience signal (507 likes): "If the penalty is a fine, it's legal for a price"
- Added comment analysis workflow: yt-dlp → JSON → keyword filter → sort by likes → extract insights

### New Video: "Why Breaking the Law Is Profitable"
- **Script v45**: `scripts/raw_breaking_law_v45.txt` — 4,224 words (~30 min), 87-91/100 LearnByLeo score
- Research facts: `research/breaking_law_profitable_facts.md` (10 case studies, all verified)
- 7 chapters: THE FORMULA → THE DATA → THE MACHINES → THE RENT → THE RECKONING
- Focus: Facebook/AI/Reddit = 70% of script, historical (Ford/WF/Purdue) = 17% setup
- 4 named characters with callbacks: Grimshaw (Ford), Guitron (Wells Fargo), Esquivel (AI), Vialpondo (RealPage)
- Thesis: "The law doesn't prevent corporate crime. It prices it." — withheld until Purdue, echoed at close
- Killer stats: $1T in fines since 2000, recidivists get SMALLER fines, Zuckerberg gained $1.1B from fine announcement
- Sponsor fit: privacy/data protection (Incogni, DeleteMe, NordVPN, Proton)
- **Pipeline state**: script DONE (stage 5), enhancer running (stage 6), stages 7-28 pending

### Source Credits Policy
- Added to pipeline: always credit original journalists when using their reporting
- On-screen lower-third + description links
- Ethical + fair use armor + goodwill (journalists share videos that credit them)

## 📋 FUTURE BUILDS (next sessions)

### Breaking Law Video Progress (session 2026-03-30)
- [x] Script v45 — 4,366 words, 95+ LearnByLeo score
- [x] Enhancer — [BEAT][PAUSE][VOICE] markers added
- [x] Script QA — 95+ score, all playbook checks pass
- [x] Voice — F5-TTS 17.4 min, resume patch (skip existing chunks)
- [x] Voice QA — PASS (1 warning: peak near 0dBFS)
- [x] Music — CC0 Pixabay track, ducked (-24dB under VO)
- [x] Footage — 12 video clips (yt-dlp)
- [x] Images — 51 images (Pexels/Google/Wikimedia)
- [x] Storyboard — 13 scenes, 83 segments
- [x] **Transcripts** — 12 clips transcribed (stage 13)
- [x] **Vision analysis** — 12 clips + 51 images analyzed via Claude vision (stage 14)
- [x] **Verify footage** — passed (stage 15)
- [x] **Re-run director** with transcript+vision data — 103 segments, 4 batches (stage 17)
- [x] **Re-validate segments** — 5 auto-fixes applied (stage 18)
- [x] **Fill gaps** — 30 new images sourced (stage 19)
- [x] **FCPXML builder** — `pipeline_v2/fcpxml_builder.py` bypasses DaVinci API bugs
- [x] **DaVinci import** — "Breaking Law FINAL" timeline via File > Import > Timeline (stage 23)
- [x] **Director review** — ran (stage 24)
- [x] **Executive producer** — 3/11 pass, issues are DaVinci FCPXML placement (stage 26)
- [ ] **Manual polish** — consolidate V2/V3 overlays, verify playback
- [ ] Render + upload (stages 27-28)

### Pipeline Architecture Fix (session 2026-03-31)
- **Gates now BLOCK on failure** — exit 1 stops pipeline, auto-retries fix stages
- 8 gate stages: qa_script, qa_voice, verify_footage, validate_segments, fill_gaps, exec_producer_pre, director_review, exec_producer
- New `exec_producer_pre` gate runs BEFORE DaVinci build (catches issues early)
- `GATE_MAX_RETRIES = 2` — retry loops with fix stage re-runs
- Segment validator: >30% warnings = FAIL (was soft warning)
- Gap resolver: <60% confidence = FAIL (was always pass)
- Footage verifier: >20% fail rate = FAIL (had no threshold)

### FCPXML Builder (session 2026-03-31)
- `pipeline_v2/fcpxml_builder.py` — generates FCPXML 1.9 with correct clip positions
- Bypasses DaVinci AppendToTimeline bug (ignores recordFrame)
- V1 clips on spine at exact `_timeline_start_sec` positions
- A1 narration + A2 music both start at frame 0 (alignment solved)
- SFX on lanes 7/8 at correct segment positions
- Import via DaVinci UI: File > Import > Timeline (AppleScript automation)

### Bugs Fixed (session 2026-03-30)
- **llm.py**: stdin pipe for large prompts (was passing 21K chars as CLI arg)
- **director.py**: batched processing — 4×30 segments (was timing out at 103)
- **voice_generator.py**: resume/skip-existing patch (process kept getting killed)
- **footage_sourcer.py**: v2 storyboard compat (nested scenes vs flat segments)
- **davinci_timeline_builder.py**: clip_start_sec None handling
- **davinci_timeline_builder.py**: simultaneous A1+A2 placement (music after narration fix)
- **DaVinci AppendToTimeline**: STILL ignores recordFrame — need FCPXML or computer-use MCP

### Critical Discovery: Director Was Blind
- Director was picking clips by FILENAME only — no transcripts, no vision descriptions
- Stages 13-15 (transcripts, vision, verify) were skipped before director ran
- Must ALWAYS run 13→14→15→17 in sequence — director needs full clip knowledge
- Pipeline v2 stage ordering is CORRECT, we just skipped stages

### Pipeline V2 Overhaul (session 2026-03-31 evening)
- [x] **narration_aligner.py** — Whisper word-level forced alignment (replaces 150 WPM estimates)
- [x] **Director upgrade** — vision descriptions now in Claude prompt (was loaded but unused), `music_state` per segment, asset sufficiency check (exits 1 if < 0.8x coverage), Whisper alignment timestamps
- [x] **FCPXML builder fixes** — absolute file paths (`os.path.abspath`), API import with `timelineName` option (was returning None), lane clips on trailing gap with correct offset math
- [x] **Pipeline orchestrator** — added `align` stage, 1800s timeout (was 600s), UTF-8 subprocess env, wired gapfilled director JSON + alignment path
- [x] **Footage sourcer** — MIN_VIABLE_CLIPS raised from 2 to 15
- [x] **Unicode fix** — `sys.stdout.reconfigure(encoding='utf-8')` in all DaVinci-reading scripts

Key bugs found:
- DaVinci `ImportTimelineFromFile` returns None unless you pass `{"timelineName": "..."}` option
- FCPXML `file://` URLs must be absolute — relative paths cause silent clip drops on import
- Director was picking clips by filename only — vision data loaded but never passed to Claude's prompt
- Director timing estimated at 150 WPM linear — Whisper gives actual word-level timestamps
- Never hack around pipeline gates — produces Frankenstein videos

### Breaking Law Video — Session 2026-03-31 night
- [x] FCPXML overlay offset fix (lane clips on trailing gap, correct math)
- [x] FCPXML absolute file paths (os.path.abspath)
- [x] DaVinci API import fix (timelineName parameter required)
- [x] Whisper narration aligner (word-level timestamps)
- [x] Director upgrade (vision in prompt, music_state, alignment, sufficiency check)
- [x] Segment validator auto-fix + re-validate
- [x] Overlay matching (sequential index, 44/50 found)
- [x] clip_audio modes (play, play_then_mute, mute)
- [x] V1 gap fill (extend clips to next segment boundary)
- [x] Music loop to 100% timeline coverage
- [x] Unicode fixes (_safe_str, _sanitize_strings, encoding='utf-8')
- [ ] **BLOCKER: Narration WAV is broken** — F5-TTS hallucinated "what your life looks like" 88 times. MUST regenerate
- [ ] Source 15+ video clips (only 3 exist) — fix footage_sourcer args
- [ ] Source 3-5 CC0 music tracks — fix music_sourcer args
- [ ] Source 15+ varied SFX (only 6 unique sounds)
- [ ] Image diversity enforcement in builder (currently no cap on images)
- [ ] Chapter card styling (current: plain white-on-black)
- [ ] Voice QA: add hallucination detection (repeated phrase check in Whisper output)
- [ ] Director second pass (self-review for source reuse, thin coverage)
- [ ] exec_producer_pre: should check director JSON, not stale DaVinci timeline

### How to Resume (next session) — Chapter-by-Chapter Assembly

ALL assets are ready. Do NOT re-run voice, director, footage, or image stages. Go straight to assembly.

**Strategy:** Build each chapter as a separate FCPXML, import one at a time into DaVinci, verify each looks right before moving on. This prevents the monolithic builder from cycling images or carpet-bombing SFX.

**The 5 chapters** (from director v4):
1. **INTRO + THE FORMULA** (0-250s) — Ford Pinto, Grimshaw, Wells Fargo, Purdue
2. **THE DATA** (250-460s) — Facebook, Cambridge Analytica, Zuckerberg hearing
3. **THE MACHINES** (460-680s) — AI scraping, training data, copyright
4. **THE RENT** (680-900s) — RealPage, rent algorithms, settlements
5. **THE RECKONING** (900-1200s) — GDPR, proportional fines, Eliana Esquivel, thesis

**For each chapter:**
1. Extract segments from `storyboards/breaking_law_directed_v4.json` for that time range
2. Pick UNIQUE visuals for each segment (no repeats within chapter)
3. Place 1-2 SFX MAX per chapter at key dramatic moments (using Whisper word timestamps)
4. Assign that chapter's music track (track 1→ch1, track 2→ch2, etc.)
5. Build FCPXML for just that chapter
6. Import into DaVinci via API (`ImportTimelineFromFile` with `timelineName`)
7. Verify it looks right
8. Move to next chapter

**Key files:**
```
storyboards/breaking_law_directed_v4.json   — director decisions (113 segments)
audio/breaking_law/narration.wav            — clean narration (20 min)
audio/breaking_law/narration_alignment.json — word-level timestamps
footage/breaking_law/clips/                 — 23 video clips (transcribed)
footage/breaking_law/images/                — images in seg_NNN/ subdirs
footage/breaking_law/gap_fills/images/      — 251 gap-fill images
assets/breaking_law/overlays/               — 75 overlay MOVs (tw_NNN_*.mov)
assets/breaking_law/chapters/               — 5 chapter card MOVs
assets/sfx/                                 — 18 normalized SFX WAVs (*_loud.wav)
audio/breaking_law/music_tracks/            — 4 music WAVs (tense/investigative/emotional/dark)
```

**Environment:**
```bash
cd /Users/jefflawrence/Documents/youtube-automation-production
export PATH="/opt/homebrew/bin:/Users/jefflawrence/.local/bin:$PATH"
# Python: venv/bin/python (NOT system python)
# DaVinci API: PYTHONPATH="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
# Whisper SSL fix: SSL_CERT_FILE=$(venv/bin/python -c "import certifi; print(certifi.where())")
# DaVinci import: mp.ImportTimelineFromFile(path, {"timelineName": "..."})  ← MUST pass timelineName
```

### Immediate TODO
- [ ] Source credits field in director schema
- [ ] Sponsor integration placeholder in script structure
- [ ] Recalibrate scorer for business/tech niche

### Technical Debt
- [ ] run_pipeline_v2.py: remove pipeline/ v1 fallbacks (topic_radar, comments_miner, etc. need v2 versions)
- [ ] MEMORY.md: remove all Fern/Ollama references

### Features
- [ ] Thumbnail generator (Claude describes ideal → generate image)
- [ ] Auto-publish (YouTube Data API upload with title/description/tags)
- [ ] Multi-topic queue (run 5 topics in parallel, pick best)
- [ ] Cost tracker (log Claude API calls per video)
- [ ] Audience feedback integration (YouTube analytics → retention graph → director learns)
- [ ] Music mood matcher (director picks music MOMENTS, not just one track)
- [ ] Voice register controller (render each segment with matched emotion)
- [ ] A/B title testing (live test on YouTube)
- [ ] Comment miner v2: auto-analyze competitor comments for topic validation
- [ ] News peg detector: monitor DOJ/FTC/SEC press releases for fresh stories

## How to Start
```bash
cd /Users/jefflawrence/Documents/youtube-automation-production
python run_pipeline_v2.py --topic "Your Topic" --stage all
```
