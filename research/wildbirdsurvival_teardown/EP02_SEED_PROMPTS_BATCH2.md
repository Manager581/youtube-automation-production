# EP02 — Seed batch 2 (7 seeds for the shots proven un-croppable, 2026-07-23)

Written after the 14-crop resolution pass: S008, S029, S046, S050, S067, S068, S082 were each
proven un-croppable on their assigned seeds (geometry exhausted or content absent — see the
session log / commit 9912a50). Each gets a purpose-built seed below, generated with gpt-image
in the existing "Nature Documentary Stills" thread so the grade matches.

Rules applied (from EP02_OPEN_SEEDS.md + ep02_new_seed_prompts.json):
- Register: "dark red stain, dried, rust-brown" — NEVER wound/bleeding/blood/gore/raw.
- Beak guard on every finch: SHORT BLUNT CONICAL, never long/pointed/crow-like.
- Booby never faces camera; strict/side profile named explicitly.
- ONE line per prompt; paste via execCommand('insertText'); verify .innerText.length.
- After download: verify anatomy, stain dryness, creature counts, then retarget the shot
  via apply_defect_edits.py (seed + grok_prompt/vantage/action edits per shot notes below).

## SEED_crane_flank.png → S008 (12s futility hold, MS)
The craning pose is IN frame 1 so the i2v only has to continue it, not invent it.
S008 retarget notes: prompt stays close to current; drop "the whole adult Nazca booby"
(tail cropped by design); finches start below the flank (two climb up during the shot).

```
Candid handheld wildlife documentary still, extreme telephoto, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. A side-on telephoto MEDIUM shot at the bird's own eye height of one adult Nazca booby squatting low on a pale guano-streaked black lava shelf, pale grey overcast sea haze behind it and a soft dark out-of-focus lava mass at the right edge of frame; the booby's neck is twisted back and down over its own near flank so its long orange dagger bill reaches toward the base of its folded wing, its dark grey facial mask and one pale yellow eye still visible in profile, never facing the camera; ONE small jet-black vampire ground finch with a SHORT BLUNT CONICAL seed-cracking beak (never long, never pointed, never crow-like) is pressed in at the base of the near wing where a SMALL dark red stain, dried and rust-brown and matted with no wet gloss, no drip, no run, no thread, is fixed in the white down, and TWO more jet-black ground finches stand together on the lava just below the booby's flank; exactly one large seabird and exactly three small black finches, the whole head and neck in frame and the tail cropped by the left frame edge; Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_stain_opposed.png → S029 (XCU, "the parasite, plural")
Restores the shot's ORIGINAL action (two beaks working one stain from opposite sides) that the
A2 respec had watered down. On A2 every legal box hit S056's region (IoU 0.83).

```
Candid handheld wildlife documentary still, extreme telephoto macro, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. An extreme telephoto macro, hard side-on and level with a large Nazca booby seabird's white flank at the base of its dark folded wing, white plumage and the dark wing edge filling the whole frame, no seabird head, no horizon, no sky; at the centre of the white down one WIDE matted dark red stain, dried and rust-brown and crusted at its edges with no wet gloss, no drip, no run, no thread; TWO small jet-black vampire ground finches with SHORT BLUNT CONICAL seed-cracking beaks (never long, never pointed, never crow-like) work the stained down from OPPOSITE sides, the left finch standing on the pale lava below the flank with its head up and beak tip in the stained down, the right finch braced higher against the flank with its head down and beak tip in the same stained patch, their heads a few centimetres apart and both in sharp focus; exactly two finches, no other bird; shallow macro depth of field, Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_shimmer_distance.png → S046 (extreme-distance MS through heat shimmer)
Cropping can only enlarge, so distance needs its own seed (verifier: CONCUR WITH RE-SEED).
S046 retarget notes: set has_blood=false + drop the stain sentence and rider — the shot's own
action says "No blood readable at this range", and a rider without a stain in frame 1 orders
invention (the S079 lesson).

```
Candid handheld wildlife documentary still, extreme telephoto, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. An extreme long telephoto shot from very far across a flat black lava field, heavy heat shimmer and mirage ripple boiling in the air low over the hot rock between the camera and the subject, the lower third of frame all hot rippling out-of-focus black lava; in the middle distance one adult Nazca booby sits side-on on the rock in strict side profile, heavily compressed by the long lens, clearly readable but small, about a quarter of the frame tall, with two tiny black finches just visible at the base of its folded wing; flat pale grey overcast haze fills the background and the bird's outline is softened by the shimmering air; no other animal, Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_guano_peck.png → S050 (XCU, foraging triptych beat 4 — VO "Even the droppings of other birds")
finch_portrait had no ledge to peck (verifier-measured); finch_ground would repeat beat 1's
crevice 10s later. This restores the pecking beat under its own VO line.

```
Candid handheld wildlife documentary still, telephoto lens with shallow depth of field, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. Camera looking DOWN from just over and slightly behind a small jet-black vampire ground finch's shoulder onto a chalk-white guano-crusted black lava ledge, close-up: the finch stands on the crusted ledge with its head lowered, its SHORT BLUNT CONICAL seed-cracking beak (never long, never pointed, never crow-like) touching the dried chalky white crust, a few small pale flakes of dried crust loose on the rock around its beak tip, its dark back and near shoulder soft in the lower foreground and the crust sharp beyond it; vertical chalky white streaks of dried seabird droppings running down dark lava soft in the far background; entirely clean, no red anywhere, no stain; exactly one finch, no other bird; Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_foot_clamp.png → S067 (XCU, foot clamps the rock; egg deliberately out of frame)
The egg-prompt variant would have recreated an egg→flank→egg A-B-A inside 5s (S065→S066→S067),
which S067's vantage was explicitly designed to prevent. B-seed's only eggless foot box was
rejected on framing (foot = 20% of frame) at a 2.50x ceiling upscale.
S067 retarget notes: rewrite grok_prompt to the foot version (slow toe-flex + clamp, action
in frame); reconcile the action field; has_blood stays false.

```
Candid handheld wildlife documentary still, extreme telephoto macro, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. A raking near-ground extreme macro looking ACROSS bare black lava at surface height with extreme foreshortening along the rock: one adult Nazca booby's large pale grey webbed FOOT fills the left half of frame in sharp focus, its scaled toes spread wide and clamped down hard onto the rough black rock, webbing stretched tight between the toes, small claws pressed against the stone; above and behind it only the soft out-of-focus white curve of the seabird's belly feathers; NO egg anywhere in frame, no head, no bill, no horizon, no sky, no other animal; shallow macro depth of field, Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_hold_wide.png → S068 (10.5s WS hold-before)
A-seed cannot host another distinct wide (S003 full + S007/S066 at 1400 + S033 full-crop close
the whole solution space); B-seed full frame is owned by S061 20s away.

```
Candid handheld wildlife documentary still, extreme telephoto, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. A locked-off side-on telephoto WIDE at standing height: one adult Nazca booby pressed low over its nest scrape on bare black lava in strict side profile facing frame right, never facing the camera, its whole body clearly readable in the middle of frame about a third of the frame wide, with wide bare guano-streaked black rock around it on every side; THREE small jet-black vampire ground finches with SHORT BLUNT CONICAL seed-cracking beaks (never long, never pointed, never crow-like) stand motionless on the lava a short distance from the booby, spaced apart, all turned toward it; one SMALL dark red stain, dried and rust-brown and matted with no wet gloss, no drip, no run, low on the booby's near white flank; flat pale grey overcast haze behind the ledge; exactly one large seabird and exactly three small black finches; Wolf and Darwin Islands, gritty naturalistic detail.
```

## SEED_aftermath_flat.png → S082 (11s MS hold-after)
S082's content (head in profile + wing finch + two lava finches + streak) forces w≥1350 on the
A-seed, whose only legal window is the box already rejected at 1.01x from S004/S036; B-seed's
booby is STANDING (audit-verified) so the pressed-flat start state is unreachable there.

```
Candid handheld wildlife documentary still, extreme telephoto, flat overcast light, desaturated color, BBC Planet Earth realism, no golden hour, no cinematic lighting, realistic bird anatomy, 16:9, no text, no watermark, no people. A locked-off level telephoto MEDIUM from a Nazca booby's near flank at the bird's own height: the adult booby pressed completely flat down on bare guano-streaked black lava in right-facing side profile, wing folded to its flank, head held low with the long orange dagger bill angled away from the lens, dark grey facial mask and pale yellow eye in profile, never facing the camera, grey sea haze behind and a soft dark out-of-focus lava mass at the right edge of frame; ONE small jet-black vampire ground finch with a SHORT BLUNT CONICAL seed-cracking beak is worked into the white down at the base of the near wing, and TWO more jet-black ground finches stand on the lava just behind the wing; one thin dark red streak, dried and rust-brown and matted with no wet gloss, no drip, no run, runs a short way down the white flank from the wing base; exactly one large seabird and exactly three small black finches; Wolf and Darwin Islands, gritty naturalistic detail.
```

## Verify each seed before accepting (the audit's own lenses)
- Booby anatomy correct, never head-on; finch beaks SHORT/BLUNT/CONICAL, never crow.
- Creature counts exactly as the prompt names (count them).
- Every stain DRY: rust-brown, crusted, zero wet gloss, zero downward trail.
- Desaturated overcast grade matching the existing 26 seeds.
- Then retarget shots via /tmp/batch_*_out.json + apply_defect_edits.py, and re-run
  gate_shots.py + gate_crop_distinct.py + gen_seed_shopping.py.
