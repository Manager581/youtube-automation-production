# Space Facts YouTube Automation - Complete Workflow

## 📋 Overview

This system automates 90% of YouTube video production for faceless space content channels (WATOP-style). The workflow is designed for **manual copy/paste** initially (free), with the ability to upgrade to full API automation later.

**Target Output:** 3-5 high-quality 20-minute space videos per week

---

## 🚀 Quick Start

### 1. Initial Setup (One-Time)

```bash
# Install dependencies
pip install -r requirements.txt

# Create necessary directories (already done)
# Configure settings
cp config/.env.template config/.env
# Edit config/config.yaml if needed
```

### 2. Complete Workflow for ONE Video

**Time Estimate:** 4-6 hours per video (manual mode)

---

## 📺 Step-by-Step Video Production

### PHASE 1: Content Planning (30 minutes)

#### Step 1.1: Generate Topic Ideas

```bash
python src/content/topic_generator.py generate 20
```

**What this does:**
- Creates a prompt file for ChatGPT/Claude
- Asks for 20 viral-worthy space topic ideas

**Your actions:**
1. Open the generated prompt file (location shown in output)
2. Copy entire prompt
3. Paste into ChatGPT-4 or Claude
4. Review the 20 topic ideas
5. Choose 1 topic for your next video
6. Save the AI response

#### Step 1.2: Analyze Competitors (Optional)

```bash
python src/content/topic_generator.py competitors
```

- Use this to understand what's working in the space niche
- Identify content gaps
- Refine your topic choice

---

### PHASE 2: Script Writing (1-2 hours)

#### Step 2.1: Generate Script Prompt

```bash
python src/content/script_generator.py generate "Your Chosen Topic Title"
```

**Example:**
```bash
python src/content/script_generator.py generate "Black Holes That Defy Physics"
```

**What this does:**
- Creates a comprehensive script writing prompt
- Includes WATOP style guide
- Specifies engagement techniques
- Requests 5,000-word script (~20 minutes)

**Your actions:**
1. Open the generated prompt file
2. Copy entire prompt
3. Paste into ChatGPT-4 or Claude (Claude Sonnet recommended for longer context)
4. Wait for full script generation
5. Save the script as: `scripts/drafts/[topic_name]_[date].md`

#### Step 2.2: Validate Script

```bash
python src/content/script_generator.py validate scripts/drafts/your_script.md
```

**What this checks:**
- Word count (should be ~5,000 words)
- Hook presence (first 5 seconds)
- Visual cues `[SHOW: ...]`
- Music cues `[MUSIC: ...]`
- CTA (call-to-action at end)

**If validation fails:** Edit the script or regenerate with adjustments

---

### PHASE 3: Asset Collection (2-3 hours)

#### Step 3.1: Generate Veo Shot List

```bash
python src/production/veo_generator.py generate scripts/drafts/your_script.md
```

**What this does:**
- Parses your script for `[SHOW: ...]` cues
- Generates optimized Veo 3 prompts
- Creates both JSON and human-readable shot lists

**Your actions:**
1. Open the generated `_shotlist.txt` file
2. Go to [Google AI Studio](https://aistudio.google.com/)
3. For each shot in the list:
   - Copy the Veo prompt
   - Paste into Veo 3
   - Generate 8-second clip
   - Download as: `assets/veo_clips/[script_name]/veo_clip_001.mp4` (002, 003, etc.)

**Tips for Veo:**
- Generate in batches (10-20 at a time)
- Keep clips organized by number
- Veo quota: Check your limits in AI Studio

#### Step 3.2: Download NASA Footage

```bash
python src/production/nasa_downloader.py script scripts/drafts/your_script.md
```

**What this does:**
- Automatically analyzes your script
- Identifies space-related keywords
- Downloads relevant footage from NASA (free, public domain)
- Saves to `assets/nasa_footage/`

**Manual alternative:**
```bash
python src/production/nasa_downloader.py search "black hole, nebula, galaxy" 15
```

**Your actions:**
- Let it run (takes 10-20 minutes)
- Downloads are automatic
- Check `assets/nasa_footage/` when complete

#### Step 3.3: Record Voiceover

**Your actions:**
1. Open your script
2. Record your voiceover (use any recording software)
   - Audacity (free)
   - GarageBand (Mac)
   - Adobe Audition
3. Save as: `assets/voiceovers/[script_name].mp3` or `.wav`

**Tips:**
- Use consistent microphone setup
- Record in quiet space
- Match pacing: ~250 words per minute
- Save as high quality (192kbps+)

#### Step 3.4: Add Music (Optional)

**Free music sources:**
- YouTube Audio Library (royalty-free)
- https://www.free-stock-music.com
- https://incompetech.com/music/

**Your actions:**
1. Download 1-2 background music tracks
2. Save to: `assets/music/`
3. Choose dramatic/cinematic space-themed tracks

---

### PHASE 4: Video Assembly (1 hour + render time)

#### Step 4.1: Assemble Video

```bash
python src/production/video_assembler.py [script_name] prompts/veo_shots/[script_name]_shotlist.json assets/voiceovers/[script_name].mp3
```

**Example:**
```bash
python src/production/video_assembler.py black_holes prompts/veo_shots/black_holes_shotlist.json assets/voiceovers/black_holes.mp3
```

**What this does:**
- Combines Veo clips in sequence
- Fills gaps with NASA footage
- Syncs with your voiceover
- Adds background music (15% volume)
- Applies fades and transitions
- Exports final 1080p video

**Your actions:**
1. Run the command
2. Wait for rendering (may take 1-3 hours depending on your M1)
3. Video saves to: `output/videos/`
4. Review the video

**If you're not happy with the result:**
- Adjust footage order manually
- Replace specific Veo clips
- Re-run assembly

---

### PHASE 5: Distribution (30 minutes)

#### Step 5.1: Generate Thumbnail

```bash
python src/distribution/thumbnail_generator.py "Your Video Title"
```

**What this does:**
- Creates 3 thumbnail prompt variations
- Optimized for WATOP style
- Includes text overlay suggestions

**Your actions:**
1. Open the generated thumbnail prompt file
2. Choose DALL-E 3 or Midjourney:
   - **DALL-E 3:** Use ChatGPT Plus (easiest)
   - **Midjourney:** Use Discord bot
3. Generate 3 variations
4. Add text overlay in:
   - Canva (free, easiest)
   - Photoshop
   - Figma
5. Save as: `output/thumbnails/[video_name]_v1.jpg`

**Thumbnail tips:**
- Bold white text with black outline
- High contrast
- 1280x720 resolution
- Test multiple versions

#### Step 5.2: Generate Metadata

```bash
python src/distribution/metadata_generator.py "Your Video Title" scripts/drafts/your_script.md
```

**What this does:**
- Creates optimized YouTube title
- Generates description with chapters
- Creates 20 relevant tags
- Exports ready-to-paste metadata

**Your actions:**
1. Review the generated metadata
2. Make any adjustments
3. Keep the file for upload

#### Step 5.3: Upload to YouTube

**Option A: Manual Upload (Easiest)**
1. Go to https://studio.youtube.com/
2. Click "Upload videos"
3. Select your video from `output/videos/`
4. Copy/paste metadata from the generated file:
   - Title
   - Description (with chapters)
   - Tags
5. Upload thumbnail
6. Set to "Public" or "Scheduled"
7. Publish

**Option B: Automated Upload (Requires Setup)**

**One-time setup:**
```bash
# 1. Install YouTube API libraries
pip install google-api-python-client google-auth-oauthlib

# 2. Set up Google Cloud credentials
# Follow: https://developers.google.com/youtube/v3/quickstart/python
# Download client_secrets.json to config/

# 3. Authenticate
python src/distribution/youtube_uploader.py auth
```

**Upload:**
```bash
python src/distribution/youtube_uploader.py upload output/videos/your_video.mp4 output/metadata/metadata_your_video.json
```

---

## 📊 Weekly Production Schedule

### Goal: 3-5 Videos/Week

**Batch Production Strategy:**

#### Monday (3 hours)
- Generate 10 topic ideas
- Select 5 topics for the week
- Generate all 5 script prompts
- Paste into ChatGPT/Claude

#### Tuesday (4 hours)
- Review/edit all 5 scripts
- Generate Veo shot lists for all
- Start generating Veo clips (batch process)

#### Wednesday (4 hours)
- Continue Veo clip generation
- Download NASA footage for all videos
- Record voiceovers for 2-3 videos

#### Thursday (4 hours)
- Finish voiceovers
- Assemble 2-3 videos (let render overnight)

#### Friday (3 hours)
- Generate thumbnails for all
- Generate metadata for all
- Upload 2-3 videos

#### Weekend
- Monitor performance
- Schedule remaining uploads
- Plan next week's topics

**Total time:** ~18-20 hours/week for 5 videos = ~4 hours per video

---

## 💡 Pro Tips

### Efficiency Hacks

1. **Batch Everything**
   - Generate 5 scripts at once
   - Create all Veo clips in one session
   - Record multiple voiceovers back-to-back

2. **Reuse Assets**
   - Keep NASA footage library
   - Reuse music tracks
   - Build Veo clip library

3. **Templates**
   - Save script formulas that work
   - Reuse thumbnail styles
   - Create title templates

4. **Overnight Rendering**
   - Queue video assemblies at night
   - Let your M1 work while you sleep

### Quality Control

1. **Script Review Checklist:**
   - [ ] Strong hook (first 5 seconds)
   - [ ] Re-engagement every 60-90 seconds
   - [ ] Facts are accurate
   - [ ] Visual cues throughout
   - [ ] Strong CTA at end

2. **Video Review Checklist:**
   - [ ] Audio levels balanced
   - [ ] No jarring transitions
   - [ ] Visuals match voiceover
   - [ ] 20 minutes ± 1 minute
   - [ ] Export quality good (1080p)

3. **Thumbnail Checklist:**
   - [ ] Text is readable on mobile
   - [ ] High contrast
   - [ ] Eye-catching
   - [ ] Accurate to content

### Optimization After Launch

**Track these metrics:**
- Click-through rate (CTR) - aim for 8%+
- Average view duration (AVD) - aim for 70%+
- Likes/comments ratio
- Subscriber conversion rate

**A/B test:**
- Different titles (first 48 hours)
- Thumbnail variations
- Video length (try 15 min vs 20 min)
- Hook styles

---

## 🔧 Troubleshooting

### Common Issues

**1. Script too short/long**
```bash
# Validate script
python src/content/script_generator.py validate scripts/drafts/your_script.md

# If too short: Ask ChatGPT to expand specific sections
# If too long: Ask ChatGPT to condense
```

**2. Not enough Veo clips**
- Add more `[SHOW: ...]` cues to script
- Regenerate shot list
- Or: Rely more on NASA footage

**3. Video assembly fails**
- Check file paths are correct
- Ensure voiceover file exists
- Check MoviePy is installed: `pip install moviepy`

**4. Render takes too long**
- Normal on M1 for 20-min videos (1-3 hours)
- Run overnight
- Or: Reduce video quality in config.yaml

**5. NASA downloader fails**
- Check internet connection
- NASA API might be slow (retry later)
- Or: Download footage manually from images.nasa.gov

---

## 🚀 Upgrade Path: API Automation

**When to upgrade:** After channel monetization ($100+/month revenue)

### Phase 1: Add APIs ($50-100/month)
1. Add OpenAI API key (script generation)
2. Add Anthropic API (Claude for longer scripts)
3. Automate with browser automation (Playwright)

### Phase 2: Full Automation ($150+/month)
1. Add voice cloning (ElevenLabs - $22/month)
2. Automated thumbnail generation
3. Scheduled uploads
4. Analytics tracking
5. Automated topic research

**ROI:** At $500/month channel revenue, APIs cost 20-30%, save 15+ hours/week

---

## 📞 Support & Resources

### Documentation
- WATOP Style Guide: See script_generator.py
- Veo Best Practices: See veo_generator.py
- NASA API: https://images.nasa.gov/docs

### Community
- r/YouTubeAutomation
- r/ContentCreation
- Space YouTube Creator communities

### Tools Used
- **Veo 3:** Google AI Studio
- **NASA Footage:** images.nasa.gov (free)
- **AI Chat:** ChatGPT/Claude (your Pro accounts)
- **Video Editing:** MoviePy (Python)
- **Thumbnails:** Canva/DALL-E 3

---

## 🎯 Success Metrics

**Month 1 Goals:**
- [ ] 12-15 videos published (3-4/week)
- [ ] 100+ subscribers
- [ ] Consistent upload schedule

**Month 3 Goals:**
- [ ] 50+ videos published
- [ ] 1,000+ subscribers
- [ ] Partner Program eligibility (1000 subs + 4000 watch hours)

**Month 6 Goals:**
- [ ] Monetized channel
- [ ] 10,000+ subscribers
- [ ] $500+/month revenue

**Year 1 Goals:**
- [ ] 100K+ subscribers
- [ ] $2,000+/month revenue
- [ ] Full automation with APIs

---

**Version:** 1.0
**Last Updated:** December 2024
**For questions or improvements, open an issue on GitHub**
