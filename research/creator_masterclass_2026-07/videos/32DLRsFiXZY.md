# 32DLRsFiXZY — "I Made a Viral BeamNG-Style Video in 5 Minutes Using Only AI" (Ai pay you, 500s, 5,534 views)

## What the video is
A comment-gate/affiliate funnel tutorial for the AI "BeamNG-style" car-crash Shorts niche. Workflow: a "master prompt" in Claude generates 10 topic ideas → paste a topic back → scene-by-scene concept → type "okay" → paired image+video prompts per scene. Then Google Flow (free 50 credits/day): Nano Banana 2 image model, 9:16, generate stills; switch to video ("Omni" model, i.e. Veo-family) for i2v clips; chain clips by feeding the LAST FRAME of each clip as the start frame of the next ("add to prompt", or copy-video-frame + Ctrl+V when credits are low, or a fresh browser session for another 50 credits). Assemble in CapCut. The teased "secret" step is just: regenerate any clip with broken physics before uploading.

## What's actually shown (evidence)
Screen recording of the real Flow UI doing image gen, i2v, and the last-frame chaining (~03:00–06:06). View counts of OTHER channels (214M/182M/149M/255M views, a 4M-sub channel) shown as social proof at 00:00. No revenue of his own, no analytics of his own channel, no upload shown performing.

## Credibility
Low. Classic engagement-farm structure: comment-to-get-prompt gate, WhatsApp funnel, affiliate links (VidIQ, CapCut, and Pippit.ai — which never appears in the video at all, pure link stuffing). The description's own disclaimer admits figures are "estimates... NOT guarantees." "5 minutes" is implausible with gen times + editing. The "fresh browser = another 50 credits" move is TOS-violating multi-accounting. He also never mentions Flow's free-tier watermark (our own prior audit of Flow flagged it) or that Shorts RPM makes this niche pennies. BUT: the on-screen workflow is real and mechanically demonstrated — the last-frame continuity technique genuinely works and is the one piece of signal.

## Tactics extracted
1. **Last-frame continuity chaining** (04:36–05:36) — use the final frame of clip N as the i2v input image for clip N+1 → seamless "continuous recording" feel. NEW as an explicit technique; portable to Grok Imagine via FFmpeg last-frame extraction (`-sseof -0.1`). Maps to the ChatGPT-stills→Grok-i2v workflow.
2. **Two-stage LLM prompt factory** (topics → concept → "okay" → paired image+video prompts). CONFIRM — Claude Code already builds storyboards/TSV prompts more rigorously.
3. **Clip-level QC as "the viral step"** (06:37) — regenerate any clip with broken physics before upload. CONFIRM — this is literally our mandatory frame-level QA + i2v-real-physics rules.
4. **Flow free tier (50 cr/day, Nano Banana 2 img, Veo i2v)** as $0 gen. CONFIRM/known — already audited (watermark + YPP template-AI risk noted in memory); the multi-account refill is IGNORE.
5. **Niche pitch: BeamNG-style crash Shorts.** IGNORE — saturated, Shorts RPM, and it is the poster child for the July-2025 "inauthentic content" repetitive-AI demonetization policy the video never mentions.

## Policy notes
Zero policy intel. It promotes exactly the mass-produced, template-AI repetitive content YouTube's July 15 2025 inauthentic-content policy targets, while hiding the risk in a boilerplate disclaimer ("follow the platform's monetization and reused-content policies"). Also teaches Flow credit multi-accounting (Google TOS risk). Treat as a negative example.

## What we apply
- **Prehistoric POV (TEST, free):** last-frame chaining for continuous POV runs — extract the final frame of a Grok i2v clip with FFmpeg and use it as the next gen's input still instead of a fresh ChatGPT still. One chase sequence, frame-strip QA'd, is the experiment.
- **Rexcaped (TEST, narrow):** use chaining ONLY when a single action beat needs two gens (e.g., a strike longer than one clip). Across beats the clip-variety rule (distinct vantage per beat) still wins — do not chain the whole edit.
- **Bizdoc:** nothing. Niche and workflow are irrelevant to documentary format.

## Verdict
One real technique (last-frame chaining → TEST), two confirmations of existing QA/prompting practice, everything else is funnel noise or policy-risk. Do not enter the niche; do not multi-account Flow.
