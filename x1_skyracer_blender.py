"""
X1 SkyRacer - FAN-TILT BRANCH (25 deg cockpit, pushers lowered + tilted 20 deg, wings at +5 deg incidence) - procedural model for Blender 3.6 / 4.x
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

Cockpit (ergonomic rework, Oct 2026 - outside design unchanged above the wing roots):
  * two side-by-side bare-frame seats (3.4), backrest 25 deg from vertical (sports-car posture),
    H-point dropped to 17.1 in off the ground
  * belly bubbled down and out from the toes back under the whole seat into a foot well / seat tub
    (keel 7 in off the ground)
  * canopy crown raised 2.8 in to 52.7 in (stowed limit 53 in) and moved back over the heads
  * adjustable foot-rest rail; fit is checked every run for a 95th-percentile man and a
    5th-percentile woman, bare-headed (head, shoulders, torso, knees, shins, feet, firewall)
  Tune with H_Y/H_Z, SEAT_BACK_DEG, FLOOR_Z, FOOTWELL and CANOPY.

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

Outputs (folder set by OUT_DIR): X1_SkyRacer_FanTilt.blend, .glb, _UE5.fbx, X1_Livery.png (branch names)
PteroSim / JSBSim / PX4 / ArduPilot files: run x1_pterosim_kit.py next to this script.
Run outside Blender (numpy + matplotlib) for preview PNGs and the rule report.
"""
import math
import os
import numpy as np

# ------------------------------------------------------------------ settings
OUT_DIR = os.path.join(os.path.expanduser("~"), "X1_SkyRacer")
OUT_NAME = "X1_SkyRacer_FanTilt"   # branch: never overwrites the main X1_SkyRacer model
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
LIVERY_LOWER = "Paint_White"     # paint below the waist line (was "Paint_Black"); the red pinstripe stays


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def waist(s):
    """Height (m above Z0) of the waist line (red pinstripe) at distance s from the nose: high at the
    nose, dipping under the cabin, sweeping up the rear flanks. Below it: LIVERY_LOWER."""
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
    img[hh < w] = np.array(MATS[LIVERY_LOWER]["color"])
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
        if getattr(self, "park", 0.0):
            p.park = -self.park                                    # mirror image turns the other way
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
DUCT_ZF, DUCT_ZR = 0.48, 0.96                       # front ducts low (chin), rear ducts high (spine)
DUCT_X = RULES["span_max"] / 2 - DUCT_R1 - 0.002    # outboard edges on the span limit
DUCT_YF, DUCT_YR = -1.50, 1.20                      # front / rear lift locations
LIFT_TIP_R = DUCT_R0 - 0.010                        # blade tips: 10 mm gap (teams' choice)
ROTOR_DZ = 0.035                                    # rotor planes above / below the mid plane
BLADES_UPPER, BLADES_LOWER = 13, 17                 # coprime counts for the coaxial pair

# forward-flight ducted pushers at the tail
FWD_R0, FWD_R1, FWD_HL = 0.33, 0.40, 0.25          # 26 in bore (FWD_HL: original half length, layout reference)
# Pusher duct length (Oct 2026): 0.39 m instead of 0.50 m (L/D 0.59). 9 cm of inlet ahead of the fan
# (rotor at -0.10), ending 2 cm behind the heat-exchanger rings (+0.18); fan and cooling section unchanged.
FWD_Z0, FWD_Z1 = -0.19, 0.20                      # duct front / rear along the pusher axis (m from FWD_C)
# Fan and wing angles (fan-tilt branch, Oct 2026), from the trim of the fully loaded 3,500 lb craft
# (X1_SkyRacer_FanTilt/): pushers lowered 4 in and tilted so the exhaust points PUSHER_TILT_DEG below the
# body axis (thrust line tilted up). Lift ducts stay square to the body (level hover and landing); the
# wings are built at WING_INCIDENCE_DEG so they keep lifting while the body tips slightly nose-down at
# speed. Duct cant is still available (LIFT_CANT_*_DEG) but a front cant toes the folded ducts into the nose.
PUSHER_Z = 0.80                                 # pusher centre height (was 0.90)
PUSHER_TILT_DEG = 10.0                          # exhaust below the body axis (was 0; 20 before the momentum-model optimum)
LIFT_CANT_F_DEG = 0.0                           # front lift-duct thrust tilted forward (deg)
LIFT_CANT_R_DEG = 10.0                          # rear lift-duct thrust tilted forward (deg)
WING_INCIDENCE_DEG = 5.0                        # front + rear wings, leading edge up, about mid-chord (was 0)


def _ss01(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def wing_incidence(xm, key, fillet_s=None):
    """Section incidence (deg, LE up) for the front ("F") or rear ("R") wing at span station xm, or at
    fraction fillet_s across the tip fillet. The whole wing, folding panels included, runs at
    WING_INCIDENCE_DEG out to the duct ring; only the tip fillet twists, so the tip meets its ring in the
    ring's own plane (a ring canted c deg forward sits at -c deg), the same joint as the original design."""
    if key == "R" and REAR_PANEL_FLAT:
        # rear (real fold hinges): the fixed stub runs at REAR_STUB_INC_DEG, easing to 0 at the fold line
        # (a y-axis hinge on the upper skin needs an untwisted section there); the folding panel then twists
        # into the duct ring's plane (-cant) at the duct hinge, and the tip fillet stays in that plane
        if fillet_s is not None:
            return -LIFT_CANT_R_DEG * (1.0 if REAR_TIP_TWIST else _ss01(fillet_s / 0.6))
        inc = REAR_STUB_INC_DEG * (1 - _ss01((xm - (REAR_FOLD_X - 0.15)) / 0.15))
        if REAR_TIP_TWIST:
            # outer panel twists from 0 at the wing fold to the ring plane (-cant) at the duct hinge, so the
            # duct hinge axis lies in the ring's own plane along the whole chord
            inc -= LIFT_CANT_R_DEG * _ss01((xm - REAR_FOLD_X) / (DUCT_X - DUCT_R1 - REAR_FOLD_X))
        return inc
    if fillet_s is None:
        return WING_INCIDENCE_DEG
    tip = -(LIFT_CANT_F_DEG if key == "F" else LIFT_CANT_R_DEG)
    return WING_INCIDENCE_DEG + (tip - WING_INCIDENCE_DEG) * _ss01(fillet_s / 0.6)


def wing_incidence_mean():
    """Area-weighted mean incidence of the two wings (deg), for trim: chord-weighted along each span."""
    ring_in = DUCT_X - DUCT_R1
    tot = num = 0.0
    for key, x0, c0, c1 in (("F", 0.30, 1.05, 0.95), ("R", 0.15, 1.20, 1.00)):     # wing area to the ring
        for x in np.linspace(x0, ring_in, 200):
            c = c0 + (c1 - c0) * (x - x0) / (ring_in - x0)
            tot += c; num += c * wing_incidence(x, key)
    return num / tot
FWD_C = (0.45, TAIL_Y - 0.47, PUSHER_Z)        # on the tail (no fin)
OPF_PUSHER_Z = 0.90                             # where x1_opfplg_blender.py builds the pusher heat exchangers


def pusher_tilt(v, weight=1.0):
    """Move a point built at the OPFPLG model's pusher height down to PUSHER_Z, then rotate it about the
    pusher axis line (through FWD_C, along X) by the tilt (exhaust down). weight blends both (0..1)."""
    v = np.array([v[0], v[1], v[2] + (FWD_C[2] - OPF_PUSHER_Z) * weight])
    d = -math.radians(PUSHER_TILT_DEG) * weight
    y, z = v[1] - FWD_C[1], v[2] - FWD_C[2]
    return np.array([v[0], FWD_C[1] + y * math.cos(d) - z * math.sin(d), FWD_C[2] + y * math.sin(d) + z * math.cos(d)])

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

# cabin (Oct 2026 ergonomic rework). Same outside design; the cabin is resized around real people:
#  * bare-frame seats at a 25 deg sports-car back angle with the H-point dropped close to the floor,
#  * the belly bubbled down and out from the toes back under the seats (no change above the wing roots),
#  * the canopy crown raised to the stowed-height limit and moved back over the heads.
# Checked on every run against a bare-headed 95th-percentile man and 5th-percentile woman.
FIREWALL_Y = -0.33                                  # cabin / engine-bay bulkhead (unchanged)
SEAT_X = 0.30                                       # seat centre lines (driver on the left, +X)
H_Y, H_Z = -0.95, 0.435                             # H-point (hip joint) of the seated occupant
SEAT_BACK_DEG = 25                                  # backrest from vertical (was 18; 25-30 = sports car)
SEAT_PAN_DEG = 12                                   # seat pan rises toward the knees
SEAT_Y = H_Y + 0.05                                 # seat cushion centre (ballast / downstream tools)
FLOOR_Z = 0.255                                     # foot-well floor (heel line)
FOOTWELL = dict(y0=-2.45, y1=-0.40, ramp_f=0.40,    # belly bubble from the toes back under the seats:
                ramp_r=0.40,                        # y extent, fore / aft blend lengths,
                z_cut=0.42, z_bot=0.18, n=3.5)      # skin above z_cut untouched, new keel z_bot, boxy tub
LOUVRE_HW, LOUVRE_CHORD, LOUVRE_LIFT, LOUVRE_T = 0.20, 0.045, 0.024, 0.008   # spine intake slats (m)
LOUVRE_ROOT_GAP = 0.04                              # slat ends stop this far inboard of the rear wing roots
BAY_TUB = dict(y0=-0.60, y1=2.05, ramp_f=0.40,     # engine-bay tub (Oct 2026): the belly under the bay is
               ramp_r=0.60, z_cut=0.70, hw=0.53, n=3.5,   # bubbled down and out like the foot well, no wider
               z_bot=((-0.60, 0.25), (0.80, 0.25), (1.45, 0.39), (2.05, 0.64)))   # than hw; keel (y, z)
ENGINE_DZ = -0.13                                   # engine + accumulator lowered (same as x1_opfplg_blender.py)
CANOPY = dict(y_f=-2.42, y_p=-0.62, y_e=0.55, peak=1.34, w_max=0.66)   # was y_p -0.80, peak 1.27, w 0.62 (stowed limit 1.346)
KNEE_DEG = 125                                      # comfortable knee angle used to place the heels
MANIKINS = {  # side-view link lengths (m), SAE J826 / ANSUR II based, bare head (no helmet)
    "95th-percentile man": dict(torso=0.90, head_c=0.80, head_r=0.10, shoulder=0.55, shoulder_w=0.53,
                                thigh=0.456, leg=0.459, ankle=0.09, foot=0.22),
    "5th-percentile woman": dict(torso=0.72, head_c=0.63, head_r=0.09, shoulder=0.43, shoulder_w=0.40,
                                 thigh=0.38, leg=0.36, ankle=0.075, foot=0.18),
}
HEAD_CLEAR_MIN = 1.0 * IN                           # head to canopy, demo / certification flights


def _circle_up(P, r1, Q, r2):
    """Upper intersection (y, z) of circles centred P, Q (the knee between hip and ankle)."""
    d = np.linalg.norm(Q - P)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(max(r1 * r1 - a * a, 0.0))
    m = P + a * (Q - P) / d
    n = np.array([-(Q - P)[1], (Q - P)[0]]) / d
    k1, k2 = m + h * n, m - h * n
    return k1 if k1[1] > k2[1] else k2


def posture(mk):
    """Joint positions (y, z) of a manikin in the seat, heels on the foot-well floor at KNEE_DEG."""
    a = math.radians(SEAT_BACK_DEG)
    up = np.array([math.sin(a), math.cos(a)])                   # torso line: aft and up
    H = np.array([H_Y, H_Z])
    T, L = mk["thigh"], mk["leg"]
    d = math.sqrt(T * T + L * L - 2 * T * L * math.cos(math.radians(KNEE_DEG)))
    dz = FLOOR_Z + mk["ankle"] - H_Z
    A = H + [-math.sqrt(max(d * d - dz * dz, 0.0)), dz]
    K = _circle_up(H, T, A, L)
    s = (A - K) / L                                             # shin direction
    c, sn = math.cos(math.radians(-95)), math.sin(math.radians(-95))
    f = np.array([c * s[0] - sn * s[1], sn * s[0] + c * s[1]])  # foot ~95 deg to the shin, toes forward
    if f[0] > 0:
        f = -f
    return dict(H=H, up=up, head=H + up * mk["head_c"], top=H + up * mk["torso"],
                shoulder=H + up * mk["shoulder"], knee=K, ankle=A, heel=A + [0.03, -mk["ankle"]],
                toe=A + f * mk["foot"])


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


def lift_duct_part(name, loc, cant=0.0):
    """Stationary ring + three stator struts + motor pod bulged above and below."""
    p = Part(name, ["Paint_White", "Silver", "Dark_Metal"], loc, (math.radians(cant), 0, 0), split=60)
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


def lift_rotor_part(name, loc, n, upper=True, hand=1, cant=0.0):
    """One rotor of the coaxial pair: hub ring around the motor pod + n blades.
    hand = +1 / -1 sets which way the blades are pitched, so each fan pushes air down for its own spin."""
    p = Part(name, ["Dark_Metal", "Silver"], loc, (math.radians(cant), 0, 0), split=50)
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
        if o.name.startswith("OPF_Fan_HX"):       # heat exchangers ride with the fans
            p.V = [pusher_tilt(v) for v in p.V]
        elif "Vapour_Line" in o.name or "Liquid_Return" in o.name:
            # bend the last 0.75 m of each propane line onto the moved heat-exchanger rings
            p.V = [pusher_tilt(v, min(1.0, max(0.0, (v[1] - (FWD_C[1] - 0.75)) / 0.70))) for v in p.V]
        p.F = [tuple(f) for f in o.mesh.f]
        p.M = [mats.index(m) for m in o.mesh.m]
        p.opfplg = o.coll
        out.append(p)
    return out


BODY_X = None
REAR_PANEL_FLAT = True
REAR_STUB_INC_DEG = 9.0                        # rear stub incidence (deg): makes up the lift of the twisted outer panel
REAR_TIP_TWIST = True                          # rear folding panel twists to the ring plane by the duct hinge
REAR_DUCT_RAISE = 0.035                        # rear duct + rotors sit this much higher on the wing tip (m)
REAR_LIP_SCALLOP = True                        # trim the rear ducts' inboard lower lip flat at the fold hinge
REAR_ROTOR_PARK_DEG = 2.0                      # rear lower rotors stop at this index angle before folding
REAR_PANEL_TR = 0.10                          # rear folding panel thickness / chord (stub 0.09, eased)
REAR_FOLD_MAX_DEG = 90.0                      # rear wing fold limit (90 = panel vertical)
REAR_LIP_CLEAR = 0.006                         # clearance below the hinge line (m)
REAR_FOLD_X = 0.78                             # rear wing fold line (RW_HX), also used by wing_incidence
TAIL_SPINE_HW = 0.085                          # tail spine half-width between the pusher bores (bore starts 0.12)


def footwell(v, bot):
    """Belly bubbles: the foot well under the cabin, then the engine-bay tub."""
    return _bubble(_bubble(v, bot, FOOTWELL), bot, BAY_TUB)


def _bubble(v, bot, fw):
    """Bubble the belly down and out: below z_cut the skin is blended toward a boxier
    tub reaching z_bot, smoothly faded in and out along Y. Nothing above z_cut (wing roots, sills) moves."""
    x0, y, z0 = v
    if not (fw["y0"] < y < fw["y1"]) or z0 >= fw["z_cut"]:
        return v
    u = min((y - fw["y0"]) / fw["ramp_f"], (fw["y1"] - y) / fw["ramp_r"], 1.0)
    k = u * u * (3 - 2 * u)
    a = min(BODY_X_AT(y, fw["z_cut"]), fw.get("hw", 9.0))        # tub meets the original skin at z_cut
    zb_ = fw["z_bot"]
    if not isinstance(zb_, (int, float)):                        # keel line given as (y, z) points
        zb_ = float(np.interp(y, [q[0] for q in zb_], [q[1] for q in zb_]))
    b = fw["z_cut"] - min(zb_, bot)
    phi = math.atan2(fw["z_cut"] - z0, abs(x0))                  # same polar angle about (0, z_cut)
    c_, s_ = abs(math.cos(phi)), abs(math.sin(phi))
    xt = math.copysign(a * c_ ** (2 / fw["n"]), x0) if x0 else 0.0
    zt = fw["z_cut"] - b * s_ ** (2 / fw["n"])
    if math.hypot(xt, fw["z_cut"] - zt) < math.hypot(x0, fw["z_cut"] - z0):
        return v                                                 # bubble only ever adds volume
    return (x0 + k * (xt - x0), y, z0 + k * (zt - z0))


BODY_X_AT = None


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
        # aft body: full engine-bay width to y 1.50, then smooth S-ramps narrow it to a slim spine
        # between the pushers, so each pusher swallows the side flow instead of the fuselage
        # running through its bore; the duct inner walls merge into the spine (their mount)
        [1.50, 0.53, 1.12, 0.54, 2.3, 2.4],
        [1.78, 0.30, 1.11, 0.60, 2.2, 2.3],
        [2.00, TAIL_SPINE_HW, 1.10, 0.64, 2.2, 2.2],
        [2.55, TAIL_SPINE_HW, 1.07, 0.72, 2.2, 2.2],
        [TAIL_Y, 0.04, 1.04, 0.82, 2.2, 2.2]]
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
    global BODY_X_AT
    BODY_X_AT = _body_x_frozen
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
        rings.append([footwell(v, bot) for v in ring])
    body = Part("Body", ["Livery"], split=60)
    body.add(loft(rings, start=(0, NOSE_Y, 0.60), end="c"), uv=body_uv)
    parts.append(body)

    # ---- canopy: dark glass helmet-visor sitting on the sills, starting just behind the nose tip,
    #      peaking over the seats, diving into the spine behind the firewall
    y_f, y_p, y_e, peak, w_max = (CANOPY[k] for k in ("y_f", "y_p", "y_e", "peak", "w_max"))

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

    # ---- two side-by-side bare-frame seats (3.1/3.4), reclined, built around the H-point:
    #      pan surface 95 mm under the hip joint, backrest surface 135 mm behind it (SAE J826 manikin)
    ab, ap = math.radians(SEAT_BACK_DEG), math.radians(SEAT_PAN_DEG)
    H2 = np.array([H_Y, H_Z])
    up = np.array([math.sin(ab), math.cos(ab)])                    # along the backrest (y, z)
    aft = np.array([math.cos(ab), -math.sin(ab)])                  # backrest normal, pointing aft
    fwd = np.array([-math.cos(ap), math.sin(ap)])                  # along the pan, toward the knees
    P0 = H2 - 0.095 * np.array([math.sin(ap), math.cos(ap)])
    B0 = H2 + 0.135 * aft
    t_ = np.linalg.solve(np.array([fwd, -up]).T, B0 - P0)[0]
    bight = P0 + t_ * fwd                                          # where the pan meets the backrest
    def yz(q, x=SEAT_X):
        return (x, float(q[0]), float(q[1]))
    def fz(y):                                                     # floor-plate top: flat heel line, rising aft
        return FLOOR_Z - 0.008 + max(0.0, y + 1.30) * 0.12
    seat = Part("Seat_L", ["Seat", "Dark_Metal"], smooth=False)
    PAN_L, BACK_L, T_ = 0.50, 0.62, 0.035
    seat.add(box(yz(bight + fwd * PAN_L / 2 - np.array([math.sin(ap), math.cos(ap)]) * T_ / 2),
                 (0.36, PAN_L, T_), rot_x(-ap)))
    seat.add(box(yz(bight + up * BACK_L / 2 + aft * T_ / 2), (0.38, T_, BACK_L), rot_x(-ab)))
    hd = posture(MANIKINS["95th-percentile man"])["head"]
    seat.add(box(yz(hd + aft * (MANIKINS["95th-percentile man"]["head_r"] + 0.035)), (0.24, 0.05, 0.18),
                 rot_x(-ab)))                                      # headrest behind the head
    for sx in (-0.15, 0.15):                                       # bare tube frame rails
        x_ = SEAT_X + sx
        seat.add(sweep([yz(bight + fwd * PAN_L, x_), yz(bight, x_), yz(bight + up * BACK_L, x_)], 0.014, 8),
                 mat=1)
        yl = float(bight[0] + fwd[0] * (PAN_L - 0.05))
        seat.add(cylinder(yz(bight + fwd * (PAN_L - 0.05), x_), (x_, yl, fz(yl)), 0.014, 8), mat=1)   # front leg
    parts += [seat, seat.mirrored("Seat_R")]
    empties["Seat_L_H_Point"] = (SEAT_X, H_Y, H_Z)
    empties["Seat_R_H_Point"] = (-SEAT_X, H_Y, H_Z)

    # foot-well floor over the bubbled belly, with an adjustable heel rest / toe board per seat
    fl = Part("Cockpit_Floor", ["Dark_Metal"], smooth=False)
    ring_y = np.array([r[0][1] for r in rings])

    def skin_hw(y, z):
        """Half-width of the (bubbled) skin at height z, from the nearest body ring."""
        r = rings[int(np.argmin(abs(ring_y - y)))]
        best = 0.0
        for p_, q_ in zip(r, r[1:] + r[:1]):
            if p_[0] >= 0 and q_[0] >= 0 and (p_[2] - z) * (q_[2] - z) <= 0 and p_[2] != q_[2]:
                best = max(best, p_[0] + (q_[0] - p_[0]) * (z - p_[2]) / (q_[2] - p_[2]))
        return best
    y_fl0 = next(y for y in np.linspace(-2.45, -1.8, 66)
                 if min(v[2] for v in rings[int(np.argmin(abs(ring_y - y)))]) < FLOOR_Z - 0.035)
    ys_ = np.linspace(y_fl0, bight[0], 16)
    floor_hw = lambda y: skin_hw(y, fz(y) - 0.006) - 0.04
    frings = [[(-floor_hw(y), y, fz(y) - 0.006), (floor_hw(y), y, fz(y) - 0.006),
               (floor_hw(y), y, fz(y)), (-floor_hw(y), y, fz(y))] for y in ys_]
    fl.add(loft(frings, start="c", end="c"))
    parts.append(fl)
    pm = posture(MANIKINS["95th-percentile man"])
    pw = posture(MANIKINS["5th-percentile woman"])
    rest = Part("Footrest_L", ["Paint_Black", "Dark_Metal"], smooth=False)
    for x_ in (SEAT_X - 0.12, SEAT_X + 0.12):                      # rail from the man's heel to the woman's
        rest.add(box((x_, (pm["heel"][0] + pw["heel"][0]) / 2, FLOOR_Z + 0.008),
                     (0.025, abs(pw["heel"][0] - pm["heel"][0]) + 0.16, 0.016)), mat=1)
    tb = (pm["heel"] + pm["toe"]) / 2
    ft = (pm["toe"] - pm["heel"]) / np.linalg.norm(pm["toe"] - pm["heel"])
    rest.add(box((SEAT_X, float(tb[0]), float(tb[1]) - 0.012), (0.26, float(np.linalg.norm(pm["toe"] - pm["heel"])), 0.012),
                 rot_x(math.atan2(ft[1], ft[0]))), mat=0)
    parts += [rest, rest.mirrored("Footrest_R")]

    # ---- engine bay under the raised spine, firewall to the pushers
    BAY_Y0, BAY_Y1 = FIREWALL_Y, FWD_C[1] - FWD_HL - 0.05
    firewall = Part("Firewall", ["Dark_Metal"], smooth=False)
    firewall.add(box((0, BAY_Y0, 0.66), (0.90, 0.03, 0.56)))
    firewall.add(box((0, BAY_Y0, 0.37), (0.56, 0.03, 0.06)))        # down to the bay tub floor
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
    engine.add(box((0, (ENG_Y0 + 1.50) / 2, 0.78 + ENGINE_DZ), (1.00, 1.50 - ENG_Y0, 0.46)), mat=0)
    for x in (-0.24, 0.24):
        engine.add(cylinder((x, ENG_Y0 + 0.05, 0.92 + ENGINE_DZ), (x, 1.40, 0.92 + ENGINE_DZ), 0.13, 16), mat=1)
    parts.append(engine)
    empties["Engine_Bay"] = (0.0, (ENG_Y0 + 1.50) / 2, 0.78 + ENGINE_DZ)
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

    def duct_wing(name, yc, zc, root_x, chord_root, chord_tip, tr, x_from, x_to=None, n=10, trim=False, key="F"):
        """Wing segment from x_from to x_to (None = out to the ring, tip following its inboard curve).
        trim=True: the inboard end follows the fuselage skin instead of running on inside the body."""
        w = Part(name, ["Paint_White"], split=50)
        span = (DUCT_X - DUCT_R1) - root_x
        rings_w = []
        for s_ in np.linspace(0, 1, n):
            ring_pts = []
            xm = x_from + ((x_to if x_to is not None else DUCT_X - DUCT_R1) - x_from) * s_
            ch = chord_root + (chord_tip - chord_root) * min(1.0, (xm - root_x) / span)
            inc = math.radians(wing_incidence(xm, key, s_ if x_from >= DUCT_X - DUCT_R1 - 1e-6 else None))
            sec = airfoil(1.0, tr(xm) if callable(tr) else tr)
            ci, si = math.cos(inc), math.sin(inc)
            for dy, dz in sec:
                u, v_ = -ch / 2 + dy * ch, dz * ch                # chord position, thickness offset
                y, z = yc + u * ci + v_ * si, zc - u * si + v_ * ci   # incidence about mid-chord, LE up
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
    #      Every hinge axis sits on the skin on the INSIDE of its fold (front wing: lower skin, front duct:
    #      upper, rear wing: upper, rear duct: lower), so the panels open apart instead of passing
    #      through each other. Axis heights and fold angles are set at the end of build_parts().
    HINGES.clear()
    ring_in = DUCT_X - DUCT_R1
    FW_HX, RW_HX = 0.70, REAR_FOLD_X    # wing hinge lines (fixed stubs inboard)
    beta = alpha = 1.2                                            # placeholders; solved at the end
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
    fp = duct_wing("Front_Wing_L", DUCT_YF, DUCT_ZF, 0.30, 1.05, 0.95, 0.09, FW_HX, ring_in, n=10, trim=True)
    fp.parent = "Hinge_FrontWing_L"
    ff = duct_wing("Front_Wing_Fillet_L", DUCT_YF, DUCT_ZF, 0.30, 1.05, 0.95, 0.09, ring_in, n=4)
    ff.parent = "Hinge_FrontDuct_L"                               # curved tip blends into the ring, folds with it
    # rear wing: high, off the upper rear fuselage - fixed stub, outer panel folds
    def rear_tr(xm):                                              # thinner outer rear wing: smaller fold offset
        return 0.09 + (REAR_PANEL_TR - 0.09) * _ss01((xm - (RW_HX - 0.25)) / 0.25)
    rs = duct_wing("Rear_Wing_Stub_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, rear_tr, 0.15, RW_HX, n=12, key="R")
    rp = duct_wing("Rear_Wing_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, rear_tr, RW_HX, ring_in, n=8, key="R")
    rp.parent = "Hinge_RearWing_L"
    rf = duct_wing("Rear_Wing_Fillet_L", DUCT_YR, DUCT_ZR - 0.01, 0.15, 1.20, 1.00, REAR_PANEL_TR, ring_in, n=4, key="R")
    rf.parent = "Hinge_RearDuct_L"
    for w in (fs, fp, ff, rs, rp, rf):
        parts += [w, w.mirrored(w.name[:-1] + "R")]

    # ---- engine-bay intake louvres on the spine: each slat is bent to the crown across its whole width
    #      (aft edge on the skin, leading edge raised), and stops short of where the rear wing roots come
    #      up through the skin
    louvres = Part("Engine_Louvres", ["Paint_Black"], smooth=False)
    stub_v = np.array(rs.V)
    for y in np.arange(0.70, 1.60, 0.085):
        ya, yf = y + LOUVRE_CHORD / 2, y - LOUVRE_CHORD / 2
        near = stub_v[(stub_v[:, 1] > yf - 0.03) & (stub_v[:, 1] < ya + 0.03)]
        proud = [v[0] for v in near if v[2] > body_z(v[0], v[1]) - 0.025]   # roots at or just under the skin
        hw = min(LOUVRE_HW, (min(proud) if proud else 9.0) - LOUVRE_ROOT_GAP)
        if hw < 0.05:
            continue
        slat = []
        for x in np.linspace(-hw, hw, 21):
            a_top = np.array([x, ya, body_z(x, ya) + 0.002])
            f_top = np.array([x, yf, body_z(x, yf) + LOUVRE_LIFT])
            slat.append([a_top, f_top, f_top - [0, 0, LOUVRE_T], a_top - [0, 0, LOUVRE_T]])
        louvres.add(loft(slat, start="c", end="c"))
    parts.append(louvres)
    def skin_z(parts_, x0, top):
        zz = [v[2] for q in parts_ for v in q.V if abs(v[0] - x0) < 0.004]
        return (max(zz) + 0.003) if top else (min(zz) - 0.003)
    HINGE_Z = dict(FW=skin_z([fs, fp], FW_HX, False), FD=skin_z([fp, ff], ring_in, True),
                   RW=skin_z([rs, rp], RW_HX, True), RD=skin_z([rp, rf], ring_in, False))
    cr = math.radians(LIFT_CANT_R_DEG)
    RD_N = rot_x(cr) @ np.array([0, 0, 1.0]) if REAR_TIP_TWIST else np.array([0, 0, 1.0])   # ring normal
    RD_AX = rot_x(cr) @ np.array([0, 1.0, 0]) if REAR_TIP_TWIST else np.array([0, 1.0, 0])  # hinge axis
    c0 = np.array([ring_in, DUCT_YR, DUCT_ZR - 0.01])
    wmin = min(float((v - c0) @ RD_N) for q in (rp, rf) for v in q.V if abs(v[0] - ring_in) < 0.004) - 0.003
    RD_LOC = c0 + wmin * RD_N                                     # on the lower skin line at the tip
    HINGE_Z["RD"] = float(RD_LOC[2])
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
        cant = LIFT_CANT_F_DEG if key == "F" else LIFT_CANT_R_DEG
        C = np.array([DUCT_X, yc, zc]) + ((rot_x(math.radians(cant)) @ np.array([0, 0, REAR_DUCT_RAISE]))
                                          if key == "R" else 0)
        d = lift_duct_part(f"Duct_{key}L", C, cant)
        # the rear pair spins opposite to the front pair (diagonal torque balance), so its blades are
        # pitched the other way; the right side is a mirror image, which flips pitch and spin together
        hand = 1 if key == "F" else -1
        up = lift_rotor_part(f"Rotor_{key}L_Upper", C, BLADES_UPPER, True, hand, cant)
        lo = lift_rotor_part(f"Rotor_{key}L_Lower", C, BLADES_LOWER, False, hand, cant)
        if key == "R":
            lo.park = math.radians(REAR_ROTOR_PARK_DEG)            # stow index: blades clear the folded panel
        for p in (d, up, lo):
            p.parent = "Hinge_FrontDuct_L" if key == "F" else "Hinge_RearDuct_L"
            parts.append(p)
            parts.append(p.mirrored(p.name.replace("L_", "R_") if "L_" in p.name else p.name[:-1] + "R"))

    # ---- twin ducted pushers (forward flight, 3.6.2) on the raised tail
    trot = (-(math.pi / 2 + math.radians(PUSHER_TILT_DEG)), 0, 0)   # fan axis aft, exhaust tilted down
    th = Part("Thruster_L", ["Paint_White", "Paint_Red", "Paint_Black", "Dark_Metal"], FWD_C, trot, split=60)
    th.duct_id = 2 * FWD_R0
    prof = rounded_rect(FWD_R0, FWD_R1, FWD_Z0, FWD_Z1, 0.03, n=4, outer_z=(-0.17, -0.14, 0.10))
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
    # minimal fairing: one slim streamlined pylon per side ties the sponson (tank + wheels) to the fuselage
    # where they come closest, along the top of the sponson; the ends run into both skins
    PY_Y0, PY_Y1, PY_Z, PY_T = -0.72, 0.30, 0.50, 0.06       # chord ends, height, thickness / chord
    def sponson_in_x(y, z):
        t = (y - SP_Y0) / (SP_Y1 - SP_Y0)
        k = max((1 - abs(2 * t - 1) ** 3.0), 0.0) ** (1 / 3.0)
        q = min(abs(z - SP_ZC) / max(SP_B * k, 1e-6), 1.0)
        return SP_XC - SP_A * k * (1 - q ** 2.6) ** (1 / 2.6)
    ch = PY_Y1 - PY_Y0
    th_ = np.linspace(0, math.pi, 13)
    cs = 0.5 * (1 - np.cos(th_))
    yt = 5 * PY_T * (0.2969 * np.sqrt(cs) - 0.126 * cs - 0.3516 * cs ** 2 + 0.2843 * cs ** 3 - 0.1036 * cs ** 4)
    sec = [(c, t) for c, t in zip(cs, yt)][::-1] + [(c, -t) for c, t in zip(cs, yt)][1:-1]
    py_rings = []
    for s_ in np.linspace(0, 1, 5):
        ring = []
        for c, t in sec:
            y, z = PY_Y0 + c * ch, PY_Z + t * ch
            a_, b_ = skin_hw(y, z) - 0.006, sponson_in_x(y, z) + 0.006
            ring.append((a_ + (max(b_, a_) - a_) * s_, y, z))
        py_rings.append(ring)
    pylon = Part("Sponson_Pylon_L", ["Paint_White"], split=50)
    pylon.add(loft(py_rings, start="c", end="c"))
    parts += [pylon, pylon.mirrored("Sponson_Pylon_R")]
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
            c = np.array([sgn * DUCT_X, yc, zc]) + ((rot_x(math.radians(LIFT_CANT_R_DEG)) @
                                                     np.array([0, 0, REAR_DUCT_RAISE])) if key == "R" else 0)
            col = Part(f"COL_Duct_{key}{side}", [], smooth=False, coll="col")
            ax_ = rot_x(math.radians(LIFT_CANT_F_DEG if key == "F" else LIFT_CANT_R_DEG)) @ np.array([0, 0, 0.15])
            col.add(cylinder(c - ax_, c + ax_, DUCT_R1, 10))
            col.parent = f"Hinge_{'Front' if key == 'F' else 'Rear'}Duct_{side}"
            parts.append(col)

    parts += engine_ext                     # exhaust tailpipe, external propane lines, pusher heat exchangers

    eye = pm["head"] + np.array([-0.08 * math.cos(ab), 0.0]) - pm["up"] * 0.02   # eyes ahead of head centre
    empties["Cam_Driver_Eye"] = (SEAT_X, float(eye[0]), float(eye[1]))

    # fold angles with the hinge axes on the skins: bisect the wing fold so the folded craft's top stays
    # 3 mm under the 53 in limit; the duct then turns to stand on edge (front -90 deg net, rear +90 deg net)
    def set_hinges(beta_, alpha_):
        for side, sgn in (("L", 1), ("R", -1)):
            HINGES[f"Hinge_FrontWing_{side}"] = dict(loc=np.array([sgn * FW_HX, DUCT_YF, HINGE_Z["FW"]]), parent=None,
                                                     angle=sgn * beta_)
            HINGES[f"Hinge_FrontDuct_{side}"] = dict(loc=np.array([sgn * ring_in, DUCT_YF, HINGE_Z["FD"]]),
                                                     parent=f"Hinge_FrontWing_{side}", angle=-sgn * (math.pi / 2 + beta_))
            HINGES[f"Hinge_RearWing_{side}"] = dict(loc=np.array([sgn * RW_HX, DUCT_YR, HINGE_Z["RW"]]), parent=None,
                                                    angle=-sgn * alpha_)
            HINGES[f"Hinge_RearDuct_{side}"] = dict(loc=RD_LOC * [sgn, 1, 1], axis=RD_AX,
                                                    parent=f"Hinge_RearWing_{side}", angle=sgn * min(math.pi, math.pi / 2 + alpha_))
    if REAR_LIP_SCALLOP:
        scallop_rear_lips(parts, RD_LOC, RD_N, ring_in, RD_AX)
        for q in [q for q in parts if q.name in ("Duct_RL", "Rear_Wing_Fillet_L")]:   # right side = mirror
            r_ = [x for x in parts if x.name == q.name[:-1] + "R"][0]
            r_.V = [v * [-1, 1, 1] for v in q.V]
    front = [q for q in parts if q.coll == "main" and q.parent and "Front" in q.parent and q.parent.endswith("_L")]
    rear = [q for q in parts if q.coll == "main" and q.parent and "Rear" in q.parent and q.parent.endswith("_L")]
    top_lim = RULES["folded_height_max"] - 0.003
    def solve_fold(group, which):
        lo, hi = 0.2, 1.55
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            set_hinges(mid if which == "F" else beta, mid if which == "R" else alpha)
            top = max(posed(q, True)[:, 2].max() for q in group)
            # front: a bigger fold drops the duct (lower top); rear: a bigger fold raises it
            if (top > top_lim) == (which == "F"):
                lo = mid
            else:
                hi = mid
        return hi if which == "F" else lo
    beta, alpha = 1.2, 1.2
    beta = solve_fold(front, "F")
    # rear: the hinge is on the upper skin, so a fold just past vertical leans the short panel over the
    # engine bay and brings the hanging duct back inboard; pick the narrowest fold that stays under the
    # height limit and off the ground
    best_a = None
    for a_ in np.radians(np.arange(45.0, REAR_FOLD_MAX_DEG + 0.01, 0.5)):
        # past vertical the duct's own fold stays at 180 deg (it would otherwise pass through the panel), so
        # the panel leans in over the engine bay and the hanging duct tilts its bottom inboard
        set_hinges(beta, a_)
        Vr = np.vstack([posed(q, True) for q in rear])
        if Vr[:, 2].max() > top_lim or Vr[:, 2].min() < 0.03:
            continue
        if best_a is None or Vr[:, 0].max() < best_a[1]:
            best_a = (a_, Vr[:, 0].max())
    alpha = best_a[0]
    set_hinges(beta, alpha)
    empties["Cam_Chase"] = (0.0, 8.0, 2.4)
    return parts, empties


def hinge_chain(name):
    chain = []
    while name:
        chain.append(name)
        name = HINGES[name]["parent"]
    return chain                                                  # innermost first


def axis_rot(ax, a):
    """Rotation matrix by angle a about unit axis ax (right-handed)."""
    ax = np.asarray(ax, float) / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


def _vhits(T, x, y):
    """z of the crossings of the vertical line through (x, y) with a triangle soup T (n, 3, 3)."""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    v0, v1, v2 = B[:, :2] - A[:, :2], C[:, :2] - A[:, :2], np.array([x, y]) - A[:, :2]
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
    ok = np.abs(den) > 1e-14
    den = np.where(ok, den, 1)
    b = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
    c = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
    m_ = ok & (b >= -1e-9) & (c >= -1e-9) & (1 - b - c >= -1e-9)
    return (A[m_, 2] + b[m_] * (B[m_, 2] - A[m_, 2]) + c[m_] * (C[m_, 2] - A[m_, 2]))


def scallop_rear_lips(parts, h_loc, h_n, ring_in, h_ax=None):
    """Real hinge on the rear wing's lower skin, duct folding 180 degrees: anything that folds with the duct
    and sits below the hinge line inside the folded panel's footprint would swing up through the panel.
    The canted ring's forward-inboard arc (and the fillet under it) dips below the hinge there, so the
    ring's lower lip is trimmed flat just above the hinge plane over that arc (a scallop), blended out at the ends."""
    h_n = np.asarray(h_n, float)
    panel = [q for q in parts if q.name == "Rear_Wing_L"][0]
    W = posed(panel)
    y0, y1 = W[:, 1].min() - 0.03, W[:, 1].max() + 0.03
    xr = ring_in + (ring_in - W[:, 0].min()) + 0.03          # mirror image of the panel root about the hinge
    for q in parts:
        if not (q.parent and q.parent.startswith("Hinge_RearDuct_")) or q.name.startswith("Rotor_"):
            continue
        R = euler_xyz(q.rot)
        Vw = np.array([R @ v + q.loc for v in q.V])
        ax = np.abs(Vw[:, 0])
        # clip level: just above the hinge plane (through the hinge axis, normal h_n) inside the folded
        # panel's footprint, falling away outside it (no step)
        out = np.maximum(np.maximum(y0 - Vw[:, 1], Vw[:, 1] - y1), np.maximum(ax - xr, ring_in - 0.01 - ax))
        lim = REAR_LIP_CLEAR - 1.5 * np.clip(out, 0, None)
        hp = h_loc * [np.sign(q.loc[0]) or 1, 1, 1]
        w = (Vw - hp) @ h_n
        hit = w < lim
        if hit.any():
            Vw[hit] += np.outer(lim[hit] - w[hit], h_n)
        n_hit = int(hit.sum())
        if h_ax is not None and q.coll == "main" and not q.name.endswith("R"):
            # then against the panel itself: the rear panel's twisted root dips below the tip plane aft, so
            # lift any point whose 180-degree image still lands inside the panel until it clears by 4 mm
            Rf = axis_rot(h_ax, math.pi)
            Tp = W[np.array([(f[0], f[j], f[j + 1]) for f in panel.F for j in range(1, len(f) - 1)])]
            for i in range(len(Vw)):
                if abs(Vw[i, 0]) > xr + 0.05 or not (y0 - 0.05 < Vw[i, 1] < y1 + 0.05):
                    continue
                for _ in range(40):
                    im = Rf @ (Vw[i] - hp) + hp
                    z = _vhits(Tp, im[0], im[1])
                    if len(z) < 2 or not (z.min() - 0.004 < im[2] < z.max() + 0.004):
                        break
                    Vw[i] += 0.002 * h_n
                    n_hit += 1
        if n_hit:
            q.V = [R.T @ (v - q.loc) for v in Vw]
            q.scalloped = n_hit


def posed(p, stowed=False):
    """World-space vertices of a part, in flight or stowed pose."""
    R = euler_xyz(p.rot)
    if stowed and getattr(p, "park", 0.0):
        R = R @ rot_z(p.park)                                     # rotor parked at its stow index angle
    V = np.array([R @ v + p.loc for v in p.V])
    if stowed and p.parent:
        for h in hinge_chain(p.parent):                           # rotate about each hinge (rest frame)
            c, a = HINGES[h]["loc"], HINGES[h]["angle"]
            Rh = axis_rot(HINGES[h]["axis"], a) if "axis" in HINGES[h] else rot_y(a)
            V = (Rh @ (V - c).T).T + c
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
    ergo_check(parts)
    return rows


def _soup(p):
    V = posed(p)
    return V[np.array([(f[0], f[k], f[k + 1]) for f in p.F for k in range(1, len(f) - 1)])]


def _vhits(T, x, y):
    """Heights where the vertical line through (x, y) crosses a triangle soup."""
    A, B, C = T[:, 0], T[:, 1], T[:, 2]
    v0, v1, v2 = B[:, :2] - A[:, :2], C[:, :2] - A[:, :2], np.array([x, y]) - A[:, :2]
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
    ok = np.abs(den) > 1e-14
    den = np.where(ok, den, 1.0)
    b = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
    c = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
    m = ok & (b >= -1e-9) & (c >= -1e-9) & (1 - b - c >= -1e-9)
    return np.sort(((1 - b - c) * A[:, 2] + b * B[:, 2] + c * C[:, 2])[m])


def ergo_check(parts, verbose=True):
    """Seat a 95th-percentile man and a 5th-percentile woman (bare-headed) and measure clearance
    to the canopy (8 mm glass), the floor skin (25 mm floor) and the firewall. Negative = interference."""
    d = {p.name: p for p in parts}
    TB, TC = _soup(d["Body"]), _soup(d["Canopy"])

    def margin(x, y, z):
        zb, zc = _vhits(TB, x, y), _vhits(TC, x, y)
        if len(zb) == 0:
            return -1.0, "outside"
        roof = (zc.max() - 0.008) if len(zc) else zb.max() - 0.025
        lo = zb.min() + 0.025
        return min(roof - z, z - lo), ("canopy" if roof - z < z - lo else "floor")

    dirs = [np.array(v, float) / np.linalg.norm(v) for v in
            [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)] +
            [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)] +
            [(0, sy, 1) for sy in (-1, 1)] + [(sx, 0, 1) for sx in (-1, 1)]]
    report = {}
    if verbose:
        print("Cockpit fit (bare-headed, left seat; right seat is the mirror image)")
    for name, mk in MANIKINS.items():
        P = posture(mk)
        X = SEAT_X
        regions = {
            "head": [((X, *P["head"]), mk["head_r"])],
            "shoulders": [((X + s * (mk["shoulder_w"] / 2 - 0.06), *P["shoulder"]), 0.06) for s in (-1, 1)],
            "torso": [((X, *(np.array([H_Y, H_Z]) + P["up"] * t)), 0.12) for t in (0.15, 0.30, 0.45)],
            "knees": [((X + s * 0.10, *P["knee"]), 0.065) for s in (-1, 1)],
            "shins": [((X + s * 0.09, *((P["knee"] + P["ankle"]) / 2)), 0.055) for s in (-1, 1)],
            "feet": [((X + s * 0.08, *q), 0.045) for s in (-1, 1) for q in (P["toe"], P["heel"] + [0, 0.05])],
        }
        res = {}
        for rg, spheres in regions.items():
            best = (9.0, "")
            for c, r in spheres:
                for u in dirs:
                    q = np.array(c) + r * u
                    mg = margin(*q)
                    best = min(best, mg)
            res[rg] = best
        T, L = mk["thigh"], mk["leg"]
        kv1, kv2 = P["knee"] - P["H"], P["ankle"] - P["knee"]
        knee = 180 - math.degrees(math.acos(np.dot(kv1, kv2) / (T * L)))
        # headrest (built for the man) and head against the firewall: anything aft of the firewall face
        # must be above its top edge (the space over the transverse tank is open up to the canopy)
        fwp = d["Firewall"]
        Vf = posed(fwp)
        fy, ftop = Vf[:, 1].min(), Vf[:, 2].max()
        Vs = posed(d["Seat_L"])
        low = Vs[Vs[:, 2] < ftop + 0.01]
        fw = fy - low[:, 1].max()
        under = min(Vs[:, 2][i] - _vhits(TB, *Vs[i, :2]).min() for i in range(len(Vs))
                    if Vs[i, 1] > -1.20 and len(_vhits(TB, *Vs[i, :2])))
        report[name] = dict(res=res, knee=knee, heel_y=P["heel"][0], firewall=fw, P=P)
        if verbose:
            h = res["head"][0]
            print(f"  {name}: head to canopy {h / IN:+5.1f} in "
                  f"({'OK' if h >= HEAD_CLEAR_MIN else 'TIGHT' if h >= 0 else 'HITS'}, want >= {HEAD_CLEAR_MIN / IN:.1f} in)")
            for rg in ("shoulders", "torso", "knees", "shins", "feet"):
                mg, w = res[rg]
                print(f"      {rg:9s} {mg / IN:+5.1f} in to {w:6s} {'OK' if mg >= 0 else 'HITS'}")
            print(f"      knee angle {knee:4.0f} deg, heel at y {P['heel'][0]:+.2f} m")
    m_, w_ = report["95th-percentile man"], report["5th-percentile woman"]
    if verbose:
        print(f"  Seat frame to firewall face (below its top edge): {fw / IN:+.1f} in  {'OK' if fw >= 0 else 'HITS'}")
        print(f"  Seat frame to belly skin (floor depth under the seat): {under / IN:+.1f} in  "
              f"{'OK' if under >= 0.025 else 'TIGHT' if under >= 0 else 'HITS'}")
        print(f"  Foot-rest rail travel (man -> woman): {(w_['heel_y'] - m_['heel_y']) / IN:.1f} in")
        print(f"  Seat: back {SEAT_BACK_DEG} deg from vertical, pan {SEAT_PAN_DEG} deg, H-point "
              f"({H_Y:+.2f}, {H_Z:.2f}) m = {(H_Z - FLOOR_Z) / IN:.1f} in above the heel line")
    return report


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
    # fold hinges: empties parented in a chain, rotating about their local Y axis (rear ducts: canted axis)
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
        if "axis" in HINGES[name]:                                # canted hinge (rear duct): axis-angle
            ax_ = HINGES[name]["axis"]
            e.rotation_mode = "AXIS_ANGLE"
            e.rotation_axis_angle = (0.0, ax_[0], ax_[1], ax_[2])
            e.keyframe_insert(data_path="rotation_axis_angle", frame=1)
            e.rotation_axis_angle = (HINGES[name]["angle"], ax_[0], ax_[1], ax_[2])
            e.keyframe_insert(data_path="rotation_axis_angle", frame=60)
            continue
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
