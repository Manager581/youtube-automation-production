"""v2 editorial config for assemble_cookies.py (loaded with --variant v2). Everything here overrides the module
globals of the assembler: v2 clips, reuse map (hook flash-forwards + goods reprises), trims, SFX, captions, music.
Gap-analysis fixes baked in: no pops/whoosh/word-pops/title pop/timers; one small caption register; two baked-cookie
reprises; reveal ladder; longer money-shot hold; quiet bed; silence at the pull-apart."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))

OVERRIDES = dict(
    SHOTS=os.path.join(HERE, "shots_v2.json"),
    CLIPS=os.path.join(REPO, "assets", "techjoint_cookies", "clips_v2"),
    GFX=os.path.join(REPO, "assets", "techjoint_cookies", "gfx_v2"),
    # reuse map: shot -> (source clip, in-point). Hook = goods-first flash-forwards; G1/G2 = mid-process reprises.
    HOOK_SRC={"H1": ("C33", 0.0), "H2": ("C34", 0.3), "H3": ("C29", 0.5), "H4": ("C37", 0.6),
              "H5": ("C35", 0.0), "H6": ("C31", 0.4),
              "G1": ("C33", 4.0), "G2": ("C35", 0.8),
              "C09": ("P2", 0.0), "C23": ("P3", 0.0)},
    CLIP_IN={"C12": 0.0, "C13": 0.5, "C05": 1.0, "C16": 0.5, "C20": 0.5},
    DUR_OVERRIDE={"C12": 3.5, "C33": 6.5, "H1": 2.5},
    VO_BLOCKS=[("crispy", "H1", 0.25), ("here's", "C01", 0.4), ("rule", "C04", 0.4),
               ("both", "C09", 0.4), ("flour,", "C14", 0.4), ("now", "C18", 0.4),
               ("big", "C22", 0.4), ("375,", "C26", 0.4), ("okay,", "C33", 0.6), ("crispy", "C34", 0.3), ("gooey", "C35", 0.3), ("full", "C36", 0.6)],
    GAP_AFTER_BLOCK=0.45,
    SFX_EVENTS={
        "H1": [("cookie_crunch", 0.0, 1.8, 0.8)], "H2": [("crisp_crunch", 0.0, 1.4, 0.75)],
        "H3": [("tray_rack", 0.0, 1.4, 0.5)], "H6": [("sprinkle", 0.1, 1.3, 0.6)],
        "C01": [("bowl_set", 1.0, 1.2, 0.45)], "C03": [("bowl_set", 0.6, 0.8, 0.4)],
        "C04": [("sizzle", 0.0, 5.0, 0.5)], "C05": [("sizzle", 0.0, 5.0, 0.6)],
        "C06": [("sizzle", 0.0, 6.0, 0.95)], "C07": [("pour_liquid", 0.3, 3.5, 0.6)],
        "C09": [("rice_pour", 0.2, 2.5, 0.55)], "C10": [("whisk", 0.0, 4.5, 0.7)],
        "C11": [("egg_crack", 1.2, 2.0, 0.8)], "C13": [("whisk", 0.8, 3.5, 0.5)],
        "C14": [("rice_pour", 0.2, 2.8, 0.5)], "C15": [("sprinkle", 0.3, 2.5, 0.6)],
        "C16": [("stir_bowl", 0.0, 6.0, 0.95)], "C17": [("stir_bowl", 0.0, 3.5, 0.55)],
        "C18": [("chop", 0.2, 4.5, 0.95)], "C19": [("rice_pour", 0.3, 1.8, 0.45)],
        "C20": [("stir_bowl", 0.0, 4.5, 0.6)], "C22": [("bowl_set", 2.4, 0.6, 0.35)],
        "C23": [("tray_laydown", 0.8, 2.0, 0.45)], "C24": [("oven_door", 2.6, 2.2, 0.55)],
        "C25": [("tray_laydown", 0.0, 1.5, 0.4)], "C26": [("knob_spin", 0.4, 1.6, 0.6)],
        "C27": [("tray_rack", 0.0, 3.0, 0.7), ("oven_door", 3.4, 2.2, 0.6)],
        "C28": [("oven_fan", 0.0, 7.0, 0.3)], "C29": [("tray_rack", 0.0, 3.0, 0.7)],
        "C30": [("tray_foley", 0.3, 1.5, 0.9)], "C31": [("sprinkle", 0.2, 2.2, 0.8)],
        "C37": [("tray_laydown", 0.2, 0.8, 0.3)], "C38": [("tray_laydown", 1.6, 0.6, 0.25)],
        "C33": [("cookie_crunch", 0.0, 2.2, 0.9)], "C34": [("crisp_crunch", 0.1, 1.6, 0.9)],
    },
    GFX_EVENTS=[
        ("hook_claim", "H5", 0.0, 3.6),
        ("cap_choc", "C02", 0.3, 3.5), ("rule1", "C04", 0.3, 4.0), ("toffee", "C06", 2.0, 3.0), ("cool10", "C08", 0.3, 4.0),
        ("sugars", "C09", 0.3, 3.5), ("rule2", "C12", 0.2, 3.2), ("flour", "C14", 0.3, 3.0), ("soda", "C15", 0.3, 3.0),
        ("stop", "C17", 0.3, 3.2), ("choc", "C19", 0.3, 3.0), ("scoop", "C22", 0.4, 3.5), ("rule3", "C23", 0.3, 4.0),
        ("chill30", "C24", 0.3, 3.5), ("temp", "C26", 0.3, 3.4), ("bake", "C28", 0.5, 5.5), ("rest", "C32", 0.3, 3.4),
        ("card", "C36", 0.3, "end_of_shot"),
    ],
    GFX_SFX={}, POP_KEYS=set(), GFX_SLIDE=0,
    ASMR_HOLDS={"C06", "C16", "C18", "C33", "C34"},
    MUSIC_BASE=0.14, MUSIC_DIP=0.07, MUSIC_CARD=0.30,
)
