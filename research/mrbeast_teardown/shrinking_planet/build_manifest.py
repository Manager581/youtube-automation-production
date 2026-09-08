import json, math, re
OUT='/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet/shot_manifest_v1.json'

ART_STYLE=("Stylized 3D-animated creature feature, one locked look for every shot: painterly-realistic CG with soft subsurface skin and groomed fur, "
 "cinematic 35mm lens with shallow depth of field, matte-grey basalt planet surface with fine dust, deep black space with a dense cool starfield "
 "and one warm orange key light (the planet's own small sun) plus a cold blue fill from space; colour codes locked — PIP magenta #E0479E, "
 "GRUFF cyan #35C6E8, ORB chrome with a gold halo, THE COUNT matte black with red seven-segment digits; no photoreal humans anywhere; "
 "no logos, wordmarks or brand props; on-screen text is never generated (composited later in the FFmpeg renderer); same costume, same scarf, "
 "same goggle in every shot for all 30 story days — only the planet changes.")

LADDER={"1":1000,"2":1000,"4":1000,"5":500,"6":500,"7":500,"9":500,"10":300,"14":300,"15":300,"16":300,"19":300,"20":25,"24":25,"25":20,"26":12,"27":7,"28":4,"29":2,"30":2}

CHARS={
 "ORB":{"role":"host","design":"60-cm floating chrome sphere, one large glass lens-eye, gold ring-light halo that pulses in brightness when it speaks, always the same starfield reflection on the chrome; no mouth, no arms; objects arrive on tray drones","speech":"halo brightness keyframe in FFmpeg — no lip-sync","voice":"announcer energy, dry, precise, mischievous; ~55% of words","seed":"M_ORB"},
 "PIP":{"role":"contestant (the singer who went solo)","design":"1-m axolotl-like creature, matte magenta skin, six frilly gill-fronds that act as hair and emote (droop = sad, flare = angry, curl = flirt, fold flat = fear), oversized glossy black eyes, one yellow scarf that never changes, small mouth, one brass anklet with a glowing tether","speech":"mouth-visible lines capped at 20 for the episode; all other lines are voice-over on reactions/inserts","voice":"bright, quick, fragile underneath; ~22% of words","seed":"M_PIP_front"},
 "GRUFF":{"role":"contestant (the drummer who got left)","design":"2.5-m cyan-blue yeti, long fur completely covers the mouth (speech reads as fur movement and heavy brows), one cracked brass goggle worn on the forehead (the plot object), no clothes, one brass anklet with a glowing tether","speech":"fur-covered mouth — no lip-sync required","voice":"low, gravelly, few words, deadpan; ~23% of words","seed":"M_GRUFF_front"},
 "COUNT":{"role":"scoreboard / comic foil","design":"matte-black hovering 40-cm cube, red seven-segment displays on every face (clean plate — digits composited in FFmpeg), one wobbling antenna, four corner thrusters (gained on Day 10)","speech":"beeps only","voice":"none","seed":"M_COUNT"}}

CH={"PIP":"PIP, the 1-m matte-magenta axolotl creature with six gill-fronds, glossy black eyes and a yellow scarf",
    "GRUFF":"GRUFF, the 2.5-m cyan-blue yeti with fur covering his mouth and a cracked brass goggle on his forehead",
    "ORB":"ORB, the 60-cm floating chrome sphere with one glass lens-eye and a pulsing gold ring halo",
    "COUNT":"THE COUNT, the matte-black hovering cube with blank red display faces and a wobbling antenna"}
SETM={"landing_pad":"M_SET_pad","camp_north":"M_SET_camp","cave_south":"M_SET_cave","booth":"M_SET_booth","vent":"M_SET_vent","valley":"M_SET_valley","space":None,"archive":None}
PLANM={1000:"M_PLANET_1000",500:"M_PLANET_500",300:"M_PLANET_300",25:"M_PLANET_25",20:"M_PLANET_20",12:"M_PLANET_20",7:"M_PLANET_4",4:"M_PLANET_4",2:"M_PLANET_2"}
CHM={"PIP":"M_PIP_front","GRUFF":"M_GRUFF_front","ORB":"M_ORB","COUNT":"M_COUNT"}

SEEDS=[
 {"id":"M_PIP_front","kind":"character","prompt":"Front three-quarter full-body master of "+CH["PIP"]+", neutral stance on grey basalt, black space behind, warm orange key + blue fill, "+"small closed mouth, fronds relaxed; matte skin, no gloss except the eyes.","notes":"ONE approved seed; every PIP composite derives from it. Scarf and anklet locked."},
 {"id":"M_GRUFF_front","kind":"character","prompt":"Front three-quarter full-body master of "+CH["GRUFF"]+", standing on grey basalt against black space, fur groomed, mouth fully hidden by fur, heavy brows visible, goggle strap worn shiny, brass anklet on left leg.","notes":"ONE approved seed; goggle crack pattern must be identical in every derivative."},
 {"id":"M_ORB","kind":"character","prompt":"Master of "+CH["ORB"]+", hovering at eye level, chrome reflecting a fixed starfield, halo at mid brightness, no arms, no mouth.","notes":"Halo brightness is animated in FFmpeg; starfield reflection is locked."},
 {"id":"M_COUNT","kind":"character","prompt":"Master of "+CH["COUNT"]+", faces blank matte red (clean plate for composited digits), antenna mid-wobble, no thrusters (Day-10 thruster variant is a composite).","notes":"Digits are never generated; composited over the clean plate."},
 {"id":"M_PLANET_1000","kind":"planet","prompt":"Orbital hero still of a 1,000-metre grey basalt planetoid with a faint thin blue atmosphere haze, one small orange sun, dense starfield, tiny landing pad with a red ring visible on the equator.","notes":"Hero orbit master; used for the 0:45 pull-out and the 19:55 bookend."},
 {"id":"M_PLANET_500","kind":"planet","prompt":"Orbital still of the same planetoid after a wedge is sheared away: a clean glowing meridian scar, half the mass gone, thin haze thinner, same sun and starfield.","notes":"Wedge scar geometry locked for all Day 5–9 shots."},
 {"id":"M_PLANET_300","kind":"planet","prompt":"Orbital still of the same planetoid at 300 metres, two scars, no atmosphere haze left, landing pad now a large feature on the surface.","notes":"Most-used mid-episode master (Days 10–19)."},
 {"id":"M_PLANET_25","kind":"planet","prompt":"Orbital still of a house-sized (25 m) basalt rock with the landing pad, crate and pod door covering most of one face, two figures visible as specks.","notes":"Days 20–24."},
 {"id":"M_PLANET_20","kind":"planet","prompt":"Orbital still of a 20-metre basalt rock, pad and pod door filling one hemisphere, red pod light visible from space.","notes":"Day 25. The 12-m (Day 26) planet is a scale composite between this and M_PLANET_4."},
 {"id":"M_PLANET_4","kind":"planet","prompt":"Ground-level hero still of a 4-metre basalt rock in space with the pod door and crate on it, sized so a 2.5-m creature would stand taller than the world.","notes":"THUMBNAIL SEED (Day 28). The 7-m (Day 27) planet is a scale composite from this master."},
 {"id":"M_PLANET_2","kind":"planet","prompt":"Ground-level hero still of a car-sized (2 m) basalt rock in space, crate, clock face and red pod door crammed onto it, room for two bodies and nothing else.","notes":"Days 29–30; finale and rescue-ship plate."},
 {"id":"M_SET_pad","kind":"set","prompt":"Set master: the landing pad — a flat basalt disc with a painted red ring, a steel crate stencilled with a question mark, and a small escape-pod hatch set into the rock beside it (door unlit).","notes":"Red ring = QUIT line. Pod door = STEAL device (lit red only from Day 25). Same set at every planet size."},
 {"id":"M_SET_camp","kind":"set","prompt":"Set master: PIP's north-pole camp — a small magenta-trimmed tent, a kettle on a rock, a keyboard under a tarp, planet horizon curving close behind.","notes":"Re-lit for sunrise and night variants; slides into the valley from Day 6."},
 {"id":"M_SET_cave","kind":"set","prompt":"Set master: GRUFF's south-pole cave mouth — a mattress half outside, a wall with one fresh dent, cyan-tinted shadow inside.","notes":"Heart moon-rock (Day 10) and paperback (Day 16) are props added in composites."},
 {"id":"M_SET_booth","kind":"set","prompt":"Set master: a bare confessional booth — one stool, one lens-height mark, walls that take colour light (magenta for PIP, cyan for GRUFF).","notes":"Booth angle varies per use; also re-dressed as the glass soundproof pods (Day 26)."},
 {"id":"M_SET_vent","kind":"set","prompt":"Set master: a plasma vent — a crack in the basalt breathing violet light like a campfire, two sitting rocks either side.","notes":"The Talk (7:05), the goggle plant (10:25)."},
 {"id":"M_SET_valley","kind":"set","prompt":"Set master: the shallow valley both camps slide into after Day 5 — two tents almost touching, tether coiled between them, wedge scar glowing on the horizon.","notes":"Day 6 night, Day 7 fight and truce, Day 10 arrival."},
 {"id":"M_ARCH_01","kind":"archive","prompt":"Archive still, faded print: PIP and GRUFF's old tour van at night, goggle on GRUFF's forehead, scarf on PIP.","notes":"Hook photo stack #1 (0.4 s)."},
 {"id":"M_ARCH_02","kind":"archive","prompt":"Archive still, stage-lit: PIP at a microphone, GRUFF behind a drum kit, goggle up.","notes":"Hook photo stack #2."},
 {"id":"M_ARCH_03","kind":"archive","prompt":"Archive still, phone-photo look: the two of them mid-song, laughing, in a tiny club.","notes":"Hook photo stack #3."},
 {"id":"M_ARCH_04","kind":"archive","prompt":"Archive still: a battered drum kit with a heart drawn on the bass-drum case.","notes":"Hook photo stack #4; pays off 'drawn worse ones on drum cases' (9:45)."},
 {"id":"M_ARCH_05","kind":"archive","prompt":"Archive still, close: GRUFF's cracked brass goggle on a dressing-room table next to a set list.","notes":"Hook photo stack #5; goggle loop seed."},
 {"id":"M_ARCH_06","kind":"archive","prompt":"Archive still: a torn tour poster with PIP's name printed alone.","notes":"Hook photo stack #6 ('he found out from a poster')."},
]
assert len(SEEDS)==23

# Beat table: id, t_in, t_out, day, planet (pre-shrink), post_day, post_planet
BEATS={
"B01":("00:00","00:12",1,1000),"B02":("00:12","00:17",1,1000),"B03":("00:17","00:21",1,1000),"B04":("00:21","00:30",1,1000),
"B05":("00:30","00:45",1,1000),"B06":("00:45","01:30",1,1000),"B07":("01:30","02:00",1,1000),"B08":("02:00","02:45",2,1000),
"B09":("02:45","04:10",4,1000,5,500),"B10":("04:10","04:50",6,500),"B11":("04:50","06:20",7,500),"B12":("06:20","07:05",9,500,10,300),
"B13":("07:05","08:15",10,300),"B14":("08:15","08:45",14,300),"B15":("08:45","09:45",15,300),"B16":("09:45","10:25",16,300),
"B17":("10:25","10:55",16,300),"B18":("10:55","12:00",19,300,20,25),"B19":("12:00","12:25",20,25),"B20":("12:25","12:45",20,25),
"B21":("12:45","13:30",24,25,25,20),"B22":("13:30","15:10",25,20),"B23":("15:10","15:40",25,20),"B24":("15:40","16:25",26,12,27,7),
"B25":("16:25","17:10",28,4),"B26":("17:10","17:55",29,2),"B27":("17:55","18:35",29,2),"B28":("18:35","19:30",30,2),
"B29":("19:30","19:55",30,2),"B30":("19:55","20:00",30,2)}

# Shot DSL per beat: (vantage, set, chars, type, prompt, dur, opts)
# opts: ins=<insert id reused>, new=<insert id defined by this unique shot>, post=True (after shrink), loops=[...], mouth=[...], flash=True
S={}
S["B01"]=[
 ("extreme close-up on ORB lens-eye","landing_pad",["ORB"],"ECU","ORB punched in so tight the gold halo bleeds off both frame edges, halo pulsing hard with speech, starfield in the chrome.",3,{}),
 ("wide 3-shot low angle","landing_pad",["PIP","GRUFF","ORB"],"WS","PIP and GRUFF pull off space helmets on a bare grey rock hanging in black space, ORB hovering between them, red ring and steel crate behind; one steady 6-s take for FFmpeg punch-ins.",5,{"new":"INS_WIDE_A","mouth":[]}),
 ("archive photo stack","archive",[],"STILL","Six faded band photos flip past as a stack with whiteouts between them (composited from the archive masters).",2,{"ins":"INS_ARCHIVE_STACK"}),
 ("crate bloom macro","landing_pad",[],"MACRO","Slow push on the steel crate with the stencilled question mark as a hot white light bloom blows out across its lid.",2,{"new":"INS_CRATE_HERO"}),
]
S["B02"]=[
 ("PIP close-up open-mouthed","camp_north",["PIP"],"CU","PIP at the rock edge, mouth slightly open, gill-fronds lifting slowly, eyes huge; no dialogue, held.",1.6,{"new":"INS_PIP_CU_GASP"}),
 ("GRUFF close-up brows down","cave_south",["GRUFF"],"CU","GRUFF's face, brows down, fur drifting in a wind that should not exist, silent.",1.4,{"new":"INS_GRUFF_CU_BROW"}),
 ("tether insert with ORB above","landing_pad",["ORB"],"INSERT","The coiled glowing gravity tether on basalt, ORB hovering above it with a dim halo; one sub hit.",1,{"new":"INS_TETHER"}),
 ("wide 3-shot slow pull-back","landing_pad",["PIP","GRUFF","ORB"],"WS","Slow 1.6-s pull-back on the landing-pad wide, all three motionless.",1,{"ins":"INS_WIDE_A"}),
]
S["B03"]=[
 ("over-the-shoulder 2-shot ORB and GRUFF","landing_pad",["ORB","GRUFF"],"OTS","Over ORB's chrome curve onto GRUFF, fur bristling as he answers, halo pulsing in the foreground.",1.5,{}),
 ("PIP close-up against the crate","landing_pad",["PIP"],"CU","PIP framed against the steel crate, bright and quick, small mouth visible as she speaks two words.",1,{"mouth":["PIP"]}),
 ("punch-in on the 2-shot","landing_pad",["ORB","GRUFF"],"MCU","Tighter on GRUFF's heavy brows over ORB's halo; FFmpeg punch-in of the OTS take.",0.8,{"ins":"INS_OTS_A"}),
 ("PIP laugh close-up","landing_pad",["PIP"],"CU","PIP barks one surprised laugh and pulls the yellow scarf up over her mouth, fronds bouncing.",0.7,{"new":"INS_PIP_LAUGH"}),
]
S["B04"]=[
 ("wide 3-shot halo flare","landing_pad",["PIP","GRUFF","ORB"],"WS","Wide take B: ORB's halo flares white across the whole pad while PIP and GRUFF each hold a brass anklet.",3,{}),
 ("side medium on GRUFF, ORB drifting out of foreground","landing_pad",["GRUFF","ORB"],"MS","Side angle: GRUFF bends and snaps the anklet shut, ORB drifting out of the near foreground, motion blur on the click.",2,{}),
 ("2-shot anklet click fast punch-in","landing_pad",["PIP","GRUFF"],"MS","PIP looks at her anklet, at him, closes it — second click, fast punch-in with motion blur.",2,{}),
 ("GRUFF smirk close-up","landing_pad",["GRUFF"],"CU","GRUFF's smirk under the fur, brows lifting a millimetre, one full second of silence.",1,{"new":"INS_GRUFF_SMIRK"}),
 ("PIP close-up open-mouthed","landing_pad",["PIP"],"CU","PIP's reaction close-up, fronds lifting.",1,{"ins":"INS_PIP_CU_GASP"}),
]
S["B05"]=[
 ("whip tilt from anklet to face","landing_pad",["PIP"],"TILT","Whip-tilt up from PIP's locked brass anklet to her face, fronds settling.",1.5,{}),
 ("landing pad wide with red ring, all three","landing_pad",["PIP","GRUFF","ORB"],"WS","ORB inside the painted red ring, PIP and GRUFF outside it, the crate to one side; ORB delivers the rule with no music.",5,{"loops":["redline:OPEN"]}),
 ("ORB close-up dry","landing_pad",["ORB"],"CU","ORB's lens-eye close, halo steady and low, the red ring reflected in the chrome.",2.5,{"new":"INS_ORB_CU"}),
 ("orbit pull-out hero","space",["ORB"],"HERO","ORB launches and the camera rises with it: pad, two figures, the whole grey rock shrinking to a marble against the stars (1,000-m planet master).",6,{"new":"INS_ORBIT_1000"}),
]
S["B06"]=[
 ("orbital push-in to the north-pole camp","camp_north",[],"PUSH","From black space down through thin haze to a small tent, a kettle on a rock and a keyboard under a tarp.",6,{"loops":["crate:OPEN"]}),
 ("south-pole cave mouth medium","cave_south",[],"MS","GRUFF's cave: mattress half outside, a wall with a fresh dent, cyan shadow inside.",5,{}),
 ("THE COUNT hover insert","space",["COUNT"],"INSERT","THE COUNT drifts past the lens, antenna wobbling, blank red faces (digits composited: DAY 1 · 1,000 M).",3,{"new":"INS_COUNT_HOVER"}),
 ("tether insert with ORB above","landing_pad",["ORB"],"INSERT","The braided, faintly glowing tether paying out across the rock.",3,{"ins":"INS_TETHER"}),
 ("crate hero slow push","landing_pad",[],"MACRO","Slow hero push on the sealed steel crate, dust on the lid, the question mark stencil.",5,{"ins":"INS_CRATE_HERO"}),
 ("wide over the hole, two figures","landing_pad",["PIP","GRUFF"],"WS","A hole in the rock with stars beyond it; GRUFF hands on hips over it, PIP arriving and stopping dead.",5,{"new":"INS_HOLE"}),
 ("PIP appalled reaction close-up","landing_pad",["PIP"],"CU","PIP staring down into the hole, fronds flaring, scarf clutched; voice-over only.",4,{}),
 ("GRUFF pleased medium at the hole","landing_pad",["GRUFF"],"MS","GRUFF, pleased, brows up, fur moving with speech, gesturing at the hole like an estate agent.",5,{}),
 ("2-shot walking the equator, tether paying out","landing_pad",["PIP","GRUFF"],"WS","They walk the equator in opposite directions, the tether paying out between them, planet horizon curving.",6,{}),
]
S["B07"]=[
 ("magenta booth PIP frontal","booth",["PIP"],"CU","PIP alone in a booth lit magenta, speaking to the lens, fronds low, small mouth visible.",8,{"new":"INS_BOOTH_PIP_A","mouth":["PIP"]}),
 ("cyan booth GRUFF frontal","booth",["GRUFF"],"CU","GRUFF alone in a booth lit cyan, brows down, fur moving when he talks.",8,{"new":"INS_BOOTH_GRUFF_A"}),
 ("ORB against black space","space",["ORB"],"MS","ORB alone against the starfield, halo steady, then dimming to almost nothing on the beat.",6,{}),
 ("flash-forward stack","space",[],"FLASH","Five borrowed shots at 0.5 s with whiteouts: wedge tearing away (S055), GRUFF's hand on the red lever (S158), PIP shouting in rock dust (S062), truth beam flashing red (S142), a clock face with unreadable digits (S166).",4,{"ins":"INS_FLASH_STACK","flash":True}),
 ("ORB against black space, halo rising","space",["ORB"],"CU","ORB's halo comes back up slowly as it speaks the premise line.",4,{"ins":"INS_ORB_CU"}),
]
S["B08"]=[
 ("split-screen sunrise over the camp","camp_north",[],"WS","Magenta dawn sky over the north-pole tent, the small sun breaking the too-close horizon.",5,{}),
 ("split-screen sunrise over the cave","cave_south",[],"WS","Cyan dawn over the south-pole cave, same sun from the other hemisphere.",5,{}),
 ("orbital wide with diameter ring","space",[],"HERO","The 1,000-m planet from orbit; a glowing diameter ring (composited) draws around it and ticks one notch smaller.",7,{"ins":"INS_ORBIT_1000"}),
 ("GRUFF at the cave mouth medium","cave_south",["GRUFF"],"MS","GRUFF at the cave mouth looking at a horizon that curves away too soon, content, fur moving with speech.",8,{}),
 ("PIP at the covered keyboard","camp_north",["PIP"],"MS","PIP, one hand resting on the tarp over the keyboard, not lifting it; voice-over only, fronds soft.",8,{}),
 ("ORB hover over the equator","landing_pad",["ORB"],"MS","ORB hovering low over the equator, halo pulsing with the question, music gone.",6,{}),
 ("THE COUNT hover insert","space",["COUNT"],"INSERT","THE COUNT drifting past with DAY 2 · 1,000 M composited.",3,{"ins":"INS_COUNT_HOVER"}),
]
S["B09"]=[
 ("ORB arrival from orbit onto the pad","landing_pad",["ORB"],"WS","Midnight: ORB drops out of the black onto the pad, halo blazing, a tray drone settling beside it with two covered platters.",7,{"loops":["crate:FEED"]}),
 ("tray-drone platter reveal macro","landing_pad",[],"MACRO","Two silver lids lift: a tiny model planet whole, then the same model sawn clean in half.",5,{}),
 ("deliberation 2-shot, a metre apart","landing_pad",["PIP","GRUFF"],"MS","PIP and GRUFF a metre apart looking at the model planet instead of each other, rubbing sleep from their eyes.",8,{}),
 ("GRUFF medium shrugging","landing_pad",["GRUFF"],"MS","GRUFF shrugs — money is money — fur rippling with speech, brass anklet catching the halo.",6,{}),
 ("ORB close-up over the platters","landing_pad",["ORB"],"CU","ORB close over the two platters, their silver lids reflected in the chrome, stating the two rules of every visit, halo ticking.",7,{}),
 ("THE COUNT lap around the pad, tracking","landing_pad",["COUNT","PIP","GRUFF"],"TRACK","THE COUNT begins a slow lap of the pad, digits glowing, the two contestants in the background arguing.",7,{}),
 ("PIP close-up cold decision","landing_pad",["PIP"],"CU","PIP's fronds go dead still; she says two words with her small mouth visible.",5,{"mouth":["PIP"]}),
 ("hero wedge shearing away from space","space",[],"HERO","From orbit: a seam of light opens along a meridian and a whole wedge of the planet shears off, turning slowly into the dark.",10,{"new":"INS_WEDGE_SPACE"}),
 ("ground-level POV, the camp drifting past their feet","valley",["PIP","GRUFF"],"POV","Ground level: tents, kettle and the dented wall drift past two pairs of feet and out of reach; crack, rumble, then vacuum silence.",8,{}),
 ("THE COUNT digit flip insert","landing_pad",["COUNT"],"INSERT","THE COUNT's faces flip (composited) to DAY 5 · 500 M with one beep.",3,{"ins":"INS_COUNT_HOVER","post":True}),
 ("GRUFF watching the wedge go, close-up","valley",["GRUFF"],"CU","GRUFF watching his mattress leave on a wedge of planet, brows up, fur still.",6,{"post":True}),
 ("orbital 500-m planet with scar","space",[],"HERO","The half-planet from orbit, the fresh meridian scar glowing, ORB a speck rising away.",7,{"post":True,"new":"INS_ORBIT_500"}),
]
S["B10"]=[
 ("night wide, two tents sliding toward the valley","valley",[],"WS","Night: two tents on a half-planet, both creeping slowly downhill toward the same shallow valley.",7,{}),
 ("GRUFF snore close-up","cave_south",["GRUFF"],"CU","GRUFF asleep, fur rippling out from the mouth with each enormous snore.",5,{}),
 ("PIP tiptoe POV into the cave","cave_south",["PIP"],"POV","PIP's point of view tiptoeing into the cave mouth, one frond raised like a candle, whispering.",7,{}),
 ("low wide, PIP trips on the tether","cave_south",["PIP","GRUFF"],"WS","Her foot hooks the tether and she goes down flat beside the mattress; GRUFF does not move.",5,{}),
 ("GRUFF one-eye-open close-up","cave_south",["GRUFF"],"CU","GRUFF, one eye open, brows confused, fur moving with two mumbled sentences.",5,{}),
 ("PIP retreating reaction, over the shoulder","cave_south",["PIP"],"OTS","Over GRUFF's shoulder: PIP backing out of the cave, sweet and guilty; voice-over.",4,{}),
 ("tally marks insert","cave_south",[],"MACRO","Six tally marks scratched into basalt, the sixth still pale and fresh.",4,{"new":"INS_TALLY"}),
]
S["B11"]=[
 ("handheld 2-shot, fronds flared","valley",["PIP","GRUFF"],"MS","Morning in the valley, tents almost touching; PIP arms crossed, fronds flaring wide as she speaks; handheld energy.",8,{"mouth":["PIP"]}),
 ("reverse 2-shot, fur bristled","valley",["PIP","GRUFF"],"MS","Reverse angle: GRUFF's fur standing up along the shoulders as he answers, PIP small in the foreground.",7,{}),
 ("PIP furious close-up","valley",["PIP"],"CU","PIP escalating — one song, Gruff — small mouth visible, fronds rigid.",7,{"mouth":["PIP"]}),
 ("GRUFF cold close-up","valley",["GRUFF"],"CU","GRUFF, cold and quiet, brows flat, fur barely moving.",7,{}),
 ("valley wide, dust kicking, PIP shouting","valley",["PIP","GRUFF"],"WS","Wide of the valley; PIP shouting into a storm of kicked-up rock dust, GRUFF a wall beside her; voice-over.",5,{"new":"INS_PIP_DUST"}),
 ("2-shot on a 2-metre rock, shoulder to shoulder","space",["PIP","GRUFF"],"FLASH","Flash-forward: both bodies jammed shoulder to shoulder on a car-sized rock with no room to turn away.",1,{"ins":"INS_TWOSHOT_2M","flash":True}),
 ("GRUFF turning away, wide","valley",["GRUFF","PIP"],"WS","GRUFF turns his back and walks the tether out to its full length; PIP left standing.",6,{}),
 ("PIP crying behind the boulder","valley",["PIP"],"CU","PIP on the far side of a boulder, crying without sound, fronds drooping to her shoulders.",7,{"new":"INS_PIP_CRY"}),
 ("cyan booth GRUFF, high angle","booth",["GRUFF"],"MCU","GRUFF in the cyan booth from a high angle, shoulders down, ashamed.",7,{}),
 ("hands on one ration bar insert","valley",[],"MACRO","One magenta hand and one enormous cyan hand on a single ration bar; the bar snaps.",5,{}),
 ("2-shot sitting a metre apart","valley",["PIP","GRUFF"],"MS","They sit with a metre of rock between them, eating, not looking at each other; PIP's mouth visible for the truce line.",8,{"mouth":["PIP"]}),
 ("orbital 500-m planet with scar","space",[],"HERO","The half-planet from orbit at dusk; strings.",6,{"ins":"INS_ORBIT_500"}),
]
S["B12"]=[
 ("ORB arrival low over the valley","valley",["ORB"],"WS","Midnight: ORB drops in low over the valley from a new angle, halo bright, no tray drone.",6,{}),
 ("2-shot arriving tethered","valley",["PIP","GRUFF"],"MS","PIP and GRUFF arrive together, tethered, still a metre apart, blinking at the light.",5,{}),
 ("GRUFF close-up brows down","valley",["GRUFF"],"CU","GRUFF, suspicious — a gift — brows down; PIP's wary voice-over lands on his face.",6,{"ins":"INS_GRUFF_CU_BROW"}),
 ("hero wedge shearing away from space","space",[],"HERO","A smaller wedge shears off, cleaner and faster than the first, and drifts away like a slice off a loaf.",5,{"ins":"INS_WEDGE_SPACE"}),
 ("THE COUNT thruster gag, wobbling across frame","landing_pad",["COUNT"],"INSERT","Four little thrusters ignite on THE COUNT's corners; it lurches, wobbling, across frame with a ration tin in a claw (digits DAY 10 · 300 M composited).",6,{"post":True,"new":"INS_COUNT_THRUST"}),
 ("2-shot at the cave mouth with ORB","cave_south",["PIP","GRUFF","ORB"],"MS","ORB delivers the promise at the cave mouth, halo dimming a shade; GRUFF dry, PIP watching ORB lift away.",8,{"post":True}),
 ("moon-rock heart insert on the mattress","cave_south",[],"MACRO","Dawn: a moon rock chipped and scraped into a lopsided heart, sitting on the mattress.",4,{"post":True}),
 ("GRUFF picks up the heart, medium","cave_south",["GRUFF"],"MS","GRUFF looks at the rock heart, says nothing, and tucks it inside the cave.",5,{"post":True}),
 ("PIP on the ridge watching, long lens","valley",["PIP"],"LS","PIP small on a ridge, watching him keep it; fronds curling at the tips.",5,{"post":True}),
]
S["B13"]=[
 ("vent 2-shot lit from below","vent",["PIP","GRUFF"],"MS","Night: a plasma vent hisses violet in a crack in the rock; the two of them sit either side, lit from below.",9,{}),
 ("PIP close-up firelit","vent",["PIP"],"CU","PIP firelit, fronds folded not drooping, telling it; small mouth visible.",12,{"mouth":["PIP"]}),
 ("PIP in a column of green light","landing_pad",["PIP"],"FLASH","Flash-forward: PIP standing in a column of pale green light on the equator.",0.5,{"ins":"INS_BEAM_PIP","flash":True}),
 ("GRUFF close-up firelit slow push","vent",["GRUFF"],"CU","Slow push-in on GRUFF looking at the vent, not at her, admitting it.",10,{}),
 ("starfield time-lapse over the tiny horizon","space",[],"TIMELAPSE","Stars wheel over a too-small horizon with the violet vent glow at the bottom of frame.",8,{}),
 ("GRUFF profile firelit","vent",["GRUFF"],"MCU","GRUFF in profile against the vent, rueful, the dentist story.",9,{}),
 ("PIP profile firelit, wet laugh","vent",["PIP"],"MCU","PIP in profile laughs once and it comes out wet; voice-over over her looking at the fire.",8,{}),
 ("GRUFF close-up plain","vent",["GRUFF"],"CU","GRUFF, plain — now we survive a rock — brows level.",6,{}),
]
S["B14"]=[
 ("GRUFF at the cave mouth staring at the horizon","cave_south",["GRUFF"],"MS","GRUFF at the cave mouth staring at a horizon he can nearly touch, hollow.",7,{"loops":["crate:FEED"]}),
 ("continuous tracking lap of the planet, sped 2x","landing_pad",["GRUFF"],"TRACK","One continuous tracking shot: GRUFF walks the full circumference — past the crate, the vent, her tent, the crate again — back to his start; sped to feel like ten seconds.",15,{}),
 ("cyan booth GRUFF, low angle","booth",["GRUFF"],"MCU","GRUFF in the cyan booth from a low angle, taps the side of his own head once.",8,{}),
]
S["B15"]=[
 ("dome hologram unfolding over the planet","space",[],"HERO","Above the 300-m planet a hologram unfolds: a glass dome the width of the sky, a garden, trees, a bath steaming.",8,{"loops":["crate:FEED"]}),
 ("ORB arrival with no platters, high angle","landing_pad",["ORB"],"WS","ORB drops in with nothing on the tray drone, halo generous, the dome's green light on the pad.",6,{}),
 ("GRUFF face green-lit, tilted up","landing_pad",["GRUFF"],"CU","GRUFF's face lit green by the hologram, tilted up like a child's, awed, fur moving.",6,{}),
 ("PIP close-up, has not looked up","landing_pad",["PIP"],"CU","PIP, firm, eyes on ORB not the dome, one word with her small mouth visible.",3,{"mouth":["PIP"]}),
 ("2-shot wide with 10-s timer over it","landing_pad",["PIP","GRUFF"],"WS","Wide two-shot under the dome; a 10-second timer draws itself over the frame (composited) and ticks.",6,{}),
 ("GRUFF pleading medium","landing_pad",["GRUFF"],"MS","GRUFF turns to her, huge and pleading — there's a bath — brows up.",5,{}),
 ("PIP close-up open-mouthed","landing_pad",["PIP"],"CU","PIP's steely reaction over the ticking timer; voice-over.",6,{"ins":"INS_PIP_CU_GASP"}),
 ("dome folding away into a point of light","space",[],"HERO","The dome folds itself into a single point of light and is gone; the planet stays.",5,{}),
 ("cyan booth GRUFF, sulking, three-quarter","booth",["GRUFF"],"MCU","GRUFF in the booth, three-quarter angle, sulking so hard the fur droops.",7,{}),
 ("crate hero slow push","landing_pad",[],"MACRO","The crate below ORB in frame, sealed, waiting.",4,{"ins":"INS_CRATE_HERO"}),
]
S["B16"]=[
 ("ration-bar heart insert","camp_north",[],"MACRO","Ration bars laid out on a flat rock in a slightly lopsided heart.",5,{"loops":["riff:OPEN"]}),
 ("2-shot over the plate","camp_north",["PIP","GRUFF"],"MS","Over the plate: GRUFF picks a bar from the top of the heart and puts it back exactly where it was; PIP defensive, voice-over.",6,{}),
 ("PIP close-up bright, testing","camp_north",["PIP"],"CU","PIP bright, testing — colleagues? — small mouth visible, fronds half-curled.",4,{"mouth":["PIP"]}),
 ("GRUFF close-up firm","camp_north",["GRUFF"],"CU","GRUFF firm — say the real word — brows level, fur moving; PIP's small reply lands as voice-over on him.",6,{}),
 ("ration-tin tap macro","camp_north",["PIP"],"MACRO","A magenta fingernail taps four notes on the rim of a ration tin; GRUFF's shadow shifts as he looks up.",5,{"new":"INS_TIN_RIFF"}),
 ("GRUFF reading against the cave wall, medium","cave_south",["GRUFF"],"MS","GRUFF alone against the cave wall reading a battered paperback, pencil in his fist.",6,{}),
 ("book cover macro","cave_south",[],"MACRO","The paperback's cover held up — blank white panel for the composited title HOW TO STOP BEING A DRUMMER ABOUT IT.",4,{}),
]
S["B17"]=[
 ("goggle macro on the forehead","vent",["GRUFF"],"MACRO","The cracked brass goggle on GRUFF's forehead, one lens starred, strap worn shiny, vent light in the crack.",5,{"new":"INS_GOGGLE_MACRO","loops":["goggle:OPEN"]}),
 ("vent 2-shot, reverse side","vent",["PIP","GRUFF"],"MS","The two at the vent from the opposite side; PIP teasing him about the goggle, small mouth visible.",7,{"mouth":["PIP"]}),
 ("GRUFF hand-on-goggle close-up","vent",["GRUFF"],"CU","GRUFF's hand rises to the goggle and rests there; guarded; fur moving with the promise.",7,{}),
 ("PIP thrown reaction close-up","vent",["PIP"],"CU","PIP thrown — why the last night — fronds lifting; voice-over.",4,{}),
 ("magenta booth PIP, side angle","booth",["PIP"],"MCU","PIP in the magenta booth from the side, turning the scarf over in her hands, rattled; voice-over on her hands.",7,{}),
]
S["B18"]=[
 ("five-platter wide with the crate lit behind","landing_pad",["ORB","PIP","GRUFF"],"WS","Midnight: ORB, a tray drone and five covered platters in a row; the crate behind them lit for the first time.",8,{"loops":["crate:FEED"]}),
 ("lid one macro, cash with a bite out","landing_pad",[],"MACRO","A silver lid lifts on a stack of prop cash with a bite taken out of it.",3,{"new":"INS_LID"}),
 ("GRUFF close-up instant no","landing_pad",["GRUFF"],"CU","GRUFF — no — instant, brows flat.",2,{}),
 ("lid two macro, bigger bite, re-lit","landing_pad",[],"MACRO","Second lid, cooler light and a tighter crop (re-lit re-use of lid one): a bigger bite; PIP's appalled voice-over.",3,{"ins":"INS_LID"}),
 ("lid three macro, two model planets","landing_pad",[],"MACRO","Third lid: a tiny model planet and, beside it, a tinier one.",3,{}),
 ("debate 2-shot with 5-s timer","landing_pad",["PIP","GRUFF"],"MS","Fast debate two-shot, a five-second timer composited over their heads; GRUFF eager, PIP reckless with her mouth visible.",6,{"mouth":["PIP"]}),
 ("ORB lifting platter four, slow push","landing_pad",["ORB"],"MS","ORB tips platter four's lid with a tray-drone arm as the camera pushes in slowly.",5,{}),
 ("empty plate macro, one engraved word","landing_pad",[],"MACRO","An empty silver plate with one engraved word (blank panel for the composited FREE).",4,{}),
 ("GRUFF stunned close-up","landing_pad",["GRUFF"],"CU","GRUFF stunned, mouth-fur still, brows climbing.",4,{}),
 ("PIP crying behind the boulder","valley",["PIP"],"CU","PIP's stricken face; no dialogue.",2,{"ins":"INS_PIP_CRY"}),
 ("ORB close-up unrepentant","landing_pad",["ORB"],"CU","ORB, halo full, unrepentant — I said it out loud.",4,{"ins":"INS_ORB_CU"}),
 ("big wedge tearing away, ground angle","landing_pad",["PIP","GRUFF"],"HERO","From the pad: a third of the sky tears away and drifts off; what remains is small enough to see its whole curve.",9,{}),
 ("THE COUNT hover insert","landing_pad",["COUNT"],"INSERT","THE COUNT beeps and flips (composited) to DAY 20 · 25 M.",3,{"ins":"INS_COUNT_HOVER","post":True}),
 ("house-sized planet from orbit","space",[],"HERO","A rock the size of a house from orbit, two specks and a crate on it.",7,{"post":True,"new":"INS_ORBIT_25"}),
]
S["B19"]=[
 ("crate doors opening with light","landing_pad",["PIP","GRUFF"],"WS","The crate doors swing open and light pours out over both faces.",5,{"loops":["crate:PAY"]}),
 ("ticket macro, two embossed names","landing_pad",[],"MACRO","Two paper tickets, embossed, each with a blank name panel (names composited).",5,{}),
 ("PIP sobbing close-up, new angle","landing_pad",["PIP"],"CU","PIP folds in half sobbing, fronds over her face; voice-over.",5,{}),
 ("2-shot hug from behind","landing_pad",["PIP","GRUFF"],"MS","From behind: GRUFF's arm around her without either of them deciding it.",6,{}),
 ("ORB close-up turning","landing_pad",["ORB"],"CU","ORB's halo dims — the tickets have a price — and the lens tilts down.",4,{}),
]
S["B20"]=[
 ("house-sized planet from orbit","space",[],"HERO","The 25-m rock from orbit, two figures and the crate between them.",4,{"ins":"INS_ORBIT_25"}),
 ("ground shoulder-bump 2-shot","landing_pad",["PIP","GRUFF"],"MS","They turn to walk and bump shoulders; turn the other way and bump shoulders again.",5,{}),
 ("wide over the hole, two figures","landing_pad",["PIP","GRUFF"],"WS","Callback: the hole, now two metres from the mattress.",3,{"ins":"INS_HOLE"}),
 ("GRUFF resigned close-up","landing_pad",["GRUFF"],"CU","GRUFF resigned — I can hear you swallow — brows down.",4,{}),
 ("PIP flat close-up disbelieving","landing_pad",["PIP"],"CU","PIP flat, disbelieving, small mouth visible; ORB's stinger lands as she stares.",4,{"mouth":["PIP"]}),
]
S["B21"]=[
 ("ORB low-angle arrival, hard white halo","landing_pad",["ORB"],"WS","Midnight: ORB arrives low, halo a hard white ring; behind it the escape-pod door lit red for the first time.",6,{"loops":["launch:OPEN"]}),
 ("key-under-platter macro","landing_pad",[],"MACRO","A single brass key on a silver platter as the lid lifts; clink.",5,{"new":"INS_KEY_MACRO"}),
 ("pod door lit red with one seat visible","landing_pad",[],"MS","The small escape pod set into the rock, door glowing red, one seat visible inside.",6,{"new":"INS_POD_DOOR"}),
 ("split-screen reactions PIP and GRUFF","landing_pad",["PIP","GRUFF"],"SPLIT","Split-screen: PIP's fronds folding flat / GRUFF looking at the key, then her, then the key.",6,{"ins":"INS_SPLIT_REACT"}),
 ("key on the platter inside the red ring, wide","landing_pad",["ORB","PIP","GRUFF"],"WS","Wide: the platter set down inside the red ring, the key on it, both contestants outside the ring looking at it.",9,{}),
 ("hero wedge shearing away from space","space",[],"HERO","A fresh sliver shears off the small rock from orbit.",3,{"ins":"INS_WEDGE_SPACE","post":True}),
 ("THE COUNT flip with ladder graphic","landing_pad",["COUNT"],"INSERT","THE COUNT flips (composited) to DAY 25 · 20 M as the ladder's last five rungs draw beside it.",6,{"post":True}),
 ("GRUFF close-up to himself","landing_pad",["GRUFF"],"CU","GRUFF, to himself — two metres, that's a doormat — brows up; ORB's reply as it leaves.",4,{"post":True}),
]
S["B22"]=[
 ("truth-beam wide on the equator","landing_pad",["COUNT","PIP","GRUFF"],"WS","Dawn on a 20-m world: a pale humming column of light on the equator, THE COUNT hovering above it holding the beam like a lantern.",8,{"new":"INS_BEAM_WIDE","loops":["launch:FEED"]}),
 ("ORB close-up with the beam in the chrome","landing_pad",["ORB"],"CU","ORB gleeful, the pale beam column reflected across the chrome, halo strobing softly with the rules.",8,{}),
 ("GRUFF steps into the light, medium","landing_pad",["GRUFF"],"MS","GRUFF steps into the beam first; it turns his fur white.",6,{}),
 ("PIP close-up in the beam","landing_pad",["PIP"],"CU","PIP in the beam, fronds glowing through, answers one word with her small mouth visible; light shifts green.",6,{"new":"INS_BEAM_PIP","mouth":["PIP"]}),
 ("GRUFF thrown close-up","landing_pad",["GRUFF"],"CU","GRUFF thrown — you sold twice what we sold — brows up; PIP's reply as voice-over.",7,{}),
 ("swap wide, GRUFF in the beam","landing_pad",["PIP","GRUFF","COUNT"],"WS","They swap; GRUFF in the beam, enormous, the light barely reaching his shoulders.",5,{}),
 ("PIP close-up brave","landing_pad",["PIP"],"CU","PIP asks the question, brave and small, mouth visible.",4,{"mouth":["PIP"]}),
 ("GRUFF close-up immediate answer","landing_pad",["GRUFF"],"CU","GRUFF answers instantly; the beam behind him flickers green, red, green.",5,{}),
 ("THE COUNT falls, beam dies, wide","landing_pad",["COUNT","GRUFF"],"WS","THE COUNT's thrusters cough; it lurches, tips and lands upside-down on the equator with a clatter; the light goes out.",6,{}),
 ("GRUFF urgent close-up","landing_pad",["GRUFF"],"CU","GRUFF urgent — fix it, ask me again — fur bristling.",4,{}),
 ("ORB close-up final","landing_pad",["ORB"],"CU","ORB, level and final — one question per person.",4,{}),
 ("PIP close-up in the beam","landing_pad",["PIP"],"CU","PIP beside the dead beam, shaken, light gone; voice-over — ask me the same thing.",6,{"ins":"INS_BEAM_PIP"}),
 ("beam relit, PIP steps in, low angle","landing_pad",["PIP","COUNT"],"WS","THE COUNT rights itself with a beep; the beam relights; PIP steps in from a low angle.",5,{}),
 ("PIP close-up steady, eyes on GRUFF","landing_pad",["PIP"],"CU","PIP steady, eyes on GRUFF, one word, mouth visible; green.",5,{"mouth":["PIP"]}),
 ("truth-beam wide on the equator","landing_pad",["COUNT","PIP","GRUFF"],"WS","The beam wide, green, then silence; ORB lays it out in voice-over.",7,{"ins":"INS_BEAM_WIDE"}),
 ("cyan booth GRUFF, insisting, frontal tight","booth",["GRUFF"],"CU","GRUFF in the booth, tight, insisting it was true — mostly.",6,{}),
 ("magenta booth PIP, three-quarter, over her hands","booth",["PIP"],"MCU","PIP in the booth, three-quarter, looking at her hands; voice-over.",4,{}),
]
S["B23"]=[
 ("GRUFF alone at the pod door, wide","landing_pad",["GRUFF"],"WS","Night: GRUFF alone at the pod door, red light on his fur, PIP a sleeping shape ten metres behind.",10,{"loops":["launch:FEED"]}),
 ("key in his fist macro","landing_pad",["GRUFF"],"MACRO","GRUFF's fist opens: the brass key, red light along its teeth.",6,{}),
 ("GRUFF close-up in red light","landing_pad",["GRUFF"],"CU","GRUFF's face in the red door light, colder, then the hand closing again — not tonight.",10,{}),
 ("key-under-platter macro","landing_pad",[],"MACRO","The key, then hard cut to black.",4,{"ins":"INS_KEY_MACRO"}),
]
S["B24"]=[
 ("two glass pods wide on a 12-m world","landing_pad",["PIP","GRUFF"],"WS","Two glass soundproof pods side by side on a twelve-metre rock, one creature in each.",6,{"loops":["goggle:FEED"]}),
 ("PIP pod interior, knees up","booth",["PIP"],"MCU","Inside her pod, knees up, scarf wound twice, speaking to the glass — small mouth visible, muffled treatment.",10,{"mouth":["PIP"],"new":"INS_PIP_POD"}),
 ("ORB at GRUFF's pod glass","landing_pad",["ORB","GRUFF"],"MS","ORB hovering at the glass of GRUFF's pod, needling; GRUFF's shape inside.",5,{}),
 ("GRUFF pod interior, evasive","booth",["GRUFF"],"MCU","GRUFF inside the pod, looking at ORB a long time, evasive.",7,{}),
 ("PIP pod interior, knees up","booth",["PIP"],"MCU","PIP watching his pod through her glass, his mouth-fur moving, no sound; voice-over.",5,{"ins":"INS_PIP_POD"}),
 ("seven-metre planet from orbit","space",[],"HERO","A seven-metre rock from orbit, two pods and a crate covering most of it.",4,{"post":True}),
 ("tethered walk gag, ground level","landing_pad",["PIP","GRUFF"],"WS","The two try to walk to the hole, tethered, on a surface curving away under every second step.",5,{"post":True}),
]
S["B25"]=[
 ("thumbnail hero: GRUFF taller than the world","landing_pad",["PIP","GRUFF"],"HERO","GRUFF standing on a four-metre planet, taller than the world under him; PIP at his feet in his shadow; black space; the pod's red door the only colour. THUMBNAIL SEED.",12,{"new":"INS_THUMB_4M","loops":["launch:FEED"]}),
 ("lever-hand macro inside the pod door","landing_pad",["GRUFF"],"MACRO","GRUFF's hand resting on the red launch lever inside the pod door.",7,{"new":"INS_LEVER_HAND"}),
 ("GRUFF strained close-up","landing_pad",["GRUFF"],"CU","GRUFF strained — every time she bumps me — brows knotted.",8,{}),
 ("PIP in his shadow, low angle","landing_pad",["PIP","GRUFF"],"LOW","Low angle: PIP small inside GRUFF's shadow, looking up; her frightened voice-over.",9,{}),
 ("magenta booth PIP, high angle","booth",["PIP"],"MCU","PIP in the booth from a high angle, frightened; voice-over continues.",5,{}),
 ("THE COUNT thruster gag, wobbling across frame","landing_pad",["COUNT"],"INSERT","THE COUNT wobbles past with DAY 28 · 4 M composited; a clock tick begins.",4,{"ins":"INS_COUNT_THRUST"}),
]
S["B26"]=[
 ("2-shot on a 2-metre rock, bodies fill the frame","landing_pad",["PIP","GRUFF"],"MS","A two-metre planet: both bodies fill the frame because there is nothing else to fill it.",6,{"new":"INS_TWOSHOT_2M","loops":["goggle:PAY"]}),
 ("THE COUNT bolting the clock into the rock","landing_pad",["COUNT"],"INSERT","THE COUNT bolts a clock face into the rock with three metal taps (digits composited: 24:00:00).",5,{"new":"INS_CLOCK"}),
 ("GRUFF takes the goggle off, close-up","landing_pad",["GRUFF"],"CU","GRUFF takes the goggle off his forehead for the first time and holds it in both hands, telling it.",12,{}),
 ("goggle macro in his hands","landing_pad",["GRUFF"],"MACRO","The goggle turned over in enormous hands, the cracked lens catching red door light.",8,{}),
 ("PIP close-up undone","landing_pad",["PIP"],"CU","PIP undone, scarf in her fists, barely voiced — you sold the van for me — mouth visible.",4,{"mouth":["PIP"]}),
 ("magenta booth PIP, frontal, wrecked","booth",["PIP"],"CU","PIP in the booth, frontal, wrecked, not getting the words in order; voice-over.",6,{}),
]
S["B27"]=[
 ("night wide, tiny rock, two sleeping shapes","space",["PIP","GRUFF"],"WS","From a distance: a rock the size of a car, two shapes asleep against the crate, the clock glowing between them.",10,{"loops":["launch:FEED"]}),
 ("THE COUNT bolting the clock into the rock","landing_pad",["COUNT"],"INSERT","The clock face on the rock (composited 11:07:00).",4,{"ins":"INS_CLOCK"}),
 ("PIP eyes open in the dark","landing_pad",["PIP"],"CU","PIP's face in the dark, eyes open, not asleep; whispered voice-over.",10,{}),
 ("cyan booth GRUFF, cold, half-lit","booth",["GRUFF"],"MCU","GRUFF in the booth half-lit, honest and cold; two seconds of nothing after.",12,{}),
 ("2-shot on a 2-metre rock, bodies fill the frame","landing_pad",["PIP","GRUFF"],"MS","The two shapes against the crate, the tick only.",4,{"ins":"INS_TWOSHOT_2M"}),
]
S["B28"]=[
 ("two hands on the lever macro","landing_pad",["PIP","GRUFF"],"MACRO","Flash-forward: 00:00:03 on the clock (composited); two hands on a lever — one huge, one small; whiteout.",3,{"loops":["launch:PAY"]}),
 ("day-30 wide, no room to pace","landing_pad",["PIP","GRUFF","ORB"],"WS","Ten minutes left: two creatures, a crate, a pod, a clock, on a rock with no room to pace; ORB above.",7,{}),
 ("ORB close-up, clock reflected in the lens","landing_pad",["ORB"],"CU","ORB close, the clock face reflected in its lens-eye, saying the numbers out loud because that's the job.",6,{}),
 ("truth-beam wide on the equator","landing_pad",["COUNT","PIP","GRUFF"],"WS","Replay in his head: the beam flickering red, THE COUNT falling.",2,{"ins":"INS_BEAM_WIDE"}),
 ("GRUFF at the lever, medium","landing_pad",["GRUFF","PIP"],"MS","GRUFF at the pod, hand on the lever, PIP right behind him because there is nowhere else to be.",6,{}),
 ("over PIP's shoulder onto his back","landing_pad",["PIP","GRUFF"],"OTS","Over PIP's shoulder onto GRUFF's back; her quiet voice-over; he does not turn round.",5,{}),
 ("GRUFF close-up, sweat in the fur","landing_pad",["GRUFF"],"CU","GRUFF's face, sweat in the fur, the tick speeding up.",4,{}),
 ("lever-hand macro inside the pod door","landing_pad",["GRUFF"],"MACRO","His hand lifts off the lever.",3,{"ins":"INS_LEVER_HAND"}),
 ("PIP grabs his hand macro","landing_pad",["PIP","GRUFF"],"MACRO","A magenta hand grabs the enormous cyan one before it gets anywhere else.",3,{}),
 ("PIP close-up one word","landing_pad",["PIP"],"CU","PIP, fierce, one word — Stay — mouth visible.",2,{"mouth":["PIP"]}),
 ("ORB close-up, each number alone","landing_pad",["ORB"],"CU","ORB counting three, two, one; halo pulses on each; then one full second of nothing.",5,{}),
 ("rescue ship rising over the tiny planet","space",["PIP","GRUFF"],"HERO","Over the horizon of a car-sized planet a rescue ship rises — enormous, slow, lights on, engines rolling.",9,{}),
]
S["B29"]=[
 ("anklet release macro","landing_pad",["PIP","GRUFF"],"MACRO","Two brass anklets spring open — the hook's two clicks, reversed.",3,{"loops":["riff:PAY"]}),
 ("crate 2-shot, new high angle","landing_pad",["PIP","GRUFF","ORB"],"MS","High angle over the open crate: the tickets in their hands, ORB warm above them.",6,{}),
 ("ration-tin riff macro","landing_pad",["PIP","GRUFF"],"MACRO","PIP taps four notes on the ration tin; two cyan fingers answer on the crate lid.",5,{}),
 ("ORB spinning in place","landing_pad",["ORB"],"MS","ORB spins in place, halo strobing, delighted.",3,{}),
 ("PIP close-up wet-eyed bright","landing_pad",["PIP"],"CU","PIP bright and wet-eyed — we'll need a new van — mouth visible.",4,{"mouth":["PIP"]}),
 ("GRUFF close-up grinning under the fur","landing_pad",["GRUFF"],"CU","GRUFF grinning under the fur, brows high.",4,{}),
]
S["B30"]=[
 ("orbit pull-out hero","space",["ORB"],"HERO","The 0:45 orbit pull-out re-used with a new warm grade: the planet becomes a dot; hard cut to black.",5,{"ins":"INS_ORBIT_1000","loops":["redline:PAY"]}),
]

def ts(s): m,x=s.split(':'); return int(m)*60+int(x)
def fmt(t): t=int(round(t)); return '%02d:%02d'%(t//60,t%60)

shots=[]; n=0; ins_first={}; pending=[]
for bid,(t0,t1,day,planet,*post) in BEATS.items():
    lst=S[bid]; a,b=ts(t0),ts(t1); tot=sum(x[5] for x in lst); k=(b-a)/tot; cur=a
    for (vant,setn,chars,typ,prompt,dur,o) in lst:
        n+=1; sid='S%03d'%n
        d=day; p=planet
        if o.get('post') and post: d,p=post
        if o.get('flash'): d,p=d,p  # flash-forwards are tagged to the beat they play in
        dur_s=round(dur*k,1); t_in=cur; t_out=cur+dur*k; cur=t_out
        masters=[CHM[c] for c in chars]
        if SETM.get(setn): masters.append(SETM[setn])
        if setn=='archive': masters+= [f"M_ARCH_0{i}" for i in range(1,7)]
        if typ not in ('STILL',) and setn!='booth': masters.append(PLANM[p])
        reuse='insert' if 'ins' in o else 'unique'
        full_prompt=prompt
        if chars: full_prompt+=' Characters: '+'; '.join(CH[c] for c in chars)+'.'
        full_prompt+=f' Planet {p} m; on-screen text and digits are NOT generated. Locked art style.'
        rec={"id":sid,"beat":bid,"t_in":fmt(t_in),"t_out":fmt(t_out),"t_in_s":round(t_in,1),"t_out_s":round(t_out,1),"day":d,"planet_m":p,"count_display":p,
             "characters":chars,"set":setn,"vantage":vant,"seed_masters":masters,"composite_seed_id":None,"shot_type":typ,
             "i2v_prompt":full_prompt,"duration_s":dur_s,"reuse":reuse,"loops":o.get('loops',[]),"mouth_visible":o.get('mouth',[])}
        if 'new' in o: ins_first[o['new']]=sid; rec['insert_id']=o['new']
        if 'ins' in o: rec['insert_id']=o['ins']; pending.append(rec)
        shots.append(rec)
# composite ids + reuse_of
cid=0
for r in shots:
    if r['reuse']=='unique': cid+=1; r['composite_seed_id']='C%03d'%cid
for r in pending:
    src=ins_first.get(r['insert_id'])
    if src is None:
        # library inserts defined by composition (flash stack / split screen / OTS punch-in)
        r['composite_seed_id']='C_'+r['insert_id']; r['reuse_of']=None
    else:
        srec=next(x for x in shots if x['id']==src); r['composite_seed_id']=srec['composite_seed_id']; r['reuse_of']=src
# validation
errs=[]
for i in range(1,len(shots)):
    if shots[i]['vantage']==shots[i-1]['vantage']: errs.append(('adjacent vantage',shots[i-1]['id'],shots[i]['id']))
    if shots[i].get('insert_id') and shots[i].get('insert_id')==shots[i-1].get('insert_id'): errs.append(('adjacent insert',shots[i-1]['id'],shots[i]['id']))
for r in shots:
    if not (r['count_display']==r['planet_m']==LADDER[str(r['day'])]): errs.append(('ladder',r['id'],r['day'],r['planet_m']))
beats_covered=set(r['beat'] for r in shots); assert beats_covered==set(BEATS), set(BEATS)-beats_covered
from collections import Counter
uses=Counter(r['insert_id'] for r in shots if r.get('insert_id'))
uniq=sum(1 for r in shots if r['reuse']=='unique')
print('shots',len(shots),'unique',uniq,'inserts',len(shots)-uniq,'errs',errs)
print('insert uses',dict(uses))
# pip mouth-visible shots vs script mouth:ON lines
lines=json.load(open('/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet/script_lines_v1.json'))
on_beats=Counter(l['beat'] for l in lines if l['speaker']=='PIP' and l['mouth']=='ON')
mv_beats=Counter(r['beat'] for r in shots if 'PIP' in r['mouth_visible'])
print('PIP ON lines per beat',dict(on_beats)); print('PIP mouth_visible shots per beat',dict(mv_beats))
print('mismatch',{b:(on_beats.get(b,0),mv_beats.get(b,0)) for b in set(on_beats)|set(mv_beats) if on_beats.get(b,0)!=mv_beats.get(b,0)})
man={"title":"Shrinking Planet","version":"v1","runtime":"20:00","art_style":ART_STYLE,
 "ladder":LADDER,
 "ladder_note":"Keys 1/5/10/20/25/26/27/28/29/30 are the bible ladder; the extra keys (2,4,6,7,9,14,15,16,19,24) are the intermediate story days used by shots and carry the size in force that day. Convention: ORB visits at midnight and THE COUNT rolls the day over at the instant the planet shrinks, so the pre-shrink half of an offer beat is tagged to the previous day (e.g. Day 4 · 1000 M → Day 5 · 500 M inside B09).",
 "devices":{"RED_LINE":"quit device — painted ring around the landing pad; cross it and BOTH go home with nothing (B05 open, B30 pay: nobody crossed)","LAUNCH_KEY":"steal device — brass key on a platter inside the ring from Day 25; turning it launches the one-seat pod with the whole prize (B21 open, B28 pay: never turned)"},
 "characters":CHARS,"seed_masters":SEEDS,
 "planet_master_note":"12-m (Day 26) and 7-m (Day 27) planets are scale composites derived from M_PLANET_20 and M_PLANET_4 respectively; the 100-m dome offer (B15) is a hologram overlay on M_PLANET_300, not a planet master.",
 "insert_library":{k:v for k,v in ins_first.items()},
 "counts":{"shots":len(shots),"unique":uniq,"inserts":len(shots)-uniq,"beats":len(BEATS)},
 "shots":shots}
json.dump(man,open(OUT,'w'),indent=1,ensure_ascii=False); print('wrote',OUT)
