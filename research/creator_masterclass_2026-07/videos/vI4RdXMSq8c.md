# Sandy Lee AI — "How I Fully Automated Video Editing (Claude Code)" (vI4RdXMSq8c, 21:27, 18.2K views)

## What the video is
A tool-demo/tutorial for talking-head creators: Claude Code + Whisper + FFmpeg edits raw footage (cuts, dead-space trims, brand-kit captions, SFX), Hyperframes (HeyGen's open-source framework) renders motion graphics, and Higgsfield's MCP generates AI B-roll from transcript context. Workflow: `raw/` → `output/` folder convention, a `brand.md` (font/colors), a saved Claude Code skill `/long-form-edit` that runs the whole pass.

## What's actually shown (evidence)
- Live demo (~9:51–20:45): Whisper transcript pulled (~2–3 min), Claude builds a cut list, "identify 4–5 word-motivated B-roll moments," Higgsfield MCP calls visible, Hyperframes preview then MP4 render.
- Her own caveats: preview stalls on camera; "prompting back and forth a couple of times"; "I have to tell Claude a couple of times like fix this, fix that"; "don't expect anything to come out perfectly from the first round."
- Ops details: `/mcp` to verify server connections; restart the IDE if MCP won't connect; Opus for planning, Sonnet for execution ("Fable is way too expensive to do this"); runs Claude Code inside free Antigravity IDE.
- Cost claims: Max plan $100/mo covers editing ("tokens not credits"); Higgsfield B-roll $2–$7/video; human editors $50–$3,000/video (unverified anchor).
- Pre-spend gate: Claude is instructed to ask clarifying questions BEFORE generating Higgsfield B-roll "so that I don't have to waste my credit."

## Credibility
Medium. The mechanics are real and demonstrated live, and she's honest about iteration friction — which quietly refutes her own "fully automated / I'm not technical" framing. Motive is clear: the description carries a Higgsfield referral link (`higgsfield.ai/s/mcp-sandyleeai-...`), the actual workflow markdown is gated inside her paid Skool community, and sleeautomation.com is a lead magnet. So the Higgsfield push is affiliate-shaped; the Whisper/FFmpeg/Claude core is genuine. No revenue claims, no analytics shown.

## Tactics extracted (vs our playbook)
1. **Claude Code + Whisper + FFmpeg as the edit engine** — CONFIRM. This is a beginner version of our entire pipeline (WhisperX align → paper edit → ffmpeg_production_render.py → verify_render.py). Ours is deeper (word-level realign, auto-QA watcher).
2. **Hyperframes (free, open-source, HeyGen) for programmatic motion graphics/chart animations/captions** — NEW tool lead. We have nothing that animates charts; bizdoc stat beats are static cards + Ken Burns.
3. **Higgsfield MCP context-driven B-roll ($2–7/video)** — CONTRADICT hard rules (new paid subscription) and redundant vs Grok i2v + VACE at $0. Affiliate-driven.
4. **Screenshot-a-style → Claude restyles to your brand kit** (Dan Martell caption example) — CONFIRM of our measure-the-competitor method (viral_recreation_spec / edit_grammar_ruleset), applied to on-screen text.
5. **Ask-questions-before-spending-credits gate** — CONFIRM of no-spend-without-prototype + approval ledger.
6. **Opus-plan / Sonnet-execute model tiering** — NEW-ish ops discipline for long render/QA sessions on a capped plan.
7. **Workflow saved as a slash-command skill + per-channel brand.md** — CONFIRM in spirit (our playbook/scripts), but skill-ifying the Rexcaped edit pass is a cheap ergonomic win.

## Policy notes
None. Zero YouTube monetization/policy content.

## What we apply
- **bizdoc (one experiment)**: prototype Hyperframes on ONE killer-stat beat of "Breaking the Law" (Pinto formula or Meta $5B) → animated chart clip → composite via the FFmpeg renderer. Adopt only if it beats the static card.
- **all (free)**: Sonnet for mechanical batch work (render/verify/realign), Opus/Fable only for design decisions.
- **bizdoc (free)**: write a `brand.md` (fonts, hex, overlay style) the way style_bands.json already locks Rexcaped, so sessions stop re-deriving card styling.
- **rexcaped (free)**: wrap rexcaped_edit_engine invocation as a `/rexcaped-edit` skill.

## Verdict
Mostly a mirror of what we already built, pitched at beginners, with one real lead. TEST Hyperframes; ADOPT model tiering + bizdoc brand.md; IGNORE Higgsfield (affiliate, paid, redundant).
