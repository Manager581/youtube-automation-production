# Fern-Clone YouTube Automation Pipeline

Automated production pipeline that replicates the style of **@fern-tv** (4.6M subscribers) — dark, archival, documentary-style long-form YouTube videos — using your own cloned voice on new topics.

**Target:** 22–27 min videos at 138.7 WPM with Ken Burns + color grade + chapter cards, fully assembled locally at zero cost.

---

## Prerequisites

### System dependencies

```bash
# macOS
brew install ffmpeg ffprobe yt-dlp
```

- **Python 3.13** (the venv is already at `venv/`)
- **Ollama** — [install from ollama.com](https://ollama.com) — runs local AI models
- **F5-TTS** v1.1.16 — local voice cloning (see Voice section below)

### Ollama models

```bash
# Primary text model — storyboard generation, script enhancement
# M5 24GB: use 27b (17GB, fits fine, much better output quality)
ollama pull qwen3.5:27b         # 17 GB — recommended for M5 24GB

# Fallback text model (if 27b is too slow for you)
# ollama pull qwen3.5:4b        # 3.4 GB — faster but lower quality output

# Already installed — vision tasks (footage verification, focal points)
# qwen2.5vl:7b                  # 6 GB — already pulled, correct tool for vision
```

> **Note:** `qwen3.5:27b` is NOT yet installed. Run `ollama pull qwen3.5:27b` (17GB download). The pipeline falls back to `qwen3.5:4b` → `qwen2.5vl:7b` if 27b isn't available, but storyboard quality will be noticeably lower.

### Python dependencies

```bash
# Activate the venv (already set up)
source venv/bin/activate

# If starting fresh
pip install -r requirements.txt
# Also needed (not in requirements.txt yet):
pip install librosa soundfile
```

---

## One-Command Run

```bash
python run_pipeline.py
```

This runs the entire pipeline interactively. It stops at 4 human decision points and runs everything else automatically.

```bash
python run_pipeline.py --list       # show all stages
python run_pipeline.py --status     # show current progress
python run_pipeline.py --from voice # resume from a specific stage
python run_pipeline.py --reset      # start over
```

State is saved in `.pipeline_run.json` — Ctrl+C at any point and resume later.

---

## Manual Stage-by-Stage

If you prefer to run stages individually:

### 1. Topic Research

```bash
venv/bin/python pipeline/topic_radar.py --brand fern_clone
venv/bin/python pipeline/comments_miner.py --brand fern_clone
```

Scans Reddit, Google News, YouTube for viral story candidates. Auto-checks Fern overlap (won't suggest topics Fern already covered). Output: `research/fern_clone/` directory.

**Human decision: pick a topic.** High viral score + low Fern overlap = best bet.

### 2. Research Brief

```bash
venv/bin/python pipeline/research_brief.py --brand fern_clone --query "Your Topic Here"
venv/bin/python pipeline/story_validator.py --query "Your Topic Here" --brand fern_clone
```

Generates Wikipedia background + news RSS brief. Scores story on 5 dimensions (factual depth, viral hook, narrative arc, visual assets, public interest). Must be GO or NEEDS WORK to continue.

### 3. Script Generation

**Use Claude Code interactively — do NOT run `research_pipeline.py` from code (calls paid API).**

```
1. Open a new Claude Code session
2. Paste contents of research/fern_clone/briefs/{topic}.json
3. Say: "Write a full Fern-style script using SCRIPT_FORMULA.json and FERN_MASTER_FORMULA.json"
4. Save output to scripts/{topic}.txt
```

Target: ~4,200 words / 25 min at 138.7 WPM. Use `[PAUSE:5.0]` markers at chapter breaks.

### 4. Script Enhancement + QA

```bash
venv/bin/python pipeline/script_enhancer.py \
  --input scripts/{topic}.txt \
  --output scripts/enhanced_{topic}.txt

venv/bin/python check_fern_script.py scripts/enhanced_{topic}.txt
```

Adds `[BEAT]`, `[PAUSE:1.2]`, `[BREATH]`, `[VOICE:tense/neutral/energized]` markers. Script must score **85+** before proceeding to voice.

### 5. Storyboard Generation

```bash
venv/bin/python pipeline/storyboard_generator.py \
  --script scripts/enhanced_{topic}.txt \
  --out storyboards/{topic}.json
```

Generates per-segment visual brief: what to show, exact footage search query, focal element, shot type, intensity. Story-drives all downstream choices. Uses `qwen3.5:4b` locally.

### 6. Voice Narration

```bash
venv/bin/python pipeline/voice_generator.py \
  --ref-neutral   assets/voice/voice_neutral_ref.wav \
  --ref-tense     assets/voice/voice_tense_ref.wav \
  --ref-energized assets/voice/voice_energized_ref.wav \
  --auto-transcribe \
  --script scripts/enhanced_{topic}.txt \
  --out audio/{topic}/narration.wav
```

Uses F5-TTS v1.1.16 locally. Reference clips must be exactly 10s (trimmed `*_ref.wav` files).

**Voice QA (automatic — no listening required):**

```bash
venv/bin/python check_fern_voice.py audio/{topic}/narration.wav \
  --manifest audio/{topic}/narration_manifest.json
```

Checks: LUFS (-20 to -16 target), WPM (138.7 target), silence ratio, peak clipping. PASS/WARN = auto-proceed. FAIL = regenerate.

### 7. Music

```bash
venv/bin/python pipeline/music_sourcer.py --script scripts/enhanced_{topic}.txt
# Downloads to assets/music/track.mp3
```

Analyzes script mood, downloads a free CC0 track. Requires `PIXABAY_API_KEY` env var (free — register at pixabay.com/api).

### 8. Footage Sourcing

```bash
venv/bin/python pipeline/footage_sourcer.py \
  --brand fern_clone \
  --brief research/fern_clone/briefs/{topic}.json \
  --storyboard storyboards/{topic}.json \
  --download \
  --out footage/fern_clone/{topic}/
```

Sources from YouTube (yt-dlp), Internet Archive, Wikimedia Commons. Storyboard drives targeted search queries per segment. Each clip is tagged with storyboard segment IDs.

**Footage QA (automatic):**

```bash
venv/bin/python pipeline/footage_verifier.py \
  --manifest footage/fern_clone/{topic}/manifest.json
```

Vision model scores each item vs storyboard description. Removes unrelated items (<0.10 score). ≥60% coverage = auto-proceed. <40% = asks for override.

**Find pivotal moments in downloaded clips (optional but recommended):**

```bash
venv/bin/python pipeline/clip_analyzer.py manifest \
  --manifest footage/fern_clone/{topic}/manifest.json
```

Scores each 5s window in every clip against the storyboard description. Saves `clip_start_sec` to manifest — assembler uses the best moment instead of position 0.

### 9. Video Assembly

```bash
venv/bin/python pipeline/video_assembler.py \
  --brand fern_clone \
  --narration audio/{topic}/narration_manifest.json \
  --footage footage/fern_clone/{topic}/manifest.json \
  --music assets/music/track.mp3 \
  --storyboard storyboards/{topic}.json \
  --out output/{topic}/final.mp4
```

Produces: Ken Burns stills, color-graded clips, chapter cards, lower-thirds, beat-synced cuts, text overlays, narration + music mix. Saves `output/{topic}/timeline.json` alongside.

Optional flags:
- `--focal-points` — enable vision model focal point detection (needs Ollama running)
- `--dry-run` — preview timeline without rendering
- `--no-beat-sync` — disable beat-snap

### 10. Final QA

```bash
venv/bin/python check_fern_video.py output/{topic}/final.mp4
```

8 checks: duration (22–27 min), cut rate (11.3/min target), audio levels (-14 to -18 LUFS), color grade, A/V sync, chapter cards (≥5), footage variety, beat sync (~39%). Must PASS or WARN before upload.

### 11. Thumbnail + Title

**Title:** Paste `TITLE_ANGLE_FORMULA.json` + topic into Claude Code — ask for 3 options ranked by formula score.

**Thumbnail:** Follow `THUMBNAIL_FORMULA.json` manually (no script — no volume to justify automation yet).

### 12. Upload

Manual via YouTube Studio.

---

## Voice Reference Clips Setup

If voice reference files are missing or need replacement:

```bash
# Record yourself reading a few sentences in neutral/tense/energized tone
# Then clean and normalize:
venv/bin/python pipeline/audio_preprocessor.py \
  --input my_raw_recording.wav \
  --output assets/voice/voice_neutral.wav \
  --report

# Trim to exactly 10s reference clip (F5-TTS clips anything >12s → bad output):
ffmpeg -ss 0 -t 10 -i assets/voice/voice_neutral.wav assets/voice/voice_neutral_ref.wav
```

Required files in `assets/voice/`:
- `voice_neutral_ref.wav` (10s)
- `voice_tense_ref.wav` (10s)
- `voice_energized_ref.wav` (10s)

---

## F5-TTS Installation

```bash
# F5-TTS v1.1.16 (exact version — other versions have speed issues)
pip install f5-tts==1.1.16

# Verify
python -c "from f5_tts.api import F5TTS; print('OK')"
```

---

## Environment Variables

```bash
# Required for music sourcing
export PIXABAY_API_KEY="your_key_here"   # free at pixabay.com/api

# Optional — only if using paid APIs (not needed for this pipeline)
# export ANTHROPIC_API_KEY="..."
```

---

## Project Structure

```
youtube-automation-production/
├── pipeline/                    # All automation scripts
│   ├── topic_radar.py           # Find viral story candidates
│   ├── comments_miner.py        # Mine Fern comments for signals
│   ├── research_brief.py        # Wikipedia + RSS brief
│   ├── story_validator.py       # GO/SKIP verdict (5-dim scoring)
│   ├── script_enhancer.py       # Add emotion/pause/breath markers
│   ├── storyboard_generator.py  # Per-segment visual brief (story-driven)
│   ├── voice_generator.py       # F5-TTS narration generation
│   ├── audio_preprocessor.py    # Clean + normalize voice recordings
│   ├── music_sourcer.py         # CC0 music download (Pixabay)
│   ├── footage_sourcer.py       # Download footage (yt-dlp, Archive, Wikimedia)
│   ├── footage_verifier.py      # Vision model scores footage vs storyboard
│   ├── clip_analyzer.py         # Find pivotal moment in downloaded clips
│   ├── animation_generator.py   # Generate doc/map/person cards (Pillow)
│   └── video_assembler.py       # Full video assembly (ffmpeg + moviepy)
├── check_fern_script.py         # Script QA gate (must score 85+)
├── check_fern_voice.py          # Voice QA gate (LUFS, WPM, silence, clipping)
├── check_fern_video.py          # Final video QA gate (8 checks vs Fern benchmarks)
├── run_pipeline.py              # Single-command interactive pipeline runner
├── monitor.py                   # Live dashboard (run in second terminal)
├── brand_configs/
│   └── fern_clone.json          # Brand identity, topic filters, title formulas
├── analysis/fern/               # All analyzed Fern data
│   ├── FERN_MASTER_FORMULA.json # The formula — feeds all generation scripts
│   ├── SCRIPT_FORMULA.json      # Script writing rules (4,200 words, 25 min)
│   ├── FERN_MOTION_FORMULA.json # Camera motion + transition spec
│   ├── MUSIC_IDENTITY.json      # Music selection + BPM (116 BPM)
│   ├── SOUND_DESIGN_FORMULA.json
│   ├── THUMBNAIL_FORMULA.json
│   ├── TITLE_ANGLE_FORMULA.json
│   └── {video_id}/              # Per-video analysis data
├── scripts/                     # Raw and enhanced scripts
├── storyboards/                 # Per-topic visual storyboards
├── audio/                       # Narration audio + manifests
├── footage/                     # Downloaded footage + manifests
├── assets/
│   ├── voice/                   # Voice reference clips (10s each)
│   ├── music/                   # Background music tracks
│   └── sfx/                     # Sound effects
├── output/                      # Final rendered videos + timelines
└── research/fern_clone/         # Research briefs + topic signals
```

---

## Cost

**Everything is free.** No paid APIs are used.

| Component | Tool | Cost |
|---|---|---|
| Topic/research | topic_radar + Reddit/RSS | $0 |
| Script | Claude Code (Claude Max sub) | $0 |
| Script enhancement | Ollama qwen3.5:4b local | $0 |
| Voice | F5-TTS local | $0 |
| Footage | yt-dlp + Internet Archive | $0 |
| Music | Pixabay CC0 (free API) | $0 |
| Video assembly | ffmpeg + moviepy | $0 |
| AI scoring | Ollama local | $0 |

> One exception: `research_pipeline.py` calls the Anthropic API directly — **do not run this from code.** Use Claude Code interactively instead.

---

## Key Formula Stats (measured from Fern)

- Script: ~4,200 words, 25 min @ **138.7 WPM**
- Color grade: 0.46× saturation, 7% black crush, 0.90 gamma
- Ken Burns: 5%/sec zoom rate (modulated by storyboard intensity)
- Cut rate: **11.3 cuts/min** avg (content-driven, 4–6s per segment)
- Music BPM: **116 BPM** (dark cinematic)
- Beat sync: ~39% of cuts land within ±100ms of a beat
- Chapter cards: ~5 per video (white serif typewriter on black)
- SFX: minimal (10.9% of cuts) — impact_thud dominant

---

## Troubleshooting

**Ollama not running:**
```bash
ollama serve   # start in background
ollama list    # verify models
```

**F5-TTS speed issues:** Make sure reference clips are exactly 10s. F5-TTS clips anything >12s which causes erratic speed output.

**Footage sourcing hangs:** Each search has a 20s timeout built in. If it's still hanging, check `yt-dlp` version: `yt-dlp --update`

**Black screens in output:** Shouldn't happen — `animation_generator.py` auto-generates text/doc/map cards for segments with no footage. If you see black, check that `needs_animation` segments have a valid `storyboard_show` description in the storyboard JSON.

**WPM check shows SKIP:** The narration manifest `segments` field may be empty. Check `audio/{topic}/narration_manifest.json` — it should have a `segments` list with `start_sec`, `end_sec`, `text` fields.

---

See [MASTER_PLAN.md](MASTER_PLAN.md) for complete pipeline status, formula details, and architectural notes.
