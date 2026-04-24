# v47 SPEC — Corpus-Driven Rewrite

**Generated:** 2026-04-22 (council-compliant rewrite after corpus check)
**Status:** Thesis draft for approval before 3-hour rewrite clock starts
**Replaces:** v46 (flagged as 90% v45 in costume)

---

## TITLE

**Primary:** *The Apology Economy*
**Subtitle:** *Why Every Corporate Scandal Ends the Same Way*

### Alternate candidates (if primary doesn't hit)
1. *Why Every Corporate Scandal Ends the Same Way* (punchier, no tagline needed)
2. *The Ritual That Ends Every Corporate Scandal* (noun-forward, more documentary)
3. *The System Is Working As Designed* (most political; hardest promise to pay off)

---

## THESIS (one sentence, the 12 quotes must prove it)

> **When a company breaks the law, four things happen in order — apology, fine, defiance, continuation — and that sequence is what the system was actually built to produce.**

### Promise: THEATER, not math.
→ Corpus is sufficient. 3-hour rewrite clock starts.
→ **Does NOT require** the profit-vs-penalty math quote Outsider flagged missing.
→ **Does NOT require** Pinto/Wells/Purdue clips that don't exist.

---

## QUOTE → THESIS MAPPING (every one of the 12 lands)

| # | Quote | Step of ritual | Lands in |
|---|---|---|---|
| **2** | Zuck "major breach of trust, sorry" | APOLOGY | Act 1 |
| **3** | Zuck "we don't deserve to serve people" | APOLOGY (standard set) | Act 1 |
| **4** | FTC "Facebook betrayed trust" | ACCUSATION | Act 1 |
| **5** | FTC "privacy set by click-happy friends" | ACCUSATION (mechanism) | Act 1 |
| **7** | Zuck via anchor: "historic fine but more important..." | FINE + early DEFIANCE | Act 1 |
| **8** | "Meta fined €1.2B" | FINE | Act 1 |
| **9** | Meta: "disappointed, singled out, unjustified, dangerous precedent" | DEFIANCE | Act 1 |
| **10** | "old-fashioned price fixing using new technology" | ACCUSATION (RealPage) | Act 2 |
| **11** | AG: "housing cartel" | ACCUSATION (RealPage) | Act 2 |
| **12** | "extravagant profits... insulting" | CONTINUATION (RealPage) | Act 2 |
| **1** | AI: "independent artists... not going to get paid" | CONTINUATION (AI, newest form) | Act 2 |
| **13** | "whistleblowers exposed more fraud than audit + compliance + law enforcement combined" | THE ONLY THING THAT WORKS | Act 3 |

**#6 killed** (duplicate of #4).

---

## STRUCTURE — 3 acts, not 5 chapters

v45/v46 had FORMULA → DATA → MACHINES → RENT → RECKONING (5 chapters, 3 had zero footage).
v47 has 3 acts built from the ritual itself. Every beat has a clip.

### ACT 1 — The Ritual (0:00 – ~9:00) — Meta case study

Show the full cycle with ONE company so the viewer learns the pattern.

- **Cold open (0:00-0:45):** FTC #4 lands. Silence. Zuck apology #2 lands. Narrator (one line): *"Two people. Same event. Watch how the story ends."*
- **Thesis at 0:45:** One-sentence narration locks the thesis.
- **Setup of Zuck's standard (1:00-3:00):** #3 ("we don't deserve to serve people") → Cambridge Analytica context (narration, no clips needed).
- **The mechanism (3:00-5:00):** FTC #5 ("click-happy friends") → explain the actual deception.
- **The fine lands (5:00-7:00):** #7 and #8 back-to-back. Narration: the math the fine represents vs Facebook's revenue.
- **The defiance (7:00-9:00):** #9. The moment the mask slips. Narration interprets, doesn't accuse.

### ACT 2 — The Ritual Scales (~9:00 – 17:00) — Other industries

Same ritual, different industries. Prove the pattern isn't Meta's problem — it's the system.

- **RealPage / housing (9:00-13:00):** #10 → #11 → #12. Full arc (accusation, cartel label, continuation via extravagant profits). Narration connects to the Meta ritual.
- **AI / training data (13:00-17:00):** #1. The ritual in its newest form — fine hasn't even landed yet. Anthropic $1.5B settlement, OpenAI NYT suit as narration-supported data (no clip needed, industry reporting).

### ACT 3 — The Only Thing That Works (17:00 – 23:00) — The indictment

Why internal oversight fails, why whistleblowers succeed, what changes the system.

- **The failure of internal oversight (17:00-19:00):** GDPR Meta contrast — Europe changed ONE variable (proportional fines) and Meta panicked and rebuilt their pipeline in weeks. This IS the math argument the corpus otherwise can't make, grounded in a real event.
- **#13 as the hinge (19:00-20:30):** "Whistleblowers exposed more fraud than internal audit + compliance + law enforcement combined." This is the indictment of the entire apology economy.
- **Closer (20:30-23:00):** Yesenia Guitron (Wells Fargo whistleblower) as the human face. No clip required — narration over stills. Call back to Zuck #3 ("we don't deserve to serve") vs Meta #9 ("singled out, dangerous precedent") — same speaker-class, opposite valences. End on the question: which version of accountability is the real one?

---

## WHAT GETS KILLED FROM v45/v46

- **THE FORMULA chapter** (Ford Pinto, Wells Fargo fake accounts as standalone chapters) → dissolved. Their narrative role (historical canon) is absorbed by the Meta case study, which IS the 2020s Pinto.
- **THE MACHINES chapter** (Perplexity scraping, Elliana Esquivel illustrator) → compressed into Act 2's AI segment. Elliana stays as one human anecdote, not a chapter.
- **Richard Grimshaw burns, Yesenia Guitron whistleblower story** → Yesenia absorbs the human-face role in Act 3. Grimshaw cut.
- **Purdue Pharma / Sacklers** → cut entirely. No clip. Not needed for the thesis.
- **Proportional fines / Europe** → retained as Act 3 evidence that the system CAN work when changed.

**Runtime impact:** v46 was 23 min built around 5 chapters. v47 is 23 min built around 3 acts. Narration word count probably drops 15-20% (cutting Pinto + Purdue segments) which is fine — the quotes carry more weight, matching the footage-first thesis.

---

## DECISION TREE (from council)

- [x] Title promises theater, not math → **corpus sufficient**
- [x] Every quote maps to a beat → **rewrite is load-bearing, not garnish**
- [x] 3 acts instead of 5 chapters → **no canon tax, no empty-evidence sections**
- [ ] Get user approval on this spec → **if approved, 3-hour rewrite clock starts**

---

## What changes downstream

1. **narration.wav** must be regenerated from v47 (ElevenLabs Brian). Current narration.wav is v45.
2. **paper_edit_v2.json** must be rebuilt from v47 beats, not v45 beats.
3. **Title + thumbnail** — both need to be redone for "The Apology Economy." Current thumbnail work was for "Why Breaking the Law Is Profitable." Can probably reuse the style/design system but copy must change.
4. **FCPXML** auto-rebuilds from paper edit.

---

## Open questions for user before clock starts

1. Approve title *"The Apology Economy"* or pick from alternates above?
2. Approve 3-act structure or want a different cut (e.g., 2 acts, or keep Elliana's story as a bigger moment)?
3. Keep #5 (FTC "click-happy friends") in Act 1, or move to cold open as the more vivid accusation?
4. Any soundbites from the 28-quote pool (medium-relevance) you want to promote into v47 to hit closer to 15% soundbite density?

---

## If this spec doesn't land: the fallback

Outsider's path: source 3-4 more clips where someone says *"fine was $X, profit was $Y"* directly. Targets:
- CNBC / Bloomberg segment on Meta's $134B revenue the year of the $1.2B fine
- Any Senate hearing where a senator reads the math on record
- DOJ press conference on a specific fine-vs-profit ratio

Then the OG "The law prices crime" thesis IS provable. But that's another day's corpus-extension work, not today's rewrite.
