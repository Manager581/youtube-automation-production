# Chocolate-chip-cookie YouTube teardown — top 10 videos (<10 min, last 12 months) + top 20 Shorts (last 24 months)

_Built 2026-08-19. Every number below came from a tool call (yt-dlp metadata, ffmpeg scene/audio analysis,
whisperx transcripts, contact sheets, full-res frame pulls). Per-video forensic cards (timestamped, ≤700 words)
are in `cards/<id>.md`; sheets in `sheets/`; measured metrics in `metrics_long.tsv` / `metrics_short.tsv`;
metadata in `catalog.tsv`. Method + scripts: `collect_candidates.py`, `analyze_competitors.py`, `build_catalog.py`,
`REVIEW_BRIEF.md`._

## 0. How the sets were chosen (and what got excluded)

- **Long-form**: 16 query variants × YouTube search `sp=` filters (sort by views · this year · <4 min / 4–20 min) →
  1,182 unique ids → 177 topic-matched candidates metadata-checked → landscape, <600 s, uploaded ≥ 2025-08-19 → ranked by views.
- **Shorts**: Shorts don't surface in normal search results (7 of 2,601 rows). Pulled the "Shorts" chip of the results page
  via its innertube continuation (14 pages × 16 queries → 2,069 unique Shorts) → topic filter → metadata for the top 181 →
  vertical, ≤180 s, uploaded ≥ 2024-08-19 → top 20 by views (the #20 cut is 4.5M; nothing below row 54 could displace it).
- **Excluded from the long top-10 (listed, downloaded, carded as `ad/brand`, not counted as creator format):**
  Piper's Gold product-launch spot `vYA2RDDWfOg` (13.9M views on a 6.6K-sub channel, 29 likes — paid), Nestlé Toll House ×
  Peyton Manning spot `DzV36K1H7RY` (2.2M), Crumbl weekly-menu promo `XQvB5w_cHHA` (3.8M). Near-miss: Sugar Spun Run
  `9ThezB21fhA` 1.25M but 10:55 (>10 min). Older giants excluded by the 1-year rule: Tasty 22M (2017), Cooking Foodie 10M (2020).
- **Shorts excluded by the 2-year rule (for context):** Fitwaffle 76M/22M/13M (2022–23), Turkuaz Kitchen 73M (2023),
  DanCookedIt 36M (Mar 2024), Tasty "50 recipes" 28M (2023), audreysaurus 22M (2021), Nick DiGiovanni 15M (2021).
- Added 2 "next-in-line" long-form recipes (#11 Pinch Of Warmth brown butter, #12 Cookie Kitchen Tv) because 4 of the
  literal top 10 are one channel's repeat format — the main deliverable is still 10 + 20.

## 1. Measured tables

### LONG-FORM (<10 min, ≤1 yr, landscape) — ranked by views
| # | id | channel (subs) | views | dur | upload | talk% | wpm | hard cuts/min | med shot | 1st cut | <2 s% | longest hold | onsets/min | like% |
|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `26p-npt4fTI` | Casual Cooking (264K) | 10.3M | 0:41 | 2025-10-24 | 0 | – | 7.3 | 5.6 | 1.1 | 17 | 18.0 | 13.1 | 2.77 |
| 2 | `HfNhp_YHNxE` | Casual Cooking (264K) | 1.7M | 0:40 | 2025-10-27 | 0 | – | 10.5 | 2.9 | 1.9 | 25 | 13.6 | 7.5 | 2.89 |
| 3 | `ZLULwy2cXVE` | Joshua Weissman Recipes (856K) | 1.3M | 9:10 | 2025-12-22 | 90 | 223 | 11.6 | 3.4 | 5.8 | 24 | 20.6 | 0.1 | 3.03 |
| 4 | `AFBr-AnTtXE` | Casual Cooking (264K) | 1.2M | 0:52 | 2025-09-16 | 0 | – | 4.6 | 12.3 | 4.4 | 0 | 17.9 | 10.4 | 2.62 |
| 5 | `DXoLCKDcwbk` | Casual Cooking (264K) | 700K | 0:42 | 2025-10-26 | 0 | – | 10.0 | 2.3 | 10.2 | 50 | 13.1 | 8.6 | 2.80 |
| 6 | `PLIOTjj_gmY` | Lilac's kitchen (86K) | 657K | 3:42 | 2025-11-28 | 0 | – | 0 (≈14 dissolves) | – | – | – | 222 | 0.5 | 5.61 |
| 7 | `1gcLatHJa8o` | a little calm (374K) | 566K | 6:50 | 2025-09-17 | 0 | – | 6.9 | 3.6 | 5.7 | 8 | 71.2 | 1.6 | 3.43 |
| 8 | `qK-ZOlrv2BM` | Preppy Kitchen (6.2M) | 332K | 8:32 | 2025-10-07 | 69 | 216 | 12.8 | 3.5 | 3.5 | 23 | 19.9 | 0.1 | 2.38 |
| 9 | `f4My3oGalqo` | Pinch Of Warmth (42K) | 220K | 5:00 | 2026-01-23 | 0 | – | 0.2 (≈35 dissolves) | – | 2.6 | – | 297 | 0.2 | 3.38 |
| 10 | `3OHIS5IoRtA` | Savor Easy (1.3M) | 196K | 2:23 | 2026-01-16 | 0 | – | 0 (≈26 dissolves) | ≈5 | – | – | 143 | 2.5 | 2.20 |
| +11 | `8909Nv2EqhQ` | Pinch Of Warmth (42K) | 245K | 4:30 | 2026-04-22 | 0 | – | 0.9 (≈20 dissolves) | – | 47.5 | – | 138 | 1.6 | 4.10 |
| +12 | `kS_Clm3FA7o` | Cookie Kitchen Tv (16K) | 182K | 5:07 | 2026-02-18 | 0 | – | 11.5 | 3.5 | 8.5 | 27 | 25.3 | 0.8 | 3.87 |

### SHORTS (vertical, ≤3 min, ≤2 yr) — ranked by views (likes are hidden on Shorts)
| # | id | channel (subs) | views | dur | upload | talk% | wpm | true shots (est.) | reveal t (%) | text events |
|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|
| 1 | `u2XhUfvMC7E` | Koreanosh (4.4M) | 99.3M | 0:23 | 2025-05-15 | 26 | 200 | ≈20 (1.1 s) | cookies 4.75 s (no single reveal) | 0 |
| 2 | `9t3tFhoOOps` | Hey It's Honeysuckle (3.0M) | 21.5M | 1:19 | 2025-06-07 | 100 | 222 | ≈38 | 64 s (81%) | ≈200 word chunks |
| 3 | `hv5qFlTJ6Fs` | FutureCanoe (4.8M) | 18.8M | 2:00 | 2025-01-27 | 89 | 223 | ≈45 | 103 s (86%) | source cards only |
| 4 | `obKCe-OP3rQ` | Birchberry (82K) | 17.7M | 0:26 | 2025-03-20 | 0 | – | ≈20 (1.2 s) | 24.25 s (95%) | watermark only |
| 5 | `T41Oe_H4VCA` | Ashley Markle Treats (430K) | 16.1M | 1:01 | 2025-05-05 | 0 | – | 17 (1.6 s) | 43 s (70%) | 1 |
| 6 | `eNzWAWN2hsM` | Iramsfoodstory (240K) | 14.7M | 0:16 | 2025-11-01 | 0 | – | ≈8 | 0 s (reveal-first) | 0 |
| 7 | `VHutIcveQDQ` | Ashley Markle Treats (430K) | 13.0M | 1:06 | 2025-04-16 | 0 | – | 18 (2.2 s) | 60.5 s (92%) | 1 |
| 8 | `NbAaf79K4f4` | Mad About Food (31K) | 12.9M | 0:29 | 2026-02-28 | 14 | – | ≈26 (1 s) | 24.6 s (84%) | 4 (0–4.4 s) |
| 9 | `W5GSWMin8Fw` | Foodporn (2.9M) | 11.6M | 1:22 | 2026-03-18 | 0 | – | ≈75 (1 s) | 70 s (85%) | 1 |
| 10 | `E5t1qq6u0hI` | Ashley Markle Treats (430K) | 10.2M | 1:13 | 2025-05-08 | 0 | – | 12 (5 s) | 67 s (92%) | 1 |
| 11 | `hUCchS2Rs9Y` | Jesha Ann Stevens (1.9M) | 8.6M | 0:34 | 2024-10-01 | 25 | 128 | ≈30 (1 s) | 26 s (76%) (loaf, not cookies) | 0 |
| 12 | `K5XJOJQ_z9E` | Tayyaba kiran (1.4M) | 8.2M | 2:59 | 2025-06-29 | 76 | 282 | ≈85 | 160 s (89%) | 0 |
| 13 | `n4_v0hhO4JA` | Jose.elcook (5.1M) | 7.1M | 1:10 | 2025-04-11 | 91 | 242 | ≈30 (2 s) | 0 s + 57 s (81%) | 5 |
| 14 | `-02rCdlWQwA` | Jenny Hoyos (12.4M) | 6.5M | 0:13 | 2025-06-09 | 82 | 265 | 0 (one take) | plate from 0 s (skit) | ≈12 |
| 15 | `S--5x7WFE2E` | Tamil minivlog (1.8M) | 6.4M | 1:00 | 2025-08-06 | 61 | 356 | ≈45 (1.2 s) | 50.6 s (84%) | 0 |
| 16 | `Bnfz-vJg1AI` | miso butter baby (17K) | 5.7M | 0:39 | 2024-10-18 | 0 (TV dialogue) | – | ≈10 | 28.8 s (73%) | watermark only |
| 17 | `TlryZMc6nmw` | Chuchington (2.8M) | 5.5M | 0:38 | 2024-12-07 | 75 | 238 | ≈13 | 29.1 s (76%) parody | ≈33 |
| 18 | `6elCoGd6g8w` | Louis Gantus (2.5M) | 5.0M | 0:34 | 2025-03-07 | 99 | 263 | ≈9 | 23.8 s (71%) | ≈68 one-word |
| 19 | `0uu4E3SaMz4` | The Hayeks (4.0M) | 4.6M | 0:52 | 2025-05-16 | 0 | – | ≈25 | 43.4 s (84%) | 1 label |
| 20 | `KPrr6x8lwJM` | TheContrarianMoney (320K) | 4.5M | 0:30 | 2026-01-12 | 100 | 259 | ≈30 (0.9 s) | 0 s + 26 s (88%) | ≈128 one-word |

Measurement caveats: the scene-cut detector undercounts same-framing jump cuts and dissolves (true counts above come
from the cards' frame strips); Shorts downloads may lack a Shorts-picker music track (silent files flagged in cards).

## 2. How each one comes together (1–2 lines; full construction in `cards/<id>.md`)

**Long-form**
- **Casual Cooking ×4** (#1,2,4,5): "what if you bake a whole tub/tube of store dough like this" — handheld overhead phone, hands-only (grey sleeves), beige-tile kitchen, **no voice**, the **same music track in all four** (audio cross-corr 0.96–0.98), 4–5 white top-centre captions (`* Timelapse…` → `Baked at 300°F for 1 hour 40 minutes` → verdict → `Please consider giving the video a 'like'`), through-glass bake timelapse, **reveal at ~50%**, 2–6 s hero hold, then break. Frame 1 = the premise object (tub / empty pan / sealed tube). Only the vessel varies. Thumbnail "What will happen?". 1-line description + Amazon affiliate.
- **Weissman** (#3): face-first 5.8 s, then a silent 4.3 s cookie montage (pull-apart/plate/cross-section) **before the claim**, "secret ingredient" open-loop (14 s → 166 s), 223 wpm, 106+ cuts (93% on a word), 15 "goods" reprises, `FINAL TASTING` at 85.6%, cross-section bookend 9:06.
- **Lilac's kitchen** (#6): knife already in the baked cookie at 0.0, halves parted at 4.5 s; bilingual tiny captions carry the recipe; one 2-min locked bowl; **reveal held 54 s** (76%→end); file is −57 LUFS (ASMR claimed, not shipped). Highest like rate in the set (5.6%).
- **a little calm** (#7): **33-s proof montage** (9 angles, pull-apart at 24.5 s) under a serif title caption; locked overhead, gingham + candles; two caption registers (white facts / yellow asides); 2-s silent sage cards as time-skips; one loud ASMR spike (chop 216 s) in a −33 LUFS bed; reveal 88% held 33 s; 15-s end card.
- **Preppy Kitchen** (#8): finished plate 0–0.8 s then **6 shots in 6 s** under "Hey, I'm John…"; 216 wpm; 10 gram-captions (the recipe card is the captions); comment card as social proof 3:45; baked cookies vanish 0:01→8:02 (94%), filled by dough-texture beats; kid taste-test.
- **Pinch Of Warmth ×2** (#9, +11): hero in frame 1 (rack / plate + name caption) → process by 2–3 s; gloves + knit sleeves; bold sans **subtitles on ~90% of frames** (grams + cups); dissolves every 9–15 s; **numbered flash-forward CUs mid-process** (81/100/123 s); bake = caption + dip-to-black; post-bake "bakery" beats (ring-rounding, extra chocolate) then a **payoff ladder lift → tear → cross-section → plated** over 21–25 s; gated silence elsewhere.
- **Savor Easy** (#10): bowl of minis poured at 0–4.5 s, title card 1–4.5, break 6–8 s; ~26 dissolves, **one caption per shot**, metric + imperial; bake card with ⏰ at 1:58; same pour bookends the end (2:06); watermark every frame.
- **Cookie Kitchen Tv** (+12): wordless cold open on the finished platter + bite inside 8.5 s; candle-lit ingredient insert → pour cut, 10 metric+cup captions in italic serif; oven fully elided (1 s); no music, no voice; fills ×4 as the "new style" payoff.

**Shorts**
- **Koreanosh** (#1, 99M): not a cookie video — a couple's 10-dessert "present → bite" game, 1.1-s units, VO names only; cookies occupy 4.75–7.25 s. Eyes-closed static "present" frame, then the bite crowds the lens.
- **Honeysuckle** (#2): host talking from 0.05 s with the **source's finished dough as a PIP at 0.25 s** (`@FITWAFFLE`), 1–3-word caps captions pinned above the PIP, source-vs-mine ping-pong, reads comments over B-roll, ECU bite 71–76 s, "10/10".
- **FutureCanoe** (#3): opens on **Tasty's own money shot** + NPC face, 2 s silent, borrowed claim card "We Tested 50…", link-in-bio rant via screen recordings, tip cards between his attempts, **4-s silent pull-apart** at 104.5 s, "9.5/10".
- **Birchberry** (#4, 82K subs → 17.7M): locked overhead, butter into pan at 0.0, Nutella jar already in frame, "The Sounds of Baking" watermark, **same-frame step jumps every ~1.2 s**, slide-on wipes as punctuation, foley + soft bed, pull-apart 24.75–25.6 s to hard end.
- **Ashley Markle ×3** (#5,7,10): **identical template** — empty pan/board on frame 1 + verbatim persona caption `pov: you're a little treat after dinner every night type of girl` held 7–12 s, brand pack held to lens at 1.5–2.5 s (Pillsbury / Nutella / Biscoff), **no music, no callouts**, in-camera **tray swipe** skips the bake, reveal at 70/92/92%, push-in to the stretch (= thumbnail), plate dragged off-frame, no CTA. Recipe in description.
- **Iramsfoodstory** (#6, 16 s): **reveal-first loop** — finished thick cookie lifted by spatula at 0.0, raised to lens and turned 4–7 s, break 8 s, chocolate strings 9–11.5 s, hard cut to process at 12 s, ends mid-scoop (loop bait). Zero text, zero audio design.
- **Mad About Food** (#8, 31K subs → 12.9M): face + pretext 0–4.4 s ("neighbors gave us mac and cheese in this bowl… let's fill it with cookies"), then **25 s of silent, uncaptioned process at ≈1 cut/s**, ring-scoot on hot cookies, ECU pull-apart with face behind at 84%, cookies into the bowl = payoff.
- **Foodporn × chef** (#9): `POV: You're creating a michelin ⭐ chocolate chip cookie` over a water-pour gag (0–3.2 s), then **77 scene changes, no words**, 129-bpm bed + foley, product withheld to 70 s, two-hand pull-apart over the rack closes (= thumbnail).
- **Jesha Ann** (#11): towel whipped off raw dough at 0.5–1 s (= thumbnail), "Morning, we're making some bread" (it's a chip-studded loaf + whipped butter), ≈1-s MS↔overhead ping-pong, 24.5 s music-only middle, "offer to lens" ×3.
- **Tayyaba** (#12) / **Tamil minivlog** (#15): day-in-the-life; cookies 30–66% of runtime, uncaptioned non-English VO at 282–356 wpm, metronomic ≈1.2-s cuts, reveal at 84–89% with a 4–9 s VO-free hold; thumbnails = tray-to-lens.
- **Jose.elcook** (#13): giant cookie in frame 1, **torn at 1.4 s, dunked at 3.7 s**, banter at 242 wpm, text only for the insult (`WEAK`/`OLE`) and numbers (`7-8oz`), second tear at 57 s, "Save this recipe."
- **Jenny Hoyos** (#14): one 13-s POV take — plate of cookies + fake `ACCEPT`/`REJECT` pills; colour-coded speaker captions; escalation by push-in/hand-over, not cuts.
- **miso butter baby** (#16, 17K subs → 5.7M): **four ingredient drops in 3 s** (brown sugar 0.0, white 1.5, butter 2–3, whisk 3.5), soundtrack = a Gilmore Girls dialogue clip, watermark only, ring-scoot at 30–32 s (= thumbnail), pull-apart 36–37 s.
- **Chuchington** (#17): claim sentence at 0.07 s + punch-in on the punchline at 1.87 s; 18-s single take built on a repeat joke; anti-climax reveal 1 s, payoff = wordless reaction ECU.
- **Louis Gantus** (#18): empty bowl + hands + `I'M` at 0.0, 263-wpm deadpan VO with one-word caps at ~2/s, **prop-wipes under a locked overhead** instead of cuts, reveal staged as action (cookies placed one by one), tear on "DISAPPOINT…BITING", face only for "10 out of 10".
- **The Hayeks** (#19): `S'more cookies 🍪` label from frame 0, **six same-angle jump cuts in 2.6 s**, branded packs held to lens replace ingredient text, near-silent, wrapped-cookie thumbnail moment at 47–49 s, ends ON the pull-apart.
- **TheContrarianMoney** (#20): goods at 0.0, **tears at 2.2 and 4.3 s** under "best and only… you'll ever need" + "mom's famous… she finally said I can share them", word-by-word serif captions, ≈1 shot per VO verb, dunk + bite before step one, second tear 26 s, "Recipe's in the caption."

## 3. Patterns across the 30 (evidence = card timestamps)

### 3.1 Two hook grammars — both win; what they share is motion + one legible subject in frame 1
- **Goods-first** (finished cookie + tear inside ≤5 s, reprised later): long 8/12 open on finished product (Lilac's 0.0, a little calm 0.0, Preppy 0–0.8, PoW ×2 0.0, Savor 0.0, Cookie Kitchen 0.0; Weissman via 5.8-s montage); shorts 7/20 (Iram 0.0, Jose 0.0/tear 1.4, Contrarian 0.0/tear 2.2, Honeysuckle PIP 0.25, FutureCanoe 2.0, Hoyos plate 0.0, Koreanosh 4.75).
- **Process-rush** (first ingredient *action* in frame 1, a new action every ~1 s, product withheld to 70–95%): Birchberry (butter 0.0), miso (4 drops in 3 s), Hayeks (6 jumps in 2.6 s), Gantus (bowl + `I'M`), Ashley ×3 (empty pan + persona caption), Foodporn (POV card), Casual ×4 (premise object), Mad About Food (pretext then rush).
- In **both**, something moves within 0.5 s (pour, drop, lift, towel-off, tub inverted) and there is exactly one subject. Nobody opens on a logo/intro card; the only opening title cards are small captions (Savor 1–4.5 s, a little calm 0–31 s, Foodporn 0–3.2 s, Hayeks tiny label).
- The claim, when spoken, lands by 0.1–0.3 s (Preppy 0.13, Jose 0.13, Contrarian 0.11, Gantus 0.05, Chuchington 0.07) and is a superlative/permission/pretext sentence ≤5 s; Weissman withholds it behind 4.3 s of silent cookie porn.

### 3.2 Hands-only is not a handicap — it is the small-channel outlier format
- Long: 10/12 never show a face. Shorts: 10/20 hands-only. Every **small-channel breakout** is hands-only + silent: Birchberry 82K → 17.7M, Ashley 430K → 10–16M (×3), Iram 240K → 14.7M, miso 17K → 5.7M (Mad About Food 31K → 12.9M shows a face for 4.4 s only).
- Hands carry identity: French tips + navy sleeve (Ashley ×3), pink fuzzy sleeve + white almond nails (Hayeks), pale pink manicure (Birchberry), sage sleeve + thin ring (a little calm), white gloves + knit sleeve (PoW, Cookie Kitchen), grey sweatshirt (Casual ×4). Our cream sweater + gold ring + pale-pink nails is squarely in this convention.

### 3.3 Voice: either none, or FAST — nothing in between
- Long: 10/12 have **zero narration** (music bed or near-silence). The 2 voiced ones run **216–223 wpm** at 69–90% coverage with 11–13 cuts/min and cuts on words (67–93%).
- Shorts with VO (11/20): **222–282 wpm** (Tamil 356), 75–100% coverage; 6 of those pair it with word/phrase kinetic captions (Honeysuckle, Gantus ~2 words/s, Contrarian one word at a time, Hoyos colour-coded, Chuchington, Jose sparse).
- Silent shorts (9/20) ship with near-silence or a faint bed; only Birchberry/Foodporn foreground foley. Many claim ASMR and ship −40 to −57 dBFS (Lilac's, PoW gated, Hayeks) — **real foregrounded crack/snap/sizzle is rare in the pool.**
- Nobody cuts to SFX stingers: cuts-on-onset ≤10% in 29/30; no whooshes. Music, where present, is a quiet constant bed (a little calm −33 LUFS; Casual same track ×4 peaking at 30 s; Savor dips under the bake card and lifts at the reveal). Weissman/FutureCanoe/Tayyaba go **fully silent for 3–4 s at the pull-apart**.

### 3.4 Pacing: ≈1 s per action in Shorts; 3.5 s median (or 5–15 s dissolves) in long-form
- Shorts effective shot ≈1–1.5 s (Birchberry 1.2, Foodporn 1.0, Contrarian 0.9, Jesha 1.0, Tamil 1.2, Mad About Food 1.0, Koreanosh 1.1); slow end = Ashley Biscoff 5 s median (each shot = one hand doing one legible thing to camera). Jump cuts on the same framing replace cuts (Birchberry, Hayeks, Iram, Tayyaba).
- Long voiced: 3.4–3.5 s median, 11–13 cuts/min, hook = 1 s/shot montage (Preppy 6 in 6 s). Long silent: a little calm 3.6 s median with a 71-s hold; Cookie Kitchen 3.5 s; PoW/Savor/Lilac's dissolve every 5–15 s (Lilac's holds one bowl 2 min — tolerated, but the slow end).
- Time-skips are in-camera or a card, never a "timer" graphic: tray swipe raw→baked (Ashley ×3, Gantus prop-wipes, Iram), slide-on wipes (Birchberry), 2-s silent sage card (a little calm), bake card + dip-to-black (PoW, Savor), through-glass timelapse (Casual). Oven footage is mostly elided (Cookie Kitchen 1 s, PoW 0 s, Ashley 0 s).

### 3.5 Reveal grammar (the one thing every recipe video stages the same way)
- Sequence: tray/rack wide → **lift to lens and turn** (Iram 4–7 s, PoW, Jesha "offer to lens") → flip to show the base (Ashley Nutella 54 s, Casual underside 29 s) → crack/tear → **push in to the stretch, don't cut** (Ashley Biscoff 63.5–69 one take) → cross-section / stack (Weissman 498–503, PoW 262) → plated. Recurring "pro" beat: **ring-scoot on hot cookies** (Mad About Food 23 s, miso 30–32 s = thumbnail, Foodporn 71 s, PoW 4:00).
- Position: long silent 76–88% and **held 33–54 s** (a little calm 32.7 s, Lilac's 54 s, PoW 48 s); shorts 70–95% held only 1–4 s (Birchberry 0.85 s); voiced shorts bracket it (goods at 0–5 s AND at 81–88%).
- Reprise: Weissman ≈15 goods moments; PoW flash-forward CUs at 81/100/123 s; Preppy substitutes dough-texture beats; a little calm front-loads 33 s then nothing until 88%.

### 3.6 Text: captions are the recipe card in silent long-form; Shorts use 0–1 text events
- Silent long: one small caption per shot, grams + cups, white serif/sans, bottom-left/centre (a little calm white facts + yellow asides; PoW bold sans subtitles on 90% of frames; Cookie Kitchen italic serif top-centre; Savor rounded sans lower third; Lilac's bilingual tiny). Casual: a 4–5-caption template. Weissman: ~10 section cards never over the face; Preppy: 10 gram-captions + a comment card.
- Hands-only shorts: **zero ingredient callouts** — the brand pack held to lens replaces text (Ashley 1.5 s, Hayeks 16/21/28 s, Chuchington), the full recipe lives in the description (Ashley ×3, Iram 1,377 chars, Contrarian), and the only text is a frame-1 persona/claim line (Ashley 7–12 s, Foodporn 3.2 s, Hoyos POV header) or a tiny watermark (Birchberry, miso, Hayeks, Savor).
- Voiced shorts: kinetic captions (one word to 3 words, centred, caps or lower-case, colour-coded by speaker in Hoyos), refreshed every 0.25–0.5 s.

### 3.7 Packaging
- Titles: superlative/claim ("The Best X Ever", "Thickest… Ever", "best and only… you'll ever need"), "viral X recipe", style+adjective noun phrase + emoji ("Bakery style thick…", "Salted Brown Butter…🍪✨"), "what if/like this..", "Testing / Supposedly the BEST from @brand", lowercase ♡ "Bake With Me" series tags.
- Thumbnails: product fills 35–80%; the **pull-apart/stretch macro IS the thumbnail** in ≥8 (Ashley ×2, Foodporn, FutureCanoe, Gantus, Iram, Jose, Birchberry); text in ~6 (Casual "What will happen?", calm, PoW claims, Contrarian, Preppy); faces in 6/35. Shorts mostly auto-frame their money shot — so the money shot is staged to be frame-grabbable (held to lens, centred).
- Descriptions: every silent recipe channel pastes the **full recipe** (calm, PoW ×2, Savor, Lilac's, Iram, Ashley ×3, Contrarian, Cookie Kitchen); talking chefs link out; Casual = 1 line + Amazon affiliate. Like rate (long): 2.2–5.6%; highest = Lilac's 5.6%, PoW 4.1%, Cookie Kitchen 3.9% (silent, hands-only, recipe-in-description); lowest = Savor 2.2%, Preppy 2.4%.

### 3.8 Length and format vs views
- The 40–52-s "experiment" landscape videos (Casual ×4) took 5 of the top-5 creator slots (0.7–10.3M). 9-min talking chefs: 0.33–1.3M. The 2:23–6:50 silent hands-only recipes: 180K–660K. **There is no voiced 3-min hands-only video in the set** — the voiced hands-only comparables are Shorts (Contrarian 30 s, Gantus 34 s, Jose 70 s).
- Curiosity/experiment framing ("what if", "testing", "supposedly the best") out-pulls straight recipes at equal production: Honeysuckle 21.5M and FutureCanoe 18.8M re-test someone else's viral recipe; Casual's premise is a store product mis-used.

## 4. What this means for the TechJoint cookie video (v1 → v2, within the owner's locks)

Locks respected: hands-only, iPhone-real, close-ups, crispy-outside/gooey-inside, Jessica VO one pass (no re-roll), reuse existing clips/assembler.

1. **Hook (0–8 s)**: v1 already opens on the pull-apart ✓. Pool standard = motion inside 0.5 s + 3–4 goods shots in 0–5 s (Contrarian tears at 2.2/4.3 s, Jose tear 1.4 s). Keep the flash-forward hook but make every hook shot a *texture proof* (crack → stretch → edge snap → cross-section), end the hook by ~6–8 s, and demote the big `CRISPY OUTSIDE · GOOEY INSIDE` pop to a small caption (pool never uses a big title pop; the claim is spoken or a one-line caption).
2. **Reprise the goods**: v1 shows nothing baked between 0:10 and 2:20. PoW/Weissman reprise a finished-cookie CU every ~40–90 s. Cut a 1.5–2 s flash-forward (C33/C34 trims) at ~0:50 (after brown butter) and ~1:45 (after chocolate).
3. **Reveal ladder + hold**: extend 2:30–2:48 to the pool's grammar — tray → lift & turn to lens → flip (crisp base) → crack (loud) → push-in stretch (no cut) → cross-section/stack → plate; silent long-form holds the reveal 33–54 s; ours is 18 s. Add the flip + cross-section (we have C33/C34/C35 + the 10-s C36 to mine) and let the stretch run.
4. **Text**: v1's ~14 callouts + 4 timers + 3 banners + recipe card is heavier than anything in the pool. Silent long-form = one small caption per shot (grams + cups). Recommend: one caption register (small white sentence-case, grams + cups), keep the 3 rule banners as small captions, drop spinning-timer graphics (pool uses a 2-s card or an in-camera swipe), keep the recipe card (pool puts the full recipe in description — do both).
5. **Time-skips**: replace timer-spins with the in-camera tray swipe (raw tray out / chilled or baked tray in on the same framing) or a 2-s silent card (a little calm).
6. **Audio**: foreground the real crack/snap/sizzle — the pool claims ASMR and ships silence; keep the bed quiet (−33 LUFS range) and **drop VO + music to silence for 3–4 s at the pull-apart** (Weissman/FutureCanoe); no SFX-on-cut. v1 already has the silent money shot ✓ — make it longer.
7. **VO tempo (flag, owner's call)**: every voiced comparable runs 216–282 wpm; Jessica is ~155–160 wpm at ~65% coverage. If the note is "voice drags", `atempo 1.08–1.15` on the existing take is a no-re-roll option; otherwise the silent-family precedent says VO can be much sparser than v1's.
8. **Cut a Short from the same clips** (zero new generation, biggest upside in the data): either reveal-first 15–30 s (Iram: pull-apart 0–8 s → process → ends mid-action) or process-rush 40–60 s (Birchberry/Hayeks: one action per ~1 s, product withheld to 85–95%, end on the stretch, one persona/claim caption at t=0, recipe in description).
9. **Packaging**: title in the "the only X you'll ever need / crispy-gooey" superlative family ✓; thumbnail = the pull-apart stretch macro, 55–70% product fill, no face, ≤3 words; paste the **full recipe** in the description (every silent winner does; it's also the highest like-rate group).

## 5. Files
`cards/` (35 cards) · `sheets/` (grid/hook/cuts per video) · `thumbs/` + `long_thumbs_sheet.jpg` · `forensics/` ·
`transcripts/` · `metrics_long.tsv`, `metrics_short.tsv`, `catalog.tsv/json` · `ranked_long.tsv`, `shorts_chip_filtered.tsv`,
`shorts_meta.tsv` (selection audit) · videos (git-ignored): `footage/techjoint_competitors.nosync/{long,short}/`.
