# NEXT SESSION — Wild Bird Survival clone · Episode 02 (vampire finch)
_Last updated 2026-07-23 (FOURTH session of the day). This supersedes all earlier handoffs._

## Where we are in one line
**Packaging DONE, plan COMPLETE (88 shots, gate 15/15), all 23 seeds on disk, and the **VO IS NOW DONE
AND VERIFIED** (one pass, 37 blocks, split to timecode). What remains is the clip grind (86 shots), one
music bed, assemble.**

## ▶️ START HERE (do these in this order)
```bash
cd /Users/jefflawrence/Documents/youtube-automation-production
venv/bin/python research/wildbirdsurvival_teardown/gate_shots.py          # expect ALL 15 PASS
venv/bin/python research/wildbirdsurvival_teardown/gen_clip_ledger.py --next 3   # status + next shots
```
1. **READ `EP02_GROK_GRIND_RECIPE.md` FIRST.** It has the proven browser recipe (including the one
   incantation that actually attaches a seed), the four dead ends not to retry, and — most importantly —
   **why you must check each SEED against its prompt before generating.** The first clip generated
   this session was rejected for reasons that were all in the seed, not the prompt.
2. **The clip grind — 86 shots left.** Work the ledger, not memory. Frame-strip every clip; a shot is
   not done until `<ID>_strip.jpg` exists AND you have looked at it.
3. Music bed (one Pixabay track, hygiene only) → assemble → `gate_style_wbs.py` 11/11 → owner watch → upload.

**Decisions already made — don't re-litigate:** thumbnail = **ALT**; VO speed = **0.95** (settled by
measurement, see below).

## ✅ VO — DONE (2026-07-23, owner approved the single pass)
`audio/vampire_finch/ep02_vo_full_sp95_s74_sb75_m2.mp3` — **199.86 s, 155.2 wpm, 41.6 % coverage**,
mono 44.1 kHz 128 kbps. Split into **37 blocks** in `audio/vampire_finch/blocks/`, each with its drop
timecode in **`ep02_vo_block_manifest.json`** — that manifest is what the assembler should read.
*(Audio is local-only: `*.mp3` is gitignored repo-wide.)*

- **Speed settled at 0.95 by measurement.** 0.75→131.5, 0.84→138.9, **0.95→153.7 wpm** on the real
  script text. ⚠️ The wpm/speed curve is **NOT linear** — slope ≈82 wpm/speed below 0.84 but ≈135 above
  it, so the old linear fit predicted 147.8 and was wrong by ~6 wpm. Never fit a line to it again.
- **Verified clean, no misreads.** 509/520 script tokens aligned against whisper word timestamps; all
  10 remaining diffs are tokenisation artifacts (whisper splits "seabird"→"sea bird" 7×, joins
  "ground finch", splits "onto"/"seawater"). Read diffs before failing a take.
- **The script is 517 words, not the 487 the ledger in `EP02_SCRIPT_LOCKED.md` claims** — that table is a
  stale hand-estimate (it says ACT 1 = 28; the real text is 41). Verified: `wc -w` 526 − 9 standalone
  em-dashes = 517. The 41.6 % coverage is computed from the real count.
- **Splitting is content-aware, not silence-threshold.** Silences form a continuous ramp 1.0 s → 0.30 s,
  so paragraph breaks and ordinary sentence periods overlap and **no cutoff separates them** — a silence
  split cuts mid-block. `split_vo_blocks.py` maps script tokens to whisper word times and cuts at the
  midpoint of each inter-block gap.
- **All 37 blocks fit their storyboard slots** — 0 overrun the gap to the next timecode, and the last
  drops at 468 s + 3.48 s = 471.5 s, leaving the 8.5 s wind tail the closing [SILENCE] wants.
- To regenerate: `transcribe_vo.py` (cached) then `split_vo_blocks.py`.

## ✅ SEEDS COMPLETE (this session)
Generated 12 new seeds + 1 pricklypear in ONE ChatGPT gpt-image thread ("Nature Documentary Stills"),
recovered SEED_mutualism_clean from ~/Downloads, and built 3 crop-shortcuts + the redtip locally.
Re-run `gen_seed_shopping.py` → **0 to generate, 0 shortcuts, 23 on disk.** Every seed visually QA'd
(booby anatomy correct, finch beaks short/conical not crow, dried-not-dripping stains, desaturated grade).
- The 10 new-seed prompts are written + audited in `ep02_new_seed_prompts.json` / `EP02_SEED_PROMPTS_NEW10.md`.
- `SEED_finch_portrait_redtip` is a LOCAL paint (dark-red mark on the real portrait's beak tip) → a true
  pixel-identical match-cut, better than a regen. `SEED_macro_tail_high`, `SEED_flank_stain_top`,
  `SEED_pricklypear_top` are local crops of their base gens.

### ⚙️ BROWSER METHOD THAT WORKS (use this for the clip grind's still-handling too)
- **ChatGPT composer is ProseMirror — plain `type` keystrokes DON'T land.** Insert via
  `execCommand('insertText', …)` after focusing `#prompt-textarea`; verify `.innerText.length`; submit by
  clicking `[data-testid="send-button"]` via JS. One-line prompts only (newline submits early).
- **Download: the `<img>` CDN renders blank/lags ~15-25s and the extension BLOCKS base64 in JS returns.**
  Robust exfil = in-page `fetch(img.src,{credentials:'include'}) → blob → <a download>` (works even when
  `<img>` won't render; bytes go via Chrome's download pipe). Readiness signal = total `main img` count
  rose by 3 AND no stop-button. **Owner had to click "Always allow downloads from chatgpt.com" once.**
- Don't `location.reload()` a thread with many images — it resets ALL image loads to blank. Use fetch-blob.

---

## ✅ WHAT LANDED THIS SESSION

### The thumbnail ships — ✅ **DECIDED: ship `ALT_ep02_thumbnail_ungraded.png`**
Owner had no preference (2026-07-23) and delegated the call. **Ship the ALT (ungraded) cut.**
Measured reason: at the only size that matters (168×94 browse), ALT lands a **1291 px** red blob /
12.06 % red vs FINAL's **1378 px** / 12.81 % — a difference no browsing viewer can perceive. ALT fails
*only* the full-frame ≥12 % rule (11.66 %), by 0.34 pp. So you keep the click and drop the
"visibly bloodied bird" advertiser risk that the spec's own safety clause warns about.
Both bird anatomy and the Giant/Tiny scale gap read correctly in either cut; text-free versions are
`ALT_ep02_base_notext_ungraded.png` / `FINAL_ep02_base_notext.png` for the `BLOOD HOSTAGE` A/B swap.
*(`FINAL_ep02_thumbnail.png` remains on disk as the 4/4 alternative if you later want max blood salience.)*

### The gate is now mechanical, not an eyeball check
`thumb_gate.py` measures the four things the spec actually asserts and prints PASS/FAIL with numbers:
blood area %, blood-vs-rest saturation, luminance **under the real type box**, and the largest
surviving red blob at 168×94. It writes a gate sheet whose lower panel is the true 168×94 image
nearest-upscaled 4× — that adds no information, so it shows exactly what a browsing viewer sees.
```bash
venv/bin/python research/wildbirdsurvival_teardown/thumb_gate.py BASE.png OUTDIR --tag name
```
Flags: `--crop x,y,w,h` · `--grade` (the spec's selective grade) · `--plate` (dark gradient fallback).

**Why the old crops could never work:** measured at **0.05–0.09% blood area against a 12% spec — a
130–240× shortfall.** No crop of those sources closes that. That is now proven, not asserted.

### Recovered work that had been lost
- **The shot manifest was never missing — it was destroyed.** `STORYBOARD_SIDEBYSIDE` originally
  carried Parts D/E/F; the rewrite after Jeff rejected the stats framing took the manifest with it.
  The rewrite was correct and stands. The manifest is restored on its own at **`EP02_SHOT_MANIFEST.md`**
  with provenance. *This is why the old handoff pointed at a "Part E" that does not exist.*
- **`EP02_PACKAGING.md`** — description, 12 tags, 3 hashtags, the A/B title ladder **with the measured
  reasons each option was rejected**, and the thumbnail hard-nos. All written previously, never saved.
- **`EP02_SEED_PROMPTS.md`** — the 6 missing seed stills as copy-paste prompts, ranked by shots unblocked.

---

## ⚠️ TWO SPEC ERRORS FOUND — **both now RESOLVED** (kept for the reasoning)

**1. The thumbnail spec contradicts itself — RESOLVED → ship ALT.** It demands **wound ≥12% of frame**
*and* **"no gore beyond one bead + smear (advertiser safety)."** Both cannot hold. FINAL reaches 12.58%
only via the spec's own selective grade and reads as a visibly bloodied bird; ALT is 11.66%.
**Resolution: the ≥12% rule is only a proxy for "does blood read at browse size," and ALT passes that
directly (1291 px blob at 168×94).** Satisfying the proxy at the cost of the thing it proxies for is the
wrong trade, so **ALT ships.** See the thumbnail section above for the numbers.

**2. VO speed — NOW MEASURED (2026-07-23). Both earlier claims were wrong.**
Measured on **this script's own text** (52-word probe, Brian, stab .74 / sim .75 / style 0, Multilingual v2):

| speed | duration | **wpm** |
|---|---|---|
| 0.75 | 23.72 s | **131.5** |
| 0.84 | 22.47 s | **138.9** |

Slope ≈ **82 wpm per 1.00 speed** → **0.85 ≈ 139 wpm.** So the script note's "0.85 ≈ 150 wpm" was wrong,
and this file's own earlier "0.85 ≈ 185 wpm" was *also* wrong — that one interpolated the 0.71 cold-open
take (143.3 wpm, re-measured and confirmed) against a reported default of 215 wpm, but those are
**different texts**. ⚠️ **wpm is strongly text-dependent** — long words + sentence stops lower wpm at the
same voice speed. Never interpolate across texts again; measure on the real script.

**Target:** the script is 487 words written for ~195 s of speech (41 % coverage) ⇒ **~149 wpm**, which
extrapolates to **speed ≈ 0.96** — *UNCONFIRMED*: the 0.95 probe stalled at ElevenLabs (job never charged).
**Next session: run ONE 0.95 probe, measure, then commit the single full pass.** For reference, 0.84
already yields 210 s / 43.8 % coverage — inside the winners' 40–50 % band, so 0.90–0.96 is the safe zone.
Owner's chosen band is **150–160 wpm**. Raw data: `ep02_vo_speed_measurements.json`; probe audio in
`audio/vampire_finch/vo_probe_sp75…mp3`, `…sp84…mp3`. Account `ElevenCreative`.

**Reference channel's measured pacing** (from `FORENSICS.md`, why 150ish is right): winners run
**145–163 wpm** (biggest hit 1.98M = 157; hornbill 153; warthog 145), the **flop races at 190**. Winners
narrate ~43 % of runtime; the flop talks over 67 %.

---

### The full shot manifest now exists
**`EP02_SHOT_MANIFEST_FULL.md` — 88 shots, every one with in/out, size, a distinct vantage, action,
seed, physics risk and a copy-paste Grok prompt.** Machine-readable twin: **`ep02_shots.json`** (read
that from any builder script); re-check with **`gate_shots.py`**, regenerate the doc with
**`render_manifest.py`**. Built by a 21-agent workflow and then independently re-verified, which caught
four defects the agents' own audit missed — including **22 duplicate shot IDs** that would have made a
builder silently overwrite clips.

**All 15 gates PASS** — run `gate_shots.py` after any edit. Pacing was tuned (92→88 shots: absorbed 4
weak beats to lift mean to 5.45 s; ACT7 redistributed 6/10/6/11/7/10 to slow properly and add holds).

**All 139 adversarial defects are now worked through** (was "unresolved"):
- 62 were in families the gate proves fixed (riders, anatomy, head-on, tiling).
- 18 act-level ones triaged in `EP02_DEFECT_TRIAGE.md` (tiny-dot seed purged, mean-budget fixed, stale
  NOTES superseded by the computed manifest; ACT7 cut re-timed to land on the VO line at 444 s; two
  self-contradictory rider clauses reworded globally).
- 59 genuinely-open ones (vantage duplication, VO-sync, seed-capability) resolved by 4 agents: **43
  fixed, 4 already-resolved, 12 wont_fix** (all note/ledger-level or an intentional match-cut — none is
  live shot content). Applied via `apply_defect_edits.py` (guardrails reject timing edits / dropped
  riders), gate re-hardened so the rider regression can't recur.

⚠️ **What "signed off" still means:** the plan is now internally consistent and gated, but **no owner
has watched a cut** — because the footage doesn't exist yet. The manifest is as good as it gets on paper.

## WHAT'S MISSING (the real work, in order)
1. **Seed stills — ✅ DONE (23/23 on disk).** But see the seed-capability warnings below: "on disk" is
   not the same as "reaches the shot its prompt describes."
2. **86 clips** — the multi-hour grind. **`EP02_GROK_GRIND_RECIPE.md` is the how; `gen_clip_ledger.py`
   is the tracker.** Frame-strip every clip. **Same-seed adjacency (S007-9, S058-61, S080-82): derive
   distinct seed frames by cropping the base still, don't re-prompt one frame.**
   - **S001 is DONE** — the earlier `grok_test/shot_booby_eye.mp4` is a genuine match for S001's vantage
     (booby left two-thirds, soft finch right third, slow blink) and was adopted as `clips/S001.mp4`.
   - **`grok_test/shot_wide_island.mp4` is DEAD** — its seed `still_wide_island.png` is used by **0**
     shots now (replaced by `SEED_wide_booby_clear` under the no-tiny-animal-in-a-landscape hook rule).
     The other 6 `clip0*` test clips are grit-tests, not scene coverage — don't adopt them.
3. **VO — ✅ DONE.** See the VO section at the top.
4. **Music bed** — one Pixabay track. **Hygiene, not a lever. Do not over-invest.**
5. **Assemble** → `gate_style_wbs.py` 11/11 → owner watch → upload.

## ⚠️ THREE MANIFEST DEFECTS FOUND WHILE STARTING THE GRIND
Found by checking, before generating, whether each prompt is reachable from its seed. The gate's 15
checks cover riders/anatomy/head-on/tiling — they do **not** compare a prompt to its seed or vantage.

1. **S062 — FIXED.** Its `grok_prompt` was another shot's prompt entirely: a static wound macro with
   *"no bird enters the shot"*, on the Act-6 **payoff** shot whose whole job is the booby + egg + finch
   as the VO word "take" lands at 369.4 s. It also carried the DRY-blood rider despite `has_blood=false`,
   and self-contradicted ("no bird enters" … "while the birds move"). Rewritten from its own vantage +
   action via `apply_defect_edits.py`; only S062 changed; gates still 15/15.
2. **S002 — seed cannot reach the prompt.** Take 1 rejected on its frame strip. Full analysis in
   `EP02_GROK_GRIND_RECIPE.md`; short version: the seed is a side-on medium containing **two** finches
   with a stain that **already runs**, while the prompt asks for an extreme macro from high behind the
   shoulder with **one** finch and a stain that must not run. Needs a fixed seed (a tight crop) or a
   re-spec of the shot.
3. **S021 — seed cannot reach the prompt.** `still_booby_eye.png` is an eye close-up with no neck,
   shoulder or sky; the shot wants a low front-quarter looking up at head and neck against flat sky.

**Not defects (checked and cleared):** S026 and S070 tripped a keyword heuristic but are both fine
(S026 says "stain" not "wound"; S070's egg is simply under the bird). And there are **zero** left/right
contradictions across all 88 shots.

---

## OPERATIONAL GOTCHAS (each of these cost real time — don't rediscover them)

### ChatGPT gpt-image
- **It refuses gore-forward wording**: *"the image we created may violate our guardrails around
  violence."* Trip words: wound, bleeding, drink blood, gore, welling, raw, weeping. **The register that
  works is a "dark red stain" on plumage, with size coming from magnification, not from more blood.**
- **Never type a multi-line prompt** — the first newline submits, so only paragraph one is sent.
- **Verify the composer received the text before pressing Return.** Clicking by coordinate silently
  fails often; keystrokes go nowhere. Check `document.querySelector('#prompt-textarea').innerText.length`.
  The composer sits at a **different y on the new-chat landing page** than in an open thread.
- **The inline image icons are share, not download.** ⚠️ **The canvas recipe in `EP02_SEED_PROMPTS.md` is
  SUPERSEDED** — canvas→blob worked for exactly one download, then Chrome blocked further automatic
  downloads, and the extension blocks base64 in JS returns. **Use in-page
  `fetch(img.src,{credentials:'include'}) → blob → <a download>` instead** (see BROWSER METHOD at top).
  The owner must click "Always allow downloads from chatgpt.com" once per session.
- **Requests silently drop / the image CDN lags.** A card can sit blank 15–25 s after streaming stops —
  that's usually just the CDN, not a drop. Confirm by watching the `main img` count rise by 3.
  **Do NOT `location.reload()` to fix it** — that resets every image in the thread to blank.
- **Edit mode will not crop in** — asking a generated image for a tighter macro returns the same
  framing. Crop locally instead.

### Grok Imagine (unchanged, still true)
Video · **720p** · 6s · 16:9 — New Generation resets to 480p, re-select it. Clipboard-paste the seed and
**zoom-verify the thumbnail attached before submitting** (a background process clobbered the clipboard
once and it silently did text-to-video). Download icon position moves between generations — locate it
each time. Output is 1264×720, 6.04s, 145 frames. Strip clip audio (`-an`) at assembly.

### Riders that work
- Anatomy: *"keep exact anatomy, no extra limbs, no morphing, count stays the same."*
- **Blood (REQUIRED on every gore shot):** *"a DRY matted red bloodstain that does NOT drip, stretch,
  run, or form any thread/string — only the finch moves."* Plain "blood" → Grok animates a dripping thread.
- Never prompt the booby to turn **head-on** to camera. Never prompt it to **"hunch"** over the egg —
  use "settles gently."

---

## HARD-WON LESSONS (unchanged, still the ones that matter)
- **Grit-test clips ≠ scene coverage.** A cut built from a few test clips looks like a glitchy loop.
  Every beat needs a DISTINCT vantage. This is what got `rough_cut_v1` rejected outright.
- **Never pad the hook with a long wide of a tiny animal in a landscape** — their measured loser
  pattern. The hook opens on the FACE and cuts 1.4–2.2s, then holds lengthen.
  *(`still_wide_island.png` fails this — the booby is a dot. `SEED_wide_booby_clear` replaces it.)*
- **macOS `say` is unusable**; local Chatterbox clones Jeff's own voice with an accent and was rejected
  outright. **ElevenLabs Brian, via the browser.**
- **Aggregate stats are outputs, not the plan.** The plan is the WHY at each moment —
  `STORYBOARD_SIDEBYSIDE_reference_vs_ours.md`.
- **Evidence weight:** music peak / hook cut-count / cuts-on-word are *weak hygiene markers*. The
  load-bearing items are the shots and the title/thumbnail.
- **Whisper `base` mis-hears homophones** ("being blood alive", "Buy a bird"). Read the text before
  failing a take.
- **Do not publish within 72h of any other blood/parasite/feeding video** (self-cannibalisation took one
  of their videos to 3,041).
