#!/usr/bin/env python3
"""v2 shot list + seed prompts + Grok i2v prompts for the TechJoint cookie remake (phone-real grit look).
Writes shots_v2.json + seed_prompts_v2.json. VO anchors (shot ids H1,C01,C04,C09,C14,C18,C22,C26,C33,C36) are unchanged.

Design rules (from competitors/COMPETITOR_TEARDOWN_2026-08.md + V1_GAP_ANALYSIS.md):
- close-ups only, locked-overhead / high 70deg / side CU; one action per shot; distinct vantage per adjacent shot
- goods-first hook (reuse payoff clips), goods reprises at ~0:50 and ~1:45 (G1/G2 reuse), reveal ladder
  tray -> lift&turn -> flip base -> crack -> bend-open molten pools -> cross-section/stack -> rack
- chocolate physics: molten pools / smears / one drip; NEVER stretching ropes
- 10 s gens for continuous actions (pours, whisk, fold, money shot), 6 s elsewhere
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

LOOK = ("Candid unstyled iPhone photo, phone held by hand directly above or at a high ~70-degree angle, close-up, "
        "flat even indoor kitchen light (no window glow, no golden-hour, no bokeh), true-to-life neutral colour, "
        "faint sensor noise, white quartz counter with faint grey veining, white subway tile, no styling props, "
        "real mess (crumbs, flour dust, smears, fingerprints on glass). Hands: young woman, fair skin, short natural "
        "nails with sheer pale-pink polish, thin gold band on the right ring finger, cream oversized knit sweater "
        "with sleeves pushed up, correct anatomy. No text, no logos, no faces, no reflections of a person. 16:9.")

GROK_BASE = ("Animate this exact image as real handheld iPhone cooking footage, 16:9. Tiny natural hand tremor, slight "
             "phone drift, flat indoor light, true colours, no zoom, no cuts. Real-world physics. Exactly five fingers on "
             "each hand, hands keep their grip, no morphing, nothing appears or disappears, no faces, no text, no music. ")
CHOC = ("Melted chocolate behaves like real melted chocolate: it pools, smears and sags heavily, at most one short drip "
        "that breaks within a second - it never stretches into ropes or strings. ")

# id, act, dur_s (timeline), gen_len (0 = reuse), seed composition, grok motion, sfx, caption (v2 = one small caption max)
S = []
def shot(id, act, dur, gen, seed, motion, sfx="", cap="", reuse=None, hands=True, vantage=""):
    S.append(dict(id=id, act=act, dur_s=dur, grok_gen_len_s=gen, seed=(None if reuse else f"{id}.png"),
                  seed_prompt=(None if reuse else seed), grok_prompt=(None if reuse else GROK_BASE + motion),
                  sfx=sfx, caption=cap, reuse_of=reuse, hands_in_frame=hands, vantage=vantage))

# ---- HOOK (VO block "Crispy on the outside..." ~12 s) — flash-forwards of payoff clips, no title pop
shot("H1", "HOOK", 2.5, 0, "", "", "cookie_crunch", reuse="C33", vantage="money shot: bend open, molten pools")
shot("H2", "HOOK", 2.0, 0, "", "", "crisp_crunch", reuse="C34", vantage="edge snap")
shot("H3", "HOOK", 2.0, 0, "", "", "tray_rack", reuse="C29", vantage="tray out")
shot("H4", "HOOK", 2.0, 0, "", "", "", reuse="C37", vantage="lift & turn to lens")
shot("H5", "HOOK", 2.0, 0, "", "", "", reuse="C35", vantage="cross-section stack")
shot("H6", "HOOK", 2.0, 0, "", "", "sprinkle", reuse="C31", vantage="flaky salt macro")

# ---- INGREDIENTS (VO "Here's everything you need...")
shot("C01", "INGREDIENTS", 6, 6,
     "Directly overhead, close-up: on the bare white quartz counter, small mismatched bowls crowd the frame - a block of butter "
     "on paper, packed brown sugar, white sugar, two eggs (one cracked into a small bowl showing a yolk), a little bottle of "
     "vanilla, flour, a ramekin of baking soda and salt, a bar of dark chocolate and a bowl of chips; the right hand is setting "
     "the bowl of chips down at the edge. Slight flour dust on the counter.",
     "The right hand sets the bowl of chips down and withdraws out of frame; nothing else moves except a tiny phone drift.",
     sfx="bowl_set", cap="", vantage="overhead CU ingredients")
shot("C02", "INGREDIENTS", 4, 6,
     "High ~70-degree angle close-up: a dark chocolate bar half-chopped into chunks on a small wooden board with a bowl of "
     "chocolate chips beside it, the glass mixing bowl soft behind; the right hand rests two fingers on the board edge.",
     "The right hand nudges the bowl of chips forward a few centimetres and rests; only subtle drift.",
     cap="way too much chocolate", vantage="70deg CU chocolate")
shot("C03", "INGREDIENTS", 4, 6,
     "Side close-up at counter height: the small stainless saucepan on the hob, the right hand dropping cubes of butter in, "
     "three cubes already in the pan, one mid-air; a butter wrapper beside the hob.",
     "The cube lands in the pan and the hand drops one more cube, then withdraws; flame flickers slightly.",
     sfx="bowl_set", vantage="side CU pan")

# ---- STEP 1 brown butter (VO "Rule number one: brown your butter...")
shot("C04", "BROWN", 5, 6,
     "Directly overhead close-up into the stainless saucepan on the hob: butter cubes half-melted, edges bubbling, pale yellow "
     "pool, a little foam starting; no hands.",
     "The butter keeps melting, bubbles at the edges, the foam spreads slowly; no hands; subtle drift.",
     sfx="sizzle", cap="rule #1 - brown the butter", hands=False, vantage="overhead pan")
shot("C05", "BROWN", 5, 10,
     "High 70-degree close-up: the right hand grips the saucepan handle and swirls the pan, the butter foaming white and "
     "sloshing up the side; steam wisps.",
     "The hand swirls the pan in slow circles; the foamy butter sloshes and settles; steam drifts.",
     sfx="sizzle", vantage="70deg swirl")
shot("C06", "BROWN", 6, 10,
     "Extreme close-up macro from directly above into the pan: the foam thinning, golden-brown toasted flecks appearing on "
     "the bottom, amber liquid, tiny bubbles, a wisp of steam; no hands.",
     "The foam subsides slowly, more brown flecks appear, tiny bubbles rise and pop; no hands; very slight drift.",
     sfx="sizzle", cap="smells like toffee", hands=False, vantage="macro pan")
shot("C07", "BROWN", 5, 10,
     "High 70-degree close-up: the right hand tips the saucepan and pours amber browned butter with dark flecks into the large "
     "clear glass mixing bowl on the quartz counter; the left hand steadies the bowl.",
     "The butter pours in a steady stream into the bowl and pools; the pan tilts slightly more; hands steady.",
     sfx="pour_liquid", vantage="70deg pour")
shot("C08", "BROWN", 5, 6,
     "Directly overhead close-up: the glass bowl holding the amber browned butter with flecks, a faint wisp of steam, the "
     "right hand just releasing the rim and lifting away; a butter smear on the counter.",
     "The hand releases the bowl and lifts out of frame; the steam drifts; liquid settles.",
     cap="cool 10 min", vantage="overhead bowl")

# ---- goods reprise 1 (after brown butter, ~0:50)
shot("G1", "REPRISE", 1.6, 0, "", "", "", reuse="C33", vantage="flash: money shot")

# ---- STEP 2 sugars + eggs (VO "Both sugars into the butter...")  -- C09 = prototype P2 clip (already banked)
shot("C09", "SUGARS", 5, 0, "", "", "rice_pour", cap="1 cup brown - 1/2 cup white", reuse="P2", vantage="overhead pour onto sugars")
shot("C10", "SUGARS", 5, 10,
     "High 70-degree close-up: the right hand whisks the bowl - browned butter and sugars turning into a glossy caramel-coloured "
     "paste, the balloon whisk mid-circle; the left hand holds the rim.",
     "The whisk circles steadily; the mixture turns glossy and smooth; hands steady.",
     sfx="whisk", vantage="70deg whisk")
shot("C11", "SUGARS", 4, 6,
     "Close-up at bowl-rim height: the right hand cracks an egg on the rim of the glass bowl, the shell just splitting, "
     "the caramel mixture below.",
     "The shell splits and the egg drops into the bowl with a soft plop; the hand pulls the shell halves apart.",
     sfx="egg_crack", vantage="rim CU egg")
shot("C12", "SUGARS", 3.5, 6,
     "Macro close-up: an egg yolk sitting in a half shell held over the bowl in the right hand, the white slipping away over the "
     "edge into a small side bowl; a second half shell on the counter.",
     "The last of the white slips off the yolk; the hand tips the yolk gently into the mixing bowl.",
     cap="rule #2 - one extra yolk", vantage="macro yolk")
shot("C13", "SUGARS", 5.5, 10,
     "Side close-up: the balloon whisk lifted out of the bowl by the right hand, a thick glossy ribbon of batter falling back "
     "into the bowl; a teaspoon of vanilla on the counter.",
     "The ribbon keeps falling and folds onto the batter surface; the whisk lowers and stirs once.",
     sfx="whisk", vantage="side ribbon")

# ---- STEP 3 dry (VO "Flour, baking soda, salt...")
shot("C14", "DRY", 4, 6,
     "Directly overhead close-up: flour being tipped from a small white bowl by the right hand into the glossy batter, a soft "
     "puff of flour dust rising, flour specks on the counter.",
     "The flour keeps sliding in, a soft puff of dust rises and settles; hand steady.",
     sfx="rice_pour", cap="2 1/4 cups flour", vantage="overhead flour")
shot("C15", "DRY", 4, 6,
     "Close-up: a teaspoon of baking soda held by the right hand over the flour-topped bowl, the left fingers pinching salt "
     "above it, grains falling.",
     "The soda tips in and the pinched salt falls in a thin trickle; hands steady.",
     sfx="sprinkle", cap="1 tsp soda - 3/4 tsp salt", vantage="CU soda salt")
shot("C16", "DRY", 6, 10,
     "High 70-degree close-up: the sage-green spatula folding the dough, white flour streaks disappearing into the tan batter, "
     "the right hand on the spatula, the left holding the rim.",
     "The spatula folds in slow strokes; the flour streaks disappear; hands steady.",
     sfx="stir_bowl", vantage="70deg fold")
shot("C17", "DRY", 4, 6,
     "Macro close-up: the last pale streak of flour being folded under by the spatula edge, matte tan dough surface filling "
     "the frame.",
     "One slow fold buries the last streak; the spatula lifts slightly.",
     cap="stop here - no dry flour", vantage="macro fold")

# ---- STEP 4 chocolate (VO "Now the chocolate...")
shot("C18", "CHOC", 5, 10,
     "Side close-up at board height: a chef's knife held by the right hand chopping a dark chocolate bar on a small wooden "
     "board, shards and flakes scattered, the left fingers holding the bar.",
     "The knife rocks and chops twice; shards scatter; the left hand shifts the bar.",
     sfx="chop", vantage="side chop")
shot("C19", "CHOC", 4, 6,
     "Directly overhead close-up: the board tilted by the right hand, chopped chocolate chunks sliding into the dough bowl, "
     "a bowl of chips being poured in by the left hand at the same time.",
     "The chunks slide off the board into the bowl and the chips tumble in; boards lowers.",
     sfx="rice_pour", cap="1 1/2 cups total", vantage="overhead tip in")
shot("C20", "CHOC", 5, 10,
     "High 70-degree close-up: the spatula folding chocolate chunks and chips through the tan dough, some chunks half-buried.",
     "The spatula folds in slow strokes, chunks tumble and bury; hands steady.",
     sfx="stir_bowl", vantage="70deg fold choc")
shot("C21", "CHOC", 4, 6,
     "Macro close-up: the finished dough studded with dark chunks and chips, the spatula lifting a heap of it, a few chunks "
     "catching the light; no text.",
     "The spatula lifts the heap slowly and it slumps back; subtle drift.",
     hands=True, vantage="macro dough")
# ---- goods reprise 2 (~1:45)
shot("G2", "REPRISE", 1.6, 0, "", "", "", reuse="C35", vantage="flash: cross-section stack")

# ---- STEP 5 scoop + chill (VO "Big scoops...")  -- C23 = prototype P3 clip (press chunk on tray)
shot("C22", "SCOOP", 5, 6,
     "Close-up: the stainless cookie scoop in the right hand pulling a big ball of dough from the bowl, chunks visible, "
     "the scoop's bail half-squeezed.",
     "The scoop pulls the ball free and lifts it toward the tray; hand steady.",
     sfx="pop", cap="big scoops - about 3 tbsp", vantage="CU scoop")
shot("C23", "SCOOP", 5, 0, "", "", "tray_laydown", cap="rule #3 - chill", reuse="P3", vantage="tray: press chunk")
shot("C24", "SCOOP", 4, 6,
     "Side close-up: the parchment-lined gold sheet pan with dough balls sliding into a fridge shelf, both hands on the pan, "
     "fridge light, a jar and a milk carton on the shelf.",
     "The pan slides onto the shelf and the hands withdraw; the fridge door edge begins to swing closed.",
     sfx="oven_door", cap="30 min minimum", vantage="side fridge")
shot("C25", "SCOOP", 3, 6,
     "High 70-degree close-up: the same pan of now matte, firm chilled dough balls set back on the counter, the right hand "
     "lifting away from the pan edge.",
     "The hand lifts away; nothing else moves; subtle drift.",
     sfx="tray_laydown", vantage="70deg chilled tray")

# ---- STEP 6 bake (VO "Three-seventy-five, ten to twelve minutes...")
shot("C26", "BAKE", 4, 6,
     "Close-up: the right hand turning a stainless oven knob on a plain oven front (no digital display), knuckles and ring "
     "visible.",
     "The hand turns the knob a quarter turn and releases.",
     sfx="knob_spin", cap="375 F / 190 C", vantage="CU knob")
shot("C27", "BAKE", 4, 6,
     "Side close-up: the pan of dough balls sliding onto the middle oven rack, both hands in a grey oven mitt and bare, oven "
     "interior light.",
     "The pan slides in onto the rack; the hands withdraw; the door begins to close.",
     sfx="tray_rack", vantage="side oven in")
shot("C28", "BAKE", 7, 10,
     "Close-up through the oven door glass: the cookies on the pan spreading and puffing, edges just starting to brown, "
     "warm oven light, slight glass reflection.",
     "The cookies slowly spread and puff, edges darkening a touch; heat shimmer; no hands.",
     sfx="oven_fan", cap="10-12 min", hands=False, vantage="through glass")
shot("C29", "BAKE", 4, 6,
     "High 70-degree close-up: the pan coming out of the oven held in a grey mitt by the left hand, golden-edged cookies with "
     "pale puffy centres, a wisp of steam.",
     "The pan slides out and lowers toward the counter; steam drifts; mitt steady.",
     sfx="tray_rack", vantage="70deg tray out")
shot("C30", "BAKE", 3, 6,
     "Close-up: both hands tapping the hot pan down onto the counter, the cookies crinkling and settling, a puff of steam.",
     "The pan taps down once and the cookies settle and crinkle slightly; hands steady.",
     sfx="tray_foley", vantage="CU tray tap")
shot("C31", "BAKE", 3, 6,
     "Macro close-up: the right fingers pinching flaky sea salt above one hot cookie, flakes falling onto the molten chunks, "
     "crisp browned edge in focus.",
     "The flakes fall and land on the cookie; the fingers rub together and lift away.",
     sfx="sprinkle", vantage="macro salt")

# ---- PAYOFF ladder (VO "...okay. Look at that. Crispy edge. Gooey middle. Every time.")
shot("C32", "PAYOFF", 4, 6,
     "High 70-degree close-up: the pan of cookies resting on the counter, faint steam, crisp browned edges, no hands.",
     "Steam drifts; nothing else moves; subtle drift.",
     cap="5 min - the hardest part", hands=False, vantage="70deg resting")
shot("C37", "PAYOFF", 3, 6,
     "Close-up at counter height: the right hand lifting one cookie off the pan toward the phone and tilting it, the crisp "
     "golden underside edge and craggy top visible, molten chunks glossy.",
     "The hand lifts the cookie toward the lens and turns it slowly to show the edge and top; steady grip.",
     vantage="lift & turn")
shot("C38", "PAYOFF", 3, 6,
     "Close-up: the same cookie flipped over in the fingers showing its evenly browned crisp base, a few crumbs falling.",
     "The fingers flip the cookie over slowly to show the base; a crumb falls.",
     vantage="flip base")
shot("C33", "PAYOFF", 6, 10,
     "Directly overhead close-up: both hands have just bent one warm cookie open over the pan - the halves tilt apart, the "
     "torn faces show a soft, slightly under-baked pale centre and the melted chocolate chunks are glossy liquid pools "
     "smeared across the break, one drip already falling onto the parchment, the outer edge thin, crisp and browned; crumbs.",
     "The hands bend the halves a little further apart very slowly; the molten chocolate smears and sags, the single drip "
     "lands on the parchment, a crumb falls. " + CHOC,
     sfx="cookie_crunch", vantage="money shot bend open")
shot("C34", "PAYOFF", 4, 6,
     "Macro close-up: the right fingers snapping off a piece of the thin crisp edge of a cookie, the break clean and "
     "crumbly, crumbs scattering, molten chunk visible on the remaining half.",
     "The edge snaps off with a clean break, crumbs fall; the fingers hold the piece up slightly.",
     sfx="crisp_crunch", vantage="macro snap")
shot("C35", "PAYOFF", 4, 6,
     "Close-up at counter height: a short stack of four cookies on the parchment, the top one broken in half and laid open "
     "showing the soft centre and glossy melted chunks, crisp edges, crumbs around; no glass of milk, no props.",
     "Very slow push-in drift toward the broken centre; nothing moves.",
     hands=False, vantage="stack cross-section")
shot("C36", "CARD", 12, 10,
     "High 70-degree close-up: cookies on a black wire cooling rack on the quartz counter, the left third of frame clear "
     "counter, crisp edges and glossy chunks, crumbs; no hands.",
     "Very slow drift; nothing moves.",
     hands=False, cap="recipe card", vantage="rack for card")

assert len({s["id"] for s in S}) == len(S)
gens = [s for s in S if s["grok_gen_len_s"]]
print("shots", len(S), "gens", len(gens), "gen seconds", sum(s["grok_gen_len_s"] for s in gens))
json.dump({"project": "techjoint_cookies_v2", "look": LOOK, "grok_base": GROK_BASE, "choc_rider": CHOC, "shots": S},
          open(os.path.join(HERE, "shots_v2.json"), "w"), indent=1)
json.dump({"look": LOOK, "shots": {s["id"]: s["seed_prompt"] for s in gens}},
          open(os.path.join(HERE, "seed_prompts_v2.json"), "w"), indent=1)
print("wrote shots_v2.json, seed_prompts_v2.json")
