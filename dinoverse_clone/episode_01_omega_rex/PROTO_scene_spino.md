# PROTOTYPE — Spinosaurus Wetland (4-shot proof of the full loop)

Goal: prove the exact captured Dinoverse loop on ONE small scene before scaling to 80–90 shots.
Format produced by applying the two VERIFIED_PROMPTS to this scene (Scene 4 of the Omega Rex bible).
Chosen because we have the creator's REAL worked Spinosaurus prompt to check fidelity against.

**How to run it:**
1. Stills: paste each shot's **IMAGE prompt** into Gemini/ChatGPT image gen. Make Shot 1 first, then
   feed it back as the reference for Shots 2–4 ("same lagoon, same Spinosaurus, same light") for consistency.
2. Animate: upload each still to **Grok Imagine** with the shot's **GROK prompt** → 6s/720p clip (keep native audio).
3. Hand the 4 clips back to me → I concat + layer Pixabay ambience + a music bed → ~24s mini-cut.

Mini-arc: ESTABLISH → FACT → ACTION/COMEDY → RESOLVE.

---

## SHOT 1 — ESTABLISH (reveal)

**IMAGE prompt:**
> Photorealistic documentary wildlife-park photograph, 16:9. A wide wooden boardwalk over a broad
> green freshwater lagoon at a modern open-air dinosaur zoo ("Dinoverse Zoo" — weathered concrete-and-glass
> enclosures, lush green landscaping, paved paths). A massive sail-backed Spinosaurus wades chest-deep in
> the shallows mid-distance, crocodile-like jaws, tall back sail catching midday sun. A handful of casual
> tourists in summer clothes line the wooden rail watching. Bright sunny midday, clear blue sky, natural
> realistic lighting, natural colors, accurate anatomy and real-world scale. Zoo/wildlife documentary style.
> No text, no cinematic effects, no fog, no dramatic lighting.

**GROK prompt:**
```
Camera: POV walking up to the boardwalk rail, handheld eye-level, slight natural sway, slow reveal pan across the lagoon
Movement: Visitors -> casual walking and leaning on the rail, small head turns; Spinosaurus -> slow heavy wade, water displacing around its legs, natural breathing
Environment: real zoo documentary style, broad green lagoon and wooden boardwalk, flat natural daylight, realistic enclosure and pathways, no cinematic effects, no artificial fog or dramatic atmosphere
Sound (realistic): soft crowd murmur; footsteps on wood; light wind and leaves rustling; gentle water movement; distant birds
Dialogue: none
Style: non cinematic; grounded realistic behavior; exact environment matching reference; 16:9
```

---

## SHOT 2 — FACT (detail close-up + one staff fact line)

**IMAGE prompt:**
> Photorealistic documentary close-up, 16:9, SAME Dinoverse Zoo lagoon enclosure and same Spinosaurus as
> the reference image. Close on the Spinosaurus's long narrow crocodile-like jaws and tall back sail, water
> dripping from its snout, individual scales and skin texture detailed in midday sun. A khaki-uniformed
> zoo ranger (round embroidered patch, cap, lanyard) stands at the wooden rail in the near foreground,
> mid-gesture explaining to a small crowd. Natural realistic lighting, natural colors, accurate anatomy,
> real-world scale, wildlife documentary style. No text, no cinematic effects, no fog.

**GROK prompt:**
```
Camera: POV at the rail, handheld eye-level, slight sway, slow push-in toward the jaws
Movement: Staff -> natural pointing gesture, calm explaining movement; Spinosaurus -> slight head movement, slow blink, water dripping; Visitors -> subtle reactions
Environment: real zoo documentary style, same green lagoon enclosure, flat natural daylight, realistic enclosure and pathways, no cinematic effects, no artificial fog or dramatic atmosphere
Sound (realistic): soft crowd murmur; dripping water; light wind; natural enclosure ambience
Dialogue: Staff (softly): "Spinosaurus was actually larger than T-Rex, and spent much of its life hunting fish in the water."
Style: non cinematic; grounded realistic behavior; exact environment matching reference; 16:9
```

---

## SHOT 3 — ACTION + COMEDY (lunge/splash + visitor reaction)

**IMAGE prompt:**
> Photorealistic documentary action photograph, 16:9, SAME Dinoverse Zoo lagoon and same Spinosaurus as
> the reference image. The Spinosaurus lunges forward and snaps a fish from the lagoon, a large splash of
> water bursting toward the camera, droplets across the frame. A young woman with curly dark shoulder-length
> hair, white tee, denim shorts and a green crossbody bag stands at the wooden rail, soaked and laughing,
> mid-reaction; other tourists flinch back. Bright midday, natural realistic lighting, natural colors,
> real-world scale, wildlife documentary style. No text, no cinematic effects, no fog.

**GROK prompt:**
```
Camera: POV at the rail, handheld eye-level, small recoil as the splash hits the lens
Movement: Spinosaurus -> one slow-heavy lunge and snap, big water splash; Visitors -> flinch back then laugh, natural reactions
Environment: real zoo documentary style, same green lagoon enclosure, flat natural daylight, realistic enclosure and pathways, no cinematic effects, no artificial fog or dramatic atmosphere
Sound (realistic): big water splash; crowd gasp then laughter; footsteps on wood; natural enclosure ambience
Dialogue: Young woman visitor (laughing): "I'm soaked. Worth it."
Style: non cinematic; grounded realistic behavior; exact environment matching reference; 16:9
```

---

## SHOT 4 — RESOLVE (wide, submerge)

**IMAGE prompt:**
> Photorealistic documentary wide shot, 16:9, SAME Dinoverse Zoo lagoon as the reference image. The
> Spinosaurus has submerged until only its tall back sail cuts across the calm green lagoon water, ripples
> spreading outward. Tourists watch quietly from the wooden boardwalk in the foreground. Bright sunny
> midday, clear sky, natural realistic lighting, natural colors, real-world scale, wildlife documentary
> style. No text, no cinematic effects, no fog, no dramatic lighting.

**GROK prompt:**
```
Camera: POV locked wide at the rail, slight handheld sway
Movement: Spinosaurus -> only the sail glides slowly across the water, ripples spreading; Visitors -> quiet watching, small head turns
Environment: real zoo documentary style, broad green lagoon, flat natural daylight, realistic enclosure and pathways, no cinematic effects, no artificial fog or dramatic atmosphere
Sound (realistic): hushed crowd murmur; gentle water ripples; light wind and leaves rustling; distant birds
Dialogue: none
Style: non cinematic; grounded realistic behavior; exact environment matching reference; 16:9
```

---

### Assembly (my side, once clips exist)
```
# clips in approved/: spino_s1.mp4 .. spino_s4.mp4  (keep each clip's native Grok audio)
ffmpeg -f concat -safe 0 -i work/spino_timeline.txt -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac work/spino_cut.mp4
# then layer Pixabay ambience (water/crowd/birds) + a quiet music bed under the native audio (amix), per ORCHESTRATION.md
```
