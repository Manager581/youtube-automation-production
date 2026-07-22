# "How to create Viral AI Roblox Videos for 100% Free" — Beckett Ai (sMo5RT_dPxc, 177s, 17K views)

## What the video is
A 3-minute tool-demo/niche-pitch: clone a 1.7M-sub Roblox-cartoon channel using a ChatGPT
"master prompt" (Google Doc in description) that emits scene-by-scene video prompts, then
generate each scene in Google Flow with the "Omni Flash" video model, chain scenes for
consistency, assemble in "your favorite video editor," export, post.

## What's actually shown (evidence)
- [00:00] One screenshot-level claim: a channel at 1.7M subs, "videos sitting at millions
  of views." No channel name verification, no analytics, no revenue.
- [00:30] ChatGPT master prompt → menu of "story modes" (picks #2, "Roblox funny story") →
  per-scene prompts. Typing "next" regenerates a new story.
- [01:00] Flow: paste scene prompt, Omni Flash model, scene renders.
- [01:15] Consistency Method 1: click generated video → three dots → "add to prompt" →
  paste scene-2 prompt (previous clip becomes visual reference).
- [01:30] Consistency Method 2: "save frame" on the last frame → three dots → "animate" →
  paste next scene prompt (seamless last-frame continuation).
- [02:02] Four generated scenes; a ~35s slapstick banana-peel result with canned dialogue.

## Credibility
Low. The description carries Edimakor AI affiliate links + a "65% off" discount — the
"100% free" tutorial is a funnel for a paid editor. The "free" claim itself is shaky: our
own 2026-07-20 assessment of this exact tool stack (AI cardboard DIY niche) found Omni
Flash is a paid Gemini-tier model and Flow's free tier is ~50 credits/day with watermark.
The description's "Tools Used: Chat GPT (Historical POV Shorts)" is a copy-paste artifact
from a different tutorial — this advice channel is itself a template farm. "Every Roblox
fan never skips Roblox content" is pure assertion. No upload of the demo, no view proof.

## Tactics extracted
1. **Master-prompt scene generator** (ChatGPT emits per-scene i2v prompts; "next" loops
   ideas) — CONFIRM, and strictly weaker than our Claude-driven storyboard/TSV + AMBER
   event-sheet pipeline and 9-test topic scorer.
2. **Prev-clip-as-reference chaining** (Flow "add to prompt") — CONFIRM direction; this is
   the reference-image consistency step already planned for AMBER/VACE; Flow itself unused.
3. **Last-frame → animate chaining** — the one genuinely transferable mechanic. Testable
   today in Grok Imagine i2v: feed the saved last frame of clip N as the still for clip
   N+1. NEW as an explicit continuity technique for us; note it CONTRADICTS the Rexcaped
   clip-variety rule if overused (same vantage twice), so scope it to continuous-action
   pairs and POV sequences only.
4. **Roblox cartoon niche pitch** — IGNORE: kids-adjacent audience (made-for-kids RPM
   collapse), saturated, and one-style channel cloning is textbook inauthentic-content
   exposure.
5. **Editor assembly step** — trivial; FFmpeg engine already exceeds it.

## Policy notes
The video never mentions monetization policy — a telling omission. Mass-producing a single
cloned cartoon format with templated AI scenes is exactly the repetitive/inauthentic
content profile YouTube's July-2025 YPP policy targets; our cardboard-DIY assessment
already flagged template-AI demonetization risk for this genre. Roblox content also risks
made-for-kids classification (limited ads, no personalization, low RPM).

## What we apply
- **prehistoric_pov**: TEST last-frame→animate chaining in Grok Imagine on one 3-scene
  continuous-POV run (walk→turn→encounter) vs current independent per-still gen; keep if
  it kills scene-boundary jumps. Free, one experiment.
- **rexcaped**: limited TEST of the same trick only on continuous-action beat pairs
  (strike→aftermath) where creature-position mismatch shows in frame-strip QA; never on
  adjacent list beats (clip-variety rule wins).
- **bizdoc**: nothing — irrelevant to documentary format.

## Verdict
Low-value affiliate content-farm tutorial. One mechanic worth a free experiment
(last-frame chaining); everything else is confirmation of weaker versions of systems we
already run, or an off-strategy niche pitch with real demonetization risk.
