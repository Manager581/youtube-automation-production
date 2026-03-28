# Pipeline V2 Roadmap

## ✅ BUILT (this session)
- pipeline_v2/ — 17 scripts, LearnByLeo + Claude + DaVinci
- check_learnbyleo_script.py, voice.py, video.py — 3 QA gates
- run_pipeline_v2.py — 21-stage orchestrator
- executive_producer.py — 11 cross-reference checks

## 🔧 BUILDING NOW (items 1-5, required for closed loop)
1. Vision analyzer — Claude vision on every clip/image
2. Research agent — auto-source footage from YouTube/Google/TikTok
3. Director review loop — read DaVinci back, verify decisions executed
4. Per-segment LearnByLeo validator — score each decision against playbook
5. Footage gap resolver — fill holes automatically

## 📋 FUTURE BUILDS (next sessions)
### Technical Debt
- [ ] run_pipeline_v2.py fully self-contained (no pipeline/ v1 fallbacks)
- [ ] CLAUDE.md rewrite for pipeline_v2 order
- [ ] MEMORY.md update (remove Fern/Ollama references)

### Features
- [ ] Thumbnail generator (Claude describes ideal → generate image)
- [ ] Auto-publish (YouTube Data API upload with title/description/tags)
- [ ] Multi-topic queue (run 5 topics in parallel, pick best)
- [ ] Cost tracker (log Claude API calls per video)
- [ ] Audience feedback integration (YouTube analytics → retention drop-off → director learns)
- [ ] Music mood matcher (director picks music moments, not just one track)
- [ ] Voice register controller (render each segment with matched emotion register)
- [ ] A/B title testing (live test on YouTube)
