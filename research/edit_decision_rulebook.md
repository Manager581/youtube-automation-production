# Edit Decision Rulebook — how the owner decides a shot (so I can decide it too)

Reverse-engineered from the owner's explicit calls this session + the measured
winner grammar (`viral_recreation_spec.md`, `edit_grammar_ruleset.md`). The two
agree — the owner's instinct IS the winner's grammar. This file is the logic;
`scripts/beat_director.py` runs it.

## The one principle
**Never label a fact — ILLUSTRATE it.** A number on screen is lazy. Show the
number as a real-world visual device, oriented to make the fact *felt*, with the
creature alive in it. (Owner: "13 feet tall → a measuring tape next to it";
"9 tons → a bus on a scale with an equals sign." Winner: skull = bathtub;
crowned lion = taxes; scale charts with arrows.)

## Step 1 — classify the VO segment by WHAT KIND of fact it states
| Concept (cue words) | Device | Angle / camera | Owner or winner precedent |
|---|---|---|---|
| **Height** (tall, X ft tall, at the hip) | vertical MEASURING TAPE w/ arrows + value | FRONT, so height reads | owner: "13 FT" |
| **Length** (long, nose to tail) | horizontal MEASURING TAPE | PIVOT to SIDE profile | owner: "40 FT" |
| **Weight** (tons, weighs) + "as much as a ___" | balance SCALE: creature **=** the named object | hard CUT to the scale scene | owner: "9 TONS = bus" |
| **Force** (bite force, lbs of force, crush, PSI) | GAUGE that maxes out + a crush demo on the named object | macro on the impact | winner: crush spine |
| **Speed** (mph, miles an hour, sprint) | SPEEDOMETER needle | — | spec speedo |
| **Count** (60 teeth, 12 inches) | show them + a number that ratchets up | macro on the part | spec odometer |
| **Smell / scent / nose** | RANGE MAP: radius ring over the city | top-down map | spec smell-map |
| **Sight / eyes / pick one** | POV + target RETICLE that locks the prey | creature-POV | owner: pov-pick |
| **Body part** (arms, legs, skull, muscle) | macro/composite of THAT part | framed on the part | owner: "show the legs/nose" |
| **Action** (stomp, bite, catch, hunt, herd, swim) | creature DOING it composited into real footage | follow the action | owner: stomp; proto_strike bite |
| **Threat / collision** (police, helicopter, rifle, river) | real footage of the threat + creature reacting | — | spec modern-collision |
| **Time** (day one, hour two, ten seconds) | CLOCK face / CALENDAR flip | — | spec clocks |
| **Comparison** ("size of a ___", "like a ___") | show the ___ at the creature's scale | side-by-side | winner: skull=bathtub |
| **Danger / rule** (cannot fall, fatal, dying) | show the CONSEQUENCE (stumble) + attribution card | handheld | owner: FATAL |
| **Abstract / transition** | creature LOOM / presence in the world | slow push | owner: loom |
| **Failure / humiliation** | comedy GAG (house ink), rhyming the noun | cut | spec comedy clusters |

## Step 2 — always-on overlays (every beat, no exceptions)
1. **Creature is alive** — stomp/bob/drift; motion floor never 0. (Owner: "stomping around.")
2. **Device + value are WORD-ANCHORED** — the tape/gauge/number pops on the exact word (WhisperX align).
3. **SFX on every event** — footstomps, the pop, the cut, the impact. (Owner: "with sfx.")
4. **Brand text** — BIG orange (yellow=alert), heavy ink outline, NO banner, fit-to-width. (Owner call.)
5. **Big abstract number → a comparison object** the viewer knows (bus, school, car door). 9 tons is nothing; "= 1 bus" is everything.
6. **Bold/surprising claim → attribution sub-line** ("— paleontologists"). Real but unattributed reads fake. (Owner.)
7. **Cut hard for a scene change** (the scale scene is its own cut, not an overlay).

## Step 3 — pick the asset by the angle the device needs
Front device → front cutout (`ch_trex_avenue_wide`). Side device → side cutout
(`trex_side` from pier_river). Macro → the body-part still. Comparison object →
cut it out (`city_bus`, etc.) and put it on the scale/beside the creature.

## What this does NOT auto-decide (still owner calls)
Tone/comedy aggressiveness, music choice, i2v spend, and any beat the director
flags `LOW-CONFIDENCE`. The director PROPOSES every beat; owner vetoes the few it
gets wrong instead of art-directing all of them.

Related: `viral_recreation_spec.md` · `edit_grammar_ruleset.md` · `scripts/beat_director.py` · `scripts/build_body_reveal.py`
