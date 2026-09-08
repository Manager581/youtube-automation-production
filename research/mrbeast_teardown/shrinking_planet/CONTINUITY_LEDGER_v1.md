# SHRINKING PLANET — Continuity Ledger v1

Deterministic facts every shot must agree with. Generated from `shot_manifest_v1.json` + `SCRIPT_v1.md`; regenerate, never hand-edit.

## Planet ladder (day → metres). THE COUNT displays exactly this number.

| day | planet m | COUNT | master | beats |
|---|---|---|---|---|
| 1 | 1000 | 1000 | `M_PLANET_1000` | B01, B02, B03, B04, B05, B06, B07 |
| 2 | 1000 | 1000 | `M_PLANET_1000` | B08 |
| 5 | 500 | 500 | `M_PLANET_500` | B09, B10 |
| 6 | 500 | 500 | `M_PLANET_500` | B11, B12, B13 |
| 10 | 300 | 300 | `M_PLANET_300` | B14 |
| 12 | 300 | 300 | `M_PLANET_300` | B15, B16 |
| 14 | 300 | 300 | `M_PLANET_300` | B17 |
| 15 | 300 | 300 | `M_PLANET_300` | B18 |
| 16 | 300 | 300 | `M_PLANET_300` | B19, B20 |
| 20 | 25 | 25 | `M_PLANET_25` | B21, B22, B23, B24 |
| 25 | 20 | 20 | `M_PLANET_25` (re-crop) | B25, B26, B27, B28 |
| 26 | 12 | 12 | `M_PLANET_12` | B29 |
| 27 | 7 | 7 | `M_PLANET_12` (re-crop) | B30 |
| 28 | 4 | 4 | `M_PLANET_4` | B31 |
| 29 | 2 | 2 | `M_PLANET_2` | B32, B33 |
| 30 | 2 | 2 | `M_PLANET_2` | B34, B35, B36 |

## Fixed identity (no costume changes across 30 days)

- **PIP**: PIP: 1-metre axolotl-like creature, matte magenta skin, six frilly gill-fronds on the head that act as hair, oversized glossy black eyes, small mouth, ONE yellow scarf (never changes), no other clothing.
- **GRUFF**: GRUFF: 2.5-metre yeti, long cyan-blue fur that completely covers the mouth, heavy expressive brows, ONE cracked brass goggle worn on the forehead, no clothes.
- **ORB**: ORB: 60-cm floating chrome sphere, ONE large glass lens-eye, a gold ring-light halo, a starfield reflected on the chrome, NO mouth, NO arms.
- **COUNT**: THE COUNT: 40-cm matte-black hovering cube, red seven-segment display on every face, ONE wobbling antenna, FOUR small thrusters, no face.

## Devices (kept separate — no rule collision)
- **Red ring on the landing pad** = QUIT line (B05). Crossing it ends the game for both.
- **Escape pod launch key + red lever/door** = STEAL device (B21 → B29). One seat, whole prize.
- **Crate** on the equator: sealed until Day 20 (B06 OPEN → B15 FEED → B19 PAY).
- **Goggle**: cracked brass, forehead, never removed (B17 OPEN → B27 PAY). Only ever worn DOWN in archive still `M_ARCH_02_stage_drums`.
- **Truth beam**: PIP verified GREEN twice; GRUFF UNVERIFIED (B22) — replayed red at B29.
- **Riff**: four-note ukulele motif (B16 OPEN → B30 PAY on a ration tin).

## Open loops

| loop | sequence |
|---|---|
| crate | B01 OPEN → B06 FEED → B09 FEED → B14 FEED → B18 FEED → B23 PAY |
| riff | B19 OPEN → B24 FEED → B30 FEED → B35 PAY |
| goggle | B20 OPEN → B27 FEED → B31 FEED → B32 PAY |
| launch | B25 OPEN → B28 FEED → B29 FEED → B31 FEED → B33 FEED → B34 PAY |
| trust | B26 OPEN → B31 FEED → B34 PAY |

## PIP mouth-visible shots (cap 20)

| shot | beat | t | line it carries |
|---|---|---|---|
| S008 | B03 | 00:18 | Three years ago. |
| S030 | B07 | 01:30 | Sooner or later one of us has to bring it up. I'm hoping it's later. I'm hoping it's Day 29 and we're both too tired to do it properly. |
| S043 | B09 | 03:22 | Halve it. |
| S057 | B12 | 04:50 | I'd rather be chained to a stranger. A stranger would at least talk to me. A stranger would ask what my name is. |
| S058 | B12 | 04:58 | Six days. You've said nine words to me. I counted. He counted. There are cameras that counted. |
| S060 | B12 | 05:14 | You wrote one song in four years! One! And it was about your van! |
| S076 | B15 | 07:17 | I sat in the dressing room every night thinking nobody in that band would notice if I vanished. So I vanished first. Before anyone could not notice. |
| S079 | B16 | 07:52 | So what happens to us now? |
| S088 | B18 | 09:02 | …No. |
| S097 | B19 | 09:52 | Bandmates? |
| S112 | B21 | 11:27 | Take it. |
| S123 | B24 | 12:30 | It can't get smaller than this. |
| S136 | B26 | 13:58 | No. |
| S140 | B27 | 14:34 | Would you launch the pod? |
| S145 | B27 | 15:06 | No. |
| S152 | B29 | 15:45 | Maybe he wants it to be even. Maybe after what I did, that's fair. I left him on a stage. He leaves me on a rock. That's — that's a kind of song. |
| S166 | B31 | 16:55 | I think he's getting ready to leave. |
| S177 | B33 | 18:16 | I'm scared of the next twenty-four hours. |

Total: 18 shots / 18 mouth:ON lines.

## Shots whose seed planet differs from the day's planet (allowed: macro / re-crop / replay)

| shot | beat | day | planet | seeds | note |
|---|---|---|---|---|---|
| S033 | B07 | 1 | 1000 | M_PLANET_25 | planet not visible in frame (macro/re-crop) |
| S126 | B24 | 20 | 25 | M_PLANET_1000 | replay/flashback clip — planet size on screen is the source day's |
| S171 | B32 | 29 | 2 | M_PLANET_300 | replay/flashback clip — planet size on screen is the source day's |
| S181 | B34 | 30 | 2 | M_PLANET_25 | replay/flashback clip — planet size on screen is the source day's |

## Insert re-use counts (≤3 non-adjacent uses each)

| source shot | vantage | re-uses |
|---|---|---|
| S163 | lever-hand macro: a large furred hand resting on the red lever | 2 |
| S007 | over-the-shoulder past ORB to GRUFF | 1 |
| S008 | PIP close-up against the crate, bright | 1 |
| S005 | GRUFF close-up in the cave mouth, brows knotted | 1 |
| S004 | PIP close-up at camp, mouth open in surprise | 1 |
| S025 | THE COUNT insert, drifting past camera left to right | 1 |
| S043 | PIP close-up, decisive, chin up | 1 |
| S057 | PIP confessional, magenta booth, three-quarter angle, fronds flared | 1 |
| S063 | PIP crying close-up, fronds drooped, turned from camp | 1 |
| S046 | THE COUNT insert, front face square, tilting as it updates | 1 |
| S088 | PIP close-up, quiet refusal, low angle | 1 |
| S027 | crate hero: slow orbit around the sealed crate on the pad | 1 |
| S026 | toilet gag: low wide, a hole in the rock with the horizon and stars | 1 |
| S093 | ORB close-up tilted, teasing, halo dim pulse | 1 |
| S131 | PIP reaction close-up to the flip, fronds frozen mid-flare | 1 |
| S136 | PIP close-up inside the beam, light on fronds | 1 |
| S128 | key-under-platter macro: a heavy brass launch key on a red cloth | 1 |
| S162 | HERO / THUMBNAIL: GRUFF standing taller than the 4 m planet, PIP at his feet, black space | 1 |
| S102 | goggle macro: the cracked brass goggle on GRUFF's forehead, firelight | 1 |
| S134 | truth-beam wide: the column of light between them, ORB above (grade green/red in post) | 1 |
| S180 | clock face insert plate: the housing on the rock, blank face for digit composite | 1 |
| S120 | PIP sobbing close-up, new angle from below, crate light on her | 1 |

## Sets by shot count

| set | shots |
|---|---|
| landing_pad | 53 |
| orbit | 43 |
| equator | 33 |
| confessional | 16 |
| gruff_cave | 15 |
| pip_camp | 14 |
| pod_door | 13 |
| truth_beam | 12 |

## Per-beat shot table

| beat | span | day | m | shots (unique+insert) | PIP mouth |
|---|---|---|---|---|---|
| B01 Cold open | 00:00-00:12 | 1 | 1000 | 3+0 | 0 |
| B02 Silent hold | 00:12-00:17 | 1 | 1000 | 3+0 | 0 |
| B03 The wound | 00:17-00:21 | 1 | 1000 | 2+2 | 1 |
| B04 Anklets lock | 00:21-00:30 | 1 | 1000 | 3+2 | 0 |
| B05 Red line + orbit pull-out | 00:30-00:45 | 1 | 1000 | 4+0 | 0 |
| B06 Planet tour | 00:45-01:30 | 1 | 1000 | 9+1 | 0 |
| B07 Confessionals + flash-forward | 01:30-02:00 | 1 | 1000 | 4+0 | 1 |
| B08 The engine | 02:00-02:45 | 2 | 1000 | 6+0 | 0 |
| B09 Day 5 · Offer #1 | 02:45-03:30 | 5 | 500 | 4+0 | 1 |
| B10 The wedge | 03:30-04:10 | 5 | 500 | 5+1 | 0 |
| B11 It bites | 04:10-04:50 | 6 | 500 | 7+0 | 0 |
| B12 The first fight | 04:50-05:40 | 6 | 500 | 6+1 | 3 |
| B13 The truce | 05:40-06:20 | 6 | 500 | 2+1 | 0 |
| B14 Day 10 · free shrink + heart | 06:20-07:05 | 10 | 300 | 7+1 | 0 |
| B15 The talk (i) | 07:05-07:40 | 12 | 300 | 3+0 | 1 |
| B16 The talk (ii) | 07:40-08:15 | 12 | 300 | 3+0 | 1 |
| B17 GRUFF's lap | 08:15-08:45 | 14 | 300 | 5+0 | 0 |
| B18 Day 15 · the dome refused | 08:45-09:45 | 15 | 300 | 8+2 | 1 |
| B19 Breakfast + the book | 09:45-10:25 | 16 | 300 | 6+0 | 1 |
| B20 The goggle | 10:25-10:55 | 16 | 300 | 4+0 | 0 |
| B21 Day 20 · five platters | 10:55-11:30 | 20 | 25 | 7+0 | 1 |
| B22 Platter four | 11:30-12:00 | 20 | 25 | 4+0 | 0 |
| B23 The crate opens | 12:00-12:25 | 20 | 25 | 5+0 | 0 |
| B24 The cost | 12:25-12:45 | 20 | 25 | 4+1 | 1 |
| B25 Day 25 · the flip | 12:45-13:30 | 25 | 20 | 6+1 | 0 |
| B26 The truth beam (i) | 13:30-14:20 | 25 | 20 | 4+0 | 1 |
| B27 The truth beam (ii) | 14:20-15:10 | 25 | 20 | 6+2 | 2 |
| B28 GRUFF at the pod | 15:10-15:40 | 25 | 20 | 4+1 | 0 |
| B29 Day 26 · soundproof pods | 15:40-16:05 | 26 | 12 | 6+0 | 1 |
| B30 Day 27 · three-legged race | 16:05-16:25 | 27 | 7 | 5+0 | 0 |
| B31 Day 28 · taller than the world | 16:25-17:10 | 28 | 4 | 6+1 | 1 |
| B32 24 hours left · the secret | 17:10-17:55 | 29 | 2 | 5+1 | 0 |
| B33 Night doubt | 17:55-18:35 | 29 | 2 | 4+1 | 1 |
| B34 The clock | 18:35-19:30 | 30 | 2 | 10+3 | 0 |
| B35 Half each + the riff | 19:30-19:55 | 30 | 2 | 5+1 | 0 |
| B36 Band's back | 19:55-20:00 | 30 | 2 | 1+0 | 0 |
