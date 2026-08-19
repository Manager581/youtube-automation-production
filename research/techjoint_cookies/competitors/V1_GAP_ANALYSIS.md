# cookies_v1.mp4 vs the pool — where the gaps are

_2026-08-19. `output/techjoint_cookies/cookies_v1.mp4` (1920×1080 @24, 3:04) was run through the **same** forensic pass as
the 30 competitor videos (`analyze_competitors.py --set ours` → `metrics_ours.tsv`, `forensics/cookies_v1.json`,
`sheets/cookies_v1_{grid1,grid2,hook,cuts}.jpg`), plus the timeline JSON (`output/techjoint_cookies/cookies_preview_timeline.json`:
42 shots, 10 VO blocks, 56 SFX events) and the gfx manifest (30 graphics). Visual evidence: `OURS_vs_POOL_frames.jpg`
(our frames next to the pool at matching moments) and `OURS_pullapart_strip.jpg` (the money shot, 6 frames 2:40.5–2:45)._

**Owner notes status:** the previous session has no notes — only "awful, but I can't tell how shit it is through the stalling player".
So this is the pool-vs-v1 gap list, not a notes-driven edit.

## Measured: v1 in the pool's terms
| metric | v1 | pool reference |
|---|---|---|
| length | 184 s | silent hands-only long-form 143–410 s; voiced chefs 512–550 s; experiment clips 40–52 s |
| first finished cookie on screen | 0.0 s (pull-apart) | goods-first videos: 0.0–5 s ✓ |
| hook length before process | 12.7 s (VO-driven) + title pop at 10.9 s | 6–10 s montage then process (Preppy 6.2 s, Weissman 10 s, a little calm 33 s) |
| motion inside first 0.5 s | minimal — same pull-apart pose 0.0→2.0 s (hook sheet) | decisive action in frame 1 in 30/30 (pour, drop, tear, tub inverted, towel off) |
| hard cuts / median shot | 38 / 4.0 s (12.4 per min, 5% under 2 s) | long voiced 3.4–3.5 s; long silent 3.5–5 s (or 5–15 s dissolves) — **on-model** |
| talk coverage / tempo | **46 % @ 218 wpm** (whisperx) | voiced long-form 69–90 % @ 216–223 wpm; silent family 0 % — tempo on-model, coverage in between |
| longest VO gap | 13.4 s | silent money shot 3–4 s in Weissman/FutureCanoe; whole-video silence in 10/12 long |
| baked-cookie reprise between hook and reveal | **none** (0:12 → 2:20 = 128 s of process, nothing baked) | PoW flash-forwards every ~40 s; Weissman ≈15 goods moments; Preppy dough-texture beats |
| reveal position / hold | 2:20 tray (76 %), pull-apart 2:38–2:42, total payoff 2:20–2:52 = 32 s incl. 3 tray shots | silent long-form reveal 76–88 % held 33–54 s; ladder tray→lift/turn→flip→crack→push-in stretch→cross-section→plate |
| text events | **30 graphics** (title pop, 8-pill ingredient stack 0:13–0:23, 3 rule banners, ~12 callouts, 4 spinning timers, CRISPY/GOOEY pops, recipe card) | silent long-form ≈10 static one-line captions; hands-only Shorts 0–1; **0 animated pills, 0 word pops in 30/30** |
| UI sounds | **22 "pop" SFX + 1 whoosh** on graphics | **0 in 30/30** (cuts on an audio hit ≤10 % everywhere; no stingers) |
| foley / ASMR | present and audible: sizzle hold 0:38–0:44 is the loudest passage of the film (rms 0.23), crack 2:38 (0.12), snap 2:44 (0.21) | pool mostly claims ASMR and ships near-silence — ours is **ahead** here |
| music | Pixabay bed ×0.16, dips in holds, up on card; money shot 2:45–2:52 near-silent (rms 0.01) | quiet constant bed or none; Savor lifts at reveal; silence at the pull-apart — **on-model** |
| time-skips | 4 spinning-ring timers (COOL 10 / CHILL 30 / 10–12 MIN / 5 MIN) | in-camera tray swipe, 2-s silent card, bake card + dip-to-black — no timer graphics anywhere |
| oven | 7-s through-door C28 + door shots C27/C29 | mostly elided (0–1 s); Casual uses through-glass timelapse — fine |
| end | 11-s recipe card over C36 + "see you in the next one" | 3–15 s thanks/end card; full recipe in description — fine, add description recipe |
| hands identity | cream knit sleeve + gold ring + pale nails consistent across all hands shots (grid) | sleeve/nails/ring anchors are exactly the pool convention ✓ |

## The gaps, ranked by how much they would explain "awful"

### 1. The money shot does not deliver "gooey" (RED — needs new clip(s), cannot be fixed in the assembler)
`OURS_pullapart_strip.jpg`: the pulled halves show a baked crumb with two melted chips and **thin wire-like chocolate threads**
— no molten mass, no soft under-baked centre, no ooze. Compare Ashley's Nutella stretch (`cards/VHutIcveQDQ.md` 60.5 s), Iram's
chocolate pull (9–11.5 s), Foodporn's molten pools over the rack (79 s), Lilac's molten half rotated to lens (3:16–3:40). Every
one of those is a thick mass smearing/pooling; ours is strings. The "CRISPY" edge snap (2:44) shows crumb, not a shattering edge.
The whole title promise rests on these two shots. This is the first thing to regenerate: one new seed pair (molten centre bent
open, thick chocolate pool smearing; crisp edge cracking with visible shards) → i2v on the paid account — **ask before spend**.

### 2. The look reads "AI food stock", not "ultra-real iPhone" (RED/AMBER — partly fixable in the grade, fully only by re-seeding)
`OURS_vs_POOL_frames.jpg` row 1 vs rows 2–3: every one of our frames is saturated gold, glossy, shallow-DoF, window light +
marble + flowers + milk glass — the same "pretty render" band the WBS teardown flagged as the AI tell. The pool's iPhone-real
winners (Casual on beige tile, Ashley on quartz under artificial light, Birchberry, Iram's bare white surface, Mad About Food's
real kitchen) are flatter, cooler, imperfect, and **one subject per frame**; our cookies are uniformly perfect and the stack at
0:08/2:48 looks like a product render. v2 partial fix in FFmpeg (no regen): desaturate ~10–15 %, pull warmth, lift blacks, add
fine grain + 1–2 % handheld drift; full fix = re-seed with the "grit" prompt (plain counter, no styling props, slight mess, flat
light) — owner's call and credit spend.

### 3. Graphics + UI sounds read "template" (RED — assembler-only fix, free)
30 graphics and 23 pop/whoosh cues in 184 s against a pool where 30/30 videos have zero animated pills and zero UI sounds.
The 8-pill ingredient stack (0:13–0:23) alone has more text on screen than any pool video at any moment; spinning timers and
CRISPY/GOOEY word pops have no precedent in the set. v2: delete `pop`/`whoosh` cues; replace the pill stack with one small
static caption per ingredient shot (grams + cups, a little calm / PoW register); keep the 3 rule banners as small captions;
timers → in-camera tray swipe or 2-s silent card; drop the word pops (the SFX crack/snap already makes the point).

### 4. No baked cookie for 128 s (RED — assembler-only fix, free)
Between the hook and 2:20 nothing baked appears. Pool silent long-form reprises a finished-cookie CU every ~40–90 s (PoW
81/100/123 s) and Weissman ~15 times. v2: drop a 1.5–2 s flash of C33/C34/C35 at ~0:50 (after brown butter) and ~1:45 (after
chocolate), or a push-in on the dough macro C21 as a texture beat (Preppy's substitute).

### 5. Hook is static and long (AMBER — assembler fix, plus one trim)
Frame 1 holds the same pull-apart pose for ~2 s with the strings already stretched; the pool's frame 1 always has a decisive
motion inside 0.5 s (tear, pour, tub inverted, towel whipped off). The hook then runs 12.7 s because the spoken hook is 12 s, and
the title pop + whoosh land at 10.9 s (no precedent). v2: open on the instant of separation (trim C33 to start ~0.5 s before the
halves part; if the clip has no pre-separation frames, open on the edge snap C34 — it has motion), cut the title pop to a small
caption, and consider tightening the spoken hook block so process starts by ~8–9 s.

### 6. Reveal ladder incomplete (AMBER — partly assembler, partly new clips)
Ours: tray (×3 similar shots 2:20–2:30) → salt → tray rest → pull-apart 4 s → snap 4 s → stack 4 s → card. Pool ladder adds
lift-and-turn to lens (Iram 4–7 s), flip to show the base (Ashley 54 s), push-in to the stretch instead of a cut, cross-section
/ stack (Weissman, PoW). v2 in the assembler: cut two of the three tray shots, let the pull-apart run its full 6 s, add the
flash-forward reuse; missing shots (lift/turn, flip/base, cross-section) = 2–3 new i2v clips.

### 7. Minor
- C01 ingredient flat-lay (0:13–0:23) is a medium overhead, not a close-up (owner rule); the three top-down pan shots 0:28–0:42
  are the same vantage for 14 s (clip-variety rule).
- Continuity: plate of yellow items appears at screen-left in the pull-apart (2:40) and nowhere else; the hook's tray shot (C29)
  reappears at 2:20–2:26 and a near-identical tray on the counter fills 2:28–2:36 (5 tray frames in the payoff).
- Not a gap: voice tempo (218 wpm measured) matches the voiced long-form band; foley is louder/better than the pool; music, silence
  at the money shot, hands identity, cut rhythm and length are all inside the pool's norms.

## What v2 can do without a single new generation (in `assemble_cookies.py` / `render_gfx.py`)
1. Remove all `pop` + `whoosh` SFX; drop CRISPY/GOOEY word pops and the animated title pop (small static caption instead).
2. Ingredient pill stack → one static caption per ingredient shot; banners → small captions; spinning timers → 2-s silent card or tray swipe.
3. Insert baked-cookie flashes at ~0:50 and ~1:45; cut two tray shots from the payoff; extend pull-apart hold; full 6 s on C33.
4. Grade pass: −10–15 % saturation, −warmth, lifted blacks, fine grain, slight drift — to pull the frames toward the phone-real band.
5. Open on the separation instant (trim C33) or on C34's snap; tighten hook to ~8–9 s.
6. Full recipe pasted into the description; thumbnail = the stretch macro (once a real gooey clip exists).

## What needs new clips (paid Grok account — ask first)
- **Molten-centre pull-apart** (thick chocolate pool / soft centre, halves bent not snapped) and **crisp-edge shatter** — the two promise shots.
- Lift-and-turn to lens; flip to show the browned base; cross-section/stack — the reveal-ladder shots the pool always has.
- (Optional, owner's call) re-seed the look toward iPhone-real: plain counter, flat light, no flowers/candles/marble.

---
## v2 closure (2026-08-19 — `output/techjoint_cookies/cookies_v2.mp4`, 3:15, −16.2 LUFS)
Remade from scratch: 36 new phone-real seeds (ChatGPT thread `6a85fcec`, grit standing rules) → 36 Grok 720p i2v clips
(11 × 10 s, 25 × 6 s, paid account) + the 2 prototype clips (P2→C09, P3→C23) → `assemble_cookies.py --variant v2`
(`cookies_v2_config.py`, `render_gfx_v2.py`). Every clip frame-strip QA'd (five fingers, grips, physics; C12 trimmed to
3.5 s before the yolk lands in the wrong bowl; C16 seed redone without chocolate).
| gap | v1 | v2 |
|---|---|---|
| money shot | thin wire strings over dry crumb | bend-open, molten pools on both faces, one drip that lands and pools, sub-second thread only; 6.5 s hold, VO silent 4.3 s after "look at that" |
| look | saturated gold, marble/flowers/milk glass | flat indoor light, neutral, bare quartz + tile, crumbs/smears, faint grain — checked against Ashley/Birchberry/Casual frames |
| graphics + UI sounds | 30 graphics, 22 pops + whoosh | 18 small static captions (one register, bottom-left) + recipe card; **0 pops/whoosh** |
| baked-cookie reprise | none for 128 s | G1 @0:54 (open halves), G2 @1:54 (stack) |
| hook | static pose 2 s, 12.7 s + title pop | motion in frame 1 (drip falling), 6 goods flashes, tiny claim caption on the stack only |
| reveal ladder | tray ×3 → salt → tray → pull → snap → stack | tray out → tap → salt → rest → lift & turn → flip base → bend-open (hold) → snap on "Crispy edge" → stack on "gooey middle" → rack + card |
| measured | 38 cuts, med 4.0 s, talk 46 % @218 wpm, onsets 10 | 37 cuts, med 4.0 s, talk 43 % @220 wpm, onsets 18, longest hold 23.5 s (money shot + card) |
Residual tells I know of: C37's edge-on moment reads thin; C24 fridge milk carton has legible label text; C13 vanilla bottle label; oven interior light is warm by nature.
