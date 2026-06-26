# ORCHESTRATION — how the episode actually gets built
## ⚠️ CORRECTED 2026-06-22 — engine is GROK, not Veo (per the channel owner directly)

**Confirmed pipeline (owner's own words):**
1. He makes **~80 still images first** (photoreal zoo frames). The realism lives in the stills.
2. He **animates each still in Grok Imagine** (image-to-video, native audio) → **6-second / 720p / 24fps** clips. 80 × 6s ≈ 8 min.
3. **He explicitly rejected Veo 3** — "doesn't look real." (Veo is t2v; animating his own hyper-real stills looks more real.)
4. **Voiceover = INTRO ONLY.** All other speech ("dialogues") is generated **natively by Grok** inside each clip (Grok Imagine 1.5 does synced multi-character dialogue + SFX + ambience in one pass).
5. **Sound:** keeps Grok's native audio, then **manually layers ambient SFX from Pixabay** (birds, nature, crowd murmur) "to look more real." Music = Kevin MacLeod (CC, from the description).
6. **No formal storyboard.** Loose plan: intro must trigger curiosity (1–1.5s flash of the finale creature); order creatures by fame/most-searched; the headline dino (T-Rex / Indominus / Distortus-Rex) goes **last** to hold curiosity.
7. Finish: stills are 720p/24 → **upscale + interpolate to 4K/60** (tool unconfirmed; Topaz-class). Assemble in an editor; add logo bug; publish with synthetic-content disclosure.

**Tools (owner, all confirmed 2026-06-22):** **stills = mostly Gemini or ChatGPT** (from a **reusable prompt list**); **Grok Imagine = the animator (i2v, 6s)**; **edited in CapCut (basic/free plan)** — likely also the 4K/60 export. Intro = **10–20 fast cuts in ~20s**, then opens at the **park entrance**. Time: **~2 days focused, ~1 week now** (Grok rate-limited + he's also studying). Cost driver = Grok limits + manual labor, not API fees. **He offered to mentor Jeff through a first build.**

---

## Per-shot, you now write TWO prompts (not one)
For each of the ~80 shots:
- **(A) IMAGE prompt** → make the still. = `STYLE_KIT + character-locks-present + SHOT on-screen/delta`. Tool: GPT-Image / Imagen / Grok. Pick the best still (curate here — the still decides realism).
- **(B) GROK animation prompt** → feed that still to Grok Imagine i2v. = `camera move + action + "<Character> says: '<line>'" (for in-clip dialogue) + audio/sfx note`. Out: 6s/720p clip with native audio.
- The existing `PRODUCTION_BIBLE.md` shot list already gives you both: its `P:`/delta = the **image** prompt; its CAM + action + the **(N)** lines + 🔊 = the **Grok** prompt. **Correction:** lines I tagged `(VO)` in the *body* are actually Grok-native — fold them into prompt (B). Only the **intro** VO (≈S06–S08) is a separate recorded track.

## Folder layout
```
episode_01_omega_rex/
  shots.json  style.txt  characters.txt
  stills/      S01.png …          # ~80 generated stills (the realism step)
  gen/         S01_take1.mp4 …     # Grok i2v takes (6s/720p)
  approved/    S01.mp4 …           # one curated clip per shot
  audio/  intro_vo.wav  music.mp3  sfx/ (pixabay: birds.wav crowd.wav …)
  work/  timeline.txt   out/  episode_raw.mp4  episode_4k60.mp4
  publish/  title.txt description.txt tags.txt thumbnail.png
```

## STAGES
**1 · Plan (loose).** Script/idea in ChatGPT/Gemini/Grok. Intro = curiosity hook + 1–1.5s flashes of the finale dino. Creatures ordered by fame; hero last.
**2 · Stills (~80).** For each shot: `STYLE_KIT + char locks + delta` → GPT-Image / Imagen / Grok. Curate the still (this is where realism is won). → `stills/Sxx.png`.
**3 · Animate in Grok Imagine (i2v).** Upload each still + the Grok prompt (camera + action + dialogue + audio) → 6s/720p clip with native audio. Reroll bad ones. → `approved/Sxx.mp4`.
**4 · Intro VO only.** Record/generate the intro voiceover (one short track). The body needs no VO — Grok speaks.
**5 · Assemble (editor or ffmpeg).** Hard-cut clips in order; KEEP Grok-native audio; layer **Pixabay ambience** (birds/crowd/nature) for realism; add Kevin MacLeod music bed (duck under intro VO); burn DINOVERSE logo bug. → `episode_raw.mp4`.
```bash
# concat (keeps each clip's native Grok audio), then add ambience + music:
ffmpeg -f concat -safe 0 -i work/timeline.txt -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac work/cut.mp4
ffmpeg -i work/cut.mp4 -i audio/sfx/crowd.wav -i audio/sfx/birds.wav -i audio/music.mp3 \
 -filter_complex "[1]volume=0.3[a1];[2]volume=0.25[a2];[3]volume=0.18[m];\
   [0:a][a1][a2][m]amix=inputs=4:duration=longest:normalize=0[mix]" \
 -map 0:v -map "[mix]" -c:v copy -c:a aac out/with_audio.mp4
ffmpeg -i out/with_audio.mp4 -i assets/dinoverse_bug.png -filter_complex "overlay=W-w-34:H-h-30" -c:a copy out/episode_raw.mp4
```
**6 · Finish: 720p/24 → 4K/60.** Big upscale (Grok is 720p). Topaz Video AI, or free RIFE (→60fps) + Real-ESRGAN (→4K), or ffmpeg fallback:
```bash
ffmpeg -i out/episode_raw.mp4 -vf "minterpolate=fps=60:mi_mode=mci,scale=3840:2160:flags=lanczos" -c:v libx264 -crf 16 -c:a copy out/episode_4k60.mp4
```
**7 · Publish.** Title + chaptered description + Kevin MacLeod credit + **synthetic-content disclosure**; no-text "two-apex face-off" thumbnail.

## OPEN QUESTIONS worth asking the owner (to close the last gaps)
- Which tool makes the **stills** (GPT-Image? Imagen? Grok?) — and how does he keep the **same zoo + same ranger** consistent across 80 separate stills?
- How many **Grok rerolls** per usable clip (the curation ratio)?
- What does he use to **upscale 720p → 4K/60**?
- What's the **intro VO** tool (his voice? a TTS?)?
- How long does one video take, and what's the second channel? (he hadn't answered yet)
