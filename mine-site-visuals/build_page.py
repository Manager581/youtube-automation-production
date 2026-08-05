#!/usr/bin/env python3
"""Build the Mine Dry Facility concept visual package.

Generates:
  - dry-facility-visuals.html  (artifact page: 2D plan + isometric view + CI projects)
  - floorplan.svg / isometric.svg (standalone copies of the two sheets)

Geometry is derived from Sarah's floor plan (scaled off the 7-ft hallway
dimension -> footprint ~= 48 ft x 42 ft). Plan coordinates: x east (0..48),
y south (0..42), feet.
"""

import math

# ---------------------------------------------------------------- palette --

INK = "#1D2A36"
PAPER = "#FFFFFF"
WALL = "#4A5560"
FLOOR_MAIN = "#F1F2F0"
FLOOR_BATH = "#DFEAF0"
FLOOR_CHANGE = "#EFE7D9"
FLOOR_HALL_A = "#FBF0D2"   # upper unit (Sarah's yellow)
FLOOR_HALL_B = "#F9E3ED"   # lower unit (Sarah's pink)
ACC_A = "#D9A421"          # yellow accent
ACC_B = "#CE6B96"          # pink accent
SAFETY = "#F26A1B"         # hi-vis coverall orange
SAFETY_DK = "#C24F0A"
NAVY = "#1B4F8A"           # Source Atlantic-style navy (innovation accent)
TEAL = "#16697A"
MAT = "#3A4048"
WOOD = "#C89B62"
GLASS = "#BAD6E4"
VOID = "#E4E7EA"
MONO = "ui-monospace,'Cascadia Mono','Segoe UI Mono',Menlo,Consolas,monospace"
SANS = "-apple-system,'Segoe UI',system-ui,Roboto,'Helvetica Neue',Arial,sans-serif"


def mix(hex_c, other, f):
    """Mix hex_c toward other by fraction f."""
    a = [int(hex_c[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * f) for x, y in zip(a, b))


def lite(c, f):
    return mix(c, "#FFFFFF", f)


def dark(c, f):
    return mix(c, "#000000", f)


def fnum(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


# ------------------------------------------------------------- layout (ft) --

W, H = 48.0, 42.0          # inner footprint
T = 0.8                    # wall thickness
HALL_X0, HALL_X1 = 30.0, 37.0     # hallway column
ROOM_X1 = 48.0                     # right rooms to east wall
TOPBATH = (30.0, 0.0, 37.0, 4.5)
NE_VOID = (37.0, 0.0, 48.0, 4.5)
UP_HALL = (30.0, 4.5, 37.0, 19.6)
UP_CHANGE = (37.0, 4.5, 48.0, 11.5)
UP_BATH = (37.0, 11.5, 48.0, 18.0)
CHASE = (37.0, 18.0, 48.0, 22.3)
LO_HALL = (30.0, 22.3, 37.0, 38.7)
LO_CHANGE = (37.0, 22.3, 48.0, 30.0)
LO_BATH = (37.0, 30.0, 48.0, 36.0)
SE_VOID = (37.0, 36.0, 48.0, 42.0)
BOT_BATH = (30.0, 38.7, 37.0, 42.0)
DOOR_X0, DOOR_X1 = 15.5, 24.0      # entrance opening in south wall
MID = (DOOR_X0 + DOOR_X1) / 2
MATS = (15.2, 39.3, 23.8, 41.0)
RACK = (0.8, 19.6, 3.0, 41.2)      # clothing rack against west wall
GRATE = (3.4, 17.2, 7.2, 19.5)     # boot-wash grate pad
CUBBY = (7.2, 17.2, 13.1, 19.5)    # boot cubbies
PINK2 = (13.1, 17.2, 17.0, 19.5)   # her pink "2 FT" block
BENCH = (7.7, 29.0, 11.3, 30.2)
RAILS_X = [16.6, 19.7, 22.7, 25.7, 28.7]
RAILS_Y = (20.6, 38.0)
VEND = (30.4, 9.0, 32.4, 12.5)     # vending vs upper hallway west wall
TVWALL = (6.0, 4.0, 10.8, 4.55)    # innovation 1: media wall
STOOLS = [(7.0, 6.2, 8.0, 7.2), (9.5, 6.2, 10.5, 7.2)]
TVZONE = (5.0, 3.2, 12.5, 8.2)
MICRO = [(6.0, 36.2, 7.2, 38.7), (6.0, 39.0, 7.2, 41.2)]  # innovation 2 kiosks
MICROZONE = (4.8, 35.3, 8.4, 41.9)

# interior door gaps (on wall line, from..to along the wall)
DOORS_X37 = [(6.5, 9.5), (13.2, 16.2), (24.7, 27.7), (31.5, 34.5)]  # y-ranges
DOOR_TOPBATH = (32.0, 35.0)   # x-range on y=4.5
DOOR_BOTBATH = (32.0, 35.0)   # x-range on y=38.7


# =========================================================== 2D FLOOR PLAN ==

def plan_svg():
    S = 16.0                       # px per ft
    ML, MT, MR, MB = 30, 30, 30, 96
    PW = round(W * S) + ML + MR
    PH = round(H * S) + MT + MB

    def X(x):
        return fnum(ML + x * S)

    def Y(y):
        return fnum(MT + y * S)

    def rect(x0, y0, x1, y1, fill, extra=""):
        return (f'<rect x="{X(x0)}" y="{Y(y0)}" width="{fnum((x1 - x0) * S)}" '
                f'height="{fnum((y1 - y0) * S)}" fill="{fill}" {extra}/>')

    def label(x, y, text, size=12.5, rotate=None, fill=INK, weight="600",
              spacing="0.08em", font=MONO, anchor="middle", halo=None):
        tr = (f' transform="rotate({rotate} {X(x)} {Y(y)})"' if rotate is not None else "")
        halo = PAPER if halo is None else halo
        hstr = (f'paint-order="stroke" stroke="{halo}" stroke-width="3.5" stroke-linejoin="round" '
                if halo != "none" else "")
        return (f'<text x="{X(x)}" y="{Y(y)}" font-family="{font}" font-size="{size}" '
                f'font-weight="{weight}" letter-spacing="{spacing}" fill="{fill}" '
                f'text-anchor="{anchor}" {hstr}{tr}>{text}</text>')

    def dim_h(x0, x1, y, text):
        """Horizontal dimension arrow."""
        p = []
        p.append(f'<line x1="{X(x0)}" y1="{Y(y)}" x2="{X(x1)}" y2="{Y(y)}" '
                 f'stroke="{INK}" stroke-width="1.2" marker-start="url(#da)" marker-end="url(#db)"/>')
        p.append(label((x0 + x1) / 2, y - 0.45, text, size=11.5))
        return "".join(p)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PW} {PH}" '
             f'role="img" aria-label="Concept floor plan of the mine dry facility: open dry area with clothing rack and drying rails on the left, two 7-foot hallways serving change rooms and bathrooms on the right, double-door entrance at the bottom, with two innovation zones marked.">')
    s.append(f'<rect width="{PW}" height="{PH}" fill="{PAPER}"/>')
    s.append('<defs>'
             f'<pattern id="hatchOpen" width="26" height="26" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="26" stroke="{mix(INK, PAPER, 0.72)}" stroke-width="1.4"/></pattern>'
             f'<pattern id="hatchVoid" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="9" height="9" fill="{VOID}"/><line x1="0" y1="0" x2="0" y2="9" stroke="{mix(INK, PAPER, 0.62)}" stroke-width="1"/></pattern>'
             f'<pattern id="hatchGrate" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="{mix(VOID, PAPER, 0.35)}"/><line x1="0" y1="0" x2="0" y2="7" stroke="{mix(INK, PAPER, 0.5)}" stroke-width="1"/></pattern>'
             f'<marker id="da" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto"><path d="M7,0 L1,3 L7,6" fill="none" stroke="{INK}" stroke-width="1.2"/></marker>'
             f'<marker id="db" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="{INK}" stroke-width="1.2"/></marker>'
             f'<marker id="entry" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="{NAVY}"/></marker>'
             '</defs>')

    # floors
    s.append(rect(0, 0, W, H, FLOOR_MAIN))
    for r, f in [(TOPBATH, FLOOR_BATH), (UP_CHANGE, FLOOR_CHANGE), (UP_BATH, FLOOR_BATH),
                 (LO_CHANGE, FLOOR_CHANGE), (LO_BATH, FLOOR_BATH), (BOT_BATH, FLOOR_BATH)]:
        s.append(rect(*r, f))
    s.append(rect(*UP_HALL, FLOOR_HALL_A))
    s.append(rect(*LO_HALL, FLOOR_HALL_B))
    for r in (NE_VOID, SE_VOID, CHASE):
        s.append(rect(*r, "url(#hatchVoid)"))
    # unit accent outlines (Sarah's yellow / pink coding)
    s.append(rect(*UP_HALL, "none", f'stroke="{ACC_A}" stroke-width="2.5"'))
    s.append(rect(*LO_HALL, "none", f'stroke="{ACC_B}" stroke-width="2.5"'))

    # open-to-building hatch region
    s.append(f'<path d="M {X(1.2)} {Y(1.2)} H {X(27)} V {Y(15.5)} H {X(1.2)} Z" fill="url(#hatchOpen)" opacity="0.55"/>')

    # walls -------------------------------------------------------------
    def wall(x0, y0, x1, y1):
        s.append(rect(x0, y0, x1, y1, WALL))

    wall(-T, -T, W + T, 0)                    # N
    wall(-T, H, DOOR_X0, H + T)               # S left of doors
    wall(DOOR_X1, H, W + T, H + T)            # S right of doors
    wall(-T, 0, 0, H)                         # W
    wall(W, 0, W + T, H)                      # E
    # hallway column west wall x=30
    wall(HALL_X0 - T, 0, HALL_X0, 19.6)
    wall(HALL_X0 - T, 22.3, HALL_X0, H)
    # x=37 wall with 4 door gaps
    prev = 0.0
    for g0, g1 in DOORS_X37 + [(H, H)]:
        if g0 > prev:
            wall(HALL_X1, prev, HALL_X1 + T, g0)
        prev = g1
    # horizontals
    for (x0, x1, y), gap in [((HALL_X0, W, 4.5), DOOR_TOPBATH),
                             ((HALL_X1, W, 11.5), None),
                             ((HALL_X1, W, 18.0), None),
                             ((HALL_X1, W, 22.3), None),
                             ((HALL_X1, W, 30.0), None),
                             ((HALL_X1, W, 36.0), None),
                             ((HALL_X0, HALL_X1, 38.7), DOOR_BOTBATH)]:
        if gap:
            wall(x0, y - T / 2, gap[0], y + T / 2)
            wall(gap[1], y - T / 2, x1, y + T / 2)
        else:
            wall(x0, y - T / 2, x1, y + T / 2)

    # door swings -------------------------------------------------------
    def swing(hx, hy, fx, fy):
        """Door leaf from hinge (hx,hy) to (fx,fy) + quarter arc."""
        r = math.hypot(fx - hx, fy - hy) * S
        s.append(f'<line x1="{X(hx)}" y1="{Y(hy)}" x2="{X(fx)}" y2="{Y(fy)}" stroke="{INK}" stroke-width="2"/>')
        # arc from leaf tip sweeping to the wall line
        a0 = math.atan2((fy - hy), (fx - hx))
        for a1 in (a0 + math.pi / 2,):
            ex = float(X(hx)) + r * math.cos(a1)
            ey = float(Y(hy)) + r * math.sin(a1)
            s.append(f'<path d="M {fnum(float(X(fx)))} {fnum(float(Y(fy)))} A {fnum(r)} {fnum(r)} 0 0 1 {fnum(ex)} {fnum(ey)}" fill="none" stroke="{mix(INK, PAPER, 0.45)}" stroke-width="1.1"/>')

    for (g0, g1) in DOORS_X37:                      # rooms open east off hallways
        swing(HALL_X1 + T, g0, HALL_X1 + T + (g1 - g0), g0)
    swing(DOOR_TOPBATH[0], 4.5 - T / 2, DOOR_TOPBATH[0], 4.5 - T / 2 - 3.0)
    swing(DOOR_BOTBATH[0], 38.7 + T / 2, DOOR_BOTBATH[0], 38.7 + T / 2 + 3.0)
    # entrance double doors
    mid = (DOOR_X0 + DOOR_X1) / 2
    swing(DOOR_X0, H, DOOR_X0, H - (mid - DOOR_X0))
    swing(DOOR_X1, H, DOOR_X1, H - (mid - DOOR_X0))

    # fixtures & features ----------------------------------------------
    # white underlays so innovation zones read cleanly over hatching
    for z in (TVZONE, MICROZONE):
        s.append(rect(*z, FLOOR_MAIN, 'rx="6"'))
    s.append(rect(*MATS, MAT, 'rx="3"'))
    s.append(rect(*RACK, SAFETY, f'stroke="{SAFETY_DK}" stroke-width="1.5"'))
    s.append(rect(*GRATE, "url(#hatchGrate)", f'stroke="{mix(INK, PAPER, 0.5)}" stroke-width="1"'))
    s.append(rect(*CUBBY, mix(SAFETY, PAPER, 0.55), f'stroke="{SAFETY_DK}" stroke-width="1.2"'))
    for i in range(1, 6):   # cubby grid
        cx = CUBBY[0] + (CUBBY[2] - CUBBY[0]) * i / 6
        s.append(f'<line x1="{X(cx)}" y1="{Y(CUBBY[1])}" x2="{X(cx)}" y2="{Y(CUBBY[3])}" stroke="{SAFETY_DK}" stroke-width="1"/>')
    s.append(f'<line x1="{X(CUBBY[0])}" y1="{Y((CUBBY[1]+CUBBY[3])/2)}" x2="{X(CUBBY[2])}" y2="{Y((CUBBY[1]+CUBBY[3])/2)}" stroke="{SAFETY_DK}" stroke-width="1"/>')
    s.append(rect(*PINK2, mix(ACC_B, PAPER, 0.35), f'stroke="{ACC_B}" stroke-width="1.5"'))
    s.append(rect(*BENCH, WOOD, f'stroke="{dark(WOOD, 0.3)}" stroke-width="1.2"'))
    for rx in RAILS_X:
        s.append(f'<line x1="{X(rx)}" y1="{Y(RAILS_Y[0])}" x2="{X(rx)}" y2="{Y(RAILS_Y[1])}" stroke="{INK}" stroke-width="2.4"/>')
        for ry in (RAILS_Y[0], RAILS_Y[1]):
            s.append(f'<circle cx="{X(rx)}" cy="{Y(ry)}" r="3" fill="{INK}"/>')
    s.append(rect(*VEND, NAVY, 'rx="2"'))
    # innovation zones
    for z in (TVZONE, MICROZONE):
        s.append(rect(*z, "none", f'stroke="{NAVY}" stroke-width="2" stroke-dasharray="7 5" rx="6"'))
    s.append(rect(*TVWALL, dark(NAVY, 0.25)))
    for st in STOOLS:
        s.append(rect(*st, mix(NAVY, PAPER, 0.55), 'rx="4"'))
    for mk in MICRO:
        s.append(rect(*mk, TEAL, 'rx="2"'))

    # badges ------------------------------------------------------------
    def badge(x, y, n):
        s.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="12" fill="{NAVY}" stroke="{PAPER}" stroke-width="2.5"/>')
        s.append(f'<text x="{X(x)}" y="{fnum(float(Y(y)) + 4.5)}" font-family="{SANS}" font-size="13.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">{n}</text>')

    badge(TVZONE[2] - 0.55, TVZONE[1] + 0.75, 1)
    badge(MICROZONE[2] - 0.7, MICROZONE[1] + 0.9, 2)

    # labels ------------------------------------------------------------
    s.append(label(14, 10.2, "OPEN TO BUILDING", size=13.5, fill=mix(INK, PAPER, 0.25)))
    s.append(label(1.9, 30.5, "CLOTHING RACK", size=11.5, rotate=-90, fill="#FFFFFF", halo="none"))
    s.append(label(10.15, 16.3, "BOOT CUBBIES", size=10.5))
    s.append(label(15.05, 18.6, "2 FT", size=10.5))
    s.append(label(9.5, 28.2, "BENCH", size=10.5))
    s.append(label(21.2, 29.9, "DRYING RAILS", size=11.5, rotate=-90))
    s.append(label(31.4, 10.9, "VENDING", size=10, rotate=-90, fill="#FFFFFF", halo="none"))
    s.append(label(33.5, 2.5, "BATHROOM", size=11))
    s.append(label(33.5, 14.2, "HALLWAY", size=11.5))
    s.append(label(33.5, 15.4, "7 FT WIDE", size=10.5))
    s.append(dim_h(HALL_X0, HALL_X1, 17.8, "7 FT"))
    s.append(label(42.5, 8.2, "CHANGE ROOM", size=11))
    s.append(label(42.5, 15.0, "BATHROOM", size=11))
    s.append(label(33.5, 29.8, "HALLWAY", size=11.5))
    s.append(label(33.5, 31.0, "7 FT WIDE", size=10.5))
    s.append(dim_h(HALL_X0, HALL_X1, 36.6, "7 FT"))
    s.append(label(42.5, 26.4, "CHANGE ROOM", size=11))
    s.append(label(42.5, 33.2, "BATHROOM", size=11))
    s.append(label(33.5, 40.6, "BATHROOM", size=11))
    s.append(label(8.75, 7.6, "TV INNOVATION HUB", size=10.5, fill=NAVY))
    s.append(label(6.6, 34.6, "MICRO-MARKET", size=10.5, fill=NAVY))
    # entrance arrow + label (label sits beside the arrow, clear of the legend)
    s.append(f'<line x1="{X(mid)}" y1="{Y(H + 1.6)}" x2="{X(mid)}" y2="{Y(H - 2.2)}" stroke="{NAVY}" stroke-width="2.2" marker-end="url(#entry)"/>')
    s.append(label(mid + 1.0, H + 1.9, "MAIN ENTRY — DOUBLE DOORS · SAFETY MATS", size=11.5, fill=NAVY, anchor="start"))

    # legend + titleblock ----------------------------------------------
    ly = round(H * S) + MT + 56
    items = [(FLOOR_CHANGE, "CHANGE ROOM"), (FLOOR_BATH, "BATHROOM"),
             (FLOOR_HALL_A, "UNIT A"), (FLOOR_HALL_B, "UNIT B"),
             (SAFETY, "EXISTING FEATURE"), (NAVY, "CI INNOVATION")]
    lx = ML
    for c, t in items:
        s.append(f'<rect x="{lx}" y="{ly}" width="14" height="14" fill="{c}" stroke="{mix(INK, PAPER, 0.4)}" stroke-width="1" rx="2"/>')
        s.append(f'<text x="{lx + 20}" y="{ly + 11.5}" font-family="{MONO}" font-size="10.5" letter-spacing="0.04em" fill="{INK}">{t}</text>')
        lx += 30 + len(t) * 6.9
    s.append(f'<text x="{PW - MR}" y="{ly + 33}" font-family="{MONO}" font-size="10.5" letter-spacing="0.06em" fill="{mix(INK, PAPER, 0.35)}" text-anchor="end">SK-01 · CONCEPT FLOOR PLAN · DIMENSIONS APPROX. · NOT FOR CONSTRUCTION</text>')
    s.append('</svg>')
    return "".join(s)


# ============================================================== ISOMETRIC ==

CO = math.cos(math.radians(30))


class Iso:
    def __init__(self, scale=13.0):
        self.S = scale
        self.polys = []   # drawn in append order

    def pt(self, x, y, z=0.0):
        u = (x - y) * CO * self.S
        v = (x + y) * 0.5 * self.S - z * 0.92 * self.S
        return (u, v)

    def poly(self, pts3, fill, stroke=None, sw=1.0, opacity=None, dash=None, layer=None):
        p = " ".join(f"{u:.1f},{v:.1f}" for u, v in (self.pt(*p) for p in pts3))
        at = f'<polygon points="{p}" fill="{fill}"'
        at += f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ' stroke="none"'
        if opacity is not None:
            at += f' opacity="{opacity}"'
        if dash:
            at += f' stroke-dasharray="{dash}"'
        (layer if layer is not None else self.polys).append(at + "/>")

    def flat(self, x0, y0, x1, y1, fill, z=0.0, **kw):
        self.poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], fill, **kw)

    def box(self, x0, y0, x1, y1, z0, z1, base, cap=None, outline=None, layer=None):
        top = cap or lite(base, 0.22)
        south = base
        east = dark(base, 0.22)
        ol = outline or dark(base, 0.45)
        self.poly([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], south, ol, 0.8, layer=layer)
        self.poly([(x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0)], east, ol, 0.8, layer=layer)
        self.poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top, ol, 0.8, layer=layer)


def iso_svg():
    iso = Iso(13.0)
    S = iso.S
    # canvas bounds
    us = [iso.pt(x, y, z) for x in (0, W) for y in (0, H) for z in (0, 8)]
    umin = min(u for u, _ in us) - 306
    umax = max(u for u, _ in us) + 160
    vmin = min(v for _, v in us) - 66
    vmax = max(v for _, v in us) + 108
    PW, PH = umax - umin, vmax - vmin

    def TX(u, v):
        return (u - umin, v - vmin)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PW:.0f} {PH:.0f}" '
             f'role="img" aria-label="Isometric cutaway view of the mine dry facility: orange coveralls on the clothing rack and drying rails, double glass entrance doors with black mats, two color-coded hallways serving change rooms and bathrooms, vending, plus the proposed TV innovation hub and micro-market zones.">')
    s.append(f'<g transform="translate({-umin:.1f},{-vmin:.1f})">')

    # ground shadow
    sh = [(0 - 1.5, 0 - 0.5, 0), (W + 1.6, 0 - 0.5, 0), (W + 3.2, H + 2.4, 0), (0 - 0.2, H + 2.6, 0)]
    iso.poly(sh, mix(INK, PAPER, 0.88), opacity=0.6)

    # slab sides + floor
    SL = 0.9
    iso.poly([(0 - T, H + T, 0), (W + T, H + T, 0), (W + T, H + T, -SL), (0 - T, H + T, -SL)], mix(WALL, PAPER, 0.25))
    iso.poly([(W + T, 0 - T, 0), (W + T, H + T, 0), (W + T, H + T, -SL), (W + T, 0 - T, -SL)], mix(WALL, "#000000", 0.05))
    iso.flat(0 - T, 0 - T, W + T, H + T, FLOOR_MAIN)

    # region floors
    for r, f in [(TOPBATH, FLOOR_BATH), (UP_CHANGE, FLOOR_CHANGE), (UP_BATH, FLOOR_BATH),
                 (LO_CHANGE, FLOOR_CHANGE), (LO_BATH, FLOOR_BATH), (BOT_BATH, FLOOR_BATH),
                 (UP_HALL, FLOOR_HALL_A), (LO_HALL, FLOOR_HALL_B),
                 (NE_VOID, VOID), (SE_VOID, VOID), (CHASE, VOID)]:
        iso.flat(*r, f)

    # open-to-building hatch (floor strokes)
    for i in range(7):
        y0 = 2.0 + i * 1.9
        iso.poly([(2.2, y0, 0), (25.5, y0, 0), (25.5, y0 + 0.55, 0), (2.2, y0 + 0.55, 0)],
                 mix(INK, PAPER, 0.86), opacity=0.5)

    # flat markings
    iso.flat(*MATS, MAT)
    iso.flat(*GRATE, mix(VOID, INK, 0.12))
    iso.flat(*TVZONE, NAVY, opacity=0.06)
    iso.flat(*MICROZONE, NAVY, opacity=0.06)
    zb = []
    for z in (TVZONE, MICROZONE):
        iso.poly([(z[0], z[1], 0), (z[2], z[1], 0), (z[2], z[3], 0), (z[0], z[3], 0)],
                 "none", NAVY, 1.6, dash="6 4", layer=zb)
    s.extend(iso.polys)
    s.extend(zb)
    iso.polys = []

    # ------------------------------------------------ solids (painter sort)
    solids = []   # (sortkey, [poly strings])

    def add(fn, *a, key=None, **kw):
        buf = []
        fn(*a, layer=buf, **kw)
        k = key if key is not None else (a[0] + a[1])
        solids.append((k, buf))

    def wall_box(x0, y0, x1, y1, h, cap=None):
        add(iso.box, x0, y0, x1, y1, 0, h, WALL, key=x0 + y0,
            cap=cap or lite(WALL, 0.35), outline=dark(WALL, 0.35))

    H_BACK, H_STUB, H_INT = 5.0, 2.6, 3.5
    capA, capB = mix(ACC_A, "#FFFFFF", 0.15), mix(ACC_B, "#FFFFFF", 0.15)

    # perimeter
    wall_box(-T, -T, W + T, 0, H_BACK)                 # N
    wall_box(-T, 0, 0, H + T, H_BACK)                  # W
    wall_box(-T, H, DOOR_X0, H + T, H_STUB)            # S left
    wall_box(DOOR_X1, H, W + T, H + T, H_STUB)         # S right
    wall_box(W, -T, W + T, H, H_STUB)                  # E
    # hallway column west walls
    wall_box(HALL_X0 - T, 0, HALL_X0, 19.6, H_INT, cap=capA)
    wall_box(HALL_X0 - T, 22.3, HALL_X0, H, H_INT, cap=capB)
    # x=37 wall segments (door gaps)
    prev = 0.0
    for g0, g1 in DOORS_X37 + [(H, H)]:
        if g0 > prev:
            cap = capA if g0 <= 19.6 else capB
            wall_box(HALL_X1, prev, HALL_X1 + T, g0, H_INT, cap=cap)
        prev = g1
    # horizontal interior walls
    for (x0, x1, y), gap, cap in [((HALL_X0, W, 4.5), DOOR_TOPBATH, capA),
                                  ((HALL_X1, W, 11.5), None, capA),
                                  ((HALL_X1, W, 18.0), None, capA),
                                  ((HALL_X1, W, 22.3), None, capB),
                                  ((HALL_X1, W, 30.0), None, capB),
                                  ((HALL_X1, W, 36.0), None, capB),
                                  ((HALL_X0, HALL_X1, 38.7), DOOR_BOTBATH, capB)]:
        if gap:
            wall_box(x0, y - T / 2, gap[0], y + T / 2, H_INT, cap=cap)
            wall_box(gap[1], y - T / 2, x1, y + T / 2, H_INT, cap=cap)
        else:
            wall_box(x0, y - T / 2, x1, y + T / 2, H_INT, cap=cap)

    # interior room doors (open leaf panels, wood)
    for g0, g1 in DOORS_X37:
        add(iso.box, HALL_X1 + 0.15, g1 - 0.12, HALL_X1 + 2.4, g1 + 0.12, 0, 3.4,
            mix(WOOD, INK, 0.25), key=HALL_X1 + g1)
    add(iso.box, DOOR_TOPBATH[0] - 0.12, 4.5 - 2.4, DOOR_TOPBATH[0] + 0.12, 4.5 - 0.15, 0, 3.4,
        mix(WOOD, INK, 0.25), key=DOOR_TOPBATH[0] + 3.2)
    add(iso.box, DOOR_BOTBATH[0] - 0.12, 38.7 + 0.15, DOOR_BOTBATH[0] + 0.12, 38.7 + 2.4, 0, 3.4,
        mix(WOOD, INK, 0.25), key=DOOR_BOTBATH[0] + 39.4)

    # clothing rack: posts, rail, coveralls
    add(iso.box, 1.35, RACK[1], 1.75, RACK[1] + 0.4, 0, 4.8, dark(WALL, 0.1))
    add(iso.box, 1.35, RACK[3] - 0.4, 1.75, RACK[3], 0, 4.8, dark(WALL, 0.1))
    add(iso.box, 1.4, RACK[1], 1.7, RACK[3], 4.5, 4.8, SAFETY_DK, key=1.4 + RACK[1] + 0.01)
    yc = RACK[1] + 0.7
    i = 0
    while yc + 0.95 < RACK[3] - 0.5:
        c = SAFETY if i % 3 else mix(SAFETY, "#FFFFFF", 0.16)
        add(iso.box, 1.15, yc, 1.95, yc + 0.95, 1.9, 4.35, c, outline=SAFETY_DK)
        yc += 1.4
        i += 1

    # boot grate row features
    add(iso.box, *CUBBY, 0, 3.0, mix(SAFETY, PAPER, 0.45), outline=SAFETY_DK)
    # cubby grid lines on south face
    gl = []
    for j in range(1, 6):
        cx = CUBBY[0] + (CUBBY[2] - CUBBY[0]) * j / 6
        a, b = iso.pt(cx, CUBBY[3], 2.9), iso.pt(cx, CUBBY[3], 0.1)
        gl.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{SAFETY_DK}" stroke-width="0.9" opacity="0.75"/>')
    a, b = iso.pt(CUBBY[0], CUBBY[3], 1.5), iso.pt(CUBBY[2], CUBBY[3], 1.5)
    gl.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{SAFETY_DK}" stroke-width="0.9" opacity="0.75"/>')
    solids.append((CUBBY[0] + CUBBY[1] + 0.02, gl))
    add(iso.box, *PINK2, 0, 3.0, mix(ACC_B, PAPER, 0.25), outline=ACC_B)
    p2 = iso.pt(14.3, PINK2[3], 1.5)
    solids.append((PINK2[0] + PINK2[1] + 0.03,
                   [f'<text x="{p2[0]:.1f}" y="{p2[1] + 4:.1f}" font-family="{MONO}" font-size="11" font-weight="700" fill="{dark(ACC_B, 0.35)}" text-anchor="middle">2 FT</text>']))
    add(iso.box, *BENCH, 0, 1.4, WOOD)

    # drying rails with hung coveralls (uniform rows, like the site photo)
    for rx in RAILS_X:
        add(iso.box, rx - 0.1, RAILS_Y[0], rx + 0.1, RAILS_Y[0] + 0.22, 0, 4.55, dark(WALL, 0.05))
        add(iso.box, rx - 0.1, RAILS_Y[1] - 0.22, rx + 0.1, RAILS_Y[1], 0, 4.55, dark(WALL, 0.05))
        add(iso.box, rx - 0.08, RAILS_Y[0], rx + 0.08, RAILS_Y[1], 4.35, 4.55, dark(WALL, 0.2),
            key=rx - 0.08 + RAILS_Y[0] + 0.01)
        for j, yc in enumerate((23.0, 26.4, 29.8, 33.2)):
            c = SAFETY if j % 2 else dark(SAFETY, 0.1)
            add(iso.box, rx - 0.38, yc, rx + 0.38, yc + 1.05, 2.05, 4.25, c, outline=SAFETY_DK)

    # vending machine (existing, upper hallway)
    add(iso.box, *VEND, 0, 5.8, dark(NAVY, 0.1))
    vf = []
    iso.poly([(VEND[2], VEND[1] + 0.25, 5.4), (VEND[2], VEND[3] - 0.9, 5.4),
              (VEND[2], VEND[3] - 0.9, 0.6), (VEND[2], VEND[1] + 0.25, 0.6)],
             lite(NAVY, 0.45), opacity=0.9, layer=vf)
    solids.append((VEND[0] + VEND[1] + 0.05, vf))

    # bathroom fixtures: (toilet box + tank) + sink
    def bath_fix(tx, ty, tank_side, sx, sy):
        add(iso.box, tx, ty, tx + 1.3, ty + 1.8, 0, 1.25, "#F4F7F8", outline=mix(INK, PAPER, 0.45))
        if tank_side == "n":
            add(iso.box, tx, ty - 0.45, tx + 1.3, ty, 0, 2.3, "#E9EEF0", outline=mix(INK, PAPER, 0.45))
        else:
            add(iso.box, tx + 1.3, ty, tx + 1.75, ty + 1.8, 0, 2.3, "#E9EEF0", outline=mix(INK, PAPER, 0.45))
        add(iso.box, sx, sy, sx + 1.3, sy + 1.1, 0, 2.5, "#F4F7F8", outline=mix(INK, PAPER, 0.45))

    bath_fix(31.2, 1.3, "n", 34.6, 0.9)          # top bathroom
    bath_fix(44.9, 12.3, "e", 45.4, 16.0)        # upper-right bathroom
    bath_fix(44.9, 30.8, "e", 45.4, 34.3)        # lower-right bathroom
    bath_fix(30.9, 39.3, "e", 34.6, 39.6)        # bottom bathroom

    # change room benches
    add(iso.box, 41.0, 7.4, 45.0, 8.6, 0, 1.4, WOOD)
    add(iso.box, 41.0, 25.4, 45.0, 26.6, 0, 1.4, WOOD)

    # innovation 1: TV hub
    add(iso.box, *TVWALL, 0, 6.2, dark(NAVY, 0.3))
    tv = []
    iso.poly([(TVWALL[0] + 0.7, TVWALL[3], 5.6), (TVWALL[2] - 0.7, TVWALL[3], 5.6),
              (TVWALL[2] - 0.7, TVWALL[3], 2.6), (TVWALL[0] + 0.7, TVWALL[3], 2.6)],
             "#0C1116", stroke=lite(NAVY, 0.4), sw=1.2, layer=tv)
    iso.poly([(TVWALL[0] + 1.0, TVWALL[3], 5.25), (TVWALL[2] - 2.2, TVWALL[3], 5.25),
              (TVWALL[2] - 2.2, TVWALL[3], 4.4), (TVWALL[0] + 1.0, TVWALL[3], 4.4)],
             mix(NAVY, "#8FD0FF", 0.75), opacity=0.85, layer=tv)
    iso.poly([(TVWALL[0] + 1.0, TVWALL[3], 4.1), (TVWALL[2] - 1.1, TVWALL[3], 4.1),
              (TVWALL[2] - 1.1, TVWALL[3], 3.9), (TVWALL[0] + 1.0, TVWALL[3], 3.9)],
             lite(NAVY, 0.55), opacity=0.8, layer=tv)
    solids.append((TVWALL[0] + TVWALL[1] + 0.05, tv))
    for st in STOOLS:
        add(iso.box, *st, 0, 1.5, mix(NAVY, PAPER, 0.45))

    # innovation 2: micro-market kiosks
    for k, mk in enumerate(MICRO):
        add(iso.box, *mk, 0, 5.6, TEAL if k == 0 else dark(TEAL, 0.15))
        kf = []
        iso.poly([(mk[2], mk[1] + 0.2, 5.2), (mk[2], mk[3] - 0.2, 5.2),
                  (mk[2], mk[3] - 0.2, 0.7), (mk[2], mk[1] + 0.2, 0.7)],
                 lite(TEAL, 0.5), opacity=0.9, layer=kf)
        solids.append((mk[0] + mk[1] + 0.05, kf))

    # entrance: frames + glass doors
    add(iso.box, DOOR_X0 - 0.35, H, DOOR_X0, H + T, 0, 7.2, "#20262C")
    add(iso.box, DOOR_X1, H, DOOR_X1 + 0.35, H + T, 0, 7.2, "#20262C")
    add(iso.box, MID - 0.12, H, MID + 0.12, H + T, 0, 6.8, "#20262C")
    add(iso.box, DOOR_X0, H, DOOR_X1, H + T, 6.8, 7.4, "#20262C", key=DOOR_X0 + H + 0.05)
    gz = []
    for gx0, gx1 in ((DOOR_X0 + 0.15, MID - 0.2), (MID + 0.2, DOOR_X1 - 0.15)):
        iso.poly([(gx0, H + 0.1, 6.6), (gx1, H + 0.1, 6.6), (gx1, H + 0.1, 0.15), (gx0, H + 0.1, 0.15)],
                 GLASS, stroke="#20262C", sw=1.4, opacity=0.55, layer=gz)
        iso.poly([(gx0, H + 0.1, 3.4), (gx1, H + 0.1, 3.4), (gx1, H + 0.1, 3.15), (gx0, H + 0.1, 3.15)],
                 "#20262C", opacity=0.9, layer=gz)
    solids.append((DOOR_X0 + H + 0.1, gz))

    solids.sort(key=lambda t: t[0])
    for _, buf in solids:
        s.extend(buf)

    # ------------------------------------------------------------- labels
    # Leader labels live in the left/right margins at explicit canvas spots
    # (world u,v coordinates, pre-translate) so they never sit on geometry.
    LX = umin + 292          # left column: text ends here
    RX = umax - 152          # right column: text starts here

    def lab(x, y, z, lu, lv, text, color=INK, size=12, anchor="end"):
        u, v = iso.pt(x, y, z)
        s.append(f'<circle cx="{u:.1f}" cy="{v:.1f}" r="2.6" fill="{color}"/>')
        s.append(f'<line x1="{u:.1f}" y1="{v:.1f}" x2="{lu:.1f}" y2="{lv:.1f}" stroke="{color}" stroke-width="1.1" opacity="0.85"/>')
        tx = lu - 7 if anchor == "end" else lu + 7
        s.append(f'<text x="{tx:.1f}" y="{lv + 4:.1f}" font-family="{MONO}" '
                 f'font-size="{size}" font-weight="600" letter-spacing="0.07em" fill="{color}" text-anchor="{anchor}" '
                 f'paint-order="stroke" stroke="{PAPER}" stroke-width="3.5" stroke-linejoin="round">{text}</text>')

    def flab(x, y, text, color, size=11.5):
        """Label drawn directly on an open floor area (no leader)."""
        u, v = iso.pt(x, y, 0)
        s.append(f'<text x="{u:.1f}" y="{v:.1f}" font-family="{MONO}" font-size="{size}" font-weight="700" '
                 f'letter-spacing="0.08em" fill="{color}" text-anchor="middle" '
                 f'paint-order="stroke" stroke="{PAPER}" stroke-width="3" stroke-linejoin="round">{text}</text>')

    # left margin, top to bottom
    lab(1.55, 23.0, 4.9, LX, 96, "CLOTHING RACK — ORANGE COVERALLS", SAFETY_DK)
    lab(10.15, 17.4, 2.9, LX, 152, "BOOT CUBBIES")
    lab(16.6, 21.5, 4.5, LX, 260, "DRYING RAILS")
    lab(MID - 3.0, H + 0.4, 6.9, LX, 392, "MAIN ENTRY — GLASS DOUBLE DOORS", "#20262C")
    lab(MID + 0.5, 40.2, 0.1, LX, 442, "SAFETY MATS", "#20262C")
    # right margin, top to bottom
    lab(33.5, 1.2, 4.9, RX, 108, "BATHROOM", anchor="start")
    lab(31.5, 9.6, 5.7, RX, 154, "VENDING", dark(NAVY, 0.1), anchor="start")
    lab(43.5, 5.4, 3.4, RX, 212, "CHANGE ROOM", anchor="start")
    lab(46.0, 12.4, 3.4, RX, 270, "BATHROOM", anchor="start")
    lab(44.0, 23.0, 3.4, RX, 358, "CHANGE ROOM", anchor="start")
    lab(46.0, 31.0, 3.4, RX, 422, "BATHROOM", anchor="start")
    lab(34.5, 41.0, 3.3, RX, 488, "BATHROOM", anchor="start")
    # floor labels (no leader)
    flab(33.5, 13.8, "HALLWAY", dark(ACC_A, 0.35))
    flab(34.6, 15.6, "7 FT", dark(ACC_A, 0.35))
    flab(33.0, 31.4, "HALLWAY", dark(ACC_B, 0.25))
    flab(34.1, 33.2, "7 FT", dark(ACC_B, 0.25))
    flab(16.5, 10.8, "OPEN TO BUILDING", mix(INK, PAPER, 0.4), size=12.5)

    def ibadge(x, y, z, n, bu, bv, text, anchor="end"):
        u, v = iso.pt(x, y, z)
        s.append(f'<line x1="{u:.1f}" y1="{v:.1f}" x2="{bu:.1f}" y2="{bv:.1f}" stroke="{NAVY}" stroke-width="1.2"/>')
        s.append(f'<circle cx="{bu:.1f}" cy="{bv:.1f}" r="12" fill="{NAVY}" stroke="{PAPER}" stroke-width="2.5"/>')
        s.append(f'<text x="{bu:.1f}" y="{bv + 4.5:.1f}" font-family="{SANS}" font-size="13.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">{n}</text>')
        tx = bu - 18 if anchor == "end" else bu + 18
        s.append(f'<text x="{tx:.1f}" y="{bv + 4.5:.1f}" font-family="{MONO}" font-size="12" '
                 f'font-weight="700" letter-spacing="0.07em" fill="{NAVY}" text-anchor="{anchor}" '
                 f'paint-order="stroke" stroke="{PAPER}" stroke-width="3.5" stroke-linejoin="round">{text}</text>')

    tvu, tvv = iso.pt(8.75, 4.2, 6.4)
    ibadge(8.75, 4.2, 6.4, 1, tvu + 26, -40, "TV INNOVATION HUB", anchor="start")
    ibadge(6.6, 38.5, 2.0, 2, LX + 16, 330, "MICRO-MARKET VENDING")

    s.append('</g>')
    s.append(f'<text x="{PW - 14:.0f}" y="{PH - 12:.0f}" font-family="{MONO}" font-size="10.5" letter-spacing="0.06em" '
             f'fill="{mix(INK, PAPER, 0.35)}" text-anchor="end">SK-02 · CONCEPT ISOMETRIC VIEW · DIMENSIONS APPROX. · NOT FOR CONSTRUCTION</text>')
    s.append('</svg>')
    return "".join(s)


# ==================================================================== HTML ==

def html_page(plan, iso):
    return f"""<title>Mine Dry Facility — Concept Visuals</title>
<style>
  :root {{
    --bg: #EDF0F2; --ink: #1D2A36; --sub: #5B6B7A; --line: #D4DBE1;
    --accent: {SAFETY}; --navy: {NAVY}; --card: #FFFFFF;
    --sheet-shadow: 0 1px 2px rgba(29,42,54,.08), 0 10px 28px rgba(29,42,54,.10);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #12181E; --ink: #E7ECF1; --sub: #94A3B1; --line: #2A3540;
            --card: #1A222B; --sheet-shadow: 0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.45); }}
  }}
  :root[data-theme="dark"] {{ --bg: #12181E; --ink: #E7ECF1; --sub: #94A3B1; --line: #2A3540;
            --card: #1A222B; --sheet-shadow: 0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.45); }}
  :root[data-theme="light"] {{ --bg: #EDF0F2; --ink: #1D2A36; --sub: #5B6B7A; --line: #D4DBE1;
            --card: #FFFFFF; --sheet-shadow: 0 1px 2px rgba(29,42,54,.08), 0 10px 28px rgba(29,42,54,.10); }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
         font-family: {SANS}; line-height: 1.55; }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 40px 22px 72px; }}
  .eyebrow {{ font-family: {MONO}; font-size: 12px; letter-spacing: .18em; color: var(--accent);
              font-weight: 700; margin: 0 0 10px; }}
  h1 {{ font-size: clamp(26px, 4.4vw, 40px); line-height: 1.12; margin: 0 0 10px;
        font-weight: 800; letter-spacing: -0.015em; text-wrap: balance; }}
  .meta {{ font-family: {MONO}; font-size: 12.5px; color: var(--sub); letter-spacing: .05em;
           display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 0 0 8px; }}
  .rule {{ border: 0; border-top: 2px solid var(--ink); margin: 22px 0 34px; opacity: .85; }}
  .sheet {{ background: var(--card); border-radius: 10px; box-shadow: var(--sheet-shadow);
            margin: 0 0 34px; overflow: hidden; border: 1px solid var(--line); }}
  .sheet-head {{ display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
                 padding: 14px 18px; border-bottom: 1px solid var(--line); }}
  .sk {{ font-family: {MONO}; font-weight: 700; font-size: 13px; letter-spacing: .1em;
         color: #fff; background: var(--navy); padding: 4px 10px; border-radius: 5px; }}
  .sheet-title {{ font-weight: 700; font-size: 15.5px; letter-spacing: .01em; }}
  .spacer {{ flex: 1; }}
  button.dl {{ font-family: {MONO}; font-size: 12.5px; font-weight: 600; letter-spacing: .04em;
               color: var(--ink); background: transparent; border: 1.5px solid var(--ink);
               border-radius: 7px; padding: 7px 14px; cursor: pointer; }}
  button.dl:hover {{ background: var(--ink); color: var(--bg); }}
  button.dl:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .dl-note {{ font-family: {MONO}; font-size: 11.5px; color: var(--sub); }}
  .sheet-body {{ background: #FFFFFF; padding: 10px; overflow-x: auto; }}
  .sheet-body svg {{ display: block; min-width: 640px; max-width: 100%; height: auto; margin: 0 auto; }}
  h2 {{ font-size: 21px; margin: 46px 0 6px; letter-spacing: -0.01em; }}
  .h2-sub {{ color: var(--sub); font-size: 14.5px; margin: 0 0 20px; max-width: 68ch; }}
  .ci-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; }}
  .ci {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
         padding: 18px 20px; box-shadow: var(--sheet-shadow); }}
  .ci-tag {{ display: inline-flex; align-items: center; gap: 9px; margin-bottom: 10px; }}
  .ci-num {{ width: 26px; height: 26px; border-radius: 50%; background: var(--navy); color: #fff;
             display: inline-flex; align-items: center; justify-content: center;
             font-weight: 700; font-size: 14px; }}
  .ci-kicker {{ font-family: {MONO}; font-size: 11.5px; letter-spacing: .14em; color: var(--sub); font-weight: 700; }}
  .ci h3 {{ margin: 0 0 8px; font-size: 16.5px; }}
  .ci p {{ margin: 0; font-size: 14px; color: var(--sub); }}
  .notes {{ margin: 18px 0 0; padding: 0 0 0 18px; color: var(--sub); font-size: 13.5px; max-width: 72ch; }}
  .notes li {{ margin-bottom: 6px; }}
  footer {{ margin-top: 52px; padding-top: 16px; border-top: 1px solid var(--line);
            font-family: {MONO}; font-size: 12px; color: var(--sub); letter-spacing: .05em; }}
  @media (prefers-reduced-motion: no-preference) {{
    .sheet, .ci {{ transition: box-shadow .2s ease; }}
  }}
</style>
<div class="wrap">
  <header>
    <p class="eyebrow">SOURCE ATLANTIC · SITE SERVICES PROPOSAL</p>
    <h1>Mine Dry Facility — Concept Visual Package</h1>
    <div class="meta">
      <span>SUDBURY OPERATIONS</span><span>SHEETS SK-01 / SK-02</span>
      <span>CONCEPT FOR RFP RESPONSE</span><span>AUG 2026</span>
    </div>
  </header>
  <hr class="rule"/>

  <section class="sheet" id="sheet1">
    <div class="sheet-head">
      <span class="sk">SK-01</span>
      <span class="sheet-title">Concept Floor Plan — Dry &amp; Change Facility</span>
      <span class="spacer"></span>
      <span class="dl-note" id="note1"></span>
      <button class="dl" id="dl1" hidden>Download PNG</button>
    </div>
    <div class="sheet-body">{plan}</div>
  </section>

  <section class="sheet" id="sheet2">
    <div class="sheet-head">
      <span class="sk">SK-02</span>
      <span class="sheet-title">Concept Isometric View — Existing Layout + Proposed Innovations</span>
      <span class="spacer"></span>
      <span class="dl-note" id="note2"></span>
      <button class="dl" id="dl2" hidden>Download PNG</button>
    </div>
    <div class="sheet-body">{iso}</div>
  </section>

  <h2>Continuous-Improvement Innovation Projects</h2>
  <p class="h2-sub">Two site-specific CI projects proposed for this location, shown as
  numbered zones on both sheets.</p>
  <div class="ci-grid">
    <div class="ci">
      <span class="ci-tag"><span class="ci-num">1</span><span class="ci-kicker">CI PROJECT · THIS SITE</span></span>
      <h3>TV Innovation Hub</h3>
      <p>A digital display wall at the building-side entry of the dry: live safety
      metrics, shift notices, PPE availability, and continuous-improvement ideas from
      the crew. Turns dead wall space into a communication point every worker passes
      twice a shift.</p>
    </div>
    <div class="ci">
      <span class="ci-tag"><span class="ci-num">2</span><span class="ci-kicker">CI PROJECT · THIS SITE</span></span>
      <h3>Micro-Market Vending, Relocated</h3>
      <p>A dedicated self-serve micro-market near the main entry — separate from the
      hallway vending — stocked for PPE consumables and quick supplies. Shorter queues
      at shift change, restock data by SKU, and hallway congestion removed from the
      7-ft corridors.</p>
    </div>
  </div>

  <ul class="notes">
    <li>Layout reproduced from the site-walk sketch; the 7-ft hallway widths and 2-ft
    cubby depth are as noted on site. Overall dimensions are approximate.</li>
    <li>Orange elements are existing features (coverall rack, drying rails, boot
    cubbies). Navy dashed zones are proposed innovations.</li>
    <li>Yellow / pink coding follows the original plan's two hallway units.</li>
  </ul>

  <footer>CONCEPT VISUALS FOR PROPOSAL DISCUSSION · NOT FOR CONSTRUCTION</footer>
</div>
<script>
(function () {{
  var jobs = [
    {{ btn: "dl1", note: "note1", sheet: "sheet1", name: "SK-01-concept-floor-plan.png" }},
    {{ btn: "dl2", note: "note2", sheet: "sheet2", name: "SK-02-concept-isometric.png" }}
  ];
  var canSave = window.claude && window.claude.downloads;
  jobs.forEach(function (j) {{
    var btn = document.getElementById(j.btn);
    var note = document.getElementById(j.note);
    if (!canSave) {{ note.textContent = ""; return; }}
    btn.hidden = false;
    btn.addEventListener("click", function () {{
      note.textContent = "Rendering…";
      var svg = document.getElementById(j.sheet).querySelector("svg");
      var vb = svg.viewBox.baseVal;
      var xml = new XMLSerializer().serializeToString(svg);
      var url = URL.createObjectURL(new Blob([xml], {{ type: "image/svg+xml" }}));
      var img = new Image();
      img.onload = function () {{
        URL.revokeObjectURL(url);
        var scale = 3;
        var c = document.createElement("canvas");
        c.width = Math.round(vb.width * scale);
        c.height = Math.round(vb.height * scale);
        var ctx = c.getContext("2d");
        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.drawImage(img, 0, 0, c.width, c.height);
        c.toBlob(function (blob) {{
          if (!blob) {{ note.textContent = "Export failed"; return; }}
          window.claude.downloads.save({{ filename: j.name, data: blob }})
            .then(function () {{ note.textContent = "Saved ✓"; }})
            .catch(function (e) {{
              note.textContent = e && e.code === "declined" ? "" : "Save unavailable";
            }});
        }}, "image/png");
      }};
      img.onerror = function () {{ note.textContent = "Export failed"; }};
      img.src = url;
    }});
  }});
}})();
</script>
"""


def main():
    import pathlib
    here = pathlib.Path(__file__).parent
    plan = plan_svg()
    iso = iso_svg()
    (here / "floorplan.svg").write_text(plan)
    (here / "isometric.svg").write_text(iso)
    (here / "dry-facility-visuals.html").write_text(html_page(plan, iso))
    print("wrote floorplan.svg (%d KB), isometric.svg (%d KB), dry-facility-visuals.html"
          % (len(plan) // 1024, len(iso) // 1024))


if __name__ == "__main__":
    main()
