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
- Research brief: `research/breaking_law_brief.md`
- 6-act structure, ~35 minutes, 7 case studies
- RealPage $0 settlement (THIS WEEK) + AI scraping wars + Boeing/Meta/Wells Fargo/Purdue
- Killer stat: $1 trillion in corporate fines since 2000
- Sponsor fit: privacy/data protection (Incogni, DeleteMe, NordVPN)
- Pipeline state: stages 1-2 complete, stage 3 (research brief) written

### Source Credits Policy
- Added to pipeline: always credit original journalists when using their reporting
- On-screen lower-third + description links
- Ethical + fair use armor + goodwill (journalists share videos that credit them)

## 📋 FUTURE BUILDS (next sessions)

### Immediate (this video)
- [ ] Recalibrate scorer for business/tech niche (lower blind spot weight, add analysis depth test)
- [ ] Write script for "Why Breaking the Law Is Profitable"
- [ ] Source credits field in director schema
- [ ] Sponsor integration placeholder in script structure

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
