#!/usr/bin/env python3
"""v2 storyboard — "We Snuck Into a Dinosaur Zoo (Then the Teens Ruined It)" (owner pivot 2026-07-07).
Source of truth = v2/SHOOTING_SCRIPT_v2.md (89 scenes, Luke+GF, DINO ZOO brand) + v2/PIVOT_PLAN.md.
Supersedes the Dee/Maya v1 board (kept in git history).

v2 build rules (PIVOT_PLAN):
 - viewing_mode infrastructure baked into EVERY image prompt (the v1 quality fix) — see VIEW map.
 - DINO ZOO brand kit in every prompt (IMG prefix); character/creature tags expand via characters_v2.txt.
 - Cold-open flashes S03-S12 = TRIMS of Act 3 payoff clips (no new generation).
 - GEN shots >6s carry a "Grok EXTEND" flag in the Edit column (Grok gens 6s natively).
 - Silent connective TRIMs ONLY where Sik has them: T-Rex walk-ups (4x6s=24s vs his 24s),
   Hybrid dread stack 6+1+6 +6s overlook (19s vs his 19s); Climax already 19s silent as written
   (S82/S83/S85/S86) vs his Incident 19.5s. Sauropods/herbivores get ZERO added silence (measured).
 - S13 line says "Dino Zoo" (owner renamed the park; script draft said "Dinoverse Park").
 - Status preservation only inherits from a v2 TSV (first row "0 Cold Open") — never from the v1 board,
   whose S-numbers collide but mean different shots.
"""
import csv, os

COLS=["Scene","Shot","Time","Dur","Beat","Speaker","On-screen","Camera",
      "Image prompt (still)","Grok video prompt (i2v)","Dialogue / VO",
      "SFX & ambience","Music bed","Clip type","Edit / transition","Status"]

# Sik's verified image-prompt style (VERIFIED_PROMPTS.md ①) + brand kit front-loaded.
IMG=("16:9, photorealistic documentary photography, zoo photography, wildlife photography style, "
     "DINO ZOO (modern dinosaur theme park; round green DINO ZOO logo bottom-right on all signage, "
     "carved-wood zone signs, yellow-black hazard striping, khaki staff uniforms): ")
SUF=("; natural realistic daylight, natural colors, balanced shadows, realistic skin textures and "
     "accurate anatomy and proportions, grounded and believable, real-world scale and perspective, "
     "clear focus on the main subject, non-cinematic, Discovery Channel realism; no text or captions "
     "other than the described signage, no fog, no movie-style color grading.")

# PIVOT_PLAN §1 — viewing_mode -> concrete infrastructure language, appended to every GEN prompt.
VIEW={
 "glass":"seen through thick laminated viewing glass with steel mullions, faint reflections and hand smudges on the pane",
 "tunnel":"inside a curved acrylic viewing tunnel, water and the animal overhead, tourists silhouetted along the walkway",
 "dome":"inside a vast geodesic glass-and-net aviary dome, sunlight breaking through the panels",
 "rail":"a sturdy wooden visitor rail and a dry moat between the guests and the animal",
 "keeper":"a khaki DINO ZOO keeper on a low staff platform with the juvenile, guests watching from behind the wooden visitor rail",
 "tank":"tiered stadium seating packed with guests around the open show tank, splash-zone warning signs on the front rows",
 "":"",
}

R=[]; _t=[0.0]
def _fmt(s):
    m=int(s//60); r=round(s-60*m,1)
    return f"{m}:{int(r):02d}" if r==int(r) else f"{m}:{r:04.1f}"
def _time(dur):
    a=_t[0]; _t[0]=a+dur; return f"{_fmt(a)}-{_fmt(_t[0])}"

def G(cam,move,sound,dia):
    d=dia if dia!="-" else "NONE — silent shot, do NOT invent speech"
    return (f"Cam: {cam}. Move: {move}. Env: real zoo doc, flat daylight, no cinematic/fog. "
            f"Sound: {sound}. Dialogue: {d}. Style: non-cinematic, grounded, exact-env-match, 16:9.")

def gen(scene,shot,dur,beat,spk,view,on,cam,imgd,move,sound,dia,sfx,mus,edit="Hard cut"):
    if dur>6.01: edit+=f" — gen 6s, Grok EXTEND to {dur:g}s"
    img=IMG+imgd+(", "+VIEW[view] if view else "")+SUF
    R.append([scene,shot,_time(dur),f"{dur:g}s",beat,spk,on,cam,img,G(cam,move,sound,dia),dia,sfx,mus,"GEN",edit,"todo"])
def trim(scene,shot,dur,beat,spk,on,src,dia,sfx,mus,edit):
    R.append([scene,shot,_time(dur),f"{dur:g}s",beat,spk,on,"(trim of "+src+")",
              "(trim of "+src+" - NO new generation)","(trim of "+src+")",dia,sfx,mus,"TRIM",edit,"todo"])
def card(scene,shot,dur,beat,on,dia,mus,edit):
    R.append([scene,shot,_time(dur),f"{dur:g}s",beat,"(card)",on,"static","n/a text card","n/a",dia,"-",mus,"CARD",edit,"todo"])

# ============ ACT 0 — COLD OPEN (12 fast beats; S03-S12 are TRIMS of Act 3 payoffs) ============
CO="0 Cold Open"
card(CO,"S01",2.0,"Title/disclaimer card","Black card + round green DINO ZOO logo + 'AI-generated for entertainment'",
     'LUKE VO: "So last time, we barely made it out of the dinosaur zoo alive."',"trailer sting","2.0s static, hard cut")
gen(CO,"S02",3.0,"Host selfie at the gate","LUKE / GF","",
    "Luke + GF at the gate, grinning at the camera","selfie arm's-length, slight sway",
    "[LUKE][GF] selfie-angle shot at the carved-wood DINO ZOO entrance gate, Luke's arm extended holding the camera, his girlfriend beside him grinning, morning crowd streaming in behind them",
    "both grin; GF leans in; crowd flows behind","cheerful crowd, gate turnstiles",
    'GF: "This time we found the part they really didn\'t want us to see."',"-","trailer sting","Hard cut")
trim(CO,"S03",1.5,"Flash: Carnotaurus roars","LUKE VO","1.5s: Carnotaurus roaring under red alarm light","S80 (Carno under red alarm)",
     'LUKE VO (over the whole montage): "A T-Rex. A raptor pack. Two hybrids that should not exist... and three kids who thought a locked door was a dare."',
     "roar","trailer sting","1.5s flash, hard cut")
trim(CO,"S04",1.5,"Flash: Utahraptor pack sprints","LUKE VO","1.5s: the feathered pack sprinting the fence line","S48 (pack running the fence)","(VO continues)","sprint, chitter","trailer sting","1.5s flash")
trim(CO,"S05",1.5,"Flash: Mosasaurus breaches","LUKE VO","1.5s: the Mosa erupting from the show tank","S38 (Mosa feeding show breach)","(VO continues)","breach, splash","trailer sting","1.5s flash")
trim(CO,"S06",1.5,"Flash: Dunkleosteus jaws snap at glass","LUKE VO","1.5s: bone blades snap shut at the pane","S36 (Dunkle bite feeding)","(VO continues)","muffled CLACK","trailer sting","1.5s flash")
trim(CO,"S07",1.5,"Flash: T-Rex slams the window","LUKE VO","1.5s: the roar that shakes the glass","S67 (T-Rex roar at glass)","(VO continues)","roar, glass rattle","trailer sting","1.5s flash")
trim(CO,"S08",1.5,"Flash: Quetzal dives on a picnic table","LUKE VO","1.5s: wings crash onto the abandoned food court","S84 (Quetzal picnic raid)","(VO continues)","wing whoosh, trays clatter","trailer sting","1.5s flash")
trim(CO,"S09",1.5,"Flash: Indominus bursts through a wall","LUKE VO","1.5s: the pale hybrid through the service wall","S82 (Indominus wall breach)","(VO continues)","wall crash","trailer sting","1.5s flash")
trim(CO,"S10",1.5,"Flash: D-Rex silhouette in smoke","LUKE VO","1.5s: the black hybrid stalking through smoke","S83 (D-Rex in the plaza smoke)","(VO continues)","low rumble","trailer sting","1.5s flash")
trim(CO,"S11",1.5,"Flash: teens at the door","GF VO","1.5s: three teens easing open the red STAFF ONLY door","S69 (teens sneak in)",'GF VO: "Remember them."',"door creak","trailer sting","1.5s flash")
trim(CO,"S12",2.0,"Showdown tease","LUKE VO","2s: T-Rex vs two hybrids, crowd fleeing","S88 (three-way showdown)",
     'LUKE VO: "Stay till the end. You will not believe how this one ended."',"roars, alarm","trailer sting","2.0s flash -> HARD CUT to arrival")

# ============ ACT 1 — ARRIVAL ============
EN="1 Entry"
gen(EN,"S13",6.5,"Host intro (owner rename: 'Dino Zoo', not 'Dinoverse Park')","LUKE / GF","",
    "Selfie-POV walking in just inside the gate, GF mid-eyeroll","selfie arm's-length, walking",
    "[LUKE][GF] selfie-angle walking shot just inside the DINO ZOO entry plaza, girlfriend beside him rolling her eyes, banners and holiday crowd behind",
    "both walk; GF eyerolls then smirks","crowd, distant creature call",
    'LUKE: "Okay - we\'re back at Dino Zoo." GF: "You said that like it\'s a good thing." LUKE: "It\'s got the best dinos on earth-" GF: "-and the worst safety record."',
    "-","upbeat doc bed IN","Hard cut")
gen(EN,"S14",6.0,"Ticket booth gag","CLERK / LUKE","",
    "POV hand takes tickets from the clerk","locked POV, slight sway",
    "[LUKE-POV][CLERK] first-person POV at a carved-wood DINO ZOO ticket booth window, Luke's hand taking two paper tickets from the smiling young clerk leaning out",
    "clerk hands tickets, smiles","booth window, crowd murmur",
    'CLERK: "Two adults?" LUKE: "Any chance of a discount for repeat trauma?" CLERK (smiling): "...same price for everyone, sir."',
    "-","upbeat doc bed","Hard cut")
gen(EN,"S15",6.0,"Walk in — packed park","GF / LUKE","",
    "POV into the packed main plaza, GF a step ahead","walking POV",
    "[GF] first-person POV walking into the packed DINO ZOO main plaza, girlfriend a step ahead looking around at the dense crowd, zone banners overhead",
    "walk forward; crowd flows; GF turns back to camera","dense crowd, footsteps",
    'GF: "Whoa. It\'s packed today." LUKE: "Everyone\'s here for the new exhibit. The one they\'ve been hyping."',
    "-","upbeat doc bed","Hard cut")
gen(EN,"S16",5.0,"Park map — the hybrid tease","LUKE / GF","",
    "POV finger traces the park map, lands on a red [!] zone","locked POV close",
    "[LUKE-POV] first-person close-up of Luke's finger tracing a large painted DINO ZOO park map board, stopping on a zone marked with a red [!] and 'HYBRID ENCLOSURE - STAFF ONLY'",
    "finger traces the path, taps the [!] zone","crowd behind, paper map board tap",
    'LUKE: "...\'Hybrid Enclosure - Staff Only.\' Why would a zoo have a staff-only dinosaur?" GF: "Luke. No." LUKE: "I\'m just reading."',
    "-","upbeat doc bed, curious turn","Hard cut")

# ============ ACT 2 — THE TOUR ============
CA="2 Carnotaurus"
gen(CA,"S17",6.0,"Zone gate sign","LUKE","",
    "Carved-wood CARNOTAURUS gate","walking POV",
    "[GF] first-person POV approaching a carved-wood 'CARNOTAURUS' zone gate sign with yellow-black hazard striping, girlfriend beside, path curving into the exhibit",
    "walk toward the gate; GF points","crowd, birds, footsteps",
    'LUKE: "First up - Carnotaurus. The one with the horns."',"-","light doc bed","Hard cut")
gen(CA,"S18",6.0,"BABY — keeper cradles the hatchling","KEEPER / GF","keeper",
    "Keeper cradles a 3-week-old Carno hatchling","handheld",
    "[KEEPER][CARNO] the keeper cradling a three-week-old Carnotaurus hatchling with tiny horn buds, guests leaning in",
    "hatchling squirms; keeper steadies it; guests lean in","crowd aww, tiny squeak",
    'KEEPER: "This little guy\'s only three weeks old." GF: "He\'s adorable-" KEEPER: "-and he\'ll be two tons of adorable in a year."',
    "-","light doc bed","Hard cut")
gen(CA,"S19",6.0,"The adult","LUKE","glass",
    "Adult Carnotaurus pacing","slow pan",
    "[CARNO] adult horned Carnotaurus pacing its dusty scrub enclosure, head swinging",
    "carno paces; head swings toward the crowd","low huff, crowd murmur",
    'LUKE: "There\'s the grown-up. Look at those horns."',"-","light doc bed","Hard cut")
gen(CA,"S20",5.0,"Close at the glass (NEW angle)","GF","glass",
    "Head fills the pane; kids flinch","locked close",
    "[CARNO] the Carnotaurus head filling the viewing pane at point-blank range, a row of kids flinching back in the foreground",
    "head presses close; kids flinch back","muffled breath on glass, gasps",
    'GF: "He is right there."',"-","light doc bed","Hard cut")
gen(CA,"S21",6.0,"BABY — adult + juvenile","LUKE","glass",
    "Mom and baby together","slow push-in",
    "[CARNO] adult Carnotaurus standing over its juvenile in the enclosure, the young one mirroring its posture",
    "juvenile mirrors the adult's steps","low calls, crowd",
    'LUKE: "Mom and baby together. Fun fact - Carnotaurus used those horns to fight each other for territory."',
    "-","light doc bed","Hard cut")
gen(CA,"S22",6.0,"Rival display + comment bait","LUKE","glass",
    "Two adults face off, horns lowered","slow pan",
    "[CARNO] two adult Carnotaurus facing off in a horns-lowered rival display, dust rising between them",
    "the two circle, horns lowered; dust kicks","snorts, scraping dirt, crowd",
    'LUKE: "So - who do you think its real rival was? Drop it in the comments. We\'ll settle it."',
    "-","light doc bed","Hard cut (comment CTA)")
gen(CA,"S23",4.5,"'?' sign transition (NEW)","GF","",
    "Big carved '?' curiosity sign on the path","walking POV",
    "[GF] first-person POV passing a big carved-wood '?' curiosity sign on the path between zones, girlfriend shrugging at the camera",
    "walk past the sign; GF shrugs to camera","footsteps, crowd, birds",
    'GF: "Do you think dinosaurs were ever actually real? ...asking for the internet."',
    "-","light doc bed","Hard cut (comment CTA)")

QU="3 Quetzalcoatlus"
gen(QU,"S24",7.0,"Giant statue landmark (NEW)","LUKE / GF","",
    "Life-size Quetzal statue towers over the plaza","awe tilt-up",
    "[GF] a life-size Quetzalcoatlus statue towering over the zone entrance plaza, tourists photographing it, carved-wood 'QUETZALCOATLUS' sign at its base, girlfriend tiny beside it",
    "tilt up the statue; GF looks up","crowd, camera shutters",
    'LUKE: "Okay THAT is huge." GF: "That\'s just the statue." LUKE: "...oh no."',
    "-","light doc bed","Hard cut")
gen(QU,"S25",6.0,"BABY — keeper with hatchling","KEEPER / GF","keeper",
    "Fuzzy Quetzal hatchling on the keeper's glove","handheld",
    "[KEEPER][QUETZ] the keeper holding a fuzzy Quetzalcoatlus hatchling perched on her heavy glove, its beak already comically long",
    "hatchling flaps for balance; keeper steadies","crowd aww, squawk",
    'KEEPER: "Baby Quetzals can fly minutes after hatching." GF: "Minutes?!"',
    "-","light doc bed","Hard cut")
gen(QU,"S26",5.0,"BABY — chick flight test (NEW)","LUKE","glass",
    "Fuzzy chick flaps off a perch","locked",
    "[QUETZ] a fuzzy Quetzalcoatlus chick flapping off a low perch in a nursery enclosure, caught mid-hop, wings spread",
    "chick hops off the perch, glide-flaps, lands","flap, tiny squawks, crowd laugh",
    'LUKE: "He just... yep. He\'s flying. That\'s terrifying and cute."',
    "-","light doc bed","Hard cut")
gen(QU,"S27",6.0,"The adult in the dome","GF","dome",
    "Adult stands giraffe-tall","slow tilt up",
    "[QUETZ] adult Quetzalcoatlus standing giraffe-tall on the dome floor among low scrub, guests dwarfed on the walkway",
    "it strides slowly on folded wings, head high","echoing calls, wind through net",
    'GF: "Their wingspan\'s bigger than a small plane."',"-","light doc bed","Hard cut")
gen(QU,"S28",6.0,"Flight overhead","LUKE","dome",
    "Two bank overhead through the dome","tilt, tracking",
    "[QUETZ] two Quetzalcoatlus banking overhead through the dome interior, huge shadows sweeping across the guests below",
    "the pair bank and cross overhead; shadows sweep","wing rush, awed crowd",
    'LUKE: "Imagine looking up and seeing that."',"-","light doc bed","Hard cut")
gen(QU,"S29",6.0,"Looming at the tunnel","LUKE","tunnel",
    "One stalks alongside the walkway tunnel, beak inches away","locked, slight sway",
    "[QUETZ] a Quetzalcoatlus looming right over the walkway tunnel through the aviary, its huge beak inches above the curved acrylic",
    "the beak tracks along the tunnel; guests duck instinctively","muffled steps on acrylic, nervous laughs",
    'LUKE: "One of its rivals was another giant flyer, Hatzegopteryx. ...you\'ll want to Google that spelling."',
    "-","light doc bed","Hard cut")
gen(QU,"S30",5.0,"Exterior + comment bait","GF / LUKE","",
    "Aviary dome from outside, silhouettes through the panels","walking POV",
    "[GF] exterior of the geodesic aviary dome from the path, Quetzalcoatlus silhouettes visible through the glass panels, girlfriend walking beside",
    "walk along the dome; a silhouette glides inside","crowd, birds",
    'GF: "How long did these even live?" LUKE: "Twenty, thirty years, they think. What do you think?"',
    "-","light doc bed","Hard cut (comment CTA)")

AQ="4 Aquatic"
gen(AQ,"S31",6.0,"Swamp boardwalk dining (NEW transition)","GF / LUKE","",
    "Boardwalk food terrace over the swamp","walking POV",
    "[GF] a boardwalk dining terrace over a swamp lagoon, food kiosks with carved-wood menus, families eating, cypress trees, girlfriend eyeing the food",
    "walk the boardwalk; GF gestures at the food","water lap, cutlery, crowd",
    'GF: "Ooh, food. Later." LUKE: "Later. Water first."',"-","light doc bed","Hard cut")
gen(AQ,"S32",5.0,"Aquatic gate","LUKE","",
    "Carved AQUATIC LIFE ENCLOSURE gate","walking POV",
    "[GF] first-person POV approaching the carved-wood 'AQUATIC LIFE ENCLOSURE' gate with wave motifs and hazard striping, girlfriend beside",
    "walk toward the gate","crowd, gulls, water",
    'LUKE: "\'Aquatic Life Enclosure.\'"',"-","light doc bed","Hard cut")
gen(AQ,"S33",5.0,"Facade","LUKE","",
    "The huge curved aquatic complex","slow tilt",
    "the facade of the aquatic complex - a huge curved building with a wave-shaped roof and glass front, crowds filing in",
    "crowd files in; banners sway","crowd, doors, water ambience",
    'LUKE: "This is the one I wanted."',"-","light doc bed","Hard cut")
gen(AQ,"S34",5.0,"BABY — Dunkleosteus fry (NEW)","GF","glass",
    "Hand-sized armored fry school at the nursery pane","locked close",
    "[DUNK] a nursery tank of hand-sized armored Dunkleosteus fry schooling against the pane, tiny bone head-shields catching the light",
    "the fry school and turn as one","filtered water hum, crowd aww",
    'GF: "Those are... babies? They look like tiny tanks."',"-","light doc bed","Hard cut")
gen(AQ,"S35",6.0,"The adult Dunkleosteus","LUKE","glass",
    "The 6m adult glides past","slow tracking",
    "[DUNK] the adult six-meter Dunkleosteus gliding past in dark green water, plated head shield and bone shear-blades clearly visible",
    "it glides past, jaw slightly working","deep water hum, muffled crowd",
    'LUKE: "Meet Dunkleosteus. No teeth - just self-sharpening bone blades."',"-","light doc bed","Hard cut")
gen(AQ,"S36",6.0,"Bite feeding","GF","glass",
    "Jaws shear a fish in half","locked",
    "[DUNK] the Dunkleosteus mid-bite shearing a large fish clean in half, bone blades exposed, water clouding with scales",
    "jaws snap the fish; the halves drift; it circles back","muffled CLACK, crowd reaction",
    'GF: "Okay I felt that in my soul."',"bite CLACK SFX","light doc bed","Hard cut, SFX")
gen(AQ,"S37",5.0,"Arena approach (NEW transition)","LUKE","",
    "Ramp toward the show arena","walking POV",
    "[GF] first-person POV walking a ramp toward the show arena, carved-wood 'MOSASAURUS FEEDING SHOW' sign overhead, crowd flowing the same way",
    "walk with the crowd up the ramp","excited crowd, distant PA",
    'LUKE: "And through here - feeding time for the big one."',"-","light doc bed","Hard cut")
gen(AQ,"S38",12.0,"Mosasaurus feeding show (12s HOLD)","RANGER / LUKE","tank",
    "Crane hoists meat; the Mosa breaches","wide, locked with shake on breach",
    "[MOSA][RANGER] a crane hoisting a slab of meat over the open show tank as the enormous Mosasaurus erupts from the water with jaws wide, splash wall over the front rows, ranger with a mic on the show platform",
    "crane swings the meat out; the Mosa breaches, snaps it, crashes back; splash soaks the front rows","PA echo, crowd roar, huge splash",
    'RANGER (mic): "Ladies and gentlemen - the Mosasaurus." (crowd gasps) LUKE: "No thank you."',
    "BREACH + splash SFX","light doc bed, swell on breach","Hard cut, SFX")
gen(AQ,"S39",6.0,"Mosa + prey","GF","glass",
    "The Mosa glides past, shoal scattering","slow tracking",
    "[MOSA] the Mosasaurus gliding past the huge viewing wall, a shoal of fish scattering ahead of it",
    "it cruises past; the shoal parts around it","deep water, muffled awe",
    'GF: "It\'s the size of a bus."',"-","light doc bed","Hard cut")
gen(AQ,"S40",12.0,"Dunkle + Mosa tunnel (12s money shot)","LUKE","tunnel",
    "Both glide over the tunnel together","slow tilt along the tunnel",
    "[DUNK][MOSA] both the Dunkleosteus and the Mosasaurus gliding together over the acrylic tunnel, tourists beneath looking straight up",
    "the two pass overhead in slow layers; guests turn beneath them","muffled water, hushed crowd",
    'LUKE: "Do you think these two could actually live in the same water? ...I genuinely don\'t know. Tell me."',
    "-","light doc bed","Hard cut (comment CTA)")
gen(AQ,"S41",5.0,"Dome exterior (NEW transition)","GF / LUKE","",
    "Exiting the aquatic dome","walking POV",
    "[GF] exterior of the aquatic dome in late-morning light, guests exiting, girlfriend walking beside the camera",
    "walk out; GF turns to camera; Luke's view drifts off-frame","crowd, gulls",
    'GF: "That was incredible." LUKE (quieter): "...hey. Look."',"-","light doc bed","Hard cut")
gen(AQ,"S42",6.0,"TEENS at the Staff Only door","LUKE / GF","",
    "Three teens loitering by the red door","locked candid, long-ish lens feel",
    "[TEENS] three teenagers loitering by a red steel door stenciled 'STAFF ONLY - HYBRID DANGER' with yellow-black hazard striping, glancing around, tucked in a quiet corner of the park",
    "the teens shuffle, glance around, one tries the handle","quiet crowd, distant PA",
    'LUKE: "Those kids have been by that door twice now." GF: "Not our problem. Keep walking."',
    "-","unsettling doc bed","Hard cut")

UT="5 Utahraptor"
gen(UT,"S43",5.0,"Zone gate","LUKE","",
    "Carved UTAHRAPTOR gate","walking POV",
    "[GF] first-person POV approaching a carved-wood 'UTAHRAPTOR' zone gate sign with claw-mark motif and hazard striping, girlfriend beside",
    "walk toward the gate","crowd, birds",
    'LUKE: "Next - and this is the one people always get wrong."',"-","light doc bed","Hard cut")
gen(UT,"S44",6.0,"BABY — keeper with feathered chick","KEEPER / GF","keeper",
    "Feathered raptor chick on the keeper's glove","handheld",
    "[KEEPER][RAPTOR] the keeper kneeling with a FEATHERED Utahraptor chick perched on her glove, downy slate plumage clearly visible",
    "the chick head-tilts and nibbles the glove; keeper steadies","chirps, crowd aww",
    'KEEPER: "Careful - they imprint fast." GF: "It\'s covered in feathers." KEEPER: "They all were."',
    "-","light doc bed","Hard cut")
gen(UT,"S45",6.0,"BABY — juveniles in the nursery (NEW)","GF","glass",
    "Two feathered juveniles trot","locked",
    "[RAPTOR] two FEATHERED Utahraptor juveniles trotting across a nursery pen, tail fans out for balance",
    "the two trot and pivot in sync","scratching claws, chirps, crowd",
    'GF: "I could watch these all day."',"-","light doc bed","Hard cut")
gen(UT,"S46",13.0,"RANGER MYTH-BUST (13s centerpiece — plays DRY, no music)","RANGER / LUKE","",
    "Ranger addresses the group; adult raptor behind the fence; size-comparison board","locked, slight sway",
    "[RANGER][RAPTOR] the ranger addressing a small tour group in front of the open-air raptor paddock, an adult FEATHERED Utahraptor watching from behind the fence, a turkey-vs-man size comparison board mounted on the rail",
    "ranger gestures at the board then the animal; the raptor watches, perfectly still",
    "quiet crowd, wind, a single raptor chirp",
    'RANGER: "Here\'s what the movies got wrong. The famous \'velociraptors\'? Real velociraptors were the size of a turkey. What Hollywood actually drew - this size, this build - that\'s a Utahraptor. They just kept the cooler-sounding name." LUKE: "So every raptor you\'ve ever feared... was basically this guy, with a rebrand."',
    "-","NO MUSIC — plays dry","Hard cut")
gen(UT,"S47",6.0,"The pack","GF","glass",
    "The whole pack, alert","slow pan",
    "[RAPTOR] a pack of five FEATHERED Utahraptors standing alert in their paddock, heads flicking in coordination",
    "heads flick in sequence; one steps forward","chitters, crowd murmur",
    'GF: "And there\'s a whole pack."',"-","light doc bed","Hard cut")
gen(UT,"S48",6.0,"Pack running the fence","LUKE","",
    "The pack sprints the fence line","fast tracking pan",
    "[RAPTOR] the FEATHERED Utahraptor pack sprinting along the tall paddock fence line in eerie sync, dust kicking up, guests at the rail beyond",
    "the pack bolts along the fence in sync; dust trails","sprinting feet, chitter burst, gasps",
    'LUKE: "They hunt in coordination. That\'s the scary part."',"sprint SFX","light doc bed","Hard cut, SFX")
gen(UT,"S49",5.0,"Stare-down at the glass (NEW angle)","GF / LUKE","glass",
    "One raptor locks eyes with GF","locked close",
    "[GF][RAPTOR] a FEATHERED Utahraptor at the viewing pane, its eye locked on the girlfriend inches away on the other side",
    "the raptor holds the stare, pupil narrowing; GF frozen","low chitter, held breath",
    'GF (low): "...it\'s looking at me." LUKE: "It\'s definitely looking at you."',"-","light doc bed","Hard cut")
gen(UT,"S50",5.0,"Banter transition + quiz CTA","LUKE","",
    "Walking out of the raptor zone","walking POV",
    "[GF] first-person POV walking out of the raptor zone past greenery, girlfriend beside talking to the camera",
    "walk out; GF talks to camera","footsteps, crowd, birds",
    'LUKE: "Comment \'Utahraptor\' if you learned something. Let\'s give the internet a quiz."',
    "-","light doc bed","Hard cut (comment CTA)")

HE="6 Herbivores"
gen(HE,"S51",5.0,"Zone gate","GF","",
    "Carved HERBIVORE VALLEY gate","walking POV",
    "[GF] first-person POV approaching a carved-wood 'HERBIVORE VALLEY' gate sign, softer landscaping, girlfriend visibly relaxing",
    "walk toward the gate; GF exhales","crowd, birdsong",
    'GF: "Finally. Something that won\'t eat us."',"-","calm warm bed","Hard cut")
gen(HE,"S52",6.0,"Styracosaurus","LUKE","rail",
    "Styracosaurus grazing","slow pan",
    "[STYRACO] a Styracosaurus grazing in an open meadow paddock, spiked frill catching the sun",
    "it grazes; frill tilts as it looks up","chewing, birdsong, crowd",
    'LUKE: "Styracosaurus - all those spikes are just for show. Mostly."',"-","calm warm bed","Hard cut")
gen(HE,"S53",6.0,"BABY — calf + mother (NEW)","GF","rail",
    "Calf nuzzles mom","slow push-in",
    "[STYRACO] a Styracosaurus calf nuzzling against its mother's leg, the mother lowering her frilled head to it",
    "the calf nuzzles; mom lowers her head gently","soft calls, crowd aww",
    'GF: "Okay THAT\'S the cutest thing here."',"-","calm warm bed","Hard cut")
gen(HE,"S54",6.0,"Brachiosaurus","LUKE","rail",
    "Brachiosaurus reaches into the canopy","slow tilt up",
    "[BRACHIO] a Brachiosaurus reaching its crane neck into the tree canopy, stripping leaves, tourists tiny at the rail below",
    "the neck sweeps up; leaves shower down","deep footfall, leaves, crowd",
    'LUKE: "Brachiosaurus. That neck\'s basically a crane."',"-","calm warm bed","Hard cut")
gen(HE,"S55",10.0,"Argentinosaurus adult+juv (10s — the biggest)","GF / LUKE","rail",
    "Towering wide, adult with juvenile beneath","very slow rising wide",
    "[ARGENTINO] a towering wide shot of the Argentinosaurus adult with its juvenile walking beneath it, tourists ant-sized at the rail, the animal filling the sky",
    "the pair walk slowly; the ground-shake reads in the crowd","slow seismic footfalls, awed hush",
    'GF: "...how is that real." LUKE: "Biggest animal to ever walk the earth. Ate 150 kilos of plants a day."',
    "-","calm warm bed","Hard cut")
gen(HE,"S56",6.0,"BABY — family crossing","LUKE","rail",
    "Herbivores + young cross together","wide locked",
    "[STYRACO][BRACHIO] a mixed group of herbivores crossing a shallow stream together with their young between the adults, seen over the visitor rail",
    "the family crosses; a young one splashes","splashes, calls, crowd",
    'LUKE: "Whole family crossing together."',"-","calm warm bed","Hard cut")
gen(HE,"S57",6.0,"Fact / banter","GF / LUKE","rail",
    "At the rail, gastroliths banter","handheld",
    "[GF] the girlfriend at the wooden visitor rail turning to the camera mid-question, herbivores grazing beyond the dry moat",
    "GF turns to camera; a sauropod swallows in the background","crowd, chewing, birds",
    'GF: "Wait - sauropods swallowed rocks?" LUKE: "To grind food in their stomach. No teeth needed."',
    "-","calm warm bed","Hard cut")
gen(HE,"S58",5.0,"TEENS glimpse","GF / LUKE","",
    "The teens drifting back toward the hybrid zone","candid long-ish",
    "[TEENS] the same three teenagers across the plaza, drifting back toward the hybrid zone, one checking over his shoulder",
    "the teens walk off; one glances back","crowd, distant PA",
    'GF: "...those kids are heading the wrong way." LUKE: "Yeah. Toward the door."',
    "-","unsettling doc bed","Hard cut")

LU="7 Lunch"
gen(LU,"S59",5.0,"Walk to food","LUKE","",
    "POV toward the lakeside food deck","walking POV",
    "[GF] first-person POV walking toward a lakeside food deck with smoking BBQ grills and carved-wood menu boards, girlfriend leading the way",
    "walk toward the deck; GF beckons","grill sizzle, crowd, water",
    'LUKE: "Okay, NOW food."',"-","warm mellow bed","Hard cut")
gen(LU,"S60",8.0,"BBQ + teen callback (8s) — MIDROLL SLOT","GF / LUKE","",
    "Lakeside deck, ribs, Luke raises a drink","locked table POV",
    "[LUKE-POV][GF] a lakeside BBQ deck table with a rack of ribs, Luke's hand raising a drink, girlfriend across the table mid-bite, calm water behind",
    "GF eats; Luke's hand raises the drink; a pause lands","deck ambience, water, cutlery",
    'GF: "This is nice. Peaceful." LUKE: "...you don\'t think those kids actually got in, do you?" GF (pause): "...eat your ribs, Luke."',
    "-","warm mellow bed","Hard cut — MIDROLL SLOT (set the ad break here in Studio)")

TR="8 T-Rex"
gen(TR,"S61",5.0,"Zone gate","LUKE","",
    "Carved T-REX gate, heavier hazard striping","walking POV",
    "[GF] first-person POV approaching a carved-wood 'T-REX' zone gate with double hazard striping and taller reinforced fencing beyond, girlfriend beside",
    "walk toward the gate","crowd hush, distant deep call",
    'LUKE: "The one everyone\'s waiting for. T-Rex."',"-","light doc bed, tenser","Hard cut")
gen(TR,"S62",6.0,"BABY — host holds the hatchling","RANGER / LUKE","keeper",
    "Ranger hands the hatchling into Luke's POV hands","handheld POV",
    "[LUKE-POV][RANGER][TREX] the ranger placing a T-Rex hatchling into Luke's first-person POV hands, the hatchling gripping his forearm",
    "the hatchling grips and squeaks; ranger keeps a hand near","squeaks, crowd laugh",
    'RANGER: "Wanna hold him?" LUKE: "...is that safe?" RANGER: "For you or the baby?"',
    "-","light doc bed","Hard cut")
gen(TR,"S63",5.0,"Fossil jaw","LUKE","",
    "Museum case: fossil jaw, 30cm tooth","slow push-in",
    "a fossil T-Rex jaw in a glass museum case inside the exhibit hall, one 30-centimeter tooth highlighted by a spotlight, kids' faces reflected in the case",
    "slow push toward the tooth; reflections shift","quiet hall, murmurs",
    'LUKE: "A single tooth - 30 centimeters, root included."',"-","light doc bed","Hard cut")
gen(TR,"S64",5.0,"Dome walkway — heard before seen","GF","",
    "The walkway toward the dome; GF stops","walking POV, stops",
    "[GF] first-person POV on the walkway toward the T-Rex dome, girlfriend stopped mid-step with a hand half-raised, listening",
    "GF stops, hand up; a distant footfall shivers the frame","deep distant footfall, hush",
    'GF: "I can hear it. Before I can even see it."',"-","light doc bed, low pulse","Hard cut")
gen(TR,"S65",6.0,"It steps into view","LUKE / GF","glass",
    "The T-Rex steps into view","slow reveal",
    "[TREX] the massive T-Rex stepping into full view from behind trees, head swinging toward the viewing wall",
    "it steps out; the head swings to the glass; crowd stills","one deep footfall, crowd hush",
    'BOTH: "Whoa."',"-","light doc bed","Hard cut")
trim(TR,"S65b",6.0,"Silent walk-up 1 (Sik: alternating silents at scene open)","-",
     "6s: the T-Rex just walking, nobody talks","S65 (step into view, different segment)",
     "-","deep footfalls (MUTE trim audio, ambience only)","light doc bed","6s SILENT")
gen(TR,"S66",5.0,"Head at the glass, kids (NEW angle)","GF","glass",
    "The head lowers to a row of kids","locked low",
    "[TREX] the T-Rex head lowering level with a row of kids at the viewing pane, its eye bigger than their heads",
    "the head lowers slowly; the kids crane up","low rumble breath, tiny gasps",
    'GF: "Those kids are so brave. I\'d be gone."',"-","light doc bed","Hard cut")
trim(TR,"S66b",6.0,"Silent walk-up 2 (the stare)","-",
     "6s: the head at the glass, just staring","S66 (head at glass, different segment)",
     "-","low rumble breath (MUTE trim audio, ambience only)","light doc bed","6s SILENT")
gen(TR,"S67",10.0,"THE ROAR (10s)","LUKE","glass",
    "It roars; the pane trembles","locked, shake on roar",
    "[TREX] the T-Rex in full roar at the viewing wall, jaws wide, the pane visibly trembling, guests recoiling",
    "it rears and roars; the glass shivers; crowd recoils","ROAR, glass rattle, screams-then-laughs",
    'LUKE: "Strongest bite of any land animal that ever lived. And that\'s not even the scary one here."',
    "ROAR SFX","light doc bed, swell","Hard cut, SFX")
trim(TR,"S67b",6.0,"Silent aftermath 1 (Sik: 2 silents back-to-back after the peak)","-",
     "6s: the T-Rex settling after the roar, no words","S67 (roar aftermath segment)",
     "-","settling breath (MUTE trim audio, ambience only)","light doc bed","6s SILENT")
trim(TR,"S67c",6.0,"Silent aftermath 2","-",
     "6s: hold the stare a beat longer","S65 (tail end of the walk-up)",
     "-","distant crowd hush (MUTE trim audio, ambience only)","light doc bed","6s SILENT")
gen(TR,"S68",5.0,"Banter turn -> hybrid zone","GF / LUKE","",
    "Walking transition, the dread turn","walking POV",
    "[GF] first-person POV walking out of the T-Rex dome, girlfriend turning to the camera with a questioning look",
    "GF turns with the question; Luke's view drifts toward the hybrid zone","crowd fading, low tone",
    'GF: "What do you mean \'not the scary one\'-" LUKE: "...the hybrid zone."',
    "-","light doc bed -> dread turn","Hard cut")

HY="9 Hybrid"
gen(HY,"S69",6.0,"TEENS SNEAK IN","GF / LUKE","",
    "The teens slip through the propped red door","candid, then whip to GF",
    "[TEENS] the three teenagers slipping one by one through the propped-open red 'STAFF ONLY - HYBRID DANGER' door, the last one holding it",
    "the teens slip through; the door eases shut behind them","door hinge, quiet crowd",
    'GF: "Luke - they just went in." LUKE: "...we have to tell someone."',
    "-","dread drone IN","Hard cut")
gen(HY,"S70",6.0,"BABY — Indominus juveniles","RANGER / -","glass",
    "Two pale juveniles pace; tense ranger","handheld",
    "[INDOMINUS][RANGER] two pale bone-white Indominus juveniles pacing a bare holding pen, a tense ranger turning toward the camera in the foreground",
    "the juveniles pace in mirror; the ranger turns, unsmiling","claws on concrete, hum",
    'RANGER (tense): "You two shouldn\'t be here either. This section\'s not open."',
    "-","dread drone","Hard cut")
gen(HY,"S71",6.0,"Indominus feeding at the moat","LUKE","glass",
    "It snaps meat off a crane","locked",
    "[INDOMINUS] the adult Indominus snapping a slab of meat off a feeding crane across a deep dry moat, seen from a glassed observation deck",
    "it lunges up, snaps the meat, lands heavy","crane winch, snap, thud",
    'LUKE: "That\'s the Indominus. Part T-Rex, part... a lot of things."',"-","dread drone","Hard cut")
gen(HY,"S72",5.0,"Claw-scarred wall (NEW angle)","GF","glass",
    "Deep gouges in the concrete","slow pan along the scars",
    "[INDOMINUS] deep claw gouges raked across the concrete enclosure wall, four parallel channels taller than a person, the animal blurred in the background",
    "slow pan along the gouges; the blur shifts behind","hum, distant scrape",
    'GF: "...did it do that? To the wall?"',"-","dread drone","Hard cut")
gen(HY,"S73",6.0,"Camouflage reveal (NEW angle)","LUKE / GF","glass",
    "It fades into the foliage on camera","locked",
    "[INDOMINUS] the Indominus half-faded against the enclosure foliage, its outline barely visible, skin tone matching the leaves",
    "the outline dissolves into the foliage until only the eye reads","hum, a single leaf-rustle",
    'LUKE: "It can camouflage. One second it\'s there-" GF: "-and then it\'s not."',
    "-","dread drone","Hard cut")
gen(HY,"S74",8.0,"The overlook (8s)","LUKE","",
    "High wide over the deepest enclosure; idle alarm light","high locked, slight sway",
    "a high overlook over the deepest hybrid enclosure complex, reinforced walls and restraint cable anchors below, an idle orange alarm beacon on a mast",
    "nothing moves but the idle beacon; wind sways the frame","wind, faint hum",
    'LUKE: "And this - the deepest one - is the D-Rex."',"-","dread drone","Hard cut")
trim(HY,"S74b",6.0,"Silent overlook (Sik: pre-incident dread)","-",
     "6s: the overlook, just the idle beacon","S74 (overlook, different segment)",
     "-","wind, hum (MUTE trim audio, ambience only)","dread drone","6s SILENT")
gen(HY,"S75",9.0,"D-REX REVEAL (9s)","GF / LUKE","",
    "The massive wrong-looking hybrid emerges","slow reveal",
    "[DREX] the massive D-Rex emerging from its deep pen into half-light, charcoal-black hide with faint glowing orange seams, oversized asymmetric jaws, moving wrong",
    "it emerges one limb at a time; the head swings up last","dragging weight, deep breath",
    'GF (whisper): "...that\'s not a dinosaur. That\'s a monster." LUKE: "People think he\'s a monster. But is he?"',
    "-","dread drone","Hard cut")
gen(HY,"S76",7.0,"TEENS IN DANGER (7s — distance + reaction framing, no contact)","LUKE","",
    "The teens inside the perimeter, filming, too close","wide from the overlook",
    "[TEENS][DREX] a wide shot from the overlook: the three teenagers far below inside the enclosure perimeter holding up phones, the D-Rex looming distant beyond them - clear distance between them, tension from framing not contact",
    "the teens film, oblivious; the D-Rex's head turns their way","wind, faint phone chatter",
    'LUKE (shouting): "HEY - get away from the-"',"-","dread drone, rising","Hard cut")
gen(HY,"S77",5.0,"At the glass, breathing (NEW angle)","GF","glass",
    "Breath fogs the pane inches from a teen","locked close",
    "[TEENS][DREX] the D-Rex's snout inches from the safety pane, its breath fogging the glass, one teen frozen in the foggy reflection",
    "breath fogs and clears the pane in slow pulses; the teen doesn't move","huge slow breathing",
    'GF: "It sees them."',"-","dread drone, peak","Hard cut")
trim(HY,"S77b",6.0,"Silent dread 1 (Sik: 6+1+6 stack before the incident)","-",
     "6s: the breathing at the pane, nobody speaks","S77 (breathing, different segment)",
     "-","slow breathing (MUTE trim audio, ambience only)","dread drone","6s SILENT")
trim(HY,"S77c",1.0,"Silent dread 2 (1s flash)","-",
     "1.0s: flash of the camouflage fade","S73 (camouflage, best 1s)",
     "-","single sub hit","dread drone","1.0s FLASH")
trim(HY,"S77d",6.0,"Silent dread 3","-",
     "6s: the teens frozen, the shape looming","S76 (teens wide, different segment)",
     "-","heartbeat, wind (MUTE trim audio, ambience only)","dread drone","6s SILENT")
gen(HY,"S78",10.0,"BREAKOUT — cables snap (10s)","LUKE","",
    "It rips its restraint cables; sparks","handheld shake",
    "[DREX] the D-Rex rearing back and ripping its restraint cables from their anchors, sparks showering from the snapped mounts, dust erupting",
    "it wrenches free cable by cable; sparks rain; the last anchor gives","cable SNAP, sparks, roar",
    'LUKE: "RUN. RUN-"',"cable SNAP SFX","dread -> alarm/action","Hard cut into the incident")

CL="10 Climax"
gen(CL,"S79",7.0,"Control room breach (7s)","PA","",
    "Red room: SECURITY BREACH / EVACUATE","locked, strobing",
    "a park control room bathed in red emergency light, wall screens reading 'SECURITY BREACH - EVACUATE', staff scrambling between consoles",
    "staff scramble; screens strobe the warning","klaxon, radio chatter",
    'PA: "Containment failure. All guests evacuate immediately."',"klaxon SFX","alarm/action","Hard cut")
gen(CL,"S80",5.0,"Carnotaurus under red alarm (NEW)","GF","glass",
    "The first exhibit again, bathed red","locked",
    "[CARNO] the Carnotaurus enclosure from the morning now bathed in strobing red alarm light, the animal agitated and roaring",
    "it wheels and roars under the strobe","roar, klaxon",
    'GF: "It\'s the whole park."',"-","alarm/action","Hard cut")
gen(CL,"S81",5.0,"Evacuation","LUKE","",
    "Crowd floods out through the food court","fast handheld",
    "a large crowd moving fast through the food court in an urgent evacuation, staff in khaki waving them through, dropped trays and an abandoned stroller - evacuation framing, no panic close-ups",
    "the crowd streams past; staff wave them on","running feet, klaxon, shouts",
    'LUKE: "This way - go, go!"',"-","alarm/action","Hard cut")
gen(CL,"S82",6.0,"Indominus breach (the S09 flash, paid off) — SILENT","-","",
    "It smashes through the wall","locked, debris shake",
    "[INDOMINUS] the Indominus bursting through a concrete service wall into an emptied plaza, debris flying, dust rolling - no people near it",
    "the wall gives; it shoulders through; debris scatters","wall CRASH, roar",
    "-","CRASH SFX","alarm/action","Hard cut — SILENT (no dialogue)")
gen(CL,"S83",4.0,"D-Rex in the plaza — SILENT","-","",
    "The hybrid loose in the smoke","slow push through haze",
    "[DREX] the D-Rex silhouette stalking through drifting smoke across the empty central plaza, orange seams glowing faintly in the haze",
    "it stalks through the smoke, unhurried","low rumble, distant klaxon",
    "-","-","alarm/action","Hard cut — SILENT (no dialogue)")
gen(CL,"S84",5.0,"Quetzal picnic-raid payoff (the S08 flash lands)","GF","",
    "A Quetzal dives on the abandoned food court","fast tilt down",
    "[QUETZ] a Quetzalcoatlus dropping onto the abandoned lakeside picnic tables, wings mantled over the food, trays scattering",
    "it drops in, mantles, snaps up food; trays scatter","wing crash, trays, screech",
    'GF: "FROM THE SKY TOO?!"',"trays clatter SFX","alarm/action","Hard cut")
gen(CL,"S85",5.0,"T-Rex loose — SILENT","-","",
    "The T-Rex out, roaring","low wide, shake",
    "[TREX] the T-Rex striding out through its shattered dome gate, roaring, debris around its feet - emptied paths, no people near it",
    "it strides out and roars skyward","ROAR, klaxon",
    "-","ROAR SFX","alarm/action","Hard cut — SILENT (no dialogue)")
gen(CL,"S86",4.0,"T-Rex toward the city — SILENT","-","",
    "It charges toward the skyline","long-lens wide",
    "[TREX] the T-Rex charging down the empty entry boulevard toward the distant city skyline, banners whipping in its wake",
    "it accelerates away toward the skyline","receding footfalls, wind",
    "-","-","alarm/action","Hard cut — SILENT (no dialogue)")
gen(CL,"S87",4.0,"TEENS rescued / regret (NEW payoff)","TEEN / RANGER","",
    "A ranger yanks the teens behind cover as the D-Rex passes","handheld low",
    "[RANGER][TEENS][DREX] the ranger pulling the three teenagers down behind a concrete planter as the D-Rex thunders past in the background haze - clear separation, no contact",
    "the ranger pulls them down; the shape passes beyond; they shake","thundering pass, breathing",
    'TEEN (shaking): "We\'re sorry - we didn\'t think-" RANGER: "Nobody ever does."',
    "-","alarm/action, drop under the line","Hard cut")
gen(CL,"S88",10.0,"THE SHOWDOWN (10s)","LUKE VO","",
    "T-Rex vs Indominus vs D-Rex, park in ruins","slow wide push",
    "[TREX][INDOMINUS][DREX] the three-way showdown in the ruined central plaza - T-Rex, Indominus and D-Rex circling each other among torn banners and smoke, the DINO ZOO gate broken behind them",
    "the three circle, feint, roar in turn; smoke drifts","layered roars, klaxon dying out",
    'LUKE VO: "Three apex predators. One park. And it started with one unlocked door."',
    "-","action peak","Hard cut")
card(CL,"S89",2.0,"End card","Black + round green DINO ZOO logo + 'PART TWO?'",
     'GF VO: "...we are never coming back." LUKE VO: "Comment which dino you\'d survive. Subscribe - part two if this hits."',
     "sting -> silence","Cut to black, end card (comment CTA)")

# ---- STATUS PRESERVATION (v2-guarded): only inherit from a v2 TSV. The v1 Dee/Maya board reuses
# the same S-numbers for DIFFERENT shots, so inheriting its statuses would mark redone shots done.
old_status={}
if os.path.exists("STORYBOARD.tsv"):
    with open("STORYBOARD.tsv") as f:
        rd=csv.reader(f,delimiter="\t"); hdr=next(rd); rows=list(rd)
    if rows and rows[0][0]=="0 Cold Open":   # v2 marker
        si,sti=hdr.index("Shot"),hdr.index("Status")
        for row in rows:
            if len(row)>sti: old_status[row[si]]=row[sti]
for r in R:
    r[15]=old_status.get(r[1], r[15])

with open("STORYBOARD.tsv","w",newline="") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(COLS); w.writerows(R)

gen_n=sum(1 for r in R if r[13]=="GEN"); trim_n=sum(1 for r in R if r[13]=="TRIM"); card_n=sum(1 for r in R if r[13]=="CARD")
runtime=_t[0]
sil=[(r[0],float(r[3][:-1])) for r in R if r[10]=="-"]
sil_total=sum(d for _,d in sil)
by_zone={}
for z,d in sil: by_zone[z]=by_zone.get(z,0)+d
ext=[r[1] for r in R if "EXTEND" in r[14]]
print(f"rows: {len(R)}  (GEN {gen_n} / TRIM {trim_n} / CARD {card_n})  cols: {len(COLS)}")
print(f"runtime: {_fmt(runtime)} ({runtime:g}s)  silent: {sil_total:g}s ({100*sil_total/runtime:.1f}%)")
print("silent by zone (target Sik: T-Rex 24 / Hybrid 19 / Incident 19.5):",
      {k:round(v,1) for k,v in by_zone.items()})
print(f"EXTEND shots ({len(ext)}):", ", ".join(ext))
