#!/usr/bin/env python3
"""title_gate.py — S2 title gate: deterministic checks derived from the measured winner titles (top10.json).
Rules (each cites the corpus): length 30-65 chars (winners 28-56); starts with an imperative verb / 'I ' / '$' / a number
/ 'Last To' (10/10); contains a NUMBER or a $ figure or 'Last To'/'vs' (10/10); no banned brand/likeness tokens;
no more than one comma; no clickbait fillers ('you won't believe', 'insane', 'gone wrong'); Title Case dominant.
Usage: title_gate.py "Title" ["Title 2" ...]   exit 1 if any title fails
"""
import re, sys
BANNED = re.compile(r"\b(mrbeast|mr\.? beast|beast|feastables|lunchly|jimmy)\b", re.I)
FILLER = re.compile(r"you won'?t believe|insane|gone wrong|not clickbait|\(.*\)", re.I)
OPEN = re.compile(r"^(Survive|Last To|I |\$|\d|100 |Ages |Trapped|Escape|Build|Win|Find|Hide|Spend|Eat|Live|Sleep|Race)", re.I)
NUM = re.compile(r"(\$\s?[\d,]+|\b\d+\b|\bLast To\b|\bvs\.?\b)", re.I)
def check(t):
    f = []
    if not (30 <= len(t) <= 65): f.append(f"length {len(t)} outside 30-65")
    if not OPEN.search(t): f.append("does not open with an imperative/'I'/number/'Last To' (10/10 winners do)")
    if not NUM.search(t): f.append("no number / $ / 'Last To' / 'vs' (10/10 winners have one)")
    if BANNED.search(t): f.append("banned brand/likeness token")
    if FILLER.search(t): f.append("clickbait filler")
    if t.count(",") > 1: f.append("more than one comma")
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z']*", t) if len(w) > 3]
    if words and sum(w[0].isupper() for w in words) / len(words) < 0.8: f.append("not Title Case")
    return f
def main():
    bad = 0
    for t in sys.argv[1:]:
        f = check(t); print(f"{'PASS' if not f else 'FAIL'} | {t}"); [print("      -", x) for x in f]; bad += bool(f)
    print("title_gate: " + ("PASS" if not bad else f"FAIL ({bad})")); sys.exit(1 if bad else 0)
if __name__ == "__main__": main()
