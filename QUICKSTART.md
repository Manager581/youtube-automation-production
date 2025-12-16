# ⚡ Quick Start Guide - Your First Video in 4-6 Hours

This guide will walk you through creating your first space facts video from scratch.

---

## ✅ Prerequisites Check

Before starting, verify you have:

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] ChatGPT Pro or Claude Pro subscription
- [ ] Gemini Pro with Veo 3 access
- [ ] Microphone for voiceover
- [ ] 4-6 hours of time

---

## 🚀 Step 1: Setup (15 minutes)

### Install Dependencies

```bash
cd youtube-automation
pip install -r requirements.txt
```

### Verify Installation

```bash
python src/content/topic_generator.py
```

You should see the help message. If you get errors, check:
- Python version: `python3 --version` (need 3.8+)
- MoviePy installed: `pip list | grep moviepy`

---

## 🎯 Step 2: Choose Your Topic (15 minutes)

### Generate Ideas

```bash
python src/content/topic_generator.py generate 20
```

This creates a prompt file in `prompts/topics/`.

### Get AI Suggestions

1. Open the generated prompt file
2. Copy the entire prompt
3. Paste into ChatGPT-4 or Claude
4. Review the 20 topic suggestions
5. Pick ONE that excites you

**Example topics:**
- "Black Holes That Defy Physics"
- "What If Earth Had Two Moons?"
- "The Darkest Secrets of the Universe"

---

## 📝 Step 3: Generate Script (1-2 hours)

### Create Script Prompt

```bash
python src/content/script_generator.py generate "Your Chosen Topic"
```

**Example:**
```bash
python src/content/script_generator.py generate "Black Holes That Defy Physics"
```

### Get Script from AI

1. Open the prompt file from `prompts/scripts/`
2. Copy the full prompt
3. Paste into **Claude Sonnet** (recommended) or ChatGPT-4
4. Wait 2-5 minutes for full 5,000-word script
5. Save the response as: `scripts/drafts/black_holes_20241216.md`

### Validate Script

```bash
python src/content/script_generator.py validate scripts/drafts/black_holes_20241216.md
```

Check that:
- Word count is ~5,000 words
- Hook is present
- `[SHOW: ...]` cues are throughout
- CTA is at the end

**If validation fails:** Ask the AI to add more visual cues or expand sections.

---

## 🎬 Step 4: Generate Veo Clips (2-3 hours)

### Create Shot List

```bash
python src/production/veo_generator.py generate scripts/drafts/black_holes_20241216.md
```

This creates:
- `prompts/veo_shots/black_holes_20241216_shotlist.json`
- `prompts/veo_shots/black_holes_20241216_shotlist.txt` (human-readable)

### Generate Clips in Veo

1. Open the `_shotlist.txt` file
2. Go to [Google AI Studio](https://aistudio.google.com/)
3. Navigate to Veo 3
4. For each shot in the list:
   - Copy the "VEO PROMPT"
   - Paste into Veo
   - Click Generate (wait ~30-60 seconds per clip)
   - Download the 8-second clip
   - Save as: `assets/veo_clips/black_holes_20241216/veo_clip_001.mp4`
   - Continue with 002, 003, etc.

**Tips:**
- Generate in batches (10-20 at a time)
- Keep naming consistent (001, 002, 003...)
- If a clip fails, regenerate or skip (NASA footage will fill gaps)

**Expected:** 100-150 clips for a 20-minute video

---

## 🚀 Step 5: Download NASA Footage (20 minutes)

### Auto-Download from Script

```bash
python src/production/nasa_downloader.py script scripts/drafts/black_holes_20241216.md
```

**What happens:**
- Analyzes your script for space keywords
- Downloads 20-40 relevant NASA clips
- Saves to `assets/nasa_footage/`
- Takes 10-20 minutes

**Manual alternative (if needed):**
```bash
python src/production/nasa_downloader.py search "black hole, nebula, galaxy" 15
```

---

## 🎙️ Step 6: Record Voiceover (1-2 hours)

### Prepare

1. Open your script: `scripts/drafts/black_holes_20241216.md`
2. Remove the `[SHOW: ...]` and `[MUSIC: ...]` cues (read only the narration)
3. Find a quiet space
4. Test your microphone levels

### Record

**Recommended software:**
- **Mac:** GarageBand (free)
- **Windows:** Audacity (free)
- **Pro:** Adobe Audition

**Recording tips:**
- Pace: ~250 words per minute
- Sound enthusiastic but not over-the-top
- Take breaks every 5 minutes
- Re-record bad sections (edit later)

**Target:** 20 minutes of audio

### Export

Save as:
- Format: MP3 or WAV
- Quality: 192kbps or higher
- Filename: `assets/voiceovers/black_holes_20241216.mp3`

---

## 🎥 Step 7: Assemble Video (15 minutes + render time)

### Run Assembly

```bash
python src/production/video_assembler.py black_holes_20241216 prompts/veo_shots/black_holes_20241216_shotlist.json assets/voiceovers/black_holes_20241216.mp3
```

**What happens:**
- Loads your Veo clips in sequence
- Fills gaps with NASA footage
- Syncs everything to your voiceover
- Adds background music (if available)
- Renders 1080p video

**Wait time:** 1-3 hours (depends on your M1)
- Tip: Run this overnight or while working on other tasks

**Output:** `output/videos/black_holes_20241216_[timestamp].mp4`

---

## 🎨 Step 8: Create Thumbnail (30 minutes)

### Generate Prompt

```bash
python src/distribution/thumbnail_generator.py "Black Holes That Defy Physics"
```

### Create Thumbnail

1. Open the prompt file from `prompts/thumbnails/`
2. Choose DALL-E 3 (in ChatGPT Plus):
   - Copy one of the prompts
   - Paste into ChatGPT
   - Download the generated image
3. Or use Midjourney:
   - Copy the Midjourney prompt
   - Paste in Discord
   - Download result

### Add Text

Use Canva (free):
1. Upload the AI-generated image
2. Add bold white text with black outline
3. Text: "BLACK HOLES THAT DEFY PHYSICS"
4. Resize to 1280x720
5. Download as JPG
6. Save to: `output/thumbnails/black_holes_20241216.jpg`

---

## 📊 Step 9: Generate Metadata (5 minutes)

```bash
python src/distribution/metadata_generator.py "Black Holes That Defy Physics" scripts/drafts/black_holes_20241216.md
```

**Output:**
- `output/metadata/metadata_Black_Holes_20241216.txt`
- Contains: title, description, tags, chapters

---

## 📤 Step 10: Upload to YouTube (15 minutes)

### Manual Upload (Easiest)

1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Click "Upload videos"
3. Select your video: `output/videos/black_holes_20241216_[timestamp].mp4`
4. While uploading:
   - **Title:** Copy from metadata file
   - **Description:** Copy from metadata file (includes chapters)
   - **Thumbnail:** Upload your thumbnail
   - **Tags:** Copy from metadata file
   - **Playlist:** Create "Space Facts" playlist (if first video)
   - **Audience:** Not made for kids
   - **Category:** Science & Technology
5. Set visibility:
   - **Private:** Review first
   - **Public:** Publish immediately
   - **Scheduled:** Pick a time
6. Click "Publish"

### Automated Upload (Optional)

If you set up YouTube API:
```bash
python src/distribution/youtube_uploader.py upload output/videos/your_video.mp4 output/metadata/metadata.json
```

---

## ✅ Final Checklist

Before publishing, verify:

- [ ] Video plays correctly (no audio sync issues)
- [ ] Thumbnail is eye-catching (test on mobile)
- [ ] Title is under 100 characters
- [ ] Description has chapters (timestamps)
- [ ] Tags are relevant
- [ ] End screen elements added (in YouTube Studio)
- [ ] Cards added for other videos

---

## 🎉 Congratulations!

You've created your first automated YouTube video!

### Next Steps:

1. **Promote your video:**
   - Share on relevant Reddit communities (r/space, r/Astronomy)
   - Post on Twitter/X with #SpaceFacts
   - Share in space-related Discord servers

2. **Monitor performance (first 48 hours):**
   - CTR (click-through rate): Aim for 8%+
   - AVD (average view duration): Aim for 14+ minutes
   - Engagement: Respond to comments

3. **Start video #2:**
   - Use what you learned
   - Batch process (generate 3 scripts at once)
   - Get faster with each video

4. **Weekly routine:**
   - Monday: Generate 5 topics, create scripts
   - Tuesday-Wednesday: Generate Veo clips
   - Thursday: Record voiceovers
   - Friday: Assemble and upload

---

## 📈 Optimization Tips

### After Your First Video:

- **A/B test thumbnails:** Upload 2-3 variations, see which performs better
- **Analyze retention:** YouTube Studio → Analytics → Audience retention
  - Find where viewers drop off
  - Improve hooks and re-engagement in future videos
- **Improve pacing:** If retention drops at specific points, edit tighter
- **Engage with comments:** Builds community and signals to algorithm

### After 10 Videos:

- Review which topics performed best
- Double down on winning formats
- Consider voice cloning (once you have consistent style)
- Start planning API automation

---

## 🆘 Troubleshooting

### "Script validation failed"
- **Solution:** Ask AI to add more `[SHOW: ...]` cues throughout script

### "Not enough Veo clips"
- **Solution:** Use more NASA footage, or generate more clips
- **Quick fix:** Reuse clips (they're only 8 seconds each)

### "Video assembly failed"
- **Check:** File paths are correct
- **Check:** Voiceover file exists in correct location
- **Check:** At least some video clips exist (Veo or NASA)

### "Render taking forever"
- **Normal:** 1-3 hours on M1 for 20-min video
- **Speed up:** Lower video quality in `config/config.yaml`
- **Best:** Run overnight

### "NASA downloader not working"
- **Check:** Internet connection
- **Try:** Manual download from images.nasa.gov
- **Alternative:** Use only Veo clips (more work but possible)

---

## 💬 Need Help?

- **Full workflow:** See [WORKFLOW.md](WORKFLOW.md)
- **Troubleshooting:** See WORKFLOW.md
- **GitHub issues:** Open an issue with details

---

## 🚀 Time to Scale

Once you've made 3-5 videos, you'll get much faster:
- Week 1: 6 hours per video
- Week 2: 5 hours per video
- Week 3: 4 hours per video
- Month 2: 3-4 hours per video (batching)

**Goal:** 3-5 videos per week = 15-20 hours total

After monetization, upgrade to APIs and reduce to 5-10 hours per week for same output.

---

**Now go create your first video! 🚀**
