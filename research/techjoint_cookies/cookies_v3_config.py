"""v3 = v2 picture (approved) + rebuilt AUDIO layer only. Loaded with --variant v3.

Owner notes on v2: (1) VO chopped ("Be 75" — the 'Thre-' onset was cut at the whisperx stamp);
(2) SFX at fixed per-shot offsets with proxy sounds that don't match the screen.

What changed here vs cookies_v2_config:
- VO: assembler now cuts at MEASURED silence with padded heads/tails (see vo_blocks) — config unchanged.
- SFX_EVENTS rebuilt from a per-clip frame-strip alignment pass (strips read 2026-08-19; action
  moments noted per shot) + in-file hit offsets of each SFX (several library files have long
  silent lead-ins: egg_crack crack@1.2s, tray_laydown thud@3.95s -> pre-trimmed one-shots
  crisp_snap/tap_down/bowl_set_hit/chips_pour added to sfx/).
- New matched sounds: bread_break (soft cookie tear, C33/H1), dough_fold (sticky spatula folds,
  C16/C17/C20/C22), flour_puff (C14), butter_pour (Grok C07 native audio, reused for C09's pour
  where P2's own track is pure hiss).
- Grok native foley mixed in situ via CLIP_AUDIO: C07 pour, C18 chop (hits sync with the knife),
  C34 edge snap (snap at 0.2s in clip).
- Dropped proxies: oven_fan (C28), oven_door on C24/C27 (no door closes inside either window),
  whisk on C13 (whisk is held still), stir_bowl everywhere (near-silent file at high gain),
  tray_laydown on C23 (no tray motion), pop on C22.
Fewer, right sounds > many proxies.
"""
from cookies_v2_config import OVERRIDES as V2

OVERRIDES = dict(
    V2,
    # shot -> [(sfx_key, offset_s in shot, dur_s, gain)]  — offsets place each file so its
    # in-file transient lands on the visual action frame noted from the strip.
    SFX_EVENTS={
        "H1": [("bread_break", 0.0, 2.3, 0.6)],          # bend-open: halves part 0.3-2.0
        "H2": [("crisp_snap", 0.0, 1.2, 0.7)],           # snap at the cut
        "H3": [("tray_rack", 0.0, 1.6, 0.45)],
        "H6": [("sprinkle", 0.0, 1.6, 0.55)],            # salt already falling at in-point
        "C01": [("bowl_set_hit", 0.8, 1.0, 0.35)],       # hand settles the chip bowl
        "C03": [("bowl_set_hit", 0.85, 0.9, 0.3)],       # butter cube lands ~0.9
        "C04": [("sizzle", 0.0, 5.0, 0.45)],
        "C05": [("sizzle", 0.0, 5.0, 0.55)],
        "C06": [("sizzle", 0.0, 6.0, 0.85)],             # ASMR hold
        "C09": [("butter_pour", 0.2, 4.5, 0.5)],         # LIQUID pour onto sugars (was rice_pour)
        "C10": [("whisk", 0.0, 4.6, 0.6)],
        "C11": [("egg_crack", 0.7, 2.05, 0.8)],          # file crack@1.2 -> lands 1.9; plop 2.45
        "C14": [("flour_puff", 0.55, 0.85, 0.55)],       # flour dumps 0.7-1.5
        "C15": [("sprinkle", 2.7, 1.3, 0.45)],           # spoon tips ~3.0+
        "C16": [("dough_fold", 0.3, 2.75, 0.55), ("dough_fold", 3.4, 2.4, 0.5)],   # ASMR hold
        "C17": [("dough_fold", 0.6, 2.2, 0.35)],
        "C19": [("chips_pour", 0.3, 2.2, 0.5)],          # chips/chunks rattle in 0.2-2.3
        "C20": [("dough_fold", 0.4, 2.75, 0.4)],
        "C22": [("dough_fold", 0.1, 1.6, 0.35)],         # sticky pull as the scoop lifts
        "C24": [("tray_foley", 0.3, 1.8, 0.45)],         # tray onto fridge shelf (door never closes in-shot)
        "C25": [("tap_down", 0.1, 1.2, 0.4)],            # chilled pan set back on counter
        "C26": [("knob_spin", 1.3, 1.5, 0.5)],           # knob turns 1.5-3.0
        "C27": [("tray_rack", 0.2, 2.4, 0.55)],          # slide onto rack 0.2-2.5; no door in-shot
        "C29": [("tray_rack", 0.9, 2.4, 0.55)],          # rack contact 1.3-3.5
        "C30": [("tap_down", 0.5, 1.0, 0.6)],            # tap lands 0.6 (native transient)
        "C31": [("sprinkle", 0.2, 2.4, 0.65)],
        "C33": [("bread_break", 0.2, 2.6, 0.65)],        # soft tear over pull-apart 0.3-2.0 (ASMR)
        "C34": [("crisp_snap", 0.05, 1.2, 0.5)],         # layered under the native snap
    },
    # Grok native foley mixed under the library layer: shot -> gain or (gain, max_dur)
    CLIP_AUDIO={
        "C07": 0.8,          # browned-butter pour into glass, continuous & synced
        "C18": 0.9,          # knife chop hits at 1.6/2.8/4.25 match the blade
        "C34": (0.9, 1.4),   # edge snap at 0.2s; cap before the hiss tail
    },
)
