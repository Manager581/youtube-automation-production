# NEXT SESSION — Wild Bird Survival clone · Episode 02 (vampire finch)
_Last updated 2026-07-23. This supersedes all earlier handoffs. Read top-to-bottom._

## Where we are in one line
**The plan, the script, the packaging and the look are LOCKED and committed. What's missing is the
footage (~72 of ~80 shots) and one music bed.** Everything below is verified, not assumed.

---

## THE DECISION (locked 2026-07-23)

**TITLE:** `Why This Giant Seabird Lets a Tiny Finch Drink Its Blood`
(56 chars · no suffix · no question mark · no colon)
Isomorph of their **#2 all-time (939,961)** — *"Why This Warthog Lets Mongooses Crawl All Over Its Face"*
(55 chars, the only top-8 title with no pipe). Stacks the 654K scale-gap lever ("Giant"/"Tiny").
"Lets" appears in exactly two of their titles: 939,961 and 130,161.

**THUMBNAIL:** text = **`BLOOD`** (yellow `#FFD400`) / **`FOR EGGS`** (white), heavy condensed sans,
8–10px black outline, stacked, **left third over a dark plate** (the finch's black body — yellow on
white feathers collapses). Wound **≥12% of frame**, most saturated element, tack sharp.
🚨 **SHIP GATE: downscale to 168×94px. If the red doesn't instantly read as _blood_, recompose.**

**⚠️ The premise-risk correction that matters (verified):** their own *"This Bird Drinks Blood From Live
Animals"* did 13,095 — but it is **upload #1 of 26**. Uploads #1/#2/#3 are the three worst ever
(13,095 / 1,879 / 26,720); first-five median **26,720** vs rest-of-channel **117,489** (4.4× cold-start),
and their first real hit was upload #8. **Blood is not disproven.** What actually kills videos on this
channel: actor-POV declaratives, benign verbs ("Protect" 34,666 / "Save" 100,703), "Full Life Cycle"
framing, and self-cannibalization (3,041 = near-clone of their own #1 published one day later).
**Do not publish within 72h of any other blood/parasite/feeding video.**

---

## WHAT EXISTS (all committed)
| Layer | State | Where |
|---|---|---|
| Second-by-second plan, full 8:00 | ✅ LOCKED | `SECOND_BY_SECOND_theirs_vs_ours.md` (+ published page) |
| The WHY / causal grammar | ✅ LOCKED | `STORYBOARD_SIDEBYSIDE_reference_vs_ours.md` |
| Full VO script, 487 words to timecode | ✅ LOCKED | `EP02_SCRIPT_LOCKED.md` |
| Scene-by-scene storyboard | ✅ | `EPISODE_02_VAMPIRE_FINCH_STORYBOARD.md` |
| Title + thumbnail | ✅ LOCKED | storyboard Step 0 (above) |
| Look / grit recipe | ✅ PROVEN on 8 clips | `EPISODE_02_GRIT_TEST_RESULTS.md` |
| Voice settings | ✅ PROVEN | ElevenLabs **Brian**, speed ~0.85 (=150–155 wpm), stability 74 |
| Mix spec | ✅ PROVEN | VO loudnorm `I=-16`, bed ~20 dB under, limiter 0.95, no SFX on cuts |
| SFX (8 diegetic) | ✅ | `assets/vampire_finch/sfx/` (wind + peck are approximate — upgrade if time) |
| Reference data | ✅ | `wbs_meta.tsv`, `FORENSICS.md`, `compare_metrics.json`, `gate_style_wbs.py` |

## WHAT'S MISSING (the real work)
1. **~72 of ~80 shots.** We have 8 clips + 5 seed stills. Shot manifest = Part E of the storyboard.
   Need ~6 more seed stills (macro-tail, raw-wound, finch portrait, mutualism-clean, prickly-pear,
   a barren wide with the booby CLEAR — not the tiny-dot one).
2. **The music bed** — one continuous harmonic track, swell ~2:19, fall at the end. Pixabay only
   (project rule); no API key → browser pull. **Hygiene, not a lever — don't over-invest.**
3. **The thumbnail image itself.** A ChatGPT gen was in flight at session end (extreme macro, booby head
   right two-thirds, blood LARGE, dark left third for text). Existing crops in
   `assets/vampire_finch/thumbs/` FAIL — blood reads too small and the left third is white.

## HOW TO GENERATE (proven recipes — do not reinvent)
- **Stills:** ChatGPT gpt-image. Grit recipe = *"raw wildlife documentary footage, telephoto, flat
  overcast light, desaturated, handheld, BBC Planet Earth, NO golden hour, NO cinematic lighting."*
  **Thumbnails are the exception — they must be punchy/saturated/dramatic, NOT the flat doc grade.**
- **Clips:** Grok Imagine, **Video · 720p · 6s · 16:9** (New Generation resets to 480p — re-select 720p).
  Upload via clipboard: `osascript -e 'set the clipboard to (read (POSIX file "<abs>.png") as «class PNGf»)'`
  → click composer → Cmd+V → **zoom-verify the thumbnail attached before submitting** (a background
  process clobbered the clipboard mid-run once; re-run the osascript immediately before each paste).
- **Riders that work:** "keep exact anatomy, no extra limbs, no morphing, count stays the same."
  **Blood rider (REQUIRED):** *"a DRY matted red bloodstain that does NOT drip, stretch, run, or form any
  thread/string — only the finch moves."* Plain "blood" → Grok animates a dripping red thread.
- **Avoid** prompting the booby to turn fully head-on to camera (weak i2v frame).
- **VO:** ElevenLabs browser (acct `ElevenCreative`), voice Brian, speed slider ~0.85. Whisper-verify
  every line. Generate the whole script in ONE pass, split at blank lines, drop at the timecodes.
- **QA:** frame-strip every clip before it's used. Then `gate_style_wbs.py` on the render → 11/11.

## THE CRITICAL PATH
1. Thumbnail image → run the **168×94 gate** → if it passes, the packaging is done.
2. ~6 seed stills → ~72 clips (the multi-hour grind) → frame-strip each.
3. VO in one ElevenLabs pass to the locked script.
4. Music bed (quick, low stakes).
5. FFmpeg assemble to the second-by-second → `gate_style_wbs.py` 11/11 → owner watch → upload.

## HARD-WON LESSONS (don't repeat)
- **Grit-test clips ≠ scene coverage.** A cut built from a few test clips looks like a glitchy loop.
  Every beat needs a DISTINCT vantage.
- **Never pad the hook with a long wide of a tiny animal in a landscape** — that's their loser pattern.
  Their hook opens on the FACE and cuts 1.4–2.2s, then lengthens.
- **macOS `say` is unusable** (robotic). Local Chatterbox clones the owner's voice with an accent —
  owner rejected it. **Use ElevenLabs Brian.**
- **Aggregate stats (median shot length etc.) are outputs, not the plan.** The plan is the WHY at each
  moment — see `STORYBOARD_SIDEBYSIDE_reference_vs_ours.md`.
- **Evidence weight matters:** music peak / hook cut-count / cuts-on-word are *weak hygiene markers*.
  The load-bearing items are the shots and the title/thumbnail.
</content>
