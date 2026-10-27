"""
X1 SkyRacer - two-seat X1 Racing flying car, procedural model for Blender 3.6 / 4.x
============================================================================
Run inside Blender:  Scripting workspace -> Open -> this file -> Run Script.

Design: glossy white / black two-tone with a red pinstripe, wraparound dark canopy over
two side-by-side seats, narrow pod fuselage, long-chord front (low) and rear (high) wings carrying
four thin white lift ducts, no tail fin, twin ducted pushers at the tail.

Sized to the X1 Racing rule book (x1racing.com/rule-book) and checked on every run:
  * 15.5 ft span, 18 ft length, 44 in lift-duct ID, 4 locations x coaxial pair = 8 lift fans
  * 2 forward-flight ducted fans under 36 in ID
  * 5 in tall lift ducts, bulged twin-motor pods, 8 in wheels, engine bay behind the cabin
Game-ready: metres, nose -Y (glTF +Z forward), Z up, origin on the ground; every rotor,
fan and wheel is its own object spinning on local Z; hidden COL_ proxies; camera empties.

Fuel: 200 lb propane (rule book 3.3/3.6) in three pressure vessels - one capsule tank inside each
Dornier-style sponson (low on the flanks, between the stowed ducts) plus a transverse tank behind
the firewall. The sponsons also carry the four wheels. The LTO accumulator under the engine bay is
part of the OPFPLG model (x1_opfplg_blender.py), which builds in these same coordinates. With that script
next to this one, the engine parts that show outside the bay are added to the craft (ENGINE_EXTERNALS):
the exhaust tailpipe under the fuselage, the propane lines to the pushers and the printed heat-exchanger
stator vanes behind each pusher fan.

Folding: wings + lift ducts fold on hinge empties (Hinge_*) into the 90 x 53 x 216 in hauler box;
no fin. A "Fold" animation (frame 1 = flight, frame 60 = stowed) is keyed on the hinges
and exported in the GLB. Set STOWED = True to leave the scene folded.

Outputs (folder set by OUT_DIR): X1_SkyRacer.blend, X1_SkyRacer.glb, X1_SkyRacer_UE5.fbx, X1_Livery.png
PteroSim / JSBSim / PX4 / ArduPilot files: run x1_pterosim_kit.py next to this script.
Run outside Blender (numpy + matplotlib) for preview PNGs and the rule report.
"""
import math
import os
import numpy as np

# ------------------------------------------------------------------ settings
OUT_DIR = os.path.join(os.path.expanduser("~"), "X1_SkyRacer")
OUT_NAME = "X1_SkyRacer"
STOWED = False            # True: leave the scene in the folded (hauler) pose
EXPORT_GLB = True
EXPORT_FBX_UE5 = True     # Unreal Engine 5 / PteroSim: FBX with UCX_ collision hulls
SAVE_BLEND = True
ADD_STAGE = True          # camera, sun and world colour for a quick render
ENGINE_EXTERNALS = True   # add the OPFPLG parts that show outside the bay (x1_opfplg_blender.py next to this
                          # script): exhaust tailpipe under the fuselage, vapour / liquid lines to the pushers,
                          # and the printed heat-exchanger stator vanes behind each pusher fan
OPFPLG_PRESET = "4.5L"

# ------------------------------------------------------------------ palette (sRGB)
MATS = {
    "Livery":      dict(color=None,                metal=0.10, rough=0.22),
    "Paint_White": dict(color=(0.93, 0.93, 0.94),  metal=0.10, rough=0.22),
    "Paint_Black": dict(color=(0.035, 0.035, 0.04), metal=0.20, rough=0.25),
    "Paint_Red":   dict(color=(0.78, 0.06, 0.09),  metal=0.10, rough=0.25),
    "Silver":      dict(color=(0.78, 0.79, 0.81),  metal=0.90, rough=0.25),
    "Dark_Metal":  dict(color=(0.07, 0.075, 0.08), metal=0.80, rough=0.40),
    "Glass":       dict(color=(0.02, 0.025, 0.035), metal=0.00, rough=0.03, alpha=0.45),
    "Seat":        dict(color=(0.06, 0.06, 0.065), metal=0.00, rough=0.70),
    "Intake":      dict(color=(0.02, 0.02, 0.02),  metal=0.20, rough=0.60),
    "Tank":        dict(color=(0.70, 0.72, 0.75),  metal=0.85, rough=0.35),
    "Battery":     dict(color=(0.10, 0.25, 0.55),  metal=0.30, rough=0.50),
    # OPFPLG externals (colours from x1_opfplg_blender.py)
    "Exhaust_Pipe":   dict(color=(0.62, 0.30, 0.16), metal=0.90, rough=0.40),
    "Propane_Vapour": dict(color=(0.98, 0.78, 0.10), metal=0.30, rough=0.40),
    "Propane_Liquid": dict(color=(0.20, 0.75, 0.35), metal=0.30, rough=0.40),
    "Printed_HX":     dict(color=(0.58, 0.60, 0.64), metal=0.70, rough=0.60),
}

# ------------------------------------------------------------------ livery layout
LIV_S, LIV_H = 5.6, 0.95         # metres covered by the texture (length, height)
Y0, Z0 = -2.80, 0.25             # world y / z at texture u=0 / v=0
STRIPE_W = 0.022                 # red pinstripe width (m)


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def waist(s):
    """Height (m above Z0) of the black/white split at distance s from the nose:
    black nose up to the canopy, dips under the cabin, sweeps up to black rear flanks."""
    return 0.48 - 0.16 * _ss(0.4, 2.2, s) + 0.42 * _ss(3.0, 5.0, s)


def make_livery(W=4096, H=640, seed=7):
    rng = np.random.default_rng(seed)
    s = (np.arange(W) + 0.5) / W * LIV_S
    h = (np.arange(H) + 0.5) / H * LIV_H
    ss, hh = np.meshgrid(s, h)                       # row 0 = bottom (v = 0)
    white = np.array(MATS["Paint_White"]["color"])
    black = np.array(MATS["Paint_Black"]["color"])
    red = np.array(MATS["Paint_Red"]["color"])
    img = np.empty((H, W, 3))
    img[:] = white
    w = waist(ss)
    img[hh < w] = black
    img[(hh >= w) & (hh < w + STRIPE_W)] = red
    # faint panel shut-lines
    lines = (np.abs(((ss + 0.2) % 0.9) - 0.45) > 0.447)
    img[lines] *= 0.90
    img *= 1 + 0.006 * rng.standard_normal((H, W, 1))
    img = np.clip(img, 0, 1)
    return np.concatenate([img, np.ones((H, W, 1))], axis=2).astype(np.float32)


def body_uv(v):
    return ((v[1] - Y0) / LIV_S, (v[2] - Z0) / LIV_H)


# ------------------------------------------------------------------ math helpers
def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_xyz(e):
    return rot_z(e[2]) @ rot_y(e[1]) @ rot_x(e[0])


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def basis(d):
    d = unit(d)
    a = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0, 0])
    u = unit(np.cross(d, a))
    return u, np.cross(d, u)


# ------------------------------------------------------------------ mesh builders -> (verts, faces)
def grid_faces(nr, nc, wrap_r, wrap_c):
    F = []
    for i in range(nr if wrap_r else nr - 1):
        for j in range(nc if wrap_c else nc - 1):
            i2, j2 = (i + 1) % nr, (j + 1) % nc
            F.append((i * nc + j, i * nc + j2, i2 * nc + j2, i2 * nc + j))
    return F


def loft(rings, wrap=True, start=None, end=None):
    rings = [np.asarray(r, float) for r in rings]
    nr, nc = len(rings), len(rings[0])
    V = list(np.vstack(rings))
    F = grid_faces(nr, nc, False, wrap)
    span = nc if wrap else nc - 1
    if start is not None:
        ci = len(V)
        V.append(rings[0].mean(0) if isinstance(start, str) else np.asarray(start, float))
        F += [(ci, (j + 1) % nc, j) for j in range(span)]
    if end is not None:
        ci = len(V)
        V.append(rings[-1].mean(0) if isinstance(end, str) else np.asarray(end, float))
        base = (nr - 1) * nc
        F += [(ci, base + j, base + (j + 1) % nc) for j in range(span)]
    return V, F


def lathe(profile, segs=48, closed=True):
    V = []
    for r, z in profile:
        for j in range(segs):
            a = 2 * math.pi * j / segs
            V.append(np.array([r * math.cos(a), r * math.sin(a), z]))
    return V, grid_faces(len(profile), segs, closed, True)


def cylinder(p0, p1, r, segs=16):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    u, v = basis(p1 - p0)
    ring = [r * (math.cos(2 * math.pi * j / segs) * u + math.sin(2 * math.pi * j / segs) * v) for j in range(segs)]
    return loft([[p0 + q for q in ring], [p1 + q for q in ring]], start="c", end="c")


def box(c, size, R=None):
    R = np.eye(3) if R is None else R
    c, h = np.asarray(c, float), np.asarray(size, float) / 2
    V = [c + R @ (h * np.array([sx, sy, sz])) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    F = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return V, F


def prism(poly, offset):
    poly = [np.asarray(p, float) for p in poly]
    n = len(poly)
    V = poly + [p + np.asarray(offset, float) for p in poly]
    F = [tuple(range(n)), tuple(n + i for i in reversed(range(n)))]
    F += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return V, F


def sweep(path, r, segs=10):
    path = [np.asarray(p, float) for p in path]
    rings = []
    for i, p in enumerate(path):
        t = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        u, v = basis(t)
        rings.append([p + r * (math.cos(2 * math.pi * j / segs) * u + math.sin(2 * math.pi * j / segs) * v)
                      for j in range(segs)])
    return loft(rings, start="c", end="c")


def rounded_rect(r0, r1, z0, z1, c, n=4, outer_z=()):
    """Closed (r, z) profile, CCW; outer_z adds cuts on the outer wall for colour bands."""
    pts = []

    def arc(cr, cz, a0, a1):
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cr + c * math.cos(a), cz + c * math.sin(a)))

    arc(r1 - c, z0 + c, -90, 0)
    pts += [(r1, z) for z in sorted(outer_z) if z0 + c < z < z1 - c]
    arc(r1 - c, z1 - c, 0, 90)
    arc(r0 + c, z1 - c, 90, 180)
    arc(r0 + c, z0 + c, 180, 270)
    return pts


def catmull_rom(K, per=6):
    K = np.asarray(K, float)
    m, out = len(K), []
    for i in range(m - 1):
        p0, p1, p2, p3 = K[max(i - 1, 0)], K[i], K[i + 1], K[min(i + 2, m - 1)]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(K[-1])
    return out


# ------------------------------------------------------------------ parts
def swap_side(name):
    if name and name.endswith("_L"):
        return name[:-2] + "_R"
    return name


HINGES = {}   # name -> dict(loc=rest world position, parent=hinge name or None, angle=stowed Y rotation)


class Part:
    def __init__(self, name, mats, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, split=40,
                 bevel=0.0, coll="main"):
        self.name, self.mats = name, list(mats)
        self.loc, self.rot = np.array(loc, float), tuple(rot)
        self.V, self.F, self.M, self.UV = [], [], [], None
        self.parent = None                       # hinge empty this part folds with
        self.smooth, self.split, self.bevel, self.coll = smooth, split, bevel, coll

    def add(self, VF, mat=0, uv=None):
        V, F = VF
        o = len(self.V)
        if uv is not None and self.UV is None:
            self.UV = [(0.0, 0.0)] * o
        self.V += [np.asarray(v, float) for v in V]
        self.F += [tuple(i + o for i in f) for f in F]
        if isinstance(mat, (list, tuple)):
            self.M += list(mat)
        elif callable(mat):
            self.M += [mat(np.mean([np.asarray(V[i], float) for i in f], 0)) for f in F]
        else:
            self.M += [mat] * len(F)
        if self.UV is not None:
            self.UV += [uv(np.asarray(v, float)) if uv else (0.0, 0.0) for v in V]
        return self

    def mirrored(self, name):
        p = Part(name, self.mats, self.loc * [-1, 1, 1], self.rot, self.smooth, self.split, self.bevel, self.coll)
        p.V = [v * [-1, 1, 1] for v in self.V]
        p.F, p.M = list(self.F), list(self.M)
        p.UV = None if self.UV is None else list(self.UV)
        p.parent = swap_side(self.parent)
        for attr in ("duct_id", "tank_l"):
            if hasattr(self, attr):
                setattr(p, attr, getattr(self, attr))
        return p


def band_mat(bands):
    """bands: list of (z_min, mat_index) sorted ascending; applied to outer-wall faces."""
    def f(c, r_mid, inner_mat, edge_mat):
        r = math.hypot(c[0], c[1])
        if r < r_mid:
            return inner_mat
        idx = edge_mat
        for zmin, m in bands:
            if c[2] >= zmin:
                idx = m
        return idx
    return f




# ------------------------------------------------------------------ X1 Racing rule book limits (x1racing.com/rule-book)
IN = 0.0254
RULES = {
    "span_max": 15.5 * 12 * IN,        # 3.2 overall span tip-to-tip, flight config  (4.724 m)
    "length_max": 18 * 12 * IN,        # 3.2 length                                  (5.486 m)
    "height_max": 9.2 * 12 * IN,       # 3.2 height, flight config                   (2.804 m)
    "folded_height_max": 53 * IN,      # 3.2 height, folded/transport                (1.346 m)
    "folded_width_max": 90 * IN,       # 3.2 width, folded/transport                 (2.286 m)
    "lift_duct_id_max": 44 * IN,       # 3.6.4 lift duct inner diameter              (1.118 m)
    "fwd_duct_id_max": 36 * IN,        # 3.6.4 forward-flight duct inner diameter    (0.914 m)
}

NOSE_Y, TAIL_Y = -RULES["length_max"] / 2 + 0.002, RULES["length_max"] / 2 - 0.002

# lift ducts: thin stationary white rings, 44 in bore, 5 in tall, coaxial pair inside
DUCT_R0 = RULES["lift_duct_id_max"] / 2 - 0.0005    # bore
DUCT_R1 = DUCT_R0 + 0.080                           # outer skin: fat, rounded, tube-like ring
DUCT_H = 5 * IN                                     # ring height
DUCT_CORNER = 0.040                                 # rounded, tube-like lips
DUCT_ZF, DUCT_ZR = 0.48, 1.12                       # front ducts low (chin), rear ducts high (spine)
DUCT_X = RULES["span_max"] / 2 - DUCT_R1 - 0.002    # outboard edges on the span limit
DUCT_YF, DUCT_YR = -1.50, 1.20                      # front / rear lift locations
LIFT_TIP_R = DUCT_R0 - 0.010                        # blade tips: 10 mm gap (teams' choice)
ROTOR_DZ = 0.035                                    # rotor planes above / below the mid plane
BLADES_UPPER, BLADES_LOWER = 13, 17                 # coprime counts for the coaxial pair

# forward-flight ducted pushers at the tail
FWD_R0, FWD_R1, FWD_HL = 0.33, 0.40, 0.25          # 26 in bore
FWD_C = (0.45, TAIL_Y - 0.47, 0.90)            # on the raised tail (no fin)

# fuel (rule book: propane only for racing, 200 lb max onboard, single or multiple tanks)
PROPANE_LB = 200
PROPANE_KG_PER_L = 0.508                            # liquid propane at ~15 C
FILL_MAX = 0.80                                     # pressure vessels filled to 80 % of water capacity
TANK_WALL = 0.006                                   # shell thickness used for internal volume
SP_Y0, SP_Y1 = -0.82, 0.52                          # sponson ends: clear of the stowed front/rear ducts
SP_XC, SP_ZC = 0.86, 0.40                           # sponson/tank centreline
SP_A, SP_B = 0.19, 0.175                            # sponson fairing half-width / half-height
SP_TANK_R, SP_TANK_L = 0.150, 0.92                  # sponson capsule tank: radius, straight length
TX_TANK_R, TX_TANK_L = 0.175, 1.16                  # transverse tank behind the firewall
ACC_KWH = 7.5                                       # LTO pack in the OPFPLG model (rule book limit 10 kWh nominal)

# cabin / engine bay
SEAT_X, SEAT_Y = 0.32, -0.95                        # seat cushion centre (driver on the left, +X)


def capsule(r, l_straight, n_cap=6, segs=28):
    """Pressure-vessel capsule along local Z: hemispherical heads + straight shell."""
    zs = []
    for i in range(1, n_cap + 1):                                 # bottom head
        a = -math.pi / 2 + (math.pi / 2) * i / n_cap
        zs.append((r * math.cos(a), -l_straight / 2 + r * math.sin(a)))
    zs.append((r, l_straight / 2))
    for i in range(1, n_cap):                                     # top head
        a = (math.pi / 2) * i / n_cap
        zs.append((r * math.cos(a), l_straight / 2 + r * math.sin(a)))
    rings = [[(rr * math.cos(t), rr * math.sin(t), z) for t in np.linspace(0, 2 * math.pi, segs, endpoint=False)]
             for rr, z in zs]
    return loft(rings, start=(0, 0, -l_straight / 2 - r), end=(0, 0, l_straight / 2 + r))


def capsule_litres(r, l_straight):
    ri = r - TANK_WALL
    return (math.pi * ri ** 2 * l_straight + 4 / 3 * math.pi * ri ** 3) * 1000


def lift_duct_part(name, loc):
    """Stationary ring + three stator struts + motor pod bulged above and below."""
    p = Part(name, ["Paint_White", "Silver", "Dark_Metal"], loc, split=60)
    p.duct_id = 2 * DUCT_R0
    ring = rounded_rect(DUCT_R0, DUCT_R1, -DUCT_H / 2, DUCT_H / 2, DUCT_CORNER, n=5)
    mid = (DUCT_R0 + DUCT_R1) / 2
    p.add(lathe(ring, 96), mat=lambda c: 1 if math.hypot(c[0], c[1]) < mid - 0.005 else 0)
    prof = [(0.05, 0.145), (0.095, 0.13), (0.125, 0.10), (0.142, 0.06), (0.146, 0.0),
            (0.142, -0.06), (0.125, -0.10), (0.095, -0.13), (0.05, -0.145)]
    rings = [[(r * math.cos(a), r * math.sin(a), z) for a in np.linspace(0, 2 * math.pi, 32, endpoint=False)]
             for r, z in prof]
    p.add(loft(rings, start=(0, 0, 0.15), end=(0, 0, -0.15)), mat=0)            # motor pod
    for k in range(3):                                                         # stator struts
        a = math.pi / 2 + k * 2 * math.pi / 3
        p.add(box(rot_z(a) @ np.array([(0.13 + DUCT_R0 + 0.006) / 2, 0, 0]),
                  (DUCT_R0 + 0.006 - 0.13, 0.035, 0.02), rot_z(a)), mat=2)
    return p


def lift_rotor_part(name, loc, n, upper=True, hand=1):
    """One rotor of the coaxial pair: hub ring around the motor pod + n blades.
    hand = +1 / -1 sets which way the blades are pitched, so each fan pushes air down for its own spin."""
    p = Part(name, ["Dark_Metal", "Silver"], loc, split=50)
    sgn = 1 if upper else -1
    z = sgn * ROTOR_DZ
    p.add(lathe(rounded_rect(0.150, 0.185, z - 0.018, z + 0.018, 0.006, n=2), 40), mat=1)
    chord, r_root = 0.07, 0.175
    x_end = math.sqrt(LIFT_TIP_R ** 2 - (chord / 2) ** 2)          # tip corners stay inside LIFT_TIP_R
    L = x_end - r_root
    for k in range(n):
        a = 2 * math.pi * k / n
        p.add(box(rot_z(a) @ np.array([r_root + L / 2, 0, z]), (L, chord, 0.006),
                  rot_z(a) @ rot_x(math.radians(hand * sgn * 18))), mat=0)
    return p


def rotor_part(name, loc, n=7, radius=0.66, twist=22, z=0.03, rot=(0, 0, 0)):
    """Simple bladed fan (used for the pushers). Blade corners stay inside `radius`."""
    p = Part(name, ["Dark_Metal", "Silver"], loc, rot, split=30)
    p.add(cylinder((0, 0, z - 0.03), (0, 0, z + 0.03), 0.10, 20), mat=0)
    p.add(cylinder((0, 0, z + 0.03), (0, 0, z + 0.06), 0.055, 16), mat=1)
    chord = 0.10
    L = math.sqrt(radius ** 2 - (chord / 2) ** 2) - 0.10 - 0.001
    for k in range(n):
        a = 2 * math.pi * k / n
        p.add(box(rot_z(a) @ np.array([0.10 + L / 2, 0, z]), (L, chord, 0.014),
                  rot_z(a) @ rot_x(math.radians(twist))), mat=0)
    return p


def opfplg_external_parts():
    """The OPFPLG parts that sit outside the engine bay, as Parts in this model's frame, or [] if
    x1_opfplg_blender.py is not next to this script. Both scripts use the same coordinates."""
    if not ENGINE_EXTERNALS:
        return []
    import importlib
    import sys
    here = []
    if "__file__" in globals():
        here.append(os.path.dirname(os.path.abspath(__file__)))
    try:
        import bpy                                                   # in Blender: the .blend's folder
        if bpy.data.filepath:
            here.append(os.path.dirname(bpy.data.filepath))
    except ImportError:
        pass
    here.append(OUT_DIR)
    here.append(os.path.join(os.path.expanduser("~"), "X1_Racer"))
    for h in here:
        if h and h not in sys.path:
            sys.path.append(h)
    try:
        opf = importlib.import_module("x1_opfplg_blender")
    except ImportError:
        print("x1_opfplg_blender.py not found: building without the engine externals")
        return []
    _, objs = opf.build(OPFPLG_PRESET)
    out = []
    for o in objs:
        if o.coll not in ("OPFPLG_External", "OPFPLG_Radiators"):
            continue
        mats = sorted(set(o.mesh.m))
        p = Part(o.name, mats, smooth=True, split=40)
        org = np.asarray(o.origin, float)
        p.V = [np.asarray(v, float) + org for v in o.mesh.v]
        p.F = [tuple(f) for f in o.mesh.f]
        p.M = [mats.index(m) for m in o.mesh.m]
        p.opfplg = o.coll
        out.append(p)
    return out


BODY_X = None


def build_parts():
    parts, empties = [], {}
    engine_ext = opfplg_external_parts()

    # ---- fuselage: bullet nose, low cockpit sills under a big canopy, white spine rising to the
    #      tail, underside sweeping up to a raised tail boom. Teardrop-ish cross-section.
    keys = [  # y, half-width, top z, bottom z, crown exponent, belly exponent
        [NOSE_Y, 0.05, 0.64, 0.56, 2.2, 2.2],
        [-2.50, 0.34, 0.74, 0.40, 2.2, 2.2],
        [-2.00, 0.56, 0.82, 0.32, 2.3, 2.4],
        [-1.30, 0.68, 0.88, 0.30, 2.4, 2.6],
        [-0.50, 0.72, 0.90, 0.32, 2.4, 2.6],
        [0.40, 0.68, 1.06, 0.38, 2.4, 2.6],
        [1.20, 0.56, 1.12, 0.50, 2.3, 2.4],
        [1.90, 0.38, 1.10, 0.66, 2.2, 2.2],
        [TAIL_Y, 0.18, 1.04, 0.82, 2.2, 2.2]]
    samples = catmull_rom(keys, 7)
    sy = np.array([q[0] for q in samples])
    col = lambda i: [q[i] for q in samples]
    half_w = lambda y: float(np.interp(y, sy, col(1)))
    bot_z = lambda y: float(np.interp(y, sy, col(3)))

    def body_z(x, y):
        hw, top, bot, n = (float(np.interp(y, sy, col(i))) for i in (1, 2, 3, 4))
        if abs(x) >= hw:
            return (top + bot) / 2
        return (top + bot) / 2 + (top - bot) / 2 * (1 - (abs(x) / hw) ** n) ** (1 / n)

    def body_x(y, z):
        """Half-width of the body at height z."""
        hw, top, bot, nt, nbt = (float(np.interp(y, sy, col(i))) for i in (1, 2, 3, 4, 5))
        zc, hh = (top + bot) / 2, (top - bot) / 2
        q = (z - zc) / hh
        if abs(q) >= 1:
            return 0.0
        n = nt if q >= 0 else nbt
        return hw * (1 - abs(q) ** n) ** (1 / n)

    global BODY_X                           # skin half-width, exposed for checks (e.g. wing roots meeting the skin)
    _cols = [list(col(i)) for i in range(6)]

    def _body_x_frozen(y, z, _sy=sy.copy(), _c=_cols):
        hw, top, bot, nt, nbt = (float(np.interp(y, _sy, _c[i])) for i in (1, 2, 3, 4, 5))
        zc, hh = (top + bot) / 2, (top - bot) / 2
        q = (z - zc) / hh
        if abs(q) >= 1:
            return 0.0
        n = nt if q >= 0 else nbt
        return hw * (1 - abs(q) ** n) ** (1 / n)
    BODY_X = _body_x_frozen
    rings, nc = [], 48
    for y, hw, top, bot, ntop, nbot in samples:
        zc, hh = (top + bot) / 2, (top - bot) / 2
        ring = []
        for j in range(nc):
            t = 2 * math.pi * j / nc
            c, s = math.cos(t), math.sin(t)
            n = ntop if s >= 0 else nbot
            ring.append((hw * math.copysign(abs(c) ** (2 / n), c), y,
                         zc + hh * math.copysign(abs(s) ** (2 / n), s)))
        rings.append(ring)
    body = Part("Body", ["Livery"], split=60)
    body.add(loft(rings, start=(0, NOSE_Y, 0.60), end="c"), uv=body_uv)
    parts.append(body)

    # ---- canopy: dark glass helmet-visor sitting on the sills, starting just behind the nose tip,
    #      peaking over the seats, diving into the spine behind the firewall
    y_f, y_p, y_e, peak, w_max = -2.42, -0.80, 0.55, 1.27, 0.62

    def crown_w(y):
        bt = body_z(0, y)
        if y <= y_p:
            u = max((y - y_f) / (y_p - y_f), 0.02)
            return bt + (peak - bt) * math.sin(math.pi / 2 * u) ** 0.8, w_max * u ** 0.45
        u = min((y - y_p) / (y_e - y_p), 0.98)
        return bt + (peak - bt) * math.cos(math.pi / 2 * u) ** 1.5, w_max * (1 - u ** 2.2) ** 0.5

    crings = []
    for y in np.linspace(y_f + 0.01, y_e - 0.01, 40):
        crown, w = crown_w(y)
        sill = body_z(w, y) - 0.015
        crings.append([(w * math.copysign(abs(math.cos(a)) ** (2 / 2.4), math.cos(a)), y,
                        sill + (crown - sill) * abs(math.sin(a)) ** (2 / 2.4))
                       for a in np.linspace(0, math.pi, 26)])
    canopy = Part("Canopy", ["Glass"])
    canopy.add(loft(crings, wrap=False, start=(0, y_f, body_z(0, y_f)), end=(0, y_e, body_z(0, y_e))))
    parts.append(canopy)
    frame = Part("Canopy_Frame", ["Paint_Black"])
    for side in (1, -1):                                          # black sills along the glass edge
        frame.add(sweep([(side * crown_w(y)[1], y, body_z(crown_w(y)[1], y) - 0.005)
                         for y in np.linspace(y_f + 0.15, y_e - 0.10, 22)], 0.022, 8))
    yb = -0.10                                                    # B-pillar hoop behind the seats
    cr, wb = crown_w(yb)
    sill_b = body_z(wb, yb)
    frame.add(sweep([(wb * math.cos(a), yb, sill_b + (cr - sill_b) * math.sin(a) + 0.004)
                     for a in np.linspace(0.05, math.pi - 0.05, 18)], 0.022, 8))
    parts.append(frame)

    # ---- two side-by-side bare-frame seats (3.1/3.4)
    seat = Part("Seat_L", ["Seat"], smooth=False)
    seat.add(box((SEAT_X, SEAT_Y, 0.42), (0.44, 0.50, 0.07)))
    seat.add(box((SEAT_X, SEAT_Y + 0.33, 0.70), (0.44, 0.08, 0.52), rot_x(math.radians(-18))))
    seat.add(box((SEAT_X, SEAT_Y + 0.42, 1.00), (0.20, 0.08, 0.12), rot_x(math.radians(-18))))
    parts += [seat, seat.mirrored("Seat_R")]

    # ---- engine bay under the raised spine, firewall to the pushers
    BAY_Y0, BAY_Y1 = SEAT_Y + 0.62, FWD_C[1] - FWD_HL - 0.05
    firewall = Part("Firewall", ["Dark_Metal"], smooth=False)
    firewall.add(box((0, BAY_Y0, 0.66), (0.90, 0.03, 0.56)))
    parts.append(firewall)
    # transverse propane tank right behind the firewall
    TX_Y = BAY_Y0 + 0.03 + TX_TANK_R + 0.02
    txt = Part("Tank_Transverse", ["Tank"], (0, TX_Y, 0.56), (0, math.pi / 2, 0), split=50)
    txt.add(capsule(TX_TANK_R, TX_TANK_L - 2 * TX_TANK_R))
    txt.tank_l = capsule_litres(TX_TANK_R, TX_TANK_L - 2 * TX_TANK_R)
    parts.append(txt)
    ACC_Y0 = TX_Y + TX_TANK_R + 0.05
    # The accumulator is no longer modelled here: the OPFPLG model carries the LTO pack
    # (162 x Toshiba SCiB 20 Ah, 7.5 kWh, 770 x 668 x 134 mm case on the belly floor under the bay).
    ENG_Y0 = ACC_Y0 + 0.02
    engine = Part("Engine_Placeholder", ["Dark_Metal", "Silver"], smooth=False)
    engine.add(box((0, (ENG_Y0 + 1.50) / 2, 0.78), (1.00, 1.50 - ENG_Y0, 0.46)), mat=0)
    for x in (-0.24, 0.24):
        engine.add(cylinder((x, ENG_Y0 + 0.05, 0.92), (x, 1.40, 0.92), 0.13, 16), mat=1)
    parts.append(engine)
    louvres = Part("Engine_Louvres", ["Paint_Black"], smooth=False)
    for y in np.arange(0.70, 1.60, 0.085):
        louvres.add(box((0, y, body_z(0, y) + 0.010), (0.40, 0.05, 0.010), rot_x(math.radians(-28))))
    parts.append(louvres)
    empties["Engine_Bay"] = (0.0, (ENG_Y0 + 1.50) / 2, 0.78)
    # side intake blocks outboard of the engine bay removed (Oct 2026)

    # ---- duct mounts: low front arms off the chin, high rear wing off the upper fuselage,
    #      white flank swoosh tying the two together
    ring_in = DUCT_X - DUCT_R1                                    # inboard edge of the ducts
    def airfoil(c_len, tr=0.09, m=0.03, pm=0.40, n=14):
        """Closed cambered NACA-style section, chord along +Y from 0 (LE) to c_len: [(dy, dz)]."""
        th = np.linspace(0, math.pi, n)
        cs = 0.5 * (1 - np.cos(th))
        yt = 5 * tr * (0.2969 * np.sqrt(cs) - 0.126 * cs - 0.3516 * cs ** 2 + 0.2843 * cs ** 3 - 0.1036 * cs ** 4)
        yc = np.where(cs < pm, m / pm ** 2 * (2 * pm * cs - cs ** 2),
                      m / (1 - pm) ** 2 * ((1 - 2 * pm) + 2 * pm * cs - cs ** 2))
        upper = [(c * c_len, (z + t) * c_len) for c, z, t in zip(cs, yc, yt)]
        lower = [(c * c_len, (z - t) * c_len) for c, z, t in zip(cs, yc, yt)]
        return upper[::-1] + lower[1:-1]                          # TE -> LE (top) -> TE (bottom)

    def wing_tip_x(y, yc):
        ry = min(abs(y - yc), DUCT_R1 - 1e-3)
        return DUCT_X - math.sqrt(DUCT_R1 ** 2 - ry ** 2) + 0.03          # into the ring wall

    WING_EMBED = 0.005                                            # wing roots end 5 mm inside the skin

    def duct_wing(name, yc, zc, root_x, chord_root, chord_tip, tr, x_from, x_to=None, n=10, trim=False):
        """Wing segment from x_from to x_to (None = out to the ring, tip following its inboard curve).
        trim=True: the inboard end follows the fuselage skin instead of running on inside the body."""
        w = Part(name, ["Paint_White"], split=50)
        sec = airfoil(1.0, tr)
        span = (DUCT_X - DUCT_R1) - root_x
        rings_w = []
        for s_ in np.linspace(0, 1, n):
            ring_pts = []
            xm = x_from + ((x_to if x_to is not None else DUCT_X - DUCT_R1) - x_from) * s_
            ch = chord_root + (chord_tip - chord_root) * min(1.0, (xm - root_x) / span)
            for dy, dz in sec:
                y, z = yc - ch / 2 + dy * ch, zc + dz * ch
                b_ = x_to if x_to is not None else wing_tip_x(y, yc)
                a_ = x_from
                if trim:                                          # start at the skin, never inside the body
                    a_ = max(x_from, body_x(y, z) - WING_EMBED)
                    b_ = max(b_, a_)
                ring_pts.append((a_ + (b_ - a_) * s_, y, z))
            rings_w.append(ring_pts)
        w.add(loft(rings_w, start="c", end="c"))
        return w

    # ---- fold kinematics. Each side: wing hinge (axis along Y) + duct hinge at the wing/ring joint.
    #      Front: wing folds DOWN, duct stands on edge beside the nose (bottom just off the ground).
    #      Rear:  wing folds UP,   duct hangs on edge beside the engine bay (top under 53 in).
    HINGES.clear()
    ring_in = DUCT_X - DUCT_R1
    FW_HX, RW_HX = 0.64, 0.87                                     # wing hinge lines (fixed stubs inboard)
    zt_f = RULES["folded_height_max"] - 2 * DUCT_R1 - 0.003       # front duct hinge height when stowed
    beta = math.asin((DUCT_ZF - zt_f) / (ring_in - FW_HX))
    zt_r = RULES["folded_height_max"] - 0.025                     # rear duct hinge height when stowed
    alpha = math.asin((zt_r - DUCT_ZR) / (ring_in - RW_HX))
    for side, sgn in (("L", 1), ("R", -1)):
        HINGES[f"Hinge_FrontWing_{side}"] = dict(loc=np.array([sgn * FW_HX, DUCT_YF, DUCT_ZF]), parent=None,
                                                 angle=sgn * beta)
        HINGES[f"Hinge_FrontDuct_{side}"] = dict(loc=np.array([sgn * ring_in, DUCT_YF, DUCT_ZF]),
                                                 parent=f"Hinge_FrontWing_{side}", angle=-sgn * (math.pi / 2 + beta))
        HINGES[f"Hinge_RearWing_{side}"] = dict(loc=np.array([sgn * RW_HX, DUCT_YR, DUCT_ZR]), parent=None,
                                                angle=-sgn * alpha)
        HINGES[f"Hinge_RearDuct_{side}"] = dict(loc=np.array([sgn * ring_in, DUCT_YR, DUCT_ZR]),
                                                parent=f"Hinge_RearWing_{side}", angle=sgn * (math.pi / 2 + alpha))

    # front wing: low, off the chin/lower flanks - whole exposed wing folds at the body side
    # trimmed where they enter the fuselage: the root stub fills from the skin out to the fold line, and the
    # folding panel starts at the fold line or the skin, whichever is further out
    fs = duct_wing("Front_Wing_Root_L", DUCT_YF, DUCT_ZF, 0.30, 1.05, 0.95, 0.09, 0.30, FW_HX, n=4, trim=True)
    fp = duct_wing("Front_Wing_L", DUCT_YF, DUCT_ZF, 0.30, 1.05, 0.95, 0.09, FW_HX, ring_in, n=6, trim=True)
    fp.parent = "Hinge_FrontWing_L"
    ff = duct_wing("Front_Wing_Fillet_L", DUCT_YF, DUCT_ZF, 0.30, 1.05, 0.95, 0.09, ring_in, n=4)
    ff.parent = "Hinge_FrontDuct_L"                               # curved tip blends into the ring, folds with it
    # rear wing: high, off the upper rear fuselage - fixed stub, outer panel folds
    rs = duct_wing("Rear_Wing_Stub_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, 0.09, 0.15, RW_HX, n=8)
    rp = duct_wing("Rear_Wing_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, 0.09, RW_HX, ring_in, n=4)
    rp.parent = "Hinge_RearWing_L"
    rf = duct_wing("Rear_Wing_Fillet_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, 0.09, ring_in, n=4)
    rf.parent = "Hinge_RearDuct_L"
    for w in (fs, fp, ff, rs, rp, rf):
        parts += [w, w.mirrored(w.name[:-1] + "R")]
    swoosh = Part("Flank_Swoosh_L", ["Paint_White"], split=60)
    path = []
    for t in np.linspace(0, 1, 26):
        y = (DUCT_YF + 0.10) + (DUCT_YR - 0.30 - DUCT_YF - 0.10) * t
        z = DUCT_ZF + (DUCT_ZR - 0.02 - DUCT_ZF) * (t * t * (3 - 2 * t))
        path.append((max(body_x(y, z), 0.12) + 0.01, y, z))
    swoosh.add(sweep(path, 0.045, 12))
    parts += [swoosh, swoosh.mirrored("Flank_Swoosh_R")]

    # ---- 4 lift locations x coaxial counter-rotating pair = 8 lift fans (3.6)
    for key, yc, zc in (("F", DUCT_YF, DUCT_ZF), ("R", DUCT_YR, DUCT_ZR)):
        C = np.array([DUCT_X, yc, zc])
        d = lift_duct_part(f"Duct_{key}L", C)
        # the rear pair spins opposite to the front pair (diagonal torque balance), so its blades are
        # pitched the other way; the right side is a mirror image, which flips pitch and spin together
        hand = 1 if key == "F" else -1
        up = lift_rotor_part(f"Rotor_{key}L_Upper", C, BLADES_UPPER, True, hand)
        lo = lift_rotor_part(f"Rotor_{key}L_Lower", C, BLADES_LOWER, False, hand)
        for p in (d, up, lo):
            p.parent = "Hinge_FrontDuct_L" if key == "F" else "Hinge_RearDuct_L"
            parts.append(p)
            parts.append(p.mirrored(p.name.replace("L_", "R_") if "L_" in p.name else p.name[:-1] + "R"))

    # ---- twin ducted pushers (forward flight, 3.6.2) on the raised tail
    trot = (-math.pi / 2, 0, 0)
    th = Part("Thruster_L", ["Paint_White", "Paint_Red", "Paint_Black", "Dark_Metal"], FWD_C, trot, split=60)
    th.duct_id = 2 * FWD_R0
    prof = rounded_rect(FWD_R0, FWD_R1, -FWD_HL, FWD_HL, 0.03, n=4, outer_z=(-0.17, -0.14, 0.10))
    pick = band_mat([(-0.17, 1), (-0.14, 0), (0.10, 2)])
    th.add(lathe(prof, 48), mat=lambda c: pick(c, (FWD_R0 + FWD_R1) / 2 + 0.01, 3, 0))
    th.add(cylinder((0, 0, 0.0), (0, 0, 0.22), 0.11, 20), mat=3)
    if not engine_ext:                      # the OPFPLG heat-exchanger vanes are the stators when present
        for k in range(3):
            a = math.pi / 2 + k * 2 * math.pi / 3
            th.add(box(rot_z(a) @ np.array([0.22, 0, 0.10]), (0.23, 0.025, 0.08), rot_z(a)), mat=3)
    fan = rotor_part("Thruster_Fan_L", FWD_C, n=11, radius=FWD_R0 - 0.01, twist=-30, z=-0.10, rot=trot)   # pitched for CCW seen from behind
    parts += [th, th.mirrored("Thruster_R"), fan, fan.mirrored("Thruster_Fan_R")]

    # ---- Dornier-style sponsons: low fuel-tank fairings on the flanks, wheels underneath
    sp = Part("Sponson_L", ["Livery"], split=60)
    srings = []
    for t in np.linspace(0, 1, 30):
        k = (1 - abs(2 * t - 1) ** 3.0) ** (1 / 3.0)               # blunt, rounded ends
        k = max(k, 0.04)
        y = SP_Y0 + (SP_Y1 - SP_Y0) * t
        srings.append([(SP_XC + SP_A * k * math.copysign(abs(math.cos(a)) ** (2 / 2.6), math.cos(a)), y,
                        SP_ZC + SP_B * k * math.copysign(abs(math.sin(a)) ** (2 / 2.6), math.sin(a)))
                       for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)])
    sp.add(loft(srings, start=(SP_XC, SP_Y0 - 0.01, SP_ZC), end=(SP_XC, SP_Y1 + 0.01, SP_ZC)), uv=body_uv)
    tank = Part("Tank_Sponson_L", ["Tank"], (SP_XC, (SP_Y0 + SP_Y1) / 2, SP_ZC), (-math.pi / 2, 0, 0), split=50)
    tank.add(capsule(SP_TANK_R, SP_TANK_L))
    tank.tank_l = capsule_litres(SP_TANK_R, SP_TANK_L)
    filler = Part("Fuel_Filler_L", ["Paint_Red", "Silver"], smooth=False)
    filler.add(cylinder((SP_XC + 0.03, -0.55, SP_ZC + SP_B - 0.02), (SP_XC + 0.03, -0.55, SP_ZC + SP_B + 0.005),
                        0.035, 16), mat=0)
    parts += [sp, sp.mirrored("Sponson_R"), tank, tank.mirrored("Tank_Sponson_R"),
              filler, filler.mirrored("Fuel_Filler_R")]

    # four 8 in wheels under the sponsons (each spins on local Z = craft X)
    WR, WW = 4 * IN, 2.5 * IN
    tire = rounded_rect(0.045, WR, -WW / 2, WW / 2, 0.014, n=3)
    sp_bot = SP_ZC - SP_B
    for key, wy in (("F", SP_Y0 + 0.14), ("R", SP_Y1 - 0.14)):
        wheel = Part(f"Wheel_{key}L", ["Seat", "Silver"], (SP_XC, wy, WR), (0, math.pi / 2, 0), split=50)
        wheel.add(lathe(tire, 32), mat=0)
        wheel.add(cylinder((0, 0, -WW / 2 - 0.004), (0, 0, WW / 2 + 0.004), 0.048, 16), mat=1)
        fork = Part(f"Wheel_Fork_{key}L", ["Paint_Black"], smooth=False)
        for side in (-1, 1):
            fx_ = SP_XC + side * (WW / 2 + 0.012)
            fork.add(box((fx_, wy, (WR + sp_bot + 0.03) / 2), (0.012, 0.07, sp_bot + 0.03 - WR + 0.04)))
        fork.add(box((SP_XC, wy, sp_bot + 0.005), (WW + 0.05, 0.10, 0.03)))
        for p in (wheel, fork):
            parts += [p, p.mirrored(p.name[:-1] + "R")]
    empties["Fuel_Filler_L"] = (SP_XC + 0.03, -0.55, SP_ZC + SP_B)
    empties["Fuel_Filler_R"] = (-SP_XC - 0.03, -0.55, SP_ZC + SP_B)

    # ---- collision proxies (hidden, not exported)
    parts.append(Part("COL_Body", [], smooth=False, coll="col").add(box((0, 0, 0.78), (1.5, 5.48, 1.0))))
    for sgn, side in ((1, "L"), (-1, "R")):
        parts.append(Part(f"COL_Sponson_{side}", [], smooth=False, coll="col")
                     .add(box((sgn * SP_XC, (SP_Y0 + SP_Y1) / 2, SP_ZC), (2 * SP_A, SP_Y1 - SP_Y0, 2 * SP_B))))
    for key, yc, zc in (("F", DUCT_YF, DUCT_ZF), ("R", DUCT_YR, DUCT_ZR)):
        for sgn, side in ((1, "L"), (-1, "R")):
            c = np.array([sgn * DUCT_X, yc, zc])
            col = Part(f"COL_Duct_{key}{side}", [], smooth=False, coll="col")
            col.add(cylinder(c - [0, 0, 0.15], c + [0, 0, 0.15], DUCT_R1, 10))
            col.parent = f"Hinge_{'Front' if key == 'F' else 'Rear'}Duct_{side}"
            parts.append(col)

    parts += engine_ext                     # exhaust tailpipe, external propane lines, pusher heat exchangers

    empties["Cam_Driver_Eye"] = (SEAT_X, SEAT_Y + 0.05, 1.08)
    empties["Cam_Chase"] = (0.0, 8.0, 2.4)
    return parts, empties


def hinge_chain(name):
    chain = []
    while name:
        chain.append(name)
        name = HINGES[name]["parent"]
    return chain                                                  # innermost first


def posed(p, stowed=False):
    """World-space vertices of a part, in flight or stowed pose."""
    R = euler_xyz(p.rot)
    V = np.array([R @ v + p.loc for v in p.V])
    if stowed and p.parent:
        for h in hinge_chain(p.parent):                           # rotate about each hinge (rest frame)
            c, a = HINGES[h]["loc"], HINGES[h]["angle"]
            V = (rot_y(a) @ (V - c).T).T + c
    return V


def rule_check(parts):
    """Measure the built geometry against the rule book and print a report."""
    main = [p for p in parts if p.coll == "main"]
    P = np.vstack([posed(p) for p in main])
    lo, hi = P.min(0), P.max(0)
    S = np.vstack([posed(p, True) for p in main])
    slo, shi = S.min(0), S.max(0)

    def bore(p):
        return 2 * min(math.hypot(v[0], v[1]) for v in p.V if math.hypot(v[0], v[1]) > p.duct_id / 2 - 0.02)
    lift_id = max(bore(p) for p in parts if p.name.startswith("Duct_"))
    fwd_id = max(bore(p) for p in parts if p.name in ("Thruster_L", "Thruster_R"))
    ring_z = [v[2] for p in parts if p.name.startswith("Duct_") for v in p.V
              if math.hypot(v[0], v[1]) > DUCT_R0 - 0.005]
    n_lift = sum(p.name.startswith("Rotor_") for p in parts)
    n_fwd = sum(p.name.startswith("Thruster_Fan") for p in parts)
    rows = [
        ("Span tip-to-tip", hi[0] - lo[0], RULES["span_max"]),
        ("Length", hi[1] - lo[1], RULES["length_max"]),
        ("Height (flight)", hi[2], RULES["height_max"]),
        ("Stowed width", shi[0] - slo[0], RULES["folded_width_max"]),
        ("Stowed height", shi[2] - min(slo[2], 0.0), RULES["folded_height_max"]),
        ("Stowed length", shi[1] - slo[1], RULES["length_max"]),
        ("Lift duct inner diameter", lift_id, RULES["lift_duct_id_max"]),
        ("Forward duct inner diameter", fwd_id, RULES["fwd_duct_id_max"]),
        ("Lift duct height (target 5 in)", max(ring_z) - min(ring_z), DUCT_H),
    ]
    print("X1 Racing rule check")
    for name, val, lim in rows:
        print(f"  {name:36s} {val:6.3f} m ({val / IN:6.1f} in)  limit {lim:6.3f} m ({lim / IN:6.1f} in)  "
              f"{'OK' if val <= lim + 1e-6 else 'OVER'}")
    print(f"  Lift fans: {n_lift} (4 locations x coaxial pair)  {'OK' if n_lift == 8 else 'CHECK'}")
    print(f"  Forward-flight fans: {n_fwd}  {'OK' if n_fwd == 2 else 'CHECK'}")
    print(f"  Stowed ground clearance (lowest point): {slo[2] / IN:.1f} in")
    need = PROPANE_LB * 0.4536 / PROPANE_KG_PER_L / FILL_MAX
    tanks = [(p.name, p.tank_l) for p in parts if hasattr(p, "tank_l")]
    have = sum(v for _, v in tanks)
    print(f"  Fuel: {PROPANE_LB} lb propane needs {need:.0f} L water capacity at {FILL_MAX:.0%} fill; "
          f"tanks {have:.0f} L  {'OK' if have >= need else 'SHORT'}")
    for n, v in tanks:
        print(f"    {n:18s} {v:5.1f} L")
    for h, d in HINGES.items():
        if h.endswith("_R"):
            continue
        print(f"  {h:22s} fold {math.degrees(d['angle']):+6.1f} deg")
    return rows


# ------------------------------------------------------------------ Blender side
def srgb_to_lin(c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def build_blender(parts, empties, livery):
    import bpy
    import bmesh
    from mathutils import Vector

    # clean previous run
    for cn in ("X1_SkyRacer", "X1_Collision", "X1_Stage"):
        coll = bpy.data.collections.get(cn)
        if coll:
            for o in list(coll.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(coll)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)

    scene = bpy.context.scene
    colls = {}
    for key, cn in (("main", "X1_SkyRacer"), ("col", "X1_Collision"), ("stage", "X1_Stage")):
        c = bpy.data.collections.new(cn)
        scene.collection.children.link(c)
        colls[key] = c
    os.makedirs(OUT_DIR, exist_ok=True)

    # livery image
    H, W = livery.shape[:2]
    img = bpy.data.images.get("X1_Livery")
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new("X1_Livery", W, H, alpha=False)
    img.pixels.foreach_set(livery.ravel())
    img.update()
    try:
        img.filepath_raw = os.path.join(OUT_DIR, "X1_Livery.png")
        img.file_format = "PNG"
        img.save()
    except Exception as ex:
        print("livery save skipped:", ex)
    try:
        img.pack()
    except Exception as ex:
        print("livery pack skipped:", ex)

    # materials
    mats = {}
    for name, d in MATS.items():
        m = bpy.data.materials.get("X1_" + name) or bpy.data.materials.new("X1_" + name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Metallic"].default_value = d["metal"]
        bsdf.inputs["Roughness"].default_value = d["rough"]
        if d["color"] is None:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.extension = "EXTEND"
            tex.location = (-400, 200)
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            bsdf.inputs["Base Color"].default_value = (*srgb_to_lin(d["color"]), 1)
            m.diffuse_color = (*srgb_to_lin(d["color"]), 1)
        if "alpha" in d:
            bsdf.inputs["Alpha"].default_value = d["alpha"]
            for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
                try:
                    setattr(m, attr, val)
                except Exception:
                    pass
        mats[name] = m

    root = bpy.data.objects.new("X1_SkyRacer", None)
    root.empty_display_type = "ARROWS"
    colls["main"].objects.link(root)

    export_objs = [root]
    # fold hinges: empties parented in a chain, rotating about their local Y axis
    hobj = {}
    for name in sorted(HINGES, key=lambda n: len(hinge_chain(n))):
        h = HINGES[name]
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.3
        colls["main"].objects.link(e)
        e.parent = hobj[h["parent"]] if h["parent"] else root
        e.location = tuple(h["loc"] - (HINGES[h["parent"]]["loc"] if h["parent"] else 0))
        e.rotation_euler = (0, 0, 0)
        hobj[name] = e
        export_objs.append(e)

    for p in parts:
        me = bpy.data.meshes.new(p.name)
        me.from_pydata([tuple(v) for v in p.V], [], [tuple(f) for f in p.F])
        if p.UV is not None:
            uvl = me.uv_layers.new(name="UVMap")
            vi = np.empty(len(me.loops), dtype=np.int64)
            me.loops.foreach_get("vertex_index", vi)
            uvl.data.foreach_set("uv", np.asarray(p.UV, dtype=np.float32)[vi].ravel())
        for mn in p.mats:
            me.materials.append(mats[mn])
        if p.mats:
            me.polygons.foreach_set("material_index", list(p.M))
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set("use_smooth", [p.smooth] * len(me.polygons))
        me.update()

        ob = bpy.data.objects.new(p.name, me)
        colls[p.coll].objects.link(ob)
        ob.rotation_euler = p.rot
        if p.parent:
            ob.parent = hobj[p.parent]
            ob.location = tuple(p.loc - HINGES[p.parent]["loc"])
        else:
            ob.parent = root
            ob.location = tuple(p.loc)
        if p.bevel:
            b = ob.modifiers.new("Bevel", "BEVEL")
            b.width, b.segments = p.bevel, 2
            b.limit_method = "ANGLE"
            b.angle_limit = math.radians(30)
        if p.smooth and p.coll == "main":
            es = ob.modifiers.new("EdgeSplit", "EDGE_SPLIT")
            es.split_angle = math.radians(p.split)
        if p.coll == "col":
            ob.display_type = "WIRE"
            ob.hide_render = True
        else:
            export_objs.append(ob)

    for name, loc in empties.items():
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "PLAIN_AXES"
        e.empty_display_size = 0.25
        e.location = loc
        colls["main"].objects.link(e)
        e.parent = root
        export_objs.append(e)

    if ADD_STAGE:
        cam = bpy.data.objects.new("Render_Cam", bpy.data.cameras.new("Render_Cam"))
        cam.data.lens = 45
        cam.location = (-7.2, -8.4, 4.0)
        cam.rotation_euler = (Vector((0, 0, 0.8)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        colls["stage"].objects.link(cam)
        scene.camera = cam
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sun.data.energy = 4.0
        sun.rotation_euler = (math.radians(45), 0, math.radians(-35))
        colls["stage"].objects.link(sun)
        if scene.world is None:
            scene.world = bpy.data.worlds.new("World")
        scene.world.use_nodes = True
        bg = scene.world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.55, 0.60, 0.66, 1)
            bg.inputs[1].default_value = 1.0
        # hauler stowage box (not exported): 90 in wide x 216 in long x 53 in tall
        W_, L_, H_ = RULES["folded_width_max"], RULES["length_max"], RULES["folded_height_max"]
        bxv = [(sx * W_ / 2, sy * L_ / 2, sz * H_) for sx in (-1, 1) for sy in (-1, 1) for sz in (0, 1)]
        bxm = bpy.data.meshes.new("Hauler_Box")
        bxm.from_pydata(bxv, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
        bx = bpy.data.objects.new("Hauler_Box_90x216x53in", bxm)
        bx.display_type = "WIRE"
        bx.hide_render = True
        colls["stage"].objects.link(bx)
        for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                scene.render.engine = eng
                break
            except Exception:
                pass

    # "Fold" animation: frame 1 flight -> frame 60 stowed
    scene.frame_start, scene.frame_end = 1, 60
    for name, e in hobj.items():
        e.rotation_euler = (0, 0, 0)
        e.keyframe_insert(data_path="rotation_euler", index=1, frame=1)
        e.rotation_euler = (0, HINGES[name]["angle"], 0)
        e.keyframe_insert(data_path="rotation_euler", index=1, frame=60)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    for o in colls["col"].objects:
        o.hide_set(True)

    if EXPORT_GLB:
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        for o in export_objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = root
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, OUT_NAME + ".glb"),
                                  export_format="GLB", use_selection=True, export_apply=True)
    if EXPORT_FBX_UE5:
        export_ue5_fbx(bpy, colls, export_objs, root)
    scene.frame_set(60 if STOWED else 1)
    if SAVE_BLEND:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, OUT_NAME + ".blend"))
    nfaces = sum(len(p.F) for p in parts if p.coll == "main")
    print(f"X1 SkyRacer built: {len([p for p in parts if p.coll == 'main'])} parts, ~{nfaces} faces -> {OUT_DIR}")


def export_ue5_fbx(bpy, colls, export_objs, root):
    """FBX for Unreal Engine 5 (PteroSim's renderer), flight pose.
    * Units: metres with FBX unit scaling -> 1 m = 100 UU in Unreal.
    * Axes: Blender FBX defaults (nose at -Y in Blender). If the craft imports sideways,
      set Import Rotation yaw to 90 deg in the Unreal FBX import dialog.
    * Every rotor / fan / wheel stays a separate object with its pivot on the spin axis, so it
      can be spun by name (see x1_skyracer_manifest.json for the rotor index map).
    * Collision: each COL_* proxy is copied as UCX_<MeshName>_00, Unreal's convex-collision naming.
    Import in Unreal with 'Combine Meshes' OFF (or 'Import Into Level') to keep the parts separate.
    """
    scene = bpy.context.scene
    scene.frame_set(1)
    ucx = []
    for o in list(colls["col"].objects):
        target = o.name[len("COL_"):] if o.name.startswith("COL_") else o.name
        dup = o.copy()
        dup.data = o.data.copy()
        dup.name = f"UCX_{target}_00"
        colls["main"].objects.link(dup)
        dup.hide_set(False)
        ucx.append(dup)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in list(export_objs) + ucx:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT_DIR, OUT_NAME + "_UE5.fbx"), use_selection=True,
                             object_types={"EMPTY", "MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", use_mesh_modifiers=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
                             path_mode="COPY", embed_textures=True)
    for o in ucx:
        bpy.data.objects.remove(o, do_unlink=True)


# ------------------------------------------------------------------ preview (no Blender)
def preview(parts, livery, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    H, W = livery.shape[:2]
    polys, cols = [], []
    light = unit([-0.4, -0.6, 0.8])
    for p in parts:
        if p.coll != "main":
            continue
        R = euler_xyz(p.rot)
        Vw = [R @ v + p.loc for v in p.V]
        tris = [((f[0], f[k], f[k + 1]), fi) for fi, f in enumerate(p.F) for k in range(1, len(f) - 1)]
        for f, fi in tris:
            pts = np.array([Vw[i] for i in f])
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-12 and len(pts) > 3:
                n = np.cross(pts[2] - pts[1], pts[3] - pts[1])
            nn = np.linalg.norm(n)
            n = n / nn if nn > 1e-12 else np.array([0, 0, 1.0])
            mname = p.mats[p.M[fi]]
            d = MATS[mname]
            if d["color"] is None:
                u, v = np.mean([p.UV[i] for i in f], 0)
                c = livery[int(np.clip(v, 0, 0.999) * H), int(np.clip(u, 0, 0.999) * W), :3]
            else:
                c = np.array(d["color"])
            shade = 0.45 + 0.55 * abs(float(n @ light))
            polys.append(pts)
            cols.append((*np.clip(c * shade, 0, 1), d.get("alpha", 1.0)))

    views = [("3/4 front", 20, -140), ("top", 89, -90), ("side", 0, 0), ("front", 0, -90)]
    fig = plt.figure(figsize=(18, 12))
    for i, (title, el, az) in enumerate(views):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(polys, facecolors=cols, edgecolors="none"))
        ax.set_xlim(-3.8, 3.8); ax.set_ylim(-3.8, 3.8); ax.set_zlim(-0.2, 2.2)
        ax.set_box_aspect((7.6, 7.6, 2.4))
        ax.view_init(elev=el, azim=az)
        ax.set_title(title)
        ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(out_png, dpi=90)
    print("preview ->", out_png, "faces:", len(polys))


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        IN_BLENDER = True
    except ImportError:
        IN_BLENDER = False
    PARTS, EMPTIES = build_parts()
    rule_check(PARTS)
    LIVERY = make_livery() if IN_BLENDER else make_livery(2048, 384)
    if IN_BLENDER:
        build_blender(PARTS, EMPTIES, LIVERY)
    else:
        preview(PARTS, LIVERY, "x1hs_preview.png")
        from PIL import Image
        Image.fromarray((LIVERY[::-1, :, :3] * 255).astype(np.uint8)).save("x1hs_livery_preview.png")
