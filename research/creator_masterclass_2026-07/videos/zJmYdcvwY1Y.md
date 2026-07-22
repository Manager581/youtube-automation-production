# zJmYdcvwY1Y — "Claude + Youtube = $7,356" (Timo Business, Russian, 15:38, 6,058 views)

## What the video is
A 16-year-old Russian-speaking operator ("Timofey") walks through a beginner faceless-slideshow pipeline: pick a proven sub-niche → rewrite a competitor's transcript in Claude → ElevenLabs VO → Claude-generated image prompts → Nano Banana 2 in Google Flow → manual CapCut slideshow edit. He showcases 3 sub-niches to copy ("what happens if you buy an airline/ranch/sports team", "everyday thing can kill you", WWII battles) and one anti-example ("10 types of rich people").

## What's actually shown (evidence)
- Revenue "shown somewhere on the screen" — never itemized in narration; the $7,356 title figure is never substantiated in the transcript.
- Niche recon with concrete signals: channel age (2 weeks / 1 month / 5 months), video counts (3 videos, 2 hits; 13 videos in 5 months), upload gaps.
- The workflow demo: VO first to get runtime → estimate image frequency (1 img/3s → 100 images per 5 min) → "break this script into 100 equal segments" prompt → style locked by feeding Claude a competitor frame → prompts generated 5 at a time (all-100-at-once makes prompts progressively compress) → Flow/NanoBanana 2, 16:9, 4 images per request, claimed unlimited → Claude revision pass "add colors to each prompt".

## Credibility
Low-to-medium. No verifiable revenue; the funnel is a Telegram channel holding the "real" prompts and a niche-selection guide, plus a "$10,000 guide" video link — classic audience-capture motive, though nothing is directly sold in-description. The strongest material is his niche recon (observable on YouTube); the weakest is every RPM/earnings number (asserted, not shown). The "Flow images are unlimited" claim conflicts with our own note that Flow's free tier is credit-capped for video — image credits unverified.

## Tactics extracted (vs our playbook)
1. **Monetization-survivor scan** — NEW. A channel with hit videos that abruptly stops uploading ≈ "90%" YPP denied/removed. Cheap pre-flight check for any niche we enter; maps to topic-scorer niche vetting. Directly relevant to our #1 risk (repetitive/inauthentic-AI demonetization).
2. **Nano Banana 2 via Google Flow bulk stills** (free, 4/request) — NEW tooling intel; candidate supplement to the painful ChatGPT one-download-per-tab still method.
3. **Prompt-batch degradation guard** (5 prompts/request, never all 100) — NEW minor; maps to our TSV prompt generation.
4. **VO-first → runtime → image count → equal-segment split** — CONFIRM; our WhisperX word-level alignment + paper-edit beats are strictly superior.
5. **Style lock from a competitor frame** — CONFIRM; style_bands.json + gate_style.py already do this measured.
6. **Voice matched to competitor's timbre, ElevenLabs V2, avoid popular voices** — CONFIRM (we already cast Liam etc. for Dinoverse).
7. **Formula adherence / frequency-as-advantage / real-facts-only / avoid repetitive ideas** — all CONFIRM of edit-grammar discipline, channel thesis, public-data rule, and known policy risk.
8. **Rewrite competitor transcripts for first videos** — CONTRADICT our 95+ original-script bar and a reused-content policy risk. Ignore.
9. **"Editing can't be automated" (CapCut manual)** — CONTRADICT; our FFmpeg renderer disproves it.

## Policy notes
Fabricated "facts" = deceiving the audience → demonetization/removal (aligns with the Jul-2025 inauthentic-content policy). Heavily repetitive idea sets flagged as demonetization bait. Vague warning about certain title/thumbnail words (garbled: "baby", likely "drugs"). The sudden-stop heuristic is his inference, not policy text — but it's a usable field signal.

## What we apply
- **All channels**: run the monetization-survivor scan on 3-5 comparable channels before committing to any new format (Rexcaped creature-attack space especially — it sits squarely in template-AI territory).
- **Prehistoric POV**: one experiment — generate one scene's still series via Flow/NanoBanana 2 vs the ChatGPT method; compare quality/throughput.
- **Bizdoc**: score the "what happens if you buy an airline/sports team" format through the 9-test topic scorer — it's adjacent high-RPM territory and World-Cup-timely.
- **Rexcaped**: chunk Claude prompt-gen ≤5 per request where prompts are generated conversationally.

## Verdict
One genuinely useful field heuristic (survivor scan), one free tool test (Flow stills), one topic-family lead for bizdoc. Everything else we already do better or should ignore. Net value: modest but non-zero.
