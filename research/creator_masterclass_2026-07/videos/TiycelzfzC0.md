# TiycelzfzC0 — "I 100% Automated Vox-Style Motion Graphics (Claude Code + Omni)" — Koen | AI Content Systems (830s, 9,654 views)

## What the video is
A build-along tutorial: create a project-local Claude Code skill (`/vox-video`) that turns one prompt into a short "Vox-style" animated news explainer. Pipeline: script gen (research from current events) → ElevenLabs TTS → speech split into 4–8 clips/chapter → style-consistent stills (GPT-Image-2 conditioned on ONE pre-made style-reference image) → i2v via Kie AI (Gemini Omni Flash; Seedance 2.0 Fast for public figures) → FFmpeg assembly with music. The complete system-build prompt is free in the description (prompts credited to Framework Explained).

## What's actually shown (evidence)
- Two real end-to-end runs on "the AI bubble," each ~38s, shown on screen (0:07 and 12:21). Output quality is genuinely decent stylized animation.
- Costs on screen: Claude $20/mo; Kie AI ~$3.50 per 35s chapter ($5 min top-up); ElevenLabs free→~$6.
- Full build prompt in description with the real mechanics: chapters ~30s; clips ONLY 4s or 6s; speech generated FIRST, word-level timestamps drive clip grouping; key-word timestamps embedded in i2v prompts ("if 'door' is said at 3s of a 6s clip, put that in the video prompt"); trim first 0.25s off every clip; keep clip-native SFX at LOW volume (not muted) under VO; random song from a music folder.

## Credibility
No revenue claims at all — the demo is the whole proof, and it's shown working. Motives: Skool community funnel ("Syndicate") + Kie AI and ElevenLabs affiliate links. But the full prompt is given away free, which is honest. Overclaims: "100% automated Vox-style" — output is a 38s animation, not Vox journalism; "Gemini Omni is the #1 AI video model" is unsupported. Critical flaw he doesn't notice: his two runs on the same topic state DIFFERENT figures (Nvidia $100B→OpenAI/Microsoft $250B vs. Oracle loop/$800B/-$14B) with zero sourcing — the "journalism" has no fact-check step.

## Tactics extracted
1. **Speech-first, word-timestamp-driven visuals** — CONFIRM: exactly our WhisperX → realign_paper_edit flow.
2. **Timestamp-conditioned i2v prompts** (motion event written into the gen prompt at the second the word lands) — NEW; maps to edit-grammar cut-on-word + motion-event ship-gate.
3. **One style-reference image conditions every still** — CONFIRM of style gate concept; NEW as an explicit per-still mechanic for ChatGPT/Gemini stills.
4. **Trim first 0.25s of every i2v clip** — NEW, free, mechanical; maps to rexcaped_edit_engine / FFmpeg assembly.
5. **Clip-native SFX at low volume under VO** — NEW-ish; maps to FFmpeg audio mix (does NOT override bizdoc clip_audio:mute, which exists for fair-use/VO integrity).
6. **4s/6s-only clips, 4–8 per 30s** — CONFIRM of measured 5–7s cut grammar.
7. **Public-figure evasion** (black bar on eyes, distant framing, never name the figure in the prompt, Seedance first-frame) — CONTRADICT: violates no-AI-human-faces hard rule and is safety-filter evasion.
8. **Kie AI pay-per-use aggregator** — NEW tool; conflicts with no-new-paid-APIs rule; Grok i2v + local VACE already cover i2v.

## Policy notes
The video says nothing about YouTube policy. Our read: one-prompt templated news animations at scale is the exact profile of the July-2025 YPP "inauthentic content" mass-produced risk; the public-figure black-bar trick produces synthetic depictions of real people (altered-content disclosure territory) via deliberate filter evasion; unverified auto-generated news claims add misinformation exposure. High-risk pattern — do not import.

## What we apply
- **rexcaped**: check frame strips for static first frames → add 0.25s head-trim to assembly; one-clip test of timestamp-in-prompt on a cut-on-word beat; try low-volume Grok-native SFX bed under VO.
- **prehistoric_pov**: attach a fixed style-reference image to every ChatGPT still gen instead of trusting thread memory; same 0.25s trim.
- **bizdoc**: test a style-consistent AI-illustration layer (one editorial style-ref image → Gemini/ChatGPT stills → existing Ken Burns) for abstract beats (money loops, "fine as line item"); NEVER adopt auto-generated unverified scripts.

## Verdict
Above-average for the genre: real demo, free prompt, concrete numbers, honest attribution. ADOPT the 0.25s head-trim check; TEST timestamp-conditioned prompts, style-ref-image stills, SFX bed; CONFIRM the alignment/clip-length/orchestration we already run; IGNORE public-figure evasion, Kie spend, and fact-check-free news generation.
