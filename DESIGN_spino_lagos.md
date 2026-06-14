# Video #2 — Spinosaurus in Lagos — DESIGN & PROVENANCE

**Purpose:** for every step of this video, exactly where the information came from —
and where I deviated from the source of truth or made a mistake. Written 2026-06-14
at the owner's request after the hook came out repetitive/zooming.

**Legend**
- ✅ **sourced** — pulled from a committed project file / rule / your decision
- ⚠️ **my own** — my authoring or training knowledge, NOT from a project source (so: unverified)
- ❌ **deviation / mistake** — I went against the source-of-truth, or got it wrong

---

## Step-by-step

### 1. Premise — Spinosaurus in Lagos ✅
- **Title formula** "I Simulated a {Creature} in {Modern Place}, {Consequence}" ← `NEXT_VIDEO.md` §10 (verified packaging formula).
- **"Modern collision is mandatory"** ← `NEXT_VIDEO.md` §2.
- **Place = your choice** — I proposed 4 (Nile, Lagos, Congo, Suez); you picked Lagos.

### 2. Script — `scripts/spino_lagos.txt` ⚠️ (mixed)
- **Grammar / arc / CTA flywheel** ← `scripts/trex_pilot.txt` (the proven pilot script). ✅
- **Chapter structure** (body → senses → hunt → reckoning) ← `research/trex_pilot_chapter_plan.md`. ✅
- **Noun-literal stats so they illustrate** ← `research/edit_decision_rulebook.md`. ✅
- ⚠️ **I did NOT read `playbook/scripting.json` or `playbook/editing.json`** — the channel's actual scripting/editing rulebooks. I modeled only on the pilot artifacts above. Gap.
- ⚠️❌ **Creature facts (50 ft, 7 tons, man-tall sail, conical teeth, pressure-sensing snout, paddle tail, dense/sinking bones, canoe-sized sawfish prey): from MY training knowledge.** Not verified against any source, not attributed on screen. The channel rule (`CLAUDE.md`, `playbook/sources.json`) is **public/verified data only**, and the rulebook says bold claims need on-screen attribution ("— paleontologists"). **These are currently unverified and unattributed — a publish blocker.**

### 3. Voiceover — ElevenLabs "Mark" ✅
- **Method** (ElevenLabs site, voice "Mark") ← `NEXT_VIDEO.md` §3.
- **Exact settings** (paragraph-split for the 5k cap, `<break>` tags for pauses, voice "Mark - Natural Conversations", model **Multilingual v2**, stability 39 / similarity 75 / style 0) ← read off the pilot's own ElevenLabs **History** during this session.
- **One pass, no re-rolls** ← your instruction.

### 4. Word alignment — whisperx ✅
- Reused the canonical `run_forced_alignment()` in `scripts/realign_paper_edit.py`, via a thin new wrapper `scripts/make_whisperx_alignment.py` (calls the existing function — not a parallel invention).

### 5. Stills — ChatGPT ✅ (method) / ⚠️ (prompts)
- **One-conversation-per-world + viewer-download route** ← `NEXT_VIDEO.md` §4.
- **Photoreal house-style language** ("photorealistic, cinematic, film grain, 16:9") ← `research/trex_pilot_shot_sheet_hook.md` ChatGPT manufacture list. ✅
- ⚠️ The specific prompts (the Lagos lagoon, the angles) are my authoring, consistent with that style.

### 6. Cutouts — rembg ✅
- rembg is the established cutout tool (pilot cutouts live in `assets/trex_pilot/cutouts/`). I added `scripts/make_cutout.py` because **no standalone cutout maker existed** (`composite_beat.py` consumes cutouts but doesn't make them; grep confirmed none).

### 7. Motion clips — LTX i2v ❌ → ✅ (this is where I screwed up worst)
- **Correct source:** `scripts/gen_dunk_clips.py` + `tools/ltx-video` — the pilot's **free, local** image-to-video. This is what produced the approved pilot's moving creature shots.
- ❌ **MISTAKE 1:** my first hook used **static stills + zoom** and **no motion clips at all** → the "same creature zooming" you rejected.
- ❌ **MISTAKE 2:** I then put a **paid** i2v decision in front of you (Kling/Veo/Hailuo, ~$5–15) as if you had to spend — when the approved method was the **free local LTX already installed**. You caught it ("what did claude do on the approved one?"). Now corrected — using `gen_dunk_clips.py` (free).

### 8. The edit / composite beats — `scripts/build_spino_hook.py` ❌ → ✅
- **Engine** ← `scripts/composite_beat.py` (existing). ✅
- **Builder pattern** ← `scripts/build_body_reveal.py` (the proven size-breakdown builder). ✅
- ❌ **MISTAKE 3:** my first version fed the engine **static plates** (`bg_still`) + a zooming cutout. But `build_body_reveal.py` uses **real moving footage** as the background (`dunk_nyc_avenue_taxis.mp4`, stock clips) — that's why the pilot felt alive and mine zoomed. Corrected: v2 uses `bg_video` = the LTX motion clips, `camera='none'` (no zoom).

### 9. Stat devices — tape / gauge / count ✅ except one ❌
- **Device renderers** (measuring_tape, gauge, count) ← `composite_beat.py`. ✅
- **Which device per stat** ← `research/edit_decision_rulebook.md`. ✅
  - 50 FT → horizontal tape (rulebook: length → horizontal tape) ✅
  - SAIL 6 FT → vertical tape (rulebook: height → vertical tape) ✅ — but ⚠️ the tape sits as a fixed side-ruler, not pinned on the sail.
- ❌ **DEVIATION — 7 TONS gauge.** The rulebook explicitly says **weight → a balance SCALE (creature = bus)**: *"9 TONS = bus."* A gauge is the rulebook's device for **force**, not weight. `composite_beat.py` has no scale device (the pilot hand-drew the bus-scale in `build_body_reveal.py`), and I took the gauge shortcut. **Wrong per the source. Open.**

### 10. SFX ❌ → ✅
- **Library** ← `assets/sfx/` (existing). **Placement** (whoosh + impact on the word) ← `build_body_reveal.py`. ✅
- ❌ **MISTAKE 4:** first version reused the same 2–3 SFX → "same sound effect." Corrected: v2 varies SFX per beat.

### 11. Brand text ✅
- BIG orange, heavy ink outline, no banner ← `composite_beat.py` `big_text_cb` (the locked brand call recorded in `research/trex_pilot_chapter_plan.md`).

### 12. Tempo / style targets — ❌ GAP (never measured)
- **Spec** ← `research/style_bands.json` (events ≥25/min · median shot 1.5–4s · static ≤40% · music ≥90% · cards ≤6 & ≤2.2s) + `scripts/gate_style.py` / `gate_ch1.py`.
- ❌ **I have NEVER run the gates on the spino render.** The project's own rule is *"the gate IS the spec."* So part A is **unverified** against the approved bands — I eyeballed it, I did not measure it.

### 13. Music bed — ❌ not chosen
- Open decision. `ffmpeg_production_render.py:994` falls back to the **Breaking-Law documentary bed** if no creature bed is set (documented gotcha). Not addressed.

---

## Honest scorecard

| # | Issue | Source it should have followed | Status |
|---|---|---|---|
| 1+3 | Static stills + zoom (not moving clips/backgrounds) → "zooming" | `build_body_reveal.py` uses moving footage | ✅ FIXED (LTX motion) |
| 2 | Proposed **paid** i2v when free local LTX is the approved method | `gen_dunk_clips.py` + `tools/ltx-video` | ✅ FIXED |
| 4 | Reused SFX → "same sound" | `build_body_reveal.py` varied SFX | ✅ FIXED |
| — | **7 TONS gauge** instead of bus-scale | `edit_decision_rulebook.md` (weight = scale) | ❌ OPEN |
| A | **Creature facts unverified + unattributed** | `playbook/sources.json` (verified/public only) | ❌ OPEN (publish blocker) |
| B | Never read `playbook/scripting.json` + `editing.json` | the channel's own rulebooks | ❌ OPEN |
| C | **Never ran the gates** on spino | `style_bands.json` + `gate_style.py` | ❌ OPEN |

**Bottom line:** the foundation traces cleanly to the pilot's proven pipeline. The four "feel" mistakes (zoom, paid-i2v, SFX, static bg) are fixed. The four **open** items — the weight device, **unverified creature facts**, the unread playbook rulebooks, and the **un-run gates** — are real and listed above. The biggest of these is the unverified facts (a publish blocker) and the un-run gates (we can't claim the edit hits the approved style until they pass).
