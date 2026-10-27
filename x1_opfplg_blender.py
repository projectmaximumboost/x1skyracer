"""
X1 SkyRacer - OPFPLG concept model (opposed free-piston linear generator)
=====================================================================
Blender 3.6 / 4.x.  Scripting workspace -> New text -> paste -> Run Script.

What it builds (collection "X1_OPFPLG"):
  * 3 opposed-piston cylinders, 6 free pistons, uniflow two-stroke:
      - forward piston controls the INTAKE port ring, aft piston the EXHAUST ring
      - ports are holes cut through the sleeve all the way round the bore, so the
        gas load on the piston is balanced on both sides (no net side thrust);
        intake ports are angled for swirl, exhaust ports are radial
  * each piston carries a tubular Halbach translator, spaced well back from the
    crown so the magnets never enter the hot liner
  * generator stator = plain hollow cylinder (as requested)
  * the sealed volume under each piston (around the translator/stator) is the
    linear-generator housing: the sealed gas volume under the piston (the gas spring
    that returns the piston) and the propane phase-change cooling volume
  * linear-generator housing vapour headers -> external lines -> 3D-printed heat exchangers
    behind the two rear pusher fans; their stator vanes are the condenser
    surfaces; liquid returns to a receiver and is fed back to the stators
  * exhaust belts -> collector -> turbine of an electric turbo-compound unit
    (compressor | motor-generator | turbine on one shaft) -> exhaust leaves the
    envelope under the pusher ducts
  * propane DI injectors + rail; 120 deg phasing between cylinders

Coordinates match the published X1 SkyRacer script (x1_skyracer_blender.py):
metres, nose toward -Y, Z up, origin on the ground.  Engine-bay envelope
derived from that script: x +/-0.50, y 0.14..1.50, z 0.42..0.88 m
(about 39 x 53 x 18 in; lowered 0.13 m in Oct 2026 by ENGINE_DZ to clear the
lowered rear wing, with the belly bubbled down under the bay to suit).  Pushers at x +/-0.45, y 2.271, z 0.90, 26 in bore.

Run it inside your X1_SkyRacer.blend and it drops straight into place (it hides
Engine_Placeholder).  In either case it also builds
spatial references (no X1 body): bay-envelope box and pusher-duct outlines in
wireframe, plus empties for the craft origin, engine bay and both thrusters.
Everything is parented to OPF_X1_Craft_Origin (at the X1 origin, identity).
Pistons are animated with drivers: frames 1-24 = one cycle.

Run with plain Python (no Blender) and it writes an OBJ + MTL, preview PNGs and
the fit report instead.
"""

import math
import os
import sys

try:
    import bpy
    IN_BLENDER = True
except ImportError:
    bpy = None
    IN_BLENDER = False

# ---------------------------------------------------------------- settings ---
PRESET = "4.5L"         # "3L", "4.5L" or "6L"  (4.5 L is the working minimum)
PRESETS = {
    "3L":   dict(bore=0.084, stroke=0.090, note="finalized OPFPLG spec: 84 bore x 90 stroke per piston"),
    "4.5L": dict(bore=0.100, stroke=0.096, note="100 bore x 96 stroke per piston"),
    "6L":   dict(bore=0.125, stroke=0.081, note="125 bore x 81 stroke, strongly oversquare so it still fits across the bay"),
}
EXHAUST_LEAD_DEG = 12.0     # exhaust piston leads the intake piston (uniflow timing)
N_PORTS = 16                # port holes per ring, evenly spaced all the way round
N_STATOR_VANES = 13         # heat-exchanger stator vanes per pusher (rotor has 11 blades)
OUT_DIR = os.path.join(os.path.expanduser("~"), "X1_Racer")   # where your X1 files live
TURBO_SPIN_RAD_PER_FRAME = 2 * math.pi * 2 / 24   # 2 turns per 24-frame loop (seamless, readable)
BUILD_REFERENCE = True     # bay box, pusher-duct wireframes and anchor empties (no X1 body)

# ------------------------------------------------- X1 SkyRacer reference data ---
ENGINE_DZ = -0.13         # whole engine + accumulator lowered 5.1 in (Oct 2026) to clear the lowered rear wing
ENV = dict(x=(-0.50, 0.50), y=(0.14, 1.50), z=(0.55 + ENGINE_DZ, 1.01 + ENGINE_DZ))   # engine bay envelope
Z_C = 0.78                # engine centre height as drawn; everything in the bay is then moved by ENGINE_DZ
ZC_BAY = Z_C + ENGINE_DZ  # engine centre height in the craft
PUSHER_X, PUSHER_Y, PUSHER_Z = 0.45, 2.271, 0.90               # FWD_C (mirrored in x)
PUSHER_R0, PUSHER_R1, PUSHER_HL = 0.33, 0.40, 0.25             # bore r, outer r, half length
PUSHER_HUB_R, PUSHER_HUB_L, PUSHER_ROTOR_Z = 0.11, 0.22, -0.10
# Accumulator: rectangular LTO power pack (burst + load smoothing), under the generator.
# 162 x Toshiba SCiB 20Ah-HP (116 x 22 x 106 mm, 545 g, 2.3 V, 46 Wh, 1.9 kW 10 s), 162S.
# Needs the stator liquid feed above the stators (nothing under the bank but the HV feed).
LTO_CELL = (0.116, 0.022, 0.106)          # across (x), stack (y), height (z)
LTO_NX, LTO_NY = 6, 27                     # 6 across x 27 fore-aft
LTO_PITCH_Y, LTO_GAP_X = 0.0235, 0.008     # stack pitch incl. spacer; gap between columns
LTO_WALL, LTO_CLR, LTO_END, LTO_BUS = 0.003, 0.006, 0.008, 0.010   # case wall, cell-case clearance, end plate, busbar layer
ACC_Y0, ACC_TOP = 0.12, 0.630
ACC_W = LTO_NX * LTO_CELL[0] + (LTO_NX - 1) * LTO_GAP_X + 2 * (LTO_WALL + LTO_CLR + LTO_END)
ACC_L = LTO_NY * LTO_PITCH_Y + 2 * (LTO_WALL + LTO_CLR + LTO_END)
ACC_H = 2 * (LTO_WALL + LTO_CLR) + LTO_CELL[2] + LTO_BUS
ACC_C = (0.0, ACC_Y0 + ACC_L / 2, ACC_TOP - ACC_H / 2)
ACC_TOP_BAY = ACC_TOP + ENGINE_DZ
HULL = [  # y, half-width, top z, bottom z, crown exponent, belly exponent (X1 SkyRacer station table)
    [-2.741, 0.05, 0.64, 0.56, 2.2, 2.2], [-2.50, 0.34, 0.74, 0.40, 2.2, 2.2],
    [-2.00, 0.56, 0.82, 0.32, 2.3, 2.4], [-1.30, 0.68, 0.88, 0.30, 2.4, 2.6],
    [-0.50, 0.72, 0.90, 0.32, 2.4, 2.6], [0.40, 0.68, 1.06, 0.38, 2.4, 2.6],
    [1.20, 0.56, 1.12, 0.50, 2.3, 2.4], [1.50, 0.53, 1.12, 0.54, 2.3, 2.4],
    [1.78, 0.30, 1.11, 0.60, 2.2, 2.3], [2.00, 0.085, 1.10, 0.64, 2.2, 2.2],
    [2.741, 0.04, 1.04, 0.82, 2.2, 2.2]]
# X1 SkyRacer engine-bay tub: below z_cut the belly is bubbled down and out to a boxy keel at z_bot
# (same rule as the X1 script's BAY_TUB; faded in / out over the ramps along Y)
BAY_TUB = dict(y0=-0.60, y1=2.05, ramp_f=0.40, ramp_r=0.60, z_cut=0.70, hw=0.53, n=3.5,
               z_bot=((-0.60, 0.25), (0.80, 0.25), (1.45, 0.39), (2.05, 0.64)))   # keel line (y, z)


def _tub_zbot(y):
    pts = BAY_TUB["z_bot"]
    for (y0, z0), (y1, z1) in zip(pts[:-1], pts[1:]):
        if y0 <= y <= y1:
            return z0 + (z1 - z0) * (y - y0) / (y1 - y0)
    return pts[0][1] if y < pts[0][0] else pts[-1][1]


def hull_row(y):
    for a, b in zip(HULL[:-1], HULL[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * t for i in range(6)]
    return HULL[0] if y < HULL[0][0] else HULL[-1]


def _body_x0(y, z):
    _, hw, top, bot, nu, nl = hull_row(y)
    zc, hh = 0.5 * (top + bot), 0.5 * (top - bot)
    q = max(-1.0, min(1.0, (z - zc) / hh))
    n = nu if q >= 0 else nl
    return hw * (1 - abs(q) ** n) ** (1 / n)


def _tub_k(y):
    t = BAY_TUB
    if not (t["y0"] < y < t["y1"]):
        return 0.0
    u = min((y - t["y0"]) / t["ramp_f"], (t["y1"] - y) / t["ramp_r"], 1.0)
    return u * u * (3 - 2 * u)


def belly_z(y):
    """Lowest point of the X1 belly at station y, with the engine-bay tub."""
    bot = hull_row(y)[3]
    return bot + _tub_k(y) * (min(bot, _tub_zbot(y)) - bot)


def body_x(y, z):
    """Skin half-width at height z, with the engine-bay tub (fully faded in; the ramps are outside the bay)."""
    x0 = _body_x0(y, z)
    t = BAY_TUB
    k = _tub_k(y)
    if k <= 0 or z >= t["z_cut"]:
        return x0
    a, b = min(_body_x0(y, t["z_cut"]), t["hw"]), t["z_cut"] - min(_tub_zbot(y), hull_row(y)[3])
    s_ = min(1.0, (t["z_cut"] - z) / b)
    xt = a * max(0.0, 1 - s_ ** t["n"]) ** (1 / t["n"])
    return max(x0, x0 + k * (xt - x0))


# --------------------------------------------------------------- materials ---
#            name:            (r, g, b),            metallic, roughness, alpha
MATS = {
    "Liner":            ((0.62, 0.63, 0.66), 0.3, 0.25, 0.30),
    "Piston":           ((0.82, 0.82, 0.84), 1.0, 0.30, 1.0),
    "Rod":              ((0.50, 0.50, 0.54), 1.0, 0.35, 1.0),
    "Magnet_N":         ((0.80, 0.14, 0.12), 0.6, 0.35, 1.0),
    "Magnet_S":         ((0.12, 0.28, 0.80), 0.6, 0.35, 1.0),
    "Stator_Coil":      ((0.86, 0.47, 0.24), 0.3, 0.30, 0.30),
    "LinGen_Housing":   ((0.60, 0.82, 0.95), 0.0, 0.10, 0.22),
    "Housing_Flange":   ((0.70, 0.71, 0.74), 1.0, 0.40, 1.0),
    "Intake_Belt":      ((0.25, 0.55, 0.95), 0.0, 0.20, 0.40),
    "Exhaust_Belt":     ((0.95, 0.45, 0.15), 0.0, 0.20, 0.40),
    "Intake_Pipe":      ((0.25, 0.55, 0.95), 0.6, 0.35, 1.0),
    "Exhaust_Pipe":     ((0.62, 0.30, 0.16), 0.9, 0.40, 1.0),
    "Compressor":       ((0.70, 0.80, 0.90), 0.0, 0.15, 0.25),
    "Turbine":          ((0.45, 0.38, 0.34), 0.0, 0.25, 0.30),
    "VGT_Actuator":     ((0.30, 0.28, 0.27), 1.0, 0.45, 1.0),
    "EMachine":         ((0.10, 0.10, 0.12), 0.0, 0.30, 0.35),
    "Compressor_Wheel": ((0.90, 0.91, 0.93), 1.0, 0.20, 1.0),
    "Turbine_Wheel":    ((0.62, 0.55, 0.48), 1.0, 0.35, 1.0),
    "Shaft":            ((0.75, 0.75, 0.78), 1.0, 0.20, 1.0),
    "HV_Orange":        ((1.00, 0.45, 0.05), 0.0, 0.50, 1.0),
    "Inverter":         ((0.22, 0.26, 0.30), 0.8, 0.40, 1.0),
    "Inverter_Lid":     ((0.40, 0.45, 0.50), 0.8, 0.35, 1.0),
    "Accumulator":      ((0.55, 0.62, 0.70), 0.0, 0.20, 0.18),
    "LTO_Cell":         ((0.16, 0.42, 0.55), 0.5, 0.35, 1.0),
    "Cell_Terminal":    ((0.85, 0.85, 0.88), 1.0, 0.25, 1.0),
    "Busbar":           ((0.80, 0.50, 0.25), 1.0, 0.25, 1.0),
    "Propane_Vapour":   ((0.98, 0.78, 0.10), 0.3, 0.40, 1.0),
    "Propane_Liquid":   ((0.20, 0.75, 0.35), 0.3, 0.40, 1.0),
    "Fuel_Rail":        ((0.85, 0.12, 0.12), 0.6, 0.35, 1.0),
    "Injector":         ((0.18, 0.18, 0.20), 0.8, 0.35, 1.0),
    "Printed_HX":       ((0.58, 0.60, 0.64), 0.7, 0.60, 1.0),
    "Ref_Ghost":        ((0.80, 0.82, 0.86), 0.0, 0.50, 0.10),
    "Ref_Duct":         ((0.92, 0.92, 0.92), 0.0, 0.50, 0.18),
    "Envelope":         ((1.00, 0.10, 0.10), 0.0, 0.50, 1.0),
}

# ----------------------------------------------------------- vector maths ---
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def unit(a):
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n)


class Frame:
    """Local frame whose +z is `axis`; P(x, y, z) -> world."""
    def __init__(self, origin, axis):
        d = unit(axis)
        ref = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
        self.e1 = unit(cross(d, ref))
        self.e2 = cross(d, self.e1)
        self.d, self.o = d, origin

    def P(self, x, y, z):
        return add(self.o, add(mul(self.e1, x), add(mul(self.e2, y), mul(self.d, z))))

    def Pc(self, r, th, z):
        return self.P(r * math.cos(th), r * math.sin(th), z)


class Mesh:
    def __init__(self):
        self.v, self.f, self.m, self.sm, self.e = [], [], [], [], []

    def add_verts(self, pts):
        i = len(self.v)
        self.v.extend(pts)
        return i

    def face(self, idx, mat, smooth=True):
        self.f.append(tuple(idx)); self.m.append(mat); self.sm.append(smooth)

    def poly(self, pts, mat, smooth=False):
        i = self.add_verts(pts)
        self.face(range(i, i + len(pts)), mat, smooth)


# --------------------------------------------------------------- primitives ---
def _ring(fr, r, z, n, th0):
    if r < 1e-9:
        return [fr.P(0, 0, z)]
    return [fr.Pc(r, th0 + 2 * math.pi * i / n, z) for i in range(n)]


def _join(m, A, B, n, mat):
    """Faces between two rings (index lists); handles apex rings."""
    for i in range(n):
        j = (i + 1) % n
        if len(A) == 1 and len(B) == 1:
            return
        if len(B) == 1:
            m.face((A[i], A[j], B[0]), mat)
        elif len(A) == 1:
            m.face((A[0], B[j], B[i]), mat)
        else:
            m.face((A[i], A[j], B[j], B[i]), mat)


def lathe(m, fr, prof, mat, n=48, smooth_profile=False, closed=False, th0=0.0):
    """Revolve an (r, z) profile.  CCW profile in the (r, z) plane -> outward normals.
    Each profile segment gets its own vertices unless smooth_profile (crisp edges)."""
    segs = []
    if smooth_profile:
        segs.append((prof, closed))
    else:
        k = len(prof) if closed else len(prof) - 1
        for i in range(k):
            segs.append(([prof[i], prof[(i + 1) % len(prof)]], False))
    for pts, cl in segs:
        rings = []
        for r, z in pts:
            ring = _ring(fr, r, z, n, th0)
            s = m.add_verts(ring)
            rings.append(list(range(s, s + len(ring))))
        for k in range(len(rings) - 1):
            _join(m, rings[k], rings[k + 1], n, mat)
        if cl:
            _join(m, rings[-1], rings[0], n, mat)


def cyl(m, fr, r, z0, z1, mat, n=48):
    lathe(m, fr, [(0, z0), (r, z0), (r, z1), (0, z1)], mat, n)


def tube(m, fr, ri, ro, z0, z1, mat, n=48):
    lathe(m, fr, [(ri, z0), (ro, z0), (ro, z1), (ri, z1)], mat, n, closed=True)


def torus(m, fr, R, r, z, mat, n=48, nm=14):
    prof = [(R + r * math.cos(2 * math.pi * k / nm), z + r * math.sin(2 * math.pi * k / nm)) for k in range(nm)]
    lathe(m, fr, prof, mat, n, smooth_profile=True, closed=True)


def obox(m, c, ax, h, mat):
    """Oriented box: centre c, right-handed unit axes ax[0..2], half sizes h."""
    def corner(s):
        p = c
        for k in range(3):
            p = add(p, mul(ax[k], s[k] * h[k]))
        return p
    for k in range(3):
        u, v = (k + 1) % 3, (k + 2) % 3
        for sk in (1, -1):
            pts = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                s = [0, 0, 0]; s[k], s[u], s[v] = sk, a, b
                pts.append(corner(s))
            m.poly(pts if sk > 0 else pts[::-1], mat)


def rounded(pts, rad, seg=7):
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        A, P, C = pts[k - 1], pts[k], pts[k + 1]
        d1, d2 = length(sub(A, P)), length(sub(C, P))
        u1, u2 = unit(sub(A, P)), unit(sub(C, P))
        if dot(u1, u2) < -0.999:
            out.append(P); continue
        t = min(rad, 0.45 * d1, 0.45 * d2)
        q0, q2 = add(P, mul(u1, t)), add(P, mul(u2, t))
        for i in range(seg + 1):
            s = i / seg
            out.append(add(add(mul(q0, (1 - s) ** 2), mul(P, 2 * (1 - s) * s)), mul(q2, s * s)))
    out.append(pts[-1])
    clean = [out[0]]
    for p in out[1:]:
        if length(sub(p, clean[-1])) > 1e-6:
            clean.append(p)
    return clean


def pipe(m, pts, r, mat, bend=None, n=16, caps=True):
    """Sweep a circle along a polyline with rounded corners."""
    P = rounded(pts, bend if bend is not None else 2.5 * r)
    sweep(m, P, [r] * len(P), mat, n, caps)


def sweep(m, P, R, mat, n=16, caps=True):
    """Sweep circles of radius R[k] along points P[k] (parallel-transport frames)."""
    N = len(P)
    T = []
    for k in range(N):
        a, b = P[max(k - 1, 0)], P[min(k + 1, N - 1)]
        T.append(unit(sub(b, a)))
    ref = (0, 0, 1) if abs(T[0][2]) < 0.9 else (1, 0, 0)
    e1 = unit(cross(T[0], ref))
    rings = []
    for k in range(N):
        e1 = unit(sub(e1, mul(T[k], dot(e1, T[k]))))
        e2 = cross(T[k], e1)
        r = R[k]
        ring = [add(P[k], add(mul(e1, r * math.cos(2 * math.pi * i / n)), mul(e2, r * math.sin(2 * math.pi * i / n))))
                for i in range(n)]
        s = m.add_verts(ring)
        rings.append(list(range(s, s + n)))
    for k in range(N - 1):
        _join(m, rings[k], rings[k + 1], n, mat)
    if caps:
        m.poly([m.v[i] for i in rings[0]][::-1], mat)
        m.poly([m.v[i] for i in rings[-1]], mat)


def ported_liner(m, fr, r_in, r_out, stations, port_cells, mat, n_ports, swirl_rings=(), swirl=0.4):
    """Sleeve with rings of port holes.  stations: axial z list; port_cells: indices j of
    the bands (between stations j and j+1) that are ported.  3 angular cells per port,
    2 open + 1 bridge, so holes go all the way round the bore."""
    N = n_ports * 3
    seg = 2 * math.pi / N
    O, I = [], []
    for j, z in enumerate(stations):
        O.append(m.add_verts([fr.Pc(r_out, i * seg, z) for i in range(N)]))
        off = swirl * seg if j in swirl_rings else 0.0
        I.append(m.add_verts([fr.Pc(r_in, i * seg + off, z) for i in range(N)]))

    def o(j, i): return O[j] + (i % N)
    def ii(j, i): return I[j] + (i % N)

    def is_port(j, i): return j in port_cells and (i % 3) != 2

    J = len(stations) - 1
    for j in range(J):
        for i in range(N):
            if not is_port(j, i):
                m.face((o(j, i), o(j, i + 1), o(j + 1, i + 1), o(j + 1, i)), mat)
                m.face((ii(j + 1, i), ii(j + 1, i + 1), ii(j, i + 1), ii(j, i)), mat)
                continue
            V = m.v
            m.poly([V[o(j, i)], V[o(j, i + 1)], V[ii(j, i + 1)], V[ii(j, i)]], mat)              # bottom wall
            m.poly([V[ii(j + 1, i)], V[ii(j + 1, i + 1)], V[o(j + 1, i + 1)], V[o(j + 1, i)]], mat)  # top wall
            if not is_port(j, i - 1):
                m.poly([V[o(j, i)], V[ii(j, i)], V[ii(j + 1, i)], V[o(j + 1, i)]], mat)
            if not is_port(j, i + 1):
                m.poly([V[o(j, i + 1)], V[o(j + 1, i + 1)], V[ii(j + 1, i + 1)], V[ii(j, i + 1)]], mat)
    V = m.v
    for i in range(N):   # end annuli
        m.poly([V[ii(0, i)], V[ii(0, i + 1)], V[o(0, i + 1)], V[o(0, i)]], mat)
        m.poly([V[o(J, i)], V[o(J, i + 1)], V[ii(J, i + 1)], V[ii(J, i)]], mat)


def scroll(m, fr, zc, R0, r_small, r_big, th_big, mat, kind, straight=0.08, n_th=48):
    """Volute scroll in the plane z = zc of frame fr.  Flow always swirls in +theta
    (the shaft's rotation direction).  Centreline radius = R0 + r so the inner edge
    stays on the diffuser / nozzle ring at R0.
      kind 'compressor': section grows from the tongue to th_big, then a straight
                         tangential DISCHARGE continues downstream (+theta).
      kind 'turbine':    a straight tangential INLET feeds th_big, section shrinks
                         toward the tongue one turn later."""
    tongue = 0.35
    if kind == "compressor":
        ths = [th_big - (2 * math.pi - tongue) * (1 - k / n_th) for k in range(n_th + 1)]
        rs = [r_small + (r_big - r_small) * (k / n_th) for k in range(n_th + 1)]
    else:
        ths = [th_big + (2 * math.pi - tongue) * (k / n_th) for k in range(n_th + 1)]
        rs = [r_big - (r_big - r_small) * (k / n_th) for k in range(n_th + 1)]
    P = [fr.Pc(R0 + r, th, zc) for th, r in zip(ths, rs)]
    et = add(mul(fr.e1, -math.sin(th_big)), mul(fr.e2, math.cos(th_big)))
    big = fr.Pc(R0 + r_big, th_big, zc)
    if kind == "compressor":
        P += [add(big, mul(et, straight * k / 3)) for k in range(1, 4)]
        rs += [r_big] * 3
        port = add(big, mul(et, straight))
    else:
        P = [add(big, mul(et, -straight * (3 - k) / 3)) for k in range(3)] + P
        rs = [r_big] * 3 + rs
        port = add(big, mul(et, -straight))
    sweep(m, P, rs, mat, n=20)
    return port, et


def blade_set(m, fr, nb, zs, rh, rt, dth, thick, mat):
    """Curved radial-turbomachine blades: per axial station, hub radius rh, tip radius
    rt and angular offset dth (radians, + = direction of rotation)."""
    for b in range(nb):
        th0 = 2 * math.pi * b / nb
        rings = []
        for z, a, c, t in zip(zs, rh, rt, dth):
            th = th0 + t
            er = add(mul(fr.e1, math.cos(th)), mul(fr.e2, math.sin(th)))
            et = add(mul(fr.e1, -math.sin(th)), mul(fr.e2, math.cos(th)))
            base = fr.P(0, 0, z)
            pts = [add(add(base, mul(er, rr)), mul(et, s * thick / 2)) for rr, s in ((a, -1), (c, -1), (c, 1), (a, 1))]
            st = m.add_verts(pts)
            rings.append(list(range(st, st + 4)))
        for k in range(len(rings) - 1):
            _join(m, rings[k], rings[k + 1], 4, mat)
        m.poly([m.v[i] for i in rings[0]][::-1], mat)
        m.poly([m.v[i] for i in rings[-1]], mat)


def vane(m, fr, th, r0, r1, z_le, chord, tmax, camber, mat, np_=10):
    """Thick cambered stator vane (internal propane channels are implied by the thickness).
    Leading edge turned against the rotor swirl, trailing edge axial."""
    er = add(mul(fr.e1, math.cos(th)), mul(fr.e2, math.sin(th)))
    et = add(mul(fr.e1, -math.sin(th)), mul(fr.e2, math.cos(th)))
    xs = [0.5 * (1 - math.cos(math.pi * k / np_)) for k in range(np_ + 1)]

    def half_t(x):
        x = max(x, 0.0)
        return 5 * tmax * chord * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)

    sec = [(x, camber * chord * (1 - x) ** 2 + half_t(x)) for x in xs[::-1]]
    sec += [(x, camber * chord * (1 - x) ** 2 - half_t(x)) for x in xs[1:-1]]

    def pt(r, x, t):
        return add(fr.o, add(mul(er, r), add(mul(et, t), mul(fr.d, z_le + x * chord))))
    rings = []
    for r in (r0, r1):
        s = m.add_verts([pt(r, x, t) for x, t in sec])
        rings.append(list(range(s, s + len(sec))))
    n = len(sec)
    for i in range(n):
        j = (i + 1) % n
        m.face((rings[0][i], rings[0][j], rings[1][j], rings[1][i]), mat)
    m.poly([m.v[i] for i in rings[0]][::-1], mat)
    m.poly([m.v[i] for i in rings[1]], mat)


# ----------------------------------------------------------------- geometry ---
class Obj:
    def __init__(self, name, coll, origin=(0, 0, 0), driver=None, travel=None, display=None,
                 driver_path="location", driver_index=1):
        self.name, self.coll, self.origin = name, coll, origin
        self.mesh, self.driver, self.travel, self.display = Mesh(), driver, travel, display
        self.driver_path, self.driver_index = driver_path, driver_index


def design(preset):
    p = PRESETS[preset]
    B, S = p["bore"], p["stroke"]
    d = dict(B=B, S=S)
    d["g"] = 0.006                          # crown offset from centre at inner dead centre
    d["Lp"] = 0.75 * B                      # piston length
    d["t_liner"] = max(0.006, 0.07 * B)
    d["r_li"], d["r_lo"] = B / 2, B / 2 + d["t_liner"]
    d["crown_bdc"] = d["g"] + S
    d["h_ex"], d["h_in"] = 0.30 * S, 0.24 * S          # exhaust ports taller (blowdown)
    d["L_l"] = d["crown_bdc"] + d["Lp"] + 0.012         # liner half length
    d["Lgap"] = S + 0.03                                # crown-to-magnet spacing: magnets never enter liner
    d["Lm"] = 0.14                                      # translator (magnet) length
    d["r_mo"] = B / 2 + 0.020
    d["r_mi"] = d["r_mo"] - 0.022
    d["r_rod"] = 0.16 * B
    d["ts"] = d["g"] + d["Lp"] + d["Lgap"]              # translator start at inner dead centre
    d["t0"], d["t1"] = d["ts"] - 0.005, d["ts"] + S + d["Lm"] + 0.005    # stator coil span
    d["r_ci"] = d["r_mo"] + 0.003                       # 3 mm air gap
    d["r_co"] = d["r_ci"] + 0.5 * B
    d["r_hi"] = d["r_co"] + 0.004
    d["r_ho"] = d["r_hi"] + 0.004
    d["h0"] = d["crown_bdc"] + 0.03                     # linear-generator housing seals onto liner here
    d["h1"] = d["t1"] + 0.03
    d["END"] = d["h1"] + 0.012                          # outer face of end cap
    d["r_b"] = d["r_lo"] + 0.03                         # port belt outer radius
    # TRANSVERSE layout: cylinder axes along X (pistons move side to side),
    # the three cylinders stacked fore-aft, e-turbo behind them on the same shaft line as before
    d["flange_r"] = d["r_ho"] + 0.004
    d["pitch"] = max(0.30, 2 * d["flange_r"] + 0.03)
    y0 = ENV["y"][0] + 0.005 + d["flange_r"]
    d["cyl_y"] = [y0 + k * d["pitch"] for k in range(3)]
    d["y_A"] = d["cyl_y"][2] + d["flange_r"]           # aft face of the cylinder bank
    # ---- gas-path sizing for 2,000 hp peak (approximate, for packaging)
    P_kw = 2000 * 0.7457
    d["m_fuel"] = P_kw / 0.55 / 46350.0                 # propane, 55 % BTE at peak, LHV 46.35 MJ/kg
    d["m_air"] = d["m_fuel"] * 15.67 * 1.20 * 1.35      # stoich AFR x trapped lambda 1.2 x scavenge delivery 1.35
    d["m_exh"] = d["m_air"] + d["m_fuel"]
    d["r_cin"] = 0.075                                  # compressor inlet  150 mm
    d["r_ca"] = 0.055                                   # charge air + pre-turbine pipes  110 mm
    d["r_dp"] = 0.090                                   # downpipe / tailpipe  180 mm
    d["pl_w"], d["pl_h"] = None, None                   # plenum box section, set below
    d["scroll_R0"], d["scroll_rbig"] = 0.060, d["r_ca"]   # volute inner radius; discharge / inlet = pipe size
    d["turbo_r"] = d["scroll_R0"] + 2 * d["scroll_rbig"]
    d["y_D"] = d["y_A"] + d["r_ca"] + 0.005             # cross-over lane between bank and turbo
    d["y_T"] = d["y_D"] + d["r_ca"] + 0.008 + d["turbo_r"]   # turbo shaft line
    # plenum / collector boxes run fore-aft over the port belts, between the generator housings
    d["Z_BUS"] = 0.988
    d["px_in"], d["px_out"] = 0.020, d["h0"] - 0.008 - 0.006
    d["pz_bot"], d["pz_top"] = Z_C + d["r_b"] - 0.004, d["Z_BUS"] - 0.010 - 0.005
    d["pl_w"], d["pl_h"] = d["px_out"] - d["px_in"], d["pz_top"] - d["pz_bot"]
    d["px_c"], d["pz_c"] = 0.5 * (d["px_in"] + d["px_out"]), 0.5 * (d["pz_bot"] + d["pz_top"])
    d["hdr_r"] = 0.020
    d["u_vp"] = d["h1"] - 0.03                          # vapour port, on top of each linear-generator housing
    d["z_hdr"] = Z_C + d["r_ho"] + 0.03                 # vapour headers run fore-aft above the bank
    d["u_liq"] = d["t0"] + 0.02                         # stator liquid inlet, top, inboard of the inverter
    d["z_liq"] = Z_C + d["r_ho"] + 0.025                # liquid feed headers above the bank
    d["x_in"] = -(d["crown_bdc"] - d["h_in"] / 2)       # intake ring on the right (-X, compressor side)
    d["x_ex"] = d["crown_bdc"] - d["h_ex"] / 2          # exhaust ring on the left (+X, turbine side)
    d["u_cm"] = 0.5 * (d["t0"] + d["t1"])
    A = math.pi * B * B / 4
    d["disp_cyl"] = 2 * A * S
    d["disp"] = 3 * d["disp_cyl"]
    # linear-generator housing gas volume (one side), at inner and outer dead centre
    v_house = math.pi * d["r_hi"] ** 2 * (d["h1"] - d["h0"]) - math.pi * d["r_lo"] ** 2 * (d["L_l"] - d["h0"])
    v_bore = math.pi * d["r_li"] ** 2 * (d["L_l"] - (d["g"] + d["Lp"]))
    v_coil = math.pi * (d["r_co"] ** 2 - d["r_ci"] ** 2) * (d["t1"] - d["t0"])
    v_moving = math.pi * (d["r_mo"] ** 2 - d["r_mi"] ** 2) * d["Lm"] + 2 * math.pi * d["r_mi"] ** 2 * 0.006 \
        + math.pi * d["r_rod"] ** 2 * (d["ts"] - d["g"] - d["Lp"])
    d["Vb_max"] = v_house + v_bore - v_coil - v_moving
    d["Vb_min"] = d["Vb_max"] - A * S
    return d


def build(preset=PRESET):
    d = design(preset)
    B, S = d["B"], d["S"]
    objs = []

    def new(name, coll, **kw):
        o = Obj(name, coll, **kw)
        objs.append(o)
        return o

    w = 2 * math.pi / 24.0      # one engine cycle = 24 frames
    for ci, yc in enumerate(d["cyl_y"]):
        tag = f"Cyl{ci + 1}"
        C = (0.0, yc, Z_C)
        fr = Frame(C, (1, 0, 0))                   # cylinder axis across the airframe
        phi = ci * 2 * math.pi / 3

        # sleeve with port rings (intake on -X, exhaust on +X)
        cb = d["crown_bdc"]
        st = [-d["L_l"], -(cb + 0.002), -(cb - d["h_in"]), cb - d["h_ex"], cb + 0.002, d["L_l"]]
        o = new(f"OPF_{tag}_Sleeve", "OPFPLG_Core")
        ported_liner(o.mesh, fr, d["r_li"], d["r_lo"], st, (1, 3), "Liner", N_PORTS, swirl_rings=(1, 2))

        # port belts (scavenge / exhaust plenums around the port rings)
        o = new(f"OPF_{tag}_Intake_Belt", "OPFPLG_Core")
        tube(o.mesh, fr, d["r_lo"] + 0.0005, d["r_b"], -(cb + 0.008), -(cb - d["h_in"] - 0.006), "Intake_Belt")
        o = new(f"OPF_{tag}_Exhaust_Belt", "OPFPLG_Core")
        tube(o.mesh, fr, d["r_lo"] + 0.0005, d["r_b"], cb - d["h_ex"] - 0.006, cb + 0.008, "Exhaust_Belt")

        # DI injectors at the inner-dead-centre plane (tilted fore and aft), fed from the rail
        o = new(f"OPF_{tag}_Injectors", "OPFPLG_Core")
        for a in (-0.70, 0.70):
            dvec = (0.0, math.sin(a), math.cos(a))
            p0 = add(C, mul(dvec, d["r_lo"]))
            p1 = add(C, mul(dvec, d["r_lo"] + 0.075))
            pipe(o.mesh, [p0, p1], 0.008, "Injector")
            pipe(o.mesh, [p1, (0.0, p1[1], 0.905)], 0.004, "Fuel_Rail")

        for s, side in ((-1, "Intake"), (1, "Exhaust")):
            def zz(u0, u1):
                return (min(s * u0, s * u1), max(s * u0, s * u1))

            # moving assembly: piston + rod + Halbach translator, driven along X
            lead = math.radians(EXHAUST_LEAD_DEG) if s > 0 else 0.0
            expr = f"{'' if s > 0 else '-'}{S / 2:.5f}*(1-cos(frame*{w:.6f}+{phi + lead - w:.5f}))"
            o = new(f"OPF_{tag}_Piston_{side}", "OPFPLG_Generator", origin=C,
                    driver=expr, driver_index=0, travel=(s * S, 0, 0))
            z0, z1 = zz(d["g"], d["g"] + d["Lp"])
            cyl(o.mesh, fr, d["r_li"] - 0.0005, z0, z1, "Piston")
            for k in range(2):                         # ring lands
                u = d["g"] + 0.008 + 0.006 * k
                a0, a1 = zz(u, u + 0.002)
                tube(o.mesh, fr, d["r_li"] - 0.0035, d["r_li"] - 0.0004, a0, a1, "Rod")
            z0, z1 = zz(d["g"] + d["Lp"], d["ts"] + 0.003)
            cyl(o.mesh, fr, d["r_rod"], z0, z1, "Rod", n=24)
            for u in (d["ts"], d["ts"] + d["Lm"] - 0.006):
                z0, z1 = zz(u, u + 0.006)
                cyl(o.mesh, fr, d["r_mi"] + 0.001, z0, z1, "Rod")
            nr = 8
            for k in range(nr):
                z0, z1 = zz(d["ts"] + k * d["Lm"] / nr, d["ts"] + (k + 1) * d["Lm"] / nr)
                tube(o.mesh, fr, d["r_mi"], d["r_mo"], z0, z1, "Magnet_N" if k % 2 == 0 else "Magnet_S")

            # stator: plain hollow cylinder
            o = new(f"OPF_{tag}_Stator_{side}", "OPFPLG_Generator")
            z0, z1 = zz(d["t0"], d["t1"])
            tube(o.mesh, fr, d["r_ci"], d["r_co"], z0, z1, "Stator_Coil")

            # linear generator housing = sealed gas volume under the piston, around translator + stator
            o = new(f"OPF_{tag}_LinearGenerator_{side}", "OPFPLG_Core")
            z0, z1 = zz(d["h0"], d["h1"])
            tube(o.mesh, fr, d["r_hi"], d["r_ho"], z0, z1, "LinGen_Housing")
            z0, z1 = zz(d["h1"], d["END"])
            cyl(o.mesh, fr, d["r_ho"], z0, z1, "LinGen_Housing")
            o = new(f"OPF_{tag}_Flange_{side}", "OPFPLG_Core")
            z0, z1 = zz(d["h0"] - 0.008, d["h0"])
            tube(o.mesh, fr, d["r_lo"], d["flange_r"], z0, z1, "Housing_Flange")

            # vapour port on top of the linear-generator housing -> header; liquid feed into stator
            o = new(f"OPF_{tag}_Coolant_Ports_{side}", "OPFPLG_Cooling")
            pipe(o.mesh, [(s * d["u_vp"], yc, Z_C + d["r_ho"] - 0.003), (s * d["u_vp"], yc, d["z_hdr"])],
                 0.013, "Propane_Vapour")
            pipe(o.mesh, [(s * d["u_liq"], yc, Z_C + d["r_ho"] - 0.003), (s * d["u_liq"], yc, d["z_liq"])],
                 0.010, "Propane_Liquid")

    # ---- electric turbo-compound unit: compressor | motor-generator | turbine
    # Shaft spins +X (right-hand rule): the top of every wheel moves FORWARD (-Y).
    #   compressor: air enters axially from the right-hand side (-X), inducer pitched to
    #               pull it in, scroll grows with rotation, tangential discharge on top
    #               heading forward -> intake plenum
    #   turbine:    exhaust enters tangentially at the bottom heading aft (same swirl as
    #               rotation), scroll shrinks to the tongue, exducer exits axially (+X)
    yT = d["y_T"]
    R0, rbig = d["scroll_R0"], d["scroll_rbig"]
    tf = Frame((0.0, yT, Z_C), (1, 0, 0))
    TOP, BOTTOM = -math.pi / 2, math.pi / 2          # theta of world +Z / -Z in this frame
    NS = 12
    ss = [k / NS for k in range(NS + 1)]
    # compressor wheel stations (inducer at -0.335 -> exducer at -0.273)
    c_z = [-0.335 + 0.062 * s for s in ss]
    c_rh = [0.013 + 0.039 * s ** 2 for s in ss]
    c_rt = [0.042 + 0.016 * s ** 1.6 for s in ss]
    c_dth = [0.75 * (1 - s) ** 2 - 0.20 * s ** 2 for s in ss]      # leading edge ahead, exducer backswept
    # turbine wheel stations (radial inlet at 0.270 -> exducer at 0.335)
    t_z = [0.270 + 0.065 * s for s in ss]
    t_rh = [0.013 + 0.039 * (1 - s) ** 2 for s in ss]
    t_rt = [0.056 - 0.008 * s ** 1.5 for s in ss]
    t_dth = [-0.65 * s ** 2 for s in ss]                          # exducer trails rotation

    o = new("OPF_ETurbo_Rotor", "OPFPLG_Air", origin=(0.0, yT, Z_C),
            driver=f"frame*{TURBO_SPIN_RAD_PER_FRAME:.4f}", driver_path="rotation_euler", driver_index=0)
    cyl(o.mesh, tf, 0.012, -0.345, 0.345, "Shaft", n=20)
    cyl(o.mesh, tf, 0.055, -0.11, 0.11, "Magnet_N", n=32)                      # e-machine rotor
    for k in range(4):                                                         # stripes show rotation
        th = k * math.pi / 2
        er = add(mul(tf.e1, math.cos(th)), mul(tf.e2, math.sin(th)))
        et = add(mul(tf.e1, -math.sin(th)), mul(tf.e2, math.cos(th)))
        obox(o.mesh, add(tf.P(0, 0, 0), mul(er, 0.056)), (er, et, tf.d), (0.002, 0.012, 0.108), "Magnet_S")
    lathe(o.mesh, tf, [(0, -0.338), (0.012, -0.338)] + [(r, z) for r, z in zip(c_rh, c_z)] +
          [(0.056, -0.268), (0, -0.268)], "Compressor_Wheel", n=40, smooth_profile=True)
    cyl(o.mesh, tf, 0.010, -0.350, -0.338, "Shaft", n=6)                        # wheel nut
    blade_set(o.mesh, tf, 8, c_z, c_rh, c_rt, c_dth, 0.0016, "Compressor_Wheel")
    k0 = NS // 3                                                               # splitter blades
    blade_set(o.mesh, tf, 8, c_z[k0:], c_rh[k0:], c_rt[k0:],
              [t + math.pi / 8 for t in c_dth[k0:]], 0.0014, "Compressor_Wheel")
    lathe(o.mesh, tf, [(0, 0.266), (0.054, 0.266)] + [(r, z) for r, z in zip(t_rh, t_z)] +
          [(0.012, 0.338), (0, 0.338)], "Turbine_Wheel", n=40, smooth_profile=True)
    blade_set(o.mesh, tf, 11, t_z, t_rh, t_rt, t_dth, 0.0018, "Turbine_Wheel")

    o = new("OPF_ETurbo_Bearings", "OPFPLG_Air")
    for a, b in ((-0.25, -0.15), (0.15, 0.25)):
        tube(o.mesh, tf, 0.014, 0.035, a, b, "Housing_Flange", n=32)
    o = new("OPF_ETurbo_MotorGenerator_Case", "OPFPLG_Air")
    tube(o.mesh, tf, 0.060, 0.075, -0.13, 0.13, "EMachine")
    for z0_, z1_ in ((-0.15, -0.13), (0.13, 0.15)):
        tube(o.mesh, tf, 0.014, 0.075, z0_, z1_, "EMachine")
    for k in range(9):
        z = -0.10 + k * 0.025
        tube(o.mesh, tf, 0.075, 0.086, z - 0.003, z + 0.003, "EMachine")
    obox(o.mesh, (0.0, yT, Z_C + 0.085), ((1, 0, 0), (0, 1, 0), (0, 0, 1)), (0.04, 0.03, 0.015), "HV_Orange")

    o = new("OPF_ETurbo_Compressor_Housing", "OPFPLG_Air")
    rci = d["r_cin"]
    torus(o.mesh, tf, rci + 0.012, 0.012, -0.48, "Compressor", nm=10)         # bellmouth lip
    tube(o.mesh, tf, rci, rci + 0.004, -0.48, -0.40, "Compressor")             # 150 mm inlet duct
    lathe(o.mesh, tf, [(rci, -0.40), (0.052, -0.36), (0.045, -0.340)] + [(r + 0.002, z) for r, z in zip(c_rt, c_z)] +
          [(R0, -0.277)], "Compressor", n=48, smooth_profile=True)               # inlet cone + contoured shroud
    tube(o.mesh, tf, 0.036, R0 + 0.003, -0.265, -0.261, "Compressor")         # back plate (diffuser wall)
    c_port, c_dir = scroll(o.mesh, tf, -0.271, R0, 0.009, rbig, TOP, "Compressor", "compressor")

    o = new("OPF_ETurbo_Turbine_Housing_VGT", "OPFPLG_Air")
    tube(o.mesh, tf, 0.036, R0 + 0.003, 0.262, 0.266, "Turbine")              # heat shield / back wall
    lathe(o.mesh, tf, [(R0, 0.277)] + [(r + 0.002, z) for r, z in zip(t_rt, t_z)] +
          [(0.054, 0.350), (0.075, 0.40)], "Turbine", n=48, smooth_profile=True)      # shroud + exducer cone to 150 mm
    t_port, t_dir = scroll(o.mesh, tf, 0.272, R0, 0.009, rbig, BOTTOM, "Turbine", "turbine")
    o = new("OPF_ETurbo_VGT_Actuator", "OPFPLG_Air")
    obox(o.mesh, (0.30, yT + 0.02, Z_C + d["turbo_r"] + 0.022), ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         (0.025, 0.035, 0.014), "VGT_Actuator")

    # ---- intake / exhaust manifolds (inside the bay), plumbed to the scroll ports
    # Each is a box plenum (about 100 x 110 mm, ~ a 118 mm pipe) sitting on its port belts and
    # running fore-aft between the generator housings, then a 110 mm cross-over to the turbo.
    X3b = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    yD, y_first = d["y_D"], d["cyl_y"][0]
    pyf, pya = y_first - 0.07, d["y_A"] + 0.01
    pc = ((pyf + pya) / 2, (pya - pyf) / 2)
    xco = d["px_c"] + 0.010                              # cross-over centre, nudged outboard
    zc = d["pz_c"]
    rca = d["r_ca"]
    o = new("OPF_Intake_Manifold", "OPFPLG_Air")
    obox(o.mesh, (-d["px_c"], pc[0], zc), X3b, (d["pl_w"] / 2, pc[1], d["pl_h"] / 2), "Intake_Pipe")
    # compressor discharge (top, heading forward) -> cross-over lane -> plenum
    pipe(o.mesh, [c_port, (c_port[0], yD, zc), (-xco, yD, zc), (-xco, d["y_A"] - 0.01, zc)],
         rca, "Intake_Pipe", bend=0.07)
    o = new("OPF_Exhaust_Collector", "OPFPLG_Air")
    obox(o.mesh, (d["px_c"], pc[0], zc), X3b, (d["pl_w"] / 2, pc[1], d["pl_h"] / 2), "Exhaust_Pipe")
    # collector -> cross-over lane -> drops to the turbine's bottom tangential inlet
    pipe(o.mesh, [(xco, d["y_A"] - 0.01, zc), (xco, yD, zc), (t_port[0], yD, zc),
                  (t_port[0], yD, t_port[2]), t_port], rca, "Exhaust_Pipe", bend=0.07)
    o = new("OPF_Fuel_Rail", "OPFPLG_Core")
    pipe(o.mesh, [(0.0, y_first - 0.12, 0.905), (0.0, d["cyl_y"][2] + 0.12, 0.905)], 0.008, "Fuel_Rail")
    d["c_port"], d["t_port"] = c_port, t_port

    # ---- propane cooling: headers, receiver, distribution (inside the bay)
    o = new("OPF_Vapour_Headers", "OPFPLG_Cooling")
    for sgn in (-1, 1):            # one header per side, collecting all three linear-generator housings
        pipe(o.mesh, [(sgn * d["u_vp"], y_first - 0.03, d["z_hdr"]), (sgn * d["u_vp"], d["cyl_y"][2], d["z_hdr"])],
             d["hdr_r"], "Propane_Vapour")
    o = new("OPF_Propane_Receiver", "OPFPLG_Cooling")
    cyl(o.mesh, tf, 0.04, -0.15, 0.15, "Propane_Liquid", n=32)
    for k in range(len(o.mesh.v)):              # receiver sits under the turbo
        x, y, z = o.mesh.v[k]
        o.mesh.v[k] = (x, y, z - (Z_C - 0.60))
    # stator liquid feed, all above the bank: receiver -> riser just aft of the motor-generator
    # -> forward along x = 0 between the plenums -> cross-bar ahead of cylinder 1 -> one header
    # per side running aft -> drop into each stator top
    o = new("OPF_Stator_Liquid_Feed", "OPFPLG_Cooling")
    u, zl, z_tr = d["u_liq"], d["z_liq"], 0.950
    y_front = y_first - 0.07 - 0.025
    y_rise = yT + 0.11
    pipe(o.mesh, [(0.0, yT + 0.04, 0.60), (0.0, y_rise, 0.60), (0.0, y_rise, z_tr), (0.0, y_front, z_tr)],
         0.012, "Propane_Liquid", bend=0.04)
    pipe(o.mesh, [(-u, y_front, z_tr), (u, y_front, z_tr)], 0.012, "Propane_Liquid")
    for sgn in (-1, 1):
        pipe(o.mesh, [(sgn * u, y_front, z_tr), (sgn * u, y_first, zl), (sgn * u, d["cyl_y"][2], zl)],
             0.010, "Propane_Liquid", bend=0.04)

    # ---- external: vapour lines to the fan heat exchangers, liquid return, exhaust
    ZV, top_ring = 1.05, PUSHER_Z + 0.365
    yv_in, yv_out = PUSHER_Y + 0.045, PUSHER_Y + 0.165
    for sgn, side in ((1, "L"), (-1, "R")):
        xh = sgn * d["u_vp"]
        o = new(f"OPF_Ext_Vapour_Line_{side}", "OPFPLG_External")
        pipe(o.mesh, [(xh, d["cyl_y"][2], d["z_hdr"]), (xh, d["cyl_y"][2] + 0.08, ZV), (xh, 1.70, ZV),
                      (sgn * PUSHER_X, 2.05, top_ring), (sgn * PUSHER_X, yv_in, top_ring)],
             0.020, "Propane_Vapour", bend=0.10)
    bot_ring = PUSHER_Z - 0.365
    for sgn, side in ((1, "L"), (-1, "R")):
        o = new(f"OPF_Ext_Liquid_Return_{side}", "OPFPLG_External")
        pipe(o.mesh, [(sgn * PUSHER_X, yv_out, bot_ring), (sgn * PUSHER_X, 2.05, bot_ring),
                      (sgn * 0.30, 1.75, 0.575), (sgn * 0.25, yT + 0.08, 0.575), (sgn * 0.155, yT, 0.60)],
             0.014, "Propane_Liquid", bend=0.10)
    # tailpipe exits under the fuselage 1.80 m aft (about 0.3 m behind the bay, ahead of the pushers)
    Y_EXH = 1.80
    x_exh = 0.30 + (0.22 - 0.30) * (Y_EXH - (yT + 0.32)) / (2.85 - (yT + 0.32))
    o = new("OPF_Ext_Exhaust_Downpipe", "OPFPLG_External")
    pipe(o.mesh, [(0.39, yT, Z_C), (0.47, yT, Z_C), (0.48, yT + 0.12, 0.62), (0.32, yT + 0.34, 0.42),
                  (x_exh, Y_EXH, 0.42)], d["r_dp"], "Exhaust_Pipe", bend=0.14)

    # ---- power electronics: one inverter per stator coil, common DC bus, single HV feed
    X3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    Z_BUS, R_BUS = d["Z_BUS"], 0.010
    inv_l, inv_w, inv_h = min(0.15, d["t1"] - d["t0"] - 0.04), min(0.11, 2 * d["r_ho"] - 0.06), 0.034
    o = new("OPF_Inverters", "OPFPLG_Electrical")
    for yc in d["cyl_y"]:
        for sgn in (-1, 1):
            xc = sgn * d["u_cm"]
            z_mount = Z_C + d["r_ho"]
            obox(o.mesh, (xc, yc, z_mount - 0.004), X3, (inv_l / 2 - 0.01, 0.025, 0.008), "Inverter")       # saddle
            obox(o.mesh, (xc, yc, z_mount + 0.004 + inv_h / 2), X3, (inv_l / 2, inv_w / 2, inv_h / 2), "Inverter")
            obox(o.mesh, (xc, yc, z_mount + 0.004 + inv_h + 0.002), X3, (inv_l / 2 - 0.006, inv_w / 2 - 0.006, 0.002),
                 "Inverter_Lid")
            for k in (-1, 0, 1):                                               # 3-phase leads into the stator
                pipe(o.mesh, [(xc + k * 0.025, yc - inv_w / 2 + 0.005, z_mount + 0.012),
                              (xc + k * 0.025, yc - inv_w / 2 - 0.006, z_mount + 0.004),
                              (xc + k * 0.025, yc - inv_w / 2 - 0.006, z_mount - 0.006)], 0.004, "Stator_Coil", bend=0.006)
            top = z_mount + 0.004 + inv_h + 0.004
            pipe(o.mesh, [(xc, yc, top), (xc, yc, Z_BUS)], 0.006, "HV_Orange")       # DC link -> bus
    y_mid = 0.5 * (d["cyl_y"][0] + d["cyl_y"][1])
    o = new("OPF_DC_Bus", "OPFPLG_Electrical")
    for sgn in (-1, 1):
        pipe(o.mesh, [(sgn * d["u_cm"], d["cyl_y"][0], Z_BUS), (sgn * d["u_cm"], d["cyl_y"][2], Z_BUS)], R_BUS, "HV_Orange")
    pipe(o.mesh, [(-d["u_cm"], y_mid, Z_BUS), (d["u_cm"], y_mid, Z_BUS)], R_BUS, "HV_Orange")
    acc_top = ACC_TOP
    x_feed = 0.5 * (d["px_out"] + d["u_liq"] - 0.010)   # midway between exhaust plenum and liquid header
    o = new("OPF_HV_Main_Feed", "OPFPLG_Electrical")
    pipe(o.mesh, [(x_feed, y_mid, Z_BUS), (x_feed, y_mid, acc_top + 0.03)], 0.012, "HV_Orange")
    obox(o.mesh, (x_feed, y_mid, acc_top + 0.015), X3, (0.03, 0.025, 0.015), "HV_Orange")   # accumulator connector
    d["y_feed"], d["x_feed"] = y_mid, x_feed

    # ---- accumulator: 162S LTO power pack in a rectangular case
    o = new("OPF_Accumulator_Case", "OPFPLG_Accumulator")
    obox(o.mesh, ACC_C, X3, (ACC_W / 2, ACC_L / 2, ACC_H / 2), "Accumulator")
    o = new("OPF_Accumulator_Cells", "OPFPLG_Accumulator")
    cw, ct, ch = LTO_CELL
    x0 = -ACC_W / 2 + LTO_WALL + LTO_CLR + LTO_END + cw / 2
    y0c = ACC_Y0 + LTO_WALL + LTO_CLR + LTO_END + LTO_PITCH_Y / 2
    zc = ACC_TOP - ACC_H + LTO_WALL + LTO_CLR + ch / 2
    for i in range(LTO_NX):
        xc = x0 + i * (cw + LTO_GAP_X)
        for j in range(LTO_NY):
            yc = y0c + j * LTO_PITCH_Y
            obox(o.mesh, (xc, yc, zc), X3, (cw / 2, ct / 2, ch / 2), "LTO_Cell")
            for k in (-1, 1):
                obox(o.mesh, (xc + k * 0.035, yc, zc + ch / 2 + 0.003), X3, (0.011, 0.007, 0.003), "Cell_Terminal")
    o = new("OPF_Accumulator_Busbars", "OPFPLG_Accumulator")
    zb = zc + ch / 2 + 0.007
    for i in range(LTO_NX):
        xc = x0 + i * (cw + LTO_GAP_X)
        for k in (-1, 1):
            obox(o.mesh, (xc + k * 0.035, y0c + (LTO_NY - 1) * LTO_PITCH_Y / 2, zb), X3,
                 (0.012, (LTO_NY - 1) * LTO_PITCH_Y / 2 + 0.008, 0.001), "Busbar")
    d["acc"] = dict(n=LTO_NX * LTO_NY, kwh=LTO_NX * LTO_NY * 0.046, kg=LTO_NX * LTO_NY * 0.545,
                    kw10=LTO_NX * LTO_NY * 1.9, v_nom=LTO_NX * LTO_NY * 2.3)

    # ---- 3D-printed heat exchangers behind the pusher fans (stator vanes = condenser)
    for sgn, side in ((1, "L"), (-1, "R")):
        df = Frame((sgn * PUSHER_X, PUSHER_Y, PUSHER_Z), (0, 1, 0))
        o = new(f"OPF_Fan_HX_{side}", "OPFPLG_Radiators")
        z_le, chord = 0.05, 0.11
        for k in range(N_STATOR_VANES):
            th = 2 * math.pi * k / N_STATOR_VANES + 0.12
            vane(o.mesh, df, th, PUSHER_HUB_R + 0.002, 0.360, z_le, chord, 0.15, sgn * 0.18, "Printed_HX")
        torus(o.mesh, df, 0.365, 0.017, z_le - 0.005, "Propane_Vapour", n=64)      # vapour-in ring
        torus(o.mesh, df, 0.365, 0.017, z_le + chord + 0.005, "Propane_Liquid", n=64)  # condensate ring
        tube(o.mesh, df, PUSHER_HUB_R - 0.004, PUSHER_HUB_R + 0.003, z_le - 0.01, z_le + chord + 0.01, "Printed_HX")
        for k in range(60):                                  # wall fins (duct bore as extra surface)
            th = 2 * math.pi * (k + 0.5) / 60
            er = add(mul(df.e1, math.cos(th)), mul(df.e2, math.sin(th)))
            et = add(mul(df.e1, -math.sin(th)), mul(df.e2, math.cos(th)))
            c = add(df.P(0, 0, z_le + chord / 2), mul(er, PUSHER_R0 - 0.007))
            obox(o.mesh, c, (er, et, df.d), (0.007, 0.0008, chord / 2 + 0.01), "Printed_HX")

    # ---- lower the engine and accumulator by ENGINE_DZ. The exhaust downpipe moves with them; the
    #      external propane lines move fully in the bay and blend back to the fixed pusher heat exchangers
    if ENGINE_DZ:
        for o in objs:
            if o.coll == "OPFPLG_Radiators":
                continue
            if o.coll == "OPFPLG_External" and "Downpipe" not in o.name:
                o.mesh.v = [(v[0], v[1], v[2] + ENGINE_DZ * _line_w(v[1])) for v in o.mesh.v]
                continue
            o.mesh.v = [(v[0], v[1], v[2] + ENGINE_DZ) for v in o.mesh.v]
            o.origin = (o.origin[0], o.origin[1], o.origin[2] + ENGINE_DZ)
    return d, objs


def _line_w(y, y0=1.50, y1=2.10):
    """1 in the engine bay, easing to 0 at the pusher heat exchangers."""
    u = min(1.0, max(0.0, (y - y0) / (y1 - y0)))
    return 1 - u * u * (3 - 2 * u)


def reference_objects():
    objs = []
    o = Obj("OPF_REF_Bay_Envelope", "OPFPLG_Reference", display="WIRE")
    x0, x1 = ENV["x"]; y0, y1 = ENV["y"]; z0, z1 = ENV["z"]
    c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    o.mesh.v = c
    o.mesh.e = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    objs.append(o)
    for sgn, side in ((1, "L"), (-1, "R")):
        df = Frame((sgn * PUSHER_X, PUSHER_Y, PUSHER_Z), (0, 1, 0))
        o = Obj(f"OPF_REF_Pusher_Duct_{side}", "OPFPLG_Reference", display="WIRE")
        tube(o.mesh, df, PUSHER_R0, PUSHER_R1, -PUSHER_HL, PUSHER_HL, "Ref_Duct", n=64)
        cyl(o.mesh, df, PUSHER_HUB_R, 0.0, PUSHER_HUB_L, "Ref_Duct")
        tube(o.mesh, df, PUSHER_HUB_R, PUSHER_R0 - 0.01, PUSHER_ROTOR_Z - 0.004, PUSHER_ROTOR_Z + 0.004, "Ref_Duct", n=64)
        objs.append(o)
    # anchors matching the X1 SkyRacer script's empties / part origins (metres, nose -Y, Z up)
    for name, loc, size in (("OPF_X1_Craft_Origin", (0.0, 0.0, 0.0), 0.6),
                            ("OPF_REF_Engine_Bay", (0.0, 0.5 * (ENV["y"][0] + ENV["y"][1]), ZC_BAY), 0.25),
                            ("OPF_REF_Thruster_L", (PUSHER_X, PUSHER_Y, PUSHER_Z), 0.2),
                            ("OPF_REF_Thruster_R", (-PUSHER_X, PUSHER_Y, PUSHER_Z), 0.2)):
        e = Obj(name, "OPFPLG_Reference", origin=loc, display="EMPTY")
        e.size = size
        objs.append(e)
    return objs


def fit_report(d, objs):
    core = [o for o in objs if o.coll in ("OPFPLG_Core", "OPFPLG_Generator", "OPFPLG_Air", "OPFPLG_Cooling")
            or (o.coll == "OPFPLG_Electrical" and o.name != "OPF_HV_Main_Feed")]
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in core:
        shifts = [(0, 0, 0)] + ([o.travel] if o.travel else [])
        for sh in shifts:
            for v in o.mesh.v:
                for k in range(3):
                    lo[k] = min(lo[k], v[k] + sh[k]); hi[k] = max(hi[k], v[k] + sh[k])
    lines = [f"X1 OPFPLG concept - preset {PRESET}: {PRESETS[PRESET]['note']}",
             f"  bore {d['B'] * 1000:.0f} mm, stroke {d['S'] * 1000:.0f} mm per piston, 3 cylinders x 2 pistons",
             f"  displacement {d['disp_cyl'] * 1000:.2f} L per cylinder, {d['disp'] * 1000:.2f} L total",
             f"  pistons move side to side; cylinder length {2 * d['END'] * 1000:.0f} mm across a {(ENV['x'][1] - ENV['x'][0]) * 1000:.0f} mm bay, "
             f"housing OD {2 * d['r_ho'] * 1000:.0f} mm, fore-aft pitch {d['pitch'] * 1000:.0f} mm",
             f"  magnets start {d['Lgap'] * 1000:.0f} mm behind the piston skirt (never enter the liner)",
             f"  linear-generator housing gas volume per side {d['Vb_max'] * 1e6:.0f} -> {d['Vb_min'] * 1e6:.0f} cm3, "
             f"volume ratio {d['Vb_max'] / d['Vb_min']:.2f}",
             "  engine-bay fit (core incl. pistons at both dead centres):"]
    ok_all = True
    for k, ax in enumerate("xyz"):
        e0, e1 = ENV[ax]
        ok = lo[k] >= e0 - 1e-6 and hi[k] <= e1 + 1e-6
        ok_all &= ok
        lines.append(f"    {ax}: {lo[k]:+.3f} .. {hi[k]:+.3f} m   bay {e0:+.3f} .. {e1:+.3f}   "
                     f"margin {min(lo[k] - e0, e1 - hi[k]) * 1000:+.0f} mm   {'OK' if ok else 'OVER'}")
    gap = (d["y_T"] - d["turbo_r"]) - (d["y_D"] + d["r_ca"])
    def vel(m, p_bar, T_k, area):
        return m / (p_bar * 1e5 / (287.0 * T_k)) / area
    A = lambda r: math.pi * r * r
    a_pl = d["pl_w"] * d["pl_h"]
    lines.append(f"  gas path sized for 2,000 hp peak: air {d['m_air']:.2f} kg/s, exhaust {d['m_exh']:.2f} kg/s "
                 f"(propane {d['m_fuel'] * 1000:.0f} g/s at 55 % BTE)")
    lines.append(f"    compressor inlet {2 * d['r_cin'] * 1000:.0f} mm: {vel(d['m_air'], 1.0, 300, A(d['r_cin'])):.0f} m/s | "
                 f"charge air {2 * d['r_ca'] * 1000:.0f} mm at PR 3.2: {vel(d['m_air'], 3.2, 430, A(d['r_ca'])):.0f} m/s | "
                 f"plenums {d['pl_w'] * 1000:.0f} x {d['pl_h'] * 1000:.0f} mm")
    lines.append(f"    pre-turbine {2 * d['r_ca'] * 1000:.0f} mm at 2.8 bar / 850 K: {vel(d['m_exh'], 2.8, 850, A(d['r_ca'])):.0f} m/s | "
                 f"downpipe {2 * d['r_dp'] * 1000:.0f} mm at 1.1 bar / 650 K: {vel(d['m_exh'], 1.1, 650, A(d['r_dp'])):.0f} m/s")
    lines.append(f"    turbo: compressor 84 mm inducer / 116 mm exducer, turbine 112 mm / 96 mm, "
                 f"volutes {2 * d['turbo_r'] * 1000:.0f} mm across")
    ok_all &= gap >= 0
    lines.append(f"    turbo volutes clear the cross-over pipes by {gap * 1000:.0f} mm   {'OK' if gap >= 0 else 'CLASH'}")
    lines.append(f"  6 inverters (one per stator) on a common DC bus; single HV feed drops between cylinders 1-2 "
                 f"at x {d['x_feed']:+.2f}, y {d['y_feed']:.3f} into the accumulator top (z {ACC_TOP_BAY:.2f})")
    a = d["acc"]
    hb = ZC_BAY - d["flange_r"]
    ys = [ACC_Y0 + ACC_L * k / 40 for k in range(41)]
    at = ACC_TOP_BAY
    zb = at - ACC_H
    belly = min(zb - belly_z(y) for y in ys)
    side = min(body_x(y, z) - ACC_W / 2 for y in ys for z in (zb, at))
    acc_ok = (hb - at) >= 0.010 and belly >= 0.05 - 1e-6 and side >= 0.035 - 1e-6
    ok_all &= acc_ok
    lines.append(f"  accumulator: {a['n']} x Toshiba SCiB 20Ah-HP LTO, {a['n']}S, {a['v_nom']:.0f} V nominal, "
                 f"{a['kwh']:.1f} kWh, ~{a['kw10']:.0f} kW for 10 s, cells {a['kg']:.0f} kg")
    lines.append(f"    case {ACC_W * 1000:.0f} W x {ACC_L * 1000:.0f} L x {ACC_H * 1000:.0f} H mm "
                 f"({ACC_W * ACC_L * ACC_H * 1000:.1f} L), y {ACC_Y0:.3f}..{ACC_Y0 + ACC_L:.3f}, z {zb:.3f}..{at:.3f}")
    lines.append(f"    clearances: housings above {(hb - at) * 1000:.0f} mm, belly below >= {belly * 1000:.0f} mm, "
                 f"skin at sides >= {side * 1000:.0f} mm   {'OK' if acc_ok else 'CLASH'}")
    lines.append(f"  RESULT: {'fits inside the engine bay' if ok_all else 'DOES NOT FIT'}"
                 " (exhaust downpipe, external coolant lines, fan heat exchangers, and the HV feed + accumulator below the bay floor are outside by design)")
    return "\n".join(lines), ok_all


# ------------------------------------------------------------ Blender side ---
def blender_build():
    d, objs = build(PRESET)
    report, _ = fit_report(d, objs)
    scn = bpy.context.scene
    placeholder = bpy.data.objects.get("Engine_Placeholder")
    if BUILD_REFERENCE:
        objs += reference_objects()

    root_name = "X1_OPFPLG"
    old = bpy.data.collections.get(root_name)
    if old:
        for c in [old] + list(old.children_recursive):
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
        for c in list(old.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.collections.remove(old)
    for me in list(bpy.data.meshes):
        if me.users == 0 and me.name.startswith("OPF_"):
            bpy.data.meshes.remove(me)
    root = bpy.data.collections.new(root_name)
    scn.collection.children.link(root)
    colls = {}

    def coll(name):
        if name not in colls:
            c = bpy.data.collections.new(name)
            root.children.link(c)
            colls[name] = c
        return colls[name]

    mats = {}
    for name, (rgb, metal, rough, alpha) in MATS.items():
        mname = "OPF_" + name
        mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Metallic"].default_value = metal
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Alpha"].default_value = alpha
        mat.diffuse_color = (*rgb, alpha)
        mat.metallic, mat.roughness = metal, rough
        if alpha < 1.0:
            # dithered / hashed transparency sorts correctly when see-through parts are nested
            # (sleeve inside stator inside linear-generator housing)
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "DITHERED"
            else:
                try:
                    mat.blend_method = "HASHED"
                    mat.shadow_method = "HASHED"
                except Exception:
                    pass
            mat.use_backface_culling = False
        mats[name] = mat

    created = []
    craft_origin = None
    for o in objs:
        if o.display == "EMPTY":
            ob = bpy.data.objects.new(o.name, None)
            ob.empty_display_type = "ARROWS" if o.name == "OPF_X1_Craft_Origin" else "PLAIN_AXES"
            ob.empty_display_size = getattr(o, "size", 0.2)
            ob.location = o.origin
            coll(o.coll).objects.link(ob)
            if o.name == "OPF_X1_Craft_Origin":
                craft_origin = ob
            created.append(ob)
            continue
        m = o.mesh
        verts = [sub(v, o.origin) for v in m.v]
        me = bpy.data.meshes.new(o.name)
        me.from_pydata(verts, m.e, m.f)
        names = []
        for mn in m.m:
            if mn not in names:
                names.append(mn)
        for mn in names:
            me.materials.append(mats[mn])
        if m.f:
            idx = {mn: i for i, mn in enumerate(names)}
            me.polygons.foreach_set("material_index", [idx[mn] for mn in m.m])
            me.polygons.foreach_set("use_smooth", [bool(s) for s in m.sm])
        me.validate(verbose=False)
        me.update()
        ob = bpy.data.objects.new(o.name, me)
        ob.location = o.origin
        coll(o.coll).objects.link(ob)
        if o.display == "WIRE":
            ob.display_type = "WIRE"
            ob.hide_render = True
            ob.color = (1, 0.1, 0.1, 1)
        if o.driver:
            fc = ob.driver_add(o.driver_path, o.driver_index)
            fc.driver.type = "SCRIPTED"
            fc.driver.expression = o.driver
        created.append(ob)

    # parent everything to the craft-origin empty (sits at the X1 SkyRacer origin, identity
    # transform) so the whole powertrain moves / appends as one unit
    if craft_origin is not None:
        for ob in created:
            if ob is not craft_origin:
                ob.parent = craft_origin

    if placeholder is not None:
        try:
            placeholder.hide_set(True)
        except Exception:
            placeholder.hide_viewport = True
        placeholder.hide_render = True
    scn.frame_start, scn.frame_end = 1, 24
    scn.frame_set(1)

    txt = bpy.data.texts.get("OPFPLG_Report") or bpy.data.texts.new("OPFPLG_Report")
    txt.clear(); txt.write(report + "\n")
    print(report)

    os.makedirs(OUT_DIR, exist_ok=True)
    stem = "X1_SkyRacer_OPFPLG" if placeholder is not None else "X1_OPFPLG"
    try:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, stem + ".blend"), copy=True)
    except Exception as exc:
        print("  .blend save skipped:", exc)
    try:
        for ob in bpy.context.view_layer.objects:
            ob.select_set(False)
        for ob in created:
            if not ob.name.startswith("OPF_REF_") and ob.type == "MESH":
                ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, stem + ".glb"), export_format="GLB",
                                  use_selection=True)
    except Exception as exc:
        print("  .glb export skipped:", exc)
    print(f"  saved to {OUT_DIR}")


# ---------------------------------------------- plain-Python preview side ---
def standalone(out_dir="x1_opfplg_out", preset=None):
    global PRESET
    if preset:
        PRESET = preset
    d, objs = build(PRESET)
    report, ok = fit_report(d, objs)
    print(report)
    os.makedirs(out_dir, exist_ok=True)
    # pose the pistons as at frame 1
    w = 2 * math.pi / 24
    for o in objs:
        if o.driver and o.driver_path == "location":
            val = eval(o.driver.replace("frame", "1"), {"cos": math.cos})
            k = o.driver_index
            dk = val - o.origin[k]
            o.mesh.v = [tuple(c + (dk if i == k else 0.0) for i, c in enumerate(v)) for v in o.mesh.v]
    refs = reference_objects()
    # OBJ + MTL
    with open(os.path.join(out_dir, "x1_opfplg.mtl"), "w") as f:
        for name, (rgb, metal, rough, alpha) in MATS.items():
            f.write(f"newmtl OPF_{name}\nKd {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f}\nd {alpha:.2f}\n\n")
    with open(os.path.join(out_dir, "x1_opfplg.obj"), "w") as f:
        f.write("# X1 OPFPLG concept, metres, Z up, nose -Y\nmtllib x1_opfplg.mtl\n")
        base = 1
        for o in objs:
            f.write(f"o {o.name}\n")
            for v in o.mesh.v:
                f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
            cur = None
            for face, mn in zip(o.mesh.f, o.mesh.m):
                if mn != cur:
                    f.write(f"usemtl OPF_{mn}\n"); cur = mn
                f.write("f " + " ".join(str(i + base) for i in face) + "\n")
            base += len(o.mesh.v)
    _previews(objs, refs, out_dir, d)
    with open(os.path.join(out_dir, "fit_report.txt"), "w") as f:
        f.write(report + "\n")
    return ok


def _previews(objs, refs, out_dir, d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    def render(ax, view, items, lim, light=(0.4, -0.5, 0.75)):
        az, el = map(math.radians, view)
        right = (math.cos(az), math.sin(az), 0.0)
        fwd = (-math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el))   # toward viewer
        up = cross(fwd, right)
        up = mul(up, -1) if up[2] < 0 else up
        right = cross(up, fwd)                      # keep the projection right-handed (no mirror)
        L = unit(light)
        polys, cols, depth = [], [], []
        for o in items:
            V = o.mesh.v
            for face, mn in zip(o.mesh.f, o.mesh.m):
                pts = [V[i] for i in face]
                nx = ny = nz = 0.0
                for a, b in zip(pts, pts[1:] + pts[:1]):
                    nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1])
                nl = math.sqrt(nx * nx + ny * ny + nz * nz)
                if nl < 1e-12:
                    continue
                n = (nx / nl, ny / nl, nz / nl)
                if dot(n, fwd) < 0:
                    n = mul(n, -1)
                rgb, _, _, alpha = MATS[mn]
                sh = 0.35 + 0.65 * max(0.0, dot(n, L)) + 0.12 * max(0.0, dot(n, fwd))
                polys.append([(dot(p, right), dot(p, up)) for p in pts])
                cols.append((min(1, rgb[0] * sh), min(1, rgb[1] * sh), min(1, rgb[2] * sh), alpha))
                depth.append(sum(dot(p, fwd) for p in pts) / len(pts))
        order = sorted(range(len(polys)), key=lambda k: depth[k])
        ax.add_collection(PolyCollection([polys[k] for k in order], facecolors=[cols[k] for k in order],
                                         edgecolors="none", antialiaseds=False))
        x0, x1 = ENV["x"]; y0, y1 = ENV["y"]; z0, z1 = ENV["z"]
        c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        for i, j in [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]:
            ax.plot([dot(c[i], right), dot(c[j], right)], [dot(c[i], up), dot(c[j], up)], "r--", lw=0.8)
        if lim:
            ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1])
        else:
            ax.autoscale_view()
        ax.set_aspect("equal"); ax.axis("off")

    ghosts = [r for r in refs if "Pusher_Duct" in r.name]
    shots = [
        ("iso_rear", (35, 28), objs + ghosts, None, (12, 9)),
        ("iso_engine", (35, 30), [o for o in objs if o.coll != "OPFPLG_Radiators" and "Ext" not in o.name],
         None, (12, 8)),
        ("iso_front_engine", (215, 30), [o for o in objs if o.coll != "OPFPLG_Radiators" and "Ext" not in o.name],
         None, (12, 8)),
        ("top", (0, 89.9), objs + ghosts, None, (7, 10)),
        ("side", (90, 0), objs + ghosts, None, (14, 6)),
        ("rear_hx", (0, 0), [o for o in objs if o.coll == "OPFPLG_Radiators"],
         None, (10, 5.5)),
    ]
    for name, view, items, lim, size in shots:
        fig, ax = plt.subplots(figsize=size, dpi=110)
        render(ax, view, items, lim)
        ax.set_title(f"X1 OPFPLG {PRESET} ({d['disp'] * 1000:.1f} L) - {name}", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"preview_{name}.png"))
        plt.close(fig)


if __name__ == "__main__":
    if IN_BLENDER:
        blender_build()
    else:
        args = [a for a in sys.argv[1:]]
        standalone(args[0] if args else "x1_opfplg_out", args[1] if len(args) > 1 else None)
