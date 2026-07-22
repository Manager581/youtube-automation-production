# POLICY & MONETIZATION DOSSIER
### Regenerated from scratch over all 54 analyzed videos (v2, 2026-07-22; supersedes the 32-video edition). Every claim cites a video id; every number carries an evidence grade.

**Evidence grades used throughout**
- **[OFFICIAL]** — quoted from YouTube's own text (CEO blog, community guidelines, Studio UI) or attributed on camera to a named YouTube source.
- **[PRACTITIONER]** — a creator reporting first-hand enforcement/revenue experience, with something shown on screen.
- **[FOLKLORE]** — asserted belief with no evidence shown ("trust score", shadow bans, filename SEO). Act on the behavior only if free; never on the theory.
- **[ESTIMATOR]** — a third-party tool's guess (NexLev/vidIQ overlays) presented as fact. Not decision-grade.
- **[DESC-SOURCED]** — appears only in a video description, not verified on screen.

Corpus note: 32 previously analyzed + 22 new (1ywvAeaFojo, 9iP588aMFBc, BePppCvXC-k, CxwFu1nEsZQ, Eb8wlFawjTw, JpvaUUgtTVk, KLswOquhsM8, Oi3nSYYQ6sM, PaXuebdY75U, Qsi9MeLh95Q, ROPkHP8jpW0, TvJhpOxFRsE, WVT2FCjhDDY, YtpQSmu794k, Z5Wn63kLhpI, ZKsldrcO_fU, f-ufEhGtVpw, oWkUwno6b0E, vI4RdXMSq8c, vuo_bPhkD_U, ylezKJG7rb8, zq_Yi1gK6Fc).

---

## 1. The August 17 membership-pricing change (CQWfqKGFoPM)

The single dated, officially-attributed policy item in the corpus. Attributed on camera to Rene Ritchie, YouTube creator liaison — **[OFFICIAL-attributed]**, relayed by TubeBuddy. It is a channel-**membership pricing** change, NOT a YPP/ad-revenue/inauthentic-content change.

Mechanics as reported:
- **Effective Aug 17**: YouTube auto-applies per-country **"smart pricing" recommendations** (built from audience geography, per-country engagement, and comparable channels' pricing) to channel-membership tiers **for NEW members outside the US** — unless the creator sets prices manually first.
- Manual path: **Studio → Earn → Memberships** → accept / tweak / set own prices.
- **Existing members grandfathered; US-dollar members unaffected.**
- Pricing is normally locked to **one change per 12 months per tier**; changes made during the transition window do NOT consume that lock.
- **$499.99/month cap** — **[DESC-SOURCED]** (description only, not in the video).

**Relevance to us: dormant.** No channel has YPP, let alone memberships. Action: one standing line in the future monetization checklist (§6.1.8). The video's transferable asset is its hook shape (hard date + forced default + cost-of-wrong-choice inside 10s) — a worked example for `playbook/intros.json` on bizdoc policy-deadline stories, not a rule change.

---

## 2. The July 2025 "inauthentic content" policy — what practitioners report actually triggers it

The operation's #1 platform risk. 54 videos yield a consistent enforcement picture.

### 2a. The confirmed baseline **[OFFICIAL]**
- The **July 15, 2025 YPP update** renamed "repetitious content" to **"inauthentic content"**, targeting mass-produced/repetitive content (analyst baseline — the rename/date is corpus framing not tied to one video id; the verbatim quotes below are the cited anchors, q0G-FzS6uxk).
- q0G-FzS6uxk quotes a **YouTube CEO blog post** verbatim: AI-slop enforcement **builds on existing anti-spam/clickbait systems targeting "low-quality repetitive content."**
- q0G-FzS6uxk also quotes the **community guidelines**: monetized content must be **original/authentic, significantly transformed if borrowed, and not mass-produced or repetitive.**
- YtpQSmu794k restates YouTube's line accurately: AI **as a tool** is fine; 100% AI-generated, mass-produced, zero-effort content ("type a prompt, slap a robot voice on it") leads to demonetization or ban. (No doc citation, but consistent with the official text.)
- The **altered/synthetic-content disclosure question is live in the publish/stream flow** — shown on screen in eF75ZffgsUk (which then gives the WRONG advice for AI channels: "click No").

### 2b. What practitioners report actually triggers enforcement **[PRACTITIONER unless noted]**
1. **"Mass-produced" sameness — not AI voice.** Sharpest datapoint in the corpus (4xWQ_fHLGAc): a channel using a **HUMAN voice** was rejected at YPP with the stated term "mass-produced" because all videos were stylistically identical; the remedy that worked: **delete the lookalike videos, change style, reapply — accepted**. The same creator's AI-VO channels all passed. Sameness is the trigger; voice provenance is not.
2. **Template reuse across uploads.** A $35K/month Shorts operator rotates his caption template (colors/shape/background) roughly **every 10 videos** because "identical templates could get demonetized" (PtO7jd8L2xs). A USA-politics template farmer under live enforcement pressure ("why is this channel monetized") warns "try not to work on the same template" (0SPqPnpQsWE). Two independent operators converging on the same evasion = detection reads the **edit fingerprint across uploads**. **[PRACTITIONER, corroborated ×2]**
3. **Fabricated content = "deceiving the audience" → demonetized or removed** (zJmYdcvwY1Y, stated as a working rule). Reinforces the public-data-only rule (`playbook/sources.json`).
4. **YPP applications from AI-faceless channels ARE being declined — and appeals succeed with a case.** A student channel was declined, then monetized after "a banger appeal" (ipbnR92Elxg ~10:36). Consequence: archive human-editorial evidence per video (script drafts, sourcing docs, `verify_render.py` reports) as appeal ammunition.
5. **Cloning another creator's voice risks demonetization or ban** (Oi3nSYYQ6sM, re: the "Human Chess" channel). Directly contradicted by 3MPSrpIOpAo's claim that competitor voice-cloning has "no issue in monetization" — conflict shown; 3MPSrpIOpAo is a bare assertion while impersonation risk matches the official inauthenticity framing. We keep own-voice-only.
6. **AI avatar presenters (HeyGen + voice clone) risk demonetization/ban/shadowban** (YtpQSmu794k [25:34] — asserted, no case shown; **[PRACTITIONER-opinion]**). Aligned with the no-AI-human-faces hard rule.
7. **Bans can propagate across channels sharing one AdSense account** (YtpQSmu794k [04:38] — asserted, no case shown; **[PRACTITIONER-opinion]**). Cheap hedge: audit AdSense linkage across our three channels before bizdoc launch (§6.1.4).
8. **Enforcement may act through distribution, not just demonetization.** vidIQ — industry-adjacent — publicly predicts undifferentiated "say-nothing faceless" AI content gets **"squeezed into oblivion" in recommendations** (ZKsldrcO_fU; opinion, but a meaningful sentiment signal given the source). q0G-FzS6uxk claims YouTube uses **Gemini to analyze whole-video context and suppresses low-effort AI pre-algorithm** (**[FOLKLORE]** — uncited). Qsi9MeLh95Q's "the algorithm smells AI slop and buries it" is the same claim at zero evidence.
9. **Partial human effort is not claimed as a safe harbor.** q0G-FzS6uxk asserts big channels were demonetized despite partial human effort (**[FOLKLORE]**, uncited); LGYiPA5SKvw says banned AI channels share "spammy vibe, no human input, no value" rather than AI tooling — his safety recipe: human ideation, human-QC'd scripts, real value. tICnK3Qb2k8 concurs: enforcement targets "AI slop" usage patterns, not AI tools.
10. **Field signal for a policy-killed format: the sudden stop.** A channel where every video hits and uploads abruptly cease = likely YPP denial/removal (zJmYdcvwY1Y estimates ~90%; **[FOLKLORE]** but free and useful) — add as a manual niche pre-flight alongside `pipeline_v2/topic_scorer.py` source_availability (§6.1.7).
11. **Cross-platform confirmation the direction is industry-wide:** TikTok Shop hard-caps low-quality accounts at ~300 videos/30 days and requires transformed (not raw-listing) images (r81ImbWaxEE, claimed); Meta's 2026 ban wave hit AI-persona accounts, OnlyFans bans AI creators while Fanvue requires an AI disclosure (Z5Wn63kLhpI); Facebook monetization stays invite-only (E_CIP98ufto, KZKFlik4M8I). Every major platform is converging on anti-inauthentic enforcement.

### 2c. What practitioners report does NOT trigger it **[PRACTITIONER]**
- **AI voiceover per se** — 4xWQ_fHLGAc's channels all use AI VO and passed YPP; CxwFu1nEsZQ: AI voices "not blocked" as of mid-2026, but generic overused stock voices add sameness risk (a unique/cloned voice is differentiation).
- **AI-assisted research/scripting with human direction** — ROPkHP8jpW0's AI-researched channel was picked up and pushed by the algorithm weeks after launch with no observed suppression (mid-2026); YtpQSmu794k's thesis: human-directed AI systems monetize while 100% slop dies.
- **YPP review mechanics observed:** review returned in **~6 minutes** after thresholds (automated first pass suspected), watch-hours lag **~5 days** in Studio, real first-upload-to-monetized timeline **14 days** (4xWQ_fHLGAc). BePppCvXC-k independently confirms the ~5-day watch-hour lag.

### 2d. Synthesis
Every source, from opposite directions, draws the same line: **enforcement keys on mass-produced sameness, absent transformation, and deception — not on AI tooling.** Our defenses are the named systems that already exist: measured per-video edit variation (`research/edit_grammar_ruleset.md` + clip-variety rule + `scripts/rexcaped_edit_engine.py`), transformative originality (creature composites into real footage, original scripts, owner's voice), public-data sourcing (`playbook/sources.json`), and QA artifacts (`verify_render.py` reports, provenance stamps) doubling as appeal evidence. The genre's silence is itself data: ~20 of 54 videos teach exactly the template-farm profile the policy targets and never mention the policy (32DLRsFiXZY, 6WDvO0Lu1sY, 8Mx2m0djgTA, NA0AOlCmelQ, NlfmQpSaYMo, h6DB0e96GI0, JpvaUUgtTVk, lL9gjPw5yjg, sMo5RT_dPxc, WVT2FCjhDDY, zq_Yi1gK6Fc, Dmqz8opSHzE, ylezKJG7rb8, TiycelzfzC0, lDpOnE3VJVI, CxwFu1nEsZQ, f-ufEhGtVpw, Ao_d-uaMJvk, 8N7-vQ9qX4w, KxsasFMMPpA).

---

## 3. Reused-content enforcement and Content ID behavior

Primary source: the corpus's one high-earning reuse operator (PtO7jd8L2xs, $35K/month claimed) — his evasion hedges ARE the enforcement map **[PRACTITIONER]**:
- **Content ID reliably catches raw movie clips** — he adds "small animations" specifically "to get away from Content ID," and states raw clips are unmonetizable without added webcam+text layers.
- **Clips sourced from other YouTube channels flag hardest** — he deliberately rips from TikTok/Instagram instead of YouTube to reduce reused-content and copyright detection. Implication: YouTube-internal reuse detection is stronger than cross-platform.
- **Repetitive-template detection is real** — the every-10-videos template rotation (§2b.2).
- His stack still includes OBS-recording Disney+/Netflix — infringement regardless of Content ID outcomes. Evasion ≠ legality.

Corroborating and adjacent:
- **"Text commentary transforms reused clips" is asserted, never evidenced** (QfbGKfkGP8U) — low-value overlays on reused clips are precisely what YPP reviewers flag under the July-2025 regime; his claimed 3-year track record predates the enforcement wave; he conflates monetization policy with copyright (wholesale TikTok-clip reuse is infringement exposure regardless of YPP status). **[FOLKLORE, high-risk]**
- **Deleting videos and re-uploading them to another channel can trip reused-content review** (8KXlxAKOTdE; **[PRACTITIONER-opinion]**).
- **Looped "24/7 live" rebroadcast of one pre-recorded video** does bank watch hours toward YPP (the mechanic is true) but is a textbook inauthentic-content + misleading-metadata target at human review (eF75ZffgsUk). Only compliant variant: honestly-labeled premieres/marathons of our own published videos.
- **Self-compilation re-uploads** (hour-plus "mega-compilation" of your own videos — BePppCvXC-k, described but never executed) sit in the same reused/repetitious zone when the source is AI-heavy; re-check policy before ever using.
- **Structural takeaway** (PtO7jd8L2xs analysis): generating original AI assets composited into real footage **sidesteps the entire reused-content enforcement vector** this genre burns effort evading. Bizdoc's fair-use rules (≤7s/clip, ≤30s/source, mute original audio, transformation layers, source credits) stay exactly as-is.

---

## 4. ToS-violating practices these gurus normalize — never adopt

Each is presented as standard practice somewhere in the corpus. All rejected; ids show how widespread the normalization is.

| Practice | Who normalizes it | Why it's radioactive |
|---|---|---|
| **Buying aged/pre-monetized channels** ("monetized in 2-3 days") | 0SPqPnpQsWE ("buy from the market"), 54UTQ2kFhuA (sells them — headstartchannels.com), 8KXlxAKOTdE (his own caveat: "you never know who had the account"), PtO7jd8L2xs, KxsasFMMPpA (monetizable-region accounts) | Accounts are non-transferable under YouTube ToS; unknown prior history; termination risk. Every "fast monetization" claim in this genre is a proxy for this trick (0SPqPnpQsWE). |
| **Multi-account free-credit farming** (fresh browsers, temp emails, account cycling) | 32DLRsFiXZY (Flow), NA0AOlCmelQ (Wan), 3MPSrpIOpAo (10-minute-mail), PtO7jd8L2xs (HeyGen), Qsi9MeLh95Q (batch extensions; its own description disclaims ToS responsibility) | Google/platform ToS abuse — account-level ban risk on the tool side; an operation built on it can lose its gen stack overnight. |
| **Watermark concealment** (scale-and-shift, overlay your own mark) | NlfmQpSaYMo, lDpOnE3VJVI, h6DB0e96GI0 (Flow/Veo output) | Veo output carries SynthID invisible watermarking that survives cropping — hiding the visible mark removes nothing and **demonstrates intent to obscure AI provenance** at any manual review. |
| **Advising "No" on the AI-disclosure question** | eF75ZffgsUk (YouTube publish flow), E_CIP98ufto (Meta "Add AI label" left OFF) | Violates the altered/synthetic-content disclosure requirement; for AI-heavy channels the correct answer is Yes (§6). |
| **Cloning another person's voice** | 3MPSrpIOpAo (claims "no issue"), Oi3nSYYQ6sM (recommends the pattern while admitting ban risk) | Impersonation + inauthenticity; contradicted inside the corpus itself (§2b.5). Own-voice only. |
| **Cloud-phone account farms / identical content across fabricated identities** | KxsasFMMPpA (DuoPlus sponsor segment), Z5Wn63kLhpI (warmed multi-account farms + cloaked deep links) | Spam/deceptive-practices territory on every platform; duplicated-content channel networks are an explicit policy target. |
| **Gray-market resold API credits** (ElevenLabs resellers at $5/1M) | 3MPSrpIOpAo (AI33.pro) | Resold/laundered credentials risk; our ElevenLabs account is paid and licensed. |
| **Ripping streaming services via OBS** | PtO7jd8L2xs (Disney+/Netflix) | Straight copyright infringement; no transformation argument survives it. |
| **Fake 24/7 "live" loops for watch hours** | eF75ZffgsUk | §3 — inauthentic content + misleading metadata at exactly the moment (YPP review) a human looks. |
| **Kids-content template farms** (nursery rhymes, Roblox cartoons, 3/day kids stories) | lDpOnE3VJVI, sMo5RT_dPxc, ylezKJG7rb8 | Not ToS-violating per se, but Made-for-Kids/COPPA collapses RPM (no personalized ads), and template-AI kids content is the highest-scrutiny enforcement category; conflicts with our not-for-kids positioning. |

**Edge case, not a violation:** ROPkHP8jpW0 used YouTube's own paid **Promotions** product ($200 → 1,419 views + 380 subs) and floats buying the final subscribers when watch hours are already met. Promotions is an official product, so not ToS-violating — but whether Promotions-bought subs count toward YPP was **not verified on screen** (**[PRACTITIONER-unverified]**), and it conflicts with the no-spend-without-prototype rule. Park it.

---

## 5. RPM / niche economics claims worth keeping

The only **on-screen, owner-analytics revenue evidence in the entire 54-video corpus** is BePppCvXC-k (revenue tab shown). Everything else is claimed, estimated, or implied.

| Claim | Source | Grade |
|---|---|---|
| Longer runtime raises RPM via midrolls: **~$3 RPM @ ~25 min → ~$6 @ 34 min** (gaming niche) | BePppCvXC-k (revenue tab on screen) | **[PRACTITIONER]** — best revenue evidence in corpus |
| Views/watch-hours accrued **before YPP acceptance are never paid**; "monetize all" applies ads going forward only; he estimates ~40K unmonetized watch hours ≈ ~$1,000 lost | BePppCvXC-k | **[PRACTITIONER]** |
| Studio watch-hour analytics **lag ~5 days** | BePppCvXC-k + 4xWQ_fHLGAc (independent) | **[PRACTITIONER ×2]** |
| YPP review can return in **~6 minutes**; realistic first-upload→monetized: **14 days** (idea-driven niche) | 4xWQ_fHLGAc | **[PRACTITIONER]** |
| Finance/legal content pays **~10x** general entertainment ("30K views worth 300K") | tICnK3Qb2k8; directionally corroborated by Ao_d-uaMJvk, Oi3nSYYQ6sM, zJmYdcvwY1Y | **[FOLKLORE-consistent]** (no screenshots) — but it is the bizdoc thesis ($10-25 RPM) and nothing in 54 videos contradicts it |
| Shorts RPM ≈ **$0.05-0.07/1,000** (implied: 600M views = $30-40K) | QfbGKfkGP8U | **[PRACTITIONER-implied]** — Shorts are a discovery funnel, not a revenue engine |
| Paid Promotions benchmark: **$200 → 1,419 views + 380 subs (~$0.53/sub, ~$0.14/view)** — "not worth it" for growth | ROPkHP8jpW0 (setup + results on screen) | **[PRACTITIONER]** |
| **Edit quality is the top spend lever**: $2,010/video channel → 1M views from 4 videos vs identical-topic $270/video channel → 10K; editor was the biggest line item ($1,600 vs $250); AI script ≈ parity with a $250 human script except conciseness | ROPkHP8jpW0 (side-by-side experiment) | **[PRACTITIONER]** (n=1, packaging confound) — confirms `research/edit_grammar_ruleset.md` + `playbook/editing.json` as the moat, and the 95+ script bar's ramble-cutting |
| Facebook content monetization: invite-only; trigger ≈ **5K followers + 60K minutes viewed** (his 7 pages' experience); image posts ≈ **$0.08/1K views** ($393/5M) | E_CIP98ufto, KZKFlik4M8I | **[PRACTITIONER-estimate]** (menu shown; thresholds are not documented policy) |
| AI news channels "monetize at **$11 RPM**" | Oi3nSYYQ6sM | **[ESTIMATOR]** (NexLev overlay on a third-party channel; monetization never verified) — never cite as fact |
| JP/KR language arbitrage (high RPM, thin competition); danger-niche RPM "4-5"; niches "live at least 4 months" | 3MPSrpIOpAo, zJmYdcvwY1Y | **[FOLKLORE]**/garbled — unverified; un-QA-able foreign-language channels also violate verify-before-claim |
| Day-one **pre-YPP affiliate monetization** with $100+/sale products + FTC disclosure line; four-layer revenue stack (high-ticket affiliate > recurring software affiliate > AdSense-as-extra > sponsorships) | LGYiPA5SKvw; TvJhpOxFRsE | **[PRACTITIONER-opinion]** — the one pre-YPP revenue idea worth a TEST on the creature channels; bizdoc already has the sponsor plan (Incogni/DeleteMe/Proton/NordVPN) |
| Judge a channel by **revenue-per-view, not views** (7.7M views=$13K vs 20K views=$100K claimed); per-video `?video=<id>` attribution params on description links | Eb8wlFawjTw (self-demonstrated in its own description) | **[PRACTITIONER-claim]**; the attribution mechanic is free and verifiable — TEST for bizdoc sponsor links |
| Monetize-early rule: apply the instant thresholds hit, **before** an expected hit lands; a dedicated sub-CTA Short closed a 999/1K sub gap | BePppCvXC-k | **[PRACTITIONER]** |
| Headline revenue claims: "$333K" (YtpQSmu794k), "$35K/31 days" (PtO7jd8L2xs), "$1K/day" (BePppCvXC-k — views verified, revenue partial), "$100K funnel" (Eb8wlFawjTw), "$28K/3 weeks" (ipbnR92Elxg), "$60K/mo MS-Paint" (f-ufEhGtVpw — VidIQ estimate of a channel the creator doesn't own) | various | **UNVERIFIED** — never use as benchmarks |

**Bottom line:** nothing in 54 videos undermines the bizdoc high-RPM strategy; the strongest new evidence (BePppCvXC-k midroll math, ROPkHP8jpW0 quality experiment) actively supports long-form + edit-quality investment. Shorts/template-niche economics confirm they are discovery surfaces or demonetization traps, not businesses.

---

## 6. Compliance checklist for OUR three channels

Maps onto existing systems BY NAME — nothing here proposes rebuilding them.

### 6.1 All channels — standing rules
1. **AI disclosure = Yes** on the altered/synthetic-content question for every upload containing AI-generated photoreal content (eF75ZffgsUk shows the flow; §4 shows the genre advising the opposite). Add as a required field in the upload checklist / NEXT_VIDEO.md handoffs.
2. **Never hide watermarks** on any generated asset (NlfmQpSaYMo, lDpOnE3VJVI, h6DB0e96GI0) — provenance concealment is the aggravating behavior at manual review. Our provenance-stamp system is the asset; keep stamping.
3. **No purchased accounts, no multi-account credit farming, no resold credits, no voice-cloning of others, no account farms, no fake live loops** (§4 table). Channels are clean-built; keep them that way.
4. **Audit AdSense linkage** across Rexcaped / Prehistoric POV / bizdoc before bizdoc launch — ban propagation via shared AdSense is unverified (YtpQSmu794k) but the hedge costs minutes.
5. **Archive appeal evidence per video**: script drafts, sourcing docs, `verify_render.py` HTML reports, edit-engine provenance stamps (ipbnR92Elxg — declines happen; documented appeals succeed). The pipeline already produces these; just retain them per-video.
6. **Vary the per-video edit fingerprint.** Template rotation is enforcement-relevant (PtO7jd8L2xs, 0SPqPnpQsWE): `scripts/rexcaped_edit_engine.py` + `research/edit_grammar_ruleset.md` must keep producing measurably distinct per-video patterns (the clip-variety rule already mandates distinct vantages) — never let the engine converge on one fingerprint. Same hygiene for thumbnail templates in `playbook/titles_thumbnails.json`.
7. **Niche pre-flight: sudden-stop scan** — before entering any format, check 3-5 comparable channels for hits-then-abrupt-silence (zJmYdcvwY1Y; folklore-grade but free). Run alongside `pipeline_v2/topic_scorer.py` (9 tests, GO=85+) as a manual check.
8. **Monetization timing**: apply to YPP the moment thresholds hit — pre-acceptance views pay $0 (BePppCvXC-k); expect the ~5-day watch-hour lag; on acceptance run "monetize all." At YPP + memberships: set tier prices manually (Studio → Earn → Memberships) before smart-pricing defaults auto-apply; note the once-per-12-months price lock (CQWfqKGFoPM).
9. **FTC disclosure line** in the description for any affiliate link (LGYiPA5SKvw) — applies the day pre-YPP affiliates are tested.
10. **No self-compilation re-uploads** without a fresh policy check (§3, BePppCvXC-k).

### 6.2 Rexcaped (AI-composite creature channel)
- Disclose AI (photoreal creatures in real footage is exactly the case the disclosure exists for).
- The composite-into-real-footage technique + measured edit grammar IS the inauthentic-content defense: original assets sidestep the reused-content vector entirely (PtO7jd8L2xs analysis). Keep frame-level QA and real-physics riders — they are the "human effort" evidence trail.
- Watch stock-voice sameness: generic ElevenLabs voices add mass-produced signal (CxwFu1nEsZQ, YtpQSmu794k). Keep the locked distinct voice; a channel-unique voice is a differentiation lever (grade: TEST, not ADOPT — no direct evidence it changes outcomes).
- Every video must differ in template fingerprint (edit rhythm, caption package, thumbnail composition) per §6.1.6.

### 6.3 Prehistoric POV
- Same disclosure + fingerprint rules. The still-series→i2v format is the closest of our three to the "static template AI" risk profile (Ao_d-uaMJvk's niche); the defenses are per-video distinct vantages (clip-variety rule), original scripts per topic, and not-for-kids positioning — never drift toward kids-classifiable content (COPPA RPM collapse: lDpOnE3VJVI, sMo5RT_dPxc).
- Pre-YPP: no shortcuts — no loops, no bought anything; volume-as-feedback (ZKsldrcO_fU) is the legitimate path to the thresholds.

### 6.4 Bizdoc (business/tech documentary)
- **Fabrication is a policy risk, not just an ethics rule** (zJmYdcvwY1Y): the public-data-only rule (`playbook/sources.json`, SEC/DOJ/court filings) is also demonetization armor. Keep on-screen "First reported by" credits.
- Fair-use discipline stays: ≤7s/clip, ≤30s/source, muted original audio, transformation layers — nothing in the corpus (QfbGKfkGP8U's "text transforms everything" folklore included) justifies loosening it; YouTube-internal reuse detection is the strongest vector (PtO7jd8L2xs), so prefer non-YouTube sourcing where licensing allows and keep transformations heavy.
- **Cloned-voice disclosure stance needed**: document a position on disclosing the owner's own cloned voice (self-clone ≠ impersonation, but the disclosure question doesn't distinguish — decide once, apply consistently). Related: **F5-TTS weights are CC-BY-NC — not licensed for monetized use**; ship monetized VO via ElevenLabs until resolved (existing local-TTS project note; corpus adds Google AI Studio TTS only as a $0 scratch-VO for timing drafts, lL9gjPw5yjg, ylezKJG7rb8).
- Sponsor links: add `?video=<id>` attribution params (Eb8wlFawjTw) — free, verifiable, enables revenue-per-view judgment of the channel.
- High-RPM long-form with midrolls is supported by the best evidence in the corpus (BePppCvXC-k, §5); the 23.4-min "Breaking the Law" format already exploits it.

---

## Folklore vs officially confirmed — quick reference

**[OFFICIAL] (act on):** community-guidelines originality/transformation/mass-production text + CEO-blog anti-slop line (q0G-FzS6uxk); AI-disclosure question in the publish flow (eF75ZffgsUk); Aug 17 membership smart-pricing mechanics attributed to Rene Ritchie (CQWfqKGFoPM); YPP thresholds 4,000 public watch hours + 1K subs incl. public live watch time (BePppCvXC-k, eF75ZffgsUk).

**[PRACTITIONER] (weight it):** "mass-produced" as the actual YPP rejection term + delete-and-reapply remedy (4xWQ_fHLGAc); template-rotation necessity (PtO7jd8L2xs, 0SPqPnpQsWE); Content ID catches raw movie clips / YouTube-sourced clips flag hardest (PtO7jd8L2xs); declines-then-successful-appeals (ipbnR92Elxg); pre-acceptance views pay $0 + midroll RPM math (BePppCvXC-k); quality-beats-slop experiment + Promotions benchmark (ROPkHP8jpW0); ~5-day watch-hour lag (×2 independent); no observed suppression of human-directed AI-assisted channels in mid-2026 (ROPkHP8jpW0).

**[FOLKLORE] (never act on alone):** "trust score" / account warming (54UTQ2kFhuA, 8KXlxAKOTdE, q0G-FzS6uxk); Gemini whole-video suppression (q0G-FzS6uxk); shadow bans; filename SEO (4xWQ_fHLGAc); "text commentary transforms reused clips" (QfbGKfkGP8U); "any visuals monetize fine" / competitor voice-clone safe (3MPSrpIOpAo); "YouTube doesn't block AI content" as blanket safety (f-ufEhGtVpw); off-platform-link suppression (TvJhpOxFRsE); "policies come and go, nothing happens" (3MPSrpIOpAo); NexLev/VidIQ RPM overlays as revenue facts (Oi3nSYYQ6sM, 8KXlxAKOTdE, ipbnR92Elxg, f-ufEhGtVpw).

---

## What the 22 new videos changed vs the 32-video edition

1. **Real revenue evidence finally exists in the corpus**: BePppCvXC-k's on-screen revenue tab ($3→$6 RPM by length; $0 for pre-acceptance views; monetize-early rule; sub-CTA Short) upgrades the length→RPM claim from folklore to practitioner-grade and adds three checklist items (§6.1.8).
2. **ROPkHP8jpW0 (Pay-To-Win)** adds the corpus's only controlled experiment: edit quality is the dominant spend lever (supports `research/edit_grammar_ruleset.md` as the moat), AI scripts near-parity with human ones except conciseness (supports the 95+ script bar), Promotions priced and rejected, and no observed algorithmic suppression of an AI-assisted channel in mid-2026.
3. **ZKsldrcO_fU (vidIQ 2026 rules)** introduces the distribution-side squeeze thesis: pressure on commodity faceless AI may arrive via recommendations before demonetization — the survivable position is AI tooling PLUS recognizable identity/format, which is exactly our architecture (measured grammar, locked voices, differentiated formats).
4. **YtpQSmu794k** adds two new hedges: AdSense-linkage ban propagation (audit added, §6.1.4) and AI-avatar-presenter risk (aligns with the no-AI-human-faces rule) — both practitioner-opinion grade.
5. **Channel-economics case studies** (Eb8wlFawjTw revenue-per-view + `?video=` link attribution; TvJhpOxFRsE four-layer revenue stack) add the pre-YPP affiliate TEST and a free attribution mechanic for bizdoc sponsor links.
6. **The cross-platform enforcement picture hardened**: Meta's AI-persona ban wave + OnlyFans AI bans vs Fanvue's required disclosure (Z5Wn63kLhpI) join TikTok's spam caps — every platform converging on the same anti-inauthentic line raises confidence YouTube enforcement deepens rather than fades.
7. **Unchanged in substance**: the Aug 17 item, the reused-content/Content ID map, and the ToS-violation table — the new batch added zero contradictions, and roughly half the new videos repeat the genre's signature omission (teaching policy-target formats without mentioning the policy).

## One-line verdict
The policy risk is real and template-shaped — enforcement keys on sameness and deception, not AI tooling — and our named systems (edit-grammar variation, composite originality, public-data sourcing, provenance QA) are the defense the evidence supports; the checklist above is hygiene on top, not a rebuild.
