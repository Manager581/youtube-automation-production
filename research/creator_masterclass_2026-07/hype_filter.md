# HYPE FILTER & CONFLICT LIST (v2 — full 54-video corpus)

Regenerated from scratch over ALL 54 analyzed videos (`analysis/<id>.json`), replacing the
32-video v1. Adjudications use `STRATEGY_CONTEXT.md` hard rules,
`research/edit_grammar_ruleset.md` (measured values) + `research/viral_recreation_spec.md`,
the 7-module playbook (`playbook/{editing,intros,scripting,titles_thumbnails,retention_delivery,ideation,sources}.json`),
and `pipeline_v2/topic_scorer.py` (9 tests, GO=85+) as tiebreakers. Every claim cites video ids.

**Evidence-grade legend** — used throughout: *(unverified)* = asserted with no auditable proof
(screenshot-tier, third-party estimate, or narrated); *(desc-sourced)* = only appears in the
video description, not demonstrated; *(shown)* = demonstrated on-screen and internally
consistent. Anything not marked (shown) does not clear the bar for ADOPT on its own.

---

## 1. Recurring hype patterns

### 1.1 Unverifiable / fabricated revenue "proof"
The dominant pattern across all 54: revenue that is computed, staged, estimated, or belongs to
someone else — never audited.
- **Title-bait numbers never evidenced in the video at all**: "$77,000/Month" is never
  mentioned once in the 12 minutes (WVT2FCjhDDY); "$30,000/month" is disclaimed on camera
  ("I'm not saying you'll make millions") (CxwFu1nEsZQ); "$10M / billions of views" pure
  assertion (TvJhpOxFRsE); "$1,024,937 in 90 days" while on-screen numbers total ~$130K
  (E_CIP98ufto); "$400/day" in the description for a screenshot showing ~$400 *total*
  (4xWQ_fHLGAc).
- **Currency-toggle theatre**: "$500K/year" proven by toggling Studio's revenue currency
  USD→EUR — proves a dashboard renders a number, nothing else (QfbGKfkGP8U). The corpus's one
  counter-example deliberately exposes this trick: YtpQSmu794k shows $333,080 in Studio with a
  live refresh AND a USD-vs-Taiwan/Jamaica currency check — the most verifiable revenue claim
  in all 54, though it comes from a mature 1.5M-sub channel, so it does not evidence
  transferability to a new faceless channel.
- **Arithmetic sold as receipts**: "$27,875" = 4M views × a NexLev RPM estimate the presenter
  *himself* calls inaccurate (ipbnR92Elxg); "$60K/month" is a VidIQ estimate of a channel the
  presenter does not own (f-ufEhGtVpw); estimate-stacked-on-estimate "$26,000 in 3 weeks"
  (Oi3nSYYQ6sM); NexLev/VidIQ third-party estimates read out as measured fact (8KXlxAKOTdE,
  Oi3nSYYQ6sM, f-ufEhGtVpw).
- **Anonymized / unnamed channels**: "Secret Channel Exposed" never names the channel
  (BePppCvXC-k); obscured dashboard, $5.2K (54UTQ2kFhuA); anonymized student screenshots
  (8KXlxAKOTdE, Z5Wn63kLhpI, Oi3nSYYQ6sM); unnamed "secret test channel" (9iP588aMFBc);
  revenue "shown somewhere on screen," never itemized (zJmYdcvwY1Y); $35K self-reported on a
  channel the presenter admits was *purchased pre-monetized* (PtO7jd8L2xs); "$100K from a
  20K-view video" narrated, not receipted (Eb8wlFawjTw); "$2.6M from Binge Central"
  *(unverified)* inside a Skool pitch (ROPkHP8jpW0).
- **The tool's own marketing dashboard as evidence**: Noodle Tomato's "$8,500/mo niche"
  numbers are rendered by the product being sold (8Mx2m0djgTA).
- **Other channels' view counts as "proof" of the method**: presenter shows third-party
  channels, not their own results (32DLRsFiXZY, 3MPSrpIOpAo, Ao_d-uaMJvk, h6DB0e96GI0,
  KxsasFMMPpA, lL9gjPw5yjg, NA0AOlCmelQ, NlfmQpSaYMo, sMo5RT_dPxc, JpvaUUgtTVk, WVT2FCjhDDY,
  f-ufEhGtVpw, CxwFu1nEsZQ, and LGYiPA5SKvw — whose "proof this works" is a *different*
  channel's old views).
- **Confounded experiments presented as proof**: ROPkHP8jpW0's "quality beats AI slop" A/B ran
  the expensive channel on a *rebranded aged account* and the cheap one fresh — and his own
  late update (cheap channel 4.4×'d untouched weeks later) undercuts the headline.

**Filter rule**: a revenue claim counts only if it is the presenter's own named channel with
method-to-revenue causality shown. Zero of 54 fully pass; YtpQSmu794k comes closest (real
dashboard, wrong channel-class for transferability). The only credible *mechanism-level*
receipts in the corpus: the 7s-video / 86%-stayed / 28s-AVD Shorts panel (PtO7jd8L2xs), the
$3→$6 RPM jump at 34-min runtime (BePppCvXC-k, shown), and the $200 → 1,419 views + 380 subs
Promotions benchmark (ROPkHP8jpW0, shown — and it argues AGAINST paying).

### 1.2 Affiliate / course / lead-magnet funnels
- **Affiliate tool pushes**: VidIQ (8N7-vQ9qX4w — the entire video is a VidIQ funnel dressed
  as "NEW algorithm rules"; 1ywvAeaFojo; BePppCvXC-k — desc credits vidIQ for a method the
  video never shows, affiliate bait-and-switch; E_CIP98ufto; QfbGKfkGP8U; 32DLRsFiXZY),
  NexLev/GenAIPro/ElevenLabs referrals (8KXlxAKOTdE, ipbnR92Elxg, Oi3nSYYQ6sM, PtO7jd8L2xs),
  Abacus (4xWQ_fHLGAc, E_CIP98ufto), kie.ai (TiycelzfzC0, Dmqz8opSHzE), Kling/DuoPlus
  (KxsasFMMPpA), Edimakor (sMo5RT_dPxc), Printify/Post Planner/Kittl (KZKFlik4M8I), Noodle
  Tomato (8Mx2m0djgTA), Pippit — a tool that never even appears in the video (32DLRsFiXZY),
  alexya.ai + Fanvue + deep-link tool five-link stack (Z5Wn63kLhpI), and a cutt.ly-shortened
  undisclosed generator link under a "RIP Paid Tools" title (Qsi9MeLh95Q).
- **The Higgsfield sponsor cluster** (new-batch pattern): five videos independently route the
  same paid gen platform through referral/campaign links — LGYiPA5SKvw, f-ufEhGtVpw
  (higgsfield.ai/s/mcp-sanji_chien), vI4RdXMSq8c (mcp-sandyleeai), CxwFu1nEsZQ
  (yt-iammoneyguy), PaXuebdY75U. Treat any "Claude Code + Higgsfield" tutorial as a sponsor
  placement first, workflow second.
- **Coaching / course / mentorship upsells**: tICnK3Qb2k8, 8KXlxAKOTdE (4 book-a-call CTAs),
  ipbnR92Elxg, PtO7jd8L2xs, QfbGKfkGP8U, Ao_d-uaMJvk, Xf_J7kBzxvo, 3MPSrpIOpAo, r81ImbWaxEE
  (the "45-item do/don't list" is paywalled), LGYiPA5SKvw, TvJhpOxFRsE (every recommendation
  terminates at something he sells: Tube Accelerator, Tube Magic, vid.ai), YtpQSmu794k
  ("Harvard of YouTube coaching", <18% acceptance scarcity framing), Eb8wlFawjTw (the video IS
  the funnel it teaches), ROPkHP8jpW0 (Skool), Oi3nSYYQ6sM (Typeform call first link),
  9iP588aMFBc ($1/7-day course trial), PaXuebdY75U (Ultimate Editors 2.0 — the three "brains"
  are gated in the course), Z5Wn63kLhpI (paid Skool; tells sub-$2K earners to re-register
  through his Fanvue referral).
- **Seller-conflict special**: 54UTQ2kFhuA sells BOTH the research tool (ChannelRecipe) and
  the aged channels (headstartchannels.com) his method requires; zq_Yi1gK6Fc funnels to his
  own chatbot-template site whose requirements quietly include paid ChatGPT + Veo 3
  *(desc-sourced)*; vuo_bPhkD_U is a launch video for the presenter's own paid plugin.
- **Prompt-doc / community lead magnets**: Telegram "Zen_Earn" mill (NlfmQpSaYMo, h6DB0e96GI0,
  lDpOnE3VJVI, lL9gjPw5yjg, JpvaUUgtTVk); WhatsApp (0SPqPnpQsWE, 3MPSrpIOpAo); Skool/Discord
  (Dmqz8opSHzE, TiycelzfzC0, KxsasFMMPpA, 8KXlxAKOTdE, vI4RdXMSq8c, oWkUwno6b0E via Gumroad,
  Qsi9MeLh95Q); Gumroad (4xWQ_fHLGAc, E_CIP98ufto); Telegram (zJmYdcvwY1Y); Patreon
  (KLswOquhsM8, mild); zapiwala.ai tracked redirects on every link (WVT2FCjhDDY).

**Filter rule**: funnel presence doesn't automatically zero a video (Dmqz8opSHzE, TiycelzfzC0,
KLswOquhsM8, PaXuebdY75U, oWkUwno6b0E are funnel-backed AND mechanically solid) — but any
claim that exists *only* to justify the funneled product (trust scores → aged channels; "new
rules" → VidIQ trial; "views are vanity" → course) is discarded.

### 1.3 "Free tool" bait that is actually paid, capped, or watermarked
- **"Omni Flash / Flow is free"** — Omni Flash is a paid Gemini-tier model and Flow's free
  tier is ~50 credits/day of *watermarked* Veo output (per our own 2026-07-20 audit,
  `reference_ai_cardboard_diy_niche`): NlfmQpSaYMo, h6DB0e96GI0, sMo5RT_dPxc, lDpOnE3VJVI,
  lL9gjPw5yjg, JpvaUUgtTVk. "Unlimited free Nano Banana" (NA0AOlCmelQ), "no limit" bulk stills
  (zJmYdcvwY1Y), and "free and UNLIMITED" (Qsi9MeLh95Q — contradicted by the same video's own
  Vids 10-12/day cap) all conflict with the same audit.
- **The tell**: "100% free" tutorials that then teach a *watermark-hiding step*
  (scale-and-shift or overlay) — the hidden cost admitting itself (NlfmQpSaYMo, lDpOnE3VJVI).
  SynthID invisible watermarking survives the crop; concealment only adds
  provenance-obfuscation risk.
- **Free-credit multi-accounting as a "hack"**: fresh-browser Flow refills (32DLRsFiXZY),
  10-minute-mail accounts (3MPSrpIOpAo), multi-Gmail Wan farming (NA0AOlCmelQ), HeyGen
  free-account cycling (PtO7jd8L2xs), FoziScribe account churn (WVT2FCjhDDY), SIM/IP-rotation
  account farms (Z5Wn63kLhpI) — all platform ToS abuse.
- **Gray-market credit resellers**: AI33.pro reselling ElevenLabs at $5/1M credits
  (3MPSrpIOpAo); GenAIPro (ipbnR92Elxg, 8KXlxAKOTdE).
- **"Free local" with a hidden platform catch**: the plugin's free local ComfyUI mode is
  Windows-only *(desc-sourced)*, gutting the pitch for this Mac operation (vuo_bPhkD_U).

### 1.4 Aged-channel tricks disguised as skill
- **Buying aged/pre-monetized channels is the hidden engine of "monetized in days" claims**:
  stated openly as "Trick No. 1" (0SPqPnpQsWE); productized as headstartchannels.com behind a
  "trust score" theory (54UTQ2kFhuA); the "$35K from zero" case started on a purchased
  pre-monetized channel (PtO7jd8L2xs); normalized with a half-warning (8KXlxAKOTdE);
  region-registered TikTok accounts sold to viewers (KxsasFMMPpA). Account trading violates
  YouTube ToS (non-transferable accounts) → termination risk.
- **The aged-channel confound also poisons the corpus's best-looking experiment**: the
  "expensive channel wins 100x" result rode a rebranded aged channel vs a fresh one
  (ROPkHP8jpW0) — so even *quality* conclusions in this genre can secretly be aged-channel
  effects.
- **"Trust score" / shadow-ban warming rituals** — folk theory YouTube has never confirmed
  (8KXlxAKOTdE, 54UTQ2kFhuA, q0G-FzS6uxk). The *behaviors* (real watch/like/comment warm-up,
  phone/ID feature verification) are free and harmless and worth doing (q0G-FzS6uxk); the
  *mechanism* is unfalsifiable.

**Filter rule**: any genre claim of "monetized in 2-10 days" is read as an aged-channel
purchase in disguise and discarded (0SPqPnpQsWE, 54UTQ2kFhuA, PtO7jd8L2xs, Ao_d-uaMJvk's
"under 1-2 months" gets the same discount).

### 1.5 Title bait & keyword-riding (new-batch pattern)
- **"Claude Code" in the title, absent from the workflow**: WVT2FCjhDDY (uses the Claude.ai
  free web app), 4xWQ_fHLGAc (entire workflow is Abacus AI, his affiliate).
- **False-novelty framing**: "NEW algorithm rules" that are years-old Studio features
  (8N7-vQ9qX4w); "untapped / 0-competition niches" contradicted inside the same video
  (tICnK3Qb2k8) or evidenced by a single unnamed channel (NlfmQpSaYMo, lL9gjPw5yjg,
  h6DB0e96GI0, sMo5RT_dPxc, 6WDvO0Lu1sY); "wireframe art" title for twig-sculpture content —
  pure SEO mismatch (lL9gjPw5yjg); an unspecified "powerful new YouTube feature" tease never
  substantiated (Eb8wlFawjTw); "US government banned Fable 5" hype (LGYiPA5SKvw).
- **"Fully automated" claims refuted by the video's own footage**: multiple manual correction
  rounds shown (vI4RdXMSq8c); the "under 10 minutes" pipeline retains a fully manual per-scene
  Grok stage (ylezKJG7rb8); "Claude edited an entire documentary" but assembly is manual
  Premiere (PaXuebdY75U); "5 minutes" for a gen+edit workflow (32DLRsFiXZY).

### 1.6 Policy silence as a red flag
Videos teaching exactly the mass-produced template-AI profile that the July-15-2025
"inauthentic content" YPP policy targets, with zero mention of it: 8Mx2m0djgTA, 6WDvO0Lu1sY,
Ao_d-uaMJvk, h6DB0e96GI0, NA0AOlCmelQ, lDpOnE3VJVI, sMo5RT_dPxc, Dmqz8opSHzE, TiycelzfzC0,
KxsasFMMPpA, 8KXlxAKOTdE, JpvaUUgtTVk, WVT2FCjhDDY, ylezKJG7rb8, zq_Yi1gK6Fc, CxwFu1nEsZQ,
f-ufEhGtVpw (which goes further: "YouTube does not block AI content," unsourced). Watch-hour
farming via a looped "live" stream (eF75ZffgsUk) is the same trap in stream form. The genre's
silence is itself intel: our transformative layers (composites into real footage, measured
grammar, original scripts, source credits) are the moat these videos don't have.

---

## 2. Conflict list — adjudicated

Tiebreakers, in order: (1) hard rules in STRATEGY_CONTEXT.md beat everything; (2) measured
data (`edit_grammar_ruleset.md`, `viral_recreation_spec.md`) beats guru round numbers; (3)
when two gurus disagree, the one with an on-screen mechanism wins; (4) unresolved → TEST, not
ADOPT. ⭐ = the three most consequential conflicts.

### C1 ⭐ Sameness paradox: "double down on the winner" vs "vary or get demonetized"
- **Double-down side**: squeeze a proven formula until dry (zJmYdcvwY1Y); 80/20 repeat rule
  (8KXlxAKOTdE); outlier-doubling — stop rotating concepts mid-streak (Oi3nSYYQ6sM); 48h
  sequel rule (ZKsldrcO_fU); sequel-on-steroids while the audience is hot (BePppCvXC-k).
- **Vary side**: rotate the caption template every ~10 uploads or risk demonetization
  (PtO7jd8L2xs); "try not to work on the same template" from a practitioner already in
  community-guidelines trouble (0SPqPnpQsWE); a YPP rejection whose stated term was
  "mass-produced" for stylistically identical videos — with a HUMAN voice — cured by deleting
  lookalikes and changing style (4xWQ_fHLGAc); CEO-blog AI-slop enforcement quotes
  (q0G-FzS6uxk); "100% AI slop gets demonetized" (YtpQSmu794k).
- **Adjudication — both are right at different layers.** Repeat the *format concept*
  (topic/packaging/thumbnail formula — the thing the audience clicked), vary the *surface
  execution* (edit fingerprint, template styling, per-beat vantage). This is exactly what the
  clip-variety rule already enforces intra-video; extend it inter-video: diff each new
  upload's motion-event fingerprint (`extract_motion_events.py`) against the previous one so
  `rexcaped_edit_engine.py` never stamps identical grammar on consecutive uploads
  (0SPqPnpQsWE application). Sequel-on-a-winner = ADOPT (ideation.json); identical-template
  churn = the demonetization archetype.

### C2 ⭐ Cut pacing: 3s vs 2.5s vs 4-6s vs 5-15s vs 7-8s vs the measured grammar
- "Change visuals every 3 seconds" (LGYiPA5SKvw) — his own generated output ignored the rule
  (clips ran 5-7s) and he shrugged. "2.5s hard ceiling on static-image holds" for
  stills-driven POV (Ao_d-uaMJvk, no data). "One image per 5-15 seconds" (Dmqz8opSHzE).
  4s/6s-only clips, ~4-6s cuts (TiycelzfzC0). One image per 7-8s (f-ufEhGtVpw, CxwFu1nEsZQ).
- **Adjudication: trust the measured grammar.** `playbook/editing.json` (cuts every 5-7s) and
  `edit_grammar_ruleset.md` (0.07-0.13s rapid-fire montages on lists, cut-on-numbers,
  cut-on-turn-words, sound on every cut) are *measured from winning competitor videos*.
  TiycelzfzC0 (4-6s) and f-ufEhGtVpw/CxwFu1nEsZQ (7-8s) independently bracket the same range —
  convergent confirmation. The 3s round number is self-refuted on screen; 5-15s holds violate
  the grammar. The 2.5s static-still ceiling survives only as a *narrow TEST parameter for
  Prehistoric POV stills* (a format the longform grammar wasn't measured on) — not a law.

### C3 ⭐ Post-upload judgment window: 48h vs 72h vs 14 days vs 4-6 weeks
- Judge CTR+AVD vs channel baseline at 24-48h, then sequel or pivot (ZKsldrcO_fU). 72h
  indexing delay — 0 views for 3 days is normal (q0G-FzS6uxk, shown on his analytics). Zero
  impressions for 10-14 days then explosion; week-1 recommendations go to mis-matched
  audiences, so early CTR/retention is noise (BePppCvXC-k, shown in Studio). No repackaging or
  write-offs before 4-6 weeks — the cheap channel 4.4×'d untouched (ROPkHP8jpW0, shown);
  flopped videos get retro-tested after a later video passes its cohort test, so never delete
  them (9iP588aMFBc).
- **Adjudication: window scales with channel maturity.** New/small channels (all three of
  ours): hard 14-day no-touch rule (no deletes, re-uploads, or packaging changes), verdicts at
  4-6 weeks, never delete flops, judge a channel only after ~5 uploads (BePppCvXC-k +
  ROPkHP8jpW0 + 9iP588aMFBc — the three strongest on-screen receipts in the corpus, all
  new-batch). ZKsldrcO_fU's 48h sequel/pivot rule applies only once a channel has a real CTR/
  AVD baseline to compare against — file it in retention_delivery as the *mature-channel*
  protocol. These rules are compatible, not contradictory, once staged by channel age.

### C4. Volume vs quality
- Volume side: 1-2 uploads/day (54UTQ2kFhuA, Oi3nSYYQ6sM), 3-15 posts/day (E_CIP98ufto), 3
  videos/day (ylezKJG7rb8), $15-30 outsourced videos sprayed across test channels
  (8KXlxAKOTdE). Quality side: weeks per video at 20-34 min took a new channel to ~$1K/day in
  5 uploads *(unverified totals, shown mechanics)* (BePppCvXC-k); "quality beats AI slop"
  (ROPkHP8jpW0, confounded); volume-as-*feedback*, not algorithm juice (ZKsldrcO_fU,
  9iP588aMFBc).
- **Adjudication: quality-gated cadence wins for us.** Hard bars (85+ topic, 95+ script,
  frame-level QA) are non-negotiable; platforms hard-cap repetitive volume (TikTok's
  ~300-videos/30-day low-quality ban, r81ImbWaxEE *(unverified but consistent)*; July-2025 YPP
  policy). What we *take* from the volume side is reps-as-data: ship enough uploads (5+ per
  channel) to get a cohort-test passer before judging any channel — which indicts Prehistoric
  POV's stalled 1-video state, not the quality bars.

### C5. "Make it longer than competitors" vs retention-first pacing
- Longer-is-better: pad past competitors to win watch time (ipbnR92Elxg), 1.5× competitor
  length (8KXlxAKOTdE), stretch 10-min videos to 12-13 and ride a 2h ladder (zJmYdcvwY1Y,
  3MPSrpIOpAo), length ≥ 90th percentile of topic winners (8N7-vQ9qX4w).
- Length-pays evidence: $3→$6 RPM at 34 min via midrolls (BePppCvXC-k, shown); long-form
  raises RPM (Oi3nSYYQ6sM *(estimate)*; bizdoc's whole $10-25 RPM thesis).
- **Adjudication: length follows the story and the measured winner range — padding never.**
  retention_delivery.json is the gate; bizdoc's 23.4-min video already sits inside the
  winner range 8N7-vQ9qX4w shows (19-40 min). Midroll economics are real (the one shown
  receipt) and argue for *earned* runtime, not stretched runtime. "Pad to beat AVD" conflates
  absolute watch time with AVD% and risks the curve — IGNORE.

### C6. Thumbnails: decisive vs "topic+length matter more"
- "Topic and length outrank thumbnails/quality" (8N7-vQ9qX4w, asserted, no data) vs
  thumbnail-first ideation with a scrap threshold (q0G-FzS6uxk), thumbnail-first production
  gate (ipbnR92Elxg), thumbnail-text-first scripting (3MPSrpIOpAo), title/thumbnail/intro
  congruence trifecta (YtpQSmu794k), packaging-is-everything (8KXlxAKOTdE).
- **Adjudication: packaging-first wins** — it is the majority position, matches
  `titles_thumbnails.json` (26 tactics) and the topic scorer's title_thumbnail +
  five_second_title gates. The 8N7 claim serves its VidIQ funnel. One scoped exception:
  PSR-established channels can survive bad packaging (Xf_J7kBzxvo) — irrelevant to
  zero-audience channels, so packaging discipline stays.

### C7. Thumbnail source: video frames vs gen-from-scratch vs reference-conditioned
- "Grab the most significant video frame, ask ChatGPT for a simple thumbnail" (Ao_d-uaMJvk)
  vs our measured recipe (candid real-phone-photo look, ONE focal point, gen from scratch, NO
  video frames — `feedback_dinoverse_thumbnail_style`); reference-image-conditioned
  generation beat a $60 commissioned design (ROPkHP8jpW0, shown); competitor-thumbnail style
  transfer via GPT image gen (3MPSrpIOpAo, shown); quality-degrade prompt line for realism
  (ipbnR92Elxg); desaturate/decontrast for natural iPhone look (Z5Wn63kLhpI).
- **Adjudication: the recipe stands; frames-as-thumbnails is IGNORE** (contradicts a measured
  winning formula). Reference-conditioning and the desaturation knob are compatible
  *refinements* → TEST as A/B variants inside the existing recipe, not replacements.

### C8. Is faceless dead? "Squeezed into oblivion" vs "faceless prints money"
- Death side: undifferentiated "say-nothing faceless" channels get squeezed out of the feed
  (ZKsldrcO_fU — industry-adjacent vidIQ, opinion but meaningful); viral AI entertainment is
  a commoditizing race to the bottom (TvJhpOxFRsE, self-serving); "AI slop trust recession"
  (Eb8wlFawjTw). Alive side: ~20 tutorials selling faceless template channels (h6DB0e96GI0,
  NlfmQpSaYMo, sMo5RT_dPxc, WVT2FCjhDDY, CxwFu1nEsZQ, f-ufEhGtVpw, …); task-attraction
  research says educational channels build parasocial bonds with no face (Xf_J7kBzxvo);
  human-directed AI systems monetize fine (YtpQSmu794k, 4xWQ_fHLGAc).
- **Adjudication: both, split by differentiation.** The squeeze targets *undifferentiated
  template* output — exactly what the tutorials in section 1 mass-produce. Differentiated
  faceless (measured grammar, composited real footage, locked VO persona, original research,
  source credits) is the survivable position every credible source converges on
  (ZKsldrcO_fU's own barbell, YtpQSmu794k's director model, q0G-FzS6uxk's originality
  standard). This is the strategy context's existing bet — reinforced, not changed.

### C9. AI voice: safe, risky, or the trigger?
- "AI voice is not the demonetization trigger; 'mass-produced' sameness is" (4xWQ_fHLGAc,
  anecdote with specifics); "AI voices are allowed, but don't use the stock voice everyone
  uses" (CxwFu1nEsZQ, TvJhpOxFRsE); "robot voice on a prompt = slop that gets banned"
  (YtpQSmu794k); voice-cloning a *stranger* risks demonetization or ban (Oi3nSYYQ6sM), while
  3MPSrpIOpAo claims competitor voice-cloning has "no monetization issue" — flatly dangerous.
- **Adjudication**: AI VO is acceptable inside a differentiated, human-directed production
  (multiple independent confirmations); voice *sameness* is a real risk vector → run the
  voice-sameness audit on stock ElevenLabs voices (Liam/Jessica/Brian, Mark) as a TEST
  (CxwFu1nEsZQ, TvJhpOxFRsE); bizdoc's owner-clone already complies. Cloning other people's
  voices = impersonation risk, never do (3MPSrpIOpAo's claim is wrong).

### C10. Account trust/warming vs per-video bandit ("subs don't matter")
- Trust side: warm accounts for weeks, aged accounts get reach, fresh ones are throttled
  (8KXlxAKOTdE, 54UTQ2kFhuA, q0G-FzS6uxk, 0SPqPnpQsWE). Bandit side: YouTube is a per-video
  recommendation engine; any small channel can break out on one upload (ZKsldrcO_fU shown
  n=1; 9iP588aMFBc mechanism; PtO7jd8L2xs viewer-profile matching).
- **Adjudication**: the bandit model has the better evidence and matches our launch premise;
  the trust *mechanism* is unfalsifiable folk theory. But the trust-side *behaviors* are free
  and plausibly reduce bot-suspicion friction → ADOPT the behaviors (real-usage warm-up,
  phone/ID feature-eligibility verification before first upload — q0G-FzS6uxk, eF75ZffgsUk),
  IGNORE the theory, never buy accounts. Unresolved residue: ROPkHP8jpW0's aged-channel
  confound is weak evidence that channel age *does* matter — insufficient to change anything.

### C11. Off-platform description links: penalized or standard practice?
- "YouTube suppresses videos that push viewers off-site; never link out — route everything
  through an on-channel money video" (TvJhpOxFRsE, zero evidence) vs day-one affiliate links
  with FTC disclosure (LGYiPA5SKvw, shown), per-video attribution params on description links
  (Eb8wlFawjTw, self-demonstrated), and bizdoc's planned sponsor links.
- **Adjudication**: the penalty claim is evidence-free and self-serving; description links
  stay (bizdoc sponsors + source credits are strategy). The *compatible* half — end-screen
  chaining to the channel's strongest video and a named-video handoff — is free and adopted
  anyway (TvJhpOxFRsE, Eb8wlFawjTw). No conflict survives.

### C12. "Editing can't be automated" vs our pipeline
- "You won't be able to automate the editing; everything must be manual" (zJmYdcvwY1Y);
  manual CapCut/Premiere assembly as the recommended final step (Dmqz8opSHzE, Ao_d-uaMJvk,
  PaXuebdY75U, oWkUwno6b0E, WVT2FCjhDDY, CxwFu1nEsZQ, Qsi9MeLh95Q) vs automated
  Claude+Whisper+FFmpeg editing demonstrated (vI4RdXMSq8c) and our own
  `ffmpeg_production_render.py` + `verify_render.py`.
- **Adjudication: trivially our side** — the operation's renderer already automates what
  every one of these videos does by hand, with an auto-QA watcher on top. Their manual
  assembly is the *weakest* step of every demoed pipeline; never import it.

### C13. Broad appeal vs niche-down
- "One character, unlimited topics" (zq_Yi1gK6Fc); "go mass market, not niche"
  (Z5Wn63kLhpI) vs niche-within-niche for algorithmic classifiability (q0G-FzS6uxk,
  9iP588aMFBc, TvJhpOxFRsE sub-niche doctrine, tICnK3Qb2k8).
- **Adjudication: niche-down wins on YouTube** — the bandit needs a classifiable audience
  cluster (9iP588aMFBc mechanism + q0G-FzS6uxk). "Broad" is only safe *inside* a legible
  niche (Rexcaped's creature-attack frame is broad-appeal but algorithmically legible).
  Topic-hopping one mascot across unlimited topics fails the topic scorer and maximizes
  repetitive-template exposure. First 3-5 uploads per channel stay in ONE sub-niche (ADOPT).

### C14. Shorts: AVD goldmine, discovery surface, or reused-content trap?
- Shorts distribution keys purely on STW/AVD, loop-shorter-than-read-time pushes AVD past
  100% (PtO7jd8L2xs — the corpus's one real analytics receipt); Shorts surface across
  homepage/search/Google and out-reach long-form ~15× (8N7-vQ9qX4w, own-channel demo);
  sub-CTA Shorts close the 1K-sub YPP gate (BePppCvXC-k) — vs text-commentary Shorts built
  on wholesale-reused TikTok clips claimed "transformative" (QfbGKfkGP8U, dangerous), and
  Shorts RPM of ~$0.05-0.07/1K implied by his own numbers.
- **Adjudication**: Shorts = discovery + sub-gate instrument built ONLY from owned assets
  (9:16 crops of composites, AVD-hack captions), gated by the Shorts metric thresholds
  (STW ≥75-80%, AVD ≥100%). Reused-clip Shorts violate fair-use hard rules and the
  inauthentic-content policy — IGNORE. Revenue expectations stay near zero; that's fine,
  it's a funnel.

### C15. Tooling ground truth: "Grok free tier is dead" vs our recipes
- Qsi9MeLh95Q claims Grok Imagine's free tier was killed *(unverified, no screenshot)* —
  directly contradicting the operation's primary i2v engine assumptions
  (`reference_grok_i2v_clipboard_upload`, Dinoverse workflow).
- **Adjudication**: our own docs are the standing truth until falsified, but this is a
  cheap, urgent check → verify Grok free-tier status BEFORE the Spino/Lagos i2v batch; if
  degraded, the corpus supplies $0 fallbacks to physics-QA: Meta AI frame-to-video and
  Google Vids' daily Veo allowance (Qsi9MeLh95Q), local VACE/LTX (in-house).

---

## 3. Advice popular in this corpus but WRONG for us (hard rule violated)

| Popular advice | Pushed by | Hard rule it violates |
|---|---|---|
| Buy aged / pre-monetized channels for instant reach | 0SPqPnpQsWE, 54UTQ2kFhuA, PtO7jd8L2xs, 8KXlxAKOTdE, KxsasFMMPpA | YouTube ToS (non-transferable accounts) + clean-channel posture; termination risk on the #1-risk surface |
| AI avatar / HeyGen presenter, face-swap real people, public-figure filter evasion | PtO7jd8L2xs, ipbnR92Elxg, TvJhpOxFRsE, Z5Wn63kLhpI, KLswOquhsM8 (human-swap path), TiycelzfzC0 (black-bar trick) | **No AI-generated human faces** (owner hard rule); YtpQSmu794k independently calls avatar presenters a demonetization risk |
| Subscribe to the sponsor gen stack (Higgsfield, kie.ai, Noodle Tomato, NexLev, VidIQ paid, Abacus, fal.ai default, Kling via Higgsfield) | LGYiPA5SKvw, f-ufEhGtVpw, vI4RdXMSq8c, CxwFu1nEsZQ, PaXuebdY75U, Dmqz8opSHzE, TiycelzfzC0, 8Mx2m0djgTA, 8KXlxAKOTdE, Oi3nSYYQ6sM, 8N7-vQ9qX4w, 4xWQ_fHLGAc, r81ImbWaxEE, vuo_bPhkD_U | **No new paid APIs/subscriptions without asking**; $0 in-house equivalents exist (Grok i2v, local VACE/LTX, WhisperX, FFmpeg) |
| Assemble manually in CapCut/Premiere/DaVinci; "editing can't be automated" | zJmYdcvwY1Y, Ao_d-uaMJvk, Dmqz8opSHzE, PaXuebdY75U, oWkUwno6b0E (DaVinci sync), vuo_bPhkD_U (DaVinci-centered), WVT2FCjhDDY, CxwFu1nEsZQ, Qsi9MeLh95Q, E_CIP98ufto | **FFmpeg is the assembly engine; DaVinci is manual polish only** — the renderer + verify_render.py already automate and QA this |
| Multi-account farms / free-credit churn (cloud phones, temp mail, fresh browsers, multi-Gmail) | KxsasFMMPpA, NA0AOlCmelQ, 3MPSrpIOpAo, 32DLRsFiXZY, WVT2FCjhDDY, Z5Wn63kLhpI, Qsi9MeLh95Q | Platform ToS abuse; maps directly onto the inauthentic-content criteria — the operation's #1 platform risk |
| Hide the gen watermark (scale-and-shift / overlay) | NlfmQpSaYMo, lDpOnE3VJVI | Frame-level QA + provenance discipline; SynthID survives the crop, concealment = intent evidence |
| Wholesale clip reuse "transformed" by text overlay or webcam; OBS-record streaming services | QfbGKfkGP8U, PtO7jd8L2xs | Fair-use hard rules (≤7s/clip, ≤30s/source, muted audio, transformative layers); copyright + July-2025 policy exposure |
| Loop a pre-recorded video as a 24/7 "live" stream to farm the 4,000 hours | eF75ZffgsUk | Inauthentic-content policy (the one true fact — live hours count — doesn't rescue the fake-live method) |
| Rewrite competitor transcripts as your script | zJmYdcvwY1Y | 95+ original-script quality bar + originality test in `topic_scorer.py`; reused-content risk |
| Post 3-15 videos/day; outsource $15 videos; no-script "words of the heart" production | E_CIP98ufto, ylezKJG7rb8, Oi3nSYYQ6sM, r81ImbWaxEE, 8KXlxAKOTdE, 0SPqPnpQsWE | 85+/95+ quality bars, frame-level QA before owner watch-through; repetitive-volume is what platforms hard-cap |
| Leave the AI/altered-content disclosure OFF ("we transformed it ourselves" / "click no") | E_CIP98ufto, eF75ZffgsUk | Disclosure posture: Rexcaped/PPOV photoreal creatures in real footage tick YES; never copy the click-no advice |
| "Any random looping visuals are fine" under AI narration | 3MPSrpIOpAo | Measured edit grammar + clip-variety rule exist precisely to avoid this repetitive-content profile |
| Pad runtime to beat competitors on watch time (1.5×, 2h ladder) | ipbnR92Elxg, 8KXlxAKOTdE, zJmYdcvwY1Y, 3MPSrpIOpAo | retention_delivery.json retention-first pacing; length is story-driven (see C5) |
| Clone a competitor's or streamer's voice ("no monetization issue") | 3MPSrpIOpAo (claim), Oi3nSYYQ6sM (documents the risk) | Own-voice-only policy; impersonation/inauthentic-content exposure |
| Generate AI backdrops behind subjects (invert the composite) | vuo_bPhkD_U | `viral_recreation_spec.md` measured law: AI creature INTO real footage — real backgrounds are the credibility layer |
| Buy YouTube Promotions for launch growth | ROPkHP8jpW0 (his own data: $0.53/sub, no flywheel) | No-spend-without-prototype rule — and the corpus's only paid-growth receipt argues against it |
| Delete-and-repost dead videos to a fresh channel | 8KXlxAKOTdE | Reused-content review risk + contradicts the retro-testing evidence (9iP588aMFBc, never delete flops) |
| Thumbnail = exported video frame | Ao_d-uaMJvk | Measured thumbnail recipe (gen from scratch, candid phone-photo, ONE focal point, no video frames) |
| Install untrusted third-party Chrome extensions / community plugins that touch your Google session or spend credits | WVT2FCjhDDY (Zapi Flow), Qsi9MeLh95Q (Auto Flow/Meta Automation), Dmqz8opSHzE (community plugin), oWkUwno6b0E (Anti-Gravity skill) | Supply-chain/prompt-injection surface; in-house browser automation recipes already exist |

---

## 4. Tier ranking — all 54

**A = load-bearing** (multiple standing rules or corpus-critical evidence come from it).
**B = one nugget** (one-to-two cheap tests or checklist lines survive the filter).
**C = ignorable** (nothing survives that isn't already covered better elsewhere).

### Tier A — 16 videos
| id | one-line justification |
|---|---|
| PtO7jd8L2xs | The corpus's only credible Shorts analytics receipt (86% STW / 400% AVD) + quantified niche-gap thresholds; also the archetype specimen of every hype pattern at once. |
| Xf_J7kBzxvo | Three adopted scripting-QA lenses (direct-address density lint, coffee-shop rule, comment referencing) + task-attraction validation of the faceless bet. |
| 8KXlxAKOTdE | Supply-check threshold, 80/20 double-down, and impressions-based failure diagnosis all wired into scorer/ideation — despite being a naked coaching funnel. |
| q0G-FzS6uxk | Best policy sourcing in corpus (verbatim CEO/guidelines quotes) + adopted launch mechanics: warm-up/ID verification, 72h window, no low-intent seeding. |
| QfbGKfkGP8U | Donated the vignette-spotlight attention guide and the operation's first vertical caption grammar — while its business model is the reused-content trap itself. |
| TiycelzfzC0 | Four portable i2v mechanics (0.25s head-trim ADOPT, timestamp-conditioned prompts, per-still style-reference, low-volume clip SFX) with real demos. |
| 4xWQ_fHLGAc | The channel-metadata layer we never built (cold-start keyword seeding, auto-dub, unlisted-first) + the corpus's most specific "mass-produced, not AI-voice" YPP rejection/remedy anecdote. |
| LGYiPA5SKvw | Ranked-backlog batch scoring, FTC boilerplate, WIPO name check — honest cost data ($95 stunt) despite the sponsor stack. |
| YtpQSmu794k | Most verifiable revenue in corpus (live Studio refresh + currency check) + congruence gate, AdSense-linkage cascade-ban audit, overage scripting, launch-window engagement. |
| ZKsldrcO_fU | The 48h CTR/AVD sequel-or-pivot protocol (fills the missing post-upload feedback loop) + the industry-side "faceless squeeze" warning that frames our differentiation. |
| BePppCvXC-k | Best channel-ops analytics intel: 14-day cold start, mis-targeted early recommendations, monetize-early/pre-acceptance-views-pay-$0, sub-CTA-Short gate — all shown in Studio. |
| ROPkHP8jpW0 | Patience rule (4-6 weeks), mashup ideation, and the only paid-Promotions benchmark ($0.53/sub — don't) — plus a live lesson in confounded experiments. |
| 9iP588aMFBc | Bandit/test-impression model with the retro-testing insight: never delete flops, judge at ~5 uploads, keep early uploads in one sub-niche — cheap standing rules. |
| PaXuebdY75U | The design-brain recipe (reference wall → codified design system) fills bizdoc's one real visual-spec gap + 5-layer animator grammar as an i2v scaffold. |
| oWkUwno6b0E | Remotion as a $0 animated-stat/chart layer bizdoc lacks vs ColdFusion/HMW + the creative-direction-lock prompt pattern adopted across all batched generation. |
| KLswOquhsM8 | High-credibility local-VFX overlap: audio-conditioned talking-character gen attacks the jaw-sync QA problem at the source, Relay-Prompt timing mirrors AMBER, Omni Voice is an F5-TTS license lead, resolution-equality assertion adopted. |

### Tier B — 32 videos
| id | one-line justification |
|---|---|
| KxsasFMMPpA | One nugget: the first-person 2-beat twist-story vertical format as a Prehistoric POV probe; everything else is DuoPlus sponsor ToS-bait. |
| 54UTQ2kFhuA | One nugget: competitor-corpus → Claude demand-gap clustering as a free ideation front-end; ignore both products he sells. |
| E_CIP98ufto | Metaphor/save-share beat for shorts cuts + FB invite-threshold intel; also the codified negative example on AI-disclosure. |
| ipbnR92Elxg | Thumbnail-first production gate + the YPP decline-then-appeal precedent (archive an editorial paper trail per video). |
| zJmYdcvwY1Y | The monetization-survivor scan (hit channel suddenly stops uploading = YPP denial tell) is a real niche-vetting pre-check; the rest is a weaker version of our pipeline. |
| sMo5RT_dPxc | Save-last-frame-then-animate chaining, scoped to continuous-action pairs so it never violates the clip-variety rule. |
| NlfmQpSaYMo | Counterfactual-deletion cold open + "history of X" ideation seeds for bizdoc; workflow itself is watermark-hiding template bait. |
| eF75ZffgsUk | Two checklist lines survive: feature-eligibility/phone-verify unlock (bizdoc needs >15-min uploads) and the per-channel AI-disclosure decision; the method itself is a trap. |
| KZKFlik4M8I | One test: zero-cost FB page reposts of existing verticals; its ~$0.08/1K FB payout datapoint confirms the high-RPM YouTube bet. |
| r81ImbWaxEE | 3-prompt-variants best-of-N for Grok i2v + the TikTok ~300/30-day cap as cross-platform evidence that repetitive AI volume gets punished. |
| lDpOnE3VJVI | Gemini music-gen as a rights-gated $0 custom-bed test; also produced the standing watermark-hiding never-do rule. |
| 8N7-vQ9qX4w | Shorts multi-surface reach + single-variable A/B protocol + the weekly-audit pattern (clone free, skip VidIQ); wrapped in false-novelty framing. |
| 32DLRsFiXZY | Last-frame continuity chaining with the concrete FFmpeg `-sseof` port; niche and credit-farming ignored. |
| tICnK3Qb2k8 | Legal/corporate adversarial-curiosity title formulas + "POV: you're the [role]" packaging + Google Trends as a timeliness input; niche scores are marketing. |
| CQWfqKGFoPM | High-credibility policy news (Aug-17 membership smart pricing) worth one dormant checklist line + a textbook deadline-hook worked example. |
| 0SPqPnpQsWE | One real signal: template-sensitive repetitive-content detection → the inter-video edit-fingerprint diff experiment; everything else is aged-channel bro-science. |
| 3MPSrpIOpAo | Competitor-thumbnail style transfer via GPT image gen + the bizdoc channel-settings/SEO pass; voice-clone and multi-account advice is dangerous. |
| Dmqz8opSHzE | SAM 2 local multi-element segmentation as a free layered-composite upgrade (parallax Ken Burns, between-layer creature placement); skip the plugin and paid stack. |
| 6WDvO0Lu1sY | Character turnaround sheets + chained-still state continuity as consistency experiments; the niche itself is template-AI demonetization territory. |
| Ao_d-uaMJvk | Three testable Prehistoric POV parameters (2.5s static ceiling, 150-200 scene density, "at every level" escalation format); thumbnail advice contradicts the recipe. |
| lL9gjPw5yjg | Google AI Studio TTS as a licensed $0 VO fallback (relevant while F5-TTS is CC-BY-NC-blocked); niche pitch recycled Telegram-mill content. |
| 1ywvAeaFojo | Screenshot-to-design-system chapter cards + the owner interview-pass for bizdoc differentiation; honestly scoped as not-for-faceless. |
| CxwFu1nEsZQ | Entity-bible batch-still prompt pattern (read whole script → recurring-entity bible → per-timestamp stills) portable to $0 Gemini access + the voice-sameness audit. |
| Eb8wlFawjTw | Per-video attribution params on description links + the named-video "goes deeper" end-screen handoff; the two-channel sales funnel itself is inapplicable. |
| Oi3nSYYQ6sM | Outlier-doubling adopted into ideation + the free four-signal fresh-entrant niche scan; all revenue math is estimate-on-estimate. |
| Qsi9MeLh95Q | The urgent Grok-free-tier-dead flag + two verifiable $0 i2v fallbacks (Meta AI frame-to-video, Google Vids Veo allowance); extensions are ToS-gray. |
| TvJhpOxFRsE | End-screen chaining and day-one pre-YPP affiliate links survive; every other recommendation terminates at one of his four products. |
| Z5Wn63kLhpI | Desaturate/decontrast prompt knob for the candid-thumbnail recipe + the own-baseline/multi-small-account trend filter; the OFM business and account farms are radioactive. |
| vI4RdXMSq8c | Hyperframes ($0 open-source) as an animated-chart lead + Opus-plan/Sonnet-execute model tiering and per-channel brand.md; "fully automated" framing refuted by its own demo. |
| vuo_bPhkD_U | Camera/lens/lighting preset vocabulary for i2v prompts + the clay-to-photoreal pattern as a $0 VACE experiment; the plugin itself contradicts the FFmpeg-engine rule. |
| ylezKJG7rb8 | Grok auto-gen-OFF setting + LLM-assigned camera-move vocabulary column for the i2v TSV; Auto Whisk batch-stills CONCEPT worth replicating with our own automation — the untrusted third-party extension itself stays banned (see action_plan DO-NOT-DO). |
| zq_Yi1gK6Fc | Character-lock descriptor blocks for recurring Dinoverse-clone hosts + the faithful-vs-optimized A/B pre-lock step; the one-character-unlimited-topics thesis is a policy trap. |

### Tier C — 6 videos
| id | one-line justification |
|---|---|
| h6DB0e96GI0 | 103-second Telegram-funnel prompt demo; only use is as a logged negative niche archetype — no mechanics we don't already exceed. |
| 8Mx2m0djgTA | Pure affiliate demo of a one-click video factory; every "tactic" is a weaker version of the topic scorer/playbook, and the product is the demonetization archetype. |
| NA0AOlCmelQ | Factually wrong on tools ("unlimited free Flow"), ToS-abuse tips, unevidenced success story; its one idea (character-block injection) is done better by our consistency system. |
| JpvaUUgtTVk | 151-second prompt-mill clip whose only salvage (two-keyframe conditioning) merely restates the already-planned VACE reference_images experiment. |
| WVT2FCjhDDY | Double-bait title ($77K never mentioned; Claude Code never used); its one mechanic (VO-pause scene cuts) is our WhisperX pipeline done worse, and the Flow-stills test is covered by better sources. |
| f-ufEhGtVpw | Higgsfield referral demo of a manual, inferior version of our WhisperX→paper-edit→FFmpeg pipeline; the MCP plumbing idea is covered better by CxwFu1nEsZQ. |

**Count check: 16 (A) + 32 (B) + 6 (C) = 54.** ✓
New-batch (22 videos added since v1) tier split: A ×8 (YtpQSmu794k, ZKsldrcO_fU, BePppCvXC-k,
ROPkHP8jpW0, 9iP588aMFBc, PaXuebdY75U, oWkUwno6b0E, KLswOquhsM8), B ×11, C ×3.
