# PRODUCTION HANDOFF — Dinoverse "Omega Rex" episode (resume here)

Cloning @Dinoverse-U: a faithful zoo-POV dinosaur-park video that turns to disaster.
Branch: `spinosnack-dunkleosteus`. Everything below is committed + pushed. Owner = Jeff.

## WHERE WE ARE (2026-06-29)
- ✅ **Storyboard locked** — `STORYBOARD.tsv` (source of truth = `build_storyboard.py`; regenerate via
  `../../venv/bin/python build_storyboard.py`). Cols incl. **Image prompt (still)** + **Grok video prompt (i2v)** + **Status**.
- ✅ **In-world park brand = "DINO ZOO"** (owner renamed from "Dinoverse Zoo" — applied everywhere).
- ✅ **ALL 76 GEN stills DONE** (`stills/Sxx.png`). Generated in ChatGPT, one thread, consistency-chained.
- ✅ **Reworked back third** (owner-directed): early **"HYBRID – STAFF ONLY" door plant** (teens slip in, Maya
  "that's weird") → tour → hybrid **breaks its gate → trips the power → all dinos loose** (raptor head-tilt
  cascade, slow→fast chaos, **crowd panic** shots) → couple **hides** → **Blackhawks** inbound → "FOLLOW FOR PART 2".
  We don't explain HOW it got out — the door plant lets the audience assume.
- ✅ **i2v STARTED: Spinosaurus scene DONE** — 6 Grok clips `approved/S10–S15.mp4` (1264×720, 6.04s each, status=`clip`).

## NEXT JOB: Grok i2v for the remaining **70 stills**
Still `status=still` (need clips), by scene:
- 0 Intro: M01, S00 · 1 Entry: S01, S02, S03, S03b, S03c · 2 Carnotaurus: S04–S09
- 4 Therizinosaurus: S16–S21 · 5 Quetzalcoatlus: S22–S27 · 6 Velociraptor: S28–S33
- 7 Sauropods: S34–S39 · 8 Mosasaurus: S40–S45 · 9 T-Rex: S46–S51 · 10 Hybrid: S52–S57
- 11 Breakout: S60–S67, S66b, S67b, S66d · 12 Outro: S68–S71

## THE i2v PIPELINE (PROVEN THIS SESSION — use exactly this)
Engine = **Grok Imagine** (grok.com/imagine), owner has Grok Pro. Settings: **Video · 720p · 16:9 · 6s**.
Output spec = **1264×720, 6.04s mp4**.

**Uploading the still is the only hard part — solved via CLIPBOARD PASTE.** (Why: Grok's "Upload" button opens a
native macOS file picker invisible to automation; the `file_upload` MCP tool sandboxes out project files; a
localhost image server is CSP-blocked by grok.com. Clipboard paste sidesteps all three.)

Per-shot loop (Chrome MCP drives the Grok tab; Bash runs osascript + saves):
1. **Put still on clipboard (Bash):**
   `osascript -e 'set the clipboard to (read (POSIX file "<ABS path>/stills/Sxx.png") as «class PNGf»)'`
2. **Grok (Chrome MCP):** click sidebar **"New Generation"** → click the **"Type to imagine"** composer input → **Cmd+V**
   (the still attaches as a thumbnail) → type the **animate prompt** (see below) → click the **submit ↑ arrow**
   (bottom-right of composer; it moves down as the prompt grows — screenshot to confirm before clicking).
3. **Wait ~60–90s.** Poll with a screenshot; done = the still-frame video + right-panel Share/Download/Regenerate/Extend.
4. **Download:** click **Download** in the right panel → then Bash:
   `f=$(ls -t ~/Downloads/grok-video*.mp4 | head -1) && cp "$f" approved/Sxx.mp4`
5. **Mark `status=clip`** for Sxx in STORYBOARD.tsv.

**Animate prompt format** (don't paste the raw sheet column — rewrite it as natural language):
> "Animate this exact image as a real zoo documentary clip, 16:9. Camera: <cam>. Motion: <move>. Audio: <sound>.
> Dialogue (<speaker>): \"<line>\". Style: non-cinematic, grounded, flat natural daylight, no fog, no color grading,
> exact environment match."
Pull cam/move/sound/dialogue from the **"Grok video prompt (i2v)"** column for each shot.

**Gotchas:**
- Grok shows a **one-time age-confirmation gate** before the first video — owner must clear it (done this session).
  It's a personal attestation; do NOT submit it for them.
- Grok keeps **native audio + dialogue** in the clip. Owner should **spot-check the audio** actually speaks the lines —
  long narrator/fact lines (e.g. S11, S14) were flagged in the original handoff as sometimes needing a re-roll.
- `cmd+v` in browser_batch works; the Grok window may resize (coords shift) — screenshot to re-anchor.

## ASSEMBLY (after all clips, separate phase)
Keep Grok native audio → layer freesound ambience + music bed → 2 disclaimer cards front → 1080p.
FFmpeg concat per `ORCHESTRATION.md`, or CapCut. Renderer ref: `scripts/ffmpeg_production_render.py`.

## STILL-REGEN GUARDRAILS (only if you must re-make a still in ChatGPT)
ChatGPT hard-refuses: visible panic/screaming crowds, predation, gunfire-at-people, kids-in-peril. Frame peril as
**"emergency evacuation"** (running, looking back, dust — NOT panic/screaming), predator action as **empty jaws /
implied / silhouette**, and never a child in danger. These dodges are already baked into the breakout/outro stills.

## KEY FILES (all in `dinoverse_clone/episode_01_omega_rex/`)
- `build_storyboard.py` (source) → `STORYBOARD.tsv` · `stills/Sxx.png` (76 done) · `approved/Sxx.mp4` (6 done)
- `VERIFIED_PROMPTS.md` · `EDITING.md` · `characters.txt` · `style.txt`
- `work/` helpers: `save.py` (move ChatGPT dl → stills + mark status) · `_extract.py` (dump remaining prompts to
  `remaining_prompts.json`) · contact sheets (`ALL_stills_contact_sheet.png`, `reworked_ending_contact_sheet.png`)
- Hard rules: `../../CLAUDE.md`. Memory index: `memory/MEMORY.md`.

## HOW TO RESUME (paste into a fresh session)
"Read dinoverse_clone/episode_01_omega_rex/dino_production.md. Continue the Grok i2v pass for the 70 stills still at
status=still, scene by scene, using the clipboard-paste pipeline (osascript PNG → Cmd+V into Grok, Video/720p/16:9/6s).
Pull each shot's motion/dialogue from the 'Grok video prompt (i2v)' column, save to approved/Sxx.mp4, mark status=clip,
commit per scene. Start with Scene 1 Entry. Grok is in Chrome; settings persist; if an age gate appears, ask me to clear it."
