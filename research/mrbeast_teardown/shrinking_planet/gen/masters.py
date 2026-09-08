ART_STYLE = ("Stylized 3D-animated feature look, NOT photoreal: matte materials, soft global illumination, "
"clean readable silhouettes, saturated character colours (PIP matte magenta, GRUFF cyan-blue fur, ORB chrome with a "
"gold ring-light halo, THE COUNT matte black with red seven-segment faces) against deep-space black and grey basalt rock, "
"a thin sky haze only on the big planet, 16:9 frame, no text baked into the image, no humans.")

ANCHORS = {
 "PIP": "PIP: 1-metre axolotl-like creature, matte magenta skin, six frilly gill-fronds on the head that act as hair, oversized glossy black eyes, small mouth, ONE yellow scarf (never changes), no other clothing.",
 "GRUFF": "GRUFF: 2.5-metre yeti, long cyan-blue fur that completely covers the mouth, heavy expressive brows, ONE cracked brass goggle worn on the forehead, no clothes.",
 "ORB": "ORB: 60-cm floating chrome sphere, ONE large glass lens-eye, a gold ring-light halo, a starfield reflected on the chrome, NO mouth, NO arms.",
 "COUNT": "THE COUNT: 40-cm matte-black hovering cube, red seven-segment display on every face, ONE wobbling antenna, FOUR small thrusters, no face.",
}
NEG = "Negative: no humans, no text, no letters, no numbers, no watermark, no logo, no photoreal skin, no extra limbs, no second scarf, no second goggle."

def P(*parts):
    return " ".join([ART_STYLE] + list(parts) + [NEG])

CHAR_VIEWS = {
 "PIP": [
  ("front", "Character master, full-body front view, neutral T-pose-free relaxed stance, centred on a plain grey basalt ground with deep-space black behind, even soft key light, fronds relaxed, scarf tucked."),
  ("3q", "Character master, full-body three-quarter view turned 45 degrees to camera-left, same lighting, fronds slightly lifted, scarf end trailing, one foot forward."),
  ("expr", "Character master, expression sheet in ONE image: the same head three times side by side — fronds drooping (sad), fronds flared straight out (angry), fronds curled at the tips (playful); eyes matching each; mouth closed in all three."),
 ],
 "GRUFF": [
  ("front", "Character master, full-body front view, heavy relaxed stance, arms at sides, on plain grey basalt with deep-space black behind, even soft key light, fur hanging over the mouth, brass goggle catching a small highlight."),
  ("3q", "Character master, full-body three-quarter view turned 45 degrees to camera-right, shoulders slightly hunched, same lighting, the goggle's crack visible."),
  ("expr", "Character master, expression sheet in ONE image: the same head three times side by side — brows flat and low (cold), brows knotted with fur bristling outward (angry), brows lifted with fur softly parted (tender); mouth never visible."),
 ],
 "ORB": [
  ("front", "Character master, the sphere floating at eye level dead-centre, lens-eye facing camera, halo lit steady gold, a crisp starfield reflected on the chrome, plain deep-space black background with a sliver of grey rock at the bottom."),
  ("3q", "Character master, the sphere turned 45 degrees so the lens-eye looks camera-left, halo tilted, the chrome catching a warm rim light, same background."),
  ("expr", "Character master, the same sphere three times side by side in ONE image: halo dim and thin (idle), halo bright and wide (speaking), halo flared into a starburst (announcing); lens-eye identical in all three."),
 ],
 "COUNT": [
  ("front", "Character master, the cube hovering dead-centre with its front face square to camera, red seven-segment segments all lit as a blank clean plate (no readable digits), antenna upright, four thrusters glowing faintly, deep-space black behind."),
  ("3q", "Character master, the cube rotated 30 degrees showing two faces, antenna bent to one side, thrusters trailing thin exhaust, same background."),
  ("expr", "Character master, the same cube three times side by side in ONE image: steady hover (normal), tilted 20 degrees with antenna wobbling (glitch), one thruster sputtering with the cube dipping (malfunction); displays remain blank plates."),
 ],
}

PLANET_MASTERS = [
 ("M_PLANET_1000", 1000, "Environment master, a 1000-metre spherical asteroid-planet seen from orbit, grey basalt with ridges and small craters, a THIN pale sky haze hugging the surface, one tiny magenta tent dot near the north pole and one cave mouth near the south pole, a sealed metal crate speck on the equator, deep-space black with sparse stars.", "Day 1-2. The only planet with sky haze. Hero pull-out source (B05, B31)."),
 ("M_PLANET_500", 500, "Environment master, a 500-metre asteroid-planet from orbit, a raw flat sheared face on one side where a wedge was torn away (fresh pale rock, faint glowing seam), no sky haze, tent and cave now on the same hemisphere, deep-space black.", "Day 5-6. Sheared face must read from orbit."),
 ("M_PLANET_300", 300, "Environment master, a 300-metre asteroid-planet from orbit with TWO sheared faces, a plasma vent glowing orange on the equator, the crate speck nearby, no haze, deep-space black.", "Day 10-16."),
 ("M_PLANET_25", 25, "Environment master, a 25-metre house-sized rock floating in space, seen from a drone height of ~40 m, clearly a single boulder with a flat top, the sealed crate the size of a car on it, a red painted ring on one side, two tiny tents, harsh sunlight from upper left, deep-space black.", "Day 20. Also re-cropped 1.25x tighter for the 20 m planet (Day 25)."),
 ("M_PLANET_12", 12, "Environment master, a 12-metre bus-sized rock floating in space, seen from ~20 m, the escape pod door glowing red on one face, two soundproof glass pods on top, no tents, deep-space black.", "Day 26. Also re-cropped ~1.7x tighter for the 7 m planet (Day 27)."),
 ("M_PLANET_4", 4, "Environment master, a 4-metre rock the size of a small van floating in space, seen from ~8 m, the red lever and pod door on its side, the crate perched on top taking a third of the surface, black space with stars all around, sunlight from the left.", "Day 28. THUMBNAIL SEED base: GRUFF stands taller than this rock."),
 ("M_PLANET_2", 2, "Environment master, a 2-metre car-sized boulder floating in space, seen from ~5 m at eye level, the pod door on its side, the crate and a small clock housing on top, every edge visible, deep-space black.", "Day 29-30. Finale rock."),
]

SET_MASTERS = [
 ("M_SET_pip_camp", "Set master, PIP's camp at the north pole: one small magenta dome tent pitched on grey basalt, a ration-bar crate, a coiled silver gravity tether, a planet horizon curving sharply 30 m away, thin haze on the horizon, stars above, warm camp lamp glow.", "Empty plate — characters composited in."),
 ("M_SET_gruff_cave", "Set master, GRUFF's cave at the south pole: a basalt cave mouth twice the height of a tall creature, cyan bioluminescent moss on the inner walls, a flat sleeping ledge, a small pile of moon rocks by the entrance, the curved horizon and stars outside.", "Empty plate."),
 ("M_SET_pad", "Set master, the landing pad: a flat circular basalt platform with a wide RED painted ring around its edge, three small pad lights, the sealed metal crate stamped with a raised question-mark plate standing just inside the ring, sharp curved horizon, stars.", "Red ring = QUIT line device."),
 ("M_SET_pod_door", "Set master, the escape pod door: a rounded metal hatch set into a rock face, glowing deep RED from a light strip around its rim, one seat visible through a porthole, a heavy brass lever on a post beside it, black space behind the rock edge.", "Launch device (separate from the red ring)."),
 ("M_SET_confessional", "Set master, the confessional booth: a tiny domed glass booth on the rock with one stool inside, lit by a single coloured strip light that can be magenta or cyan, the outside a black void with a few stars, the booth interior walls padded grey.", "Colour light swaps per contestant; booth angle varies by shot."),
 ("M_SET_truth_beam", "Set master, the truth beam: a tall column of light standing on the equator rock, colour-neutral pale white here (to be graded green or red), a small tray drone holding the projector at its base, two floor marks either side, black space.", "One clip colour-shifted per verdict."),
]

ARCHIVE_MASTERS = [
 ("M_ARCH_01_stage_wide", "Archive still, stylized flat-lit poster photograph: a four-piece creature band on a small club stage, PIP at the front microphone in her yellow scarf, GRUFF behind a drum kit with the brass goggle pushed up, two nondescript grey-blue creatures on bass and keys, stage smoke, warm tungsten wash, slight film grain, matte finish.", "Nostalgic; band = 4 years, one bus, one stage."),
 ("M_ARCH_02_stage_drums", "Archive still, stylized flat-lit poster photograph from side stage: GRUFF mid-hit on the drums, fur flying, the goggle down over one eye, PIP a magenta blur at the mic in the foreground, flash-lit, grain.", "Goggle worn DOWN here — the only time."),
 ("M_ARCH_03_bus_road", "Archive still, stylized flat-lit poster photograph: a battered tour van parked on a basalt road under a pale sky, the band's four silhouettes leaning on it, PIP sitting on the roof, GRUFF holding the van keys, daylight, grain.", "The van GRUFF later sells (B27)."),
 ("M_ARCH_04_bus_bunks", "Archive still, stylized flat-lit poster photograph inside the van: cramped bunks, PIP asleep with the scarf over her eyes, GRUFF awake in the bunk below staring at the ceiling, one small lamp, grain.", "Foreshadows 'I noticed'."),
 ("M_ARCH_05_dressing_room", "Archive still, stylized flat-lit poster photograph: a dressing-room mirror ringed with bulbs, PIP alone at the mirror seen in reflection, fronds drooping, the other three visible laughing in the background out of focus, grain.", "Pays off B13 'nobody would notice'."),
 ("M_ARCH_06_empty_hall", "Archive still, stylized flat-lit poster photograph: an empty concert hall from the stage, one drum kit left on stage, a single yellow scarf hanging on the mic stand, house lights half up, grain.", "The morning after she left."),
]

def build_masters():
    out=[]
    for name in ["ORB","PIP","GRUFF","COUNT"]:
        views=[]
        for vid,desc in CHAR_VIEWS[name]:
            views.append({"id":f"M_{name}_{vid}","view":vid,"prompt":P(ANCHORS[name],desc)})
        out.append({"id":f"M_{name}","kind":"character","prompt":views[0]["prompt"],"views":views,
                    "notes":f"One master, three views (front / three-quarter / expression). Anchor: {ANCHORS[name]}"})
    for mid,m,desc,notes in PLANET_MASTERS:
        out.append({"id":mid,"kind":"planet","planet_m":m,"prompt":P(desc),"notes":notes})
    for mid,desc,notes in SET_MASTERS:
        out.append({"id":mid,"kind":"set","prompt":P(desc),"notes":notes})
    for mid,desc,notes in ARCHIVE_MASTERS:
        out.append({"id":mid,"kind":"archive","prompt":P(desc),"notes":notes})
    return out

PLANET_FOR = {1000:"M_PLANET_1000",500:"M_PLANET_500",300:"M_PLANET_300",25:"M_PLANET_25",20:"M_PLANET_25",12:"M_PLANET_12",7:"M_PLANET_12",4:"M_PLANET_4",2:"M_PLANET_2"}
