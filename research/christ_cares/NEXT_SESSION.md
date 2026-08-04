# CHRIST CARES — NEXT SESSION HANDOFF (updated 2026-08-04)

**State:** Style LOCKED = documentary photorealism. Owner on standard SuperGrok (720p ONLY —
1080p toast-refuses AND CLEARS the composer). 38s direction test delivered
(`output/christ_cares_direction_test_38s.mp4`). **OWNER VERDICT STILL PENDING — the owner's
resume message left the verdict placeholder unfilled. The Grok grind is GATED on it.**

## SEED PHASE COMPLETE (2026-08-04)
- **All 33 doc seeds on disk + faceless-gated:** `assets/christ_cares/doc_seeds/` (30 files)
  + `style_test/` TEST1/2/3. Two seeds were gate-failed and RETAKEN same-day:
  - `doc_ram_thicket` — first take had the ram LYING DOWN (breaks the "stands caught" motion,
    [[i2v-seed-governs-shot]]); retake = standing, braced, horns locked. PASSED.
  - `doc_pit_up` — first take had facial structure on the center rim head; retake with
    "PURE SOLID BLACK cut-out shapes / ink cutouts" wording. PASSED (all heads solid black).
- **All 9 ledger crops cut + verified:** `assets/christ_cares/crops/` (G003, G016, G018, G025,
  G029, G033, G044, G046, G051), all Lanczos-upscaled to 1672×941, all pass the WBS
  distinctness gate (cutter: `research/christ_cares/cut_genesis_crops.py`). Two respecs made
  while cutting (both are in the cutter + prompt book):
  - G044 box starts at y=0 so the robed man's head stays out of frame.
  - **G046 respec: the seed has NO staff** — crop = son's torso in the shaft (window between
    his head and the patriarch's); motion prompt updated in PROMPT_BOOK_v3 (light-on-still-
    silhouette, no staff reference — do NOT let Grok hallucinate one).
- **Contact sheet for owner:** `assets/christ_cares/genesis_seed_contact_sheet_2026-08-04.png`
  (40 seed tiles + 9 crops). Sheet-level checks pass: one doc register throughout, painterly
  survivors read as the divine-light exception, serpent + sauropod continuity holds.
- Known WS-level acceptances (frame-strip at clip stage will re-check): tent_blessing
  patriarch = dim shadowed profile (below perceptibility, owner-approved silhouette treatment);
  chains forearms more lit than "deep shadow" but hands-only by design.

## MASTER DOCS (read in order)
1. `GENESIS_PROMPT_BOOK_v3.md` — LOCKED prompts (G046 motion updated 2026-08-04).
2. `GENESIS_SHOT_LEDGER.md` (v2) — timings (whisperx-snap rule), sizes, burst chains, build order.
3. `GENESIS_OVERVIEW_SCRIPT_v1.md` — script, NKJV compliance, recon.

## OTHER ASSETS (unchanged)
- **VO:** `audio/christ_cares/genesis_overview.wav` (274.2s) + `genesis_overview_whisperx.json` ✓
- **Grok clips DONE (7):** `assets/christ_cares/clips/G001,G002,G004,G005,G006,G007,G008.mp4`
  — 720p/6s, native ambient audio on ALL 7.
- **Painterly survivors:** S01a (G001 done / G047 reprise pending), S05 (G017), S14 (G049),
  S10 (G034 — owner review on the contact sheet).

## PROVEN GROK i2v CYCLE (grok.com/imagine, tab flow)
1. `osascript -e 'set the clipboard to (read (POSIX file "<seed.png>") as «class PNGf»)'` —
   **RE-RUN BEFORE EVERY PASTE** (owner's copying overwrites the clipboard; clear composer with
   cmd+a+Delete if the image chip is missing).
2. Click composer (~790,735) → `cmd+v` → wait 3s → VERIFY the image chip appears (screenshot).
3. Type the motion prompt from PROMPT_BOOK_v3 (incl. Sound: block + [RIDER]).
4. Settings: **Video / 720p / 6s** (NEVER click 1080p — refuses + clears composer).
5. Click send (~1105,766) — often needs a SECOND click ~5s later; URL flips to `/imagine/post/...`.
6. Render ~40-60s. Download icon (~1460,779) → `grok-video-*.mp4` in ~/Downloads → `mv` to
   `assets/christ_cares/clips/GXXX.mp4`.
7. Back arrow (~207,22) → next clip. ~3 min/clip. ~20 videos/24h cap on standard SuperGrok.

## CHATGPT SEED CYCLE LESSONS (2026-08-04 session)
- Gens can take 20+ min under load and the client stream HANGS while the server finishes —
  reload the thread AND nudge-scroll (up 5 / down 8) to mount the finished image; the
  lazy-loaded `<img>` won't appear without it, and background-tab timers are throttled so
  in-page autopilot intervals crawl. Drive polling externally.
- Image `src` URL patterns changed mid-session (backend-api → new CDN) — select thread images
  by `naturalWidth >= 1000`, not src substring.
- Same-tab multi-downloads work (fetch blob + a.click); one-per-fresh-tab no longer needed.

## RESUME ORDER
1. **OWNER GATE: direction-test verdict on `output/christ_cares_direction_test_38s.mp4`** —
   if changes are ordered, fold into PROMPT_BOOK_v3 before any Grok spend.
2. Owner eyeballs `genesis_seed_contact_sheet_2026-08-04.png` (incl. the G034/S10 review call).
3. Grok grind remaining ~43 gens (respect ~20/day cap — 2-3 days; the 7 test clips already
   exist) → frame-strip EVERY clip (priority: G009, G011, G025, G038, G041, G045, G046) →
   faceless+physics gate.
4. Upscale pass all clips 720p→1080p (test grain survival; Topaz or ffmpeg realesrgan-alt).
5. Assembler v2: rewrite `scripts/assemble_genesis_pilot.py` to cut CLIPS with whisperx-snapped
   times (0.3s snap rule + R2 turn-words), P2 + Joseph burst chains, G050a-d word-onset flashes
   (onsets: dinosaurs 261.01, flood 261.89, Cain's wife 263.11, Nephilim 264.43; G050c reuses G021).
6. Overlay pass: verse-reference lower-thirds at the 8 NKJV quotes + attribution card + AI disclosure.
7. Contact sheet + WATCH before reporting ([[stills-are-seeds-not-film]]; [[watch-output-before-reporting]]).
8. Music/hymn decision with owner after motion approval (self-rendered MIDI only).

## STANDING RULES
Faceless gate per frame · silhouettes featureless · no golden-hour in doc plates · divine light
= the luminous exception · Sound: blocks concrete + "no music" · keep native audio when good
(fired 7/7 so far), fallback ambience bed otherwise · AI disclosure ON · trailer title family
("All of Genesis in 5 Minutes — The True Account") · commit + push when work lands.
