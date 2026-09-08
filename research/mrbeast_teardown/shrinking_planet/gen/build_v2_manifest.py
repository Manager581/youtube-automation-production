"""shot_manifest_v1.json -> shot_manifest_v2.json + SEED_PROMPTS_v2.md (reviewer v1 LANDED fixes).

v2 timing model (every row):  slot = t_out - t_in  <=  duration_s.
  unique  : duration_s = generated clip length (<= 10 s hero cap). slot + sum(punch slots) <= duration_s.
  punch   : reuse "insert" + punch=true + clip_window [a,b] — a post re-crop of a LATER window of the SAME take,
            allowed adjacent to its source (the bible's own hook technique); adds cuts, not footage.
  insert  : replay of an earlier clip, never adjacent to its source or a sibling; slot <= source duration_s.
  post    : FFmpeg-built from stills (archive stack / archive flash); no generation; composite_seed_id null.
Ladder is keyed by the day the planet HAS that size at sunrise; every shrink lands at the START of a beat.
"""
import json, re, collections, copy, sys
sys.path.insert(0, "/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet/gen")
from masters import ART_STYLE, ANCHORS, NEG, PLANET_FOR
OUT = "/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet"
v1 = json.load(open(OUT + "/shot_manifest_v1.json"))
V1 = {s["id"]: s for s in v1["shots"]}
def sec(t): m, s = t.split(":"); return int(m) * 60 + int(s)
def tc(x): return f"{x//60:02d}:{x%60:02d}"

# ---------------- beats (v2: B21/B22 boundary moved to the tear at 11:43) ----------------
BEATS = [("B01","00:00","00:12",1,"HOOK"),("B02","00:12","00:17",1,"HOOK"),("B03","00:17","00:21",1,"HOOK"),("B04","00:21","00:30",1,"HOOK"),("B05","00:30","00:45",1,"HOOK"),
("B06","00:45","01:30",1,"A1"),("B07","01:30","02:00",1,"A1"),("B08","02:00","02:45",2,"A1"),("B09","02:45","03:30",4,"A1"),("B10","03:30","04:10",5,"A1"),("B11","04:10","04:50",6,"A1"),("B12","04:50","05:40",6,"A1"),("B13","05:40","06:20",6,"A1"),
("B14","06:20","07:05",10,"A2"),("B15","07:05","07:40",12,"A2"),("B16","07:40","08:15",12,"A2"),("B17","08:15","08:45",14,"A2"),("B18","08:45","09:45",15,"A2"),("B19","09:45","10:25",16,"A2"),("B20","10:25","10:55",16,"A2"),
("B21","10:55","11:43",19,"A3"),("B22","11:43","12:00",20,"A3"),("B23","12:00","12:25",20,"A3"),("B24","12:25","12:45",20,"A3"),("B25","12:45","13:30",25,"A3"),
("B26","13:30","14:20",25,"A4"),("B27","14:20","15:10",25,"A4"),("B28","15:10","15:40",25,"A4"),("B29","15:40","16:05",26,"A4"),("B30","16:05","16:25",27,"A4"),("B31","16:25","17:10",28,"A4"),("B32","17:10","17:55",29,"A4"),("B33","17:55","18:35",29,"A4"),
("B34","18:35","19:30",30,"A5"),("B35","19:30","19:55",30,"A5"),("B36","19:55","20:00",30,"A5")]
BEAT = {b[0]: b for b in BEATS}
LADDER = {"1":1000,"2":1000,"4":1000,"5":500,"6":500,"10":300,"12":300,"14":300,"15":300,"16":300,"19":300,"20":25,"25":20,"26":12,"27":7,"28":4,"29":2,"30":2}
def ladder_for(day):
    best = None
    for k in sorted(int(x) for x in LADDER):
        if k <= day: best = k
    return LADDER[str(best)]
SHRINK_EVENTS = [
 {"beat":"B10","t":"03:30","day":5,"from_m":1000,"to_m":500,"hero_v1":"S044","cause":"Offer #1 accepted the evening before (B09, Day 4)"},
 {"beat":"B14","t":"06:20","day":10,"from_m":500,"to_m":300,"hero_v1":"S068","cause":"free shrink (first row of the beat, ORB explains after)"},
 {"beat":"B22","t":"11:43","day":20,"from_m":300,"to_m":25,"hero_v1":"S115","cause":"Lid three chosen the night before (B21, Day 19)"},
 {"beat":"B25","t":"12:45","day":25,"from_m":25,"to_m":20,"hero_v1":None,"cause":"daily shrink from Day 25, off-screen between beats"},
 {"beat":"B29","t":"15:40","day":26,"from_m":20,"to_m":12,"hero_v1":None,"cause":"daily shrink, off-screen"},
 {"beat":"B30","t":"16:05","day":27,"from_m":12,"to_m":7,"hero_v1":None,"cause":"daily shrink, off-screen"},
 {"beat":"B31","t":"16:25","day":28,"from_m":7,"to_m":4,"hero_v1":None,"cause":"daily shrink, off-screen"},
 {"beat":"B32","t":"17:10","day":29,"from_m":4,"to_m":2,"hero_v1":None,"cause":"daily shrink, off-screen; 2 m holds through Day 30"}]

# ---------------- per-row edits on v1 rows ----------------
CHAR_FIX = {  # characters -> (characters, partial)
 "S034": ([], []), "S035": ([], []), "S050": ([], []), "S053": ([], []), "S071": ([], []),
 "S064": (["PIP","GRUFF"], ["PIP","GRUFF"]), "S193": (["PIP","GRUFF"], ["PIP","GRUFF"]),
 "S102": (["GRUFF"], ["GRUFF"]), "S171": (["GRUFF"], ["GRUFF"]),
 "S163": (["GRUFF"], ["GRUFF"]), "S179": (["GRUFF"], ["GRUFF"]), "S185": (["GRUFF"], ["GRUFF"]), "S187": (["GRUFF"], ["GRUFF"]),
 "S168": (["PIP","GRUFF"], ["GRUFF"]),
}
LOOP_SET = {  # v1 id -> loops (full replacement)
 "S003": ["crate:OPEN"], "S027": ["crate:FEED"], "S042": ["crate:FEED"], "S073": ["crate:FEED"], "S095": ["crate:FEED"], "S117": ["crate:PAY"],
 "S097": ["riff:OPEN"], "S123": ["riff:FEED"], "S160": ["riff:FEED"], "S196": ["riff:PAY"],
 "S102": ["goggle:OPEN"], "S141": ["goggle:FEED"], "S165": ["goggle:FEED"], "S169": ["goggle:PAY"],
 "S128": ["launch:OPEN"], "S146": ["launch:FEED"], "S154": ["launch:FEED"], "S163": ["launch:FEED"], "S178": ["launch:FEED"], "S187": ["launch:PAY"],
 "S134": ["trust:OPEN"], "S164": ["trust:FEED"], "S181": ["trust:PAY"], "S145": [],
}
SEED_SWAP = {"S040": ("M_PLANET_500", "M_PLANET_1000"), "S106": ("M_PLANET_25", "M_PLANET_300")}
SEED_DROP = {"S041": "M_COUNT_3q"}
BEAT_MOVE = {"S113": "B21", "S114": "B21"}
VANTAGE_FIX = {"S125": "ORB close-up, halo bright, delivering 'twenty-three metres'",
               "S126": "toilet gag re-crop re-use (non-adjacent to itself) — TIGHT re-crop >=2.2x on GRUFF and the hole so the 1000 m horizon is out of frame"}
NOTE_FIX = {"S126": "replay of the Day-1 toilet gag on the 25 m rock: crop must exclude the horizon (house-sized planet on this day)"}

# ---------------- new unique rows (N*) ----------------
def N(key, beat, chars, set_, vantage, seeds, views, st, prompt, dur, partial=None, props=None):
    return dict(key=key, beat=beat, characters=chars, set=set_, vantage=vantage, seed_masters=seeds, seed_views=views, shot_type=st, i2v_prompt=prompt, duration_s=dur, partial=partial or [], props=props or [])
NEW = {
 "N1": N("N1","B09",["PIP","GRUFF"],"landing_pad","2-shot: PIP and GRUFF trudging onto the pad at dusk, tether dragging between them, low tracking",["M_PIP","M_GRUFF","M_SET_pad"],["M_PIP_3q","M_GRUFF_3q","M_SET_pad"],"MS","Camera tracks low alongside. PIP and GRUFF walk onto the pad three metres apart, the tether dragging and catching on the rock between them; GRUFF tugs it free without looking at her; pad lights glow in the dusk.",6),
 "N2": N("N2","B09",["ORB"],"landing_pad","ORB medium over the two covered platters, halo flaring toward the left lid then the right",["M_ORB","M_SET_pad"],["M_ORB_3q","M_SET_pad"],"MS","Camera locked at platter height. ORB hovers above two silver cloches; its halo flares once toward the left cloche, dims, then flares brighter toward the right one and holds; a highlight slides over both domes.",6,props=["tray_drone","cloche"]),
 "N4": N("N4","B09",["GRUFF"],"landing_pad","GRUFF close-up on the pad, one-shoulder shrug, brows flat",["M_GRUFF","M_SET_pad"],["M_GRUFF_expr","M_SET_pad"],"CU","Camera locked. GRUFF's brows stay flat; one shoulder lifts and drops in a slow shrug; fur settles; his eyes flick sideways once toward off-frame PIP and back.",4),
 "N5": N("N5","B10",[],"orbit","debris insert: tumbling rock fragments passing close to the lens against black space, the sheared planet soft behind",["M_PLANET_500"],["M_PLANET_500"],"INS","Camera locked in space. Fist-sized to tent-sized rock fragments tumble slowly past the lens from left to right, catching sunlight on their raw faces; the half-planet with its fresh sheared face drifts soft in the background; dust glitters.",4),
 "N6": N("N6","B13",["PIP","GRUFF"],"equator","night valley wide: PIP walking up the slope to GRUFF on the ridge, one ration bar in her hand",["M_PIP","M_GRUFF","M_PLANET_500"],["M_PIP_3q","M_GRUFF_3q","M_PLANET_500"],"WS","Camera locked wide, night. GRUFF sits on the ridge with his back half turned; PIP climbs the slope toward him carrying one ration bar, fronds low, stops two metres short; the tether lies slack between them; stars fixed.",6,props=["ration_bar"]),
 "N7": N("N7","B13",["PIP"],"equator","PIP medium holding out the ration bar, fronds low, hopeful, night",["M_PIP","M_PLANET_500"],["M_PIP_front","M_PLANET_500"],"MS","Camera locked. PIP holds a ration bar out at arm's length toward camera-right, fronds drooping then lifting a little at the tips; she does not speak; the scarf end stirs.",5,props=["ration_bar"]),
 "N8": N("N8","B13",["GRUFF"],"equator","GRUFF close-up looking down at the offered bar, brows reluctant, night",["M_GRUFF","M_PLANET_500"],["M_GRUFF_expr","M_PLANET_500"],"CU","Camera locked. GRUFF's eyes drop to something held out below frame; brows knot, then slowly loosen; fur over the mouth stirs once as if a word got stuck; a huge hand rises into the bottom of frame.",6),
 "N9": N("N9","B13",["GRUFF"],"confessional","GRUFF's hands in the cyan booth, macro: claws turning over each other",["M_GRUFF","M_SET_confessional"],["M_GRUFF_3q","M_SET_confessional"],"INS","Camera locked macro under cyan strip light. Two large cyan-furred hands turn slowly over each other in a lap; one claw taps the other palm twice; nothing else in frame moves.",5,partial=["GRUFF"]),
 "N11": N("N11","B15",[],"equator","plasma vent macro: orange plasma licking out of a crack in the basalt, no characters",["M_PLANET_300"],["M_PLANET_300"],"INS","Camera locked macro. Orange plasma licks upward out of a crack in grey basalt in slow tongues, casting moving warm light on the rock around it; sparks drift up and fade; no characters.",4,props=["plasma_vent"]),
 "N13": N("N13","B15",["PIP","GRUFF"],"equator","over PIP's shoulder to GRUFF across the vent, firelight, listening",["M_PIP","M_GRUFF","M_PLANET_300"],["M_PIP_3q","M_GRUFF_front","M_PLANET_300"],"OTS","Camera locked over PIP's shoulder, her fronds soft-focus in the foreground; across the vent GRUFF sits still in orange firelight, brows lifting slowly as he listens; the vent flickers between them.",5,props=["plasma_vent"]),
 "N14": N("N14","B15",["PIP"],"equator","PIP medium across the vent from GRUFF's side, fronds slowly rising, firelight",["M_PIP","M_PLANET_300"],["M_PIP_3q","M_PLANET_300"],"MS","Camera locked from GRUFF's side of the vent. PIP sits in orange firelight, eyes wide and fixed, fronds rising slowly from drooped to level; her mouth stays closed; firelight moves on her skin.",4,props=["plasma_vent"]),
 "N15": N("N15","B16",["PIP","GRUFF"],"equator","high angle from above the vent: both looking up at the wheeling stars, tiny horizon all round",["M_PIP","M_GRUFF","M_PLANET_300"],["M_PIP_front","M_GRUFF_front","M_PLANET_300"],"WS","Camera locked high above the vent looking down. PIP and GRUFF sit either side of the orange glow with their heads tipped back; the small planet's horizon curves tightly all round; stars drift slowly across the black.",6,props=["plasma_vent"]),
 "N16": N("N16","B16",["GRUFF"],"equator","GRUFF medium at the vent from PIP's side, shrugging, fur parted",["M_GRUFF","M_PLANET_300"],["M_GRUFF_3q","M_PLANET_300"],"MS","Camera locked from PIP's side. GRUFF gives a slow one-shoulder shrug in firelight, fur softly parting over the mouth, brows lifted; he pats the rock beside him once with a huge hand.",5,props=["plasma_vent"]),
 "N17": N("N17","B16",["ORB"],"orbit","ORB in orbit above the 300 m planet, halo very low, the vent a single orange dot below",["M_ORB","M_PLANET_300"],["M_ORB_front","M_PLANET_300"],"MS","Camera locked in orbit. ORB hovers in the foreground with its halo dimmed to a thin line; below, the small planet turns slowly with one orange dot of vent-light on its equator; the halo brightens by a hair at the end.",6),
 "N18": N("N18","B22",["PIP","GRUFF"],"landing_pad","PIP and GRUFF ducking under the dust storm on the flat top, pebbles bouncing off fur and scarf, low 2-shot",["M_PIP","M_GRUFF","M_SET_pad","M_PLANET_25"],["M_PIP_expr","M_GRUFF_expr","M_SET_pad","M_PLANET_25"],"MS","Camera locked low, handheld shake. GRUFF hunches over PIP as dust and pebbles stream across frame; her scarf whips; his fur flattens in the blast; both squint upward; the storm thins toward the end and dust settles.",5),
 "N19": N("N19","B26",[],"truth_beam","beam ignition: the column of light snapping on from the tray-drone projector, ground level, no characters",["M_SET_truth_beam"],["M_SET_truth_beam"],"INS","Camera locked at ground level. The tray-drone projector blinks, then a column of pale light snaps on upward out of it, wavers once, and steadies; dust motes rise through it; no characters.",4,props=["tray_drone"]),
 "N20": N("N20","B26",["ORB"],"truth_beam","ORB close above the beam, lens catching the column's light, halo pleased",["M_ORB","M_SET_truth_beam"],["M_ORB_front","M_SET_truth_beam"],"CU","Camera locked close. ORB hovers with the top of the light column glowing just below it; the column's light plays up over the chrome; the halo pulses in slow contented waves as if speaking.",4),
 "N21": N("N21","B26",["PIP","GRUFF"],"truth_beam","PIP stepping into the light, wide from behind GRUFF's shoulder, low angle",["M_GRUFF","M_PIP","M_SET_truth_beam"],["M_GRUFF_3q","M_PIP_front","M_SET_truth_beam"],"OTS","Camera locked low behind GRUFF's shoulder. PIP walks three small steps forward and stops inside the column of light; the light brightens on her skin and scarf; her fronds lift; GRUFF's fur stirs in the foreground.",6),
 "N22": N("N22","B26",["PIP","GRUFF"],"truth_beam","the beam turning GREEN, wide from the side, both figures silhouetted either side of the column",["M_PIP","M_GRUFF","M_SET_truth_beam"],["M_PIP_3q","M_GRUFF_3q","M_SET_truth_beam"],"WS","Camera locked wide from the side. The pale column of light shifts to a clean green over one second and holds; PIP inside it and GRUFF on his mark are dark silhouettes rimmed in green; nothing else moves.",5),
 "N23": N("N23","B31",["COUNT"],"orbit","THE COUNT hovering at GRUFF's knee height beside the 4 m rock, faces blank, antenna wobbling",["M_COUNT","M_PLANET_4"],["M_COUNT_3q","M_PLANET_4"],"INS","Camera locked. THE COUNT hovers beside the small rock at the height of a knee, holding station with tiny thruster puffs, antenna wobbling; its blank display plates catch starlight; the rock turns barely.",4),
 "N25": N("N25","B33",[],"orbit","the clock housing at night, macro: blank red display face (digits in post), two sleeping shapes soft in the background",["M_PLANET_2"],["M_PLANET_2"],"INS","Camera locked macro on the small clock housing bolted to the rock; its blank red display face glows steadily (digits composited); behind it, soft and out of focus, two sleeping shapes against the crate; a slow breath of light on the housing.",5,props=["clock_housing"]),
}
POST = {
 "ARCH_STACK": dict(beat="B01", vantage="archive still stack: six band stills flip past with whiteouts (FFmpeg-built from M_ARCH_01..06, no generation)", seeds=["M_ARCH_01_stage_wide","M_ARCH_02_stage_drums","M_ARCH_03_bus_road","M_ARCH_04_bus_bunks","M_ARCH_05_dressing_room","M_ARCH_06_empty_hall"], prompt="POST ONLY, no i2v: six stills at 0.4 s each with a 2-frame whiteout between, a slow 1.03x push on each; the band = PIP, GRUFF and two silhouettes."),
 "ARCH_VAN": dict(beat="B32", vantage="archive flash: the tour-van still (M_ARCH_03) whiteout in and out under 'I sold the tour van'", seeds=["M_ARCH_03_bus_road"], prompt="POST ONLY, no i2v: one still, 2 s, whiteout in and out, slow 1.05x push."),
}

# ---------------- per-beat tiling plans: list of (ref, slot). ref = v1 id | 'N*' | 'POST:*' | 'PUNCH:<v1 id>' | 'INS:<v1 id>' ----------------
# beats not listed keep v1 order and v1 slots (with the automatic 8-10 s punch rule applied).
PLAN = {
 "B01": [("S001",2),("S002",1),("POST:ARCH_STACK",3),("PUNCH:S002",2),("S003",4)],
 "B09": [("S040",6),("N1",6),("S041",5),("N2",5),("PUNCH:S041",3),("S042",5),("N4",4),("PUNCH:S042",3),("S043",8)],
 "B10": [("S044",8),("N5",3),("S045",5),("PUNCH:S045",4),("S046",4),("S047",7),("S048",7),("S049",2)],
 "B13": [("N6",6),("S064",5),("N7",4),("N8",5),("S065",6),("N9",4),("PUNCH:S065",3),("S066",4),("INS:S047",3)],
 "B14": [("S068",8),("S067",7),("S069",6),("S070",5),("S071",5),("S072",7),("S073",5),("S074",2)],
 "B15": [("N11",3),("S075",6),("PUNCH:S075",3),("S076",6),("N13",5),("S077",6),("N14",3),("PUNCH:S077",3)],
 "B16": [("S078",6),("N15",6),("S079",4),("N16",4),("INS:S075",3),("S080",6),("N17",6)],
 "B22": [("S115",8),("N18",4),("S116",5)],
 "B26": [("N19",4),("S134",7),("N20",3),("PUNCH:S134",3),("S135",6),("N21",6),("S136",4),("N22",4),("INS:S135",4),("S137",5),("PUNCH:S137",4)],
 "B31": [("S162",9),("N23",3),("S163",5),("S164",7),("S165",6),("S166",6),("S167",3),("S168",6)],
 "B32": [("S169",6),("POST:ARCH_VAN",2),("PUNCH:S169",4),("S170",5),("PUNCH:S170",3),("S171",2),("S172",5),("PUNCH:S172",3),("S173",5),("PUNCH:S173",3),("S174",7)],
 "B33": [("S175",7),("N25",5),("S176",5),("PUNCH:S176",4),("S177",7),("S178",5),("PUNCH:S178",4),("S179",3)],
}
INS_NOTE = {("B13","S047"): "aftermath half-planet re-use (non-adjacent) under 'rock left to lose'",
            ("B16","S075"): "vent 2-shot wide re-use (non-adjacent) under 'that's a chair'",
            ("B26","S135"): "GRUFF in-beam close-up re-use (non-adjacent) — 'Bigger room. Smaller everything else.'"}
HERO_TYPES = {"HERO"}
def punch_split(slot):  # 8 -> (5,3), 9 -> (5,4), 10 -> (6,4)
    return {8: (5,3), 9: (5,4), 10: (6,4)}[slot]

# ---------------- build ----------------
by_beat_v1 = collections.defaultdict(list)
for s in v1["shots"]: by_beat_v1[BEAT_MOVE.get(s["id"], s["beat"])].append(s)
v1slot = {s["id"]: sec(s["t_out"]) - sec(s["t_in"]) for s in v1["shots"]}
# S113/S114 keep their v1 slots (11:30-11:37, 11:37-11:43) inside the new B21 span.

def base_row(v):
    r = copy.deepcopy(v); r["v1_id"] = v["id"]; r.pop("continuity_note", None)
    r["beat"] = BEAT_MOVE.get(v["id"], v["beat"])
    if v["id"] in CHAR_FIX: r["characters"], r["partial"] = CHAR_FIX[v["id"]]
    else: r["partial"] = []
    if v["id"] in LOOP_SET: r["loops"] = LOOP_SET[v["id"]]
    if v["id"] in SEED_SWAP:
        a, b = SEED_SWAP[v["id"]]; r["seed_masters"] = [b if x == a else x for x in r["seed_masters"]]; r["seed_views"] = [b if x == a else x for x in r["seed_views"]]
    if v["id"] in SEED_DROP:
        d = SEED_DROP[v["id"]]; r["seed_views"] = [x for x in r["seed_views"] if x != d]; r["seed_masters"] = [x for x in r["seed_masters"] if x != d.rsplit("_",1)[0]]
    if v["id"] in VANTAGE_FIX: r["vantage"] = VANTAGE_FIX[v["id"]]
    if v["id"] in NOTE_FIX: r["continuity_note"] = NOTE_FIX[v["id"]]
    elif v.get("continuity_note"): r["continuity_note"] = v["continuity_note"]
    return r

next_c = 177
rows = []  # ordered rows with 'slot'
for bid, ti, to, day, act in BEATS:
    plan = PLAN.get(bid)
    if plan is None:
        plan = []
        for s in by_beat_v1[bid]:
            slot = v1slot[s["id"]]
            if s["reuse"] == "unique" and s["shot_type"] not in HERO_TYPES and "PIP" not in s["mouth_visible"] and 8 <= slot <= 10:
                a, b = punch_split(slot); plan += [(s["id"], a), ("PUNCH:" + s["id"], b)]
            else: plan.append((s["id"], slot))
    assert sum(sl for _, sl in plan) == sec(to) - sec(ti), (bid, sum(sl for _, sl in plan), sec(to) - sec(ti))
    for ref, slot in plan:
        if ref.startswith("PUNCH:"):
            src = ref[6:]; r = {"beat": bid, "v1_id": None, "punch_of_v1": src, "slot": slot}
        elif ref.startswith("INS:"):
            src = ref[4:]; r = {"beat": bid, "v1_id": None, "insert_of_v1": src, "slot": slot}
        elif ref.startswith("POST:"):
            p = POST[ref[5:]]; r = {"beat": bid, "v1_id": None, "post": ref[5:], "slot": slot, **p}
        elif ref in NEW:
            n = NEW[ref]; r = dict(n); r.update({"v1_id": None, "slot": slot, "composite_seed_id": f"C{next_c:03d}"}); next_c += 1
        else:
            r = base_row(V1[ref]); r["slot"] = slot
        r["day"], r["act"] = day, act; r["planet_m"] = r["count_display"] = ladder_for(day)
        rows.append(r)

# assign ids + times, resolve punch/insert sources, set durations
out = []; t = 0; v1_to_new = {}; cur_beat = None
for i, r in enumerate(rows, 1):
    sid = f"S{i:03d}"
    if r["beat"] != cur_beat: cur_beat = r["beat"]; t = sec(BEAT[cur_beat][1])
    slot = r.pop("slot"); t_in, t_out = tc(t), tc(t + slot); t += slot
    if r.get("v1_id"): v1_to_new[r["v1_id"]] = sid
    r.update(id=sid, t_in=t_in, t_out=t_out)
    out.append(r)
assert t == 1200
byid = {r["id"]: r for r in out}
final = []
for r in out:
    if "punch_of_v1" in r:
        src = byid[v1_to_new[r.pop("punch_of_v1")]]; slot = sec(r["t_out"]) - sec(r["t_in"])
        d = {"id": r["id"], "beat": r["beat"], "act": r["act"], "t_in": r["t_in"], "t_out": r["t_out"], "day": r["day"], "planet_m": r["planet_m"], "count_display": r["count_display"],
             "characters": src["characters"], "partial": src.get("partial", []), "set": src["set"],
             "vantage": f"punch-in {1.5 if slot >= 4 else 1.6}x on: {src['vantage']} (post re-crop, same take, later window)",
             "seed_masters": src["seed_masters"], "seed_views": src["seed_views"], "composite_seed_id": src["composite_seed_id"], "shot_type": src["shot_type"],
             "i2v_prompt": f"REUSE of {src['id']} (same clip; post re-crop only, no new generation) — plays the NEXT window of the take, see clip_window",
             "duration_s": slot, "reuse": "insert", "punch": True, "insert_of": src["id"], "v1_id": None, "v1_source": src["v1_id"], "loops": [], "mouth_visible": src["mouth_visible"], "props": src.get("props", [])}
        src.setdefault("_punch_slots", []).append(slot); d["_src"] = src; final.append(d); continue
    if "insert_of_v1" in r:
        src = byid[v1_to_new[r.pop("insert_of_v1")]]; slot = sec(r["t_out"]) - sec(r["t_in"])
        d = {"id": r["id"], "beat": r["beat"], "act": r["act"], "t_in": r["t_in"], "t_out": r["t_out"], "day": r["day"], "planet_m": r["planet_m"], "count_display": r["count_display"],
             "characters": src["characters"], "partial": src.get("partial", []), "set": src["set"], "vantage": INS_NOTE[(r["beat"], src["v1_id"])],
             "seed_masters": src["seed_masters"], "seed_views": src["seed_views"], "composite_seed_id": src["composite_seed_id"], "shot_type": src["shot_type"],
             "i2v_prompt": f"REUSE of {src['id']} (same clip; re-crop/re-grade in FFmpeg only, no new generation)", "duration_s": slot, "reuse": "insert", "insert_of": src["id"], "v1_id": None, "v1_source": src["v1_id"],
             "loops": [], "mouth_visible": [], "props": src.get("props", [])}
        if src["planet_m"] != r["planet_m"]: d["continuity_note"] = "replay/flashback clip — planet size on screen is the source day's"
        final.append(d); continue
    if "post" in r:
        slot = sec(r["t_out"]) - sec(r["t_in"])
        d = {"id": r["id"], "beat": r["beat"], "act": r["act"], "t_in": r["t_in"], "t_out": r["t_out"], "day": r["day"], "planet_m": r["planet_m"], "count_display": r["count_display"],
             "characters": [], "partial": [], "set": "archive", "vantage": r["vantage"], "seed_masters": r["seeds"], "seed_views": r["seeds"], "composite_seed_id": None, "shot_type": "INS",
             "i2v_prompt": r["prompt"], "duration_s": slot, "reuse": "post", "v1_id": None, "loops": [], "mouth_visible": [], "props": [],
             "continuity_note": "archive stills: the band (PIP, GRUFF + two silhouettes) inside the stills; no composite, no generation; banked as the FFmpeg-built clip"}
        final.append(d); continue
    if "key" in r:  # new unique
        r.pop("key")
        d = {"id": r["id"], "beat": r["beat"], "act": r["act"], "t_in": r["t_in"], "t_out": r["t_out"], "day": r["day"], "planet_m": r["planet_m"], "count_display": r["count_display"],
             "characters": r["characters"], "partial": r["partial"], "set": r["set"], "vantage": r["vantage"], "seed_masters": r["seed_masters"], "seed_views": r["seed_views"],
             "composite_seed_id": r["composite_seed_id"], "shot_type": r["shot_type"], "i2v_prompt": r["i2v_prompt"], "duration_s": r["duration_s"], "reuse": "unique", "v1_id": None,
             "loops": [], "mouth_visible": [], "props": r["props"]}
        r.clear(); r.update(d); final.append(r); continue
    # v1 row
    if r["reuse"] == "insert":
        r["insert_of"] = v1_to_new[r["insert_of"]]; r["v1_source"] = V1[r["v1_id"]]["insert_of"]
        r["duration_s"] = sec(r["t_out"]) - sec(r["t_in"])
        srcrow = byid[r["insert_of"]]
        if srcrow["planet_m"] != r["planet_m"] and "continuity_note" not in r: r["continuity_note"] = "replay/flashback clip — planet size on screen is the source day's" if ("re-use" in r["vantage"] or "replay" in r["vantage"]) else "planet not visible in frame (macro/re-crop)"
    r.setdefault("props", [])
    final.append(r)
# unique durations: slot + punches <= duration_s (raise where needed, cap 10); planet-master continuity notes
for r in final:
    if r["reuse"] == "unique":
        slot = sec(r["t_out"]) - sec(r["t_in"]); need = slot + sum(r.pop("_punch_slots", []))
        if r["duration_s"] < need: r["duration_s"] = need
        assert r["duration_s"] <= 10, (r["id"], r["v1_id"], r["duration_s"])
        want = PLANET_FOR[r["planet_m"]]; sp = [m for m in r["seed_masters"] if m.startswith("M_PLANET_")]
        if sp and want not in sp and "continuity_note" not in r: r["continuity_note"] = "wedge hero: from->to planet pair by design" if r["shot_type"] == "HERO" else "planet not visible in frame (macro/re-crop)"
# punch clip windows
for r in final:
    if r.get("punch"):
        src = r.pop("_src"); used = sec(src["t_out"]) - sec(src["t_in"])
        prior = [x for x in final if x.get("punch") and x.get("insert_of") == src["id"] and sec(x["t_in"]) < sec(r["t_in"])]
        a = used + sum(sec(x["t_out"]) - sec(x["t_in"]) for x in prior); b = a + r["duration_s"]
        r["clip_window"] = [a, b]; assert b <= src["duration_s"], (r["id"], src["id"], a, b, src["duration_s"])
# ordered keys
KEYS = ["id","v1_id","beat","act","t_in","t_out","day","planet_m","count_display","characters","partial","set","vantage","seed_masters","seed_views","composite_seed_id","shot_type","i2v_prompt","duration_s","reuse","punch","insert_of","clip_window","v1_source","loops","mouth_visible","props","continuity_note"]
final = [{k: r[k] for k in KEYS if k in r} for r in final]

# ---------------- props (master list + per-row assignment) ----------------
PROPS = {
 "helmet": "two clear bubble space helmets with a plain neck-seal ring, one PIP-sized, one GRUFF-sized, held or lying on the rock",
 "anklet": "a brushed-steel ankle cuff with one hinge and a single small red status light, one on each contestant, joined by the silver gravity tether",
 "tether": "the silver gravity tether: a thin coiled silver cable with a faint inner glow, always joining the two anklets",
 "tray_drone": "a small flat tray drone: a hovering silver tray on four tiny rotors, no face, no markings",
 "cloche": "a domed silver platter lid (cloche) on a silver tray",
 "crate_open": "the sealed metal crate with both doors swung open, warm gold light inside, a dark velvet tray in it",
 "tickets": "two rectangular tickets with blank soft-gold glowing faces (any text composited in post), lying on a dark velvet tray",
 "paperback": "a battered paperback with a blank pale cover and dog-eared pages (title composited in post)",
 "dome_hologram": "a translucent pale-green hologram of a glass dome with a garden, trees and circling birds drawn in lines of light, floating over the planet",
 "rescue_ship": "a long blunt grey rescue ship with two blue engine bells and small running lights, no markings",
 "tally_marks": "claw-scratched tally marks on cave rock, six of them",
 "moon_rock_heart": "a heart shape laid out from fist-sized pale moon rocks on grey basalt",
 "ration_bar": "a plain grey-green ration bar the size of a hand; tin plate and ration tin are dull pressed metal",
 "clock_housing": "a small matte-black clock housing bolted to the rock with two bolts, one blank red seven-segment face (digits composited in post)",
 "launch_key": "a heavy brass launch key with a round bow, lying on a folded red cloth",
 "red_lever": "a red lever on a steel bracket beside the pod door, hand-sized grip",
 "glass_pod": "a domed soundproof glass pod on the rock with one stool inside, lit by a magenta or cyan strip light",
 "plasma_vent": "a crack in the basalt leaking slow orange plasma that lights the rock around it like a campfire",
 "bedroll": "a rolled grey sleeping mat; two of them jammed side by side",
 "tent": "a small magenta dome tent with a single zip flap",
 "lamp": "a small handheld lamp with a soft white beam",
 "keyboard": "a compact battered keyboard instrument in a soft case (PIP's luggage)",
}
RULES = [("helmet", r"helmet"), ("anklet", r"anklet"), ("tether", r"tether"), ("tray_drone", r"tray drone|tray-drone"), ("cloche", r"cloche|platter|\blids?\b"),
 ("crate_open", r"crate doors|open crate|doors open"), ("tickets", r"ticket"), ("paperback", r"paperback|\bbook\b"), ("dome_hologram", r"hologram|glass dome"), ("rescue_ship", r"rescue ship|ship rising|the ship"),
 ("tally_marks", r"tally"), ("moon_rock_heart", r"moon-rock heart|moon rock heart|heart shape|heart of small"), ("ration_bar", r"\brations?\b|tin plate|ration tin"), ("clock_housing", r"clock"), ("launch_key", r"launch key|brass key|the key"),
 ("red_lever", r"lever"), ("glass_pod", r"glass pod|pod glass|soundproof|through the pane"), ("plasma_vent", r"\bvent\b|firelit|firelight"), ("bedroll", r"bedroll"), ("tent", r"\btent\b"), ("lamp", r"\blamp\b"), ("keyboard", r"keyboard")]
OVERRIDE = {  # by v1_id — the reviewer's list + a few the regex would miss
 "S002": ["helmet"], "S011": ["helmet"], "S013": ["anklet","tether"], "S016": ["anklet"], "S012": ["anklet","tether"], "S006": ["tether","anklet"], "S193": ["anklet","tether"],
 "S041": ["tray_drone","cloche"], "S106": ["tray_drone","cloche"], "S107": ["tray_drone","cloche"], "S108": ["tray_drone","cloche"], "S109": ["tray_drone","cloche"], "S110": ["tray_drone","cloche"], "S113": ["tray_drone","cloche"],
 "S098": ["paperback"], "S099": ["paperback"], "S100": ["paperback"], "S086": ["dome_hologram"], "S087": ["dome_hologram"], "S089": ["dome_hologram"], "S118": ["tickets","crate_open"], "S119": ["tickets","crate_open"],
 "S117": ["crate_open"], "S195": ["crate_open"], "S190": ["rescue_ship"], "S191": ["rescue_ship"], "S055": ["tally_marks"], "S070": ["moon_rock_heart"], "S071": ["moon_rock_heart"], "S072": ["moon_rock_heart"],
 "S096": ["ration_bar"], "S097": ["ration_bar"], "S064": ["ration_bar"], "S021": ["ration_bar","keyboard"], "S196": ["ration_bar"], "S173": ["clock_housing","tray_drone"], "S180": ["clock_housing"], "S192": ["clock_housing"],
 "S128": ["launch_key","cloche"], "S149": ["launch_key"], "S146": ["launch_key","red_lever"], "S163": ["red_lever"], "S179": ["red_lever"], "S185": ["red_lever"], "S187": ["red_lever"], "S183": ["red_lever"], "S184": ["red_lever"], "S188": ["red_lever"],
 "S151": ["glass_pod"], "S152": ["glass_pod"], "S153": ["glass_pod"], "S154": ["glass_pod"], "S155": ["glass_pod"], "S075": ["plasma_vent"], "S076": ["plasma_vent"], "S077": ["plasma_vent"], "S079": ["plasma_vent"], "S080": ["plasma_vent"], "S102": ["plasma_vent"], "S103": ["plasma_vent"], "S105": ["plasma_vent"],
 "S124": ["bedroll"], "S050": ["tent"], "S051": ["tent"], "S034": ["tent"], "S053": ["lamp"], "S045": ["tent"],
}
for r in final:
    if r["reuse"] in ("unique",) and r["v1_id"]:
        txt = (r["vantage"] + " " + r["i2v_prompt"]).lower(); p = list(OVERRIDE.get(r["v1_id"], []))
        for pid, rx in RULES:
            if re.search(rx, txt) and pid not in p: p.append(pid)
        r["props"] = p
for r in final:
    if r.get("insert_of"): r["props"] = byid[r["insert_of"]].get("props", []) if r["insert_of"] in byid else r["props"]
byid = {r["id"]: r for r in final}
for r in final:
    if r.get("insert_of"): r["props"] = byid[r["insert_of"]]["props"]

# ---------------- masters (notes remapped to the 36-beat numbering) ----------------
masters = copy.deepcopy(v1["seed_masters"])
REMAP = {"M_PLANET_1000": "Day 1-4. The only planet with sky haze. Hero pull-out source (B05, B36).", "M_PLANET_500": "Day 5-6 (shrinks at B10 sunrise). Sheared face must read from orbit.",
         "M_PLANET_300": "Day 10-19 (shrinks at B14 open).", "M_PLANET_25": "Day 20 (tear at B22 sunrise). Also re-cropped 1.25x tighter for the 20 m planet (Day 25).",
         "M_ARCH_03_bus_road": "The van GRUFF later sells (B32). Also the 2 s archive flash in B32.", "M_ARCH_05_dressing_room": "Pays off B15 'nobody would notice'.",
         "M_ARCH_01_stage_wide": "Nostalgic; band = 4 years, one bus, one stage. Part of the B01 archive stack (post)."}
for m in masters:
    if m["id"] in REMAP: m["notes"] = REMAP[m["id"]]
    elif m["kind"] == "archive" and "archive stack" not in m["notes"]: m["notes"] += " Part of the B01 archive stack (post)."
MID = {m["id"] for m in masters} | {v["id"] for m in masters if m["kind"] == "character" for v in m["views"]}
SETD = {m["id"]: re.sub(r"^.*?Set master, ", "", m["prompt"].replace(ART_STYLE + " ", "")).replace(" " + NEG, "") for m in masters if m["kind"] == "set"}
PLD = {m["id"]: m["prompt"].replace(ART_STYLE + " ", "").replace(" " + NEG, "") for m in masters if m["kind"] == "planet"}

# ---------------- composites (one per unique composite_seed_id) ----------------
comps = []; seen = set()
for r in final:
    cid = r.get("composite_seed_id")
    if not cid or cid in seen or r["reuse"] != "unique": continue
    seen.add(cid)
    chars = r["characters"]; views = [v for v in r["seed_views"] if any(v.startswith("M_" + c + "_") for c in chars)]
    sets = [v for v in r["seed_views"] if v.startswith("M_SET_")]; planets = [v for v in r["seed_views"] if v.startswith("M_PLANET_")]
    parts = [ART_STYLE] + [ANCHORS[c] for c in chars]
    fr = f"Composite seed frame for shot {r['id']} ({r['shot_type']}): {r['vantage']}."
    if r.get("partial"): fr += f" Only a body part of {', '.join(r['partial'])} is in frame (no face)."
    if sets: fr += " Setting: " + SETD[sets[0]]
    if planets: fr += (" Planet class: " + PLD[planets[0]]) if not sets else f" Planet horizon per {planets[0]}."
    if r["props"]: fr += " Props in frame: " + "; ".join(PROPS[p] for p in r["props"]) + "."
    fr += " First frame of the shot only, everything at rest, no motion blur."
    comps.append({"id": cid, "shot": r["id"], "v1_shot": r["v1_id"], "beat": r["beat"], "characters": chars, "partial": r.get("partial", []), "views": views, "set_master": sets[0] if sets else None, "planet_master": planets[0] if planets else None,
                  "props": r["props"], "framing_prompt": " ".join(parts + [fr, NEG]), "used_by": []})
CID = {c["id"]: c for c in comps}
for r in final:
    if r.get("composite_seed_id") in CID: CID[r["composite_seed_id"]]["used_by"].append(r["id"])

# ---------------- totals ----------------
uniq = [r for r in final if r["reuse"] == "unique"]; ins = [r for r in final if r["reuse"] == "insert" and not r.get("punch")]; pun = [r for r in final if r.get("punch")]; post = [r for r in final if r["reuse"] == "post"]
peract = collections.Counter(r["act"] for r in uniq)
manifest = {"title": "Shrinking Planet", "version": "v2", "source_of_truth": v1["source_of_truth"],
 "review_applied": "v1 adversarial review — LANDED items applied (clock ladder, ladder-by-event, loops sync, timing model, archive stack row, character refs, composites/props layer, seed-note remap, prize arithmetic, paraphrase rewrites)",
 "art_style": ART_STYLE, "identity_anchors": ANCHORS, "negative_constraints": NEG,
 "ladder": LADDER,
 "ladder_notes": "Keyed by the day the planet HAS that size at sunrise (bible rungs 1/5/10/20/25-30 plus the story days). Every shrink lands at the START of a beat — B10 (Day 5 sunrise, 1000->500), B14 (Day 10, 500->300, first row), B22 (Day 20 sunrise, 300->25) — and the offer that causes it is made the evening before (B09 = Day 4 at 1000 m, B21 = Day 19 at 300 m), so no beat and no row straddles a shrink; count_display == planet_m == ladder[day] on every row. See shrink_events. 20 m and 7 m are re-crops of the 25 m and 12 m masters.",
 "shrink_events": SHRINK_EVENTS,
 "characters": v1["characters"], "seed_masters": masters,
 "props": [{"id": k, "description": v, "used_by": [r["id"] for r in final if k in r.get("props", [])]} for k, v in PROPS.items()],
 "composites": comps,
 "rules": {"unique_target": 176, "unique_range": [150, 200], "adjacent_vantage_must_differ": True, "inserts_never_adjacent_to_self": True,
           "punch_rows": "reuse='insert' + punch=true + clip_window: a post re-crop of a LATER window of the same take; MAY sit next to its source (same-take continuation, the bible's hook technique); never two punches of one take back-to-back",
           "post_rows": "reuse='post': FFmpeg-built from archive stills, no generation, composite_seed_id null; banked as the built clip",
           "slot_rule": "for every row t_out - t_in <= duration_s; for unique rows slot + sum(punch slots) <= duration_s (the generated length)",
           "partial": "characters listed in `partial` appear only as a body part (hand/anklet/goggle/fur wall): identity QA checks colour + material, not the face",
           "pip_mouth_visible_cap": 20, "default_duration_s": 6, "hero_max_duration_s": 10, "cut_cadence_target_s": [5, 7]},
 "totals": {"shots": len(final), "unique": len(uniq), "inserts": len(ins), "punches": len(pun), "post": len(post), "gate_unique_count_reuse_not_insert": len(uniq) + len(post),
            "unique_per_act": dict(peract), "composites": len(comps), "pip_mouth_visible_shots": sum(1 for r in final if "PIP" in r["mouth_visible"]), "beats": len(BEATS), "v1_unique": 176},
 "shots": final}
json.dump(manifest, open(OUT + "/shot_manifest_v2.json", "w"), indent=1)

# ---------------- verification ----------------
errs = []
script = open(OUT + "/SCRIPT_v2.md", encoding="utf-8").read().split("\n")
hdr = re.compile(r"^## (B\d{2}) \[(\d\d:\d\d)-(\d\d:\d\d)\]"); tagre = re.compile(r"^\[(DAY|PLANET|COUNT|LOOP)\s+(.*)\]$"); dlg = re.compile(r"^\*\*(PIP|GRUFF|ORB)\*\* \(([^)]*)\):")
sb = {}; cur = None
for ln in script:
    m = hdr.match(ln)
    if m: cur = m.group(1); sb[cur] = {"t_in": m.group(2), "t_out": m.group(3), "tags": collections.defaultdict(list), "on": 0}; continue
    if not cur: continue
    m = tagre.match(ln.strip())
    if m: sb[cur]["tags"][m.group(1)].append(m.group(2)); continue
    m = dlg.match(ln.strip())
    if m and m.group(1) == "PIP" and "mouth:ON" in m.group(2): sb[cur]["on"] += 1
mb = collections.defaultdict(list)
for r in final: mb[r["beat"]].append(r)
prev = None
for r in final:
    slot = sec(r["t_out"]) - sec(r["t_in"])
    if slot > r["duration_s"]: errs.append(f"{r['id']} slot {slot} > duration {r['duration_s']}")
    if r["reuse"] == "unique":
        pun_slots = sum(sec(x["t_out"]) - sec(x["t_in"]) for x in final if x.get("punch") and x["insert_of"] == r["id"])
        if slot + pun_slots > r["duration_s"]: errs.append(f"{r['id']} slot+punches {slot+pun_slots} > duration {r['duration_s']}")
    if r.get("insert_of"):
        src = byid[r["insert_of"]]
        if sec(src["t_in"]) >= sec(r["t_in"]): errs.append(f"{r['id']} insert points forward")
        if not r.get("punch") and slot > src["duration_s"]: errs.append(f"{r['id']} replay slot {slot} > source dur {src['duration_s']}")
        if src["reuse"] != "unique": errs.append(f"{r['id']} insert of non-unique {src['id']}")
    if r["count_display"] != r["planet_m"] or r["planet_m"] != ladder_for(r["day"]): errs.append(f"{r['id']} ladder mismatch")
    for c in r["characters"]:
        if not any(v.startswith("M_" + c + "_") for v in r["seed_views"]): errs.append(f"{r['id']} character {c} without a view")
    for v in r["seed_views"]:
        if v not in MID: errs.append(f"{r['id']} unknown view {v}")
        if v.startswith(("M_PIP_", "M_GRUFF_", "M_ORB_", "M_COUNT_")) and v.split("_")[1] not in r["characters"]: errs.append(f"{r['id']} view {v} but character absent")
    if prev:
        if prev["vantage"] == r["vantage"]: errs.append(f"{r['id']} same vantage as {prev['id']}")
        if prev.get("composite_seed_id") and prev.get("composite_seed_id") == r.get("composite_seed_id") and not (r.get("punch") and r["insert_of"] == prev["id"]): errs.append(f"{r['id']} same composite as adjacent {prev['id']}")
        if r.get("punch") and prev.get("punch") and prev["insert_of"] == r["insert_of"]: errs.append(f"{r['id']} two punches back-to-back")
        if r["reuse"] == "insert" and not r.get("punch"):
            if prev["id"] == r["insert_of"] or prev.get("insert_of") == r["insert_of"]: errs.append(f"{r['id']} replay adjacent to source/sibling")
        if sec(r["t_in"]) != sec(prev["t_out"]) and r["beat"] == prev["beat"]: errs.append(f"{r['id']} gap")
    if r["duration_s"] > 10: errs.append(f"{r['id']} > 10 s")
    if r["reuse"] == "unique" and r["composite_seed_id"] not in CID: errs.append(f"{r['id']} no composite entry")
    prev = r
for bid, ti, to, day, act in BEATS:
    ms = mb[bid]
    if not ms: errs.append(f"{bid} no shots"); continue
    if ms[0]["t_in"] != ti or ms[-1]["t_out"] != to: errs.append(f"{bid} span {ms[0]['t_in']}-{ms[-1]['t_out']} vs {ti}-{to}")
    if (sb[bid]["t_in"], sb[bid]["t_out"]) != (ti, to): errs.append(f"{bid} script span differs {sb[bid]['t_in']}-{sb[bid]['t_out']}")
    tg = sb[bid]["tags"]
    if int(tg["DAY"][0]) != day or int(tg["PLANET"][0]) != ladder_for(day) or int(tg["COUNT"][0]) != ladder_for(day): errs.append(f"{bid} script DAY/PLANET/COUNT {tg['DAY']}/{tg['PLANET']}/{tg['COUNT']} vs {day}/{ladder_for(day)}")
    sl = sorted(tg["LOOP"]); ml = sorted(l.replace(":", " ") for r in ms for l in r["loops"])
    if sl != ml: errs.append(f"{bid} loops script {sl} vs manifest {ml}")
    mv = sum(1 for r in ms if "PIP" in r["mouth_visible"])
    if mv != sb[bid]["on"]: errs.append(f"{bid} mouth_visible {mv} vs mouth:ON {sb[bid]['on']}")
used_masters = collections.Counter(m for r in final for m in r["seed_masters"])
for m in masters:
    if used_masters[m["id"]] == 0: errs.append(f"master {m['id']} unreferenced")
if len(masters) != 23: errs.append("masters != 23")
g = len(uniq) + len(post)
if not (150 <= g <= 200): errs.append(f"gate unique count {g} outside 150-200")
ic = collections.Counter(r["insert_of"] for r in final if r["reuse"] == "insert" and not r.get("punch"))
for k, v in ic.items():
    if v > 3: errs.append(f"{k} re-used {v} times")
print(f"v2: shots={len(final)} unique={len(uniq)} inserts={len(ins)} punches={len(pun)} post={len(post)} gate_unique={g} composites={len(comps)} pip_mouth_visible={manifest['totals']['pip_mouth_visible_shots']}")
print("slots>7s:", [(r["id"], sec(r["t_out"]) - sec(r["t_in"]), r["shot_type"]) for r in final if sec(r["t_out"]) - sec(r["t_in"]) > 7])
print("ERRORS", len(errs)); [print("  ", e) for e in errs]

# ---------------- SEED_PROMPTS_v2.md ----------------
L = []; w = L.append
w("# SHRINKING PLANET — Seed Prompt Pack v2 (23 masters + 22 props + per-shot composites)\n")
w("Gate 1 deliverable: image-gen prompts for the 23 approved masters, the props master list, and the composite-seed recipe for every unique shot. Every prompt carries the locked art-style paragraph verbatim, the fixed identity anchors, and the negative constraints. One seed per character is chosen from these; files are frozen with hashes (`scripts/seed_lock.py`); every composite derives from them (`scripts/build_composite_seeds.py`). Source: `SHRINKING_PLANET_bible_v2.html`; v2 applies the v1 review (seed notes remapped to the 36-beat script, archive masters now referenced by the B01 stack row, composites/props layer added).\n")
w("**Image generator (pinned, subscription only — no metered API):** Grok Imagine text-to-image on the paid account for masters and composites (recipe: `reference_grok_imagine_batch_recipe_2026-08.md`); fallback = the ChatGPT-image subscription batch recipe. i2v: Grok Imagine image-to-video from the composite seed. Post: FFmpeg. Foley: MMAudio. VO: ElevenLabs one pass.\n")
w("## Locked art style (verbatim in every prompt)\n"); w("> " + ART_STYLE + "\n")
w("## Identity anchors (fixed, never vary across the 30 days)\n")
for k, v in ANCHORS.items(): w(f"- **{k}** — {v}")
w("\n## Negative constraints (verbatim in every prompt)\n"); w("> " + NEG + "\n")
w("## Master index\n"); w("| # | id | kind | notes |\n|---|---|---|---|")
for i, m in enumerate(masters, 1): w(f"| {i} | `{m['id']}` | {m['kind']} | {m['notes'].replace('|','/')} |")
w("\n*Planet classes: 1000 / 500 / 300 / 25 / 12 / 4 / 2 m. The 20 m (Day 25) and 7 m (Day 27) planets are re-crops of the 25 m and 12 m masters — no separate generation. Beat numbers are the 36-beat SCRIPT_v2 numbering.*\n")
for kind, title in [("character","Characters (4 masters × 3 views)"),("planet","Planet-size masters (7)"),("set","Set masters (6)"),("archive","Archive band stills (6)")]:
    w(f"\n---\n\n# {title}\n")
    for m in masters:
        if m["kind"] != kind: continue
        w(f"\n## {m['id']}\n"); w(f"*{m['notes']}*\n")
        if kind == "character":
            for v in m["views"]: w(f"\n### {v['id']} ({v['view']})\n"); w("```text\n" + v["prompt"] + "\n```")
        else: w("```text\n" + m["prompt"] + "\n```")
w("\n---\n\n# Props master list (22)\n")
w("Props are NOT separate generations: each is described inside the composite framing prompt of every shot that needs it (i2v cannot conjure an object absent from the seed). Descriptions are fixed wording — paste verbatim.\n")
w("| prop | description | shots |\n|---|---|---|")
for p in manifest["props"]: w(f"| `{p['id']}` | {p['description']} | {len(p['used_by'])} |")
w("\n---\n\n# Composite seeds (one per unique shot)\n")
w(f"{len(comps)} composites. Recipe per C-id: `framing_prompt` = art-style paragraph + the identity anchor of every character in the shot + the shot-specific framing sentence (vantage, set/planet master description, props) + negative block. Build order: (1) `scripts/build_composite_seeds.py` places the locked character cutouts on the set/planet master for the layout; (2) the framing_prompt is the image-to-image / inpaint instruction that makes the seed frame (best-of-4, keep one); (3) i2v from that frame with the row's `i2v_prompt`. Full prompts are in `shot_manifest_v2.json` → `composites[].framing_prompt` (verbatim); the table lists the shot-specific part.\n")
w("| C-id | shot | beat | views | set / planet | props | framing (shot-specific sentence) |\n|---|---|---|---|---|---|---|")
for c in comps:
    fs = c["framing_prompt"].replace(ART_STYLE + " ", "")
    for ch in c["characters"]: fs = fs.replace(ANCHORS[ch] + " ", "")
    fs = fs.replace(" " + NEG, "")
    w(f"| `{c['id']}` | {c['shot']} | {c['beat']} | {', '.join(c['views']) or '—'} | {c['set_master'] or ''}{' / ' if c['set_master'] and c['planet_master'] else ''}{c['planet_master'] or ''} | {', '.join(c['props']) or '—'} | {fs.replace('|','/')} |")
w("\n### Worked example (full prompt, verbatim from the manifest)\n")
ex = CID[byid[v1_to_new["S002"]]["composite_seed_id"]]
w(f"`{ex['id']}` for shot {ex['shot']}:\n"); w("```text\n" + ex["framing_prompt"] + "\n```")
use = collections.Counter()
for r in final:
    for sm in r["seed_masters"]: use[sm] += 1
w("\n---\n\n# Master usage across the shot manifest (v2, all 23 referenced)\n")
w("| master / view | shots referencing |\n|---|---|")
for k, v in sorted(use.items(), key=lambda x: -x[1]): w(f"| `{k}` | {v} |")
open(OUT + "/SEED_PROMPTS_v2.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("wrote shot_manifest_v2.json + SEED_PROMPTS_v2.md")
sys.exit(1 if errs else 0)
