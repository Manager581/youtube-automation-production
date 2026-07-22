> **⚠ Read [CRITIQUE_AND_SEQUENCE.md](CRITIQUE_AND_SEQUENCE.md) first — it is authoritative on hours, conflicts, and whether this play runs now, is gated, or is parked.** Individual plans assume they run standalone; the portfolio does not have hours for all five.

# PLAY #2 — High-RPM Business Documentary Channel (fresh channel, new topic)

**Owner:** Jeff Lawrence · **Written:** 2026-07-22 · **Horizon:** 90 days (13 weeks)
**Standing order:** the prior video is DEAD as a deliverable. Nothing below uploads, re-cuts, or references it. What this plan inherits is the *pipeline*: `scripts/ffmpeg_production_render.py` (renderer), `scripts/verify_render.py` (auto-QA watcher), `scripts/make_whisperx_alignment.py` + `scripts/realign_paper_edit.py` (word-level timing), `pipeline_v2/topic_scorer.py` (9-test gate), the 7-module `playbook/*.json` + `playbook/loader.py`, and `scripts/make_thumbnail.py`. All verified on disk 2026-07-22.

**Hours honesty:** this play needs **~10 hrs/week as the PRIMARY play** (of the 10–15 hr/week total side-operation budget). It cannot run alongside another primary play; Rexcaped/PPOV drop to ≤2 hrs/week maintenance if this is chosen. One 19–25-min documentary ships every **2 weeks** (~19–20 production hours each — breakdown in §4). Anyone promising weekly long-form documentaries at 10 hrs/week is lying; the corpus's own quality-over-volume receipt (BePppCvXC-k: ~5 videos in ~100 days) supports the biweekly bet.

**90-day revenue honesty up front:** realistic case is **$0–50** (affiliate clicks only; YPP not yet reached). This play's 90-day output is *monetizable inventory + algorithm classification*, not cash. The receipted AdSense math is in §5 — plan on **$3–6 RPM** (receipted, BePppCvXC-k), not the $10–25 folklore.

---

## 1. Decisions required from Jeff before Day 1

| # | Question | Recommended default | Why |
|---|---|---|---|
| D1 | **Which sub-niche locks for the first 5 uploads?** (Procedure and 3 candidates in §3 — a fresh channel must stay in ONE story family so recommendation cohorts converge: 9iP588aMFBc, q0G-FzS6uxk, tactic_map 5.11.) | **Candidate A: "Who Actually Owns It" — private-equity / hidden-ownership documentaries** (deepest public-data supply, named-villain structure matches the scorer's calibration winners). Ratify after the Day-2 scorer run. | Best blind-spot scores + weakest incumbent coverage of the three (analysis in §3). |
| D2 | **Channel identity: real name or pseudonymous brand?** | **Pseudonymous channel brand, no face, no real-name byline.** Faceless documentary needs no employer clearance the way Plays #1/#3 do; keeps the day-job firewall. | Task attraction (competence + info density) suffices for educational channels — no face needed (Xf_J7kBzxvo). |
| D3 | **Voice: Jeff's own ElevenLabs voice clone, or a distinct library voice?** | **Own-voice clone made inside the existing paid ElevenLabs account.** F5-TTS is CC-BY-NC — banned for monetized VO (hard constraint). Own voice = licensed, differentiated, and the anti-"stock-voice sameness" hedge (CxwFu1nEsZQ, YtpQSmu794k, tactic_map 6.18). | One-time ~30-min setup; if Jeff declines voicing, fall back to an *obscure* library voice, never Liam/Jessica/Brian-tier popular ones. |
| D4 | **AI-disclosure stance, written once:** answer YES to the altered/synthetic-content question on every upload containing AI-generated imagery or synthetic VO; document the cloned-own-voice position (self-clone ≠ impersonation, disclose anyway). | **Yes / disclose, recorded in the channel ops doc.** | #1 platform risk demands a consistent documented stance (eF75ZffgsUk; policy_dossier §6.1.1, §6.4). |
| D5 | **Account structure: new Brand Account with its own future AdSense, or shared with Rexcaped/PPOV?** | **Separate Brand Account; audit AdSense linkage before launch.** Ban propagation across channels on one AdSense account is practitioner-claimed, unverified — the hedge costs minutes (YtpQSmu794k; policy_dossier §6.1.4). | Cheap insurance against correlated loss. |
| D6 | **Approve day-one affiliate signups** (free): Incogni, DeleteMe, Proton, NordVPN affiliate programs — the privacy/data-broker category already planned for mid-rolls. Jeff creates the accounts himself (credential work is his, not the agent's). | **Yes — sign up Day 3.** | Only revenue available pre-YPP (LGYiPA5SKvw, TvJhpOxFRsE; §5). |
| D7 | **Ratify the hours trade:** bizdoc = primary (10 hrs/wk); Rexcaped/PPOV maintenance-only for 13 weeks. | **Yes, or don't start this play.** | Two primary plays at 10–15 total hrs/wk is arithmetic failure. |

---

## 2. Day 1–7 concrete setup

Every step names its tool and output artifact. Total: **~10 hrs** across the week.

### Day 1 (1.5 h) — channel + compliance scaffolding
1. **Create the Brand Account + channel** (Chrome, Jeff's Google identity). Name diligence first: candidate name through YouTube search + WIPO Global Brand Database (LGYiPA5SKvw). *Artifact:* live empty channel; name-diligence note in the ops doc.
2. **AdSense-linkage audit** (Chrome: Google account → AdSense/monetization settings for all three channels). *Artifact:* one paragraph in the ops doc recording which channel attaches to what (YtpQSmu794k).
3. **Feature-eligibility pre-flight** (Studio → Settings → Channel → Feature eligibility): phone verify → intermediate (custom thumbnails) → advanced ID verify (>15-min uploads — a 19–25-min doc literally requires it) (eF75ZffgsUk). *Artifact:* all three tiers enabled.
4. **Channel ops doc** started: `docs/bizdoc_channel_ops.md` in the repo (Write tool) holding D1–D7 answers, the AI-disclosure stance, the patience-doctrine windows (§6), and the upload checklist below.

### Day 2 (2.5 h) — niche lock, run for real
5. **Run the niche-lock procedure of §3**: three candidate files → `venv/bin/python pipeline_v2/topic_scorer.py --file <candidates>.txt --niche "<sub-niche>" --output scorer_<sub-niche>.json` (3 runs) + the free supply checks. *Artifacts:* 3 scorer JSONs + `research/bizdoc_niche_lock.md` with the decision table filled in.
6. **Jeff ratifies D1** on the evidence. *Artifact:* decision logged in the ops doc.

### Day 3 (2 h) — monetization + identity plumbing
7. **Affiliate signups** (Jeff, in browser): Incogni, DeleteMe, Proton, NordVPN partner programs. *Artifact:* 4 tracked links in `docs/bizdoc_description_template.md`, each carrying `?video=<ytid>`-style attribution params (Eb8wlFawjTw, tactic_map 7.10) and the FTC line "This description contains affiliate links" (LGYiPA5SKvw).
8. **ElevenLabs own-voice clone** (D3): Jeff records ~2 min of clean read; create the voice in the existing paid account. *Artifact:* locked channel voice ID noted in ops doc.
9. **Cold-start seeding** (4xWQ_fHLGAc, 3MPSrpIOpAo; action_plan bizdoc DO-NOW): keyword-rich channel description (~5 high-volume sub-niche terms), same set in Studio → Channel keywords, country set, banner/avatar from the brand kit (next step). *Artifact:* completed channel About page.

### Day 4 (2 h) — brand kit + the Week-1 one-sample proof, part 1
10. **`brand.md` styling lock** (Write tool): fonts, hex palette, lower-third/card/overlay rules, caption style — the bizdoc equivalent of Rexcaped's `style_bands.json` (vI4RdXMSq8c, PaXuebdY75U; action_plan bizdoc DO-NOW). Seed it with a **design-brain extraction**: ~50 frames from ColdFusion/HMW/Wendover reference videos → Claude derives the design-guidelines spec (PaXuebdY75U). *Artifact:* `docs/bizdoc_brand.md` + thumbnail/card templates.
11. **Remotion/Hyperframes animated-stat prototype — setup**: `npx create-video@latest` (Remotion, free ≤3-person org) and clone `github.com/heygen-com/hyperframes` (free, open source). *Artifact:* both repos building locally.

### Day 5 (2 h) — the one-sample proof, part 2 (prototype-before-plan, hard rule #2)
12. **Build ONE killer-stat beat both ways** — the lead video's central number (e.g., the ownership-consolidation counter for Video 1, §4): Claude Code drives Remotion (oWkUwno6b0E workflow) and Hyperframes (vI4RdXMSq8c) to an animated stat card each, rendered **ProRes 4444 WITH ALPHA** (never green-screen keying — CLAUDE.md H.264-kills-alpha rule), composited as an overlay beat by `scripts/ffmpeg_production_render.py`, checked by `scripts/verify_render.py`. *Artifacts:* two ~8-s MP4/MOV beats + a composited test render + watcher HTML report. **Pass = visibly beats a static card + Ken Burns on Jeff's pick AND renders clean through the watcher. Winner becomes the standing stat-graphic tool; loser is filed.** Timebox 3 h total; if both fail, ship Video 1 with static cards and retry in Week 4 — the prototype gates the *capability*, not the schedule.

### Days 6–7 (2 h) — Video 1 research begins
13. **Research pack V1** (per §4 workflow, stage 2): SEC EDGAR / DOJ / PACER-mirror documents + existing reporting for the #1-ranked topic. *Artifact:* `research/<slug>/sources.md` with links, killer stats, and "First reported by" credits list (source-credit rule, CLAUDE.md).
14. **Account warm-up** running all week: real watching/liking in the sub-niche from the new account (folklore-grade but free; q0G-FzS6uxk) — doubles as competitor deep-watch.

---

## 3. The niche-lock decision (one sub-niche for uploads 1–5)

**Why lock:** early uploads clustered in ONE story family let the recommender's test cohorts converge on a stable audience cluster (9iP588aMFBc; q0G-FzS6uxk; tactic_map 5.11 — MEDIUM evidence, mechanism-consistent, free). Locked for uploads 1–5; loosened only per the 80/20 rule after a first outlier (5.10).

### 3a. The three candidates

| | Sub-niche | Story family | Public-data anchors | 3 sample stories |
|---|---|---|---|---|
| **A (recommended)** | **"Who Actually Owns It"** — private-equity rollups & hidden ownership of everyday services | "The thing you use every week is secretly owned by X, and here's what the filings show it did" | SEC 10-K/13-F, bankruptcy dockets, FTC/DOJ actions, Senate/GAO reports, CMS data | Vet-clinic rollups (Mars/VCA); mobile-home-park acquisitions; ER physician-staffing (Envision Ch.11 docket) |
| **B** | **"The Fee Machine"** — the documented machinery of hidden fees and middlemen | "Here is the actual mechanism, from the regulator's own filing, that makes X cost more" | DOJ v. Ticketmaster antitrust complaint, FTC junk-fee rulemaking docket, FTC PBM interim reports, CFPB enforcement actions | Ticketing fee stack; pharmacy-benefit managers; airline seat/bag fee economics from 10-Ks |
| **C** | **"Tech's Money Problems"** — the financial reality under the AI boom | ColdFusion-style: "the filings say something different from the keynote" | SEC filings/8-Ks, earnings transcripts, court dockets on AI suits | AI-datacenter capex vs revenue; circular vendor-financing deals; an AI unicorn's S-1 vs reality |

### 3b. Scoring procedure (run Day 2 — mechanical, all free)

1. **Candidate generation:** one Claude session per sub-niche using `playbook/ideation.json` via `playbook/loader.py` → **10 candidate topics each** (30 total), including 2–3 mashup/transplant candidates per tactic_map 5.8/5.3. *Artifact:* `candidates_A.txt / _B.txt / _C.txt`.
2. **9-test scorer:** `venv/bin/python pipeline_v2/topic_scorer.py --file candidates_X.txt --niche "<sub-niche> documentary" --output scorer_X.json`. GO = 85+ overall with all tests ≥65 (the scorer's own thresholds, verified in-file).
3. **Corpus supply-check** per topic, 5 min each, logged next to the score (tactic_map 5.6 — 8KXlxAKOTdE, tICnK3Qb2k8, 8N7-vQ9qX4w): (a) YouTube search-bar count of near-identical treatments — **3+ with no differentiated angle = drop**; (b) Studio Research/Trends interest read; (c) Google Trends line. Plus the **monetization-survivor scan** on the 3–5 nearest comparable channels — hits-then-sudden-silence = format flagged (zJmYdcvwY1Y, tactic_map 5.7) — and the **niche-gap thresholds** as notes: incumbents at 300–500K views/video posting <1×/week = gap signal (PtO7jd8L2xs, tactic_map 5.2).
4. **Decision rule:** lock the sub-niche with the most GO verdicts (need ≥5 of 10) **and** ≥half its GO topics passing the supply check **and** no survivor-scan red flag. Tie-break: sponsor-fit — stories that attract privacy/money-anxious viewers convert better on the planned affiliate category (TvJhpOxFRsE, tactic_map 1.6) — then Jeff's interest (he has to read bankruptcy dockets for 13 weeks).

**Speculation (pre-run assessment, to be replaced by the Day-2 artifacts):** A should win — deepest untapped story supply, named-villain structure identical to the scorer's own calibration winners (Wendover's Southwest/PE video, 2.7M), and the weakest YouTube incumbency; C scores highest on timeliness but fails supply checks hardest (ColdFusion + a dozen clones already live there); B is the strongest backup and the natural 80/20 "adjacent lane" after upload 5.

---

## 4. The first 5 deliverables + full per-video workflow

### 4a. The launch slate (Candidate A, pending the Day-2 scorer run)

Working titles use the adversarial-curiosity patterns already in `playbook/titles_thumbnails.json` (tICnK3Qb2k8, tactic_map 1.7). Each story rests on SEC/DOJ/court/agency documents — no original journalism. **8–10 candidates enter the scorer; these are the 5 predicted survivors — the scorer + supply check may reorder or replace any of them, and that's the system working.**

| # | Working title | Killer stat / blind spot | Public-data anchor |
|---|---|---|---|
| 1 | **"One Candy Company Owns Your Vet"** | A confectionery giant owns thousands of vet clinics; visit prices vs filings | FTC merger/consent materials, state filings, corporate disclosures |
| 2 | **"Your ER Doctor Works for a Hedge Fund"** | Physician-staffing rollup → surprise-billing machine → Chapter 11 | Envision bankruptcy docket, No Surprises Act arbitration data, Senate reports |
| 3 | **"Wall Street Bought the Trailer Park"** | The last affordable housing became a yield product; documented rent escalations | SEC filings of park REITs/funds, congressional letters, HUD data |
| 4 | **"How Wall Street Killed the Instant Pot"** | A beloved profitable product; the debt that ate it | Instant Brands Chapter 11 docket, PE dividend-recap coverage credits |
| 5 | **"The Funeral Home Monopoly"** | One company, ~2,000 funeral homes under local family names | FTC Funeral Rule docket, SCI 10-Ks, state AG actions |

Congruence gate on every one: title + thumbnail + cold open generated together; first ~5 s of the cut must visually echo the thumbnail (YtpQSmu794k, tactic_map 1.2; action_plan bizdoc DO-NOW).

### 4b. Per-video production workflow — tools, artifacts, hours (~19.5 h/video)

| Stage | Tool | Output artifact | Hours |
|---|---|---|---|
| 1. Topic gate (re-confirm) | `pipeline_v2/topic_scorer.py` + 5-min supply checklist | scorer JSON + supply log in `research/<slug>/` | 0.5 |
| 2. Research pack | Chrome (SEC EDGAR, DOJ releases, court-records mirrors, agency reports) + Claude synthesis | `research/<slug>/sources.md` — facts, killer stats, "First reported by" credit list | 3.5 |
| 3. Script | Claude drafts against `playbook/scripting.json` + `intros.json` + `retention_delivery.json` (loader: `playbook/loader.py`); Jeff edits to the 95+ bar. QA passes: coffee-shop lint + direct-address count (Xf_J7kBzxvo, 2.2), conciseness/ramble strip (ROPkHP8jpW0, 6.19), overage-prune on list beats (YtpQSmu794k), 20–40 s re-hook check (oWkUwno6b0E, 2.1), 3–5 cold-open variants → pick the thumbnail-congruent one | `research/<slug>/script_FINAL.md` (locked) | 3.5 |
| 4. VO | ElevenLabs, **one pass on the locked script**, split at paragraphs, SHA-verify the textarea (memory: elevenlabs-one-pass rule) | `audio/<slug>/narration.wav` | 1.0 |
| 5. Align | `scripts/make_whisperx_alignment.py` (word-level) | `audio/<slug>/narration_alignment_whisperx.json` | 0.25 (machine does the rest) |
| 6. Assets | Image-sourcing rules (CLAUDE.md): YouTube stills, Google Images, Wikimedia, news sites, archives, Chrome screenshots — **NO Pexels/Pixabay images**. Fair use: ≤7 s/clip, ≤30 s/source, clip audio muted, zoom/crop + overlay transformation. Text as overlays, never baked into gens (4xWQ_fHLGAc, 9.2). Animated stat beats from the §2 prototype winner (Remotion or Hyperframes → ProRes 4444 alpha). Materialize iCloud-dataless files before render | `footage/<slug>/`, `assets/<slug>/` + asset manifest | 5.0 |
| 7. Paper edit | Claude builds the beat JSON; `scripts/realign_paper_edit.py` snaps beats to WhisperX word times | `storyboards/<slug>_paper_edit_v1.json` | 1.5 |
| 8. Render | `scripts/ffmpeg_production_render.py --preview` (540p check) then full 1080p | `output/<slug>_FINAL.mp4` | 0.5 human (renders run unattended) |
| 9. QA | `scripts/verify_render.py` (not_black, coverage, narration transcription, overlays) + contact-sheet frame pass + phone "bed test" (ROPkHP8jpW0; action_plan cross-channel) | `output/verify_<slug>.html` + fix list → re-render if needed | 1.5 |
| 10. Package + upload | Thumbnail: `scripts/make_thumbnail.py` / brand-kit template + reference-conditioned gen (3 ColdFusion/HMW-referenced generations vs template — tactic_map 1.3; real photos only for real people, text added in post, desaturation knob per 1.4). Title A/B candidates; description first 2 lines = plain audience+subject keywords (9iP588aMFBc, 1.5); chapters; affiliate + credit links with `?video=<ytid>`; **AI disclosure = YES**; upload unlisted → public after HD processing (4xWQ_fHLGAc, 7.4); pinned comment + first-hour replies (YtpQSmu794k, 7.5). Archive appeal packet: script lineage, sources.md, watcher HTML (ipbnR92Elxg; policy_dossier §6.1.5) | Live video + `docs/uploads/<slug>_package.md` | 1.75 |
| **Total** | | | **~19.5 h** |

Runtime target: **19–25 min** — inside the receipted mid-roll window (§5) without padding; length stays story-driven (conflict ledger #4).

---

## 5. Revenue mechanics + honest milestones

### 5a. The receipted math (what we plan on)

- **Mid-roll eligibility begins at 8 min**; a 19–25-min doc carries multiple mid-roll slots. The only on-screen revenue receipt in the 54-video corpus: **~$3 RPM at ~25 min → ~$6 RPM at ~34 min** (BePppCvXC-k, revenue tab shown — **receipted**). Planning number for this channel: **$3–6 RPM**.
- The **"finance/legal pays 10× entertainment"** claim ($10–25 RPM) is **folklore** — asserted across tICnK3Qb2k8/Ao_d-uaMJvk/Oi3nSYYQ6sM with zero screenshots (policy_dossier §5). If it materializes, it's upside, never the plan.
- **Pre-YPP views pay $0, forever** — no retroactive payment (BePppCvXC-k — **receipted** on-screen; ~40K unpaid watch hours in the shown case). Consequence: apply to YPP the moment thresholds hit; expect the ~5-day watch-hour analytics lag (**practitioner-claim ×2**: BePppCvXC-k + 4xWQ_fHLGAc); ship a sub-CTA Short if watch hours outpace subs (BePppCvXC-k, tactic_map 4.5).
- YPP thresholds: 1K subs + 4K public watch hours (**official**). Observed first-upload→monetized in 14 days exists (4xWQ_fHLGAc, **practitioner-claim**) but is the outlier tail, not the plan.

### 5b. Where the first dollar actually comes from

**The day-one affiliate layer** (§2 Day 3): privacy/data-broker programs in the descriptions from Video 1, FTC-disclosed, `?video=` attributed. Mechanic grade: **practitioner-claim** (LGYiPA5SKvw showed terms + math; TvJhpOxFRsE's four-layer stack is asserted). Conversion at cold-channel view counts is an **analyst estimate**: low-hundreds of views/video × sub-1% click × single-% conversion → **first affiliate dollar plausibly days 30–90, $10–50 total by day 90**. That's the honest number.

### 5c. 90-day cases (all totals = analyst estimates built only on receipted/practitioner inputs)

| Case | Assumptions | Day-90 position |
|---|---|---|
| **Realistic** | 6 uploads; best video 2–8K views; 150–500 subs; 300–800 watch hours; YPP **not** reached | **$0 AdSense + $0–50 affiliate.** Assets: 6-video monetizable back catalog, classified audience cluster, appeal packet per video |
| **Optimistic** | One upload outliers (≥10× channel median — the pattern behind every corpus case study); 1K subs + 4K hours cross ~day 60–75; YPP granted after review (declines happen; appeals with evidence succeed — ipbnR92Elxg, practitioner-claim) | **$150–500**: ~30–80K monetized views × $3–6 RPM (receipted rate, estimated volume) + $50–150 affiliate |
| **Failure-shaped** | Flat impressions after 5 uploads, diagnostics point at niche | $0; §6 pivot fires — the pipeline and channel survive, the sub-niche doesn't |

Month 4–6 is where AdSense becomes real in the realistic case; a channel holding **$3–6 RPM at 50K views/month ≈ $150–300/month** — that's the honest medium-term shape unless an outlier changes the curve.

---

## 6. Weeks 2–13 cadence + metrics + kill/scale criteria

### 6a. Cadence (10 hrs/week; each video spans 2 weeks of stages)

| Week | Ships / happens |
|---|---|
| 1 | §2 setup + prototype + Video 1 research (10 h) |
| 2 | Video 1: script → VO → align → assets started |
| 3 | **Video 1 LIVE** (assets → paper edit → render → QA → package). 2 Shorts cut from its killer-stat beats (FFmpeg 9:16 crop — manual one-offs, not a pipeline build) |
| 4 | Video 2 research + script. **72-h no-read rule holds on V1** (q0G-FzS6uxk, 7.3) |
| 5 | **Video 2 LIVE.** V1 day-14 read: read-only, queue-informing (BePppCvXC-k) |
| 6 | Video 3 research + script |
| 7 | **Video 3 LIVE** |
| 8 | Video 4 research + script. **Day-30 checkpoint** (below) |
| 9 | **Video 4 LIVE** |
| 10 | Video 5 research + script |
| 11 | **Video 5 LIVE — niche lock complete (5 uploads, one story family)** |
| 12 | Video 6 research + script: **80/20 decision** — if any upload outliered (≥10× channel median), V6 is its direct sequel-on-steroids (BePppCvXC-k, 5.10); else next-ranked scorer topic |
| 13 | **Video 6 LIVE + Day-90 verdict.** Weekly ~30-min channel-audit habit starts (manual Studio read; automate later per action_plan build #2) |

Standing post-upload protocol on every video (action_plan cross-channel; 7.3 — STRONG evidence): 72-h no-read → day-14 first read → day-14 earliest repackage → week 4–6 earliest write-off → **never delete/unlist flops** (winners retro-test the back catalog, 9iP588aMFBc).

### 6b. Decision points

**Day 30 (~2 uploads): diagnostic only — no verdicts** (patience doctrine, STRONG: BePppCvXC-k, ROPkHP8jpW0, 9iP588aMFBc, q0G-FzS6uxk). Record per video: impressions, CTR, AVD, browse/search split. Distinguish **zero-impressions** (distribution/classification problem → check packaging adjacency per 1.5) from **impressions-but-no-clicks** (packaging → thumbnail-only Test & Compare when powered; never combined tests, 8N7-vQ9qX4w) from **clicks-but-no-retention** (edit/script → retention-graph read against the script's re-hook map).

**Day 60 (~4 uploads): first real read.**
- Any video ≥5K views or channel impressions trending up → **stay the course**.
- Flat but diagnostics say packaging → repackage the 2 oldest (day-14+ rule respected), don't change niche.
- Flat and diagnostics say niche (impressions served, cohort won't click across 4 distinct packagings) → prepare Candidate B slate through the §3 procedure; decision, not execution.

**Day 90 (5–6 uploads): keep / scale / pivot.**
- **SCALE** if ≥1 outlier exists: V7+ = sequel + 80/20 formula lock; YPP application the day thresholds hit; sponsor outreach becomes worthwhile at ~25K+/video (analyst estimate).
- **KEEP** (default) if best video >2K views with rising impressions: continue biweekly, month-4 target = YPP thresholds.
- **PIVOT sub-niche** (same channel, same pipeline, Candidate B) if <100 subs AND flat impressions AND day-60 diagnostics pointed at niche. Uploads stay live.
- **KILL the play** (retire to Rexcaped/other plays) only if BOTH A and B slates flat-line by month ~5 — 90 days cannot kill it honestly given the 14-day/4–6-week evidence windows; committing to that falsely would just re-create the judge-a-channel-too-early error the corpus warns about (5.9).

---

## 7. Risks + mitigations

| Risk | Grade | Mitigation (named system) |
|---|---|---|
| **July-2025 "inauthentic content" / mass-produced sameness enforcement** — the #1 platform risk; the rejection term used in the wild is "mass-produced," triggered by sameness, not AI voice (4xWQ_fHLGAc, practitioner; policy_dossier §2) | Real, documented | Vary the per-video edit fingerprint (renderer settings + `scripts/extract_motion_events.py` diff between uploads); template refresh every ~8–10 uploads (PtO7jd8L2xs, 0SPqPnpQsWE); 95+ human-edited scripts; own-voice VO; per-video appeal packet (scripts, sources.md, watcher HTML) — declines get appealed with evidence (ipbnR92Elxg) |
| **YPP application declined** | Practitioner-documented, recoverable | Appeal packet above; delete-nothing; the 4xWQ_fHLGAc remedy (style variation) is already structural |
| **Copyright / Content ID on sourced clips** | Real | Existing fair-use armor: ≤7 s/clip, ≤30 s/source, muted clip audio, zoom/crop + overlay transformation, on-screen "First reported by" credits; prefer non-YouTube sourcing (YouTube-internal reuse detection is strongest — PtO7jd8L2xs) |
| **Defamation/accuracy on named-villain stories** | Real, self-inflicted only | Public-documents-only rule (`playbook/sources.json`): every claim traces to a filing/agency document; allegations labeled as allegations; fabrication is also a demonetization vector (zJmYdcvwY1Y; policy_dossier §9.3) |
| **RPM disappointment** — the 10× claim is folklore | Certain to matter | Already planned on receipted $3–6; affiliate layer decouples first dollars from RPM |
| **Hours overrun** (research-heavy stories blow the 19.5-h budget) | Likely early | Timebox research at 4 h — a story that can't be sourced in 4 h fails `source_availability` and gets swapped for the next scorer-ranked topic; the slate is 8–10 deep for exactly this |
| **Judge-flagged uncertainty: slow first dollar vs Plays #1/#3** | Certain | Stated honestly in §5; the compensating asset is compounding inventory + zero employer-clearance exposure (D2) |
| **Voice-clone disclosure ambiguity** | Minor | D4: disclose synthetic VO uniformly; own-voice clone via paid ElevenLabs is license-clean (F5-TTS stays banned for monetized output) |
| **Distribution-side squeeze on faceless AI content** (ZKsldrcO_fU, vidIQ prediction — opinion) | Directional | Persona markers: signature sign-off, recognizable intro cadence, on-screen source-credit convention — the channel reads as a voice-brand, not commodity faceless AI (action_plan bizdoc DO-NOW) |

---

## 8. DO-NOT list (play-specific)

1. **Do not upload, re-cut, or reference the dead prior video as a deliverable.** Pipeline only. (Owner order.)
2. **No Pexels/Pixabay images** (Pixabay music only); no stock-site shortcuts under deadline pressure. (Hard rule.)
3. **No new paid APIs/subscriptions/tools** without explicit owner approval — no VidIQ paid, NexLev, TubeBuddy, Pikzels, kie.ai, Higgsfield, fal.ai-by-default. Remotion/Hyperframes are free; everything else in this plan is owned or free. (Hard rule; action_plan DO-NOT.)
4. **No F5-TTS voice on any monetized upload** — CC-BY-NC. ElevenLabs only. (Hard rule.)
5. **No AI-generated human faces, ever** — real photos with Ken Burns for real people; AI disclosure = YES every upload. (Hard rule; policy_dossier §6.)
6. **No reused-clip laundering** — "text overlay makes it transformative" is folklore and the policy's explicit target (QfbGKfkGP8U rejected; policy_dossier §3). Fair-use rules are not negotiable under deadline.
7. **No padding for runtime.** Length is story-driven; the mid-roll effect is captured at 19–25 min without stuffing (conflict ledger #4).
8. **No auto-generated news/story scripts without the document trail** — the moat is verified public-data sourcing (TiycelzfzC0/8Mx2m0djgTA pipelines have no fact-check step).
9. **No Reddit/social link-blasting** of uploads (low-intent clicks poison retention and later CTR — q0G-FzS6uxk); no sub4sub, no bought views, **no YouTube Paid Promotions** (~$0.53/sub benchmark, no flywheel — ROPkHP8jpW0; no-spend rule).
10. **No deleting or unlisting flops**; no repackaging before day 14; no verdicts before week 4–6. (7.3, STRONG.)
11. **No combined title+thumbnail A/B tests** — single-variable only (8N7-vQ9qX4w).
12. **No second assembler.** Remotion/Hyperframes output feeds `scripts/ffmpeg_production_render.py` as alpha overlay assets; the FFmpeg engine remains the only assembler, DaVinci stays manual-polish-only. (Tool policy; action_plan build #5.)
13. **No breaking the niche lock before upload 5** — no ranging across business topics because a shiny story appeared; the shiny story goes into the scorer queue for slot 6+.
14. **No buying channels, accounts, credits, or engagement of any kind.** (Hard rule; policy_dossier §4.)

---

*Every mechanic above cites its corpus evidence (video ids) or a verified repo file. Revenue numbers carry their evidence grade at point of use: receipted = BePppCvXC-k's on-screen revenue tab (the corpus's only long-form AdSense receipt, alongside YtpQSmu794k's Studio total); practitioner-claim = shown-but-unverifiable; analyst estimate = this plan's own arithmetic on those inputs.*
