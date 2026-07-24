# THE ORIGINAL — camera & sound spec, shot by shot
### Everything you need to reproduce the grammar with our own animal and story

All numbers measured off the file (ffmpeg + numpy), not eyeballed.
- **Horizon %** = height of the strongest horizontal luma break, % from frame top.
  **Low % = camera HIGH looking down. High % = camera LOW looking up.**
- **Pan/tilt** = background-edge tracking, converted to **% of frame width per second**.
- **Subj %** = share of frame occupied by the subject.
- **Roll90** = frequency below which 90% of audio energy sits. **This is the underwater filter.**

---

## ⭐ THE FIVE RULES THAT MATTER MOST

**1. THE CAMERA BARELY MOVES. 9 of 19 shots are dead locked-off.**
The rest drift at **≤3.3% of frame width per second** — a slow hold, not a pan.
**There is not one push-in, pull-back, whip, shake, or speed ramp in the entire film.**
Whatever growth you see in frame is the *animal moving*, not the lens.

**2. Camera HEIGHT does the storytelling, and it alternates every cut.**
The horizon is never near the middle. It is either **6–22% (high, looking down — animal
small, watched, vulnerable)** or **78–98% (low, looking up — animal huge, dominant)**.
**Eye level is used exactly ONCE — the hero portrait at 24–26 s.** That is why it lands.

**3. Sound is a lowpass filter arc, and it is the best trick in the film.**
Above water roll90 sits at **3,500–6,600 Hz**. Underwater it collapses to **409–990 Hz**.
The dive (21→28 s) is a 3-second sweep down; the breach (49 s) snaps it back in one frame.
That single filter move does more work than any music cue could.

**4. Every loud moment is pre-loaded with a hole.**
The lull at 5–8 s bottoms at **−42.7 dB**; the film's loudest points are **−12 dB**.
That is a 30 dB swing. Silence buys the impact.

**5. Violence is dark, short, and obscured — deliberately.**
Contact frames are ~25% darker than clean shots, and buried in blood/foam/blur, because
the generator cannot render two creatures touching. Copy the staging, not the weakness.

---

## SHOT-BY-SHOT SPEC

### ACT 1 — LAND / SURFACE · sat 12–28% · roll90 3,500–6,600 Hz (bright, airy)

| # | Time | Camera height | Movement | Framing | Sound |
|---|---|---|---|---|---|
| **1** | 0.0–5.0 | **LOW, near water level** (horizon 91%) | **TILT DOWN 1.3%/s** — barely a settle | WIDE. Subject 62% but reads as terrain | **−24 dB, sub 48%.** Low water rumble. **Soft-in, no bang** |
| **2** | 5.0–8.2 | **HIGH, looking down** (horizon 12%) | **LOCKED OFF** | WIDE, subject drops to 39% | **THE HOLE: −35 → −38 dB.** Deliberate lull |
| **3** | 8.2–12.1 | **HIGH** (horizon 21%) | **LOCKED OFF** | WIDE, flat marsh. Only the sail shows | **−42.7 dB — quietest second in the film**, then bright detail (roll90 5,600) |
| **4** | 12.1–14.6 | **VERY LOW, under the eyeline** (horizon 98%) | **PAN RIGHT 1.8%/s** | CLOSE. Subject jumps to 84% | **−19.5 dB spike.** The catch |
| **5** | 14.6–17.3 | **LOW, from the beach** (horizon 93%) | **PAN LEFT 2.8%/s** | Long lens, compressed surf. Sail as a fin | **−23 dB.** Surf, bright (roll90 5,600) |
| **6** | 17.3–20.6 | **LOW, at water level** (horizon 22%) | **LOCKED OFF** (3px drift) | VERY CLOSE, sail fills frame | −28 to −33 dB, airy |

### ACT 2 — UNDERWATER · sat 48–81% · roll90 **409–990 Hz** (the filter)

| # | Time | Camera height | Movement | Framing | Sound |
|---|---|---|---|---|---|
| **7** | 20.6–23.8 | Level, side-on | **PAN RIGHT 3.3%/s** (fastest in film) | Subject only **9%** — tiny in blue | **THE DIVE SWEEP: roll90 1,981 → 1,507 → 1,550 Hz.** −15 dB peak at 22 s |
| **8** | 23.8–26.9 | **EYE LEVEL — the only time** | **LOCKED OFF** | **HERO. Head-on, symmetric.** Subject 69%, skull 71% of width | **−17 → −15 dB, sub 47–52%.** Loudest sustained passage of the first half |
| **9** | 26.9–29.0 | **LOW, from the seabed looking UP** (79%) | **TILT UP 4.5%/s** | Legs above camera. **A turtle = the only scale cue in the film** | **−13.8 dB, sub 57.7% — the sub-heaviest second.** roll90 926 Hz |
| **10** | 29.0–31.8 | Level, side-on | **LOCKED OFF** | Subject 35%. A marine reptile passes above | −21 → −27 dB, opening back up |
| **11** | 31.8–38.2 | Level, side-on | **PAN RIGHT 1.0%/s** — the long slow drift | Subject 71%. Jellyfish, squid | **−19 to −24 dB.** roll90 sinks to **452 → 409 Hz at 36–37 s = DEEPEST POINT** |
| **12** | 38.2–40.6 | Level | **PAN LEFT 2.2%/s** | Swimming, light shafts | −23 to −30 dB, mid-forward |
| **13** | 40.6–43.4 | Level | **PAN RIGHT 3.2%/s** | **Subject 80% — the threat fills frame** | **−15.6 dB, sub 35%.** Something big |
| **14** | 43.4–46.9 | Level | **PAN LEFT 2.5%/s** | Subject drops to 52% — he shrinks | **THE BITE at 45 s: −12.0 dB, the loudest point in the film** |
| **15** | 46.9–49.3 | **BELOW, looking up** (78%) | **LOCKED OFF** | **Subject 23% — taken away from us.** Darkest frame (br 45) | −19 to −20 dB, **roll90 624 Hz — muffled, deep** |

### ACT 3 — SURFACE KILL · sat 19–35% · roll90 back to 3,000–6,500 Hz

| # | Time | Camera height | Movement | Framing | Sound |
|---|---|---|---|---|---|
| **16** | 49.3–52.6 | **HIGH, looking down** (horizon 20%) | **PAN RIGHT 2.3%/s** | Thrashed on black rock | **THE BREACH: roll90 624 → 5,276 → 6,266 Hz in one cut.** Full band snaps back |
| **17** | 52.6–56.8 | **LOW, almost under them** (horizon 97%) | **LOCKED OFF** | Rolling, wave washes through | **−12 to −14 dB** — sustained loud |
| **18** | 56.8–61.5 | **HIGH, looking down** (horizon 15%) | **LOCKED OFF** | Held and shaken | −12.1 dB at 59 s (joint-loudest) |
| **19** | 61.5–65.7 | **HIGH, wide** (horizon 66%) | **LOCKED OFF** | Final hold. Body draped, unmoving | −15 dB, settling |
| **—** | 65.7–70.5 | — | static black card | Logo, centred | **4.716 s of TRUE DIGITAL SILENCE (−240 dB)** |

---

## THE AUDIO ARC IN ONE LINE

```
BRIGHT (3.5-6.6 kHz) → sweep down over 3 s → MUFFLED (400-990 Hz) → snap back in 1 frame → BRIGHT
   land/surface 0-20s          dive 21-28s        underwater 29-48s      breach 49s      kill 49-65s
```

**Loudest seconds:** 45 (−12.0, the bite) · 55 (−12.0) · 59 (−12.1) · 28 (−13.8, the sub-heavy pass)
**Quietest seconds:** 8 (−42.7) · 7 (−37.7) · 5 (−35.5) — all in the deliberate lull before the catch
**Dynamic swing: 30 dB.** Integrated −17.2 LUFS, LRA 15.9 — cinematic, not crushed.

---

## HOW WE REPRODUCE THIS WITH GROK i2V

Grok gives 10 s clips (vs their 6.5 s max), which is an advantage: one generation can hold a
whole beat. Prompts must specify **camera height, camera behaviour, and diegetic sound** —
because in i2v the prompt controls motion, and the seed controls the animal.

**Camera language that maps to the measurements:**
| What we want | Put this in the prompt |
|---|---|
| Locked off (9 of 19 shots) | "locked off on a tripod, the camera does not move" |
| Slow drift (≤3.3%/s) | "the camera holds, drifting very slightly to follow" |
| High looking down | "shot from above looking down, horizon high in the upper fifth of frame" |
| Low looking up | "camera low at water level looking up, horizon near the top of frame" |
| Eye level (ONCE only) | "camera at eye level with the animal, head-on, symmetrical" |
| **NEVER** | push in, pull back, zoom, dolly, handheld, shake, orbit, drone move |

**Sound language:**
| Beat | Put this in the prompt |
|---|---|
| Above water | "natural ambient sound: water lapping, insects, distant birds, open air" |
| The dive | "the sound muffles as it goes under, high frequencies falling away" |
| Underwater | "muffled underwater sound, deep low rumble, no high frequencies" |
| The strike | "a heavy dull impact, churning water, muffled" |
| The breach | "the sound snaps back to full clarity as it breaks the surface, spray and air" |

**Then in the edit (`assemble_*.py`):**
1. **Apply the lowpass arc ourselves** — do not trust the generator to be consistent.
   Above water: full band. Underwater: lowpass ~800 Hz. Dive: 3 s sweep between them.
   Breach: one-frame snap back. This is the highest-value thing to bake in post.
2. **Cut a hole before every payoff** — 0.5–1.0 s dropping to ~−40 dB before the reveal,
   the catch, and the strike.
3. **Master −15 LUFS, TP −1.5, and defend LRA ≥ 9.** Do not crush it.
4. **3–4 s of near-silence on the end card** (use −55 dB room tone, not true zero).
5. **Grade per location, not per "look"** — the saturation arc is three real environments,
   not a filter. Keep full black and clean highlights.
