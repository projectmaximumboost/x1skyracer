"""
X1 SkyRacer - OPFPLG 1,500 hp continuous (opposed free-piston linear generator)
===============================================================================
Blender 3.6 / 4.x.  Scripting workspace -> New text -> paste -> Run Script.
Nov 2026 redesign of the 4.5 L concept. Same airframe coordinates, same LTO pack, same pusher
heat-exchanger idea, but every part is now sized from a free-piston cycle model (opf_cycle.py)
instead of an assumed 100 Hz.

What it builds (collection "X1_OPFPLG"):
  * 3 opposed-piston cylinders across the airframe, 6 free pistons, uniflow two-stroke, propane DI.
    150 mm bore x 124 mm stroke per piston (13.1 L), about 45 Hz, 120 deg between cylinders,
    the two pistons of a cylinder mirror each other exactly (taller exhaust ports give the lead).
  * each piston carries a folded "bell" translator: a tail tube runs out of the open liner end to a
    spoked disc, and the magnet sleeve hangs back from the disc over the OUTSIDE of the liner, so the
    generator shares length with the cylinder. Stators on both faces of the magnet sleeve
    (inner stator around the liner; the outer stator stops 60 % of the stroke short of the outer dead
    centre, where the generating force is low). Lightweight build: aluminium windings on cobalt-iron cores.
  * printed aluminium block: each cylinder is a coated-bore centre section (20 mm combustion band, 6 mm
    elsewhere). ONE metal-printed centre block (collection OPFPLG_Block) holds the three bores, the intake
    and exhaust port galleries, the injector bosses and, printed into the bore walls, a propane cooling
    gallery right through the combustion zone of each cylinder (one half per piston circuit: liquid from
    that piston's check valve goes through the block first, then into its chamber). The intake plenum and
    exhaust collector are printed onto the block top. Each side of the block has a bolt face; the six stator
    assemblies (4.5 mm housing, both stators, liner extension, end cap) bolt on with 16 x M8 each.
  * the sealed volume behind each piston (linear-generator housing) is that piston's own propane
    circuit: liquid enters through a check valve and a spray lance up the hollow tail onto the crown
    underside and through the stator slots, boils, and leaves through a BLEED VALVE to its own sector
    of the pusher-fan condenser. Chamber pressure swings with the piston, so the chamber pumps its own
    loop; the bleed valve sets the mean pressure = boiling temperature = bounce (return) force.
  * charge air cooler in the spine over the engine (air to boiling propane), feeding the intake plenum;
    exhaust collector beside it, electric turbo-compound unit aft.
  * power-electronics deck ahead of the rear wing: 6 SiC inverters (one per stator set), DC/DC to the
    373 V LTO pack, and ONE placeholder box for control electronics and sensors. Inverter cold plates
    and the charge air cooler share two auxiliary propane circuits (left / right).
  * 162-cell LTO accumulator under the engine, unchanged.
  * pusher-fan condensers: annular finned cores behind each fan, four sectors each
    (three piston circuits + one auxiliary circuit). Thin cambered fins only, no thick vanes: about 20 deg
    at the leading edge against the rotor swirl, axial at the trailing edge; the propane runs in the splitter rings.

Coordinates match x1_skyracer_blender.py: metres, nose toward -Y, Z up, origin on the ground.
Everything is built directly at craft height (no ENGINE_DZ shift afterwards).

Run it inside your X1_SkyRacer.blend and it drops into place (it hides Engine_Placeholder).
Pistons are keyframed from the cycle model's motion table (every half frame, linear): frames 1-24 = one cycle.
The turbo spins on a driver.

Run with plain Python (no Blender) and it writes an OBJ + MTL, preview PNGs and the report instead.
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
PRESET = "1500hp"
PRESETS = {
    "1500hp": dict(bore=0.150, x_po=0.100, cr=16.0,
                   note="lightweight build: 150 bore x 124 stroke per piston, 13.1 L, aluminium windings, printed block"),
}
N_PORTS = 16                # port holes per ring, evenly spaced all the way round
N_FINS_DRAWN = 78           # thin condenser fins drawn per pusher (about 1/10 of the real count)
FIN_CAMBER = 0.18           # fin camber: leading-edge angle = atan(2 x camber), about 20 deg against the rotor swirl
OUT_DIR = os.path.join(os.path.expanduser("~"), "X1_Racer")   # where your X1 files live
TURBO_SPIN_RAD_PER_FRAME = 2 * math.pi * 2 / 24   # 2 turns per 24-frame loop (seamless, readable)
BUILD_REFERENCE = True     # bay box, pusher-duct wireframes and anchor empties (no X1 body)

# generator rating assumptions (state them, they drive the size)
SIGMA_CONT = 85e3           # Pa, continuous rms air-gap shear with boiling propane in the slots
PEAK_OVER_CONT = 2.0        # short-term force / continuous force
END_MAX = 0.496             # half length of a cylinder assembly (bay half width is 0.500)
X_TRAY = 0.512              # propane line trays run outboard of the end caps, inside the skin
TURBO_K = 1.15              # radial scale of the e-turbo against the 4.5 L model (more air: lean burn)
# lightweight generator and printed block (Nov 2026 weight study)
T_YOKE, T_SLOT = 0.0065, 0.024   # cobalt-iron back iron, winding slot depth (m)
STATOR_TRIM = 0.60          # outer stator ends this share of the stroke short of the magnet's outermost reach
K_RES = 1.64 * 0.38 / 0.48  # winding resistance vs the reference copper winding (aluminium, wider slots)
FE_FRAC = 0.018             # core loss, share of converted energy (cobalt-iron at 150-300 Hz)
Q_CU_REF = 33.5e3           # W per m2 of air gap: reference copper winding loss at 85 kPa shear
T_LINER, T_BAND, L_BAND = 0.006, 0.020, 0.035   # printed bore wall, combustion band thickness and half length
T_HOUSING = 0.0045          # printed generator housing wall (26 bar propane)
TURBO_KA = 0.82             # axial scale: shorter shaft line, the fuselage is already narrowing at the turbo

# Cycle-model result for this geometry (written by tune_cycle.py from opf_cycle.py; per piston).
CYCLE = dict(
    f=44.932,
    stroke=0.12375,
    x_min=0.00625,
    x_max=0.13,
    cr=16.0,
    p_max=22533206.0,
    v_mean=11.12,
    v_max=21.963,
    Qf=9170.57,
    E_el=4233.66,
    E_mech=4487.37,
    W_gas=4709.63,
    Q_wall=792.67,
    W_fric=76.93,
    F_rms=16027.0,
    F_peak=27980.0,
    pb_min=2238156.0,
    pb_max=2632479.0,
    pb_mean=2467116.0,
    m_trap=0.006156,
    p_s=380000.0,
    lam=1.787,
    T_trap=380.0,
    imep=2153683.0,
    motion=[0.0, 0.000462, 0.002135, 0.004994, 0.008772, 0.013152, 0.017898, 0.02285, 0.027906, 0.032995, 0.038069, 0.04309, 0.048033, 0.052877, 0.057606, 0.062208, 0.066674, 0.070996, 0.075169, 0.079188, 0.08305, 0.086751, 0.090291, 0.093668, 0.096879, 0.09991, 0.102754, 0.105407, 0.10787, 0.110144, 0.11223, 0.114132, 0.115852, 0.117393, 0.11876, 0.119953, 0.120976, 0.121834, 0.122529, 0.123064, 0.123441, 0.123664, 0.123738, 0.123668, 0.123453, 0.123101, 0.122615, 0.121998, 0.121251, 0.120379, 0.119384, 0.118269, 0.117035, 0.115686, 0.114225, 0.112653, 0.110975, 0.109191, 0.107304, 0.105318, 0.103234, 0.101054, 0.098782, 0.09642, 0.093969, 0.091432, 0.088813, 0.086114, 0.083339, 0.08049, 0.077572, 0.074587, 0.071539, 0.068432, 0.06527, 0.062056, 0.058795, 0.05549, 0.052148, 0.048773, 0.04537, 0.041946, 0.038507, 0.035062, 0.03162, 0.028191, 0.024788, 0.021427, 0.018128, 0.014916, 0.011824, 0.008897, 0.0062, 0.00382, 0.001883, 0.000549],
    e_cu=172.94,
    sig_rms=82405.97,
    sig_pk=121251.04,
    burst={'p_s': 410000.0, 'lam': 1.6, 'bus_hp': 1900.0, 'p_max': 24735692.0, 'f': 47.36, 'F_rms': 19253.0, 'sig_pk': 147267.0},
)


# ------------------------------------------------- X1 SkyRacer reference data ---
ENGINE_DZ = -0.13         # whole engine + accumulator lowered 5.1 in (Oct 2026) to clear the lowered rear wing
ENV = dict(x=(-0.50, 0.50), y=(0.14, 1.50), z=(0.55 + ENGINE_DZ, 1.01 + ENGINE_DZ))   # engine bay envelope
# Pushers as in x1_skyracer_blender.py (fan-tilt, Oct 2026). x1_skyracer_blender.py sets these from its own
# FWD_C / PUSHER_TILT_DEG / FWD_Z0..FWD_Z1 before it builds the engine externals, so the two always agree.
PUSHER_X, PUSHER_Y, PUSHER_Z = 0.45, 2.271, 0.80               # FWD_C (mirrored in x); lowered from 0.90
PUSHER_TILT_DEG = 10.0                                         # fan axis tilted so the exhaust points down
PUSHER_R0, PUSHER_R1, PUSHER_HL = 0.33, 0.40, 0.25             # bore r, outer r, original half length
PUSHER_Z0, PUSHER_Z1 = -0.19, 0.20                             # duct front / rear along the axis (0.39 m)
PUSHER_HUB_R, PUSHER_HUB_L, PUSHER_ROTOR_Z = 0.11, 0.22, -0.10


def pusher_frame(sgn):
    """Frame on a pusher axis: origin at the fan centre, +z aft along the tilted thrust axis."""
    t = math.radians(PUSHER_TILT_DEG)
    return Frame((sgn * PUSHER_X, PUSHER_Y, PUSHER_Z), (0.0, math.cos(t), -math.sin(t)))
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
    "Stator_Inner":     ((0.93, 0.60, 0.30), 0.3, 0.30, 0.45),
    "Bell_Carrier":     ((0.28, 0.30, 0.33), 0.6, 0.45, 1.0),
    "Cooling_Jacket":   ((0.25, 0.80, 0.45), 0.0, 0.15, 0.35),
    "Valve":            ((0.78, 0.66, 0.30), 1.0, 0.30, 1.0),
    "Valve_Actuator":   ((0.14, 0.15, 0.17), 0.6, 0.45, 1.0),
    "Intake_Hot":       ((0.55, 0.42, 0.85), 0.6, 0.35, 1.0),
    "CAC_Core":         ((0.66, 0.70, 0.74), 0.9, 0.45, 1.0),
    "CAC_Fin":          ((0.82, 0.85, 0.88), 1.0, 0.35, 1.0),
    "Aux_Vapour":       ((0.98, 0.60, 0.20), 0.3, 0.40, 1.0),
    "Aux_Liquid":       ((0.15, 0.70, 0.72), 0.3, 0.40, 1.0),
    "Heat_Shield":      ((0.85, 0.80, 0.62), 1.0, 0.30, 1.0),
    "Deck":             ((0.20, 0.22, 0.25), 0.7, 0.50, 1.0),
    "Cold_Plate":       ((0.15, 0.70, 0.72), 0.6, 0.30, 1.0),
    "DCDC":             ((0.30, 0.24, 0.36), 0.8, 0.40, 1.0),
    "Controller":       ((0.85, 0.15, 0.55), 0.2, 0.50, 0.75),
    "AC_Lead":          ((0.90, 0.55, 0.20), 0.4, 0.40, 1.0),
    "HX_Fin":           ((0.70, 0.72, 0.76), 0.8, 0.50, 0.55),
    "Printed_Block":    ((0.60, 0.63, 0.67), 0.9, 0.55, 1.0),
    "Block_Body":       ((0.56, 0.60, 0.66), 0.9, 0.50, 0.60),
    "Bolt":             ((0.16, 0.17, 0.19), 1.0, 0.40, 1.0),
    "Stator_Coil":      ((0.80, 0.83, 0.88), 0.6, 0.35, 0.45),
    "Stator_Inner":     ((0.72, 0.78, 0.86), 0.6, 0.35, 0.50),
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
                 driver_path="location", driver_index=1, motion=None):
        self.name, self.coll, self.origin = name, coll, origin
        self.motion = motion                    # (sgn, phase) for a piston: keyframed from the cycle table
        self.mesh, self.driver, self.travel, self.display = Mesh(), driver, travel, display
        self.driver_path, self.driver_index = driver_path, driver_index


RHO_MAGNET, RHO_STEEL, RHO_AL, RHO_TI, RHO_CFRP = 7600.0, 7850.0, 2700.0, 4430.0, 1600.0


def stator_cover(d, travel):
    """Share of the magnet sleeve inside the (outer, inner) stator at this outward travel from the inner dead centre."""
    b1 = d["disk0"] + travel
    b0 = b1 - d["Lm"]
    co = max(0.0, min(b1, d["so_u1"]) - max(b0, d["so_u0"])) / d["Lm"]
    ci = max(0.0, min(b1, d["si_u1"]) - max(b0, d["si_u0"])) / d["Lm"]
    return co, ci


def design(preset=None):
    p = PRESETS.get(preset) or PRESETS[PRESET]
    B = p["bore"]
    d = dict(B=B, note=p["note"])
    A = math.pi * B * B / 4
    d["A"] = A
    # ---- cylinder (u = distance from the cylinder centre plane, same on both sides)
    d["x_po"], d["cr"] = p["x_po"], p["cr"]             # mean port-opening position, compression ratio
    d["g"] = d["x_po"] / d["cr"]                        # crown gap at inner dead centre
    d["h_ex"], d["h_in"] = 0.034, 0.026                 # exhaust ports taller: they open first, close last
    d["cb"] = d["x_po"] + 0.030                         # crown at outer dead centre (ports fully open)
    S = d["cb"] - d["g"]
    d["S"] = S
    d["r_li"], d["r_lo"] = B / 2, B / 2 + T_LINER
    d["r_band"] = B / 2 + T_BAND                        # thick band over the combustion zone
    d["Lp"] = S + d["h_ex"] + 0.026                     # skirt always covers the ports and the propane seal
    d["L_l"] = d["cb"] + d["Lp"] + 0.006                # liner end (open into the generator housing)
    d["u_seal"] = d["cb"] + 0.022                       # stationary propane seal pack in the liner
    d["h0"] = d["cb"] + 0.016                           # housing inner wall, on the liner just outboard of the belt
    d["r_b"] = d["r_lo"] + 0.032                        # port belt outer radius
    # ---- folded translator: tail tube -> disc -> magnet sleeve hanging back over the liner
    d["END"], d["t_cap"], d["t_disk"] = END_MAX, 0.014, 0.012
    d["disk0"] = d["END"] - d["t_cap"] - 0.016 - d["t_disk"] - S     # disc inner face at inner dead centre
    # the carrier disc must clear the liner end (and the inner stator on it) at the inner dead centre, so on a
    # long stroke the liner stops short and the skirt overhangs it at the outer dead centre
    d["L_l"] = min(d["L_l"], d["disk0"] - 0.008)
    d["L_tail"] = d["disk0"] - (d["g"] + d["Lp"])
    d["Lm"] = d["disk0"] - (d["h0"] + 0.009)            # magnet sleeve length (clears the housing wall at IDC)
    d["n_poles"] = max(2, 2 * round(d["Lm"] / 0.068))
    d["r_tail"] = 0.034
    d["gap"] = 0.002
    d["r_si0"] = d["r_lo"] + 0.004                      # inner stator (around the liner, 4 mm propane gap)
    d["r_si1"] = d["r_si0"] + T_YOKE + T_SLOT - 0.002
    d["r_mi"] = d["r_si1"] + d["gap"]
    d["r_mo"] = d["r_mi"] + 0.010                       # 10 mm NdFeB sleeve, worked on both faces
    d["r_so0"] = d["r_mo"] + d["gap"]
    d["r_so1"] = d["r_so0"] + T_YOKE + T_SLOT                     # outer stator
    d["r_hi"] = d["r_so1"] + 0.0035
    d["r_ho"] = d["r_hi"] + T_HOUSING                       # housing: ~30 bar propane vessel
    d["flange_r"] = d["r_ho"] + 0.016                    # bolt flange: 16 x M8 on a circle just outside the housing
    d["r_bolt"] = d["r_ho"] + 0.008
    d["Rb"] = d["r_b"] + 0.012                          # centre block outer radius about each bore
    d["blk_face"], d["blk_tf"] = d["h0"] - 0.008, 0.012   # block bolt face (x from centre), block flange thickness
    d["si_u0"], d["si_u1"] = d["h0"] + 0.010, d["L_l"]
    d["so_u0"], d["so_u1"] = d["h0"] + 0.010, d["disk0"] + S + 0.004 - STATOR_TRIM * S
    # ---- generator force rating
    A_out = 2 * math.pi * (d["r_mo"] + d["gap"] / 2) * d["Lm"]
    A_in = 2 * math.pi * (d["r_mi"] - d["gap"] / 2) * d["Lm"]

    d["A_out"], d["A_in"] = A_out, A_in
    (d["cover_out_idc"], d["cover_idc"]), (d["cover_out_mid"], d["cover_mid"]), (d["cover_out_odc"], d["cover_odc"]) = \
        stator_cover(d, 0.0), stator_cover(d, S / 2), stator_cover(d, S)
    d["A_eff"] = d["cover_out_mid"] * A_out + d["cover_mid"] * A_in     # at mid stroke, where the force peaks
    d["F_cont"] = SIGMA_CONT * d["A_eff"]
    # ---- moving-part clearances (m); every one must stay positive through the stroke
    d["clear"] = dict(
        crowns_idc=2 * d["g"],                                             # between the two crowns
        disc_liner_idc=d["disk0"] - max(d["L_l"], d["si_u1"]),             # carrier disc to liner / inner stator end
        sleeve_wall_idc=d["disk0"] - d["Lm"] - d["h0"],                    # magnet sleeve to the housing inner wall
        skirt_disc=d["L_tail"],                                            # skirt end to the carrier disc
        disc_cap_odc=d["END"] - d["t_cap"] - (d["disk0"] + d["t_disk"] + S),   # carrier disc to the end cap
        seal_cover=d["L_l"] - (d["u_seal"] + 0.010),                       # liner still carries the seal pack
        radial_gap=d["gap"])
    d["skirt_engaged"] = (d["L_l"] - d["cb"]) / d["Lp"]                    # share of the skirt in the liner at ODC
    d["F_pk"] = PEAK_OVER_CONT * d["F_cont"]
    # ---- moving mass (one piston assembly)
    m_mag = math.pi * (d["r_mo"] ** 2 - d["r_mi"] ** 2) * d["Lm"] * RHO_MAGNET
    m_sleeve = 2 * math.pi * 0.5 * (d["r_mo"] + d["r_mi"]) * d["Lm"] * 2 * 0.0012 * RHO_CFRP   # retaining wraps
    m_disk = 0.35 * math.pi * (d["r_mo"] ** 2 - d["r_tail"] ** 2) * d["t_disk"] * RHO_TI       # spoked, 35 % solid
    m_tail = 2 * math.pi * d["r_tail"] * 0.0025 * (d["L_tail"] + 0.02) * RHO_TI
    m_crown = math.pi * d["r_li"] ** 2 * 0.012 * RHO_STEEL
    m_skirt = 2 * math.pi * d["r_li"] * 0.003 * (d["Lp"] - 0.02) * RHO_AL
    d["mass"] = dict(magnets=m_mag, sleeve=m_sleeve, disc=m_disk, tail=m_tail, crown=m_crown, skirt=m_skirt,
                     rings_web=0.6)
    d["m_move"] = sum(d["mass"].values())
    # ---- bounce / propane chamber gas volume (one side) at inner dead centre
    hl = (d["END"] - d["t_cap"]) - (d["h0"] + 0.008)
    v_gross = math.pi * d["r_hi"] ** 2 * hl
    v_liner = math.pi * (d["r_lo"] ** 2 - d["r_li"] ** 2) * (d["L_l"] - d["h0"] - 0.008)
    v_si = 0.85 * math.pi * (d["r_si1"] ** 2 - d["r_si0"] ** 2) * (d["si_u1"] - d["si_u0"])
    v_so = 0.85 * math.pi * (d["r_so1"] ** 2 - d["r_so0"] ** 2) * (d["so_u1"] - d["so_u0"])
    v_move = d["m_move"] / 5500.0                        # moving parts behind the seal, mean density
    d["Vb_idc"] = v_gross - v_liner - v_si - v_so - v_move
    d["Vb_odc"] = d["Vb_idc"] - A * S
    # ---- layout in the craft
    d["zc"] = ACC_TOP_BAY + 0.010 + d["flange_r"]       # cylinder axis height: 10 mm over the accumulator
    d["pitch"] = 2 * d["flange_r"] + 0.008
    y0 = ENV["y"][0] + 0.005 + d["flange_r"]
    d["cyl_y"] = [y0 + k * d["pitch"] for k in range(3)]
    d["y_A"] = d["cyl_y"][2] + d["flange_r"]            # aft face of the cylinder bank
    k = TURBO_K
    d["scroll_R0"], d["scroll_rbig"] = 0.060, 0.055     # before the radial scale
    d["r_ca"] = 0.055 * k                               # charge-air and pre-turbine pipes
    d["r_cin"] = 0.075 * k
    d["r_dp"] = 0.100                                   # downpipe
    d["turbo_r"] = (d["scroll_R0"] + 2 * d["scroll_rbig"]) * k
    d["y_T"] = d["y_A"] + 0.008 + d["turbo_r"]          # turbo shaft line, volutes just clear the bank
    d["z_T"] = 0.640                                    # lower than the cylinders: clears the rear wing root
    # manifolds over the port belts, in the spine between the generator housings
    d["px_in"], d["px_out"] = 0.022, d["h0"] - 0.024
    d["pz_bot"], d["pz_top"] = d["zc"] + d["r_b"] - 0.004, ENV["z"][1] - 0.006
    d["col_top"] = 0.930                                # exhaust collector rises into the spine aft of the deck
    d["pl_w"] = d["px_out"] - d["px_in"]
    d["x_in"] = -(d["cb"] - d["h_in"] / 2)
    d["x_ex"] = d["cb"] - d["h_ex"] / 2
    d["disp_cyl"] = 2 * A * S
    d["disp"] = 3 * d["disp_cyl"]
    # charge air cooler (spine, between the rear wing roots) and power-electronics deck (ahead of the wing)
    d["cac"] = dict(hw=0.140, y0=0.640, y1=1.240, z0=0.945, z1=1.035, yf=0.580, ya=1.385)
    d["deck"] = dict(hw=0.360, y0=0.155, y1=0.565, z=0.884)
    return d


def piston_travel(theta):
    """Outward travel from the inner dead centre at cycle angle theta (rad), straight from the cycle
    model's motion table (equal time steps, starting at the inner dead centre), linear in between."""
    tab = CYCLE["motion"]
    n = len(tab)
    u = (theta / (2 * math.pi)) % 1.0 * n
    i = int(u)
    f = u - i
    return tab[i % n] * (1 - f) + tab[(i + 1) % n] * f


CYCLE_FRAMES = 24          # one engine cycle = 24 frames


def piston_x(sgn, phi, frame):
    """Piston displacement along the cylinder axis at a Blender frame (frame 1 = cylinder 1 at the
    inner dead centre). sgn = -1 for the intake-side piston, phi = cylinder phase (rad)."""
    return sgn * piston_travel((frame - 1) * 2 * math.pi / CYCLE_FRAMES + phi)



X3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
Z_LIP_OFF = 0.04            # propane lines turn in this far ahead of the pusher duct lip
R_RING, R_OUT = 0.365, 0.425
HX_Z_LE, HX_CHORD = 0.05, 0.14
# line heights in the side trays (craft z): liquid below vapour, cylinder 1 innermost of the nest
TRAY_Z_LIQ = (0.752, 0.734, 0.716)
TRAY_Z_VAP = (0.775, 0.803, 0.831)
AUX_SPAN_DEG = 171.0        # share of each condenser annulus given to the auxiliary circuit


def sector_table(sgn):
    """Condenser sectors of one pusher: (name, centre angle, span) in the pusher frame
    (0 = +X, 90 deg = down). Three piston circuits share the lower arc, the auxiliary circuit the top."""
    span = (360.0 - AUX_SPAN_DEG) / 3.0
    out = []
    for k in range(3):                                   # cylinder 1 outboard, 2 bottom, 3 inboard
        a = 90.0 + (k - 1) * span * sgn
        out.append((f"Cyl{k + 1}", math.radians(a), math.radians(span)))
    out.append(("Aux", math.radians(-90.0), math.radians(AUX_SPAN_DEG)))
    return out


def arc(m, fr, R, z, th0, th1, r, mat, n=24):
    P = [fr.Pc(R, th0 + (th1 - th0) * k / n, z) for k in range(n + 1)]
    sweep(m, P, [r] * len(P), mat, n=10)


def build(preset=PRESET):
    d = design(preset)
    B, S = d["B"], d["S"]
    zc = d["zc"]
    objs = []

    def new(name, coll, **kw):
        o = Obj(name, coll, **kw)
        objs.append(o)
        return o

    w = 2 * math.pi / 24.0      # one engine cycle = 24 frames
    stroke = CYCLE.get("stroke", S)
    cb = d["cb"]
    n45 = math.sqrt(0.5)
    for ci, yc in enumerate(d["cyl_y"]):
        tag = f"Cyl{ci + 1}"
        C = (0.0, yc, zc)
        fr = Frame(C, (1, 0, 0))                   # cylinder axis across the airframe
        phi = ci * 2 * math.pi / 3

        # sleeve with port rings (intake on -X, exhaust on +X), open ends into the generator housings
        st = [-d["L_l"], -(cb + 0.002), -(cb - d["h_in"]), cb - d["h_ex"], cb + 0.002, d["L_l"]]
        o = new(f"OPF_{tag}_Sleeve", "OPFPLG_Core")
        ported_liner(o.mesh, fr, d["r_li"], d["r_lo"], st, (1, 3), "Liner", N_PORTS, swirl_rings=(1, 2))
        tube(o.mesh, fr, d["r_lo"], d["r_band"], -L_BAND, L_BAND, "Liner")     # printed combustion band
        for s in (-1, 1):                                # stationary propane seal packs
            a0, a1 = sorted((s * d["u_seal"], s * (d["u_seal"] + 0.010)))
            tube(o.mesh, fr, d["r_lo"], d["r_lo"] + 0.004, a0, a1, "Housing_Flange")

        o = new(f"OPF_{tag}_Intake_Belt", "OPFPLG_Core")
        tube(o.mesh, fr, d["r_lo"] + 0.0005, d["r_b"], -(cb + 0.008), -(cb - d["h_in"] - 0.006), "Intake_Belt")
        o = new(f"OPF_{tag}_Exhaust_Belt", "OPFPLG_Core")
        tube(o.mesh, fr, d["r_lo"] + 0.0005, d["r_b"], cb - d["h_ex"] - 0.006, cb + 0.008, "Exhaust_Belt")

        # propane cooling gallery printed in the bore wall, right through the combustion zone; one half per
        # piston circuit, split at the centre plane. Ring manifolds at the centre (inlet) and by the ports (outlet)
        o = new(f"OPF_{tag}_Block_Cooling_Gallery", "OPFPLG_Cooling")
        rg0, rg1 = d["r_li"] + 0.007, d["r_li"] + 0.012
        for s_, hp_ in ((-1, d["h_in"]), (1, d["h_ex"])):
            u_out = cb - hp_ - 0.012
            a0, a1 = sorted((s_ * 0.003, s_ * u_out))
            tube(o.mesh, fr, rg0, rg1, a0, a1, "Cooling_Jacket")
            torus(o.mesh, fr, 0.5 * (rg0 + rg1), 0.0045, s_ * 0.010, "Propane_Liquid", nm=8)
            torus(o.mesh, fr, 0.5 * (rg0 + rg1), 0.0045, s_ * (u_out - 0.006), "Propane_Liquid", nm=8)

        # DI injectors at the inner-dead-centre plane (tilted fore and aft), fed from the rail
        rail_z = zc + d["r_lo"] + 0.066
        o = new(f"OPF_{tag}_Injectors", "OPFPLG_Core")
        for a in (-0.70, 0.70):
            dvec = (0.0, math.sin(a), math.cos(a))
            p0 = add(C, mul(dvec, d["r_lo"]))
            p1 = add(C, mul(dvec, d["r_lo"] + 0.075))
            pipe(o.mesh, [p0, p1], 0.008, "Injector")
            pipe(o.mesh, [p1, (0.0, p1[1], rail_z)], 0.004, "Fuel_Rail")

        for s, side in ((-1, "Intake"), (1, "Exhaust")):
            def zz(u0, u1):
                return (min(s * u0, s * u1), max(s * u0, s * u1))

            # ---- moving assembly: piston + tail tube + spoked disc + magnet sleeve, driven along X
            o = new(f"OPF_{tag}_Piston_{side}", "OPFPLG_Generator", origin=C,
                    motion=(s, phi), travel=(s * stroke, 0, 0))
            g, Lp = d["g"], d["Lp"]
            z0, z1 = zz(g, g + 0.022)
            cyl(o.mesh, fr, d["r_li"] - 0.0005, z0, z1, "Piston")                    # crown
            z0, z1 = zz(g + 0.022, g + Lp)
            tube(o.mesh, fr, d["r_li"] - 0.0045, d["r_li"] - 0.0005, z0, z1, "Piston")   # long skirt
            for k in range(3):                         # ring lands
                u = g + 0.007 + 0.005 * k
                a0, a1 = zz(u, u + 0.002)
                tube(o.mesh, fr, d["r_li"] - 0.0035, d["r_li"] - 0.0004, a0, a1, "Rod")
            z0, z1 = zz(g + Lp - 0.008, g + Lp)
            tube(o.mesh, fr, d["r_tail"], d["r_li"] - 0.0045, z0, z1, "Rod")         # skirt-to-tail web
            z0, z1 = zz(g + Lp - 0.008, d["disk0"] + d["t_disk"])
            tube(o.mesh, fr, d["r_tail"] - 0.003, d["r_tail"], z0, z1, "Rod", n=32)  # hollow tail tube
            z0, z1 = zz(d["disk0"], d["disk0"] + d["t_disk"])
            tube(o.mesh, fr, d["r_tail"], d["r_mo"], z0, z1, "Bell_Carrier")         # disc (spoked in reality)
            tau = d["Lm"] / d["n_poles"]
            for k in range(d["n_poles"]):
                z0, z1 = zz(d["disk0"] - d["Lm"] + k * tau, d["disk0"] - d["Lm"] + (k + 1) * tau)
                tube(o.mesh, fr, d["r_mi"], d["r_mo"], z0, z1, "Magnet_N" if k % 2 == 0 else "Magnet_S")

            # ---- stators on both faces of the magnet sleeve
            o = new(f"OPF_{tag}_Stator_Outer_{side}", "OPFPLG_Generator")
            z0, z1 = zz(d["so_u0"], d["so_u1"])
            tube(o.mesh, fr, d["r_so0"], d["r_so1"], z0, z1, "Stator_Coil")
            o = new(f"OPF_{tag}_Stator_Inner_{side}", "OPFPLG_Generator")
            z0, z1 = zz(d["si_u0"], d["si_u1"])
            tube(o.mesh, fr, d["r_si0"], d["r_si1"], z0, z1, "Stator_Inner")

            # ---- linear-generator housing = that piston's propane chamber (bounce + boiling)
            o = new(f"OPF_{tag}_LinearGenerator_{side}", "OPFPLG_Core")
            z0, z1 = zz(d["h0"], d["END"] - d["t_cap"])
            tube(o.mesh, fr, d["r_hi"], d["r_ho"], z0, z1, "LinGen_Housing")
            z0, z1 = zz(d["END"] - d["t_cap"], d["END"])
            cyl(o.mesh, fr, d["r_ho"], z0, z1, "LinGen_Housing")
            o = new(f"OPF_{tag}_Flange_{side}", "OPFPLG_Core")
            z0, z1 = zz(d["h0"] - 0.008, d["h0"])
            tube(o.mesh, fr, d["r_lo"], d["flange_r"], z0, z1, "Housing_Flange")
            z0, z1 = zz(d["END"] - d["t_cap"] - 0.010, d["END"] - d["t_cap"])
            tube(o.mesh, fr, d["r_ho"], d["flange_r"], z0, z1, "Housing_Flange")

            # ---- this piston's propane circuit hardware
            u_v = d["END"] - 0.040
            o = new(f"OPF_{tag}_Spray_Lance_{side}", "OPFPLG_Cooling")
            z0, z1 = zz(d["g"] + d["Lp"] + 0.055, d["END"] - d["t_cap"])
            tube(o.mesh, fr, 0.006, 0.009, z0, z1, "Propane_Liquid", n=16)      # up the hollow tail to the crown
            ju = cb - (d["h_ex"] if s > 0 else d["h_in"]) - 0.030                # jacket half -> housing jumper
            th_j = math.radians(135)
            pipe(o.mesh, [fr.Pc(d["r_lo"] + 0.010, th_j, s * ju), fr.Pc(d["r_b"] + 0.010, th_j, s * ju),
                          fr.Pc(d["r_b"] + 0.010, th_j, s * (d["h0"] + 0.004))], 0.005, "Propane_Liquid", bend=0.012)

            o = new(f"OPF_{tag}_Bleed_Valve_{side}", "OPFPLG_Cooling")
            nv = (0.0, n45, n45)                                                # up and aft, into the valley
            pv0 = (s * u_v, yc + n45 * d["r_ho"], zc + n45 * d["r_ho"])
            pv1 = add(pv0, mul(nv, 0.038))
            pipe(o.mesh, [pv0, pv1], 0.015, "Valve")
            obox(o.mesh, add(pv0, mul(nv, 0.020)), ((1, 0, 0), nv, (0.0, -n45, n45)),
                 (0.030, 0.010, 0.013), "Valve_Actuator")
            o = new(f"OPF_{tag}_Check_Valve_{side}", "OPFPLG_Cooling")
            nl = (0.0, n45, -n45)                                               # down and aft
            pl0 = (s * u_v, yc + n45 * d["r_ho"], zc - n45 * d["r_ho"])
            pl1 = add(pl0, mul(nl, 0.030))
            pipe(o.mesh, [pl0, pl1], 0.011, "Valve")
            pf0 = add(pl0, mul(nl, 0.012))                                     # block feed: along the housing to the bolt face
            pipe(o.mesh, [pf0, (s * (u_v - 0.03), pf0[1], pf0[2]), (s * (d["h0"] + 0.001), pf0[1], pf0[2])], 0.005, "Propane_Liquid", n=8)

            # ---- external lines: vapour to this circuit's condenser sector, liquid back
            pfr = pusher_frame(s)                                               # +X pistons use the left pusher
            name, th_c, span = sector_table(s)[ci]
            dth = math.radians(7.0)
            zlip = PUSHER_Z0 - Z_LIP_OFF
            xt = s * X_TRAY
            zv, zl = TRAY_Z_VAP[ci], TRAY_Z_LIQ[ci]
            o = new(f"OPF_Ext_Vapour_Line_{tag}_{side}", "OPFPLG_External")
            pipe(o.mesh, [pv1, (xt, pv1[1], pv1[2]), (xt, pv1[1] + 0.03, zv), (xt, 1.47, zv),
                          pfr.Pc(R_OUT, th_c - dth, zlip), pfr.Pc(R_OUT, th_c - dth, HX_Z_LE - 0.005),
                          pfr.Pc(R_RING, th_c - dth, HX_Z_LE - 0.005)], 0.011, "Propane_Vapour", bend=0.05, n=12)
            o = new(f"OPF_Ext_Liquid_Return_{tag}_{side}", "OPFPLG_External")
            z_te = HX_Z_LE + HX_CHORD + 0.005
            pipe(o.mesh, [pfr.Pc(R_RING, th_c + dth, z_te), pfr.Pc(R_OUT, th_c + dth, z_te),
                          pfr.Pc(R_OUT, th_c + dth, zlip), (xt, 1.47, zl), (xt, pl1[1] + 0.03, zl),
                          (xt, pl1[1], pl1[2]), pl1], 0.006, "Propane_Liquid", bend=0.04, n=10)

    # ---- ONE metal-printed centre block: three bores, port galleries, cooling galleries, two bolt faces
    ys3 = d["cyl_y"]
    hp_y = d["pitch"] / 2

    def slab(m_, xa, xb, R_out, r_hole, mat, n=96):
        """Solid between x = xa and xb whose outline is a racetrack of radius R_out round the three bore axes
        (flat top and bottom, round ends), with a hole of radius r_hole on each axis."""
        for k, yk in enumerate(ys3):
            ro, ri = [], []
            for i in range(n):
                th = 2 * math.pi * (i + 0.5) / n
                c_, s_ = math.cos(th), math.sin(th)
                inner = (c_ > 0 and k < 2) or (c_ < 0 and k > 0)       # toward a neighbouring cylinder
                rho = R_out / abs(s_)
                rho = min(rho, hp_y / abs(c_)) if inner else min(rho, R_out)
                ro.append((yk + rho * c_, zc + rho * s_, inner and abs(rho * abs(c_) - hp_y) < 1e-9))
                ri.append((yk + r_hole * c_, zc + r_hole * s_))
            for i in range(n):
                j = (i + 1) % n
                (ya, za, fa), (yb, zb, fb) = ro[i], ro[j]
                (yc_, zc_), (yd, zd) = ri[i], ri[j]
                for x in (xa, xb):
                    m_.poly([(x, yc_, zc_), (x, ya, za), (x, yb, zb), (x, yd, zd)], mat)
                if not (fa and fb):                                    # outer wall (not the plane shared by two cells)
                    m_.poly([(xa, ya, za), (xb, ya, za), (xb, yb, zb), (xa, yb, zb)], mat)

    xf, tf_ = d["blk_face"], d["blk_tf"]
    o = new("OPF_Block_Body", "OPFPLG_Block")
    slab(o.mesh, -(xf - tf_), xf - tf_, d["Rb"], d["r_lo"], "Block_Body")
    for s, side in ((-1, "Intake"), (1, "Exhaust")):
        o = new(f"OPF_Block_Bolt_Face_{side}", "OPFPLG_Block")
        slab(o.mesh, s * (xf - tf_), s * xf, d["flange_r"], d["r_lo"], "Printed_Block")
        o = new(f"OPF_Block_Bolts_{side}", "OPFPLG_Block")
        for yk in ys3:
            bf = Frame((0.0, yk, zc), (1, 0, 0))
            for i in range(16):
                p0 = bf.Pc(d["r_bolt"], 2 * math.pi * (i + 0.5) / 16, s * (xf - tf_ - 0.004))
                p1 = bf.Pc(d["r_bolt"], 2 * math.pi * (i + 0.5) / 16, s * (d["h0"] + 0.007))
                pipe(o.mesh, [p0, p1], 0.0045, "Bolt", n=6)
    by0, by1 = ys3[0] - d["Rb"], ys3[2] + d["Rb"]
    o = new("OPF_Block_Mounts", "OPFPLG_Block")
    for s in (-1, 1):
        for y in (by0 + 0.06, by1 - 0.06):
            obox(o.mesh, (s * (xf - tf_ - 0.035), y, zc - d["Rb"] - 0.012), X3, (0.030, 0.035, 0.014), "Printed_Block")

    # ---- electric turbo-compound unit: compressor | motor-generator | turbine (built at 1:1, then scaled radially)
    yT, zT, kT = d["y_T"], d["z_T"], TURBO_K
    R0, rbig = d["scroll_R0"], d["scroll_rbig"]
    tf = Frame((0.0, yT, zT), (1, 0, 0))
    TOP, FRONT = -math.pi / 2, 0.0                  # theta of world +Z and of forward (-Y) in this frame
    NS = 12
    ss = [k / NS for k in range(NS + 1)]
    c_z = [-0.335 + 0.062 * s for s in ss]
    c_rh = [0.013 + 0.039 * s ** 2 for s in ss]
    c_rt = [0.042 + 0.016 * s ** 1.6 for s in ss]
    c_dth = [0.75 * (1 - s) ** 2 - 0.20 * s ** 2 for s in ss]
    t_z = [0.270 + 0.065 * s for s in ss]
    t_rh = [0.013 + 0.039 * (1 - s) ** 2 for s in ss]
    t_rt = [0.056 - 0.008 * s ** 1.5 for s in ss]
    t_dth = [-0.65 * s ** 2 for s in ss]
    turbo_objs = []

    def tnew(name, **kw):
        o = new(name, "OPFPLG_Air", **kw)
        turbo_objs.append(o)
        return o

    o = tnew("OPF_ETurbo_Rotor", origin=(0.0, yT, zT),
             driver=f"frame*{TURBO_SPIN_RAD_PER_FRAME:.4f}", driver_path="rotation_euler", driver_index=0)
    cyl(o.mesh, tf, 0.012, -0.345, 0.345, "Shaft", n=20)
    cyl(o.mesh, tf, 0.055, -0.11, 0.11, "Magnet_N", n=32)
    for k in range(4):
        th = k * math.pi / 2
        er = add(mul(tf.e1, math.cos(th)), mul(tf.e2, math.sin(th)))
        et = add(mul(tf.e1, -math.sin(th)), mul(tf.e2, math.cos(th)))
        obox(o.mesh, add(tf.P(0, 0, 0), mul(er, 0.056)), (er, et, tf.d), (0.002, 0.012, 0.108), "Magnet_S")
    lathe(o.mesh, tf, [(0, -0.338), (0.012, -0.338)] + [(r, z) for r, z in zip(c_rh, c_z)] +
          [(0.056, -0.268), (0, -0.268)], "Compressor_Wheel", n=40, smooth_profile=True)
    cyl(o.mesh, tf, 0.010, -0.350, -0.338, "Shaft", n=6)
    blade_set(o.mesh, tf, 8, c_z, c_rh, c_rt, c_dth, 0.0016, "Compressor_Wheel")
    k0 = NS // 3
    blade_set(o.mesh, tf, 8, c_z[k0:], c_rh[k0:], c_rt[k0:],
              [t + math.pi / 8 for t in c_dth[k0:]], 0.0014, "Compressor_Wheel")
    lathe(o.mesh, tf, [(0, 0.266), (0.054, 0.266)] + [(r, z) for r, z in zip(t_rh, t_z)] +
          [(0.012, 0.338), (0, 0.338)], "Turbine_Wheel", n=40, smooth_profile=True)
    blade_set(o.mesh, tf, 11, t_z, t_rh, t_rt, t_dth, 0.0018, "Turbine_Wheel")

    o = tnew("OPF_ETurbo_Bearings")
    for a, b in ((-0.25, -0.15), (0.15, 0.25)):
        tube(o.mesh, tf, 0.014, 0.035, a, b, "Housing_Flange", n=32)
    o = tnew("OPF_ETurbo_MotorGenerator_Case")
    tube(o.mesh, tf, 0.060, 0.075, -0.13, 0.13, "EMachine")
    for z0_, z1_ in ((-0.15, -0.13), (0.13, 0.15)):
        tube(o.mesh, tf, 0.014, 0.075, z0_, z1_, "EMachine")
    for k in range(9):
        z = -0.10 + k * 0.025
        tube(o.mesh, tf, 0.075, 0.086, z - 0.003, z + 0.003, "EMachine")
    obox(o.mesh, (0.0, yT, zT + 0.085), X3, (0.04, 0.03, 0.015), "HV_Orange")

    o = tnew("OPF_ETurbo_Compressor_Housing")
    rci = 0.075
    torus(o.mesh, tf, rci + 0.012, 0.012, -0.43, "Compressor", nm=10)          # short bellmouth: the tail narrows here
    tube(o.mesh, tf, rci, rci + 0.004, -0.43, -0.40, "Compressor")
    lathe(o.mesh, tf, [(rci, -0.40), (0.052, -0.36), (0.045, -0.340)] + [(r + 0.002, z) for r, z in zip(c_rt, c_z)] +
          [(R0, -0.277)], "Compressor", n=48, smooth_profile=True)
    tube(o.mesh, tf, 0.036, R0 + 0.003, -0.265, -0.261, "Compressor")
    c_port, _ = scroll(o.mesh, tf, -0.271, R0, 0.009, rbig, TOP, "Compressor", "compressor")

    o = tnew("OPF_ETurbo_Turbine_Housing_VGT")
    tube(o.mesh, tf, 0.036, R0 + 0.003, 0.262, 0.266, "Turbine")
    lathe(o.mesh, tf, [(R0, 0.277)] + [(r + 0.002, z) for r, z in zip(t_rt, t_z)] +
          [(0.054, 0.350), (0.075, 0.40)], "Turbine", n=48, smooth_profile=True)
    # exhaust comes down the front of the volute (same swirl as the rotation), exducer exits axially (+X)
    t_port, _ = scroll(o.mesh, tf, 0.272, R0, 0.009, rbig, FRONT, "Turbine", "turbine")
    o = tnew("OPF_ETurbo_VGT_Actuator")
    obox(o.mesh, (0.30, yT + 0.11, zT + 0.135), X3, (0.025, 0.030, 0.012), "VGT_Actuator")

    def tscale(v):
        return (v[0] * TURBO_KA, yT + (v[1] - yT) * kT, zT + (v[2] - zT) * kT)
    for o in turbo_objs:
        o.mesh.v = [tscale(v) for v in o.mesh.v]
    c_port, t_port = tscale(c_port), tscale(t_port)
    d["c_port"], d["t_port"] = c_port, t_port
    rca = d["r_ca"]
    y_lane = t_port[1]

    # ---- gas path: compressor -> charge air cooler (spine) -> intake plenum; collector -> turbine
    cac = d["cac"]
    y_first, y_last = d["cyl_y"][0], d["cyl_y"][2]
    pyf, pya = y_first - 0.07, y_last + 0.07
    pxc, pw = 0.5 * (d["px_in"] + d["px_out"]), d["pl_w"] / 2
    zb, zt = d["pz_bot"], d["pz_top"]
    o = new("OPF_Intake_Manifold", "OPFPLG_Air")
    obox(o.mesh, (-pxc, (pyf + pya) / 2, (zb + zt) / 2), X3, (pw, (pya - pyf) / 2, (zt - zb) / 2), "Intake_Pipe")
    # downcomer from the cooler's front tank into the plenum
    obox(o.mesh, (-pxc, (cac["yf"] + cac["y0"]) / 2, (zt + cac["z0"]) / 2), X3,
         (pw, (cac["y0"] - cac["yf"]) / 2, (cac["z0"] - zt) / 2), "Intake_Pipe")
    o = new("OPF_Charge_Air_Pipe", "OPFPLG_Air")
    xc_in = -0.075
    pipe(o.mesh, [c_port, (c_port[0], y_lane, c_port[2] + 0.003), (-0.115, y_lane, c_port[2] + 0.035),
                  (xc_in, y_lane, 0.860), (xc_in, y_lane, cac["z0"] + 0.005)], rca, "Intake_Hot", bend=0.06)

    o = new("OPF_Charge_Air_Cooler", "OPFPLG_Air")
    hw = cac["hw"]
    zm, zh = (cac["z0"] + cac["z1"]) / 2, (cac["z1"] - cac["z0"]) / 2
    obox(o.mesh, (0, (cac["y0"] + cac["y1"]) / 2, zm), X3, (hw - 0.012, (cac["y1"] - cac["y0"]) / 2, zh - 0.004),
         "CAC_Core")
    nf = 30                                               # plate edges, so the core reads as a bar-and-plate block
    for k in range(nf + 1):
        y = cac["y0"] + (cac["y1"] - cac["y0"]) * k / nf
        obox(o.mesh, (0, y, zm), X3, (hw - 0.010, 0.0012, zh - 0.002), "CAC_Fin")
    obox(o.mesh, (0, (cac["yf"] + cac["y0"]) / 2, zm), X3, (hw, (cac["y0"] - cac["yf"]) / 2, zh), "Intake_Pipe")   # cold tank
    obox(o.mesh, (0, (cac["y1"] + cac["ya"]) / 2, zm), X3, (hw, (cac["ya"] - cac["y1"]) / 2, zh), "Intake_Hot")    # hot tank
    o = new("OPF_CAC_Propane_Headers", "OPFPLG_Cooling")
    for sgn in (-1, 1):
        pipe(o.mesh, [(sgn * (hw - 0.004), cac["y0"] - 0.01, cac["z0"] + 0.004), (sgn * (hw - 0.004), cac["y1"], cac["z0"] + 0.004)],
             0.010, "Aux_Liquid", n=10)
        pipe(o.mesh, [(sgn * (hw - 0.020), cac["y0"], cac["z1"] + 0.004), (sgn * (hw - 0.020), cac["y1"] + 0.01, cac["z1"] + 0.004)],
             0.015, "Aux_Vapour", n=10)

    o = new("OPF_Exhaust_Collector", "OPFPLG_Air")
    dk = d["deck"]
    y_step = dk["y1"] + 0.035
    obox(o.mesh, (pxc, (pyf + y_step) / 2, (zb + zt) / 2), X3, (pw, (y_step - pyf) / 2, (zt - zb) / 2), "Exhaust_Pipe")
    y_ce = y_lane - 0.055
    obox(o.mesh, (pxc, (y_step + y_ce) / 2, (zb + d["col_top"]) / 2), X3,
         (pw, (y_ce - y_step) / 2, (d["col_top"] - zb) / 2), "Exhaust_Pipe")
    zcol = (zb + d["col_top"]) / 2
    pipe(o.mesh, [(pxc, y_ce - 0.02, zcol), (pxc + 0.004, y_lane, zcol - 0.035), (0.200, y_lane, t_port[2] + 0.075),
                  (t_port[0], y_lane, t_port[2] + 0.040), t_port], rca, "Exhaust_Pipe", bend=0.06)
    o = new("OPF_CAC_Heat_Shield", "OPFPLG_Air")
    obox(o.mesh, (0.075, (cac["yf"] + cac["ya"]) / 2, (d["col_top"] + cac["z0"]) / 2), X3,
         (0.078, (cac["ya"] - cac["yf"]) / 2, 0.0015), "Heat_Shield")

    o = new("OPF_Fuel_Rail", "OPFPLG_Core")
    pipe(o.mesh, [(0.0, ENV["y"][0] + 0.01, rail_z), (0.0, y_last + 0.13, rail_z)], 0.008, "Fuel_Rail")

    # ---- exhaust downpipe: out of the turbine, down beside the housing, aft under the belly
    EXH_DOWN_DEG = 20.0
    a_ = math.radians(EXH_DOWN_DEG)
    xe0 = 0.40 * TURBO_KA
    p3 = (xe0 + 0.02, yT + 0.32, 0.385)
    exit_ = (p3[0], p3[1] + 0.15 * math.cos(a_), p3[2] - 0.15 * math.sin(a_))
    d["exhaust_exit"] = exit_
    o = new("OPF_Ext_Exhaust_Downpipe", "OPFPLG_External")
    pipe(o.mesh, [(xe0, yT, zT), (xe0 + 0.03, yT, zT), (xe0 + 0.08, yT, zT), (xe0 + 0.05, yT + 0.14, 0.45), p3, exit_],
         d["r_dp"], "Exhaust_Pipe", bend=0.12)

    # ---- power-electronics deck ahead of the rear wing: 6 inverters, DC/DC, controller placeholder
    zd = dk["z"]
    o = new("OPF_Electronics_Deck", "OPFPLG_Electrical")
    obox(o.mesh, (0, (dk["y0"] + dk["y1"]) / 2, zd), X3, (dk["hw"], (dk["y1"] - dk["y0"]) / 2, 0.002), "Deck")
    inv_hx, inv_hy, inv_h = 0.115, 0.058, 0.056
    rows = [dk["y0"] + 0.068 + k * 0.135 for k in range(3)]
    zi0 = zd + 0.002
    inv_pos = {}
    o_cp = new("OPF_Cold_Plates", "OPFPLG_Cooling")
    o = new("OPF_Inverters", "OPFPLG_Electrical")
    for ci, yr in enumerate(rows):
        for sgn in (-1, 1):
            xc = sgn * 0.225
            obox(o_cp.mesh, (xc, yr, zi0 + 0.003), X3, (inv_hx, inv_hy, 0.003), "Cold_Plate")
            obox(o.mesh, (xc, yr, zi0 + 0.006 + inv_h / 2), X3, (inv_hx, inv_hy, inv_h / 2), "Inverter")
            obox(o.mesh, (xc, yr, zi0 + 0.006 + inv_h + 0.0015), X3, (inv_hx - 0.008, inv_hy - 0.008, 0.0015), "Inverter_Lid")
            inv_pos[(ci, sgn)] = (xc, yr, zi0 + 0.006 + inv_h / 2)
    o = new("OPF_DCDC_Converter", "OPFPLG_Electrical")
    y_dc = 0.5 * (rows[0] + rows[1])
    obox(o_cp.mesh, (0, y_dc, zi0 + 0.003), X3, (0.075, 0.120, 0.003), "Cold_Plate")
    obox(o.mesh, (0, y_dc, zi0 + 0.006 + inv_h / 2), X3, (0.075, 0.120, inv_h / 2), "DCDC")
    o = new("OPF_Control_Electronics_Placeholder", "OPFPLG_Electrical")
    obox(o.mesh, (0, rows[2], zi0 + 0.026), X3, (0.075, 0.055, 0.026), "Controller")

    # AC leads: inverter -> its stator terminal on top of the housing, outboard
    u_term = d["so_u1"] - 0.030
    z_term = zc + d["r_ho"]
    o = new("OPF_AC_Leads", "OPFPLG_Electrical")
    for (ci, sgn), (xi, yi, zi) in inv_pos.items():
        yc = d["cyl_y"][ci]
        xo = sgn * (u_term + 0.006 * (ci - 1))
        ztr = zd + 0.012 + 0.0
        pts = [(xi + sgn * inv_hx, yi, zi), (sgn * (dk["hw"] + 0.012), yi, zi), (sgn * (dk["hw"] + 0.012), yi, ztr)]
        if ci > 0:
            pts += [(xo, dk["y1"] + 0.02, z_term + 0.016), (xo, yc - 0.03, z_term + 0.016)]
        pts += [(xo, yc, z_term + 0.012), (xo, yc, z_term - 0.004)]
        pipe(o.mesh, pts, 0.009, "AC_Lead", bend=0.02, n=10)
    # 900 V DC link along the deck, e-turbo feed, DC/DC, then the single feed down to the LTO pack
    z_bus = zi0 + 0.006 + inv_h + 0.012
    o = new("OPF_DC_Bus", "OPFPLG_Electrical")
    for sgn in (-1, 1):
        pipe(o.mesh, [(sgn * 0.095, rows[0] - 0.04, z_bus), (sgn * 0.095, rows[2] + 0.04, z_bus)], 0.007, "HV_Orange", n=10)
        for yr in rows:
            pipe(o.mesh, [(sgn * 0.095, yr, z_bus), (sgn * 0.125, yr, z_bus), (sgn * 0.125, yr, z_bus - 0.014)],
                 0.005, "HV_Orange", bend=0.008, n=8)
    pipe(o.mesh, [(-0.095, y_dc, z_bus), (0.095, y_dc, z_bus)], 0.007, "HV_Orange", n=10)
    pipe(o.mesh, [(0.0, yT, zT + 0.115 * 1.0), (0.0, yT - 0.02, cac["z1"] + 0.009), (0.0, cac["yf"] - 0.01, cac["z1"] + 0.009),
                  (0.0, dk["y1"] - 0.01, z_bus + 0.02), (0.060, dk["y1"] - 0.03, z_bus)], 0.006, "HV_Orange", bend=0.03, n=10)
    o = new("OPF_HV_Main_Feed", "OPFPLG_Electrical")
    y_feed = 0.5 * (d["cyl_y"][0] + d["cyl_y"][1]) - 0.10
    x_conn = ACC_W / 2
    z_conn = ACC_TOP_BAY - ACC_H / 2
    pipe(o.mesh, [(0.075, y_dc + 0.06, z_bus), (0.30, y_feed, z_bus + 0.004), (X_TRAY, y_feed, z_bus - 0.02),
                  (X_TRAY, y_feed, 0.585), (0.497, y_feed, 0.472), (x_conn + 0.055, y_feed, z_conn), (x_conn, y_feed, z_conn)],
         0.012, "HV_Orange", bend=0.035)
    obox(o.mesh, (x_conn + 0.018, y_feed, z_conn), X3, (0.018, 0.028, 0.022), "HV_Orange")   # pack connector
    d["y_feed"], d["x_feed"] = y_feed, x_conn

    # ---- auxiliary propane circuits (left / right): receiver + pump -> inverter cold plates -> charge air
    #      cooler -> top sector of that side's pusher condenser
    o_rc = new("OPF_Aux_Receivers", "OPFPLG_Cooling")
    for sgn, side in ((1, "L"), (-1, "R")):
        pfr = pusher_frame(sgn)
        zlip = PUSHER_Z0 - Z_LIP_OFF
        th_a = math.radians(-90.0)
        dth = math.radians(10.0) * sgn
        zr = 0.468
        cyl(o_rc.mesh, Frame((sgn * 0.085, yT, zr), (1, 0, 0)), 0.036, -0.058, 0.058, "Aux_Liquid", n=24)
        obox(o_rc.mesh, (sgn * 0.085, yT - 0.060, zr), X3, (0.030, 0.022, 0.022), "Valve_Actuator")     # feed pump
        y_val = 0.5 * (d["cyl_y"][1] + d["cyl_y"][2])          # lower valley between cylinders 2 and 3
        y_up = 0.5 * (d["cyl_y"][0] + d["cyl_y"][1]) + 0.05
        o = new(f"OPF_Aux_Liquid_Feed_{side}", "OPFPLG_Cooling")
        xe = sgn * (dk["hw"] - 0.012)
        pipe(o.mesh, [(sgn * 0.085, yT - 0.082, zr), (sgn * 0.085, y_val, 0.455), (sgn * 0.400, y_val, 0.460),
                      (sgn * 0.400, y_up, 0.460), (sgn * (X_TRAY - 0.004), y_up, 0.565), (sgn * (X_TRAY - 0.004), y_up, zd + 0.016),
                      (xe, y_up, zd + 0.010), (xe, rows[0] - 0.05, zd + 0.010)], 0.008, "Aux_Liquid", bend=0.03, n=10)
        pipe(o.mesh, [(xe, dk["y1"] - 0.012, zd + 0.010), (xe, y_up + 0.02, zd + 0.010)], 0.008, "Aux_Liquid", n=10)
        # deck manifold -> cooler liquid header
        pipe(o.mesh, [(xe, dk["y1"] - 0.012, zd + 0.010), (sgn * 0.20, cac["yf"] - 0.004, cac["z0"] - 0.020),
                      (sgn * (hw - 0.004), cac["y0"] - 0.01, cac["z0"] + 0.004)], 0.008, "Aux_Liquid", bend=0.03, n=10)
        for yr in rows:                                   # cold-plate branches
            pipe(o.mesh, [(xe, yr, zd + 0.010), (sgn * 0.300, yr, zd + 0.006)], 0.005, "Aux_Liquid", n=8)
        o = new(f"OPF_Ext_Vapour_Line_Aux_{side}", "OPFPLG_External")
        pipe(o.mesh, [(sgn * (hw - 0.020), cac["y1"] + 0.01, cac["z1"] + 0.004), (sgn * 0.110, cac["ya"] + 0.05, 1.040),
                      (sgn * 0.110, 1.80, 1.040), pfr.Pc(R_OUT, th_a - dth, zlip),
                      pfr.Pc(R_OUT, th_a - dth, HX_Z_LE - 0.005), pfr.Pc(R_RING, th_a - dth, HX_Z_LE - 0.005)],
             0.015, "Aux_Vapour", bend=0.06, n=12)
        o = new(f"OPF_Ext_Liquid_Return_Aux_{side}", "OPFPLG_External")
        z_te = HX_Z_LE + HX_CHORD + 0.005
        pipe(o.mesh, [pfr.Pc(R_RING, th_a + dth, z_te), pfr.Pc(R_OUT, th_a + dth, z_te), pfr.Pc(R_OUT, th_a + dth, zlip),
                      (sgn * 0.070, 1.86, 0.950), (sgn * 0.070, 1.70, 0.560), (sgn * 0.085, yT + 0.10, zr + 0.01),
                      (sgn * 0.085, yT + 0.058, zr)], 0.009, "Aux_Liquid", bend=0.05, n=10)

    # ---- accumulator: 162S LTO power pack in a rectangular case (unchanged)
    o = new("OPF_Accumulator_Case", "OPFPLG_Accumulator")
    acc_c = (ACC_C[0], ACC_C[1], ACC_C[2] + ENGINE_DZ)
    obox(o.mesh, acc_c, X3, (ACC_W / 2, ACC_L / 2, ACC_H / 2), "Accumulator")
    o = new("OPF_Accumulator_Cells", "OPFPLG_Accumulator")
    cw, ct, ch = LTO_CELL
    x0 = -ACC_W / 2 + LTO_WALL + LTO_CLR + LTO_END + cw / 2
    y0c = ACC_Y0 + LTO_WALL + LTO_CLR + LTO_END + LTO_PITCH_Y / 2
    zcc = ACC_TOP_BAY - ACC_H + LTO_WALL + LTO_CLR + ch / 2
    for i in range(LTO_NX):
        xc = x0 + i * (cw + LTO_GAP_X)
        for j in range(LTO_NY):
            ycj = y0c + j * LTO_PITCH_Y
            obox(o.mesh, (xc, ycj, zcc), X3, (cw / 2, ct / 2, ch / 2), "LTO_Cell")
            for k in (-1, 1):
                obox(o.mesh, (xc + k * 0.035, ycj, zcc + ch / 2 + 0.003), X3, (0.011, 0.007, 0.003), "Cell_Terminal")
    o = new("OPF_Accumulator_Busbars", "OPFPLG_Accumulator")
    zbb = zcc + ch / 2 + 0.007
    for i in range(LTO_NX):
        xc = x0 + i * (cw + LTO_GAP_X)
        for k in (-1, 1):
            obox(o.mesh, (xc + k * 0.035, y0c + (LTO_NY - 1) * LTO_PITCH_Y / 2, zbb), X3,
                 (0.012, (LTO_NY - 1) * LTO_PITCH_Y / 2 + 0.008, 0.001), "Busbar")
    d["acc"] = dict(n=LTO_NX * LTO_NY, kwh=LTO_NX * LTO_NY * 0.046, kg=LTO_NX * LTO_NY * 0.545,
                    kw10=LTO_NX * LTO_NY * 1.9, v_nom=LTO_NX * LTO_NY * 2.3)

    # ---- pusher-fan condensers: structural vanes + annular finned core, four circuit sectors each
    for sgn, side in ((1, "L"), (-1, "R")):
        df = pusher_frame(sgn)
        o = new(f"OPF_Fan_HX_{side}", "OPFPLG_Radiators")
        z_le, chord = HX_Z_LE, HX_CHORD
        tube(o.mesh, df, PUSHER_HUB_R - 0.004, PUSHER_HUB_R + 0.003, z_le - 0.01, z_le + chord + 0.01, "Printed_HX")
        for k in range(5):                                   # concentric splitter rings carrying the fin pack
            r = PUSHER_HUB_R + (0.355 - PUSHER_HUB_R) * (k + 1) / 6
            tube(o.mesh, df, r - 0.0012, r + 0.0012, z_le + 0.006, z_le + chord - 0.006, "HX_Fin", n=64)
        # thin cambered fins only (no thick vanes): about 20 deg at the leading edge against the rotor swirl,
        # axial at the trailing edge, evenly spaced all the way round. With the splitter rings they straighten
        # the flow and carry the hub; the propane runs in the rings. Drawn at about 1/10 of the real fin count.
        for k in range(N_FINS_DRAWN):
            th = 2 * math.pi * k / N_FINS_DRAWN + 0.12
            vane(o.mesh, df, th, PUSHER_HUB_R + 0.003, 0.357, z_le, chord, 0.008, sgn * FIN_CAMBER, "HX_Fin", np_=6)
        o = new(f"OPF_Fan_HX_Headers_{side}", "OPFPLG_Radiators")
        for name, th_c, span in sector_table(sgn):
            aux = name == "Aux"
            h = span / 2 - math.radians(2.5)
            arc(o.mesh, df, R_RING, z_le - 0.005, th_c - h, th_c + h, 0.015, "Aux_Vapour" if aux else "Propane_Vapour",
                n=max(8, int(span / 0.12)))
            arc(o.mesh, df, R_RING, z_le + chord + 0.005, th_c - h, th_c + h, 0.012, "Aux_Liquid" if aux else "Propane_Liquid",
                n=max(8, int(span / 0.12)))
            for e in (-1, 1):                                # sector dividers in the duct wall
                er = add(mul(df.e1, math.cos(th_c + e * span / 2)), mul(df.e2, math.sin(th_c + e * span / 2)))
                et = add(mul(df.e1, -math.sin(th_c + e * span / 2)), mul(df.e2, math.cos(th_c + e * span / 2)))
                obox(o.mesh, add(df.P(0, 0, z_le + chord / 2), mul(er, R_RING)), (er, et, df.d),
                     (0.018, 0.003, chord / 2 + 0.012), "Printed_HX")
    return d, objs





# ------------------------------------------------------ performance + fit ---
LHV_PROPANE = 46.35e6


def t_sat(p_pa):
    """Propane saturation temperature, K (Antoine, NIST, 278-361 K)."""
    return 1149.36 / (4.53678 - math.log10(p_pa / 1e5)) - 24.906


def body_ztop(x, y):
    """Top skin height at (x, y) from the X1 SkyRacer station table."""
    _, hw, top, bot, nu, _ = hull_row(y)
    if abs(x) >= hw:
        return 0.5 * (top + bot)
    zc_, hh = 0.5 * (top + bot), 0.5 * (top - bot)
    return zc_ + hh * (1 - (abs(x) / hw) ** nu) ** (1 / nu)


def wing_low(y):
    """Estimated lower surface of the rear wing root (stub from |x| 0.15, 1.20 m chord centred on y 1.20,
    9 deg incidence, 9 % thick), or None outside the chord. Estimate only: check against x1_skyracer_blender.py."""
    c, yc, zc_ = 1.20, 1.20, 0.95
    u = (y - yc) / c + 0.5
    if not 0.0 <= u <= 1.0:
        return None
    t = 5 * 0.09 * c * (0.2969 * math.sqrt(u) - 0.1260 * u - 0.3516 * u ** 2 + 0.2843 * u ** 3 - 0.1036 * u ** 4)
    return zc_ - (y - yc) * math.sin(math.radians(9.0)) - t


def mass_estimate(d):
    """Built-up mass estimate, kg (about +/-20 %). Engine = stators + moving parts + printed block and casing."""
    pi = math.pi
    RHO_COFE, RHO_ALW = 8120.0, 2700.0

    def sh(ri, ro, L, rho):
        return pi * (ro * ro - ri * ri) * L * rho

    def stator(r0, r1, L, inner):                 # back iron + slot zone (30 % teeth, 48 % aluminium, resin)
        if inner:
            ry0, ry1, rs0, rs1 = r0, r0 + T_YOKE, r0 + T_YOKE, r1
        else:
            ry0, ry1, rs0, rs1 = r1 - T_YOKE, r1, r0, r1 - T_YOKE
        return sh(ry0, ry1, L, RHO_COFE) + sh(rs0, rs1, L, 0.30 * RHO_COFE + 0.48 * RHO_ALW + 0.06 * 1500.0)
    so = stator(d["r_so0"], d["r_so1"], d["so_u1"] - d["so_u0"], False)
    si = stator(d["r_si0"], d["r_si1"], d["si_u1"] - d["si_u0"], True)
    centre = (sh(d["r_li"], d["r_lo"], 2 * d["L_l"], RHO_AL) + sh(d["r_lo"], d["r_band"], 2 * L_BAND, RHO_AL)
              + 2 * (2 * pi * (d["r_lo"] + 0.016) * 0.050 * 2 * 0.003 * RHO_AL)            # port belt skins
              + 2 * pi * (d["r_lo"] + 0.012) * 2 * d["cb"] * 0.002 * RHO_AL * 0.6 + 1.2)   # jacket skin, bosses
    hl = (d["END"] - d["t_cap"]) - d["h0"]
    housing = (sh(d["r_hi"], d["r_ho"], hl, RHO_AL) + pi * d["r_ho"] ** 2 * 0.007 * RHO_AL   # ribbed domed cap
               + 2 * sh(d["r_ho"], d["flange_r"], 0.008, RHO_AL) + sh(d["r_lo"], d["flange_r"], 0.006, RHO_AL) + 0.6)
    # centre block beyond the bore walls and galleries: 3 mm outer skin, two pocketed bolt faces, webs between
    # the bores, mount bosses, plus an allowance for injector bosses and internal ribbing
    pitch_, Rb, Rf = d["pitch"], d["Rb"], d["flange_r"]
    body_len = 2 * (d["blk_face"] - d["blk_tf"])
    skin = (4 * pitch_ + 2 * pi * Rb) * body_len * 0.003
    faces = 2 * (4 * pitch_ * Rf + pi * Rf * Rf - 3 * pi * d["r_lo"] ** 2) * d["blk_tf"] * 0.6
    webs = 2 * (2 * Rb * body_len) * 0.004
    ties = (skin + faces + webs) * RHO_AL + 4 * 0.5 + 5.0
    acc = d.get("acc", dict(kg=LTO_NX * LTO_NY * 0.545))
    m = dict(stators_outer=6 * so, stators_inner=6 * si, moving=6 * d["m_move"], centre_sections=3 * centre,
             housings=6 * housing, block_ties=ties, fasteners=9.0, valves_injectors=9.0,
             air_path=72.0, electronics=90.0, cooling=86.0, pack=acc["kg"] + 14.0)
    m["block"] = m["centre_sections"] + m["housings"] + m["block_ties"] + m["fasteners"]
    m["engine"] = m["stators_outer"] + m["stators_inner"] + m["moving"] + m["block"] + m["valves_injectors"]
    m["package"] = m["engine"] + m["air_path"] + m["electronics"] + m["cooling"] + m["pack"]
    return m


def performance(d):
    c = CYCLE
    n, f = 6, c["f"]
    A = d["A"]
    r = {}
    r["fuel_kw"] = n * c["Qf"] * f / 1e3
    r["fuel_gps"] = r["fuel_kw"] * 1e3 / LHV_PROPANE * 1e3
    r["gen_kw"] = n * c["E_el"] * f / 1e3                 # out of the six stator sets (AC)
    r["eta_inv"] = 0.985
    r["bus_gen_kw"] = r["gen_kw"] * r["eta_inv"]
    # air path
    m_fuel = r["fuel_gps"] / 1e3
    r["delivery"] = 1.20
    m_air = n * 0.90 * c["m_trap"] * r["delivery"] * f
    m_exh = m_air + m_fuel
    T_amb, T_cac = 303.0, 335.0
    r["pr"] = (c["p_s"] + 0.08e5) / 0.98e5
    eta_c, eta_t = 0.80, 0.82
    T2 = T_amb * (1 + (r["pr"] ** 0.2857 - 1) / eta_c)
    P_c = m_air * 1005.0 * (T2 - T_amb)
    r["cac_kw"] = m_air * 1005.0 * (T2 - T_cac) / 1e3
    E_exh = n * f * (0.975 * c["Qf"] - c["W_gas"] - c["Q_wall"])
    T_exh = T_cac + E_exh / (m_exh * 1100.0)
    er = c["p_s"] * 0.90 / 1.06e5
    P_t = m_exh * 1150.0 * T_exh * eta_t * (1 - er ** -0.248)
    net = 0.98 * P_t - P_c
    r["turbo_kw"] = (net * 0.95 if net > 0 else net / 0.95) / 1e3
    r.update(m_air=m_air, m_exh=m_exh, T2=T2, T_exh=T_exh, er=er, comp_kw=P_c / 1e3, turb_kw=P_t / 1e3)
    r["aux_kw"] = 3.0                                      # propane feed pumps, valves, controller
    r["net_kw"] = r["bus_gen_kw"] + r["turbo_kw"] - r["aux_kw"]
    r["net_hp"] = r["net_kw"] / 0.7457
    r["eta"] = r["net_kw"] / r["fuel_kw"]
    r["eta_ind"] = c["W_gas"] / c["Qf"]
    r["endurance_min"] = 200 * 0.4536 / (r["fuel_gps"] / 1e3) / 60.0
    # generator force margins
    r["cont_margin"] = SIGMA_CONT / c["sig_rms"]
    r["peak_margin"] = PEAK_OVER_CONT * SIGMA_CONT / c["sig_pk"]
    r["wind_frac"] = c["e_cu"] / c["E_mech"]
    r["wind_kw"] = c["e_cu"] * f / 1e3
    r["mass"] = mass_estimate(d)
    gam = 1.35
    w_c = c["p_s"] * A * d["x_po"] / (gam - 1) * (d["cr"] ** (gam - 1) - 1)
    r["w_comp"] = w_c
    r["motor_only_boost"] = d["F_pk"] * (d["x_po"] - d["g"]) / w_c
    r["motor_only_start"] = r["motor_only_boost"] * c["p_s"] / 1.0e5
    # heat: one piston circuit, and one auxiliary circuit
    hyst = 2 * 0.012 * c["pb_mean"] * A * c["stroke"] * f
    q_p = (c["Q_wall"] + c["W_fric"] + (c["E_mech"] - c["E_el"])) * f + hyst
    r["q_piston_kw"] = q_p / 1e3
    r["q_parts"] = dict(wall=c["Q_wall"] * f / 1e3, friction=c["W_fric"] * f / 1e3,
                        stator=(c["E_mech"] - c["E_el"]) * f / 1e3, bounce=hyst / 1e3)
    q_inv = r["gen_kw"] * (1 - r["eta_inv"]) + 4.0 + 3.0   # six inverters + DC/DC + e-turbo machine
    r["q_aux_kw"] = (r["cac_kw"] + q_inv) / 2
    r["q_total_kw"] = 6 * r["q_piston_kw"] + 2 * r["q_aux_kw"]
    r["p_cond"] = c["pb_min"] + 0.35 * (c["pb_max"] - c["pb_min"])
    r["T_cond_p"] = t_sat(r["p_cond"])
    r["T_boil_min"], r["T_boil_max"] = t_sat(c["pb_min"]), t_sat(c["pb_max"])
    r["T_cond_aux"] = 332.0
    r["vap_piston_gps"] = r["q_piston_kw"] / 262.0 * 1e3
    r["bleed_frac"] = r["vap_piston_gps"] / 1e3 / f / 52.0 / (A * c["stroke"])   # of swept volume per cycle, ~52 kg/m3
    # condenser per pusher at cruise (60 m/s through the duct): fin area needed on a 35 C day and a 15 C day,
    # against what a compact fin pack filling the annulus can hold (about 1,100 m2 per m3)
    a_ann = math.pi * (0.357 ** 2 - PUSHER_HUB_R ** 2)
    m_fan = 1.12 * 60.0 * a_ann

    def fin_area(T_air):
        area, ok = 0.0, True
        for q, Tc, frac in [(r["q_piston_kw"], r["T_cond_p"], (1 - AUX_SPAN_DEG / 360.0) / 3)] * 3 + \
                           [(r["q_aux_kw"], r["T_cond_aux"], AUX_SPAN_DEG / 360.0)]:
            mi = m_fan * frac
            eps = q * 1e3 / (mi * 1005.0 * (Tc - T_air))
            if eps >= 0.97:
                ok, eps = False, 0.97
            area += -math.log(1 - eps) * mi * 1005.0 / (300.0 * 0.85)
        return area, ok
    r["hx_area_hot"], r["hx_ok_hot"] = fin_area(308.0)
    r["hx_area_std"], r["hx_ok_std"] = fin_area(288.0)
    r["hx_area_pack"] = a_ann * HX_CHORD * 1100.0
    r.update(fan_air=m_fan, q_fan_kw=3 * r["q_piston_kw"] + r["q_aux_kw"],
             hx_dT=(3 * r["q_piston_kw"] + r["q_aux_kw"]) * 1e3 / (m_fan * 1005.0),
             vane_area=0.0)
    r["mep_bar"] = c["imep"] / 1e5
    return r


def reference_objects():
    objs = []
    o = Obj("OPF_REF_Bay_Envelope", "OPFPLG_Reference", display="WIRE")
    x0, x1 = ENV["x"]; y0, y1 = ENV["y"]; z0, z1 = ENV["z"]
    c = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    o.mesh.v = c
    o.mesh.e = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    objs.append(o)
    for sgn, side in ((1, "L"), (-1, "R")):
        df = pusher_frame(sgn)
        o = Obj(f"OPF_REF_Pusher_Duct_{side}", "OPFPLG_Reference", display="WIRE")
        tube(o.mesh, df, PUSHER_R0, PUSHER_R1, PUSHER_Z0, PUSHER_Z1, "Ref_Duct", n=64)
        cyl(o.mesh, df, PUSHER_HUB_R, 0.0, PUSHER_HUB_L, "Ref_Duct")
        tube(o.mesh, df, PUSHER_HUB_R, PUSHER_R0 - 0.01, PUSHER_ROTOR_Z - 0.004, PUSHER_ROTOR_Z + 0.004, "Ref_Duct", n=64)
        objs.append(o)
    # anchors matching the X1 SkyRacer script's empties / part origins (metres, nose -Y, Z up)
    for name, loc, size in (("OPF_X1_Craft_Origin", (0.0, 0.0, 0.0), 0.6),
                            ("OPF_REF_Engine_Bay", (0.0, 0.5 * (ENV["y"][0] + ENV["y"][1]), 0.5 * (ENV["z"][0] + ENV["z"][1])), 0.25),
                            ("OPF_REF_Thruster_L", (PUSHER_X, PUSHER_Y, PUSHER_Z), 0.2),
                            ("OPF_REF_Thruster_R", (-PUSHER_X, PUSHER_Y, PUSHER_Z), 0.2)):
        e = Obj(name, "OPFPLG_Reference", origin=loc, display="EMPTY")
        e.size = size
        objs.append(e)
    return objs



def fit_report(d, objs):
    c = CYCLE
    P = performance(d)
    cyl_objs = [o for o in objs if o.coll in ("OPFPLG_Core", "OPFPLG_Generator", "OPFPLG_Block")]
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in cyl_objs:
        shifts = [(0, 0, 0)] + ([o.travel] if o.travel else [])
        for sh in shifts:
            for v in o.mesh.v:
                for k in range(3):
                    lo[k] = min(lo[k], v[k] + sh[k]); hi[k] = max(hi[k], v[k] + sh[k])
    L = []
    L.append(f"X1 OPFPLG 1,500 hp - {d['note']}")
    L.append(f"  bore {d['B'] * 1000:.0f} mm, stroke {c['stroke'] * 1000:.0f} mm per piston, 3 cylinders x 2 pistons, "
             f"{d['disp'] * 1000:.1f} L swept, compression ratio {c['cr']:.0f}:1 after port closure")
    L.append(f"  CYCLE MODEL (opf_cycle.py), continuous point: {c['f']:.1f} Hz, mean piston speed {c['v_mean']:.1f} m/s, "
             f"scavenge {c['p_s'] / 1e5:.2f} bar abs, lambda {c['lam']:.2f}, IMEP {P['mep_bar']:.1f} bar, peak {c['p_max'] / 1e5:.0f} bar")
    L.append(f"    fuel {P['fuel_kw']:.0f} kW ({P['fuel_gps']:.1f} g/s propane) -> indicated {P['eta_ind'] * 100:.1f} % -> "
             f"stators {P['gen_kw']:.0f} kW -> DC link {P['bus_gen_kw']:.0f} kW")
    L.append(f"    e-turbo: compressor {P['comp_kw']:.0f} kW at PR {P['pr']:.2f}, turbine {P['turb_kw']:.0f} kW at {P['T_exh']:.0f} K, "
             f"net {P['turbo_kw']:+.0f} kW to the DC link")
    L.append(f"    NET {P['net_kw']:.0f} kW = {P['net_hp']:.0f} hp continuous at {P['eta'] * 100:.1f} % fuel-to-DC; "
             f"200 lb of propane lasts {P['endurance_min']:.0f} min at this power")
    b = c.get("burst")
    if b:
        L.append(f"    burst point (scavenge {b['p_s'] / 1e5:.1f} bar, lambda {b['lam']:.2f}): {b['bus_hp']:.0f} hp from the engine, "
                 f"peak {b['p_max'] / 1e5:.0f} bar; with the LTO pack ({d['acc']['kw10'] * 1.341:.0f} hp for 10 s) the 2,000 hp ceiling is covered")
    L.append(f"  LINEAR GENERATOR (per piston): double-sided magnet sleeve {2 * d['r_mo'] * 1000:.0f} mm dia x {d['Lm'] * 1000:.0f} mm, "
             f"{d['n_poles']} poles, moving mass {d['m_move']:.1f} kg (magnets {d['mass']['magnets']:.1f} kg)")
    L.append(f"    stators: cobalt-iron cores, aluminium windings in {T_SLOT * 1000:.0f} mm slots; outer stator covers "
             f"{d['cover_out_idc'] * 100:.0f} / {d['cover_out_mid'] * 100:.0f} / {d['cover_out_odc'] * 100:.0f} % of the sleeve at inner / mid / outer dead centre")
    L.append(f"    air-gap area {d['A_out'] + d['A_in']:.3f} m2 ({d['A_eff']:.3f} m2 working at mid stroke; inner stator covers "
             f"{d['cover_idc'] * 100:.0f} / {d['cover_mid'] * 100:.0f} / {d['cover_odc'] * 100:.0f} % at inner / mid / outer dead centre)")
    L.append(f"    force {c['F_rms'] / 1e3:.1f} kN rms, {c['F_peak'] / 1e3:.1f} kN peak; air-gap shear {c['sig_rms'] / 1e3:.0f} kPa rms against the "
             f"{SIGMA_CONT / 1e3:.0f} kPa continuous yardstick: margin x{P['cont_margin']:.2f}")
    L.append(f"    peak shear {c['sig_pk'] / 1e3:.0f} kPa against {PEAK_OVER_CONT * SIGMA_CONT / 1e3:.0f} kPa short-term: margin x{P['peak_margin']:.2f}")
    L.append(f"    winding loss {P['wind_frac'] * 100:.1f} % of converted power ({P['wind_kw']:.1f} kW per piston into boiling propane), "
             f"core loss {FE_FRAC * 100:.1f} %")
    L.append(f"    motor alone, bounce chamber vented: can drive a full compression stroke x{P['motor_only_boost']:.2f} at full boost, "
             f"x{P['motor_only_start']:.1f} at start (compression work {P['w_comp'] / 1e3:.2f} kJ)")
    L.append(f"    peak gas load {c['p_max'] * d['A'] / 1e3:.0f} kN is carried by piston inertia (as in every free-piston engine), not by the machine")
    L.append(f"    recommended DC link 900 V (SiC), tied to the {d['acc']['v_nom']:.0f} V LTO pack through the deck DC/DC")
    L.append(f"  PROPANE CHAMBERS (one per piston): gas volume {d['Vb_idc'] * 1e3:.1f} -> {d['Vb_odc'] * 1e3:.1f} L, "
             f"pressure {c['pb_min'] / 1e5:.1f} -> {c['pb_max'] / 1e5:.1f} bar each stroke (boils at {P['T_boil_min'] - 273.15:.0f}-{P['T_boil_max'] - 273.15:.0f} C)")
    q = P["q_parts"]
    L.append(f"    heat per circuit {P['q_piston_kw']:.0f} kW (crown + liner {q['wall']:.0f}, stators {q['stator']:.1f}, friction {q['friction']:.1f}, "
             f"bounce losses {q['bounce']:.1f}) -> {P['vap_piston_gps']:.0f} g/s of vapour, "
             f"{P['bleed_frac'] * 100:.0f} % of the swept volume bled per stroke")
    L.append(f"    condenser side held near {P['p_cond'] / 1e5:.1f} bar ({P['T_cond_p'] - 273.15:.0f} C): liquid enters through the check valve "
             f"at the low end of the swing, vapour leaves through the bleed valve at the high end")
    L.append(f"  CHARGE AIR COOLER: {P['m_air']:.2f} kg/s from {P['T2'] - 273.15:.0f} C to 62 C, {P['cac_kw']:.0f} kW into the two auxiliary "
             f"circuits ({P['q_aux_kw']:.0f} kW each with the inverter cold plates)")
    L.append(f"  HEAT REJECTION: {P['q_total_kw']:.0f} kW total, {P['q_fan_kw']:.0f} kW per pusher; at 60 m/s through the duct "
             f"({P['fan_air']:.0f} kg/s) the air warms {P['hx_dT']:.0f} K")
    L.append(f"    fin area needed per pusher: {P['hx_area_std']:.0f} m2 on a 15 C day, {P['hx_area_hot']:.0f} m2 on a 35 C day"
             f"{'' if P['hx_ok_hot'] else ' (not enough air)'}; a pack of thin cambered fins filling the annulus {HX_CHORD * 1000:.0f} mm deep holds about "
             f"{P['hx_area_pack']:.0f} m2 (no thick vanes)")
    cl = d["clear"]
    cl_ok = min(cl.values()) > 0.0015 and d["skirt_engaged"] >= 0.6
    L.append(f"  MOVING CLEARANCES: crowns {cl['crowns_idc'] * 1000:.0f} mm apart at the inner dead centre; carrier disc "
             f"{cl['disc_liner_idc'] * 1000:.0f} mm from the liner end and magnet sleeve {cl['sleeve_wall_idc'] * 1000:.0f} mm from the housing wall there; "
             f"disc {cl['disc_cap_odc'] * 1000:.0f} mm from the end cap at the outer dead centre; "
             f"{d['skirt_engaged'] * 100:.0f} % of the skirt still in the liner there   {'OK' if cl_ok else 'INTERFERENCE'}")
    L.append(f"  CENTRE BLOCK: one printed aluminium piece {2 * d['blk_face'] * 1000:.0f} mm wide x {(2 * d['pitch'] + 2 * d['flange_r']) * 1000:.0f} mm long x "
             f"{2 * d['flange_r'] * 1000:.0f} mm tall with the three bores, port galleries and a propane cooling gallery through each combustion zone; "
             f"six stator assemblies bolt to its two faces, 16 x M8 each, carrying about {c['pb_max'] * math.pi * d['r_hi'] ** 2 / 1e3:.0f} kN of chamber pressure load per joint")
    M = P["mass"]
    L.append(f"  MASS ESTIMATE (built up from this geometry, about +/-20 %):")
    L.append(f"    stators {M['stators_outer'] + M['stators_inner']:.0f} kg (outer {M['stators_outer'] / 6:.0f} + inner {M['stators_inner'] / 6:.0f} per piston), "
             f"moving parts {M['moving']:.0f} kg")
    L.append(f"    printed aluminium block and casing {M['block']:.0f} kg: bore walls and galleries {M['centre_sections']:.0f}, generator housings "
             f"{M['housings']:.0f}, block skin, bolt faces, webs and mounts {M['block_ties']:.0f}, fasteners {M['fasteners']:.0f}")
    L.append(f"    ENGINE {M['engine']:.0f} kg; with air path {M['air_path']:.0f}, electronics {M['electronics']:.0f}, cooling {M['cooling']:.0f} "
             f"and LTO pack {M['pack']:.0f}: PACKAGE {M['package']:.0f} kg ({M['package'] * 2.2046:.0f} lb)")
    L.append("  FIT in the X1 SkyRacer (craft coordinates, m):")
    ok_all = cl_ok
    for k, ax in enumerate("xyz"):
        e0, e1 = ENV[ax]
        ok = lo[k] >= e0 - 1e-6 and hi[k] <= e1 + 1e-6
        ok_all &= ok
        L.append(f"    cylinders + generators {ax}: {lo[k]:+.3f} .. {hi[k]:+.3f}   bay box {e0:+.3f} .. {e1:+.3f}   "
                 f"margin {min(lo[k] - e0, e1 - hi[k]) * 1000:+.0f} mm   {'OK' if ok else 'OVER'}")

    def group(pred):
        return [v for o in objs if pred(o) for v in o.mesh.v]
    tv = group(lambda o: o.name.startswith("OPF_ETurbo"))
    t_side = min(body_x(v[1], v[2]) - abs(v[0]) for v in tv)
    t_belly = min(v[2] - belly_z(v[1]) for v in tv)
    t_y = max(v[1] for v in tv)
    L.append(f"    e-turbo: aft of the cylinders to y {t_y:.3f} ({(t_y - ENV['y'][1]) * 1000:+.0f} mm past the old bay box, still ahead of the pushers); "
             f"skin clearance sides {t_side * 1000:+.0f} mm, belly {t_belly * 1000:+.0f} mm")
    ok_all &= t_side > 0 and t_belly > 0
    up = group(lambda o: o.name in ("OPF_Charge_Air_Cooler", "OPF_CAC_Propane_Headers", "OPF_Inverters", "OPF_DCDC_Converter",
                                    "OPF_Control_Electronics_Placeholder", "OPF_DC_Bus", "OPF_Electronics_Deck"))
    t_top = min(body_ztop(v[0], v[1]) - v[2] for v in up)
    L.append(f"    charge air cooler (spine, between the wing roots) and electronics deck (ahead of the wing): "
             f"{t_top * 1000:+.0f} mm under the outer skin line")
    ok_all &= t_top > 0
    wl = []
    for o in objs:
        if o.coll in ("OPFPLG_Radiators", "OPFPLG_Reference"):
            continue
        for v in o.mesh.v:
            if abs(v[0]) > 0.16 and v[1] < 1.75:
                z = wing_low(v[1])
                if z is not None:
                    wl.append((z - v[2], o.name))
    w_min = min(wl)
    L.append(f"    under the rear wing root (estimated lower surface): closest part {w_min[1]} at {w_min[0] * 1000:+.0f} mm")
    a = d["acc"]
    hb = d["zc"] - d["flange_r"]
    ys = [ACC_Y0 + ACC_L * k / 40 for k in range(41)]
    at = ACC_TOP_BAY
    zbm = at - ACC_H
    belly = min(zbm - belly_z(y) for y in ys)
    side = min(body_x(y, z) - ACC_W / 2 for y in ys for z in (zbm, at))
    acc_ok = (hb - at) >= 0.009 and belly >= 0.05 - 1e-6 and side >= 0.035 - 1e-6
    ok_all &= acc_ok
    L.append(f"  accumulator (unchanged): {a['n']} x Toshiba SCiB 20Ah-HP LTO, {a['n']}S, {a['v_nom']:.0f} V nominal, "
             f"{a['kwh']:.1f} kWh, ~{a['kw10']:.0f} kW for 10 s; housings {(hb - at) * 1000:.0f} mm above its lid   {'OK' if acc_ok else 'CLASH'}")
    L.append(f"  RESULT: {'fits' if ok_all else 'DOES NOT FIT'} - cylinders inside the bay box; e-turbo, cooler, deck and line trays are "
             "outside the old box but inside the skin; pusher lines, condensers and tailpipe are external by design")
    d["perf"] = P
    return "\n".join(L), ok_all



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
        if o.motion:
            # keyframes every half frame straight from the cycle table, linear, frames 1-25 (loops on 1-24)
            sgn_, phi_ = o.motion
            prefs = bpy.context.preferences.edit
            old_interp = prefs.keyframe_new_interpolation_type
            prefs.keyframe_new_interpolation_type = "LINEAR"
            for k in range(2 * CYCLE_FRAMES + 1):
                fr_ = 1 + 0.5 * k
                ob.location[0] = o.origin[0] + piston_x(sgn_, phi_, fr_)
                ob.keyframe_insert(data_path="location", index=0, frame=fr_)
            prefs.keyframe_new_interpolation_type = old_interp
            ob.location[0] = o.origin[0] + piston_x(sgn_, phi_, 1)
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
    if preset in PRESETS:
        PRESET = preset
    d, objs = build(PRESET)
    report, ok = fit_report(d, objs)
    print(report)
    os.makedirs(out_dir, exist_ok=True)
    # pose the pistons as at frame 1
    w = 2 * math.pi / 24
    for o in objs:
        if o.motion:
            k = 0
            dk = piston_x(o.motion[0], o.motion[1], 1)
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
        ax.set_title(f"X1 OPFPLG 1,500 hp ({d['disp'] * 1000:.1f} L) - {name}", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"preview_{name}.png"))
        plt.close(fig)


if __name__ == "__main__":
    if IN_BLENDER:
        blender_build()
    else:
        args = [a for a in sys.argv[1:]]
        standalone(args[0] if args else "x1_opfplg_out", args[1] if len(args) > 1 else None)

