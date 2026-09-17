# Builds cumulative wound textures for the crucifixion model (Christ Cares).
# Wound positions come from research/christ_cares/crucifixion_medical_stages_v1.json;
# they are painted in UV space against the body's own rest-pose surface, so every
# wound sits where the literature puts it on real anatomy.
# Run inside Blender:
#   g = {"GRAPHIC": 0.75}; exec(compile(open(path).read(), path, "exec"), g)
#   g["build"](wrist_points, heel_points)     # points come from the nail axes, see NOTES
import bpy, numpy as np, math, os

RES = 2048
GRAPHIC = float(globals().get("GRAPHIC", 0.75))   # 0 = none, 1 = full severity
SEED = 7
OUT = "/Users/jefflawrence/Documents/youtube-automation-production/assets/christ_cares/crucifixion_model/wounds"
os.makedirs(OUT, exist_ok=True)

def build_surface_map(obj_name="Subject_Body", res=RES):
    """Rasterise the body's REST-pose surface position into UV space, one 3-vector per texel.
    Blender's POSITION bake came back in a scale that did not match the mesh, so this does it
    directly off the mesh: exact, and in metres."""
    body = bpy.data.objects[obj_name]
    me = body.data
    me.calc_loop_triangles()
    tl = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("loops", tl); tl = tl.reshape(-1, 3)
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    vi = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get("vertex_index", vi)
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    # drop helper geometry the Mask modifier hides
    mask = next((m for m in body.modifiers if m.type == 'MASK'), None)
    keep = np.ones(len(me.vertices), dtype=bool)
    if mask and mask.vertex_group:
        gi = body.vertex_groups[mask.vertex_group].index
        keep = np.array([any(g.group == gi for g in v.groups) for v in me.vertices])
        if mask.invert_vertex_group: keep = ~keep
    UV = uv[tl] * res
    PT = co[vi[tl]]
    good = keep[vi[tl]].all(axis=1)
    UV, PT = UV[good], PT[good]
    pos = np.zeros((res, res, 3), dtype=np.float32)
    hit = np.zeros((res, res), dtype=bool)
    for i in range(len(UV)):
        a, b, c = UV[i]
        x0 = max(int(min(a[0], b[0], c[0])) - 1, 0); x1 = min(int(max(a[0], b[0], c[0])) + 2, res)
        y0 = max(int(min(a[1], b[1], c[1])) - 1, 0); y1 = min(int(max(a[1], b[1], c[1])) + 2, res)
        if x1 <= x0 or y1 <= y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        v0 = b - a; v1 = c - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12: continue
        wx = gx - a[0]; wy = gy - a[1]
        u = (wx * v1[1] - v1[0] * wy) / den
        v = (v0[0] * wy - wx * v0[1]) / den
        m = (u >= -0.002) & (v >= -0.002) & (u + v <= 1.002)
        if not m.any(): continue
        p3 = PT[i]
        interp = (p3[0][None, None, :] * (1 - u - v)[..., None]
                  + p3[1][None, None, :] * u[..., None]
                  + p3[2][None, None, :] * v[..., None])
        pos[y0:y1, x0:x1][m] = interp[m]
        hit[y0:y1, x0:x1][m] = True
    return pos, hit

P, SURF = build_surface_map()
X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
BACK = Y > 0.005                                            # body faces -Y, so +Y is the back
rng = np.random.default_rng(SEED)

def smooth(d, r, soft=0.35):
    """1 inside radius r, feathered out."""
    return np.clip((r - d) / (r * soft + 1e-9), 0.0, 1.0)

def blend(dst_c, dst_a, mask, color, strength=1.0):
    a = np.clip(mask * strength, 0, 1)
    for i in range(3):
        dst_c[..., i] = dst_c[..., i] * (1 - a) + color[i] * a
    np.maximum(dst_a, a, out=dst_a)

# ---------------------------------------------------------------- stage 3: scourging
# Edwards 1986: flagrum with iron balls + sheep bone; back, buttocks and legs;
# welts -> deep contusions -> stripe-like lacerations into muscle.
def scourge(col, alp):
    # bands: (z-low, z-high, max |x|) — torso/buttocks/thighs/calves only.
    # Arms sit at |x| > 0.22 in the rest pose and are excluded: the sources describe
    # blows to the back, buttocks and legs.
    bands = [(1.02, 1.42, 0.21), (0.80, 1.04, 0.20), (0.48, 0.82, 0.21), (0.14, 0.50, 0.16)]
    n_str = int(26 + 22 * GRAPHIC)
    for i in range(n_str):
        z0, z1, halfw = bands[rng.integers(0, len(bands))]
        side = 1 if i % 2 == 0 else -1                      # two lictors, one each side
        ang = math.radians(rng.uniform(12, 38)) * side
        d = np.array([math.cos(ang), 0.0, math.sin(ang)])   # stripe direction in x-z
        n = np.array([-math.sin(ang), 0.0, math.cos(ang)])  # across the stripe
        zc = rng.uniform(z0, z1)
        c = n[0] * rng.uniform(-0.05, 0.05) + n[2] * zc
        proj = X * n[0] + Z * n[2]
        along = X * d[0] + Z * d[2]
        wave = 0.008 * np.sin(along * 26 + rng.uniform(0, 6.3)) + 0.004 * np.sin(along * 71 + rng.uniform(0, 6.3))
        dist = np.abs(proj - c + wave)
        zmask = (Z > z0 - 0.02) & (Z < z1 + 0.02) & (np.abs(X) < halfw)
        # the lash breaks up along its length instead of reading as a continuous ribbon
        broken = 0.45 + 0.55 * (0.5 + 0.5 * np.sin(along * rng.uniform(30, 60) + rng.uniform(0, 6.3)))
        w = rng.uniform(0.0035, 0.0065)
        base = BACK * SURF * zmask * np.clip((Y + 0.01) / 0.04, 0, 1)   # fade out toward the flanks
        deep = rng.random() < (0.35 + 0.45 * GRAPHIC)
        halo = smooth(dist, w * 1.8, 0.9) * base * broken
        blend(col, alp, halo, (0.22, 0.045, 0.035), (0.18 + 0.20 * GRAPHIC))
        core = smooth(dist, w) * base * broken
        if deep:      # torn into muscle: dark, wet, open
            blend(col, alp, core, (0.045, 0.003, 0.003), 0.88 + 0.12 * GRAPHIC)
        else:         # welt / surface split
            blend(col, alp, core, (0.115, 0.012, 0.010), 0.75 + 0.25 * GRAPHIC)
        # iron balls: round contusions at intervals along the same stroke
        phase = rng.uniform(0, 1)
        s = (along / 0.075 + phase) % 1.0
        ball = smooth(np.abs(s - 0.5), 0.16, 0.9) * smooth(dist, 0.016, 0.8) * base
        blend(col, alp, ball, (0.075, 0.020, 0.045), 0.70 * (0.5 + 0.5 * GRAPHIC))

# ---------------------------------------------------------------- stage 4: crown of thorns
def thorns(col, alp):
    head_c = np.array([0.0, -0.025, 1.595])
    d3 = np.sqrt((X - head_c[0])**2 + (Y - head_c[1])**2 + (Z - head_c[2])**2)
    scalp = (Z > 1.50) & SURF
    n_p = int(22 + 20 * GRAPHIC)
    for _ in range(n_p):
        th = rng.uniform(0, 2 * math.pi)
        zz = rng.uniform(1.53, 1.66)
        r = 0.098
        c = head_c + np.array([r * math.cos(th), r * math.sin(th) * 0.9, 0.0])
        c[2] = zz
        d = np.sqrt((X - c[0])**2 + (Y - c[1])**2 + (Z - c[2])**2)
        blend(col, alp, smooth(d, 0.0035) * scalp, (0.20, 0.02, 0.02), 0.9)
        # trickle running down from the puncture. With the faceless framing the scalp is
        # under hair, so the runs are carried below the hairline onto the neck and shoulders,
        # which is where this stage can actually be seen.
        run_to = c[2] - rng.uniform(0.06, 0.26)
        run = smooth(np.abs(X - c[0]) + np.abs(Y - c[1]) * 0.6, 0.0035) * (Z < c[2]) * (Z > run_to) * SURF
        blend(col, alp, run, (0.115, 0.012, 0.010), 0.70 * (0.5 + 0.5 * GRAPHIC))
        wide = smooth(np.abs(X - c[0]) + np.abs(Y - c[1]) * 0.6, 0.0075) * (Z < c[2]) * (Z > run_to + 0.02) * SURF
        blend(col, alp, wide, (0.21, 0.035, 0.030), 0.35 * (0.5 + 0.5 * GRAPHIC))
    _ = d3

# ---------------------------------------------------------------- stage 5: carrying the crossbar
def crossbar(col, alp):
    nape = smooth(np.abs(Z - 1.40), 0.035) * BACK * SURF * (np.abs(X) < 0.20)
    blend(col, alp, nape, (0.30, 0.09, 0.06), 0.5)
    for sgn in (1, -1):
        sh = smooth(np.sqrt((X - sgn * 0.14)**2 + (Z - 1.375)**2), 0.055) * SURF * (Y > -0.02)
        blend(col, alp, sh, (0.28, 0.08, 0.055), 0.45)

# ---------------------------------------------------------------- stage 6: nails
def nails(col, alp, wrists, heels):
    # Wrist: nail between radius and carpals, crushing the median nerve (Edwards 1986).
    # Heel: nail driven lateral-to-medial through the calcaneus (Zias & Sekeles; Ingham & Duhig).
    def puncture(c, r_core, r_bruise, run_len):
        d = np.sqrt((X - c[0])**2 + (Y - c[1])**2 + (Z - c[2])**2)
        blend(col, alp, smooth(d, r_bruise, 0.9) - smooth(d, r_core), (0.22, 0.055, 0.050), 0.60)
        blend(col, alp, smooth(d, r_core * 0.62, 0.5), (0.030, 0.002, 0.002), 1.0)
        blend(col, alp, smooth(d, r_core, 0.6) - smooth(d, r_core * 0.62), (0.105, 0.010, 0.008), 0.95)
        lat = np.sqrt((X - c[0])**2 + (Y - c[1])**2)
        run = smooth(lat, r_core * 0.55, 0.7) * (Z < c[2]) * (Z > c[2] - run_len) * SURF
        blend(col, alp, run, (0.090, 0.008, 0.008), 0.75 * (0.4 + 0.6 * GRAPHIC))
    # centres must sit ON the skin (entry and exit), not at the joint centre inside the wrist
    for c in wrists:
        puncture(c, 0.011, 0.028, 0.10)
    for c in heels:
        puncture(c, 0.010, 0.024, 0.05)

# ---------------------------------------------------------------- stage 9: spear
def spear(col, alp):
    # Entry taken off the surface map itself: right chest wall, just below the nipple line
    # (the gospel does not name the side; right is tradition, and Edwards' organ path assumes it).
    c = np.array([-0.123, -0.085, 1.179])
    d = np.sqrt((X - c[0])**2 + (Y - c[1])**2 + ((Z - c[2]) / 1.8)**2)
    blend(col, alp, smooth(d, 0.030, 0.8) - smooth(d, 0.017), (0.26, 0.055, 0.045), 0.55)  # bruised margin
    blend(col, alp, smooth(d, 0.017), (0.035, 0.002, 0.002), 1.0)                          # open wound
    # blood and watery fluid running down the flank
    lat = np.sqrt((X - c[0])**2 + (Y - c[1])**2)
    trail = smooth(lat, 0.016, 0.7) * (Z < c[2]) * (Z > 0.82) * SURF
    blend(col, alp, trail, (0.105, 0.010, 0.010), 0.75 * (0.4 + 0.6 * GRAPHIC))
    wide = smooth(lat, 0.030, 0.9) * (Z < c[2] - 0.02) * (Z > 0.86) * SURF
    blend(col, alp, wide, (0.19, 0.035, 0.030), 0.35 * (0.4 + 0.6 * GRAPHIC))

def save(col, alp, name):
    out = np.empty((RES, RES, 4), dtype=np.float32)
    out[..., :3] = col
    out[..., 3] = alp
    im = bpy.data.images.get(name)
    if im: bpy.data.images.remove(im)
    im = bpy.data.images.new(name, RES, RES, alpha=True, float_buffer=True)
    im.colorspace_settings.name = 'sRGB'
    im.pixels.foreach_set(out.reshape(-1))
    im.filepath_raw = os.path.join(OUT, name + ".png"); im.file_format = 'PNG'
    im.save()
    return im, float(alp.max()), float((alp > 0.05).mean() * 100)

def build(wrists, heels):
    col = np.zeros((RES, RES, 3), dtype=np.float32)
    alp = np.zeros((RES, RES), dtype=np.float32)
    report = {}
    steps = [("s3_scourged", lambda: scourge(col, alp)),
             ("s4_thorns",   lambda: thorns(col, alp)),
             ("s5_crossbar", lambda: crossbar(col, alp)),
             ("s6_nailed",   lambda: nails(col, alp, wrists, heels)),
             ("s9_spear",    lambda: spear(col, alp))]
    for name, fn in steps:                 # cumulative: each stage keeps the earlier wounds
        fn()
        _, mx, pct = save(col.copy(), alp.copy(), "wounds_" + name)
        report[name] = (round(mx, 2), round(pct, 2))
    return report
