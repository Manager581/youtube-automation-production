# YouTube Automation Production — Master Plan
**Target channel to replicate:** @fern-tv (4.6M subscribers)
**Goal:** Fully automated pipeline that produces new YouTube videos in Fern's exact style, on new topics, using the owner's cloned voice.
**Brand config:** `brand_configs/fern_clone.json`

---

## IMPORTANT OPERATING RULES

- **No paid APIs without explicit approval.** Ask first — always.
- **Script generation:** Use Claude Code (Claude Max subscription = free) interactively. Do NOT run `research_pipeline.py` from code — it calls the Anthropic API directly and costs money.
- **All analysis/generation runs locally** via Ollama (qwen3.5:4b or qwen3.5:27b) or OpenCV — zero cost.
- **watop brand:** Ignore for now. Everything here is Fern-specific unless it's clearly general-purpose infrastructure.

---

## The End-to-End Pipeline

```
[TOPIC RESEARCH]     ← topic_radar.py (Reddit/News/YouTube, free)
       ↓
[COMMENTS MINING]    ← comments_miner.py (yt-dlp, free)
       ↓
[RESEARCH BRIEF]     ← research_brief.py (Wikipedia/RSS, free)
       ↓
[STORY VALIDATION]   ← story_validator.py (local scoring, free)
       ↓
[SCRIPT GENERATION]  ← Claude Code interactively (Claude Max = free)
       ↓
[SCRIPT ENHANCEMENT] ← script_enhancer.py (local Ollama, free)
       ↓
[VOICE NARRATION]    ← voice_generator.py + F5-TTS (local, free)
       ↓
[FOOTAGE SOURCING]   ← footage_sourcer.py (YouTube/Archive, free)
       ↓
[VIDEO ASSEMBLY]     ← video_assembler.py (local ffmpeg/moviepy, free)
       ↓
[PUBLISH]            ← manual upload (YouTube Studio) for now
```

---

## ACTUAL Pipeline Status (as of 2026-03-02)

### Phase 1: Analysis ✅ COMPLETE

All 3 Fern reference videos fully analyzed. All formula files built.

| Script | Output | Status |
|---|---|---|
| `analyze_fern_hybrid_checkpoint.py` | `timeline_hybrid_qwen-vl.json` per video | ✅ Done (1,838 frames) |
| `analyze_fern_motion.py` | `FERN_MOTION_FORMULA.json` | ✅ Done 2026-03-02 |
| `create_master_formula.py` | `FERN_MASTER_FORMULA.json` | ✅ Done 2026-03-02 (1,784 frames) |
| `measure_color_grade.py` | (feeds master formula) | ✅ Done |
| `fingerprint_music.py` | `MUSIC_IDENTITY.json` | ✅ Done |
| `analyze_sound_design.py` | `SOUND_DESIGN_FORMULA.json` | ✅ Done |
| `analyze_fern_sfx.py` | `FERN_SFX_FORMULA.json` | ✅ Done |
| `analyze_fern_text_animation.py` | `FERN_TEXT_ANIMATION_FORMULA.json` | ✅ Done |
| `check_fern_script.py` | `SCRIPT_FORMULA.json` | ✅ Done |
| (manual) | `THUMBNAIL_FORMULA.json` | ✅ Done |
| (manual) | `TITLE_ANGLE_FORMULA.json` | ✅ Done |

**Videos analyzed:** aVA7aXOH1pk (Trump Assassination Attempt), wLFY_Zu_O08 (FBI/KKK, 41 min), wkVygetgeRY (Unabomber, 28 min)

**Known gap — optional motion re-run:**
Current timelines (qwen-vl / Qwen2.5-VL 7B, 2025 model) lack the new dual-frame fields:
`animation_motion`, `animation_easing`, `kinetic_quality`, `subject_motion`, `cut_timestamps`.
As a result, `transition_types` in the motion formula shows all-zeros.
**Fix:** Re-run with `qwen3.5-4b` on M1 overnight — see M1 Setup section.

---

### Phase 2: Research Pipeline ✅ BUILT — ready to run (all free)

| Script | What it does | Cost |
|---|---|---|
| `pipeline/topic_radar.py` | Scans Reddit/Google News/YouTube for viral story candidates scored against Fern's formula | Free (public APIs) |
| `pipeline/comments_miner.py` | Mines YouTube comments for topic signals + audience curiosity gaps. Uses cached `comments.json` for all 3 Fern videos already downloaded. | Free (yt-dlp) |
| `pipeline/research_brief.py` | Wikipedia background + news RSS + footage leads → structured JSON + Markdown brief | Free |
| `pipeline/story_validator.py` | Scores story on 5 dimensions (factual depth, viral hook, arc, visuals, public interest). GO/NEEDS WORK/SKIP verdict. | Free |

**Comments already cached:** `analysis/fern/*/comments.json` exists for all 3 videos.
**Output location:** `research/fern_clone/`

**Full research run:**
```bash
venv/bin/python pipeline/topic_radar.py --brand fern_clone
venv/bin/python pipeline/comments_miner.py --brand fern_clone
venv/bin/python pipeline/research_brief.py --brand fern_clone --query "Your Topic Here"
venv/bin/python pipeline/story_validator.py --query "Your Topic Here" --brand fern_clone
```

---

### Phase 3: Script Generation ✅ READY (via Claude Code — free)

**Do NOT run `research_pipeline.py` from code** — it calls `Anthropic()` API directly = costs money.

**Correct workflow (all free):**
1. Research scripts produce `research/fern_clone/briefs/{topic}.json`
2. Open Claude Code (this terminal — Claude Max subscription)
3. Paste the brief and say: *"Write a full Fern-style script using SCRIPT_FORMULA.json and FERN_MASTER_FORMULA.json"*
4. Claude writes the script interactively — free via Max
5. Save to `scripts/{topic}.txt`

**Key formula stats:**
- Target: ~4,200 words, 25 min @ 138.7 WPM
- Structure: hook (0–30s visceral moment) → context → escalation → revelation → climax → outro
- Sentence rhythm: short declarative → medium explanation → short punchline
- Rhetorical questions every ~45 seconds
- Curiosity gaps: 0.43/min (always close one, open another)
- Chapter breaks: use `[PAUSE:5.0]` in script at chapter markers

---

### Phase 4: Script Enhancement ✅ BUILT — free, local Ollama

Transforms raw script into narration-ready format: emotion markers, strategic pauses, 138.7 WPM pacing.

```bash
venv/bin/python pipeline/script_enhancer.py \
  --input scripts/raw_topic.txt \
  --output scripts/enhanced_topic.txt
```

Adds: `[BEAT]` (0.3s), `[PAUSE:1.2]`, `[BREATH]` (0.15s), `[VOICE:tense/neutral/energized]` markers.
Uses Ollama locally (recommend `qwen2.5:32b` on M5, or `qwen3.5:27b` if installed).

---

### Phase 5: Voice Cloning + Narration ✅ BUILT — free, local (F5-TTS v1.1.16)

**BLOCKER: Voice reference clips not yet recorded.**

Record yourself in 3 emotional registers, 15–30 seconds each, quiet room, no background noise:
- `assets/voice/voice_neutral.wav` — measured, documentary tone (like reading a calm news report)
- `assets/voice/voice_tense.wav` — tight, urgent, something bad is coming
- `assets/voice/voice_energized.wav` — revelation, heightened energy, key moments

**Step 1: Clean recordings**
```bash
venv/bin/python pipeline/audio_preprocessor.py \
  --input my_raw_recording.wav \
  --output assets/voice/voice_neutral.wav \
  --report
```
Applies: 80Hz high-pass filter, noise reduction, loudness normalization to -23 LUFS, resample to 24kHz.

**Step 2: Generate narration**
```bash
venv/bin/python pipeline/voice_generator.py \
  --ref-neutral   assets/voice/voice_neutral.wav \
  --ref-tense     assets/voice/voice_tense.wav \
  --ref-energized assets/voice/voice_energized.wav \
  --auto-transcribe \
  --script scripts/enhanced_topic.txt \
  --out audio/topic/narration.wav
```
Output: `narration.wav` + word-level timestamps for video sync.

---

### Phase 6: Audio Mix ❌ NOT YET BUILT

`mix_audio.py` does not exist. `video_assembler.py` handles inline narration+music mixing, but a standalone audio mix script (SFX layering, ducking, compression) hasn't been built.

**SFX already available in `assets/sfx/`:**
`rumble_01–03.mp3`, `impact_01–02.mp3`, `tension_01.mp3`, `shimmer_01–03.mp3`, `whoosh_01–05.mp3`

**Fern's audio formula:**
- Music: 116 BPM, dark cinematic, piano + strings
- Music level: -18 dB under narration (sidechaining)
- SFX on every major revelation/cut hit
- Ambient bed: ~60% of runtime

**When building:** Use `pydub` or `ffmpeg` Python wrapper. Reference `SOUND_DESIGN_FORMULA.json` + `FERN_SFX_FORMULA.json`.

---

### Phase 7: Video Assembly ✅ BUILT — free, local

**Source footage first:**
```bash
venv/bin/python pipeline/footage_sourcer.py \
  --brand fern_clone \
  --brief research/fern_clone/briefs/topic.json \
  --out footage/fern_clone/topic/
```
Sources from Reuters, AP Archive, BBC News, Internet Archive (all free).

**Assemble video:**
```bash
venv/bin/python pipeline/video_assembler.py \
  --brand fern_clone \
  --narration audio/topic/narration_manifest.json \
  --footage footage/fern_clone/topic/manifest.json \
  --music assets/music/track.mp3 \
  --out output/topic/final.mp4 \
  [--dry-run]   # preview timeline without rendering
```

**Production constants (from Fern analysis, hardcoded):**
- Ken Burns: 5%/sec zoom, 40% zoom-in / 25% zoom-out / 26% static
- Color grade: 0.46× saturation, 7% black crush, 0.90 gamma
- Cuts: content-driven, avg 4–6s per segment
- Text: slide_reveal 511ms, held ~9s
- Chapter cards: white serif typewriter text on black

---

### Phase 8: Thumbnail + Title ❌ NOT YET BUILT as scripts

**Title (use Claude Code — free):**
Paste `TITLE_ANGLE_FORMULA.json` + video topic into Claude Code, ask for 3 title options ranked by formula score.

**Top title patterns by performance:**
1. `How [Institution] [Shocking Action]` — avg 11.2M views
2. `[Country]'s [Most/Hidden] [Dark Reality]` — avg 5.6M views
3. `The [Person] Who [Achievement] (and [Dark Consequence])` — avg 4.2M views

**Thumbnail (manual for now):** Follow `THUMBNAIL_FORMULA.json`. Ask before using DALL-E 3 or any paid image API.

---

### Phase 9: Publish ○ MANUAL FOR NOW

Manual upload via YouTube Studio is sufficient. `publish_video.py` (YouTube Data API v3) can be built when volume warrants it.

---

## Current State Summary

```
ANALYSIS:    ██████████  100% (optional re-run for animation motion fields)
RESEARCH:    ██████████  100% (all scripts built + comments cached)
SCRIPT GEN:  ████████░░   80% (Claude Code interactive = free, no standalone script)
VOICE:       ████████░░   80% (F5-TTS fully built — needs your voice recordings)
AUDIO MIX:   ░░░░░░░░░░    0% (mix_audio.py not built; assembler handles basic mix)
VIDEO:       ██████████  100% (footage_sourcer + video_assembler built)
THUMBNAIL:   ░░░░░░░░░░    0% (use Claude Code + manual, no script yet)
PUBLISH:     ██████████  100% (manual upload works fine)
```

**Next actions to produce the first video:**
1. `python pipeline/topic_radar.py --brand fern_clone`
2. `python pipeline/comments_miner.py --brand fern_clone`
3. `python pipeline/research_brief.py --brand fern_clone --query "{chosen topic}"`
4. `python pipeline/story_validator.py --query "{chosen topic}" --brand fern_clone`
5. Claude Code: write script from brief (reference SCRIPT_FORMULA.json + FERN_MASTER_FORMULA.json)
6. `python pipeline/script_enhancer.py --input scripts/raw.txt --output scripts/enhanced.txt`
7. Record voice clips → `audio_preprocessor.py` → `voice_generator.py`
8. `python pipeline/footage_sourcer.py --brief research/...`
9. `python pipeline/video_assembler.py --narration ... --footage ... --music ... --out output/final.mp4`
10. Manual upload to YouTube

---

## M1 Setup — Overnight Re-Analysis with Qwen3.5

Re-run visual classification with the newer Qwen3.5 model to get the new fields (`animation_motion`, `animation_easing`, `kinetic_quality`, `subject_motion`, `cut_timestamps`, better `transition_types`). Run on M1 (16GB) so M5 stays free.

**One-time M1 setup:**
```bash
# 1. Enable on M1: System Settings → General → Sharing → Remote Login → ON
# 2. From M5 terminal:
ssh yourname@m1.local

# 3. On M1 — install Ollama (if not already): https://ollama.com/download
# 4. Pull the model (3.4GB — fits on 16GB M1 with 12GB headroom)
ollama pull qwen3.5:4b

# 5. Sync code from M5 (git push from M5 first, then on M1):
cd ~/Documents/youtube-automation-production
git pull

# 6. Reset checkpoint
python3 -c "
import json, shutil
cp = json.load(open('analysis/fern/.checkpoint.json'))
shutil.copy('analysis/fern/.checkpoint.json', 'analysis/fern/.checkpoint.json.backup')
cp['current_video_index'] = 0
cp['current_frame_index'] = 0
json.dump(cp, open('analysis/fern/.checkpoint.json', 'w'), indent=2)
print('Reset. Ready.')
"

# 7. Run overnight (nohup survives SSH disconnect)
nohup venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-4b \
  > /tmp/fern_analysis.log 2>&1 &
echo "Running. PID: $!"

# 8. Monitor from M5 (leave this running in a tab)
ssh yourname@m1.local "tail -f /tmp/fern_analysis.log"

# 9. After completion, copy timelines back to M5
scp yourname@m1.local:'~/Documents/youtube-automation-production/analysis/fern/*/timeline_hybrid_qwen3.5-4b.json' .
# Then rebuild master formula on M5:
venv/bin/python create_master_formula.py
```

**Why qwen3.5:4b is better than the current qwen2.5vl:7b:**
- Newer architecture released Feb 2026 — outperforms Qwen3-VL on visual tasks
- Supports vision (images) natively in the unified model
- Same ~3-4GB size, similar speed, better accuracy

---

## Live Monitor

```bash
# Terminal 1 — run analysis, stream to log
venv/bin/python analyze_fern_hybrid_checkpoint.py --all --model qwen3.5-4b 2>&1 | tee /tmp/fern_analysis.log

# Terminal 2 — live dashboard (shows analysis + full pipeline status + formula files)
venv/bin/python monitor.py
```

---

## Key Files Reference

| File | Purpose |
|---|---|
| `MASTER_PLAN.md` | This file — read first after reconnects |
| `brand_configs/fern_clone.json` | Brand identity, topic filters, title formulas |
| `analysis/fern/FERN_MASTER_FORMULA.json` | THE formula — feeds all generation scripts |
| `analysis/fern/FERN_MOTION_FORMULA.json` | Camera + optical flow + transitions |
| `analysis/fern/SCRIPT_FORMULA.json` | Script writing rules |
| `analysis/fern/MUSIC_IDENTITY.json` | Music selection + BPM (116 BPM, dark cinematic) |
| `analysis/fern/SOUND_DESIGN_FORMULA.json` | SFX + ambient spec |
| `analysis/fern/THUMBNAIL_FORMULA.json` | Thumbnail composition rules |
| `analysis/fern/TITLE_ANGLE_FORMULA.json` | Title patterns ranked by view performance |
| `analysis/fern/FERN_STYLE_GROUND_TRUTH.json` | Ground truth style reference |
| `monitor.py` | Live pipeline dashboard (run in second terminal) |
| `research_pipeline.py` | ⚠️ USES PAID API — do not run; use Claude Code instead |

---

*Last updated: 2026-03-02*
*Videos analyzed: aVA7aXOH1pk (Trump), wLFY_Zu_O08 (FBI/KKK), wkVygetgeRY (Unabomber) — 3 total, 1,838 frames*
*Models: qwen3.5:4b and qwen3.5:27b added to analyze_fern_hybrid_checkpoint.py (pull with `ollama pull qwen3.5:4b`)*
