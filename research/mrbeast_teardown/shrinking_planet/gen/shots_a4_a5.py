from shots_hook_a1 import S
SHOTS=[]
A=SHOTS.append
# ---------- ACT 4 (32 unique) ----------
A(S("B22",["ORB","PIP","GRUFF"],"truth_beam","truth-beam wide: the column of light between them, ORB above (grade green/red in post)",["M_SET_truth_beam","M_PIP_front","M_GRUFF_front","M_ORB_front","M_PLANET_25"],"WS",
 "Camera locked wide. The column of light hums with a slow vertical shimmer; PIP and GRUFF stand on the floor marks either side; ORB hovers above the column, halo pulsing; dust motes rise through the beam. Colour stays neutral (graded later).",8,key="beam_wide_neutral"))
A(S("B22",["GRUFF"],"truth_beam","GRUFF close-up inside the beam, light on fur",["M_GRUFF_front","M_SET_truth_beam"],"CU",
 "Camera locked. Beam light shimmers on GRUFF's fur; he speaks a short line, fur moving, brows steady; then a slow blink and stillness.",6,key="gruff_cu_beam"))
A(S("B22",["PIP"],"truth_beam","PIP close-up inside the beam, light on fronds",["M_PIP_front","M_SET_truth_beam"],"CU",
 "Camera locked. Beam light shimmers on PIP's fronds; she answers with one small mouth movement, eyes steady on the lens, fronds still; then a small exhale.",6,key="pip_cu_beam",mouth=["PIP"]))
A(S("B22",["ORB"],"truth_beam","ORB hover above the beam, new angle from below looking up the column",["M_ORB_3q","M_SET_truth_beam"],"MS",
 "Camera locked at the beam's base looking up. ORB hovers at the top of the column, halo pulsing in verdict rhythm, chrome catching the beam light; the column shimmers past the lens.",5,key="orb_above_beam"))
A(S("B22",["COUNT"],"truth_beam","THE COUNT 'malfunction' insert, dipping, one thruster sputtering",["M_COUNT_expr","M_SET_truth_beam"],"INS",
 "Camera locked. THE COUNT hovers beside the beam's projector drone; one thruster sputters, the cube dips and tilts, the antenna whips, it rights itself with a lurch.",5,key="count_malfunction"))
A(S("B22",["PIP"],"truth_beam","PIP asking close-up, three-quarter, fronds lifted",["M_PIP_3q","M_SET_truth_beam"],"CU",
 "Camera locked three-quarter. PIP turns to GRUFF off-frame, asks a short question with small mouth movement, fronds lift and hold; her eyes do not leave him.",5,key="pip_cu_ask_beam",mouth=["PIP"]))
A(S("B22",["GRUFF"],"truth_beam","GRUFF medium in the beam, flicker on fur, hand rising to goggle",["M_GRUFF_3q","M_SET_truth_beam"],"MS",
 "Camera locked. GRUFF answers slowly, fur moving, then the beam light flickers irregularly on his fur; his hand rises to the goggle and stops there.",6,key="gruff_ms_beam_flicker"))
A(S("B22",["PIP","GRUFF"],"truth_beam","2-shot reactions either side of the beam, split by the column",["M_PIP_expr","M_GRUFF_expr","M_SET_truth_beam"],"MS",
 "Camera locked with the column dividing the frame. PIP on the left looks up at the beam then at GRUFF; GRUFF on the right looks at the ground; the column shimmers between them.",6,key="beam_split_2shot"))
A(S("B22",["PIP"],"truth_beam","PIP close-up in beam re-use (second 'No', non-adjacent)",["M_PIP_front","M_SET_truth_beam"],"CU","",3,ins="pip_cu_beam",mouth=["PIP"],loops=["trust:OPEN"]))
A(S("B23",["GRUFF"],"pod_door","GRUFF alone at the pod door, red light on fur, key in fist, wide",["M_GRUFF_3q","M_SET_pod_door","M_PLANET_25"],"WS",
 "Camera locked. GRUFF stands before the red-lit pod door, key clenched in one fist; the red strip pulses on his fur; he looks over his shoulder toward the off-frame camp, then back at the door; his fist tightens.",8,key="gruff_pod_door_wide",loops=["launch:FEED"]))
A(S("B23",["GRUFF"],"pod_door","GRUFF close-up in red light, brows flat, cold",["M_GRUFF_expr","M_SET_pod_door"],"CU",
 "Camera locked. Red light pulses across GRUFF's face; brows flat and cold; fur moves as he speaks low; the pulse slows; his eyes narrow.",6,key="gruff_cu_red"))
A(S("B23",[],"landing_pad","launch key macro re-use (non-adjacent)",["M_SET_pad"],"INS","",2,ins="launch_key_macro"))
A(S("B23",["GRUFF"],"confessional","GRUFF confessional, cyan booth, straight on, close, dead-eyed",["M_GRUFF_front","M_SET_confessional"],"CU",
 "Camera locked straight on. GRUFF stares into the lens without blinking; fur barely moves for a low line; the cyan light steady; the clip ends on stillness.",5,key="gruff_conf_D_cold"))
A(S("B24",[],"orbit","two soundproof glass pods on the 12 m rock, wide from orbit",["M_PLANET_12"],"WS",
 "Camera drifts slowly past the bus-sized rock; two glass pods on top glow faintly, one magenta, one cyan; the pod door's red strip on the side; stars fixed.",6,key="pods_wide_orbit"))
A(S("B24",["PIP"],"confessional","PIP inside her glass pod, magenta light, side angle through the glass",["M_PIP_3q","M_SET_confessional"],"MS",
 "Camera locked outside the glass. PIP speaks inside, muffled, fronds drooping then rising as she reasons; her hand rests on the glass; reflections of stars drift on the pane.",6,key="pip_pod_side",mouth=["PIP"]))
A(S("B24",["ORB","GRUFF"],"confessional","ORB at the cyan pod glass, GRUFF inside, two-shot through the pane",["M_ORB_3q","M_GRUFF_front","M_SET_confessional"],"MS",
 "Camera locked. ORB hovers outside the cyan pod, halo pulsing with a question; inside, GRUFF's brows lift, his fur shifts for a slow non-answer, he looks away from the halo.",6,key="orb_gruff_pod",loops=["launch:FEED"]))
A(S("B24",["GRUFF"],"confessional","GRUFF close-up through the pod glass, reflections, brows lifted",["M_GRUFF_expr","M_SET_confessional"],"CU",
 "Camera locked tight through the glass. GRUFF's brows rise slowly; fur parts for two words; a reflected halo drifts across the pane; he holds still.",4,key="gruff_cu_pod_glass"))
A(S("B24",["COUNT"],"orbit","THE COUNT hovering beside the 12 m rock, from orbit, faces blank",["M_COUNT_front","M_PLANET_12"],"INS",
 "Camera locked. THE COUNT hovers beside the small rock, thrusters puffing to hold station, antenna wobbling, front face square and blank.",4,key="count_orbit_12"))
A(S("B25",[],"orbit","7 m planet from orbit (re-crop master), slow rotation",["M_PLANET_12"],"WS",
 "Camera locked. The small rock rotates slowly, the two glass pods and the pod door turning into and out of the light; a shadow line sweeps across.",5,key="planet_7_rotate"))
A(S("B25",["PIP","GRUFF"],"equator","tethered three-legged-race gag, ground level tracking",["M_PIP_3q","M_GRUFF_3q","M_PLANET_12"],"MS",
 "Camera tracks sideways at a stumble. PIP and GRUFF try to walk together on a rock too small for two, the tether wrapped around both legs, GRUFF taking one huge step for PIP's three, both stumble, GRUFF catches her by the scarf.",6,key="three_legged_gag"))
A(S("B25",["PIP","GRUFF"],"equator","high angle looking straight down on the two on a 7 m rock",["M_PIP_front","M_GRUFF_front","M_PLANET_12"],"WS",
 "Camera locked directly above. Two figures on a rock barely wider than GRUFF is tall; they shuffle in a circle trying to untangle the tether; black space all around.",5,key="topdown_7m"))
A(S("B25",["PIP"],"equator","PIP close-up exasperated, fronds half-flared, tether in hand",["M_PIP_expr","M_PLANET_12"],"CU",
 "Camera locked. PIP holds up a loop of tether, fronds half-flared, eyes rolling toward GRUFF off-frame, a sharp exhale; she drops the loop.",4,key="pip_cu_exasperated"))
A(S("B26",["PIP","GRUFF"],"orbit","HERO / THUMBNAIL: GRUFF standing taller than the 4 m planet, PIP at his feet, black space",["M_GRUFF_front","M_PIP_front","M_PLANET_4"],"HERO",
 "Camera locked at eye level with the rock. GRUFF stands on the small rock, head and shoulders above its top, fur drifting in slow motion; PIP at his feet looks up at him; the rock rotates almost imperceptibly; stars fixed; nothing else moves.",10,key="thumbnail_hero_4m"))
A(S("B26",[],"pod_door","lever-hand macro: a large furred hand resting on the red lever",["M_GRUFF_3q","M_SET_pod_door"],"INS",
 "Camera locked macro. A large cyan-furred hand rests on the brass lever; the red strip light pulses on the fur; the fingers tighten slightly then relax.",5,key="lever_hand_macro",loops=["launch:FEED"]))
A(S("B26",["GRUFF"],"pod_door","GRUFF low angle against black space, taller than the frame, looking down",["M_GRUFF_front","M_SET_pod_door","M_PLANET_4"],"MS",
 "Camera locked very low. GRUFF towers above, black space behind him, looks down at PIP off-frame, brows heavy; his hand off-frame is on the lever; his fur drifts; a slow blink.",6,key="gruff_towering_low"))
A(S("B26",["PIP"],"confessional","PIP confessional, magenta booth, three-quarter, worried",["M_PIP_3q","M_SET_confessional"],"CU",
 "Camera locked three-quarter. PIP speaks quietly with small mouth movements, fronds low, eyes down then up; she hugs her arms.",5,key="pip_conf_E_worried",mouth=["PIP"]))
A(S("B26",["PIP"],"orbit","PIP at GRUFF's feet, close, looking up at a wall of fur",["M_PIP_expr","M_GRUFF_front","M_PLANET_4"],"CU",
 "Camera locked at PIP's height. PIP looks up at a wall of cyan fur that fills the top of frame; her fronds droop; she puts a hand on the fur; the fur shifts as he breathes.",5,key="pip_looks_up_fur"))
A(S("B27",["PIP","GRUFF"],"orbit","2-shot on the 2 m rock, both bodies fill the frame, GRUFF confessing",["M_PIP_3q","M_GRUFF_3q","M_PLANET_2"],"MS",
 "Camera locked. Both crouch on the car-sized rock filling the frame; GRUFF speaks slowly, fur moving, eyes on the ground; PIP's fronds rise slowly as she listens; the rock turns barely.",8,key="secret_2shot_2m",loops=["goggle:PAY"]))
A(S("B27",[],"equator","goggle macro re-use (non-adjacent, firelight)",["M_GRUFF_front","M_PLANET_300"],"INS","",2,ins="goggle_macro"))
A(S("B27",["PIP"],"confessional","PIP confessional, magenta booth, straight on, hopeful",["M_PIP_front","M_SET_confessional"],"CU",
 "Camera locked. PIP looks into the lens, fronds lifting slowly all the way up, a small breath in, the beginning of a smile; she does not speak.",5,key="pip_conf_F_hope"))
A(S("B27",[],"orbit","clock install insert: a tray drone bolts a small clock housing onto the rock",["M_SET_pod_door","M_PLANET_2"],"INS",
 "Camera locked. A tray drone lowers a small dark clock housing onto the rock and bolts it with two quick sparks, then retreats; the housing's blank face (digits composited) lights up.",5,key="clock_install"))
A(S("B27",["GRUFF"],"orbit","GRUFF close-up on the 2 m rock, looking at PIP, brows soft",["M_GRUFF_expr","M_PLANET_2"],"CU",
 "Camera locked. GRUFF looks at PIP off-frame, brows soft, fur parting gently with a breath; his hand rises to the goggle, hesitates, and lowers.",5,key="gruff_cu_soft_2m"))
A(S("B28",["PIP","GRUFF"],"orbit","night wide: the car-sized rock in space, two shapes asleep against the crate",["M_PIP_3q","M_GRUFF_3q","M_PLANET_2"],"WS",
 "Camera locked wide. The tiny rock hangs in black space; two shapes lean asleep against the crate, GRUFF's fur rising and falling, PIP curled against him; the clock housing glows faintly; stars drift very slowly.",8,key="night_rock_asleep"))
A(S("B28",["PIP"],"orbit","PIP awake close-up in the dark, whispering",["M_PIP_front","M_PLANET_2"],"CU",
 "Camera locked. PIP's eyes open in the dark, she whispers with a tiny mouth movement, fronds flat, looks up at the black sky; a faint clock glow on her face.",5,key="pip_cu_night_whisper",mouth=["PIP"]))
A(S("B28",["GRUFF"],"confessional","GRUFF confessional, cyan booth, extreme close on eyes and goggle",["M_GRUFF_front","M_SET_confessional"],"ECU",
 "Camera locked extreme close. GRUFF's eyes and the cracked goggle; the eyes shift left, then to the lens; a long unblinking hold; the cyan light hums.",6,key="gruff_conf_E_ecu",loops=["launch:FEED"]))
A(S("B28",[],"pod_door","lever-hand macro re-use (non-adjacent)",["M_GRUFF_3q","M_SET_pod_door"],"INS","",2,ins="lever_hand_macro"))
# ---------- ACT 5 (14 unique) ----------
A(S("B29",[],"orbit","clock face insert plate: the housing on the rock, blank face for digit composite",["M_PLANET_2"],"INS",
 "Camera locked on the clock housing; its blank face glows; a faint vibration on each tick; a shadow of ORB passes over it.",4,key="clock_face_plate"))
A(S("B29",["ORB","PIP","GRUFF"],"truth_beam","truth-beam replay re-use (graded red flicker)",["M_SET_truth_beam","M_PIP_front","M_GRUFF_front","M_ORB_front","M_PLANET_25"],"WS","",2,ins="beam_wide_neutral",loops=["trust:PAY"]))
A(S("B29",["ORB"],"orbit","ORB hover over the 2 m rock, counting, halo pulsing on numbers",["M_ORB_front","M_PLANET_2"],"MS",
 "Camera locked. ORB hovers above the tiny rock; the halo pulses in sharp separate beats like spoken numbers; the lens-eye tilts down toward the lever off-frame.",6,key="orb_counting_hover"))
A(S("B29",["GRUFF"],"pod_door","GRUFF close-up sweating at the lever, red pulse fast",["M_GRUFF_expr","M_SET_pod_door"],"CU",
 "Camera locked. Red light pulses fast on GRUFF's face; beads of moisture on the fur; brows knotted; his jaw region tightens; eyes flick to the lever and back.",6,key="gruff_cu_sweat"))
A(S("B29",["PIP"],"orbit","PIP close-up watching him, fronds trembling",["M_PIP_expr","M_PLANET_2"],"CU",
 "Camera locked. PIP watches off-frame, fronds trembling, eyes wide; she does not blink; a small step forward at the end.",5,key="pip_cu_watching"))
A(S("B29",[],"pod_door","lever macro: the hand lifts OFF the lever",["M_GRUFF_3q","M_SET_pod_door"],"INS",
 "Camera locked macro. The large furred hand on the lever loosens, lifts slowly off, and hangs open in the air above it; the red light keeps pulsing.",5,key="hand_off_lever",loops=["launch:PAY"]))
A(S("B29",["PIP","GRUFF"],"orbit","2-shot on the 2 m rock, new angle from behind the lever, PIP grabbing his hand",["M_PIP_3q","M_GRUFF_3q","M_SET_pod_door","M_PLANET_2"],"MS",
 "Camera locked behind the lever. GRUFF's open hand hangs in the air; PIP reaches up with both hands and grabs it and holds; both freeze; only fur and fronds move.",6,key="hand_grab_2shot"))
A(S("B29",["PIP","GRUFF","ORB"],"orbit","extreme wide: the tiny rock, two figures, ORB above, total stillness for the silence",["M_PIP_front","M_GRUFF_front","M_ORB_front","M_PLANET_2"],"EWS",
 "Camera locked extremely wide. The car-sized rock in black space; two small figures holding hands; ORB a dot above; nothing moves for the whole clip except a slow star drift.",6,key="ews_stillness_2m"))
A(S("B29",[],"orbit","HERO: rescue ship rising over the horizon of the 2 m rock",["M_PLANET_2"],"HERO",
 "Camera locked low on the rock. A long grey rescue ship rises slowly from behind the rock's tiny horizon, running lights blinking, engines glowing blue, dust lifting off the rock as it passes overhead, until its hull fills the top of frame.",10,key="rescue_ship_hero"))
A(S("B29",["PIP","GRUFF"],"orbit","2-shot looking up at the ship, blue engine light on both faces",["M_PIP_expr","M_GRUFF_expr","M_PLANET_2"],"MS",
 "Camera locked. Blue light sweeps down over both faces from above; PIP's fronds rise all the way up; GRUFF's brows lift and his fur parts; both keep looking up.",5,key="looking_up_ship"))
A(S("B29",[],"orbit","clock face plate re-use (non-adjacent)",["M_PLANET_2"],"INS","",2,ins="clock_face_plate"))
A(S("B30",[],"orbit","anklet-release macro: the anklet clasps spring open",["M_PIP_3q","M_GRUFF_3q","M_PLANET_2"],"INS",
 "Camera locked macro at ankle height. Two anklets side by side; both clasps spring open with a small burst of light and fall away; the tether goes slack and drops.",4,key="anklet_release_macro"))
A(S("B30",["PIP","GRUFF","ORB"],"orbit","3-shot on the rock with the open crate between them, new angle from ship height",["M_PIP_front","M_GRUFF_front","M_ORB_3q","M_PLANET_2"],"WS",
 "Camera locked slightly above. The open crate glows between them; ORB hovers between the two, halo pulsing; PIP and GRUFF look at each other, then both look down at a ration tin on the rock.",6,key="crate_reveal_3shot"))
A(S("B30",["PIP","GRUFF"],"orbit","the riff on the ration tin, tight 2-shot on hands and tin",["M_PIP_3q","M_GRUFF_3q","M_PLANET_2"],"CU",
 "Camera locked tight. A small magenta hand and a large furred hand tap a ration tin in turn, four beats, the tin rocking; then both hands stop; the fronds and fur at the edge of frame lift.",5,key="riff_on_tin",loops=["riff:PAY"]))
A(S("B30",["ORB"],"orbit","ORB spinning in place, halo streaking, starfield reflection whirling",["M_ORB_front","M_PLANET_2"],"CU",
 "Camera locked. ORB spins on its vertical axis faster and faster, the halo streaking into a ring of light, the starfield reflection whirling, then stops dead facing the lens.",4,key="orb_spin"))
A(S("B31",["ORB"],"orbit","bookend pull-out: ORB rises from the 2 m rock until the rock is a dot",["M_ORB_3q","M_PLANET_2"],"HERO",
 "Camera rides up with ORB from the car-sized rock: the sphere lifts, the camera pulls straight back and up, the rock and its two tiny figures shrinking to a single grey dot in black space, ORB a chrome speck in the foreground, mirroring the opening pull-out. Smooth continuous acceleration, no cuts.",6,key="bookend_pullout_2m"))
