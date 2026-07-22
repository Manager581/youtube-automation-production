# Episode 02 — Grok Grit Test Results (vampire finch × Nazca booby)
_Run 2026-07-22, autonomous session. Locked hero still + Grok Imagine i2v (Video · 720p · 6s · 16:9),
grit recipe. Every clip frame-stripped (3×3, every 15th frame) and read for physics/anatomy.
Files in `assets/vampire_finch/` and `assets/vampire_finch/grok_test/`._

## Bottom line
**The pipeline is proven and the recipe is locked.** The two biggest unknowns from the last session
(does the grit look survive i2v; does hard action hold without morphing) are both PASS, identity is
consistent across clips, and the single failure mode found (blood renders as a dripping thread) is
SOLVED with a prompt fix. Downloads worked autonomously all session. Ready to scale to the full ~80.

## Seed stills (locked)
- **`assets/vampire_finch/hero_still_A_booby_finch.png`** (1672×941) — THE anchor. ChatGPT gpt-image,
  one pass, vision-QA PASS (correct Nazca booby + vampire finch at wing base with red blood bead +
  2 more finches + grit look). Use for establishing / wide / action / interaction / resolution clips.
  **Doubles as a thumbnail base.**
- **`assets/vampire_finch/hero_still_A2_macro_finch_wound.png`** (1264×720) — tight crop of A around the
  finch+wound, upscaled. Use for cold-open + hero-hold + any tight gore close-up. (A cleaner higher-res
  macro also exists as ChatGPT's 2nd variant — regenerate at full res if A2's softness shows.)
- **`assets/vampire_finch/hero_still_B_egg_nest.png`** (1672×941) — booby half-risen over a single white
  egg with two finches eyeing it. ChatGPT gpt-image, vision-QA PASS. Use for the egg reveal (Scene 8)
  and egg-roll (Scene 9).

## Clips tested (6 gens across every class the seeds support)
| # | Clip / class | Seed | Verdict | Notes |
|---|---|---|---|---|
| 3 | Hero hold — finch drinks, booby still (long near-static) | A | **Look PASS / gore weak** | **Proves unknown #1: grit look survives i2v across 6s, zero melt.** Booby identity/anatomy hold. But finch ~5% of wide frame → drinking doesn't read + blood elongates into a thread. → use the macro seed for tight gore. |
| 8 | Raid — booby defends, finches dart in (hard action) | A | **Strong PASS** | **Proves unknown #2: hard action holds — no morph, no extra limbs, count holds.** Booby half-lifts wing + defensive gape; a finch caught mid-flight. Booby identical to clip #3 → **multi-clip identity proven.** |
| 1 | Cold-open macro gore (tight gore) | A2 | **Motion PASS / blood weak** | Macro seed fixes legibility — finch fills frame, drinking reads. But blood still animates into a dangling red **thread** even with a "not a thread" rider. |
| 1b | Cold-open macro gore, **dry-blood variant** | A2 | **PASS — fix confirmed** | Prompting the blood as a **dry matted stain that does not drip/stretch/thread, only the finch moves** → red stays a compact mark for all 6s. **Blood artifact solved.** |
| 2 | Calm interaction — booby head-turn, finch hops/perches | A | **PASS** | Booby turns head, finches hop/flutter and perch on its back (accurate behavior), grit + identity hold. One nitpick: a momentary awkward frame on a full head-**on** turn — avoid prompting head-on turns. |
| 9 | Egg-roll — object physics (climax) | B egg-nest | **PASS — object permanence holds** | The one genuinely-uncertain class. Across 6s the egg stays **ONE solid egg** — no duplication/split/morph. Booby bends bill down to tend it (action reads); finches hop around it; grit + identity hold. Minor: booby's hunched posture in the final ~1s is slightly awkward → use "settles gently over the egg" not "hunches." |

## The locked recipe (bake into every production prompt)
- **Grit prefix:** "real handheld wildlife documentary footage, 16:9, telephoto, flat overcast light,
  desaturated, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy."
- **Anatomy rider (helps):** "keep exact anatomy, no extra limbs, no morphing, count stays the same."
- **Blood rider (REQUIRED on gore shots):** "a DRY matted red bloodstain that does NOT drip, stretch,
  run, or form any thread/string — only the finch moves." (Plain "blood/wells/drips" → thread artifact.)
- **Two seeds:** wide anchor A for establishing/action/interaction; macro A2 for tight gore/drinking.
- **Avoid** prompting the booby to turn fully head-on to camera (weak i2v frame).
- **Grok output** = 1264×720, 6.04s, 145 frames. **Always strip clip audio (`-an`)** at assembly.

## Operational gotchas learned this run
- **Clipboard clobber:** a background process overwrote the macOS clipboard mid-run (pasted stray text
  into Grok instead of the PNG). Mitigation used: re-run the osascript PNG-to-clipboard **immediately**
  before each paste, and **zoom-verify the composer thumbnail attached before submitting** — else Grok
  silently does text-to-video. This worked reliably for the rest of the session.
- **Grok "New Generation" can land on a Discover post** if the click misses; verify the URL is bare
  `grok.com/imagine` (not `/post/...`) before pasting.
- **Downloads did NOT block** this session (no Chrome allow-prompt needed) — but keep an eye per
  [[feedback_chrome_download_block_ask]].

## Coverage — every distinct risk class is now tested
Long static hold ✓ · hard action ✓ · tight gore ✓ (+ blood fix ✓) · calm two-animal interaction ✓ ·
**object physics / egg permanence ✓**. Multi-clip identity ✓. Downloads autonomous ✓.

## What's left for the production pass (low risk)
- **Wide establishing/environment pan** (Scene 7 island) — needs a wide barren-lava landscape seed.
  Low risk (calm/wide motion is the easiest class; already implied by the passes above).
- **Resolution wide** (Scene 10) — low risk; an A-seeded slow pan will do.
- Then generate the remaining ~75 clips from the 3 locked seeds using the locked recipe, frame-strip
  each ([[feedback_i2v_real_physics]]), assemble in `scripts/ffmpeg_production_render.py`, gate with
  `gate_style_wbs.py` → 11/11, owner watch-through before publish.
</content>
