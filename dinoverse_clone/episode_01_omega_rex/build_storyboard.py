#!/usr/bin/env python3
"""Horizontal storyboard v3 - 90-100 clips, matched to the creator's real 764K-view video.
v3 changes vs v2:
 - TRAILER-STYLE INTRO MONTAGE: ~14 rapid 0.5-1.5s flash cuts under the VO hook, each a TRIM of a
   later payoff shot (NOT a new generation) - per his CapCut screenshot (many sub-second clips in the intro).
 - expanded each creature to ~6 shots -> 90+ timeline clips.
 - keeps SPEAKER col (3-voice model), his fact-dense narrator lines, per-creature rival CTA, dark 'MOMMY!' ending.
Two clip types: GEN = unique Grok generation; TRIM = reuse/trim of another shot (no render).
"""
import csv
COLS=["Scene","Shot","Time","Dur","Beat","Speaker","On-screen","Camera",
      "Image prompt (still)","Grok video prompt (i2v)","Dialogue / VO",
      "SFX & ambience","Music bed","Clip type","Edit / transition","Status"]
# Image prompts use the creator's own "Dinosaur Image Prompt Generator" style (Version B, chosen 2026-06-26):
# front-load photography-style tags, name the brand kit, end with quality/realism tags. Verbose on purpose.
IMG="16:9, photorealistic documentary photography, zoo photography, wildlife photography style, DINO ZOO (modern open-air dinosaur theme park, round green logo, yellow-black hazard signs, khaki rangers): "
SUF="; natural realistic daylight, natural colors, balanced shadows, realistic skin textures and accurate anatomy and proportions, grounded and believable, real-world scale and perspective, clear focus on the main subject, non-cinematic, Discovery Channel realism; no text or captions, no fog, no movie-style color grading."
def G(cam,move,sound,dia): return f"Cam: {cam}. Move: {move}. Env: real zoo doc, flat daylight, no cinematic/fog. Sound: {sound}. Dialogue: {dia}. Style: non-cinematic, grounded, exact-env-match, 16:9."
R=[]
def gen(sc,sh,t,dur,beat,spk,on,cam,imgd,gcam,gmove,gsound,dia,sfx,mus,edit):
    R.append([sc,sh,t,dur,beat,spk,on,cam,IMG+imgd+SUF,G(gcam,gmove,gsound,dia),dia,sfx,mus,"GEN",edit,"todo"])
def trim(sc,sh,t,dur,beat,spk,on,payoff,dia,sfx,mus,edit):
    R.append([sc,sh,t,dur,beat,spk,on,"(trim of "+payoff+")","(trim of "+payoff+" - NO new generation)","(trim of "+payoff+")",dia,sfx,mus,"TRIM",edit,"todo"])

# ===== DISCLAIMER =====
R.append(["0 Intro","D0","0:00-0:02","2.0s","Disclaimer card 1 (he opens with 2)","(card)","'AI-generated for entertainment.'","static","n/a text card","n/a","-","-","intro sting","CARD","2.0s static, hard cut","todo"])
R.append(["0 Intro","D1","0:02-0:03","1.0s","Disclaimer card 2","(card)","'Dinosaurs & events are fictional.'","static","n/a text card","n/a","-","-","intro sting","CARD","1.0s static, hard cut","todo"])

# ===== TRAILER MONTAGE: rapid 0.5-1.5s flashes under the VO hook (TRIMS of payoff shots) =====
gen("0 Intro","M01","0:03-0:04","1.0s","Montage open: gate flash","HOST-VO (Dee)","Quick flash of the 'DINO ZOO' gate, crowd pouring in","quick flash","'DINO ZOO' wooden gate, green logo, families streaming in","fast flash","crowd pours through gate","gate crowd, sting","HOST-VO: \"Hey guys, it's D again. Last time I barely survived the Jurassic Zoo.\"","crowd","upbeat→tense","0.8-1.0s flash, hard cut")
trim("0 Intro","M02","0:04-0:05","0.6s","Flash: carno slams glass","HOST-VO (Dee)","0.6s: Carnotaurus slams the glass","S16 (Carno charge)","(VO continues)","glass BANG","tense montage","0.6s flash")
trim("0 Intro","M03","0:05-0:06","0.7s","Flash: Spino splash","HOST-VO (Dee)","0.7s: Spinosaurus splash hits lens","S21 (Spino lunge)","(VO continues)","splash","tense montage","0.7s flash")
trim("0 Intro","M04","0:06-0:07","0.6s","Flash: Quetz swoop","HOST-VO (Dee)","0.6s: pterosaur swoops the crowd","S31 (Quetz swoop)","HOST-VO: \"This time I snuck back in...\"","wing whoosh","tense montage","0.6s flash")
trim("0 Intro","M05","0:07-0:08","0.7s","Flash: Mosa breach","HOST-VO (Dee)","0.7s: Mosasaurus breaches the tank","S45 (Mosa breach)","(VO continues)","breach","tense montage","0.7s flash")
trim("0 Intro","M06","0:08-0:09","0.6s","Flash: T-Rex roar","HOST-VO (Dee)","0.6s: T-Rex head roars at fence","S50 (T-Rex head)","HOST-VO: \"...and saw unrealistic dinosaurs no one has ever seen before.\"","roar","tense montage","0.6s flash")
trim("0 Intro","M07","0:09-0:10","0.5s","Flash: hybrid eye","HOST-VO (Dee)","0.5s: the hybrid's glowing orange eye in the dark","S56 (Hybrid reveal)","(VO continues)","low growl","tense montage","0.5s flash")
trim("0 Intro","M08","0:10-0:11","0.6s","Flash: red alarm","HOST-VO (Dee)","0.6s: red containment alarm floods the lab","S60 (Alarm)","HOST-VO: \"But one incident...\"","alarm","tense montage","0.6s flash")
trim("0 Intro","M09","0:11-0:12","0.5s","Flash: glass bursts","HOST-VO (Dee)","0.5s: the cell glass explodes","S61 (Glass bursts)","(VO continues)","shatter","tense montage","0.5s flash")
trim("0 Intro","M10","0:12-0:13","0.7s","Flash: crowd panic","HOST-VO (Dee)","0.7s: crowd flooding the exits in panic","S62 (Evacuate)","HOST-VO: \"...shut the whole park down forever.\"","screams, alarm","tense montage","0.7s flash")
trim("0 Intro","M11","0:13-0:14","0.8s","Flash: hybrid smashes gate","HOST-VO (Dee)","0.8s: hybrid bursts the park gate","S63 (Hybrid loose)","(VO continues)","gate crash, roar","tense montage","0.8s flash")
trim("0 Intro","M12","0:14-0:15","0.7s","Flash: the chase","HOST-VO (Dee)","0.7s: POV sprinting, hybrid behind","S64 (Chase)","(VO continues)","pounding, roar","tense montage","0.7s flash")
trim("0 Intro","M13","0:14-0:15","0.6s","Flash: Therizino claws","HOST-VO (Dee)","0.6s: huge claws shred a feeder","Therizinosaurus action","(VO continues)","shred","tense montage","0.6s flash")
trim("0 Intro","M14","0:15-0:16","0.6s","Flash: raptor pack bolt","HOST-VO (Dee)","0.6s: raptors bolt the fence in sync","Velociraptor action","(VO continues)","chitter","tense montage","0.6s flash")
trim("0 Intro","M15","0:16-0:17","0.7s","Flash: sauropod scale","HOST-VO (Dee)","0.7s: tilt up a towering Brachiosaurus","Sauropod scale","(VO continues)","low rumble","tense montage","0.7s flash")
trim("0 Intro","M16","0:17-0:18","0.6s","Flash: hybrid lunges glass","HOST-VO (Dee)","0.6s: the hybrid lunges at the cracking glass","Hybrid lunge","HOST-VO: \"...you won't believe it.\"","glass creak","tense montage","0.6s flash")
trim("0 Intro","M17","0:18-0:19","1.0s","Flash: rescue tease","HOST-VO (Dee)","1.0s: distant Blackhawk helicopters inbound over the burning park at dusk","S71 (choppers inbound)","HOST-VO: \"Stick till the end.\"","distant rotors (faint)","sting","1.0s flash, slowest of montage")
gen("0 Intro","S00","0:16-0:18","2.0s","Smash to title","HOST-VO (Dee)","Near-black, ember particles, 'DINO ZOO' title bug","static","near-black w/ ember particles, faint red glow (title in edit)","static","embers drift","low boom","-","low sub boom","silence bed","Title overlay, hard cut to entry")

# ===== ENTRY (ticket gag) =====
gen("1 Entry","S01","0:18-0:24","6s","Re-intro selfie at gate","HOST-VO (Dee)","'DINO ZOO' gate, Dee selfie-POV, crowds entering","slow push-in","large wooden 'DINO ZOO' gate, round green logo, families entering, Dee (30s grey tee) selfie-POV","slow push-in, sway","Dee walks to gate; crowd enters","cheerful crowd, birds","HOST-VO: \"Last time I barely survived the Jurassic Zoo... this time I'm going deeper.\"","-","upbeat doc bed IN","Hard cut from title")
gen("1 Entry","S02","0:24-0:30","6s","Ticket discount gag (verbatim)","DEE / STAFF / MAYA","Ticket booth, Lena inside, POV hand slides ticket, Maya beside","locked, sway","[LENA][MAYA] wooden DINO ZOO ticket booth, Lena leans out smiling, POV hand slides a ticket","locked sway","Lena gestures; Maya beside","booth, crowd","Dee: \"Can I get a discount?\"  Staff: \"No, it's the same for everyone.\"  Maya: \"Sad, but okay.\"","-","upbeat doc bed","Hard cut")
gen("1 Entry","S03","0:30-0:36","6s","Crowd + mystery plant","DEE / MAYA","Busy plaza + painted park map, crowd flowing one way","walk-through","[MAYA] POV through plaza past a large painted 'PARK MAP' board, big crowd flowing toward enclosures","walk-through","walk forward; crowd flows","crowd, birds","Dee: \"There's quite a crowd today. Looks like they're here to see something special.\"","-","upbeat doc bed","Hard cut")
gen("1 Entry","S03b","0:36-0:39","3s","The plant: teens slip into the hybrid door","DEE / MAYA","Two teenagers slipping through a 'HYBRID - STAFF ONLY' service door","locked, candid","two teenagers glancing around and slipping through a heavy service door stenciled 'HYBRID - STAFF ONLY' with yellow-black hazard stripes, tucked in a quiet corner of the park","locked candid","teens glance around; push through the door","quiet crowd, a latch click","-","-","unsettling doc bed","Hard cut")
gen("1 Entry","S03c","0:39-0:42","3s","The plant: 'that's weird'","DEE / MAYA","POV: the staff door easing shut; Maya glancing back","handheld","[MAYA] first-person POV catching a heavy 'HYBRID - STAFF ONLY' service door easing shut, Maya beside glancing back over her shoulder, curious","handheld","door eases shut; Maya glances back","quiet crowd","Maya: \"...that's weird.\"  Dee: \"Eh. Come on.\"","-","unsettling doc bed","Hard cut")

# creature beat builder (6 shots each)
def C(scene, base_n, t0, sign, est_on, est_cam, est_img, est_move, est_sound, est_dia, est_spk,
      narr1, narr1_on, narr1_img,
      comp_dia, comp_spk, comp_on,
      act_on, act_img, act_move, act_sound, act_dia, act_spk, act_sfx,
      narr2, narr2_on,
      cta_narr, cta_dia, sign_to, mus="light doc bed"):
    n=base_n
    def nn():
        nonlocal n; s=f"S{n:02d}"; n+=1; return s
    gen(scene,nn(),t0,"6s","Establish + "+sign,est_spk,est_on,est_cam,est_img,est_cam,est_move,est_sound,est_dia,"-",mus,"Hard cut")
    gen(scene,nn(),"+","6s","Narrator fact 1","NARRATOR",narr1_on,"slow push-in",narr1_img,"slow push-in","subject slow move, blink","low call, crowd","NARRATOR: "+narr1,"-",mus,"Hard cut")
    gen(scene,nn(),"+","6s","Companion beat","COMPANION",comp_on,"handheld","[MAYA] "+comp_on,"handheld","Maya reacts; Dee beside","crowd, light laugh",comp_dia,"-",mus,"Hard cut")
    gen(scene,nn(),"+","6s","Action beat",act_spk,act_on,"dynamic",act_img,"dynamic",act_move,act_sound,act_dia,act_sfx,mus,"Hard cut, SFX")
    gen(scene,nn(),"+","6s","Narrator fact 2","NARRATOR",narr2_on,"slow pan",narr2_on,"slow pan","subject behaviour","low call, crowd","NARRATOR: "+cta_narr.split('||')[0],"-",mus,"Hard cut")
    gen(scene,nn(),"+","6s","Rival CTA (flywheel)","NARRATOR / DEE","POV toward "+sign_to,"walking POV","[MAYA] POV past a wooden '"+sign_to+"' sign, Maya beside, greenery","walking POV","walk past sign","footsteps, crowd, birds","NARRATOR: "+cta_narr.split('||')[1]+"  Dee: \"Comments.\"","-",mus,"Hard cut (CTA)")
    return n

n=4
n=C("2 Carnotaurus",n,"0:36-0:43","'DANGER: CARNOTAURUS' sign",
    "Tall glass enclosure, yellow DANGER sign, carno paces, crowd","slow tilt up",
    "tall glass predator enclosure, yellow-black 'DANGER: CARNOTAURUS' sign, horned Carnotaurus paces behind thick glass, crowd",
    "carno paces; crowd watches","crowd murmur, hiss","Maya: \"Are they mad? They put all the dangerous ones together.\"","MAYA",
    "\"Carnotaurus used its horns to fight other Carnotaurus for territory and mating - and had some of the smallest arms of any large theropod.\"",
    "Close on horned head + tiny arms","close on Carnotaurus horned head & very small arms behind glass, scales in sun",
    "Dee: \"Even smaller than the T-Rex's. Don't tell him.\"  Maya: \"Cool.\"","DEE / MAYA","Maya at the glass grinning, gesturing at the carno's arms",
    "Carno charges & slams the glass; crowd recoils","[MAYA] Carnotaurus charges & slams thick glass, crowd jerks back, Maya flinches","carno slams glass; crowd recoils","heavy glass BANG, screams","Maya: \"NOPE.\"","MAYA","glass BANG SFX",
    "\"It usually lived alone and could reach about 25 years of age.\"","Wide of carno snorting in dusty enclosure",
    "\"It usually lived alone and could reach about 25 years.||Who was the actual rival of Carnotaurus? I'll let YOU answer.\"","","WETLANDS ->")

n=C("3 Spinosaurus",n,"0:43-0:50","Boardwalk over lagoon",
    "Boardwalk over green lagoon, huge sail-backed Spinosaurus wading, tourists","slow reveal pan",
    "wooden boardwalk over wide green lagoon, massive sail-backed Spinosaurus wading, tourists at rail",
    "Spino slow heavy wade, water displaces","water, deep rumble, crowd, birds","Staff: \"Please keep a safe distance - Spinosaurus reacts quickly to movement.\"","STAFF (Ranger)",
    "\"Spinosaurus mainly ate fish - occasionally crocodiles and small dinosaurs - and likely ate 70 to 150 kg of food a day.\"",
    "Close on the crocodile jaws + sail","close on Spinosaurus long narrow crocodile jaws & tall sail, water dripping, sun",
    "Maya: \"Bigger than a T-Rex? In a swimming pool?\"  Dee: \"Basically.\"","DEE / MAYA","Maya at the rail eyeing the Spinosaurus, impressed",
    "Spino lunges, snaps a fish, splash hits lens","[MAYA] Spinosaurus lunges & snaps a fish, big splash hits camera, Maya soaked & laughing","one heavy lunge+snap, big splash","huge splash, crowd cheer","Maya (soaked): \"I'm soaked. Worth it.\"","MAYA","big splash SFX",
    "\"Some scientists think young Spinosaurus spent more time on land than adults - still debated.\"","Wide, only the sail cutting the water",
    "\"Some think young Spinosaurus spent more time on land - still debated.||Its possible rival was Carcharodontosaurus - what do you think?\"","","FOREST ->")

n=C("4 Therizinosaurus",n,"0:50-0:57","Forest paddock",
    "Forest paddock, Therizinosaurus with huge claws among trees, crowd","slow pan",
    "sunny forest paddock, tall feathered Therizinosaurus with enormous curved claws browsing leaves, crowd at rail",
    "Therizino reaches for leaves; claws sway","crowd, leaves, low call","Maya: \"Those claws look terrifying.\"","MAYA",
    "\"Movies made Therizinosaurus look like a pure predator - but it was probably mostly herbivorous.\"",
    "Close on the claws raking bark","close on Therizinosaurus claws raking bark, feathers catching sun",
    "Dee: \"And it still mostly ate plants.\"  Maya: \"Respect.\"","DEE / MAYA","Maya staring up at the huge claws, nervous",
    "It swings its claws, shredding a hanging melon feeder","[MAYA] Therizinosaurus swings its claws and shreds a hanging melon feeder, pulp flying, crowd gasps","claws swing; feeder shreds","shred, crowd gasp","Crowd: \"Whoa!\"","CROWD","shred SFX",
    "\"Some scientists think baby Therizinosaurus were meaner than the adults.\"","Wide, Therizino calm among the trees",
    "\"Some think baby Therizinosaurus were meaner than adults.||A likely rival? Tarbosaurus - agree?\"","","AVIARY ->")

n=C("5 Quetzalcoatlus",n,"0:57-1:04","Netted aviary dome",
    "Vast netted aviary dome, giant Quetzalcoatlus perched & gliding","awe tilt-up",
    "interior vast netted aviary dome, tall cliffs, giant Quetzalcoatlus perched & gliding, sun through net, tourists below",
    "pterosaurs perch & glide","echoing screeches, wind, crowd","Crowd: \"WHOA!\"","CROWD",
    "\"Did you know baby Quetzalcoatlus could start flying just minutes after hatching?\"",
    "One spreads enormous wings on a cliff","Quetzalcoatlus on a cliff ledge spreads enormous wings, backlit through the net",
    "Maya: \"That's a dragon. That's just a dragon.\"  Dee: \"No way.\"","DEE / MAYA","Maya tilting her head all the way back, stunned",
    "A pterosaur swoops low; people duck","giant Quetzalcoatlus swoops low over the crowd, tourists duck, wind rush","pterosaur swoops; crowd ducks","loud wing-whoosh, shouts","Crowd: \"DUCK!\"","CROWD","whoosh SFX",
    "\"They lived around 20 to 30 years.\"","Wide, two pterosaurs circling the dome",
    "\"They lived around 20 to 30 years.||One big rival was Hatzegopteryx, another giant pterosaur - agree?\"","","RAPTORS ->")

n=C("6 Velociraptor",n,"1:04-1:11","Rocky raptor paddock",
    "Rocky paddock, several feathered Velociraptors alert behind a fence","slow pan",
    "sunny rocky paddock, several feathered Velociraptors moving alert behind a tall fence, crowd",
    "raptors move alert, heads flick","crowd, chittering","Maya: \"Can I give them some chicken nuggets?\"","MAYA",
    "\"Velociraptors likely hatched covered in feathers - looking more like young birds than scaly dinosaurs.\"",
    "Close on a raptor's feathered head tilting","close on a Velociraptor feathered head tilting, intelligent eye, behind fence",
    "Dee: \"I don't think the zoo allows that.\"  Maya: \"They'd want the whole bucket.\"","DEE / MAYA","Maya pretending to offer a snack, raptors tracking her hand",
    "Two raptors suddenly bolt along the fence in sync","[MAYA] two Velociraptors suddenly bolt along the fence line in eerie sync, crowd jumps","raptors bolt in sync; crowd jumps","chitter burst, gasps","Maya: \"They planned that.\"","MAYA","scurry SFX",
    "\"Fossils were found with a Velociraptor and Protoceratops locked together mid-fight.\"","Two raptors square up near a Protoceratops display",
    "\"Fossils show a Velociraptor and Protoceratops locked together mid-fight.||A likely rival? Protoceratops - who wins?\"","","PEACEFUL VALLEY ->")

n=C("7 Sauropods",n,"1:11-1:18","Grassland 'peaceful' enclosure",
    "Wide grassland: Brachiosaurus, Diplodocus, Stegosaurus, Ankylosaurus grazing together","slow rising reveal",
    "wide sunny grassland enclosure, a Brachiosaurus, Diplodocus, Stegosaurus and Ankylosaurus grazing peacefully together, families watching",
    "sauropods graze; necks sway","gentle crowd, birds, chewing","Dee: \"Finally, an enclosure of peaceful dinos.\"","DEE",
    "\"An Argentinosaurus may have needed 100 to 150 kg of vegetation every single day.\"",
    "Tilt up a towering Brachiosaurus, tiny tourists below","tilt up the leg & neck of a towering Brachiosaurus, tiny tourists below for scale",
    "Maya: \"Can I ride this one?\"  Dee: \"Absolutely not.\"","DEE / MAYA","Maya eyeing the smallest sauropod, grinning",
    "Stegosaurus swings its spiked tail lazily, clearing a feeder","Stegosaurus swings its spiked thagomizer tail lazily, knocking over a wooden feeder, crowd laughs","tail swings; feeder topples","WHUMP, laughter","Maya: \"He did that on purpose.\"","MAYA","WHUMP SFX",
    "\"Sauropods swallowed rocks - gastroliths - to grind food inside their stomachs.\"","Close on a sauropod's throat swallowing",
    "\"Sauropods swallowed gastroliths to grind food in their stomachs.||Diplodocus and Stegosaurus were neighbours - who'd you keep?\"","","MOSA LAGOON ->","calm warm bed")

n=C("8 Mosasaurus",n,"1:18-1:25","Show stadium tank",
    "Show stadium around a huge tank, crowd filling, staff ushering","slow reveal",
    "large aquatic show stadium, tiered seating around an enormous water tank, hanging bait rig, crowd filling, ranger ushering",
    "crowd fills stands; staff points","echoing PA, excited crowd","PA: \"Mosasaurus feeding time.\"  Staff: \"This way, ma'am.\"","PA / STAFF",
    "\"Mosasaurus had a second set of teeth on the roof of its mouth to drag prey deeper into its throat.\"",
    "Dark shape circles under the surface","huge dark shape circles beneath the show-tank surface, ripples, anticipation in the stands",
    "Maya: \"Front row. Obviously.\"  Dee: \"This is a mistake.\"","DEE / MAYA","POV settling into a front-row seat beside Maya, big tank ahead",
    "Mosasaurus EXPLODES out for the bait; water wall soaks the front rows","[MAYA] Mosasaurus erupts from the tank to snatch the hanging bait, enormous jaws, water cascading over the screaming front rows","Mosa breaches, snaps bait, water wall soaks crowd","huge breach, crowd roar, splash","Maya: \"Front row was a MISTAKE.\"","MAYA","BREACH+splash SFX",
    "\"Mosasaurus likely spent much of its time cruising slowly through ancient oceans.\"","The Mosa slides under; a Plesiosaur glides in a side tank",
    "\"Plesiosaurs used all four flippers to swim - almost like underwater flying.||Mosa vs Megalodon - who wins?\"","","RESTRICTED - APEX ->")

n=C("9 T-Rex",n,"1:25-1:32","Reinforced apex arena",
    "Huge reinforced arena, a T-Rex stalks; a Triceratops in the next paddock","slow tilt up",
    "huge reinforced enclosure, thick walls, a massive T-Rex stalks; a Triceratops visible in the adjacent paddock, tense crowd",
    "T-Rex stalks; head tracks crowd","deep roar, low crowd","Maya: \"That thing is even bigger than I expected.\"","MAYA",
    "\"A T-Rex tooth could reach over 30 cm long including the root - with one of the strongest bite forces of any land animal.\"",
    "Close on the T-Rex head + teeth","close on a T-Rex head, lips & huge teeth, eye catching light, behind heavy fencing",
    "Maya: \"I'm afraid to go in there.\"  Dee: \"Good instinct.\"","DEE / MAYA","Maya stepping back from the fence, nervous",
    "The T-Rex slams the fence; Triceratops lowers its horns","[MAYA] T-Rex rams the heavy fence, a Triceratops in the next paddock lowers its horns, dust, crowd jumps","T-Rex rams fence; trike lowers horns; dust","metal clang, snort, gasps","Crowd: \"AAH!\"","CROWD","clang SFX",
    "\"Some scientists think Triceratops was one of T-Rex's toughest rivals.\"","Wide, T-Rex and Triceratops eyeing across the divide",
    "\"Some think Triceratops was one of T-Rex's toughest rivals.||T-Rex or Triceratops - who really wins?\"","","STAFF ONLY ->")

# ===== HYBRID FINALE (D-Rex) =====
gen("10 Hybrid (D-Rex)",f"S{n:02d}","1:32-1:41","6s","Into the apex hall (the main attraction)","DEE","Dim corridor, 'RESTRICTED // GENETICS', flicker","slow forward dolly","dim concrete corridor, flickering fluorescents, signs 'RESTRICTED' 'GENETICS', cold blue light, POV creeping","slow forward dolly","POV creeps; lights flicker","hum, flicker, distant thud","Dee: \"Okay - THIS is the one everyone lines up for.\"","-","dread drone","Hard cut; cold-blue grade"); n+=1
gen("10 Hybrid (D-Rex)",f"S{n:02d}","+","6s","The hybrid reveal","NARRATOR","Vast dark cell, the hybrid's scarred face + glowing seams enters the light","slow reveal","[OMEGA REX] vast dark containment cell behind thick scratched glass, a massive hybrid theropod - charcoal hide, glowing orange seams, oversized jaws - moves into cold light, watching the camera","slow reveal","hybrid face enters light; eye fixes camera; claws scrape","deep breathing, claw scrape","NARRATOR: \"They built a hybrid. People think he's a monster - but is he?\"","claw scrape SFX","dread drone","Hard cut"); n+=1
gen("10 Hybrid (D-Rex)",f"S{n:02d}","+","6s","Fact: smart + camouflage","NARRATOR","The hybrid's hide shimmers/blends against the wall","slow push","[OMEGA REX] the hybrid's hide subtly shifts tone against the cell wall as if camouflaging, glowing seams dimming","slow push-in","hide shifts tone; seams dim; slow blink","low rumble, hum","NARRATOR: \"This hybrid is smarter than people realize - and camouflage may be its most dangerous advantage, even more than its size.\"","-","dread drone","Hard cut"); n+=1
gen("10 Hybrid (D-Rex)",f"S{n:02d}","+","6s","D-Rex trivia (his real line)","NARRATOR / DEE","Close on a lab plaque 'PROJECT D-REX'","push to sign","close on a stenciled lab plaque 'PROJECT D-REX // CLASSIFIED', biohazard symbol, cold light","slow push-in","push to plaque; breathing beyond","hum, deep breathing","NARRATOR: \"Fun fact - the Jurassic World team first planned their hybrid as 'Diabolus Rex', or D-Rex, before renaming it.\"  Dee: \"Ooh.\"","-","dread drone","Hard cut"); n+=1

gen("10 Hybrid (D-Rex)",f"S{n:02d}","+","6s","Companion fear","COMPANION","Maya at the glass, whispering, terrified","handheld close","[MAYA][OMEGA REX] Maya in cold blue light at the scratched glass, wide-eyed, a huge dark shape looming behind","handheld close","Maya whispers; shape looms","whisper, low growl, hum","Maya (whisper): \"Dee... what IS that?\"","-","dread drone","Hard cut"); n+=1
gen("10 Hybrid (D-Rex)",f"S{n:02d}","+","6s","It notices them","NARRATOR / DEE","The hybrid's eye snaps to the camera; it presses the glass","slow push then jolt","[OMEGA REX] the hybrid's glowing eye snaps to the camera and it presses its scarred snout against the cracking glass","slow push then jolt","eye snaps to lens; snout presses glass","low rumble, glass groan","Dee (whisper): \"...it's watching us back.\"","glass groan SFX","dread drone","Hard cut into breakout"); n+=1
# ===== BREAKOUT (hybrid out -> power trip -> everything loose) =====
gen("11 Breakout","S60","1:41-1:45","4s","The break: hybrid into the open","NARRATOR","Hybrid rams through its enclosure gate into the open park","tilt up + shake","[OMEGA REX] a massive hybrid theropod rams through its heavy enclosure gate out into the sunny open park, debris flying, hazard signs, no people in danger","tilt up + shake","hybrid bursts the gate; debris flies","gate crash, roar, alarm","NARRATOR: \"It only took one to get out.\"","CRASH SFX","alarm/action","Hard cut")
gen("11 Breakout","S61","+","3s","The trip: power goes down","PA","Hybrid topples a power pylon; sparks; lights drop","whip + shake","[OMEGA REX] the hybrid crashes into a power pylon and transformer, a shower of sparks, the park floodlights dropping dark","whip + shake","pylon topples; sparks burst; lights die","electrical bang, alarm","PA: \"Containment failure. Containment failure.\"","SPARK SFX","action","Hard cut")
gen("11 Breakout","S62","+","3s","The tell + patient zero","DEE","A dead electric fence; a small dino innocently hops over","locked then tilt","a now-dead electric perimeter fence with its warning light off, and a small harmless dinosaur calmly hopping over the unpowered fence","locked then tilt","fence light dies; small dino hops over","fence hum dies, hop","Dee: \"...the fences. The fences are dead.\"","-","action","Hard cut")
gen("11 Breakout","S63","+","2s","Raptor notices","NARRATOR","A Velociraptor tilts its head at the dead fence","slow push","a Velociraptor at its paddock fence tilts its head, intelligent eye fixed on the now-unpowered fence","slow push-in","raptor tilts head; eye fixes the fence","low chitter","-","-","tension build","Hard cut 2s")
gen("11 Breakout","S64","+","2s","Raptor realizes + over","KID/PANIC","The raptor's sly look, then it leaps the fence","quick push + whip","a Velociraptor with a sly, knowing look springs up and over the unpowered fence, the first one out","quick push then whip","raptor's sly look; springs over the fence","chitter, leap","-","-","action","Hard cut 2s")
gen("11 Breakout","S65","+","3s","The flood","KID/PANIC","Several raptors pour over the fence together","fast handheld","several Velociraptors pour over the dead fence together into the park","fast handheld","raptors pour over together","chitter, distant screams","-","-","action ramp","Rapid cuts")
gen("11 Breakout","S66","+","4s","Everything loose","NARRATOR","Wide: Quetzal swooping, Spino and Anky out, hybrid amid the worst","wide, fast pans","a wide of the park in chaos - a Quetzalcoatlus swooping low over the plaza, a Spinosaurus and an Ankylosaurus loose among emptied paths, the hybrid theropod amid the worst of it; people implied fleeing, no gore","wide fast pans","every enclosure emptying; dinosaurs everywhere","roars, alarm, distant screams","NARRATOR: \"Every gate in the park runs on the same grid.\"","-","action peak","Slow-to-fast montage")
gen("11 Breakout","S67","+","3s","Chaos peak","KID/PANIC","Accelerating slow-to-fast chaos, dust and sirens","frantic montage","fast chaotic montage of the park overrun - dust, strobing sirens, silhouetted figures running, overturned carts, dinosaurs charging through; dread not gore","frantic accelerating cuts","pure chaos accelerating","roars, sirens, rumble","Dee: \"This is the part from the intro - we're IN it.\"","-","action peak","Accelerate to fast cuts")
gen("11 Breakout","S66b","+","3s","Crowd stampede (people fleeing)","KID/PANIC","A panicked crowd running and screaming away through the plaza","fast handheld","a large crowd of panicked tourists running and screaming away from the camera through the sunny theme-park plaza, fleeing, dropped bags and an abandoned stroller, dust kicked up; no blood, no gore","fast handheld pan","crowd sprints away screaming","screams, pounding feet, alarm","-","-","action peak","Intercut with the dinosaurs")
gen("11 Breakout","S67b","+","2s","Terror reaction (faces)","KID/PANIC","Tight on terrified tourists scrambling, faces in panic","tight handheld","tight on a knot of terrified tourists scrambling and shielding each other, faces in panic, lit by strobing red emergency light; no gore","tight handheld","faces in terror; people scramble","screams, alarm","-","-","action peak","Hard cut")
gen("11 Breakout","S66d","+","3s","Crowd fleeing, dino behind","KID/PANIC","Crowd runs toward camera; a huge dinosaur silhouette far behind in the dust","wide, shake","a crowd of tourists running and screaming toward the camera in panic across the plaza, and far behind them a huge dinosaur silhouette looming in the dust and haze; no contact, no gore","wide handheld shake","crowd flees toward lens; dino looms far behind","screams, roar, rumble","-","-","action peak","Wide, hold the scale")

# ===== OUTRO (hide -> choppers -> part 2) =====
gen("12 Outro","S68","1:50-...","6s","The held breath","KID/PANIC","Dee + Maya hiding in a gap, strobing red, slow-mo, breathing","tight, slow","[MAYA] Dee and Maya crammed into a hiding spot peering out through a narrow gap, lit by strobing red light, tight and tense, time slowed","tight slow-mo","the two hide; peer out; held breath","heartbeat, breathing, muffled chaos","Dee (whisper): \"Don't move.\"","heartbeat SFX","slow tense","Slow-mo, hold")
gen("12 Outro","S69","+","4s","Their POV of the chaos","KID/PANIC","Blurry POV through the gap of dinosaurs and chaos","handheld, rack focus","first-person POV through a narrow gap, slightly blurred, of dinosaurs and chaos moving across the smoking park beyond","handheld, rack focus","blurry chaos beyond the gap","muffled roars, sirens","-","-","slow tense","Hold, then build")
gen("12 Outro","S70","+","4s","Rescue: one chopper","HOST-VO (Dee)","Dusk sky, a single distant Blackhawk silhouette, searchlight","slow tilt up","a dusk sky over the smoking park, a single distant Blackhawk military helicopter silhouette inbound with a searchlight","slow tilt up","one chopper appears; searchlight sweeps","distant rotors rising","HOST-VO: \"...and then we heard them.\"","ROTOR SFX","build → swell","Build")
gen("12 Outro","S71","+","4s","Several Blackhawks inbound","HOST-VO (Dee)","Several Blackhawks inbound, rotor-wash kicking debris","low wide, shake","several Blackhawk military helicopters inbound over the park at dusk, rotor-wash kicking up dust and debris, searchlights crossing","low wide, rotor shake","several choppers sweep in; downwash","loud rotors, wind","-","-","swell → cut","Hard cut to black on the swell")
R.append(["12 Outro","D2","...","2.0s","End card","(card)","'FOLLOW FOR PART 2'","static","n/a text card","n/a","-","-","sting → silence","CARD","Cut to black, end card","todo"])

with open("STORYBOARD.tsv","w",newline="") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(COLS); w.writerows(R)
gen_n=sum(1 for r in R if r[13]=="GEN"); trim_n=sum(1 for r in R if r[13]=="TRIM"); card_n=sum(1 for r in R if r[13]=="CARD")
print(f"rows: {len(R)}  (GEN {gen_n} / TRIM {trim_n} / CARD {card_n})  cols: {len(COLS)}")
