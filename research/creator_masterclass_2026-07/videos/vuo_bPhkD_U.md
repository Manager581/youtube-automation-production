# vuo_bPhkD_U — "This DaVinci Resolve Plugin Just DESTROYED Every AI Editing Tool" (Kevin Vandermarliere, 5:42, 35K views)

## What the video is
A product-launch demo for the creator's OWN plugin, "AI Video Studio" for DaVinci Resolve (sold on his Gumroad; also bundled into his paid Skool community "The VFX Room"). Not creator advice — a tool ad with a clickbait "DESTROYED" title. The plugin embeds AI generation inside Resolve: text-to-video, image-to-video, image gen, "edit video" (draw-to-video, reframe, relight, upscale), green-screen backdrop generation, 3D-model-from-one-image (up to 4 refs), and "clay-to-photoreal" (crude 3D animation as motion, AI as render engine). Engines: fal.ai cloud pay-per-generation, or local ComfyUI free — but the description admits local ComfyUI is **Windows-only** today ("Update coming soon for mac!"). Built-in assistant runs on NVIDIA serverless APIs. Free Resolve is supported via a script; Studio via Workspace → Workflow Integrations.

## What's actually shown (evidence)
- Interface tour (1:00–3:30): module list, green connection dot, engine settings (fal.ai vs ComfyUI), API-key panel, camera/lens/lighting/movement PRESET dropdowns replacing freeform prompting, node graph (prompts + reference images + image/video models), timeline-frame capture as i2v source.
- One worked example (3:41–4:37): green-screen footage → backdrop generated with Flux 2 in local comfy mode → composited into a "live stage," plus a second background variation and an animated version.
- 3D-from-image (shoe) and clay-to-photoreal shown in seconds, results-only. No YouTube analytics, no revenue claims, no retention data — none claimed.

## Credibility
Transparent motive: he built the product and every link monetizes him (Gumroad one-time, Skool subscription, courses). The demos are real screen recordings of the plugin working, so the tool exists and functions as shown; but "destroys every AI editing tool" is marketing, quality of outputs is shown only on his cherry-picked example, and per-generation fal.ai costs are never quantified. "Built by actual editors" is unverifiable. As tool intel it's honest enough; as advice it's an ad.

## Tactics extracted
1. **Camera/lens/lighting/movement as preset parameters, not prose prompts** — NEW (concept, free). Maps to our TSV prompt riders / edit-engine prompt templates.
2. **Capture-timeline-frame → i2v** — CONFIRM. This is exactly our stills-first pipeline (ChatGPT/Gemini stills → Grok i2v).
3. **Clay/blocked render as motion source, AI as render engine** — NEW concept; maps to AMBER/VACE-1.3B (masked-crop, reference images). A crude motion pass driving local VACE is a $0 experiment.
4. **fal.ai pay-per-generation access to frontier video models (no subscription)** — NEW tooling intel; consistent with our no-subscription/no-spend-without-prototype rule if a hero shot ever needs Kling/Veo-class motion. Requires owner approval.
5. **Backdrop generation for green screen** — CONFIRM-adjacent inverse of our layered-composite engine (we put AI creatures on REAL footage; he puts AI backgrounds behind real subjects). Rexcaped spec requires real backgrounds — no change.
6. **The plugin itself** — CONTRADICT: Resolve-centered workflow vs our "FFmpeg is the engine, DaVinci optional" hard rule; paid; local mode Windows-only on Jeff's M5 Mac.

## Policy notes
None. Zero YouTube monetization/policy content.

## What we apply
- **Rexcaped**: add a fixed camera/lens/lighting/movement preset vocabulary block to the Grok i2v + VACE prompt templates (alongside the existing physics/mouth-closed riders) so shot language is consistent instead of re-prompted per beat. Free, today.
- **Rexcaped/AMBER**: one-beat test — crude blocked motion pass (even a PIL-animated cutout) as VACE driving video, AI as "render engine," on one real beat before any planning.
- **Prehistoric POV**: same preset vocabulary applied to the ChatGPT still-series prompts (lens + lighting consistency across a POV sequence).
- **Bizdoc**: nothing — channel uses real footage/stills; no application.

## Verdict
Low-to-moderate value: it's an ad, but two free ideas transfer. ADOPT preset prompt vocabulary; TEST clay→VACE motion pass; CONFIRM stills-first i2v and pay-per-gen philosophy; IGNORE the plugin, fal.ai spend (unless owner asks), 3D-from-image, and backdrop gen.
