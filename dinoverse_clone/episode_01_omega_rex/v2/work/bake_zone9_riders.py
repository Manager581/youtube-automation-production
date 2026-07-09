#!/usr/bin/env python3
"""Bake Zone 9 Hybrid failure-specific riders into STORYBOARD.tsv col 10 (Grok i2v prompt).
Same technique as bake_zone8_riders.py: read with csv (handles existing quoting), edit only the
target rows by Shot id, re-serialize edited rows with csv.writer (correct TSV quote-escaping),
leave every other line byte-for-byte. Riders grounded in the actual v2/stills/Sxx.png content +
the 5-lens adversarial rider review (creature distinctness, glass/barrier + Zone-8 step-back roar
rule, signage-stability, mouth/head-integrity, count-constancy), incl. the S77 fog-contradiction
fix and the S74 keep-pen-empty fix."""
import csv, io, sys

TSV = "/Users/jefflawrence/Documents/youtube-automation-production/dinoverse_clone/episode_01_omega_rex/STORYBOARD.tsv"
SHOT_COL = 1    # col 2 "Shot"
PROMPT_COL = 9  # col 10 "Grok video prompt (i2v)"

NEW = {
"S69": '''Cam: candid, then whip to GF. Move: exactly three teenagers - one in a red hoodie with a phone raised, one in a dark shirt and camo shorts, one with a yellow backpack - file one by one through the propped-open red staff door; the door eases shut behind them; the group holds a CONSTANT count of three from first frame to last - none pops in, vanishes, duplicates, or merges into the doorway, and the yellow backpack stays on the same teen the whole clip. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: door hinge, quiet crowd. Dialogue: GF: "Luke - they just went in." LUKE: "...we have to tell someone.". Signage: the red door stencil reads exactly "STAFF ONLY - HYBRID DANGER" and stays pixel-identical letter-for-letter as the door eases shut; every sign in the first frame (the door plus the green HYBRID ZONE / DINO ZOO signs) is the only signage and stays exactly as-is - no new signs, letters, logos, or captions appear or sharpen, and background signs stay soft-focus. Style: non-cinematic, grounded, real-world physics (the door and walls are solid - people only pass through the open doorway, never clip through the closed door or a wall; Luke and GF stay on the public side), exact-env-match, 16:9.''',

"S70": '''Cam: handheld. Move: exactly two pale bone-white Indominus juveniles - each with red eyes, quill-like osteoderms down the neck and back, and long four-clawed arms - pace in mirror inside their glass-fronted pen; one khaki ranger stands on the viewing side, turning unsmiling toward camera; the count stays exactly two juveniles and one ranger first-to-last frame - the juveniles never merge into one or split into three, the ranger never duplicates, nothing vanishes. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: claws on concrete, hum. Dialogue: RANGER (tense): "You two shouldn't be here either. This section's not open.". Signage: any interior or background signs and placards stay soft-focus and keep their exact lettering - no new signs, warning text, or captions appear or sharpen. Style: non-cinematic, grounded, real-world physics (the juveniles are pale bone-white Indominus - never charcoal-black, never with glowing orange seams or six-clawed hands; the reinforced viewing glass is solid and absolute - the juveniles stay entirely behind it on their side with a clear air gap, the ranger stays on the viewing side, nothing crosses through the glass; each juvenile's head stays fully formed and attached every frame), exact-env-match, 16:9.''',

"S71": '''Cam: locked. Move: the pale bone-white Indominus (red eyes, quill osteoderms, long four-clawed arms) lunges VERTICALLY upward for the single slab of meat on the crane hook suspended above its own enclosure floor - not forward toward the camera - snaps it, and drops back down on its own side of the moat; on the snap its skull and jaws keep their exact shape (never collapsing to a stump or morphing), the mouth takes only that one slab and then closes EMPTY with nothing else hanging from, sprayed, or ejected out of it. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: crane winch, snap, thud. Dialogue: LUKE: "That's the Indominus. Part T-Rex, part... a lot of things.". Signage: any deck placards or DINO ZOO signs keep their exact lettering; no new signs or captions appear or sharpen; background signage stays soft-focus. Style: non-cinematic, grounded, real-world physics (this is the pale bone-white Indominus, never charcoal-black or orange-seamed; it stays fully behind the moat on its own side and never clears, lands on, or crosses the guest-side moat edge, holding a clear air gap to the viewing glass every frame; the crane and meat hang over the enclosure side only; no water jet, stream, spray, or object ever leaves its mouth), exact-env-match, 16:9.''',

"S72": '''Cam: slow pan along the scars. Move: a slow, steady pan along the deep concrete claw gouges; in the mid-ground pen behind the reinforced barrier a faint pale Indominus stands and shifts slightly but stays entirely behind the wall and never emerges through it; the gouges themselves stay fixed and identical the whole clip, never redrawing, deepening, or multiplying. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: hum, distant scrape. Dialogue: GF: "...did it do that? To the wall?". Signage: every sign or placard in the first frame (the HYBRID ZONE / DINO ZOO sign) is the only signage - it stays pixel-stable and correctly spelled, and no background sign sharpens into new or invented lettering. Style: non-cinematic, grounded, real-world physics (the wall is solid and static - the claw scars never change shape and nothing passes through the wall; the pale creature stays behind its barrier, never the charcoal D-Rex), exact-env-match, 16:9.''',

"S73": '''Cam: locked. Move: the pale bone-white Indominus (long four-clawed arms, quill osteoderms) stays standing in place behind the glass while its skin shifts color to match the foliage - its outline dissolving into the background until, by the final frame, it has all but vanished, a faint eye-glint the last thing to fade, timed to land on GF's "-and then it's not."; it does not move through the plants or the glass, only its coloration blends. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: hum, a single leaf-rustle. Dialogue: LUKE: "It can camouflage. One second it's there-" GF: "-and then it's not.". Style: non-cinematic, grounded, real-world physics (this is the pale bone-white Indominus, never charcoal-black or orange-seamed; it camouflages by changing skin color while staying in place behind its glass - it never phases through the foliage or the barrier, and its head stays fully formed the whole clip), exact-env-match, 16:9.''',

"S74": '''Cam: high locked, slight sway. Move: the deep concrete enclosure stays EMPTY - no creature is visible and none rises or enters the frame (the D-Rex reveal is the NEXT shot); the only motion is the small idle orange alarm beacon and a slight wind-sway of the camera; no crowd churns. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: wind, faint hum. Dialogue: LUKE: "And this - the deepest one - is the D-Rex.". Signage: every zone sign, placard, and hazard marking on the overlook (the HYBRID ZONE / INDOMINUS REX JUVENILES sign) keeps its exact lettering unchanged the whole clip; no new signs, numbers, letters, or captions appear or sharpen into view; all background signage stays soft-focus. Style: non-cinematic, grounded, real-world physics (the overlook glass balustrade and handrail are solid; the deep pen holds no animal this shot; all signage stays pixel-stable), exact-env-match, 16:9.''',

"S75": '''Cam: slow reveal. Move: the D-Rex emerges from the shadow of the deepest enclosure one limb at a time and its oversized asymmetric head swings up last - clearly the charcoal-black, armored, ridged-backed D-Rex (faint dark orange seams as in the source image, six-clawed hands), visibly LARGER and wrong-proportioned, unmistakably NOT the pale bone-white Indominus; exactly one creature is in frame, no second animal appears. As the head swings up the skull and oversized jaws keep their intended shape and stay intact - never melting, doubling, or collapsing to a stump - the mouth stays closed on the deep breath with nothing ejected or sprayed from it. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: dragging weight, deep breath. Dialogue: GF (whisper): "...that's not a dinosaur. That's a monster." LUKE: "People think he's a monster. But is he?". Style: non-cinematic, grounded, real-world physics (the D-Rex is charcoal-black and six-clawed - never bone-white, never quilled like the Indominus; it stays entirely within the deepest enclosure behind its barrier as it reveals, its body solid and intact), exact-env-match, 16:9.''',

"S76": '''Cam: wide from the overlook. Move: exactly three teenagers - one in a red hoodie with a phone raised, one in a light shirt, one with a yellow backpack - stand on the walled visitor ramp, oblivious; far across the pit the charcoal-black D-Rex only TURNS its head their way from a clear distance back on its own side - it does NOT step forward, lunge, or charge; the teens hold a constant count of three (none vanish, duplicate, or merge at that distance) and the yellow backpack stays on its teen; exactly one D-Rex, no second creature. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: wind, faint phone chatter. Dialogue: LUKE (shouting): "HEY - get away from the-". Signage: the overlook's HYBRID ZONE sign and hazard placards keep their exact lettering the whole clip; no new signage or captions appear or sharpen; background signs stay soft-focus. Style: non-cinematic, grounded, real-world physics (the teens are on the public visitor side, past the walkway rail, never inside the enclosure; the D-Rex stays deep on its own side of the enclosure barrier with a large visible air gap and only turns its head - it never touches, fills, or crosses the barrier; the D-Rex is charcoal-black, never the pale Indominus, and its head keeps its exact shape), exact-env-match, 16:9.''',

"S77": '''Cam: locked close. Move: the charcoal-black D-Rex's armored snout stays fully BEHIND the reinforced glass on the enclosure side with a small hand's-width air gap to the pane; its huge slow breath condenses as soft fog that spreads and clears on the glass surface in slow pulses; a single teen (reflected in the pane, phone raised) on the visitor side stays motionless. Env: real zoo doc, flat daylight, no cinematic atmospheric haze - but the breath-condensation fog ON THE GLASS PANE is intended and must appear. Sound: huge slow breathing. Dialogue: GF: "It sees them.". Style: non-cinematic, grounded, real-world physics (the reinforced viewing glass with steel mullions is solid and stays intact and in front of the D-Rex head EVERY frame - the snout only fogs the glass from behind it and never touches, presses through, cracks, fills, or crosses the pane or mullion; the breath shows ONLY as soft fog on the glass, never a water jet, stream, spray, or object from the mouth, and the jaw stays closed while breathing; the teen stays on the visitor side and is present every frame; the D-Rex is charcoal-black, never the pale Indominus, and its head keeps its exact shape), exact-env-match, 16:9.''',

"S78": '''Cam: handheld shake. Move: the charcoal-black, armored, ridged-backed D-Rex (oversized asymmetric jaws, six-clawed hands) wrenches free of its metal restraint cables one cable at a time; sparks shower as each anchor tears loose and the last anchor gives; it roars; no people are in frame. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: cable SNAP, sparks, roar. Dialogue: LUKE: "RUN. RUN-". Style: non-cinematic, grounded, real-world physics (this is the charcoal-black six-clawed D-Rex, never the pale bone-white Indominus, and it is the only creature in frame; what breaks are the RESTRAINT cables and their anchors ONLY - NOT the public viewing glass or enclosure wall, which stay intact - and the D-Rex stays within its enclosure footprint this shot, its wrench directed against the anchor points within the pen, not toward camera or public; through the roar and wrench its skull, jaws, and body keep their exact shape, never collapsing to a stump, and nothing - no water jet, stream, spray, or object - leaves its mouth except sound; no invented signage sharpens into frame), exact-env-match, 16:9.''',
}

with open(TSV, newline="") as f:
    lines = f.readlines()

def reserialize(fields):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", quotechar='"', quoting=csv.QUOTE_MINIMAL,
                   lineterminator="")
    w.writerow(fields)
    return buf.getvalue()

changed = {}
out = []
for line in lines:
    stripped = line.rstrip("\n")
    if not stripped:
        out.append(line); continue
    fields = next(csv.reader([stripped], delimiter="\t", quotechar='"'))
    shot = fields[SHOT_COL] if len(fields) > SHOT_COL else ""
    if shot in NEW and shot not in changed:
        old = fields[PROMPT_COL]
        fields[PROMPT_COL] = NEW[shot]
        newline_txt = reserialize(fields) + ("\n" if line.endswith("\n") else "")
        out.append(newline_txt)
        changed[shot] = (len(old), len(NEW[shot]))
    else:
        out.append(line)

missing = [s for s in NEW if s not in changed]
if missing:
    print("ERROR: shots not found:", missing); sys.exit(1)

with open(TSV, "w", newline="") as f:
    f.writelines(out)

for s in ["S69","S70","S71","S72","S73","S74","S75","S76","S77","S78"]:
    print(f"{s}: rider baked ({changed[s][0]} -> {changed[s][1]} chars)")
print("Done. 10 rows updated; all others untouched.")
