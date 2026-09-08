#!/usr/bin/env python3
"""title_gate.py — S2 title gate: deterministic checks derived from the measured winner titles (top10.json).
Rules (each cites the corpus, re-derived 2026-08-31 after the first version failed 5/10 winners): length 28-65
(winners 32-52); opens with an imperative verb / 'I ' / '$' / a number / 'Ages' / 'Last To' / 'Trapped' (10/10);
a NUMBER / $ / 'Last To' / 'vs' is a WARN only (9/10 — "Trapped On An Island Until I Build A Boat" has none);
no banned brand/likeness tokens; <=1 comma; no clickbait fillers; Title Case dominant (short function words ignored).
Usage: title_gate.py "Title" ["Title 2" ...]   exit 1 if any title fails
"""
import re, sys
BANNED = re.compile(r"\b(mrbeast|mr\.? beast|beast|feastables|lunchly|jimmy)\b", re.I)
FILLER = re.compile(r"you won'?t believe|insane|gone wrong|not clickbait|\(.*\)", re.I)
OPEN = re.compile(r"^(Survive|Last To|I |\$|\d|100 |Ages |Trapped|Escape|Build|Win|Find|Hide|Spend|Eat|Live|Sleep|Race)", re.I)
NUM = re.compile(r"(\$\s?[\d,]+|\b\d+\b|\bLast To\b|\bvs\.?\b)", re.I)
LEN_MIN, LEN_MAX = 28, 65  # measured on top10.json: shortest winner 32 chars ("I Saved 1,000 Animals From Dying"), longest 52
def check(t):
    f, w = [], []
    if not (LEN_MIN <= len(t) <= LEN_MAX): f.append(f"length {len(t)} outside {LEN_MIN}-{LEN_MAX} (winners span that band)")
    if not OPEN.search(t): f.append("does not open with an imperative/'I'/number/'Last To' (10/10 winners do)")
    if not NUM.search(t): w.append("no number / $ / 'Last To' / 'vs' (9 of 10 winners have one)")
    if BANNED.search(t): f.append("banned brand/likeness token")
    if FILLER.search(t): f.append("clickbait filler")
    if re.sub(r"(?<=\d),(?=\d)", "", t).count(",") > 1: f.append("more than one clause comma (thousands separators ignored)")
    words = [x for x in re.findall(r"[A-Za-z][A-Za-z']*", t) if len(x) > 3]
    if words and sum(x[0].isupper() for x in words) / len(words) < 0.8: f.append("not Title Case")
    return f, w
def main():
    bad = 0
    for t in sys.argv[1:]:
        f, w = check(t); print(f"{'PASS' if not f else 'FAIL'} | {t}"); [print("      -", x) for x in f]; [print("      ~ warn:", x) for x in w]; bad += bool(f)
    print("title_gate: " + ("PASS" if not bad else f"FAIL ({bad})")); sys.exit(1 if bad else 0)
if __name__ == "__main__": main()
