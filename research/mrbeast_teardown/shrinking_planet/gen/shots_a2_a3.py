from shots_hook_a1 import S
SHOTS=[]
A=SHOTS.append
# ---------- ACT 2 (32 unique) ----------
A(S("B12",["ORB"],"gruff_cave","ORB arrival at the cave mouth, high angle looking down",["M_ORB_front","M_SET_gruff_cave","M_PLANET_300"],"WS",
 "Camera locked high, looking down at the cave mouth. ORB descends into frame from above, halo bright, and hovers at the entrance; moss glow reacts with a brightening pulse.",6,key="orb_arrival_cave"))
A(S("B12",[],"orbit","small wedge ejection, planet 500 to 300, new angle from below the equator",["M_PLANET_500","M_PLANET_300"],"HERO",
 "Camera locked below the equator looking up. A narrower seam of light draws across the top of the planet, a smaller wedge lifts off and drifts up and away with a spray of dust, the remainder settling; debris crosses the foreground.",8,key="wedge_small_hero"))
A(S("B12",["COUNT"],"equator","THE COUNT upgrade gag: thrusters ignite, cube wobbles then zips",["M_COUNT_expr","M_PLANET_300"],"INS",
 "Camera locked. THE COUNT sits on the rock; four thrusters sputter, ignite, it lifts unevenly, tilts twenty degrees, antenna whipping, then zips out of frame right leaving a puff.",6,key="count_upgrade_gag"))
A(S("B12",[],"gruff_cave","moon-rock heart insert outside the cave",["M_SET_gruff_cave"],"INS",
 "Camera locked macro. A heart shape of small pale moon rocks on the ground outside the cave; a shadow of a large figure passes over it and stops; nothing else moves; moss glow breathes.",5,key="moonrock_heart"))
A(S("B12",["PIP","GRUFF"],"gruff_cave","2-shot at the cave mouth, PIP noticing the rocks",["M_PIP_3q","M_GRUFF_3q","M_SET_gruff_cave"],"MS",
 "Camera locked. GRUFF stands in the cave mouth pretending to fix the goggle; PIP glances down at the ground, fronds curl gently at the tips, she looks at him; he does not look back.",6,key="cave_mouth_2shot"))
A(S("B12",["ORB"],"orbit","ORB medium against the 300 m planet, halo at announcer flare",["M_ORB_3q","M_PLANET_300"],"MS",
 "Camera locked. ORB hovers beside the smaller planet; the halo flares wide then settles into a steady speaking pulse; the lens-eye tracks slowly left to right.",5,key="orb_300_announce"))
A(S("B13",["PIP","GRUFF"],"equator","2-shot at the plasma vent, orange firelight, wide",["M_PIP_3q","M_GRUFF_3q","M_PLANET_300"],"WS",
 "Camera locked. The two sit either side of a plasma vent whose orange jet flickers and throws moving light on both; PIP hugs her knees; GRUFF pokes the vent with a rock; embers drift up into black.",8,key="vent_2shot_wide"))
A(S("B13",["PIP"],"equator","PIP close-up firelit, fronds drooped, confessing",["M_PIP_front","M_PLANET_300"],"CU",
 "Camera locked (slow push-in done in post). Orange firelight flickers on PIP's face; she speaks slowly with small mouth movements, fronds drooping, eyes on the fire, then up.",8,key="pip_cu_firelit",mouth=["PIP"]))
A(S("B13",["GRUFF"],"equator","GRUFF close-up firelit, brows lifted, tender",["M_GRUFF_expr","M_PLANET_300"],"CU",
 "Camera locked. Firelight moves across GRUFF's fur; brows lift, fur parts softly as he speaks two short lines; a long still hold, one blink.",8,key="gruff_cu_firelit"))
A(S("B13",[],"orbit","starfield time-lapse over the tiny horizon, vent glow at the edge",["M_PLANET_300"],"WS",
 "Camera locked. Stars wheel fast across the sky above a sharply curved horizon; the vent's orange glow at the edge pulses; two still silhouettes stay fixed.",6,key="starfield_timelapse"))
A(S("B13",["PIP"],"equator","PIP close-up firelit, second angle, asking",["M_PIP_3q","M_PLANET_300"],"CU",
 "Camera locked three-quarter. PIP turns her head toward GRUFF, mouth moves for a short question, fronds lift a little in hope, then hold.",5,key="pip_cu_firelit_B",mouth=["PIP"]))
A(S("B13",["PIP","GRUFF"],"equator","2-shot at the vent from behind, backs to camera, silence",["M_PIP_3q","M_GRUFF_3q","M_PLANET_300"],"MS",
 "Camera locked behind them. Two backs against the vent glow; GRUFF's fur rises and falls with a breath; PIP leans a few centimetres toward him and stops; embers drift.",6,key="vent_2shot_backs"))
A(S("B14",["GRUFF"],"equator","GRUFF crisis medium, squinting at a horizon 30 m away",["M_GRUFF_front","M_PLANET_300"],"MS",
 "Camera locked. GRUFF shades his eyes with a hand and stares at a horizon far too close, turns a full circle looking, brows knotted, and lets the hand drop.",6,key="gruff_crisis_stare"))
A(S("B14",["GRUFF"],"equator","HERO: continuous tracking lap around the whole planet (to be sped 2x)",["M_GRUFF_3q","M_PLANET_300"],"HERO",
 "Camera tracks alongside GRUFF at a steady pace as he walks; the horizon rolls continuously under him, the vent, the crate and the cave mouth pass behind him in turn, and he arrives back at the same vent where he started. Continuous, no cuts.",10,key="gruff_lap_hero"))
A(S("B14",["GRUFF"],"equator","GRUFF arriving back where he started, stopping, looking at the ground",["M_GRUFF_front","M_PLANET_300"],"WS",
 "Camera locked. GRUFF walks into frame, slows, stops at his own footprints, looks down, looks up at the black sky, and sits heavily.",5,key="gruff_lap_end"))
A(S("B14",["GRUFF"],"confessional","GRUFF confessional, cyan booth, profile angle, head down",["M_GRUFF_3q","M_SET_confessional"],"CU",
 "Camera locked in profile. GRUFF's head hangs; he says a short line, fur barely moving; the cyan strip light flickers once; he does not look up.",5,key="gruff_conf_C_profile"))
A(S("B15",[],"orbit","HERO: hologram glass dome with garden unfolding over the planet",["M_PLANET_300"],"HERO",
 "Camera locked in orbit. A translucent hologram of a glass dome blooms over the planet's top, trees and grass sketching themselves inside in lines of light, birds of light circling, the dome glowing pale green then holding.",8,key="dome_hologram_hero"))
A(S("B15",["ORB","PIP","GRUFF"],"landing_pad","platter 3-shot from behind ORB, contestants facing the dome light",["M_ORB_3q","M_PIP_front","M_GRUFF_front","M_SET_pad"],"OTS",
 "Camera locked behind ORB. Pale green light from above washes over PIP and GRUFF; GRUFF's brows lift, mouth-fur parts; PIP's fronds rise then slowly flatten as she decides.",6,key="dome_ots_3shot"))
A(S("B15",["PIP"],"landing_pad","PIP close-up, quiet refusal, low angle",["M_PIP_front","M_SET_pad"],"CU",
 "Camera locked low. PIP looks up at the dome light, eyes huge, then shakes her head once slowly with a single short word; fronds hold flat.",4,key="pip_cu_no",mouth=["PIP"]))
A(S("B15",["PIP","GRUFF","ORB"],"landing_pad","wide 3-shot under the timer, high angle from the dome",["M_PIP_front","M_GRUFF_front","M_ORB_front","M_SET_pad","M_PLANET_300"],"WS",
 "Camera locked high, as if from inside the dome. Three figures on the pad; GRUFF shifts from foot to foot, looks at PIP, looks up; ORB's halo ticks in short pulses; the green light fades out over the clip.",8,key="timer_wide_high"))
A(S("B15",["GRUFF"],"landing_pad","GRUFF sulking close-up, brows low, looking up at where the dome was",["M_GRUFF_expr","M_SET_pad"],"CU",
 "Camera locked. GRUFF's brows drop, fur sags, he looks up at the empty sky, exhales through the fur, mutters, looks at PIP off-frame.",5,key="gruff_sulk_cu"))
A(S("B15",["ORB"],"landing_pad","ORB close-up tilted, teasing, halo dim pulse",["M_ORB_3q","M_SET_pad"],"CU",
 "Camera locked. ORB tilts its lens-eye toward the crate off-frame, halo giving one slow dim pulse, then rotates back to camera; the starfield reflection slides.",4,key="orb_cu_tease"))
A(S("B15",["PIP"],"confessional","PIP confessional, magenta booth, high angle, small",["M_PIP_front","M_SET_confessional"],"MS",
 "Camera locked from above. PIP sits small on the stool, fronds drooping, picks at the scarf, looks up at the lens briefly and back down; she does not speak.",5,key="pip_conf_C_high"))
A(S("B15",[],"landing_pad","crate hero re-use (non-adjacent)",["M_SET_pad"],"HERO","",3,ins="crate_hero_arc",loops=["crate:FEED"]))
A(S("B16",[],"pip_camp","breakfast insert: ration bars arranged as a heart on a tin plate",["M_SET_pip_camp"],"INS",
 "Camera locked macro. A tin plate with ration bars laid in a heart; a small magenta hand places the last bar to close the shape, straightens it, withdraws.",5,key="breakfast_heart_insert"))
A(S("B16",["PIP","GRUFF"],"pip_camp","2-shot over the plate, GRUFF looking down at it, PIP watching him",["M_PIP_3q","M_GRUFF_3q","M_SET_pip_camp"],"MS",
 "Camera locked over the plate. GRUFF looks down at the heart, brows lift, fur parts as he says one word; PIP nods once, fronds curl at the tips; a beat of stillness.",6,key="breakfast_2shot",mouth=["PIP"],loops=["riff:OPEN"]))
A(S("B16",["GRUFF"],"gruff_cave","GRUFF reading close-up, paperback held up (cover blank for composite)",["M_GRUFF_front","M_SET_gruff_cave"],"CU",
 "Camera locked. GRUFF holds a battered paperback with a blank cover close to his face, brows working, turns a page carefully with a huge hand, licks a claw, turns another.",6,key="gruff_reading_cu"))
A(S("B16",["GRUFF"],"gruff_cave","GRUFF taking notes, wide inside the cave, book on knee",["M_GRUFF_3q","M_SET_gruff_cave"],"WS",
 "Camera locked wide. GRUFF sits on the ledge with the book on one knee, scratching notes onto a flat rock with a claw, pausing to re-read, nodding.",5,key="gruff_notes_wide"))
A(S("B16",["PIP"],"pip_camp","PIP watching from her tent flap, curious, fronds curled",["M_PIP_expr","M_SET_pip_camp"],"MS",
 "Camera locked. PIP peeks around the tent flap, fronds curling, eyes tracking something off-frame, a small tilt of the head; she ducks back.",4,key="pip_peek_tent"))
A(S("B17",[],"equator","goggle macro: the cracked brass goggle on GRUFF's forehead, firelight",["M_GRUFF_front","M_PLANET_300"],"INS",
 "Camera locked macro on the cracked brass goggle; firelight moves in the lens; a large furred finger enters and touches the crack gently, then withdraws.",5,key="goggle_macro",loops=["goggle:OPEN"]))
A(S("B17",["PIP","GRUFF"],"equator","2-shot at the vent, new low side angle, GRUFF touching the goggle",["M_PIP_3q","M_GRUFF_3q","M_PLANET_300"],"MS",
 "Camera locked low from the side. GRUFF's hand rises to the goggle and rests there; he speaks slowly, fur moving; PIP leans in, fronds lifted; the vent flickers.",6,key="vent_2shot_low_side"))
A(S("B17",["PIP"],"confessional","PIP confessional, magenta booth, tight on eyes",["M_PIP_front","M_SET_confessional"],"ECU",
 "Camera locked very tight on PIP's eyes and fronds; the fronds lift slowly; the eyes flick to one side as if remembering; one blink.",4,key="pip_conf_D_eyes"))
A(S("B17",["GRUFF"],"equator","GRUFF profile against the black sky, hand still on the goggle",["M_GRUFF_3q","M_PLANET_300"],"MS",
 "Camera locked in profile. GRUFF stares at the horizon, hand on the goggle, then lets the hand fall and turns his head slightly away from PIP off-frame.",5,key="gruff_profile_goggle"))
# ---------- ACT 3 (20 unique) ----------
A(S("B18",["ORB","PIP","GRUFF"],"landing_pad","five-platter wide, tray drones hovering in a row, all three",["M_ORB_front","M_PIP_front","M_GRUFF_front","M_SET_pad","M_PLANET_25"],"WS",
 "Camera locked wide. Five tray drones hover in a row holding five silver cloches; ORB drifts along the row right to left, halo pulsing; PIP and GRUFF stand at the end, GRUFF shifting his weight.",8,key="five_platters_wide"))
A(S("B18",[],"landing_pad","lid-lift insert A: cloche rising to reveal a small glowing card",["M_SET_pad"],"INS",
 "Camera locked at platter height. A tray drone's arm lifts the cloche straight up revealing a small blank glowing card; light spills; the cloche exits top of frame.",4,key="lid_lift_A"))
A(S("B18",["PIP","GRUFF"],"landing_pad","debate 2-shot, tight, heads turning between platters",["M_PIP_3q","M_GRUFF_3q","M_SET_pad"],"MS",
 "Camera locked. Both heads turn together from one platter to the next, GRUFF's brows working, PIP's fronds twitching; GRUFF shakes his head at the first, then the second.",6,key="debate_2shot_platters"))
A(S("B18",[],"landing_pad","lid-lift insert B: cloche rising, re-lit from the side (different platter)",["M_SET_pad"],"INS",
 "Camera locked slightly lower with a hard side light. A cloche lifts revealing a small dark rock model on the tray; a puff of dust; the cloche exits frame left.",4,key="lid_lift_B"))
A(S("B18",["GRUFF"],"landing_pad","GRUFF close-up 'Take it', brows up, decisive",["M_GRUFF_expr","M_SET_pad"],"CU",
 "Camera locked. GRUFF's brows shoot up, fur parts for two short words, he nods once hard; the goggle glints.",3,key="gruff_cu_take_it"))
A(S("B18",["PIP"],"landing_pad","PIP close-up 'Take it', fronds forward",["M_PIP_front","M_SET_pad"],"CU",
 "Camera locked. PIP says two short words with a small firm mouth movement, fronds push forward, eyes on ORB off-frame.",3,key="pip_cu_take_it",mouth=["PIP"]))
A(S("B18",["ORB"],"landing_pad","the #4 reveal: ORB lifting the fourth cloche, slow push (post)",["M_ORB_3q","M_SET_pad"],"MS",
 "Camera locked. ORB hovers beside the fourth platter; a tray drone lifts the cloche slowly to reveal an empty tray; ORB's halo dims to a thin line; nothing else moves for the rest of the clip.",6,key="reveal_platter4"))
A(S("B18",["PIP","GRUFF"],"landing_pad","2-shot stunned, both staring at the empty tray",["M_PIP_expr","M_GRUFF_expr","M_SET_pad"],"MS",
 "Camera locked. Both stare at the off-frame tray; PIP's fronds droop slowly; GRUFF's brows lower; GRUFF's hand goes to the goggle; neither speaks.",5,key="stunned_2shot"))
A(S("B18",[],"orbit","HERO: big wedge ejection 300 to 25 m, seen from the pad looking up as the sky tears",["M_SET_pad","M_PLANET_300","M_PLANET_25"],"HERO",
 "Camera locked on the pad looking up. A seam of light races across the rock overhead, the whole far side of the planet tears away above them and drifts off into black space with a storm of dust and pebbles streaming past the lens; the remaining rock shudders and settles into a small boulder.",10,key="wedge_big_hero_ground"))
A(S("B18",["COUNT"],"landing_pad","THE COUNT insert, rotating to show a fresh face",["M_COUNT_3q","M_SET_pad"],"INS",
 "Camera locked. THE COUNT rotates ninety degrees on its vertical axis to present a fresh blank face, antenna wobbling, thrusters correcting; it settles square.",4,key="count_rotate"))
A(S("B19",[],"landing_pad","crate doors opening with light, low angle",["M_SET_pad","M_PLANET_25"],"HERO",
 "Camera locked low. The sealed crate's two doors unseal with a hiss of dust, swing open slowly and a warm white light floods out, flaring the lens; the question-mark plate splits in half.",6,key="crate_opens",loops=["crate:PAY"]))
A(S("B19",[],"landing_pad","ticket macro: two blank glowing tickets on a velvet tray",["M_SET_pad"],"INS",
 "Camera locked macro. Two blank glowing tickets on a tray; a small magenta hand lifts one, trembling slightly; light plays across it.",4,key="ticket_macro"))
A(S("B19",["PIP"],"landing_pad","PIP sobbing close-up, new angle from below, crate light on her",["M_PIP_expr","M_SET_pad"],"CU",
 "Camera locked from below. Warm crate light on PIP's face; her fronds droop and shake; she covers her mouth with both hands; eyes overflow.",6,key="pip_sob_cu"))
A(S("B19",["PIP","GRUFF"],"landing_pad","2-shot hug, wide, PIP lost in GRUFF's fur",["M_PIP_3q","M_GRUFF_3q","M_SET_pad","M_PLANET_25"],"WS",
 "Camera locked. PIP runs three steps and disappears into GRUFF's chest fur; his arms close around her slowly; his brows lift; the crate light dims behind them.",6,key="hug_wide"))
A(S("B20",[],"orbit","house-sized 25 m planet from orbit, slow drift around it",["M_PLANET_25"],"WS",
 "Camera drifts slowly around the house-sized rock, revealing the crate, the tents and the red ring on its top, harsh sunlight sweeping across; stars fixed.",6,key="planet_25_orbit"))
A(S("B20",["PIP","GRUFF"],"equator","ground-level 2-shot bumping shoulders on a tiny surface",["M_PIP_3q","M_GRUFF_3q","M_PLANET_25"],"MS",
 "Camera locked at ground level. PIP and GRUFF try to walk in opposite directions, the tether snaps taut, they bump shoulders, GRUFF rocks back, PIP steadies herself on his arm; the horizon is a few metres away.",6,key="shoulder_bump_2shot",mouth=["PIP"]))
A(S("B20",["ORB"],"orbit","ORB close-up, halo bright, delivering 'It can'",["M_ORB_front","M_PLANET_25"],"CU",
 "Camera locked. ORB's halo brightens sharply on a single beat and holds; the lens-eye narrows; the tiny planet turns behind it.",3,key="orb_cu_it_can"))
A(S("B20",["GRUFF"],"equator","toilet gag re-crop re-use (non-adjacent to itself)",["M_GRUFF_3q","M_PLANET_1000"],"WS","",2,ins="toilet_gag"))
A(S("B21",["ORB"],"landing_pad","ORB low-angle arrival, dropping to eye level, halo dead then igniting",["M_ORB_front","M_SET_pad","M_PLANET_25"],"MS",
 "Camera locked very low. ORB drops into frame with its halo completely dark, stops at eye level, and the halo ignites in one hard pulse; dust lifts off the pad.",5,key="orb_low_arrival_flip"))
A(S("B21",[],"landing_pad","key-under-platter macro: a heavy brass launch key on a red cloth",["M_SET_pad"],"INS",
 "Camera locked macro. A cloche lifts revealing a heavy brass launch key on red cloth; the key rocks once and settles with a glint; nothing else moves.",4,key="launch_key_macro",loops=["launch:OPEN"]))
A(S("B21",[],"pod_door","escape pod door glowing red, one seat visible through the porthole",["M_SET_pod_door","M_PLANET_25"],"WS",
 "Camera locked. The pod door's red light strip pulses slowly; the single seat inside is lit by a swinging interior lamp; a thin vapour vents from the seal and drifts away.",6,key="pod_door_red"))
A(S("B21",["PIP"],"landing_pad","PIP reaction close-up to the flip, fronds frozen mid-flare",["M_PIP_expr","M_SET_pad"],"CU",
 "Camera locked. PIP's fronds stop mid-flare and hold rigid; eyes go to GRUFF off-frame and stay there; she swallows.",4,key="pip_react_flip"))
A(S("B21",["GRUFF"],"landing_pad","GRUFF reaction medium to the flip, looking at the key",["M_GRUFF_front","M_SET_pad"],"MS",
 "Camera locked. GRUFF's eyes drop to the key off-frame and stay there; brows flatten; fur goes completely still; one slow blink.",4,key="gruff_react_flip"))
A(S("B21",["ORB"],"landing_pad","ORB close-up tease re-use (non-adjacent) under the ladder graphic",["M_ORB_3q","M_SET_pad"],"CU","",3,ins="orb_cu_tease"))
