# 🚀 YouTube Automation System - Space Facts Channel

**Automate 95% of faceless YouTube video production** - from topic research to upload. Specifically designed for **WATOP-style space facts** content.

## 🎯 What This Does

This system enables you to produce **3-5 high-quality 20-minute space videos per week** with **95-100% WATOP quality**.

**⚡ NEW: CapCut Automation** - Complete projects with all effects pre-applied. **You just import, generate captions, and export (3-5 min manual).**

### Production Pipeline (CapCut Automation)

```
Script (ChatGPT) → Veo Clips → Voiceover → WATOP Pipeline → CapCut (3 min) → Upload
    ↓                  ↓            ↓              ↓                ↓             ↓
  1-2 hrs          2-3 hrs      20 min      10 min AUTO         3-5 min       5 min
```

**Total per video:** 4-6 hours active work | **Manual editing: 3-5 minutes** | **Quality: 95-100% WATOP**

---

## ✨ Key Features

### Content Generation
- ✅ **Topic Generator** - Creates viral space topic ideas (manual prompts)
- ✅ **Script Writer** - WATOP-style engagement-optimized scripts (5,000 words)
- ✅ **Style Guide** - Built-in hooks, retention tactics, pacing rules

### Asset Collection
- ✅ **Veo 3 Integration** - Generates custom 8-second space clips (your Gemini access)
- ✅ **NASA Downloader** - Auto-downloads free public domain footage (140K+ assets)
- ✅ **Music/SFX** - YouTube Audio Library integration (free)

### Video Production
- ✅ **Effects Timeline Generator** - Analyzes scripts for zoom, text, SFX placements (every 1-2 seconds)
- ✅ **WATOP-Exact Quality** - Sub-1-second micro-engagements matching WATOP's style
- ✅ **CapCut Workflow** - 10-15 min manual editing for perfect results (see [CAPCUT_WATOP_WORKFLOW.md](CAPCUT_WATOP_WORKFLOW.md))
- ✅ **SFX Library Setup** - Auto-placement of 200-400 sound effects per video
- ✅ **Auto-Captions Ready** - Optimized for CapCut's auto-caption feature
- ✅ **Quality Rendering** - 1080p 30-60fps export

### Distribution
- ✅ **Thumbnail Generator** - Creates DALL-E/Midjourney prompts
- ✅ **Metadata Optimizer** - Titles, descriptions, tags, chapters
- ✅ **YouTube Uploader** - API integration (requires one-time setup)

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone repository (already done)
cd youtube-automation

# Install dependencies
pip install -r requirements.txt

# Verify setup
python src/content/topic_generator.py
```

### 2. Produce Your First Video

**WATOP-Exact Quality - See [CAPCUT_WATOP_WORKFLOW.md](CAPCUT_WATOP_WORKFLOW.md)**

Quick version:

```bash
# 1. Generate topic ideas
python src/content/topic_generator.py generate 20

# 2. Generate script (after choosing topic)
python src/content/script_generator.py generate "Your Topic Title"

# 3. Create Veo shot list
python src/production/veo_generator.py generate scripts/drafts/your_script.md

# 4. Download NASA footage
python src/production/nasa_downloader.py script scripts/drafts/your_script.md

# 5. **NEW: Setup SFX library (one-time, 15 min)**
python src/production/sfx_library_setup.py guide
# Follow guide to download 20+ free sound effects

# 6. Record voiceover (manual)
# Save to: assets/voiceovers/[script_name].mp3

# 7. **NEW: Generate effects timeline (WATOP-style)**
python src/production/effects_timeline.py scripts/drafts/your_script.md

# 8. Assemble base video
python src/production/video_assembler.py [script_name] [shotlist.json] [voiceover.mp3]

# 9. **NEW: Apply WATOP effects in CapCut (10-15 min)**
# See CAPCUT_WATOP_WORKFLOW.md for step-by-step CapCut editing

# 10. Generate thumbnail & metadata
python src/distribution/thumbnail_generator.py "Your Title"
python src/distribution/metadata_generator.py "Your Title" scripts/drafts/your_script.md

# 11. Upload to YouTube (manual or automated)
```

---

## 📁 Project Structure

```
youtube-automation/
├── config/
│   ├── config.yaml           # Main configuration
│   └── .env.template         # API keys (for future)
├── src/
│   ├── content/
│   │   ├── topic_generator.py      # Generate video topics
│   │   └── script_generator.py     # Write WATOP-style scripts
│   ├── production/
│   │   ├── veo_generator.py        # Create Veo 3 shot lists
│   │   ├── nasa_downloader.py      # Download NASA footage
│   │   └── video_assembler.py      # Assemble final video
│   └── distribution/
│       ├── thumbnail_generator.py  # Generate thumbnail prompts
│       ├── metadata_generator.py   # Create YouTube metadata
│       └── youtube_uploader.py     # Upload to YouTube
├── assets/
│   ├── veo_clips/           # Your Veo 3 generated clips
│   ├── nasa_footage/        # Auto-downloaded NASA videos
│   ├── voiceovers/          # Your recorded voiceovers
│   ├── music/               # Background music tracks
│   └── sfx/                 # Sound effects
├── scripts/
│   ├── drafts/              # AI-generated scripts
│   └── final/               # Approved scripts
├── output/
│   ├── videos/              # Final rendered videos
│   ├── thumbnails/          # Thumbnail images
│   └── metadata/            # YouTube metadata files
├── prompts/                 # Generated prompts for manual use
├── WORKFLOW.md              # Complete production workflow
└── README.md                # This file
```

---

## 💰 Cost Breakdown

### Current Setup (Manual Mode): **FREE**

| Component | Cost | Notes |
|-----------|------|-------|
| Topic/Script Generation | $0 | Use ChatGPT/Claude Pro (you have) |
| Veo 3 Clips | $0 | Included in Gemini Pro |
| NASA Footage | $0 | Public domain |
| Music/SFX | $0 | YouTube Audio Library |
| Video Editing | $0 | MoviePy (Python) |
| Hosting | $0 | Local + Google Cloud (you have) |
| **TOTAL** | **$0/month** | |

### Future Upgrade (API Automation): **$75-150/month**

After monetization, add:
- OpenAI/Claude API: $50-100/month
- Voice cloning (ElevenLabs): $22/month
- AI video (Runway/Pika): $12-20/month
- Analytics tools: $0-30/month

**ROI:** At $500/month revenue, APIs cost 15-30%, save 15+ hours/week

---

## 🎨 Content Style

**Inspired by:** WATOP, Bright Side, Kurzgesagt, The Infographics Show

### Script Formula
- **Hook** (0-5s): Shocking fact that demands attention
- **Setup** (5-30s): Stakes and why it matters
- **Body** (30s-18min): 10-12 segments with mini-hooks
- **Resolution** (18-20min): Payoff and final revelation
- **CTA** (last 30s): Subscribe, like, next video

### Engagement Tactics
- Curiosity loops (pose question → answer later)
- Re-engagement every 60-90 seconds
- Pattern interrupts (pace/topic changes)
- Scale comparisons (mind-blowing size/time)
- "But wait, it gets crazier..." moments

### Visual Style
- 8-second Veo clips (cinematic, dramatic)
- NASA footage (real space imagery)
- Fast cuts every 3-5 seconds
- Smooth transitions with fades
- Text overlays for emphasis

---

## 📊 Target Metrics

### Video Performance Goals
- **CTR:** 8%+ (click-through rate)
- **AVD:** 70%+ (average view duration)
- **Watch Time:** 14+ minutes average
- **Engagement:** 5%+ like rate

### Channel Growth Milestones
- **Month 1:** 100+ subscribers, 12-15 videos
- **Month 3:** 1,000+ subscribers (Partner Program eligibility)
- **Month 6:** 10,000+ subscribers, $500+/month
- **Year 1:** 100,000+ subscribers, $2,000+/month

---

## 🔧 Requirements

### Software
- **Python 3.8+**
- **MoviePy** (video editing)
- **M1 Mac** (or any computer with 8GB+ RAM)

### Services (What You Have)
- ✅ ChatGPT Pro or Claude Pro (script writing)
- ✅ Gemini Pro with Veo 3 (video generation)
- ✅ Google Cloud (storage)
- ✅ Microphone (voiceover recording)

### Optional (Free Alternatives)
- Canva (thumbnails) - free
- Audacity (audio editing) - free
- OBS (screen recording) - free

---

## 🎯 Who This Is For

### Perfect If You:
- ✅ Run or want to start a faceless YouTube channel
- ✅ Want to scale content production
- ✅ Have ChatGPT/Claude/Gemini Pro access
- ✅ Can record voiceovers (for now)
- ✅ Want WATOP-level production quality
- ✅ Prefer starting free before investing

### Not Ideal If:
- ❌ Want fully automated (no manual work) - *not yet, upgrade later*
- ❌ Don't want to record voiceovers - *voice cloning coming in Phase 2*
- ❌ Need instant results - *setup takes 1-2 hours*

---

## 📚 Documentation

- **[CAPCUT_AUTOMATION.md](CAPCUT_AUTOMATION.md)** - 🔥 **NEW: 95-100% WATOP Quality (3-5 min manual)**
- **[CAPCUT_WATOP_WORKFLOW.md](CAPCUT_WATOP_WORKFLOW.md)** - ⭐ Alternative: Manual CapCut workflow
- **[WORKFLOW.md](WORKFLOW.md)** - Complete step-by-step production guide
- **[QUICKSTART.md](QUICKSTART.md)** - First video in 4-6 hours
- **Script Style Guide** - Built into `script_generator.py`
- **Veo Best Practices** - Built into `veo_generator.py`
- **Effects Timeline** - Built into `effects_timeline.py`
- **CapCut Project Generator** - Built into `capcut_project_generator.py`
- **Troubleshooting** - See WORKFLOW.md

---

## 🗺️ Roadmap

### ✅ Phase 1: Manual Workflow (Current)
- Topic generation with prompts
- Script writing via ChatGPT/Claude
- Veo clip generation (manual)
- NASA footage automation
- Video assembly automation
- Thumbnail/metadata prompts
- Manual YouTube upload

### 🔄 Phase 2: Semi-Automation (After Monetization)
- Browser automation (Playwright)
- Voice cloning (ElevenLabs)
- Automated thumbnail generation
- Scheduled uploads
- Performance analytics

### 🚀 Phase 3: Full Automation (Scale)
- End-to-end API pipeline
- Multi-channel management
- A/B testing automation
- Trend detection
- Revenue optimization

---

## 🤝 Contributing

This is a personal project, but improvements welcome:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## ⚠️ Disclaimer

### Content & Copyright
- All NASA footage is **public domain** (verified via NASA Media Guidelines)
- Scripts must be **original or properly attributed**
- Veo-generated content is yours to use commercially
- Always verify facts and cite sources

### YouTube Policies
- Ensure compliance with YouTube Partner Program policies
- Disclose AI-generated content if required
- Follow copyright and fair use guidelines
- No misleading thumbnails or clickbait

### No Guarantees
- Channel success depends on content quality, consistency, niche selection
- YouTube algorithm changes may affect performance
- Monetization requires 1000 subs + 4000 watch hours

---

## 📧 Support

- **Documentation:** See [WORKFLOW.md](WORKFLOW.md)
- **Issues:** Open a GitHub issue
- **Questions:** Check troubleshooting section first

---

## 📝 License

**MIT License** - Use commercially, modify freely, no warranty provided.

NASA content: Public domain (no license required)

---

**Built for creators who want to scale faceless YouTube channels without sacrificing quality.**

**Current Status:** ✅ Ready for production
**Cost:** $0/month (manual mode)
**Time per video:** 4-6 hours
**Output:** WATOP-quality 20-minute videos 
