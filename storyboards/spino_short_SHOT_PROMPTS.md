# SPINOSAURUS SHORT — the journey, shot by shot, with the EXACT prompts
_Nothing below gets generated until Jeff approves. 2026-07-24._

## The journey (matching the original's structure)
**Swamp reveal → crossing the marsh → entering the sea → a LIVING underwater world →
the threat → the strike (restaged, no explosions) → dragged down → settles → card.**

## Rules baked into every prompt (each learned the hard way this session)
1. **"This exact animal"** anchors i2v to the seed. The prompt is MOTION + CAMERA + SOUND only.
2. **One seed per location** — the seed carries its environment. New location = new seed,
   made by *editing* the master so the animal's design survives.
3. **Camera is named explicitly** and is always locked off (the original never moves the lens).
4. **No dramatic figures of speech.** "Explodes" produced a literal detonation. Banned words:
   explode, blast, burst, erupt. Violence = thrash, churn, cloud, drag.
5. **Never ask for an off-screen attacker or two-creature contact.** The attacker gets its own
   shots; contact is hidden by silt and framing, exactly like the reference.
6. **Diegetic sound named per beat, always ending "No music."**
7. **Realism suffix on everything:** true natural colours, no colour grading, no glow, no lens flare.
8. Prompts stay under ~600 chars — the one 750-char prompt silently failed.

## Assets that already exist
| Asset | Status |
|---|---|
| Seed A — master, muddy river bank | LOCKED (`ae6ccc5f`) |
| Seed B — same animal underwater, murky river | LOCKED (`44a83efe`) |
| SHOT 1 hook reshoot (correct head) | RENDERING (`ef640c06`) |
| SHOT 3 wade-away | ON DISK (`SP_B02_wade_sail`) |
| SHOT 7 hero head-on | ON DISK (`SP_B05_hero`) |
| SHOT 8 threat pass | ON DISK (`SP_B07_threat`) |
| SHOT 10 bookend settle | RENDERING (`5e017d76`) |
| ~~strike~~ | REJECTED (the explosion) — replaced by shots 9a/9b below |

---

## NEW SEEDS NEEDED FIRST (image edits of Seed A — cheap, no video credits)

### Seed C — "the marsh crossing" (for SHOT 2)
> Keep this exact same animal, identical anatomy, identical long narrow gharial snout,
> identical sail, identical grey-green hide. Change ONLY the framing and environment:
> seen from very far away, small in a vast flat marsh landscape of winding water channels
> and grass, walking left to right, the sea faintly visible on the horizon. Real wildlife
> photograph, high vantage point, natural overcast dawn light, true natural colours,
> no colour grading, no glow.

### Seed D — "the surf line" (for SHOT 4)
> Keep this exact same animal, identical anatomy, identical long narrow gharial snout,
> identical sail, identical grey-green hide. Change ONLY the environment: it stands at
> the edge of the open sea where small waves break on wet sand, facing the water, grey-blue
> sea to the horizon. Real wildlife photograph, low camera on the beach, long lens,
> natural overcast light, true natural colours, no colour grading, no glow.

### Seed E — "the open sea" (for SHOTS 5 & 9b)
> Keep this exact same animal, identical anatomy, identical long narrow gharial snout,
> identical sail, identical grey-green hide. Change ONLY the environment: it is fully
> underwater in open blue-green SEA water with much better visibility than a river,
> sunlight shafts from the surface, a sandy sea floor far below, small silver fish in
> the distance. Real underwater wildlife photograph, true natural colours, no colour
> grading, no glow.

### Seed F — "the mosasaur" (for SHOT 9a — its own animal, its own seed)
> Real underwater wildlife photograph, vertical 9:16. A huge dark mosasaur — a massive
> marine reptile with a long crocodile-like head, paddle flippers and a powerful tail —
> cruising through open blue-green sea water, seen side on, filling most of the frame,
> sunlight shafts from the surface above, small fish scattering ahead of it. True natural
> colours, no colour grading, no glow, no lens flare, believable photographic grain.

---

## THE VIDEO PROMPTS — in film order

### SHOT 1 — THE HOOK (0:00–0:08) · Seed A · ALREADY RENDERING
> Camera locked off at water level, does not move. This exact animal lies completely
> still, half sunk in shallow muddy water and caked in dried mud so it looks like a
> fallen log. Small pterosaurs perch on its back. Nothing moves for five seconds. Then
> it rises, water and mud sheeting off, and the birds scatter. Real wildlife documentary
> footage, natural dawn light, true natural colours, no colour grading, no glow.
> Sound: water lapping, insects, then a surge of water. No music.

### SHOT 2 — THE JOURNEY WIDE (0:08–0:15) · Seed C
> Real wildlife documentary footage, camera locked off on a high vantage point looking
> down across the marsh, the horizon high in the upper fifth of frame, the camera does
> not move. This exact animal, small in the vast landscape, walks steadily left to right
> through the winding water channels toward the distant sea, pushing slow ripples.
> Grass moves faintly in the wind. Natural overcast dawn light, true natural colours,
> no colour grading, no glow, no lens flare. Sound: wide open air, wind over grass,
> distant birds, faint water. No music.

### SHOT 3 — THE LULL (0:15–0:22) · ON DISK (`SP_B02_wade_sail`)
Already shot: wades away from camera, legs vanish, only the sail above water. Stays quiet.

### SHOT 4 — INTO THE SEA (0:22–0:30) · Seed D
> Real wildlife documentary footage, camera locked off low on the beach with a long lens,
> the camera does not move, horizon near the top of frame. This exact animal wades forward
> into the breaking waves, deeper with every step, until its body is under and only the
> tall sail is above the surface, cutting through the swell like a fin as it moves out
> to sea. Natural overcast light, true natural colours, no colour grading, no glow, no
> lens flare. Sound: waves breaking on sand, water surging around a large body, wind,
> gulls far away. No music.

### SHOT 5 — A LIVING SEA (0:30–0:38) · Seed E
> Real underwater wildlife documentary footage, camera locked off and level, side on,
> the camera does not move. This exact animal swims slowly across frame through open
> blue-green sea water, unhurried, tail sweeping. A dense school of small silver fish
> wheels and parts around it, and light shafts from the surface sway across its back.
> Suspended particles drift. True natural underwater colours, no colour grading, no glow,
> no lens flare. Sound: muffled underwater, deep and calm, soft water movement, the
> distant crackle of a living sea. No music.

### SHOT 6 — THE SUPPORTING CAST (0:38–0:44) · NO SEED (text-to-video — appears once)
> Real underwater wildlife documentary footage, vertical, camera locked off, the camera
> does not move. Open blue-green sea water with sunlight shafts from above. Pale jellyfish
> drift slowly past at different depths, a small squid pulses by, and far below a sea
> turtle glides over the sandy floor. Calm, slow, alive. True natural underwater colours,
> no colour grading, no glow, no lens flare. Sound: muffled underwater quiet, soft
> crackle, very calm. No music.

### SHOT 7 — THE HERO (0:44–0:53) · ON DISK (`SP_B05_hero`)
Already shot: eye level, head-on, swims straight at the lens until it fills the frame.
The only eye-level shot in the film, exactly like the original.

### SHOT 8 — THE THREAT (0:53–1:00) · ON DISK (`SP_B07_threat`)
Already shot: it hangs still in frame while a far larger shape passes in the gloom behind.

### SHOT 9a — THE MOSASAUR COMMITS (1:00–1:04) · Seed F
> Real underwater wildlife documentary footage, camera locked off, the camera does not
> move. This exact animal accelerates forward and downward through the open blue-green
> water, jaws opening as it drives toward the lower edge of frame, its tail beating hard,
> small fish scattering. It passes close to the camera and out of frame, leaving swirling
> water and drifting particles. True natural underwater colours, no colour grading, no
> glow, no lens flare. Sound: a deep muffled rush of water, powerful and fast, then
> sudden quiet. No music.

### SHOT 9b — DRAGGED DOWN (1:04–1:10) · Seed E · **the restaged strike — no attacker in frame, nothing "explodes"**
> Real underwater wildlife documentary footage, camera locked off, the camera does not
> move. This exact animal is wrenched sideways and downward, thrashing, as thick silt
> churns up from below and clouds the water around it until it is only a struggling
> silhouette inside the murk, sinking out of frame. Dark, heavy, obscured. True natural
> underwater colours, no colour grading, no glow, no lens flare. Sound: one heavy dull
> muffled impact, churning water, bubbles, then fading quiet. No music.

### SHOT 10 — THE BOOKEND (1:10–1:17) · ALREADY RENDERING (`5e017d76`)
> (submitted) The animal lowers itself into the shallow water and goes completely still;
> silt drifts over its back until it reads as a low mud ridge again; the pterosaurs return.

*Note: the bookend as shot returns the SAME animal to the mud (it survives). If Jeff wants
the original's dark ending instead — the empty riverbank, the birds settling on nothing —
that is one alternative generation from Seed A with the animal absent. Decision is his.*

### CARD (1:17–1:21) · built in the assembler
4.5 s black, −55 dB room tone. Already implemented.

---

## Cost if approved as written
4 image edits (seeds C, D, E, F) + 5 videos (shots 2, 4, 5, 6, 9a, 9b = six) —
**6 video generations**, ~2 hours wall-clock at 3 concurrent, $0 on the free tier.
Everything else is already on disk or rendering.
