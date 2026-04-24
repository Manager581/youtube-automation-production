# Pricing Test — Does Every Quote Survive "What is being priced?"

**Test proposed by:** First Principles advisor, 2026-04-22 v47 council check
**Rule:** If 10+ of 13 quotes answer cleanly → v45 thesis ("the law prices crime") was right → pivot to pricing frame. If fewer → collapse to Contrarian's Meta-only cut.

---

| # | Quote (excerpt) | What is being priced? | Cleanly? |
|---|---|---|---|
| **1** | AI: "independent artists... not going to get paid" | **The price of stealing training data: zero up front.** Artists' work priced at $0 to the AI company, $3K/work in eventual settlements. | ✅ YES |
| **2** | Zuck: "major breach of trust, really sorry" | **The price of an apology.** PR delivered to set the market price (what will regulators demand? what will investors tolerate?). | ✅ YES |
| **3** | Zuck: "we don't deserve to serve people" | **The price of self-imposed accountability** — he names a standard he won't pay. Rhetorical price not paid = cheap. | ✅ YES |
| **4** | FTC: "Facebook betrayed the trust of its users and deceived them" | **The price of deception** — the regulator converts harm into a specific legal claim that eventually gets priced at $5B. | ✅ YES |
| **5** | FTC: "data privacy set by... click-happy friends" | **The price of consent design.** Facebook priced friction at zero by making privacy opt-OUT-via-friends-of-friends. | ✅ YES |
| **7** | Zuck via anchor: "historic fine but more important..." | **The price of the fine, literally discounted.** CEO reframes the cost as trivial relative to "structural changes." | ✅ YES |
| **8** | "Meta fined €1.2B" | **Literally a price.** A number, stamped on the record. | ✅ YES |
| **9** | Meta: "disappointed to have been singled out... flawed, unjustified, dangerous precedent" | **The price of compliance, too high.** Meta explicitly says the price has been set wrong. The defiance IS a pricing argument. | ✅ YES |
| **10** | "That's old-fashioned price fixing using new technology" | **Literal price fixing.** The word "price" is in the quote. | ✅ YES |
| **11** | AG: "We allege an effect at housing cartel" | **Coordinated pricing.** A cartel IS a pricing mechanism. | ✅ YES |
| **12** | "These firms are making such extravagant profits... insulting" | **The price gap between rent and cost.** Housing expert naming the arbitrage as unjustified. | ✅ YES |
| **13** | "Whistleblowers exposed more fraud than internal audit + compliance + law enforcement combined" | **The price of institutional oversight: worthless.** The actual market for truth-finding has been priced by outsiders, not insiders. | ✅ YES |

**#6 killed** (duplicate of #4).

---

## Result: **12 of 12 survive cleanly (100%)**

Every single quote in the corpus is about pricing — who sets the price, what gets priced, when the price is too low to deter, when it's too high to pay, who refuses to be priced (#13 whistleblowers).

The original v45 thesis — **"The law doesn't prevent corporate crime. It prices it."** — was correct.

The failure was execution: v45/v46 wrote the pricing thesis in prose but then built chapters around random historical case studies (Pinto 1977, Wells Fargo 2016, Purdue 2000s) instead of around the pricing moments the 12 available quotes actually deliver.

---

## What this means for v47

**Pivot back to the pricing thesis. Rewrite structure around the ledger.**

- **TITLE (candidates):**
  - "The Price of Breaking the Law"
  - "Why Corporate Crime Is a Line Item"
  - "The System Priced the Crime"
  - "Illegality Is a Business Expense"
- **THESIS:**
  *"Every major corporate harm — privacy, rent, training data, labor — has been converted into a line item the company can pay and keep going. The only thing that breaks the ledger is someone who refuses to be priced."*
- **STRUCTURE — by ledger, not by company:**
  - **ACT 1: How harm gets priced.** Meta as worked example (7 Meta quotes show the full pricing cycle: harm → accusation → fine → defiance). Pinto/Wells/Purdue become 30s historical flashes, not chapters.
  - **ACT 2: Who else is doing it.** RealPage (literal price fixing, #10/#11/#12). AI (pricing stolen data at $0 up front, settlement later, #1). The pattern generalizes because PRICING generalizes.
  - **ACT 3: What breaks the ledger.**
    - GDPR made the price proportional → Meta rebuilt the pipeline in weeks (Europe example, narration-supported, retain from v45)
    - #13: Whistleblowers exposed more than the entire priced oversight system → because they refuse to be priced
    - Yesenia Guitron: the human face of someone who refused to be priced (narration over stills — FINE for this ledger-of-humans segment, because the stills CAN be her photo + Wells Fargo branch + industry blacklist documents = visual documents of what she paid)

---

## Why this works where v47 spec ("Apology Economy") didn't

| Test | "Apology Economy" spec | "Price of Breaking the Law" |
|---|---|---|
| Quotes that survive the thesis test | 6 of 12 (Meta only) | **12 of 12** |
| Act 3 has on-corpus evidence | ❌ No GDPR quote | ✅ #13 + Meta/GDPR as proven by-contrast case |
| Meta-overfit | ❌ Yes (Meta has all 4 beats, RealPage/AI don't) | ✅ No (pricing is universal — Meta happens to have the most quotes) |
| Structure matches quote distribution | ❌ Inverted (9/8/6 vs 7/4/1) | ✅ Meta as worked example justifies its weight |
| Killing Pinto/Purdue/Wells Fargo | Kills them entirely | Keeps them as 30s historical flashes (not chapters) |
| Title tests (scroll-grab, 5-sec) | "Apology Economy" = abstract | "Price of Breaking the Law" = direct promise of math content |
| Connects to v45 script work already done | Breaks from it | Returns to original thesis, keeps existing narration where it discusses pricing |

---

## Next step (before any script writing)

1. **Run the 9-test topic scorer** on the pricing thesis (user's standard gate, flagged by peer review as skipped).
2. **Check `playbook/titles_thumbnails.json`** to see which of 26 tactics "Price of Breaking the Law" hits.
3. **Check `analysis/competitor_calibration/competitor_top_videos.json`** for retention signal on math-argument-titled vs theater-argument-titled videos.
4. **Only then** budget 7-8 hours (Executor's honest number, not the mythical 3) to write v47 around the pricing ledger.
