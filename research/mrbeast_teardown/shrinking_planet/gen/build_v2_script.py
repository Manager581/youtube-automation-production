"""SCRIPT_v1.md -> SCRIPT_v2.md + script_lines_v2.json (reviewer v1 LANDED fixes).
Every replacement asserts the v1 text is present exactly once, so the edit set is deterministic.
"""
import re, json, collections
OUT = "/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet"
src = open(OUT + "/SCRIPT_v1.md", encoding="utf-8").read()

EDITS = []  # (old, new)
def E(old, new): EDITS.append((old, new))

# ---------- header ----------
E("# SHRINKING PLANET — SCRIPT v1\n", "# SHRINKING PLANET — SCRIPT v2\n")
E("Source of truth: `research/mrbeast_teardown/SHRINKING_PLANET_bible_v2.html` (v2 outline). Runtime 20:00, 36 beats",
  "Source of truth: `research/mrbeast_teardown/SHRINKING_PLANET_bible_v2.html` (v2 outline). v2 = v1 + the adversarial review's landed fixes (clock ladder re-valued, offers moved to the evening BEFORE each shrink so every beat carries one planet size, prize pot stated once, five same-beat paraphrases rewritten). Runtime 20:00, 36 beats")
E("Ladder (day → planet metres, THE COUNT always matches): 1→1000 · 5→500 · 10→300 · 20→25 · 25→20 · 26→12 · 27→7 · 28→4 · 29→2 · 30→2.",
  "Ladder (day → planet metres, THE COUNT always matches): 1→1000 · 5→500 · 10→300 · 20→25 · 25→20 · 26→12 · 27→7 · 28→4 · 29→2 · 30→2. Every shrink lands at the START of a beat (B10 Day 5 sunrise, B14 Day 10, B22 Day 20 sunrise); the offers that cause them are made the evening before (B09 = Day 4, B21 = Day 19), so no beat straddles two planet sizes.")

# ---------- B09 / B10: offer on Day 4 evening, wedge at Day 5 sunrise ----------
E("## B09 [02:45-03:30] Day 5 · Offer #1\n[DAY 5]\n[PLANET 500]\n[COUNT 500]\n[MUSIC bed]\n[TEXT \"DAY 5\"]",
  "## B09 [02:45-03:30] Day 4 · Offer #1\n[DAY 4]\n[PLANET 1000]\n[COUNT 1000]\n[MUSIC bed]\n[TEXT \"DAY 4\"]")
E("ORB drops out of the black sky onto the pad. A tray drone lands two covered platters.\n\n**ORB** (on, energy: announcer): Day five. You've spoken eleven words to each other.",
  "Evening of Day 4. PIP and GRUFF trudge onto the pad, tether dragging. ORB drops out of the black sky. A tray drone lands two covered platters.\n\n**ORB** (on, energy: announcer): Day four. You've spoken eleven words to each other.")
E("**ORB** (on, energy: announcer): Under the right lid: I halve it. Five hundred metres. And I add a hundred thousand",
  "**ORB** (on, energy: announcer): Under the right lid: I halve it. Five hundred metres, starting at tomorrow's sunrise. And I add a hundred thousand")
E("**PIP** (mouth:OFF, emotion: thinking): We haven't seen each other in four days.",
  "**PIP** (mouth:OFF, emotion: thinking): We haven't seen each other in three days.")
E("## B10 [03:30-04:10] The wedge\n[DAY 5]\n[PLANET 500]\n[COUNT 500]\n[TEXT \"500 M\"]",
  "## B10 [03:30-04:10] Day 5 · The wedge\n[DAY 5]\n[PLANET 500]\n[COUNT 500]\n[TEXT \"DAY 5\"]\n[TEXT \"500 M\"]")
E("A seam of light draws around a third of the world. The rock cracks. A whole wedge shears off and drifts away, tumbling — their old campsite going with it past their feet.",
  "Day 5 sunrise. A seam of light draws around a third of the world. The rock cracks. A whole wedge shears off and drifts away, tumbling — their old campsite going with it past their feet. Fragments tumble past the lens.")

# ---------- B14: shrink FIRST, then ORB explains (all rows post-shrink) ----------
E("ORB descends to the cave mouth.\n\n**ORB** (on, energy: bright): Day ten. Today's shrink is on the house. No deal, no money, no choice, no lid. I'm taking two hundred metres because I feel like it and because you've been boring.\n\nA smaller wedge lifts off the top of the world and drifts away. 300 metres.\n\n**GRUFF** (on, emotion: flat): You can just do that?",
  "Day ten opens on the sky: a smaller wedge lifts off the top of the world and drifts away before anyone has been asked anything. 300 metres. ORB descends to the cave mouth behind it.\n\n**ORB** (on, energy: bright): Day ten. That one was on the house. No deal, no money, no choice, no lid. I took two hundred metres because I felt like it and because you've been boring.\n\n**GRUFF** (on, emotion: flat): You can just do that?")

# ---------- B12: stranger line (same-beat paraphrase) ----------
E("**PIP** (mouth:ON, emotion: angry): I'd rather be chained to a stranger. A stranger would at least talk to me. A stranger would ask what my name is.",
  "**PIP** (mouth:ON, emotion: angry): Tether me to anyone else. Anyone. Pick a name off the street. Whoever it is would at least ask me mine.")

# ---------- B21 / B22: five platters on Day 19 night, tear at Day 20 sunrise ----------
E("## B21 [10:55-11:30] Day 20 · five platters\n[DAY 20]\n[PLANET 25]\n[COUNT 25]\n[MUSIC bed]\n[TEXT \"DAY 20\"]\n[TEXT \"OFFER #3\"]\n[SFX game-show sting per lid]\n",
  "## B21 [10:55-11:43] Day 19 · five platters\n[DAY 19]\n[PLANET 300]\n[COUNT 300]\n[MUSIC bed]\n[TEXT \"DAY 19\"]\n[TEXT \"OFFER #3\"]\n[SFX game-show sting per lid]\n[MUSIC out]\n[SFX total silence after \"It was free\"]\n")
E("Five tray drones in a row. Five silver lids. ORB drifts along them right to left.\n\n**ORB** (on, energy: announcer): Day twenty. Crate day. Five platters. Every one of them opens the crate; every one of them costs something. You pick one, the crate opens, the price is paid. Careful — the best deal might be the one you skip.",
  "Night of Day 19. Five tray drones in a row on the pad. Five silver lids. ORB drifts along them right to left.\n\n**ORB** (on, energy: announcer): Day nineteen. The crate opens tomorrow, and tonight you choose how. Five platters. Every one of them opens the crate; every one of them costs something. You pick one, the crate opens at sunrise, the price is paid at sunrise. Careful — one of these lids is a trap and one of them is a gift, and they look the same from up here.")
E("**ORB** (on, energy: announcer): Shrink the planet. Three hundred metres to twenty-five. A house. One house, in space, for ten days.",
  "**ORB** (on, energy: announcer): Shrink the planet. Three hundred metres to twenty-five. A house. One house, in space, for the last ten days.")
E("**ORB** (on, energy: announcer): Lid three. That's the one. The crate opens; the planet pays.\n\n## B22 [11:30-12:00] Platter four\n[DAY 20]\n[PLANET 25]\n[COUNT 25]\n[MUSIC out]\n[SFX total silence after \"It was free\"]\n[SFX wedge rumble, dust storm]\n[TEXT \"25 M\"]\n\nORB hovers to the fourth platter.",
  "**ORB** (on, energy: announcer): Lid three. That's the one. At sunrise the crate opens and the planet pays.\n\nORB hovers to the fourth platter.")
E("**PIP** (mouth:OFF, emotion: hollow): You said the best deal might be the one we skip.\n\n**ORB** (on, energy: quiet): I did. I say it every time. Nobody has ever lifted lid four first.",
  "**PIP** (mouth:OFF, emotion: hollow): You said one of them was a gift.\n\n**ORB** (on, energy: quiet): I did. I say it every time. Nobody has ever lifted lid four first.")
E("**ORB** (on, energy: quiet): You had plenty of rock. Now you have a house.\n\nThen the sky tears: the whole far side of the planet rips away above them in a storm of dust and pebbles. What's left settles into a boulder the size of a house. THE COUNT rotates to a fresh face: 25 M.\n\n**ORB** (vo, energy: dry): Twenty-five metres.",
  "**ORB** (on, energy: quiet): You had plenty of rock. At sunrise you'll have a house. Sleep on it. It's already done.\n\n## B22 [11:43-12:00] Day 20 · The tear\n[DAY 20]\n[PLANET 25]\n[COUNT 25]\n[MUSIC hit]\n[TEXT \"DAY 20\"]\n[SFX wedge rumble, dust storm]\n[TEXT \"25 M\"]\n\nDay 20 sunrise. The sky tears: the whole far side of the planet rips away above them in a storm of dust and pebbles. The two of them duck under it on the flat top. What's left settles into a boulder the size of a house. THE COUNT rotates to a fresh face: 25 M.\n\n**ORB** (vo, energy: dry): Day twenty. The bill comes at sunrise. Twenty-five metres.")

# ---------- B24: 'It can't get smaller' / 'It can' (same-beat paraphrase) ----------
E("[SFX stinger on \"It can\"]", "[SFX stinger on \"twenty-three metres\"]")
E("**PIP** (mouth:ON, emotion: exasperated): It can't get smaller than this.\n\n**ORB** (on, energy: bright): It can.",
  "**PIP** (mouth:ON, emotion: exasperated): There's no rock left to lose.\n\n**ORB** (on, energy: bright): There's twenty-three metres of it.")

# ---------- B25: 'changing the rules of this entire video' + prize pot ----------
E("**ORB** (on, energy: flat): Day twenty-five. I'm changing the rules of this entire video. Everything up to now was shared.",
  "**ORB** (on, energy: flat): Day twenty-five. New rules. Everything up to now was shared.")
E("Whoever turns this key goes home now — with the whole prize, both halves, everything the crate was worth and everything I added. The other one gets nothing. No ticket. No half.",
  "Whoever turns this key goes home now — with the whole prize: both tickets, and the whole hundred thousand I put on the crate on Day 4. The other one gets nothing. No ticket. No fifty.")
E("Then Day 30 comes, and you split it, and you both go home like the crate promised.",
  "Then Day 30 comes, the hundred splits down the middle, and you both go home like the crate promised.")

# ---------- B29: 'Good question' exchange (same-beat paraphrase) ----------
E("**GRUFF** (on, emotion: evasive): …Good question.\n\n**ORB** (on, energy: light): It was a yes-or-no question.\n\n**GRUFF** (on, emotion: evasive): It was a good question. That's my answer. Write it down.\n\n**ORB** (vo, energy: dry): I wrote it down. I write everything down. She doesn't know he said it, and he doesn't know she thinks he'd be right to.",
  "**GRUFF** (on, emotion: evasive): …Is that a rule or a question?\n\n**ORB** (on, energy: light): It was a yes-or-no question.\n\n**GRUFF** (on, emotion: evasive): Then put me down as a maybe. Write that down.\n\n**ORB** (vo, energy: dry): I wrote it down. I write everything down. She doesn't know he said maybe, and he doesn't know she thinks he'd be right to.")

# ---------- B33: clock values + prize pot ----------
E("[TEXT \"12:43:00\"]\n[SFX clock tick only]", "[TEXT \"11:07:00\"]\n[SFX clock tick only]")
E("The clock glows: 12:43:00.", "The clock glows: 11:07:00.")
E("**GRUFF** (on, emotion: low): The whole prize would change my life more than half of it. That's just true. Half is a new van. Whole is a house with a room for a drum kit and a door that shuts.",
  "**GRUFF** (on, emotion: low): The whole prize would change my life more than half of it. That's just true. Fifty is a new van. A hundred is a room with a drum kit in it and a door that shuts.")
E("**ORB** (vo, energy: quiet): Twelve hours forty-three minutes. The key is eighty centimetres from his hand.",
  "**ORB** (vo, energy: quiet): Eleven hours and seven minutes. The key is eighty centimetres from his hand.")

# ---------- B34: clock ladder (all values re-valued), PIP's duration line, prize pot ----------
E("[FLASHFWD three seconds on the clock]\n[TEXT \"00:00:03\"]\n[TEXT \"10:00\"]\n[TEXT \"01:12\"]\n[TEXT \"00:16\"]\n[TIMER 10:00 → 1:12 → 0:16 → 3-2-1]",
  "[FLASHFWD the clock at two seconds]\n[TEXT \"00:00:02\"]\n[TEXT \"08:00\"]\n[TEXT \"00:58\"]\n[TEXT \"00:09\"]\n[TIMER 8:00 → 0:58 → 0:09 → 3-2-1]")
E("Flash-forward: three seconds on the clock. Back. Ten minutes left. The truth beam replays, red flicker.\n\n**ORB** (on, energy: announcer): Ten minutes. Ten minutes, and then the ship, and then the split, and then none of this matters. Unless somebody turns a key.",
  "Flash-forward: the clock at two seconds. Back. Eight minutes left. The truth beam replays, red flicker.\n\n**ORB** (on, energy: announcer): Eight minutes. Eight minutes, and then the ship, and then the split, and then none of this matters. Unless somebody turns a key.")
E("**ORB** (vo, energy: announcer): A minute and twelve seconds. Last chance to launch. After this the pod locks and the key is a souvenir.",
  "**ORB** (vo, energy: announcer): Fifty-eight seconds. Last call for the pod. After this it locks and the key is a souvenir.")
E("**GRUFF** (on, emotion: strained): Half is a van.\n\n**PIP** (mouth:OFF, emotion: urgent): Half is a van and a drummer. Whole is a house and nobody in it.\n\n**ORB** (vo, energy: announcer): Sixteen seconds.",
  "**GRUFF** (on, emotion: strained): Fifty is a van.\n\n**PIP** (mouth:OFF, emotion: urgent): Fifty is a van and a drummer. A hundred is a room and nobody in it.\n\n**ORB** (vo, energy: announcer): Nine seconds.")
E("**PIP** (mouth:OFF, emotion: quiet): You kept your hand on it for a minute and twelve seconds.\n\n**GRUFF** (on, emotion: quiet): I was counting. Drummer.",
  "**PIP** (mouth:OFF, emotion: quiet): Your hand was on that lever a long time.\n\n**GRUFF** (on, emotion: quiet): Forty-nine seconds. I was counting. Drummer.")

# ---------- B35: pot stated once ----------
E("**ORB** (on, energy: warm): Half each. And both tickets. And a hundred thousand on top, because somebody halved a planet on Day 5 and I keep my word even when nobody remembers I gave it.",
  "**ORB** (on, energy: warm): Fifty thousand each — that's the hundred I put on the crate on Day 4, split down the middle — and both tickets. Somebody said \"halve it\" that night, and I keep my word even when nobody remembers I gave it.")

for old, new in EDITS:
    n = src.count(old)
    assert n == 1, (n, old[:80])
    src = src.replace(old, new)
open(OUT + "/SCRIPT_v2.md", "w", encoding="utf-8").write(src)

# ---------- script_lines_v2.json (identical builder to gen/finish.py) ----------
lines_src = src.split("\n")
def sec(t): m, s = t.split(":"); return int(m) * 60 + int(s)
def tc(x): return f"{x//60:02d}:{x%60:02d}"
hdr = re.compile(r"^## (B\d{2}) \[(\d\d:\d\d)-(\d\d:\d\d)\] (.+)$")
tag = re.compile(r"^\[(DAY|PLANET|COUNT|LOOP|TEXT|MUSIC|SFX|FLASHFWD|TIMER)\b(.*)\]$")
dlg = re.compile(r"^\*\*(PIP|GRUFF|ORB)\*\* \(([^)]*)\): (.+)$")
beats = []; cur = None
for ln in lines_src:
    m = hdr.match(ln)
    if m:
        cur = {"beat": m.group(1), "t_in": m.group(2), "t_out": m.group(3), "title": m.group(4), "tags": [], "lines": []}; beats.append(cur); continue
    if cur is None: continue
    m = tag.match(ln.strip())
    if m: cur["tags"].append((m.group(1), m.group(2).strip())); continue
    m = dlg.match(ln.strip())
    if m:
        spk, attrs, text = m.groups(); mouth = None
        if spk == "PIP":
            mm = re.search(r"mouth:(ON|OFF)", attrs); assert mm, text; mouth = mm.group(1)
        cur["lines"].append({"speaker": spk, "mouth": mouth, "text": text})
out = []
for b in beats:
    n = len(b["lines"]); T0, T1 = sec(b["t_in"]), sec(b["t_out"])
    for k, l in enumerate(b["lines"]):
        t = T0 + int((T1 - T0) * k / max(n, 1))
        out.append({"beat": b["beat"], "t": tc(t), "speaker": l["speaker"], "mouth": l["mouth"], "words": len(l["text"].split()), "text": l["text"]})
json.dump(out, open(OUT + "/script_lines_v2.json", "w"), indent=1, ensure_ascii=False)
# contiguity check
for a, b in zip(beats, beats[1:]): assert a["t_out"] == b["t_in"], (a["beat"], a["t_out"], b["t_in"])
assert beats[0]["t_in"] == "00:00" and beats[-1]["t_out"] == "20:00" and len(beats) == 36
wc = sum(len(re.findall(r"[A-Za-z0-9']+", l["text"])) for l in out)
print("beats", len(beats), "lines", len(out), "words(regex)", wc, "PIP ON", sum(1 for l in out if l["mouth"] == "ON"))
