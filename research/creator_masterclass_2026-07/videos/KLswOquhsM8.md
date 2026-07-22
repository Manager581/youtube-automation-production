# KLswOquhsM8 — "I Made an AI Character Sit With Me and Have a Conversation" (Prompt Mastery, 18:14, ~296K views)

## What the video is
A hands-on local-AI VFX tutorial, not creator-strategy advice. The creator composites an AI character (apparently Jinx from Arcane — note the Riot Games disclaimer) into real filmed footage of himself, then makes her talk. Pipeline: film a real performer (his daughter) → crop the character region at exact custom resolution (Claude-built crop tool) → Flux 2 Klein character swap in ComfyUI → SCAIL-2 motion transfer → mask+feather composite in CapCut → LTX 2.3 22B Distill 1.1 in WAN2GP generating video *from a voice track* (Omni Voice clone) with timestamped "Relay Prompt" action control at 1080p/30fps. Transcript garbles: "Skill/scale two"=SCAIL-2, "12GP/1-2-GP"=WAN2GP, "Flats Two client/FlexClip"=Flux 2 Klein.

## What's actually shown (evidence)
- The finished 5s two-person scene plus side-by-side with the original daughter footage (~02:45).
- The crop tool cutting 960x1080 / 768x1088 regions (~05:30); ComfyUI swap at custom 768x1088 because WAN2GP's Flux 2 Klein only offers preset resolutions (~07:20).
- SCAIL-2 "resize image/mask to match size" node linked so output resolution == input (~08:30); admits 10-20 generations still leave background seams.
- CapCut rectangle mask + feather + rounded corners fixing the seams live (~09:50-11:00).
- Failed swap attempts shown (missing hands, unswapped outfit) (~12:55).
- WAN2GP: Omni Voice clone from an online sample → 4 clips; LTX 2.3 "generate video based on soundtrack and text prompt" with the voice file uploaded; Relay Prompt icon/help in UI; result gestures on cue ("pointing at camera as she talks") (~14:30-17:30).
- Honest cost datapoint: ~8 hours R&D for 5 seconds of composite.

## Credibility
High as a tool demo: real workflows on screen, failures included, no revenue claims. Motive is a Patreon free-member funnel (email capture for workflows/crop tool), a CapCut affiliate link, and cross-promotion of his own SCAIL-2/WAN2GP tutorials. Claims are self-evidencing (the clips are in the video). Zero YouTube-algorithm/monetization content.

## Tactics extracted
1. **Masked-crop-at-exact-resolution gen** — process only the character region (720p model limit), keep crop dims == gen dims == composite dims, paste back. CONFIRM: this is AMBER stage_b_vace's architecture; adopt an explicit resolution-equality assertion.
2. **Audio-conditioned talking-character gen** — LTX 2.3 in WAN2GP acts *from the voice file*. NEW: directly attacks our i2v talking-creature jaw-sync QA failures (feed ElevenLabs VO as soundtrack).
3. **Relay Prompt** — timestamped per-second action directives. NEW-ish: same idea as AMBER's event sheet, but implemented inside the generator.
4. **Omni Voice** — small local voice clone in WAN2GP. Maps to the F5-TTS license problem; check its license.
5. **Real performer as lighting/pose reference for swap; best-of-N; feathered-mask blend; Claude-built utility tools; solo two-chair dialogue trick** — CONFIRM (composite engine, best-of-N plan) or IGNORE (AI human faces violate our hard rule; FFmpeg crop replaces his tool).

## Policy notes
None. Only IP intel: he leans on a Riot character with a fan-content disclaimer — we use original creatures, no exposure.

## What we apply
- **Rexcaped**: TEST WAN2GP + LTX 2.3 audio-driven gen on ONE dialogue beat (ElevenLabs VO as soundtrack + relay-prompt mouth/gesture timing) to fix jaw-motion-vs-speech-window failures. Hardware caveat: 22B distill may not fit M5 24GB — that is the experiment. Add relay-style timestamped riders to TSV prompts where WAN2GP is used.
- **AMBER**: add resolution-equality assertion in stage_b composite; keep best-of-N plan.
- **Prehistoric POV**: thin — only the exact-crop-resolution discipline for region fixes.
- **Bizdoc**: check Omni Voice's license as a monetization-safe local clone (F5-TTS is CC-BY-NC).

## Verdict
Genuinely useful *technique* video for this operation's compositing/local-gen stack; zero strategy value. ADOPT the resolution discipline, TEST audio-driven talking-creature gen + Omni Voice license, IGNORE the human-character swap path (hard-rule conflict) and the CapCut/Patreon layer.
