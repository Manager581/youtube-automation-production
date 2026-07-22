> **⚠ Read [CRITIQUE_AND_SEQUENCE.md](CRITIQUE_AND_SEQUENCE.md) first — it is authoritative on hours, conflicts, and whether this play runs now, is gated, or is parked.** Individual plans assume they run standalone; the portfolio does not have hours for all five.

# Play 4 — Measured-Clone Channel into a Verified Content Gap
## Exact 90-day plan · Owner: Jeff Lawrence · Drafted 2026-07-22

**What this play is.** Spend weeks 1–2 running a numerically-gated gap scan (no channel exists yet). If — and only if — a niche passes every gate, weeks 3–13 clone it with the quantitative edit-grammar stack: measure the incumbent's top videos with `scripts/extract_edit_grammar.py` + `scripts/extract_motion_events.py`, derive a ruleset, produce on the existing $0 pipelines, and defend against "mass-produced" enforcement with measured fingerprint variation between uploads. If nothing passes, the play's deliverable is a **NO-GO memo + a standing 2-hour monthly re-scan** — forcing a channel into a non-gap is explicitly a failure mode of this play, not a fallback.

**Hours (honest):** 6–8 hrs/week for this play. Jeff's total cap is 10–15 hrs/week across everything; this play at full tilt is compatible with running Play 5 (existing creature channels) under its cap, and with nothing else. Weeks 1–2 need ~6 hrs/week (scan only). Production weeks need 7–8.

**Corpus grounding (headline):** the gap thresholds and scan mechanics are the corpus's most-repeated tactic family — outlier-vs-own-baseline scanning (Oi3nSYYQ6sM, 8KXlxAKOTdE, 4xWQ_fHLGAc, 8N7-vQ9qX4w, YtpQSmu794k, Z5Wn63kLhpI, LGYiPA5SKvw; tactic_map 5.1, STRONG), quantified gap entry thresholds (PtO7jd8L2xs, 8KXlxAKOTdE, Oi3nSYYQ6sM; 5.2), the 100x-effort outlier-clone bet (BePppCvXC-k; 5.4 — the corpus's only on-screen revenue receipt), and the measure-and-recreate method itself (QfbGKfkGP8U, PaXuebdY75U, q0G-FzS6uxk; 3.1 — CONFIRMS the operation's existing moat).

---

## 1. Decisions required from Jeff before Day 1

| # | Question | Recommended default |
|---|---|---|
| D1 | **Do you accept that this play may legitimately return NO-GO after ~12 hours of work, with zero channel created?** (The scan is the product of weeks 1–2; overriding a NO-GO defeats the play.) | Yes — accept the verdict. A forced clone into a non-gap is the corpus's most common failure profile (5.9 volume chorus). |
| D2 | **Account isolation:** create the channel on a fresh Google account with its own AdSense, or under an existing account? Bans reportedly propagate across channels sharing one AdSense (YtpQSmu794k, practitioner-opinion; policy_dossier §6.1.4). | Fresh account + separate AdSense. Costs 20 minutes; contains worst-case correlated loss with Rexcaped/PPOV/bizdoc. |
| D3 | **Niche exclusion list:** confirm the scan excludes (a) creature/spectacle (Rexcaped owns Play 5's slot), (b) business-documentary (Play 2's lane, if ever activated), (c) the negative-intel auto-fail niches (cardboard DIY, BeamNG, renovation, Roblox, MS-Paint, pigment ASMR, kids anything — action_plan cross-channel negative-intel log). | Confirm all three exclusions. The scan must find a *new* lane, not re-litigate owned or burned ones. |
| D4 | **VO voice:** which ElevenLabs voice for the new channel? (F5-TTS is CC-BY-NC — banned for monetized content, hard constraint.) | A lesser-used ElevenLabs library voice, distinct from Liam/Jessica/Brian and from whatever the incumbent's niche crowd uses (6.18: distinct-from-crowd, congruent-with-genre). Lock it permanently at channel creation. |
| D5 | **Seed hunches:** Jeff contributes any niches/channels he's personally noticed overperforming (10 minutes, voice note is fine). | Do it — the harvest step needs seed candidates and Jeff's feed exposure is free signal. |
| D6 | **Scan spend:** confirm $0 — the whole scan runs on yt-dlp + Claude Code + existing scripts. No NexLev/vidIQ-paid/1of10 (no-new-paid-APIs hard rule). | Confirmed $0. |

---

## 2. WEEKS 1–2 — THE GAP SCAN (no channel is created in this phase)

The scan is a repeatable, versioned workflow. Every artifact lands in `research/gap_scan_<YYYY-MM>/` in the repo so the monthly re-scan is a re-run, not a rebuild. Prototype rule applies: run every command on ONE channel first, confirm the output parses, then batch (hard rule #2).

### 2.1 Session A — candidate harvest (Day 1–2, ~3 hrs)
**Tool:** Claude Code session + `yt-dlp` (verified on PATH at `/Users/jefflawrence/miniforge3/bin/yt-dlp`).
**Output artifact:** `research/gap_scan_2026-08/candidates.md` — 15–25 candidate niches/channels, each one line: handle, why flagged, source of lead.

Candidate sources (run all four):
1. **Fresh-entrant sweep** (Oi3nSYYQ6sM; already specced as the "monthly fresh-entrant scan" in action_plan Rexcaped experiments — reuse, don't reinvent): browse YouTube search/feeds for channels <3 months old whose recent videos vastly out-view their sub count. Log every hit.
2. **Icon method** (YtpQSmu794k): for 3–4 large channels adjacent to Jeff's seed hunches, list videos massively outperforming that channel's own average — each outlier format is a candidate for transplant into an emptier niche (5.3: format transplantation, STRONG — the sharpest articulation is transplant-INTO-a-lazy-niche, BePppCvXC-k).
3. **Demand-gap clustering** (54UTQ2kFhuA; 5.5): one Claude session over yt-dlp-pulled titles of 2–3 proven channels → clusters where demand is visible (Wikipedia/news interest) but YouTube supply is thin.
4. **Jeff's D5 seed list.**

Optional (5.12, TEST-grade): start a throwaway research-only YouTube account and train its feed on faceless candidates for ~30 min; check it again in week 2. Costs nothing; drop if noise.

### 2.2 Session B — per-candidate metadata pull (Day 3–4, ~3 hrs)
**Tool:** `yt-dlp` one-liners (below), output piped to files; a Claude Code session computes the derived metrics. If the manual run works cleanly on 5+ channels, optionally promote the exact commands into a thin `scripts/gap_scan_harvest.py` — but only after the manual prototype, and only if the monthly re-scan justifies it (hard rule #3: no parallel solutions before the need is proven).
**Output artifact:** `research/gap_scan_2026-08/metrics_<handle>.txt` per candidate + one `scan_table.md` summary.

Exact pulls per candidate channel:

```bash
# last 15 uploads: date | views | duration | title
yt-dlp --skip-download --playlist-items 1-15 \
  --print "%(upload_date)s|%(view_count)s|%(duration)s|%(title)s" \
  "https://www.youtube.com/@<handle>/videos" > metrics_<handle>.txt

# subscriber count (any recent video carries it)
yt-dlp --skip-download --playlist-items 1 \
  --print "%(channel_follower_count)s" "https://www.youtube.com/@<handle>/videos"

# true channel age = oldest upload's date (flat list, take last entry id, then:)
yt-dlp --flat-playlist -J "https://www.youtube.com/@<handle>/videos" > flat_<handle>.json
yt-dlp --skip-download --print "%(upload_date)s" "https://www.youtube.com/watch?v=<oldest_id>"
```

Derived metrics (Claude computes into `scan_table.md`): trailing-10 **median views**, **views÷subs ratio**, **uploads/week over trailing 8 weeks**, **channel age** (oldest-video date — Oi3nSYYQ6sM's 4-signal scan uses exactly this, not the "joined" date), **outlier multiplier** of the best recent video vs the channel's own median.

### 2.3 The gates — numeric pass/fail, decided BEFORE any channel exists (Day 5–10)

A niche must pass **ALL seven** gates. One fail = that candidate is dead this cycle. All evidence lines are logged in the decision memo with the yt-dlp numbers that produced them.

| Gate | Test | PASS | FAIL | Corpus source |
|---|---|---|---|---|
| **G1 Demand** | Best incumbent's trailing-10 median views | ≥ 300,000/video (the brief's 300–500K band) — **or** the young-niche alternate: niche < 60 days old AND ≥ 2 channels < 90 days old each with ≥ 100K views on ≥ 2 videos | below both bars | PtO7jd8L2xs, Oi3nSYYQ6sM (5.2) |
| **G2 Under-supply** | Incumbent cadence and field size | cadence < 1 upload/week (trailing 8 wks) **or** < 10 "active" channels in the format (active = ≥ 3 format uploads in 90 days AND trailing median ≥ 10K views) | incumbent ≥ 1/week AND ≥ 10 active channels | PtO7jd8L2xs, 8KXlxAKOTdE (5.2) |
| **G3 Real-trend test** | Own-baseline + replication | outlier beats its channel's OWN median ≥ 3× AND the format replicates on ≥ 2 distinct small channels (replication waived if niche < 60 days old) | outlier only exists on big channels, or only on one account | Z5Wn63kLhpI, Oi3nSYYQ6sM (5.1) |
| **G4 Supply / forced differentiation** | Search the exact format query; count near-identical treatments | ≤ 2 near-identical → clean entry. **3–5 → entry permitted ONLY with a documented differentiated angle written into the memo** (and that angle must score ≥ 70 on the scorer's originality test) | ≥ 6 near-identical treatments → dead regardless of angle | 8KXlxAKOTdE (5.6); brief's "3+ = forced differentiation" |
| **G5 Monetization-survivor** | Upload-cadence continuity of the 5 nearest format-comparables: hits-then-abrupt-silence = probable YPP denial | ≤ 1 of 5 shows the sudden-stop pattern | ≥ 2 of 5 sudden-stops — the format itself likely fails YPP review | zJmYdcvwY1Y (5.7; policy_dossier §2b.10 — folklore-grade but free) |
| **G6 Feasibility & compliance** | Binary checklist | ALL true: executable at $0 on an existing pipeline (§3.3); no AI human faces required; not on the D3 exclusion/negative-intel list; not kids-classifiable (COPPA RPM collapse); physics-QA-able if i2v; plausible mid/high RPM | any false | LGYiPA5SKvw feasibility filter (5.1); hard constraints |
| **G7 Topic scorer** | 3 concrete video topics for the niche through `pipeline_v2/topic_scorer.py` | ≥ 2 of 3 score GO (85+ overall, all tests ≥ 65) | fewer than 2 GO | existing 9-test framework (CLAUDE.md) |

G7 exact invocation (topics file, one per line):

```bash
venv/bin/python pipeline_v2/topic_scorer.py --file research/gap_scan_2026-08/<niche>_topics.txt \
  --niche "<niche description>" --output research/gap_scan_2026-08/<niche>_scores.json
```

The G5 survivor scan and the G4 supply check are already specced as standing items in action_plan.md (cross-channel DO NOW "Monetization-survivor scan"; Rexcaped DO NOW "Search-bar supply check + trend-outlier filter") — this play reuses those procedures verbatim.

### 2.4 The decision memo (Day 10–12)
**Tool:** Claude Code session. **Output artifact:** `research/gap_scan_2026-08/DECISION.md` — for each candidate: all seven gate results with numbers; final verdict per candidate; ONE winner max.

- **If ≥ 1 candidate passes all 7 gates:** pick the single best (highest G1 median × weakest G2 supply). Proceed to §3. Do not enter two niches.
- **If 0 candidates pass: the play returns NO-GO.** Write the memo anyway (it is the deliverable), file the exact commands, and schedule the **monthly re-scan: ~2 hrs, first week of each month** — re-run §2.1–2.3 on a refreshed candidate list (gaps are time-windows: Oi3nSYYQ6sM's "start the clone the same day" logic means the scan must repeat, because this month's empty result says nothing about next month). Hours flow back to Play 5 / other plays. **No channel is created.**

---

## 3. WEEK 3 — MEASURE-AND-RECREATE SETUP (only executes on a PASS)

### 3.1 Measure the incumbent's top 3 recent outliers
Clone the *recent* outliers, never the all-time #1 (already cloned to death — 8KXlxAKOTdE, 5.1). ~4 hrs.

```bash
# download each reference + auto-subs (measurement inputs; scratchpad, not repo)
yt-dlp -f "bv*[height<=720]+ba/b" --write-auto-subs --sub-langs en --sub-format vtt \
  -o "<scratchpad>/gap_measure/%(id)s.%(ext)s" "<url>"

# measured cut grammar per reference
venv/bin/python scripts/extract_edit_grammar.py \
  --video <scratchpad>/gap_measure/<id>.webm --vtt <scratchpad>/gap_measure/<id>.en.vtt \
  --out research/gap_scan_2026-08/<niche>/<id>_grammar.json --name <id>

# within-shot motion texture (what scene-detect misses)
venv/bin/python scripts/extract_motion_events.py \
  --video <scratchpad>/gap_measure/<id>.webm --vtt <scratchpad>/gap_measure/<id>.en.vtt \
  --grammar research/gap_scan_2026-08/<niche>/<id>_grammar.json \
  --out research/gap_scan_2026-08/<niche>/<id>_motion.json
```

This is the exact stack that produced `research/edit_grammar_ruleset.md` for Rexcaped — the method is the operation's proven moat (tactic_map 3.1: full live recreations in QfbGKfkGP8U and PaXuebdY75U CONFIRM it; nothing new is being invented here).

### 3.2 Derive the ruleset
**Tool:** Claude Code session over the 3 grammar + 3 motion JSONs. **Output artifacts:**
- `research/<niche>_edit_ruleset.md` — measured cut cadence, cut-on-what (stat/turn-word/question), SFX-on-cut rate, music-bed coverage, montage burst timing, hook-window pacing. Structured as a sibling of `research/edit_grammar_ruleset.md`.
- `research/<niche>_style_bands.json` — numeric bands the finished renders must land inside (sibling of `research/style_bands.json`, checked by `scripts/gate_style.py`).
- A hook teardown of each reference's 0–15s against `playbook/intros.json`.

**Rule:** the measured numbers govern; no guru round numbers override them (conflict ledger #1 — measured 5–7s grammar beat every corpus pacing claim).

### 3.3 Pipeline fit — the format picks the production line (decision table, 30 min)

| Incumbent format looks like | Production line (all existing, $0 marginal) |
|---|---|
| Composited creature/subject into real footage | Excluded by D3 (Rexcaped's slot) — if the scan returned this, the D3 filter failed; go back |
| Stills-driven narrative / Ken Burns / doc-style | `scripts/ffmpeg_production_render.py` paper-edit path + `scripts/verify_render.py` watcher + WhisperX/`scripts/realign_paper_edit.py` alignment |
| Still-series → i2v POV / first-person | ChatGPT still-series → Grok Imagine i2v (verify free tier FIRST — conflict ledger #5, unresolved) → FFmpeg; local VACE-1.3B (`tools/amber/stage_b_vace.py`, ~22 min/beat, $0) as fallback motion engine |
| List/countdown montage format | `scripts/rexcaped_edit_engine.py` grammar-driven assembly pattern, re-parameterized from `research/<niche>_edit_ruleset.md` |
| Animated-infographic / chart-driven | FFmpeg engine + the Remotion/Hyperframes overlay bake-off already specced in action_plan (bizdoc EXPERIMENTS) — overlays feed the renderer; the assembler does not change |

VO: ElevenLabs (D4 voice), `--wpm-normalize`, one-pass on a locked script (ElevenLabs one-pass rule). Never F5-TTS on this channel (CC-BY-NC).

### 3.4 Channel creation + cold-start checklist (~1 hr; the channel exists as of this step)
All items are the already-synthesized 7.1/7.2 checklist (4xWQ_fHLGAc, eF75ZffgsUk, 3MPSrpIOpAo, LGYiPA5SKvw): fresh Google account per D2 → channel name through YouTube search + WIPO Global Brand Database → keyword-rich description (~5 high-volume niche terms) + same keywords in Studio → Settings → Channel keywords → country + phone/advanced verification (unlocks >15-min uploads, custom thumbnails, appeals) → AI-disclosure stance documented (YES on any upload with AI-generated photoreal content — hard constraint) → FTC affiliate boilerplate parked in the description template → per-video attribution params (`?video=<id>`) on all description links from video 1 (Eb8wlFawjTw). **Output artifact:** `research/gap_scan_2026-08/<niche>_CHANNEL.md` logging every setting.

### 3.5 Video 1 spec
Video 1 = a remake of the incumbent's **best recent outlier**, produced to the measured ruleset, at visibly higher polish (the 5.4 bet: outlier-clone at 100x effort in a low-effort niche — BePppCvXC-k, the corpus's only receipted revenue case), carrying the G4-documented differentiation. Packaging first: render title + thumbnail BEFORE production; kill the topic if the thumbnail doesn't read at feed size (1.1, STRONG — packaging-first gate). Thumbnail↔first-5s congruence check (1.2). Title from the G7-GO topic.

---

## 4. WEEKS 2–13 CADENCE (what ships every week)

Honest throughput: one measured-clone video ≈ 12–16 hrs (script incl. scorer 3–4h; asset gen 4–6h; render + QA 3–4h; packaging + upload 1–2h) → **one upload per ~2 weeks at 7–8 hrs/week**. That lands 5 uploads by day 90 — exactly the corpus's minimum-judgment sample (9iP588aMFBc: judge after ~5 uploads; 8KXlxAKOTdE: 5–10).

| Week | Ships | Hours |
|---|---|---|
| 1 | Sessions A+B: `candidates.md`, `metrics_*.txt`, `scan_table.md` | 6 |
| 2 | Gates G1–G7 run; **`DECISION.md`** (GO with one niche, or NO-GO + monthly re-scan scheduled — plan ends here on NO-GO) | 6 |
| 3 | Measurement pass (3 grammar + 3 motion JSONs), `<niche>_edit_ruleset.md`, `<niche>_style_bands.json`, channel created (§3.4), Video 1 topic + title + thumbnail rendered and gated | 8 |
| 4 | Video 1 script (95+ bar) + ElevenLabs VO + asset generation begins | 8 |
| 5 | **Video 1 uploaded** (full upload checklist §6); fingerprint baseline recorded (§6) | 8 |
| 6 | Video 2 script + VO + assets (remake of incumbent outlier #2); day-14 read of V1 is NOT yet due — no analytics staring | 7 |
| 7 | **Video 2 uploaded** + fingerprint diff vs V1; V1 day-14 first read (read-only: queue V3 subject) | 7 |
| 8 | Video 3 production; 1 sub-CTA-capable Short cut from V1's best beat (FFmpeg 9:16 crop — action_plan cross-channel build #1 pattern) | 7 |
| 9 | **Video 3 uploaded** + fingerprint diff; V2 day-14 read | 7 |
| 10 | Video 4 production. If any video beat 25% of incumbent median: V4 is its direct sequel-on-steroids instead (5.10, BePppCvXC-k) | 7 |
| 11 | **Video 4 uploaded** + fingerprint diff; monthly re-scan #1 of the niche field (2h — has supply moved in?) | 8 |
| 12 | Video 5 production; V3/V4 day-14 reads | 7 |
| 13 | **Video 5 uploaded** + fingerprint diff; **day-90 verdict session** (§8) | 7 |

Standing post-upload doctrine on every upload (action_plan cross-channel protocol — reuse, not reinvent): 72h no-read → day-14 first read → day-14 earliest packaging change → week 4–6 earliest write-off → never delete/unlist flops (winners retro-test the back catalog, 9iP588aMFBc) → pinned comment at publish + first-hour replies.

---

## 5. THE FIRST 5 DELIVERABLES (fully specified)

The niche is unknown until the scan completes, so deliverables 3–5 are specified structurally — each has a named subject *rule*, tool chain, and acceptance gate:

1. **`DECISION.md` — the gap-scan verdict** (week 2). Subject: 15–25 candidates × 7 numeric gates, every number sourced to a yt-dlp pull. Acceptance: every gate row has evidence; verdict is GO-with-one-niche or NO-GO. *This deliverable exists in both branches and is the play's irreducible output.*
2. **`<niche>_edit_ruleset.md` + `<niche>_style_bands.json` — the derived grammar** (week 3). Subject: incumbent's top 3 recent outliers. Tools: yt-dlp → `extract_edit_grammar.py` → `extract_motion_events.py` → Claude synthesis. Acceptance: rules are numbers (cut cadence, event rate, SFX-on-cut %), not adjectives.
3. **Video 1 — remake of the incumbent's #1 recent outlier** (week 5). Working title = the incumbent's proven title shape with the G4 differentiation visible in it (title-formula bank, 1.7). Tools: topic_scorer GO topic → 95+ script → ElevenLabs → pipeline per §3.3 → `verify_render.py` + contact-sheet frame QA → upload checklist. Acceptance: style gate passes against `<niche>_style_bands.json`; thumbnail read at feed size; AI disclosure YES.
4. **Video 2 — remake of outlier #2 + the first fingerprint diff** (week 7). Same chain; additionally ships `fingerprints/V2_vs_V1_diff.md` (§6) proving measured edit-grammar variation. Acceptance: diff shows ≥ the §6 deltas; no two adjacent uploads share caption/card styling.
5. **Video 3 — third outlier remake OR sequel-on-steroids** (week 9): if V1 or V2 beat 25% of incumbent median in its first 14 days, V3 escalates that winner directly (bigger scope, same format — 5.10); otherwise outlier #3. Acceptance: same gates + fingerprint diff vs both prior uploads.

---

## 6. SAMENESS-DEFENSE PROTOCOL (the play's #1 policy exposure, run on every upload)

A clone channel courts exactly the "mass-produced" trigger practitioners report (4xWQ_fHLGAc: YPP rejection with a HUMAN voice for stylistic sameness; PtO7jd8L2xs + 0SPqPnpQsWE: template rotation under enforcement pressure; policy_dossier §2b). Defense is measured, not vibes:

1. **Per-upload fingerprint:** after each final render, run the measurement stack on OUR OWN video:
   `extract_edit_grammar.py --video <final>.mp4 --out fingerprints/<vN>_grammar.json` then `extract_motion_events.py --grammar fingerprints/<vN>_grammar.json --out fingerprints/<vN>_motion.json`.
2. **Diff gate before upload:** Claude session diffs vN against vN-1 (and the incumbent references). **Required deltas: cut-density profile differs ≥ 15% in at least one chapter class; montage bursts sit at different narrative positions; SFX pattern not identical; hook shape rotated (from the 2.1 hook bank).** Identical fingerprints = do not upload; re-edit. Output: `fingerprints/vN_vs_vN-1_diff.md`.
3. **Template rotation:** caption/card/color styling refreshed every ~8–10 uploads, logged (1.9, STRONG — two operators under enforcement contact converge on ~10).
4. **Appeal packet per video:** archive script drafts, sourcing notes, `verify_render.py` HTML report, fingerprint diff — declines happen and documented appeals succeed (ipbnR92Elxg; policy_dossier §6.1.5).
5. **Never clone content — clone grammar.** Scripts are original (95+ bar), assets are self-generated, VO is a licensed distinct voice. The measurement stack copies *timing physics*, not copyrightable expression. No reused clips, ever (§3 of the policy dossier).

---

## 7. REVENUE MECHANICS + HONEST MILESTONES

**Where the first dollar comes from:** AdSense after YPP acceptance — with an optional earlier affiliate path only if the niche has a genuine $100+/sale product fit (LGYiPA5SKvw — practitioner-claim; do not bank on it).

**Time-to-YPP math (shown, not asserted):**
- Thresholds: 1,000 subs + 4,000 public watch hours (official). Pre-acceptance views pay $0 — **receipted** (BePppCvXC-k, on-screen revenue tab; ~40K unpaid watch hours in his case).
- 4,000 hrs = 240,000 watch-minutes. At a 12-min video and 40% average retention (~4.8 min/view), that's ≈ **50,000 views**. Sub gate: at a typical 0.5–2% sub conversion, 1,000 subs needs ≈ 50–200K views — **the sub gate is usually the binding constraint** (receipted: BePppCvXC-k sat at 999 subs with 4,000+ hrs banked; mitigation = the sub-CTA Short, week 8).
- **Realistic case (no outlier):** 5 uploads × young-channel baseline views = 5–30K total views by day 90 → **YPP not reached inside 90 days → $0 AdSense at day 90.** First dollar realistically month 4–6, and only if day-90 metrics justify continuing. Evidence grade: **analyst estimate** built on official thresholds + receipted pre-acceptance-$0 mechanics.
- **Optimistic case (the gap thesis works):** one remake captures 25–30% of the incumbent's ≥300K median (**practitioner-claim**, PtO7jd8L2xs, self-reported) → 75–90K views on one video inside weeks 4–6 of its life → both thresholds hit ~day 70–100. YPP review has returned in ~6 minutes, realistic first-upload→monetized 14 days (**practitioner-claim**, 4xWQ_fHLGAc); apply the day thresholds hit (receipted rule). First AdSense dollar *accrues* ~day 75–110; first *payout* (AdSense $100 floor + monthly cycle) ~day 110–160.
- **90-day revenue:** Realistic **$0** (the honest number). Optimistic: YPP by ~day 80, then ~100–150K post-acceptance views at $2–6 RPM (RPM band **receipted** for entertainment-length long-form: $3 @ ~25 min → $6 @ ~34 min, BePppCvXC-k) → **$200–900 accrued by day 90**. Composite grade: **analyst estimate** (receipted RPM × practitioner-claim capture rate × unverified gap thesis).
- Runtime lever: when two cuts are editorially equal, prefer the longer — midroll RPM roughly doubled 25→34 min in the one receipted case (8.1). Never pad (retention-first rule).

**What the 90 days buys even at $0:** a validated (or falsified) gap, a reusable scan harness, a second measured ruleset proving the grammar stack generalizes beyond creatures, and a channel positioned for month-4–6 monetization — or a clean NO-GO that cost ~12 hours.

---

## 8. METRICS + KILL/SCALE CRITERIA

Measured in Studio (expect ~5-day watch-hour lag — practitioner ×2) and in the fingerprint/scan artifacts.

**Day 30:** Scan verdict exists (binary). If GO: ruleset artifacts exist, channel live, Video 1 uploaded on schedule, V1 day-14 read done. *No view-based judgment yet — week-1/2 data on a new channel is noise (7.3, STRONG: mis-targeted cold-start recs).* Kill trigger at day 30: none based on views; only "scan returned NO-GO" (which is not a kill — it's the play working as designed) or production is >2 weeks behind schedule (→ re-scope hours before continuing).

**Day 60:** 3 uploads live, each with a day-14 read. Diagnostic ladder, not verdicts (5.9): zero impressions = distribution problem (check keywords/classification); impressions-but-no-clicks = packaging (rotate title/thumbnail via single-variable test, 1.8); clicks-but-no-retention = edit (re-check against the measured ruleset). Scale trigger: any video ≥ 10% of incumbent trailing median within 14 days → hold course; ≥ 25% → V4 becomes its direct sequel (5.10).

**Day 90 (the verdict session, week 13):** 5 uploads = the minimum honest sample.
- **SCALE** if: best video ≥ 25% of incumbent median, or channel trend is up-and-right with ≥ 20K total views → continue at cadence, formalize 80/20 format doubling, project YPP date from the watch-hour run rate.
- **HOLD** if: 5–25% of incumbent median on the best video → 4 more uploads over 6 weeks (retro-testing means a later winner can revive the catalog — 9iP588aMFBc), then re-verdict. No packaging rebuilds before each video's week-4–6 mark.
- **KILL** if: best video < 5% of incumbent median AND impressions were nonzero (i.e., it was tested and declined) → stop production, leave videos up (never delete — hard constraint + retro-test evidence), write the post-mortem into the scan memo, revert to the monthly re-scan. Sunk cost: ~80 hrs. The channel stays parked, not deleted, in case a later cycle revives the niche.

---

## 9. RISKS + MITIGATIONS

| Risk | Grade | Mitigation |
|---|---|---|
| **No gap exists** (most likely single outcome of week 1–2) | expected-case | The NO-GO branch IS the plan: memo + monthly 2-hr re-scan; zero channel debt. |
| **"Mass-produced" YPP rejection** — a clone channel is the policy's target profile | practitioner-documented (4xWQ_fHLGAc; policy_dossier §2b) | §6 fingerprint protocol; original scripts/assets/voice; appeal packet per video; delete-lookalikes-and-reapply is the documented remedy of last resort. |
| **The gap is a graveyard** — incumbents under-post because the format quietly fails YPP | practitioner-inference (zJmYdcvwY1Y) | G5 survivor gate blocks entry at ≥2/5 sudden-stops. |
| **Capture-rate shortfall** — the 25–30% heuristic is one operator's self-report | practitioner-claim (PtO7jd8L2xs) | Revenue plan treats it as optimistic-case only; realistic case assumes $0 at day 90. |
| **Window closes mid-production** — gaps get cloned fast (Oi3nSYYQ6sM: same-day entries) | practitioner-observed | 2-week scan→first-upload sprint; week-11 field re-scan; G4 re-checked before each new video. |
| **Grok Imagine free tier dead** (if the format needs i2v) | unverified, flagged (Qsi9MeLh95Q; conflict ledger #5) | Verify BEFORE G6 passes any i2v-dependent niche; fallbacks: local VACE-1.3B ($0), Meta AI f2v / Google Vids (pending their 10-min tests). |
| **Hours overrun** — 12–16 hrs/video is real; a 6-hr week halves cadence | honest-accounting | Cadence is 1/2-weeks by design; if two consecutive weeks miss, drop to 1/3-weeks rather than cutting QA gates. |
| **Sameness ACROSS Jeff's channels** (multi-channel operator pattern) | practitioner-opinion (YtpQSmu794k) | D2 separate account/AdSense; different voice, different grammar ruleset, no cross-posting identical content. |
| **Judge-flagged uncertainty:** this play's upside depends entirely on an unverified market condition (the gap), unlike Play 1's owned edge | analyst | Priced in: the play risks 12 scan-hours before any production commitment; gates are the insurance. |

---

## 10. DO-NOT LIST (play-specific)

- **Do NOT create the channel before all 7 gates pass.** The scan-first sequencing is the play.
- **Do NOT override a NO-GO** because the scan hours feel sunk. Re-scan monthly instead.
- **Do NOT clone the all-time #1** — recent outliers only (8KXlxAKOTdE); the all-time winner is already cloned to death.
- **Do NOT copy content** — no script paraphrases, no asset reuse, no reference-video clips in our uploads. Grammar (timing/structure numbers) only. Transcript-rewriting as a script method is rejected (zJmYdcvwY1Y; below the 95+ bar and reused-content-adjacent).
- **Do NOT enter with an identical edit fingerprint on consecutive uploads** — §6 diff gate is mandatory pre-upload.
- **Do NOT buy an aged/premonetized channel** to shortcut YPP (0SPqPnpQsWE, 54UTQ2kFhuA — ToS violation; every "monetized in days" claim decodes to this trick).
- **Do NOT run the volume play** (daily templated uploads) if early videos flop — the diagnostic ladder governs; the quality bars stay (5.9 resolution).
- **Do NOT use the incumbent niche's crowd voice** or clone any real person's voice (6.18; impersonation risk — own/licensed distinct voice only).
- **Do NOT pay for scan tooling** (NexLev, vidIQ paid, 1of10) — the yt-dlp + Claude + topic_scorer stack covers it at $0; every corpus RPM overlay from those tools is estimator-grade anyway.
- **Do NOT start this play and Play 2 (bizdoc) as simultaneous new builds** — both need the same 7–8 production hours; the hours cap makes them mutually exclusive in the same quarter.
- **Do NOT delete or unlist flops at any point** — retro-testing is real (9iP588aMFBc) and deletion destroys the appeal-packet narrative.
- **Do NOT skip the AI-disclosure toggle or hide watermarks** on any upload (hard constraint; concealment is the aggravating behavior at manual review).
