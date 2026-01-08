# 🔬 RUNNING COMPLETE ANALYSIS - QUICK GUIDE

This guide shows you how to run the complete WATOP formula extraction.

---

## ✅ WHAT YOU HAVE

Based on your system:
- ✅ Virtual environment set up
- ✅ Analysis directory with existing data: `analysis/watop/` (416 items)
- ✅ Video files in: `/Users/jefflawrence/Documents/YouTube Automation Master Process/data/entertainment/long/`

---

## 🚀 QUICK START

### **Step 1: Check What Analysis Data Already Exists**

```bash
python src/check_analysis_status.py watop
```

This will show you:
- How many transcripts you have
- How many videos have been analyzed
- Whether the formula has been extracted
- What to do next

### **Step 2: Run Complete Analysis**

If you have existing transcripts, you can jump straight to master analysis:

```bash
python src/master_formula_extractor.py watop
```

The script will:
- ✅ Auto-detect your existing `analysis/watop/` directory
- ✅ Look for videos in your Documents folder automatically
- ✅ Run all 5 deep analysis phases (curiosity gaps, audio sync, interviews, emotions, cuts)
- ✅ Extract complete formula
- ✅ Generate `FORMULA_SOP.md`

**OR** specify the video directory explicitly:

```bash
python src/master_formula_extractor.py watop "/Users/jefflawrence/Documents/YouTube Automation Master Process/data/entertainment/long/"
```

---

## 📊 WHAT THE ANALYSIS DOES

The master extractor runs **5 deep analysis phases** on each video:

### **Phase 2A: Curiosity Gap Detection**
- Finds when questions are posed
- Tracks how long until they're answered
- Identifies tension-building patterns

### **Phase 2B: Audio-Visual Sync**
- Analyzes music BPM and energy
- Measures voice pacing (words per minute)
- Detects when music swells align with reveals

### **Phase 2C: Interview Pattern Extraction**
- Finds face-to-camera vs interview segments
- Tracks when interviews are used
- Identifies purpose (credibility, explanation, emotion)

### **Phase 2D: Emotional Arc Mapping**
- Combines script sentiment + audio energy + visual pacing
- Maps emotional intensity over time
- Identifies arc shape (crescendo, wave, plateau)

### **Phase 2E: Cut Purpose Analysis**
- Analyzes WHY each cut was made
- Categories: scene change, emphasis, pacing, question/answer
- Measures average shot duration

---

## ⏱️ HOW LONG DOES IT TAKE?

- **Per video**: 5-10 minutes
- **150 videos**: ~12-20 hours

**💡 Tip**: Start with a smaller batch to test:

```bash
# Create a test directory with just 5 videos
mkdir -p test_videos
cp "/Users/jefflawrence/Documents/YouTube Automation Master Process/data/entertainment/long/"*.mp4 test_videos/ | head -5

# Run analysis on test batch
python src/master_formula_extractor.py watop test_videos/
```

---

## 📁 OUTPUT FILES

After analysis completes, you'll get:

```
analysis/watop/
├── complete_formula.json       # Complete data (all phases)
├── FORMULA_SOP.md             # Human-readable formula
├── VIDEO_ID_transcript.json   # Transcripts
├── VIDEO_ID_visual.json       # Visual analysis
├── VIDEO_ID_curiosity.json    # Curiosity gaps
├── VIDEO_ID_audio.json        # Audio analysis
├── VIDEO_ID_interviews.json   # Interview patterns
├── VIDEO_ID_emotions.json     # Emotional arcs
└── VIDEO_ID_cuts.json         # Cut purposes
```

**Most important file**: `FORMULA_SOP.md` - This is your actionable playbook!

---

## 🐛 TROUBLESHOOTING

### **"ModuleNotFoundError"**
Install missing dependencies:
```bash
pip install librosa soundfile textblob opencv-python scipy
```

### **"Video directory not found"**
Specify the full path explicitly:
```bash
python src/master_formula_extractor.py watop "/full/path/to/videos/"
```

### **Analysis fails on specific video**
The script continues even if individual phases fail. Check the error message and:
- Ensure video file is not corrupted
- Check that transcript exists for the video
- Verify dependencies are installed

### **Takes too long**
- Start with smaller batch (5-10 videos)
- Run overnight for large batches
- Consider using just the videos with highest views

---

## 💡 TIPS

### **Prioritize Top Videos**
You don't need to analyze ALL videos. Focus on:
- Top 10 most-viewed videos
- Videos that match your target style
- Recent videos (last 6 months)

### **Check Existing Data First**
You might already have partial analysis from a previous session:
```bash
ls -la analysis/watop/
```

If you have transcripts, the master extractor can use them!

### **Run in Background**
For large batches, run in background:
```bash
nohup python src/master_formula_extractor.py watop > analysis_log.txt 2>&1 &
```

Check progress:
```bash
tail -f analysis_log.txt
```

---

## 🎯 AFTER ANALYSIS

Once you have `FORMULA_SOP.md`, you can:

1. **Read the formula** - Understand exactly what WATOP does
2. **Apply to your content** - Use the SOP as a template
3. **Build automation** (Phase 4) - Script → Video pipeline

---

## ❓ QUICK REFERENCE

```bash
# Check status
python src/check_analysis_status.py watop

# Run analysis (auto-detect videos)
python src/master_formula_extractor.py watop

# Run analysis (specific directory)
python src/master_formula_extractor.py watop "/path/to/videos/"

# View results
cat analysis/watop/FORMULA_SOP.md

# Check what's in analysis folder
ls -la analysis/watop/ | grep json | wc -l
```

---

**Ready to extract the formula? Start with Step 1! 🚀**
