# (beat, chars, set, vantage, extra_seeds, shot_type, i2v_prompt, duration, key, insert_of, loops, mouth)
def S(beat,chars,set_,vantage,seeds,stype,prompt,dur=6,key=None,ins=None,loops=(),mouth=()):
    return dict(beat=beat,chars=list(chars),set=set_,vantage=vantage,seeds=list(seeds),stype=stype,prompt=prompt,dur=dur,key=key,ins=ins,loops=list(loops),mouth=list(mouth))

SHOTS=[]
A=SHOTS.append
# ---------- HOOK (14 unique) ----------
A(S("B01",["ORB"],"landing_pad","ORB extreme close-up lens-eye fills frame",["M_ORB_front","M_SET_pad"],"ECU",
 "Camera locked. The halo brightens in two short pulses as if speaking, the lens iris tightens slightly, a faint drift of the sphere up and down by a few centimetres. Nothing else moves.",4,key="orb_ecu_hello"))
A(S("B01",["PIP","GRUFF","ORB"],"landing_pad","wide 3-shot low angle on the pad",["M_PIP_front","M_GRUFF_front","M_ORB_3q","M_SET_pad","M_PLANET_1000"],"WS",
 "Camera locked low and wide. Both contestants lift bubble helmets off their heads in one motion and lower them to their sides; PIP's fronds spring up as the helmet clears; GRUFF shakes his fur once. ORB hovers between them, halo pulsing on speech. Faint dust drifts off the pad. Hold the wide the entire clip (punch-ins are done in post).",10,key="pad_wide_A"))
A(S("B01",["PIP","GRUFF"],"landing_pad","tight 2-shot chest-up on the crate",["M_PIP_3q","M_GRUFF_3q","M_SET_pad"],"MS",
 "Camera locked. A slow bloom of warm light rises from the crate's question-mark plate between them; PIP glances down at it, GRUFF looks away over his shoulder. Subtle breathing, fronds settle.",6,key="crate_bloom_2shot",loops=["crate:OPEN"]))
A(S("B02",["PIP"],"pip_camp","PIP close-up at camp, mouth open in surprise",["M_PIP_expr","M_SET_pip_camp"],"CU",
 "Camera locked. PIP's eyes widen further, fronds lift slowly outward, the mouth stays open; a tiny blink at the end. Camp lamp flickers once behind her.",6,key="pip_cu_surprise",mouth=["PIP"]))
A(S("B02",["GRUFF"],"gruff_cave","GRUFF close-up in the cave mouth, brows knotted",["M_GRUFF_expr","M_SET_gruff_cave"],"CU",
 "Camera locked. GRUFF's brows lower and knot, fur bristles around the mouth region, one slow exhale moves the fur, the goggle catches a passing highlight. Moss glow breathes behind him.",6,key="gruff_cu_scowl"))
A(S("B02",["ORB"],"pip_camp","insert: coiled tether on rock, ORB hovering above",["M_ORB_3q","M_SET_pip_camp"],"INS",
 "Camera locked on the coiled silver tether. ORB drifts down into frame from the top, halo dim, and settles in a slow hover; the tether's anklet ring rocks once as if nudged. Dust motes.",6,key="tether_insert"))
A(S("B03",["ORB","GRUFF"],"landing_pad","over-the-shoulder past ORB to GRUFF",["M_ORB_3q","M_GRUFF_front","M_SET_pad"],"OTS",
 "Camera locked over ORB's chrome curve. GRUFF's fur bristles outward as he speaks, brows drop, he leans in ten centimetres and back. ORB's halo pulses in reply.",6,key="ots_orb_gruff"))
A(S("B03",["PIP"],"landing_pad","PIP close-up against the crate, bright",["M_PIP_front","M_SET_pad"],"CU",
 "Camera locked. PIP answers quickly with a small mouth movement, fronds bounce once, then she laughs — head tips back a few degrees, fronds curl at the tips, eyes squint.",6,key="pip_cu_laugh",mouth=["PIP"]))
A(S("B03",["ORB","GRUFF"],"landing_pad","punch-in on the OTS (post re-crop 1.6x)",["M_ORB_3q","M_GRUFF_front","M_SET_pad"],"OTS",
 "",2,ins="ots_orb_gruff"))
A(S("B03",["PIP"],"landing_pad","PIP laugh re-use (non-adjacent)",["M_PIP_front","M_SET_pad"],"CU","",2,ins="pip_cu_laugh",mouth=["PIP"]))
A(S("B04",["PIP","GRUFF","ORB"],"landing_pad","wide 3-shot high angle, halo flare",["M_PIP_front","M_GRUFF_front","M_ORB_front","M_SET_pad"],"WS",
 "Camera locked from slightly above. ORB's halo flares into a wide starburst and holds, throwing gold light across both contestants; PIP steps back half a pace; GRUFF folds his arms. Pad lights brighten in sync with the flare.",6,key="pad_wide_B_flare"))
A(S("B04",["GRUFF","ORB"],"landing_pad","side-angle GRUFF medium, ORB drifting out of foreground",["M_GRUFF_3q","M_ORB_3q","M_SET_pad"],"MS",
 "Camera locked in profile. ORB drifts out of the foreground to the right, defocusing; GRUFF bends and snaps an anklet shut on his leg with a sharp jerk, then straightens and rolls his shoulders.",6,key="gruff_anklet_side"))
A(S("B04",["PIP","GRUFF"],"landing_pad","2-shot on the anklets, ground level",["M_PIP_3q","M_GRUFF_3q","M_SET_pad"],"INS",
 "Camera locked at ankle height. GRUFF's locked anklet sits still in the foreground; PIP's foot enters, she hesitates, then the anklet snaps closed with a small burst of dust and a brief motion-blur of the clasp. Tether cable tightens once.",6,key="anklet_click_2shot"))
A(S("B04",["GRUFF"],"gruff_cave","GRUFF smirk close-up re-use",["M_GRUFF_expr","M_SET_gruff_cave"],"CU","",1,ins="gruff_cu_scowl"))
A(S("B04",["PIP"],"pip_camp","PIP close-up re-use (surprise)",["M_PIP_expr","M_SET_pip_camp"],"CU","",1,ins="pip_cu_surprise",mouth=["PIP"]))
A(S("B05",["PIP"],"landing_pad","whip-tilt from PIP's anklet up to her face",["M_PIP_front","M_SET_pad"],"CU",
 "Camera starts on the locked anklet then tilts up fast along the body to PIP's face in half a second and settles; PIP's fronds are flat, eyes locked forward, no smile.",4,key="pip_whip_tilt"))
A(S("B05",["PIP","GRUFF","ORB"],"landing_pad","landing-pad wide, red ring in full, all three",["M_PIP_front","M_GRUFF_front","M_ORB_front","M_SET_pad","M_PLANET_1000"],"WS",
 "Camera locked wide with the red ring filling the lower third. ORB drifts backward toward the ring's edge while its halo pulses; PIP and GRUFF stand still, GRUFF's fur moving in a faint breeze, PIP's scarf lifting.",6,key="pad_wide_C_ring"))
A(S("B05",["ORB"],"landing_pad","ORB close-up, halo pulse, rock behind",["M_ORB_front","M_SET_pad"],"CU",
 "Camera locked. ORB's halo pulses in speech rhythm then dims; the lens-eye tilts down toward the two off-screen contestants, then straight back at camera; the starfield reflection slides across the chrome as it turns.",4,key="orb_cu_rule"))
A(S("B05",["ORB"],"orbit","ORB launch + continuous pull-out to full 1000 m planet",["M_ORB_3q","M_SET_pad","M_PLANET_1000"],"HERO",
 "Camera rides up with ORB: the sphere lifts off the pad and the camera pulls straight back and up, the pad and two tiny figures shrinking, the thin sky haze appearing as a rim, until the entire 1000-metre planet hangs as a marble in black space with ORB a chrome speck in the foreground. Smooth continuous acceleration, no cuts.",10,key="orbit_pullout_hero"))

# ---------- ACT 1 (40 unique) ----------
A(S("B06",[],"orbit","orbital push-in from space onto the north pole camp",["M_PLANET_1000","M_SET_pip_camp"],"HERO",
 "Camera dives from orbit toward the planet's north pole, the sky haze thickening as it passes through, settling on a slow glide over the magenta tent. Stars streak slightly then stabilise.",8,key="orbit_pushin_camp"))
A(S("B06",["PIP"],"pip_camp","PIP camp medium, unpacking",["M_PIP_3q","M_SET_pip_camp"],"MS",
 "Camera locked. PIP pulls a ration crate open, lays three bars in a neat row, straightens the scarf, looks up at the curved horizon and sighs; fronds settle.",6,key="pip_camp_unpack"))
A(S("B06",[],"orbit","orbital glide over the south pole cave",["M_PLANET_1000","M_SET_gruff_cave"],"WS",
 "Camera glides low over the south pole toward the cave mouth, moss glow growing brighter as it approaches, slow steady speed.",6,key="orbit_glide_cave"))
A(S("B06",["GRUFF"],"gruff_cave","GRUFF cave interior wide, settling in",["M_GRUFF_front","M_SET_gruff_cave"],"WS",
 "Camera locked inside the cave. GRUFF ducks under the entrance, thumps down onto the ledge, stacks two moon rocks, then lies back with one arm behind his head. Moss glow breathes.",6,key="gruff_cave_settle"))
A(S("B06",["COUNT"],"equator","THE COUNT insert, drifting past camera left to right",["M_COUNT_3q","M_PLANET_1000"],"INS",
 "Camera locked. THE COUNT hovers in from frame left, thrusters puffing, antenna wobbling, its display faces blank and steady (digits composited later), and drifts out frame right. Faint horizon behind.",6,key="count_drift_LR"))
A(S("B06",["GRUFF"],"equator","toilet gag: low wide, a hole in the rock with the horizon and stars",["M_GRUFF_3q","M_PLANET_1000"],"WS",
 "Camera locked low. GRUFF walks into frame, looks down at the hole, looks up at the stars, looks at the camera, and slowly sits; fur puffs. The horizon curves sharply behind him.",6,key="toilet_gag"))
A(S("B06",[],"landing_pad","crate hero: slow orbit around the sealed crate on the pad",["M_SET_pad"],"HERO",
 "Camera arcs slowly around the sealed crate, the raised question-mark plate catching light as the angle changes; pad lights blink in sequence; a thin dust haze drifts. Full 90-degree arc over the clip.",8,key="crate_hero_arc",loops=["crate:OPEN"]))
A(S("B06",["PIP","GRUFF"],"equator","2-shot walking the equator, tracking alongside",["M_PIP_3q","M_GRUFF_3q","M_PLANET_1000"],"MS",
 "Camera tracks sideways at walking pace. PIP walks ahead with quick steps, GRUFF lumbers three metres behind with the tether slack between them; the horizon rolls under their feet; neither looks at the other.",6,key="equator_walk_2shot"))
A(S("B06",["COUNT"],"equator","THE COUNT insert re-use (non-adjacent)",["M_COUNT_3q","M_PLANET_1000"],"INS","",2,ins="count_drift_LR"))
A(S("B07",["PIP"],"confessional","PIP confessional close-up, magenta booth, straight on",["M_PIP_front","M_SET_confessional"],"CU",
 "Camera locked. PIP speaks with small mouth movements, fronds drooping slightly, eyes flick down then back to camera; magenta strip light steady.",6,key="pip_conf_A",mouth=["PIP"]))
A(S("B07",["GRUFF"],"confessional","GRUFF confessional medium, cyan booth, slightly high angle",["M_GRUFF_3q","M_SET_confessional"],"MS",
 "Camera locked from slightly above. GRUFF sits hunched, fur over the mouth shifting as he speaks, brows flat and cold, one hand rubs the goggle on his forehead.",6,key="gruff_conf_A"))
A(S("B07",["ORB"],"orbit","ORB hovering in orbit, planet behind, halo dims on 'It isn't'",["M_ORB_front","M_PLANET_1000"],"MS",
 "Camera locked. ORB hovers with the planet large behind it; the halo pulses twice then drops to almost nothing; the lens-eye slowly turns to face camera dead-on.",6,key="orb_orbit_hover"))
A(S("B07",[],"equator","flash-forward card plate: rock dust storm, no characters",["M_PLANET_25"],"INS",
 "Camera handheld shake. A storm of grey rock dust blows left to right across a black void, small pebbles tumbling, a red light pulsing somewhere behind the dust.",4,key="dust_storm_plate"))
A(S("B08",["PIP"],"pip_camp","sunrise over PIP's tent, sun cresting the horizon",["M_SET_pip_camp","M_PLANET_1000"],"WS",
 "Camera locked. A hard white sun rises fast over the curved horizon behind the tent, long shadows sweeping across the rock, haze glowing; the tent flap moves once.",6,key="sunrise_camp"))
A(S("B08",["GRUFF"],"gruff_cave","sunrise on the cave mouth, opposite hemisphere",["M_SET_gruff_cave","M_PLANET_1000"],"WS",
 "Camera locked outside the cave. Sunlight crawls down the cave mouth from top to bottom, moss glow fading as it brightens; GRUFF's silhouette stirs on the ledge inside.",6,key="sunrise_cave"))
A(S("B08",[],"orbit","orbital planet plate with slow rotation (diameter ring overlay in post)",["M_PLANET_1000"],"HERO",
 "Camera locked in orbit. The full planet rotates slowly, a quarter turn over the clip, haze rim glinting, stars fixed.",8,key="planet_1000_rotate"))
A(S("B08",["ORB"],"orbit","ORB three-quarter hover, drifting closer to lens",["M_ORB_3q","M_PLANET_1000"],"MS",
 "Camera locked. ORB drifts toward the lens over the clip, halo pulsing steadily as it narrates, the starfield reflection sliding; it stops just short of filling the frame.",6,key="orb_drift_closer"))
A(S("B08",["PIP","GRUFF"],"equator","extreme wide: two tiny figures on opposite sides of a ridge",["M_PIP_front","M_GRUFF_front","M_PLANET_1000"],"EWS",
 "Camera locked extremely wide. Two tiny figures stand on opposite sides of a ridge, each facing away; PIP kicks a pebble; GRUFF sits down. The horizon curves away; haze drifts.",6,key="ews_ridge_apart"))
A(S("B09",["ORB"],"landing_pad","ORB descending from orbit onto the pad, seen from ground",["M_ORB_front","M_SET_pad","M_PLANET_500"],"WS",
 "Camera locked low. ORB drops from the black sky into frame, decelerates, and settles into a hover a metre above the red ring; halo brightens as it arrives; pad lights wake.",6,key="orb_arrival_pad"))
A(S("B09",[],"landing_pad","tray drone landing with two covered platters, close",["M_SET_pad","M_COUNT_3q"],"INS",
 "Camera locked at platter height. A small tray drone lowers two silver cloches into frame and retreats; the cloches rock and settle; a highlight slides over the domes.",6,key="tray_drone_platters"))
A(S("B09",["PIP","GRUFF"],"landing_pad","deliberation 2-shot, eye level, heads together",["M_PIP_3q","M_GRUFF_3q","M_SET_pad"],"MS",
 "Camera locked. GRUFF mutters with fur moving, shrugs one shoulder; PIP looks at him, then at the platters, fronds twitching; she takes one small step forward.",6,key="deliberation_2shot"))
A(S("B09",["PIP"],"landing_pad","PIP close-up, decisive, chin up",["M_PIP_front","M_SET_pad"],"CU",
 "Camera locked. PIP lifts her chin, mouth moves for two short words, fronds flare briefly outward and hold; eyes steady.",4,key="pip_cu_halve_it",mouth=["PIP"]))
A(S("B09",[],"orbit","HERO: wedge shearing off the planet, seen from space",["M_PLANET_1000","M_PLANET_500"],"HERO",
 "Camera locked in orbit. A seam of white light draws around a third of the planet, the rock cracks along it with a burst of dust, and the whole wedge slides away from the sphere, tumbling slowly, leaving a raw flat face; debris drifts; the remaining planet settles.",10,key="wedge_shear_hero"))
A(S("B09",["PIP","GRUFF"],"equator","ground-level POV: old campsite drifting past their feet into space",["M_PIP_3q","M_GRUFF_3q","M_PLANET_500"],"POV",
 "Camera locked at ankle height looking past two sets of feet. The ground beyond a glowing seam drops away and slides sideways, a small tent and crate on it drifting off into black space, dust streaming across the frame toward the gap.",8,key="camp_drifts_away_pov"))
A(S("B09",["COUNT"],"landing_pad","THE COUNT insert, front face square, tilting as it updates",["M_COUNT_front","M_SET_pad"],"INS",
 "Camera locked. THE COUNT hovers square to camera, dips ten centimetres and rises, antenna wobbling, thrusters puffing once; the display faces stay blank (500 composited).",4,key="count_front_update"))
A(S("B09",[],"orbit","aftermath: half planet with sheared face, debris field, slow drift",["M_PLANET_500"],"WS",
 "Camera locked. The halved planet turns slowly showing its raw pale face; a field of small rocks drifts outward and thins; one large slab tumbles in the foreground.",6,key="planet_500_aftermath"))
A(S("B09",["GRUFF"],"landing_pad","GRUFF reaction medium, watching the wedge leave, fur blown",["M_GRUFF_front","M_SET_pad"],"MS",
 "Camera locked. GRUFF stares off-frame, fur streaming sideways in a rush of dust, brows lifted, one hand slowly rising to the goggle; he does not move otherwise.",6,key="gruff_watch_wedge"))
A(S("B09",["PIP"],"landing_pad","PIP re-use: decisive close-up (non-adjacent)",["M_PIP_front","M_SET_pad"],"CU","",2,ins="pip_cu_halve_it",mouth=["PIP"]))
A(S("B10",["PIP","GRUFF"],"equator","night wide: two tents sliding toward the same valley",["M_SET_pip_camp","M_PLANET_500"],"WS",
 "Camera locked wide at night. Two small tents on opposite slopes slowly slide down toward a shared valley floor, pegs popping loose, the tether cable dragging between them; stars wheel slowly overhead.",8,key="tents_slide_night"))
A(S("B10",["GRUFF"],"gruff_cave","snoring close-up: GRUFF asleep, fur puffing on each snore",["M_GRUFF_expr","M_SET_gruff_cave"],"CU",
 "Camera locked. GRUFF asleep on the ledge; on each breath the fur over the mouth puffs outward and settles; the goggle slips a centimetre; a moss light flickers in time.",6,key="gruff_snore_cu"))
A(S("B10",["PIP"],"gruff_cave","PIP tiptoe POV into the dark cave, low lamp",["M_SET_gruff_cave"],"POV",
 "Handheld camera creeps forward into the cave at tiptoe pace, a small lamp bobbing, moss glow ahead, then the frame lurches and drops as if tripping over a cable.",6,key="pip_tiptoe_pov"))
A(S("B10",["PIP"],"gruff_cave","PIP sprawled after the trip, fronds over her eyes",["M_PIP_expr","M_SET_gruff_cave"],"MS",
 "Camera locked. PIP lies tangled in the tether cable, pushes her fronds off her eyes, looks toward the sleeping shape, freezes, then carefully backs away out of frame.",6,key="pip_tripped"))
A(S("B10",[],"gruff_cave","tally marks insert: claw scratching the sixth mark into rock",["M_SET_gruff_cave"],"INS",
 "Camera locked macro on rock. Five scratched tally marks; a large furred cyan hand enters and scratches a sixth, dust falling, then withdraws.",4,key="tally_insert"))
A(S("B10",["ORB"],"orbit","ORB wry hover over the valley, looking down",["M_ORB_3q","M_PLANET_500"],"MS",
 "Camera locked. ORB hovers tilted downward, halo pulsing dryly, then rolls its lens-eye up to camera and holds.",4,key="orb_wry_hover"))
A(S("B11",["PIP"],"confessional","PIP confessional, magenta booth, three-quarter angle, fronds flared",["M_PIP_3q","M_SET_confessional"],"CU",
 "Camera locked from a three-quarter angle. PIP speaks sharply, fronds flaring straight out, eyes narrow; she looks away from camera then snaps back.",6,key="pip_conf_B_angry",mouth=["PIP"]))
A(S("B11",["PIP","GRUFF"],"equator","handheld 2-shot argument in the valley, fronds flared",["M_PIP_expr","M_GRUFF_expr","M_PLANET_500"],"MS",
 "Handheld camera with slight drift. PIP faces GRUFF, fronds flared fully, gesturing once with a hand; GRUFF looms, fur bristling, brows knotted, leaning down toward her.",6,key="argument_2shot_A",mouth=["PIP"]))
A(S("B11",["GRUFF"],"equator","GRUFF low-angle medium, fur bristled, delivering",["M_GRUFF_expr","M_PLANET_500"],"MS",
 "Camera locked low. GRUFF's fur bristles outward in a wave as he speaks, brows knot, he straightens to full height and looks down at the lens.",6,key="gruff_low_bristle"))
A(S("B11",["PIP","GRUFF"],"equator","handheld 2-shot reverse side, fur bristled",["M_PIP_expr","M_GRUFF_expr","M_PLANET_500"],"MS",
 "Handheld camera from the opposite side. PIP shouts with a sharp forward step, one hand chopping the air; GRUFF turns his back on her mid-shot and walks two paces away, tether tightening.",6,key="argument_2shot_B",mouth=["PIP"]))
A(S("B11",["GRUFF"],"equator","GRUFF turning away, back to camera, walking to the horizon",["M_GRUFF_3q","M_PLANET_500"],"WS",
 "Camera locked. GRUFF walks away from the lens toward the sharply curved horizon, fur settling, shoulders dropping; he stops at the ridge and does not turn around.",6,key="gruff_walk_away"))
A(S("B11",["PIP"],"pip_camp","PIP crying close-up, fronds drooped, turned from camp",["M_PIP_expr","M_SET_pip_camp"],"CU",
 "Camera locked. PIP's fronds droop fully, eyes glisten, a tear runs; she wipes it with the scarf end and holds still, breathing.",6,key="pip_cry_cu"))
A(S("B11",[],"equator","truce insert: two hands on one ration bar",["M_PIP_3q","M_GRUFF_3q","M_PLANET_500"],"INS",
 "Camera locked macro. A small magenta hand holds out a ration bar; a large cyan-furred hand enters, pauses, then takes the other end; both hold it a moment; the bar snaps in half.",6,key="truce_ration_insert"))
A(S("B11",["GRUFF"],"confessional","GRUFF confessional, cyan booth, low angle, brows lifted",["M_GRUFF_front","M_SET_confessional"],"CU",
 "Camera locked low. GRUFF looks down at his hands then at the lens; the fur over his mouth shifts with a short word; brows lift slightly; a slow blink.",4,key="gruff_conf_B"))
A(S("B11",["PIP"],"pip_camp","PIP crying close-up re-use (non-adjacent)",["M_PIP_expr","M_SET_pip_camp"],"CU","",2,ins="pip_cry_cu"))
