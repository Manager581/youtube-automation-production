# Pipeline V2 Roadmap

## ✅ BUILT (this session — 2026-03-28)

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
- topic_scorer.py — 4-test validation via Claude
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

## 📋 FUTURE BUILDS (next sessions)

### Technical Debt
- [ ] run_pipeline_v2.py: remove pipeline/ v1 fallbacks (topic_radar, comments_miner, etc. need v2 versions)
- [ ] CLAUDE.md: full rewrite for pipeline_v2
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

## How to Start
```bash
cd /Users/jefflawrence/Documents/youtube-automation-production
python run_pipeline_v2.py --topic "Your Topic" --stage all
```
