"""
X1 SkyRacer - OPFPLG 1,500 hp continuous (opposed free-piston linear generator)
===============================================================================
Blender 3.6 / 4.x.  Scripting workspace -> New text -> paste -> Run Script.
Nov 2026 redesign of the 4.5 L concept. Same airframe coordinates, same LTO pack, same pusher
heat-exchanger idea, but every part is now sized from a free-piston cycle model (opf_cycle.py)
instead of an assumed 100 Hz.

What it builds (collection "X1_OPFPLG"):
  * 3 opposed-piston cylinders across the airframe, 6 free pistons (sodium-filled, printed titanium), uniflow
    two-stroke, propane DI.
    150 mm bore x 124 mm stroke per piston (13.1 L), about 45 Hz, 120 deg between cylinders,
    the two pistons of a cylinder mirror each other exactly (taller exhaust ports give the lead).
  * each piston carries a folded "bell" translator: a tail tube runs out of the open liner end to a
    spoked disc, and the magnet sleeve hangs back from the disc over the OUTSIDE of the liner, so the
    generator shares length with the cylinder. Stators on both faces of the magnet sleeve
    (inner stator around the liner; the outer stator stops 60 % of the stroke short of the outer dead
    centre, where the generating force is low). Lightweight build: aluminium windings on cobalt-iron cores.
  * printed aluminium block: each cylinder is a coated-bore centre section (20 mm combustion band, 6 mm
    elsewhere). ONE metal-printed centre block (collection OPFPLG_Block): a slim waist round the combustion
    zones (injector bosses, a propane cooling gallery in each bore wall, one half per piston circuit) and the
    AIR CHEST round the three intake port rings. On the exhaust side the block has a closing wall toward
    the stators, so the six stator assemblies (4.5 mm housing, both stators, liner extension, end cap) bolt to
    aluminium on both faces, 16 x M8 each, and never see exhaust gas. The ports are on arcs, not all round: 12 ports
    on 270 deg, exhaust centred on straight DOWN, intake on straight UP, with the same heights (timing) and open
    area as before. Each bore carries a printed steel exhaust-port insert, and the exhaust housing's
    underside is open: a short stainless COLLECTOR wraps the ported arc and opens straight down through a
    64 x 204 mm flange only 21 mm under the port insert. A separate one-piece stainless MANIFOLD bolts to the
    three flanges; its upper part sits up inside the block and a lower part grows below the block as each
    cylinder joins, then it turns round into the bottom of the turbine volute. The pack is lowered 55 mm
    for it, with a double radiant shield between.
  * gas path: compressor -> riser up behind the block -> stacked charge air cooler in the spine: a hot
    plenum on top, a wide shallow core the air passes straight down through, and a cold plenum underneath
    that drains through its floor into the air chest along its whole length. The cold plenum is a
    narrow neck on the air-chest side that flares out under a wide core and a rounded, ribbed hot tank; the wide
    part sits above the block's exhaust side, 28 mm clear at the closest point, with a formed double-skin heat shield
    following the underside. Exhaust chest -> rear outlet ->
    bottom inlet of the turbine volute. Every passage sized for velocity (see GAS PATH in the report).
  * sodium-cooled crowns: each piston is one printed titanium piece with a sealed, half-filled sodium gallery under
    a thin gas plate held by printed pillars, carried 75 mm down a jacket inside the skirt. The sodium shakes between the two and spreads the crown
    heat (about 1 MW/m2 on the gas face) over a finned wall where the propane can boil it off (about 0.27 MW/m2).
  * the sealed volume behind each piston (linear-generator housing) is that piston's own propane
    circuit: liquid enters through a check valve and a spray lance up the hollow tail onto the crown
    underside and through the stator slots, boils, and leaves through a BLEED VALVE to its own sector
    of the pusher-fan condenser. Chamber pressure swings with the piston, so the chamber pumps its own
    loop; the bleed valve sets the mean pressure = boiling temperature = bounce (return) force.
  * charge air cooler in the spine over the engine (air to boiling propane), feeding the intake plenum;
    exhaust collector beside it, electric turbo-compound unit aft.
  * power electronics: a SiC inverter on top of each stator housing (six, one per stator set), seated in a
    saddle so the housing wall is its cold plate (the chamber below boils propane at 63-71 C); all six are
    turned 40 deg forward of the top, which is what clears the rear wing root on cylinder 3. A 900 V bus runs along each side over the
    housings; the DC/DC to the 373 V LTO pack and ONE placeholder box for control electronics and sensors sit
    beside the pack. The DC/DC, controller and the cooler's cold stage share two auxiliary propane circuits;
    the cooler's hot stage (top half of the core, 212 C to 110 C) has its own two circuits condensing at 82 C.
  * 162-cell LTO accumulator under the engine, unchanged.
  * pusher-fan condensers: annular finned cores behind each fan, five sectors each
    (three piston circuits, the hot charge-cooler stage and the auxiliary circuit, sized by heat and temperature). Thin cambered fins only, no thick vanes: about 20 deg
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
N_PORTS = 12                # port holes per ring, within the ported arc
PORT_ARC_DEG = 270.0        # ported arc of each ring: exhaust ports centred on straight DOWN, intake ports on straight UP
PORT_OPEN = 0.80            # open share of the ported arc (the rest is bridges); arc x open = 60 % of the circumference, as before
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
# gas path (Nov 2026 flow revision): air and exhaust chests in the block, engine and pack lowered
ACC_DROP = 0.055            # LTO pack lowered from the bay-box layout to make room for the exhaust manifold under the block (the engine stays put)
CHEST_WALL = 0.018          # chest outer wall to the bolt circle (bolts thread into it; ribbed, ~40 % solid)
CAC_X = (-0.140, 0.108)     # charge air cooler x range at the core and hot tank (wide up top)
CAC_NECK_X = 0.008          # the cold plenum's +x wall low down: a narrow neck on the air-chest side, clear of the exhaust chest
CAC_NECK_H = 0.023          # height of the neck above the block top before the plenum flares out under the core
CAC_BAY_X = (-0.112, 0.108) # x range of the hot plenum's rear bay, where the riser comes up (behind the block)
CAC_EX_GAP_MIN = 0.025      # least air gap wanted between the cooler and the exhaust chest (m)
EX_BELT_R, EX_BELT_T = 0.150, 0.0015   # exhaust collector under each bore: outer radius round the side ports, stainless wall
EX_FLANGE_D = 0.110                    # manifold flange face below the bore axis: 21 mm under the port insert (the block's underside is open there)
EX_THROAT_Y = 2 * math.sqrt(EX_BELT_R ** 2 - EX_FLANGE_D ** 2)   # flange opening along the manifold: the full width of the collector at that depth
EX_THROAT_X1 = 0.116                   # outboard edge of the flange opening; the lowest stator bolts keep their bosses outboard of it
EX_MAN_TOP = (0.064, 0.070)            # manifold upper part, recessed into the block's underside: width x height
EX_MAN_BOT = ((0.064, 0.010), (0.142, 0.038), (0.110, 0.050), (0.130, 0.074))   # lower part below the block: after cylinder 1, at the pack's rear end (1 + 2), behind the pack, after cylinder 3
RHO_SS = 7900.0
INV_TILT_DEG = (40.0, 40.0, 40.0)   # inverter mount angle on each cylinder's housings, from the top toward the front
TURBO_KA = 0.82             # axial scale: shorter shaft line, the fuselage is already narrowing at the turbo

# sodium-cooled piston crown (Nov 2026): a sealed, half-filled gallery under the gas plate, carried down a jacket inside
# the top of the skirt. The sodium shakes between the crown and the jacket ("cocktail shaker") and spreads the crown
# heat over a larger, finned wall where the propane boils it off below its boiling limit.
# The piston is ONE printed titanium piece (Ti-6242): gas plate, pillars, gallery, back plate, jacket and skirt. It is
# printed hollow with a port, drained of powder, filled with sodium under argon and closed with a welded plug.
NA_T_PLATE, NA_K_PLATE = 0.0018, 9.0     # gas plate: thickness (m), conductivity (W/m K, Ti-6242 at about 350 C)
NA_PILLAR_PITCH, NA_PILLAR_D = 0.008, 0.002   # printed pillars holding the thin gas plate against cylinder pressure
NA_H_GAL, NA_T_BACK = 0.010, 0.0025      # gallery height, back plate
NA_L_JACKET, NA_GAP = 0.075, 0.004       # jacket length down the skirt, sodium annulus
NA_T_WALL, NA_K_WALL = 0.0012, 8.0       # jacket inner wall: titanium conducts poorly, which keeps the sodium molten
T_SKIRT = 0.002                          # printed titanium skirt wall
RHO_TI62, TI_T_LIMIT = 4540.0, 813.0     # Ti-6242 density; long-term service limit about 540 C
NA_FILL, RHO_NA, NA_T_MELT = 0.50, 927.0, 371.0
NA_H_SHAKE = 20e3                        # W/m2 K, shaken liquid sodium on a wall (estimate)
NA_FIN = 1.6                             # low fins on the propane side of the jacket and back plate: wetted / plain area
CHF_PROPANE = 0.41e6                     # W/m2, pool-boiling limit of propane near 24 bar (Zuber estimate)

# two-stage charge air cooler (Nov 2026): the top half of the core is a HOT stage that takes the air from the compressor
# temperature down to CAC_T_MID on its own propane circuits condensing at T_COND_HOT; the bottom half is the cold stage
# on the auxiliary circuits. Rejecting most of the charge heat at 80 C instead of 59 C needs far less condenser.
CAC_T_MID = 383.0           # K, charge air between the stages (110 C)
T_COND_HOT = 355.0          # K, hot-stage circuits condense at 82 C (about 32 bar)
CAC_BETA, CAC_H_AIR = 1500.0, 250.0   # core surface per volume (m2/m3) and air-side coefficient (W/m2 K): estimates

# Cycle-model result for this geometry (written by tune_cycle.py from opf_cycle.py; per piston).
CYCLE = dict(
    f=46.091,
    stroke=0.12375,
    x_min=0.00625,
    x_max=0.13,
    cr=16.0,
    p_max=21984495.0,
    v_mean=11.408,
    v_max=22.382,
    Qf=8869.03,
    E_el=4133.46,
    E_mech=4372.44,
    W_gas=4595.13,
    Q_wall=631.03,
    Q_crown=357.11,
    T_crown=665.2,
    W_fric=76.76,
    F_rms=15626.0,
    F_peak=27117.0,
    pb_min=2238292.0,
    pb_max=2628827.0,
    pb_mean=2465211.0,
    m_trap=0.006156,
    p_s=380000.0,
    lam=1.848,
    T_trap=380.0,
    imep=2101271.0,
    motion=[0.0, 0.000453, 0.002087, 0.004881, 0.008593, 0.01291, 0.0176, 0.022506, 0.027521, 0.032576, 0.03762, 0.042617, 0.047539, 0.052366, 0.057083, 0.061676, 0.066135, 0.070455, 0.074627, 0.078649, 0.082516, 0.086224, 0.089773, 0.093162, 0.096386, 0.099436, 0.102301, 0.104978, 0.107466, 0.109766, 0.111879, 0.113809, 0.115558, 0.117129, 0.118525, 0.119748, 0.120802, 0.121691, 0.122415, 0.12298, 0.123388, 0.123641, 0.123743, 0.123694, 0.123509, 0.123186, 0.122728, 0.122139, 0.12142, 0.120575, 0.119605, 0.118514, 0.117304, 0.115979, 0.114539, 0.112988, 0.111329, 0.109563, 0.107694, 0.105724, 0.103655, 0.101489, 0.099229, 0.096878, 0.094437, 0.091908, 0.089296, 0.086602, 0.08383, 0.080983, 0.078065, 0.075079, 0.072028, 0.068917, 0.065748, 0.062526, 0.059256, 0.05594, 0.052585, 0.049195, 0.045776, 0.042334, 0.038876, 0.035409, 0.031944, 0.028491, 0.025062, 0.021674, 0.018345, 0.015103, 0.011979, 0.009021, 0.006291, 0.003878, 0.001913, 0.000559],
    e_cu=160.27,
    sig_rms=80351.72,
    sig_pk=117709.27,
    burst={'p_s': 410000.0, 'lam': 1.6, 'bus_hp': 1973.0, 'p_max': 24367750.0, 'f': 48.83, 'F_rms': 19385.0, 'sig_pk': 148035.0},
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
    "Port_Insert":      ((0.42, 0.40, 0.38), 1.0, 0.35, 1.0),
    "Hot_Aux_Vapour":   ((0.93, 0.28, 0.22), 0.3, 0.40, 1.0),
    "Hot_Aux_Liquid":   ((0.55, 0.30, 0.75), 0.3, 0.40, 1.0),
    "Heat_Shield":      ((0.85, 0.80, 0.62), 1.0, 0.30, 1.0),
    "Deck":             ((0.20, 0.22, 0.25), 0.7, 0.50, 1.0),
    "Cold_Plate":       ((0.15, 0.70, 0.72), 0.6, 0.30, 1.0),
    "DCDC":             ((0.30, 0.24, 0.36), 0.8, 0.40, 1.0),
    "Controller":       ((0.85, 0.15, 0.55), 0.2, 0.50, 0.75),
    "AC_Lead":          ((0.90, 0.55, 0.20), 0.4, 0.40, 1.0),
    "Sodium":           ((0.95, 0.80, 0.25), 0.9, 0.25, 1.0),
    "HX_Fin":           ((0.70, 0.72, 0.76), 0.8, 0.50, 0.55),
    "Printed_Block":    ((0.60, 0.63, 0.67), 0.9, 0.55, 0.28),
    "Block_Body":       ((0.56, 0.60, 0.66), 0.9, 0.50, 0.28),
    "Bolt":             ((0.16, 0.17, 0.19), 1.0, 0.40, 1.0),
    "Intake_Gas":       ((0.30, 0.55, 0.95), 0.0, 0.40, 0.28),
    "Exhaust_Gas":      ((0.95, 0.45, 0.20), 0.0, 0.40, 0.28),
    "Exhaust_Liner":    ((0.72, 0.68, 0.62), 1.0, 0.35, 0.55),
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


ACC_TOP0 = ACC_TOP_BAY                        # pack lid height in the bay-box layout: the engine and electronics stay on this
ACC_TOP_BAY = ACC_TOP_BAY - ACC_DROP          # pack lowered below the bay box (not counted in the engine space)
ACC_C = (ACC_C[0], ACC_C[1], ACC_C[2] - ACC_DROP)


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
    d["Rb"] = d["r_b"] + 0.012                          # waist outer radius about each bore
    d["R_ch"] = d["flange_r"] - CHEST_WALL              # chest inner radius (racetrack round the three bores)
    d["r_sl"] = d["r_li"] + 0.014                       # thick printed sleeve where the bores cross the chests
    d["blk_face"], d["blk_tf"] = d["h0"] - 0.008, 0.012   # block bolt face (x from centre), block flange thickness
    d["xi0"] = d["cb"] - d["h_in"] - 0.040              # air chest: x from -blk_face to -xi0
    d["xe0"] = d["cb"] - d["h_ex"] - 0.058              # exhaust chest: x from xe0 to blk_face
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
    # one-piece printed titanium piston: gas plate + back plate + pillars and a 2.5 mm rim, jacket wall, and a 2 mm
    # titanium skirt over its whole length
    rl = d["r_li"]
    r_j1 = rl - 0.002                                   # jacket outer wall (the skirt), inside radius
    r_j0 = r_j1 - NA_GAP                                # jacket inner wall, sodium side
    pil = math.pi / 4 * (NA_PILLAR_D / NA_PILLAR_PITCH) ** 2 + 0.03       # pillar share of the gallery, plus a few ribs
    m_crown = (math.pi * rl ** 2 * (NA_T_PLATE + NA_T_BACK + pil * NA_H_GAL)
               + 2 * math.pi * rl * 0.0025 * NA_H_GAL) * RHO_TI62
    m_jacket = 2 * math.pi * r_j0 * NA_T_WALL * NA_L_JACKET * NA_FIN ** 0.5 * RHO_TI62   # inner wall with its low fins
    v_na = (1 - pil) * math.pi * (rl - 0.0025) ** 2 * NA_H_GAL + math.pi * (r_j1 ** 2 - r_j0 ** 2) * NA_L_JACKET
    m_na = NA_FILL * v_na * RHO_NA
    m_skirt = 2 * math.pi * rl * T_SKIRT * (d["Lp"] - NA_T_PLATE - NA_H_GAL) * RHO_TI62
    d["na"] = dict(plate_mpa=0.31 * (NA_PILLAR_PITCH - NA_PILLAR_D) ** 2 / NA_T_PLATE ** 2, r_j0=r_j0, r_j1=r_j1, v=v_na, m=m_na,
                   a_sink=math.pi * (r_j0 ** 2 - d["r_tail"] ** 2) + 2 * math.pi * (r_j0 - NA_T_WALL) * NA_L_JACKET)
    d["mass"] = dict(magnets=m_mag, sleeve=m_sleeve, disc=m_disk, tail=m_tail, crown=m_crown, jacket=m_jacket,
                     sodium=m_na, skirt=m_skirt, rings_web=0.6)
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
    d["zc"] = ACC_TOP0 + 0.010 + d["flange_r"]       # cylinder axis height: 10 mm over the accumulator
    d["pitch"] = 2 * d["flange_r"] + 0.008
    y0 = ENV["y"][0] + 0.005 + d["flange_r"]
    d["cyl_y"] = [y0 + k * d["pitch"] for k in range(3)]
    d["y_A"] = d["cyl_y"][2] + d["flange_r"]            # aft face of the cylinder bank
    k = TURBO_K
    d["scroll_R0"], d["scroll_rbig"] = 0.060, 0.055     # before the radial scale
    d["r_ca"] = 0.055 * k                               # charge-air and pre-turbine pipes
    d["r_cin"] = 0.075 * k
    d["r_dp"] = 0.122                                   # downpipe
    d["turbo_r"] = (d["scroll_R0"] + 2 * d["scroll_rbig"]) * k
    d["y_T"] = d["y_A"] + 0.008 + d["turbo_r"]          # turbo shaft line, volutes just clear the bank
    d["z_T"] = 0.640                                    # lower than the cylinders: clears the rear wing root
    d["x_in"] = -(d["cb"] - d["h_in"] / 2)
    d["x_ex"] = d["cb"] - d["h_ex"] / 2
    d["disp_cyl"] = 2 * A * S
    d["disp"] = 3 * d["disp_cyl"]
    # charge air cooler (spine, between the rear wing roots) and power-electronics deck (ahead of the wing)
    # stacked charge air cooler over the block: cold plenum (on the block) | core, flow straight down | hot plenum
    # (tapered, fed at the rear by the riser). It drains through its floor into the air chest.
    zt_ = d["zc"] + d["flange_r"]
    d["cac"] = dict(x0=CAC_X[0], x1=CAC_X[1], xc=sum(CAC_X) / 2, hw=(CAC_X[1] - CAC_X[0]) / 2, xr0=CAC_BAY_X[0], xr1=CAC_BAY_X[1], xn=CAC_NECK_X, zk=zt_ + 0.001 + CAC_NECK_H, y0=d["cyl_y"][0] - 0.170, y1=1.190, ya=1.330,   # over all three cylinders; hot plenum to ya
                    zp0=zt_ + 0.001, z0=zt_ + 0.046, z1=zt_ + 0.106,  # cold plenum floor, core bottom, core top (60 mm core)
                    zr0=zt_ + 0.096)                                  # riser bay floor; hot plenum top follows the skin
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
AUX_SPAN_DEG = 76.0         # share of each condenser annulus given to the auxiliary (cold-stage) circuit
HOT_SPAN_DEG = 84.0         # ... and to the hot-stage charge-cooler circuit


def sector_table(sgn):
    """Condenser sectors of one pusher: (name, centre angle, span) in the pusher frame
    (0 = +X, 90 deg = down). Three piston circuits share the lower arc; the top arc is split between the
    auxiliary circuit (outboard) and the hot-stage charge-cooler circuit (inboard)."""
    top = AUX_SPAN_DEG + HOT_SPAN_DEG
    span = (360.0 - top) / 3.0
    out = []
    for k in range(3):                                   # cylinder 1 outboard, 2 bottom, 3 inboard
        a = 90.0 + (k - 1) * span * sgn
        out.append((f"Cyl{k + 1}", math.radians(a), math.radians(span)))
    out.append(("Aux", math.radians(-90.0 + sgn * (top - AUX_SPAN_DEG) / 2), math.radians(AUX_SPAN_DEG)))
    out.append(("Hot", math.radians(-90.0 - sgn * (top - HOT_SPAN_DEG) / 2), math.radians(HOT_SPAN_DEG)))
    return out


def ported_liner_arc(m, fr, r_in, r_out, stations, port_bands, mat):
    """Sleeve with port rings on part of the circumference only. port_bands: {band index: centre angle of the ported
    arc in the frame (pi/2 = straight down, -pi/2 = straight up)}. N_PORTS ports in PORT_ARC_DEG, 3 cells open + 1 bridge."""
    n_arc = N_PORTS * 4
    N = int(round(n_arc * 360.0 / PORT_ARC_DEG))
    seg = 2 * math.pi / N
    O = [m.add_verts([fr.Pc(r_out, i * seg, z) for i in range(N)]) for z in stations]
    I = [m.add_verts([fr.Pc(r_in, i * seg, z) for i in range(N)]) for z in stations]

    def is_port(j, i):
        if j not in port_bands:
            return False
        k = (i - int(round(port_bands[j] / seg)) + n_arc // 2) % N      # cell index counted from the start of the arc
        return k < n_arc and (k % 4) != 3 and k != n_arc - 1

    for j in range(len(stations) - 1):
        for i in range(N):
            i1 = (i + 1) % N
            V = m.v
            if not is_port(j, i):
                m.poly([V[O[j] + i], V[O[j] + i1], V[O[j + 1] + i1], V[O[j + 1] + i]], mat)
                m.poly([V[I[j + 1] + i], V[I[j + 1] + i1], V[I[j] + i1], V[I[j] + i]], mat)
                continue
            m.poly([V[O[j] + i], V[O[j] + i1], V[I[j] + i1], V[I[j] + i]], mat)
            m.poly([V[I[j + 1] + i], V[I[j + 1] + i1], V[O[j + 1] + i1], V[O[j + 1] + i]], mat)
            if not is_port(j, (i - 1) % N):
                m.poly([V[O[j] + i], V[I[j] + i], V[I[j + 1] + i], V[O[j + 1] + i]], mat)
            if not is_port(j, i1):
                m.poly([V[O[j] + i1], V[O[j + 1] + i1], V[I[j + 1] + i1], V[I[j] + i1]], mat)
    V = m.v
    J = len(stations) - 1
    for i in range(N):
        i1 = (i + 1) % N
        m.poly([V[I[0] + i], V[I[0] + i1], V[O[0] + i1], V[O[0] + i]], mat)
        m.poly([V[O[J] + i], V[O[J] + i1], V[I[J] + i1], V[I[J] + i]], mat)


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
        # intake ports on the upper arc (-X end), exhaust ports on the lower arc (+X end), same area and height as before
        ported_liner_arc(o.mesh, fr, d["r_li"], d["r_lo"], st, {1: -math.pi / 2, 3: math.pi / 2}, "Liner")
        tube(o.mesh, fr, d["r_lo"], d["r_band"], -L_BAND, L_BAND, "Liner")     # printed combustion band
        for s in (-1, 1):                                # stationary propane seal packs
            a0, a1 = sorted((s * d["u_seal"], s * (d["u_seal"] + 0.010)))
            tube(o.mesh, fr, d["r_lo"], d["r_lo"] + 0.004, a0, a1, "Housing_Flange")

        # thick printed sleeve where the bore crosses each chest (carries the cooling gallery to the port bridges)
        o = new(f"OPF_{tag}_Chest_Sleeves", "OPFPLG_Core")
        tube(o.mesh, fr, d["r_lo"], d["r_sl"], -(cb - d["h_in"] - 0.002), -d["xi0"], "Liner")
        tube(o.mesh, fr, d["r_lo"], d["r_sl"], d["xe0"], d["xe0"] + 0.008, "Liner")
        # exhaust-port insert: a printed steel sleeve carrying the exhaust ports and their bridges, fitted over the bore
        # wall where it crosses the exhaust chest; the propane gallery runs behind it
        tube(o.mesh, fr, d["r_lo"], d["r_sl"], d["xe0"] + 0.008, cb - d["h_ex"] - 0.002, "Port_Insert")

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
            na, rl = d["na"], d["r_li"]
            u1, u2 = g + NA_T_PLATE, g + NA_T_PLATE + NA_H_GAL
            u3, u4 = u2 + NA_T_BACK, u2 + NA_T_BACK + NA_L_JACKET
            z0, z1 = zz(g, u1)
            cyl(o.mesh, fr, rl - 0.0005, z0, z1, "Piston")                           # steel gas plate
            z0, z1 = zz(u1, u1 + NA_FILL * NA_H_GAL)
            cyl(o.mesh, fr, rl - 0.004, z0, z1, "Sodium")                            # sodium gallery (half full)
            z0, z1 = zz(u2, u3)
            cyl(o.mesh, fr, rl - 0.0005, z0, z1, "Piston")                           # back plate
            z0, z1 = zz(u3, u3 + NA_FILL * NA_L_JACKET)
            tube(o.mesh, fr, na["r_j0"], na["r_j1"], z0, z1, "Sodium")               # sodium in the skirt jacket
            z0, z1 = zz(u3, u4)
            tube(o.mesh, fr, na["r_j0"] - NA_T_WALL, na["r_j0"], z0, z1, "Piston")   # jacket inner wall (finned, propane side)
            z0, z1 = zz(u1, g + Lp)
            tube(o.mesh, fr, rl - 0.0005 - T_SKIRT, rl - 0.0005, z0, z1, "Piston")   # printed titanium skirt
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

    # ---- ONE metal-printed centre block: waist round the combustion zones, a chest at each end
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

    def track(R, n=20):
        """Racetrack outline (y, z) of radius R round the three axes, closed loop."""
        pts = [(ys3[0] + R * math.cos(math.pi / 2 + math.pi * k / n), zc + R * math.sin(math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
        pts += [(ys3[2] + R * math.cos(-math.pi / 2 + math.pi * k / n), zc + R * math.sin(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
        return pts

    def shell(m_, xa, xb, Ro, Ri, mat):
        """Hollow racetrack wall between x = xa and xb: outer surface Ro, inner surface Ri, end rings."""
        po, pi_ = track(Ro), track(Ri)
        n_ = len(po)
        for i in range(n_):
            j = (i + 1) % n_
            for P_ in (po, pi_):
                m_.poly([(xa, *P_[i]), (xb, *P_[i]), (xb, *P_[j]), (xa, *P_[j])], mat)
            for x in (xa, xb):
                m_.poly([(x, *po[i]), (x, *po[j]), (x, *pi_[j]), (x, *pi_[i])], mat)

    def in_track(y, z, R):
        if ys3[0] <= y <= ys3[2]:
            return abs(z - zc) < R
        return min(math.hypot(y - ys3[0], z - zc), math.hypot(y - ys3[2], z - zc)) < R

    xf, Rch, Rf = d["blk_face"], d["R_ch"], d["flange_r"]
    o = new("OPF_Block_Waist", "OPFPLG_Block")
    slab(o.mesh, -d["xi0"], d["xe0"], d["Rb"], d["r_lo"], "Block_Body")
    chests = (("Intake", -1, d["xi0"], "Intake_Gas"), ("Exhaust", 1, d["xe0"], "Exhaust_Gas"))
    for side, s, x0, gas in chests:
        xa, xb = sorted((s * x0, s * xf))
        xw = s * (x0 + 0.008)                                          # inboard end wall thickness 8 mm
        o = new(f"OPF_Block_{side}_Chest", "OPFPLG_Block")
        slab(o.mesh, *sorted((s * x0, xw)), Rf, d["r_sl"], "Printed_Block")   # inboard end wall (part of the block)
        if side == "Intake":
            shell(o.mesh, xa, xb, Rf, Rch, "Printed_Block")             # chest wall, bolt circle in its face
        else:
            # exhaust housing: its underside is OPEN between the end wall and the closing wall, so the manifold
            # can come right up under the bores. Wall kept only above the flange level.
            z_fl = zc - EX_FLANGE_D
            po_, pi_ = track(Rf), track(Rch)
            for i_ in range(len(po_)):
                j_ = (i_ + 1) % len(po_)
                if min(po_[i_][1], po_[j_][1]) < z_fl - 1e-6:
                    continue
                for P_ in (po_, pi_):
                    o.mesh.poly([(xa, *P_[i_]), (xb, *P_[i_]), (xb, *P_[j_]), (xa, *P_[j_])], "Printed_Block")
                for x_ in (xa, xb):
                    o.mesh.poly([(x_, *po_[i_]), (x_, *po_[j_]), (x_, *pi_[j_]), (x_, *pi_[i_])], "Printed_Block")
        if side == "Exhaust":
            # The exhaust never touches the stator assemblies: the block has a closing wall on this face, and the gas
            # is collected by a stainless PORT BELT round each bore (air gap all round it inside the block), which
            # drops through the block's underside into a separate bolt-on manifold.
            slab(o.mesh, xf - 0.005, xf, Rf, d["r_sl"], "Printed_Block")        # closing wall toward the stator housings
            xb0, xb1 = xw + 0.006, xf - 0.006                                   # the collector covers the whole port band
            d["ex_belt"] = dict(x0=xb0, x1=xb1, R=EX_BELT_R)
            D_fl, yw_ = EX_FLANGE_D, EX_THROAT_Y / 2                            # flange face just under the port insert
            xt1 = EX_THROAT_X1

            def collector(m_, yk, xa_, xb_, r_in, R_, yw, D_, mat, walls=True, n_=72):
                """Collector under one bore: round the ported lower arc, straight down through a wide throat to the
                flange opening at depth D_. Outline taken as a ray from the bore axis (frame angle pi/2 = down)."""
                half = math.radians(PORT_ARC_DEG) / 2 + math.radians(6.0)
                ang = [math.pi / 2 - half + 2 * half * i / n_ for i in range(n_ + 1)]
                def rho(th):
                    dn, sd = math.sin(th), abs(math.cos(th))                    # down component, sideways component
                    if dn > 1e-6 and D_ / dn * sd <= yw:
                        return D_ / dn, True                                    # the open flange face
                    if dn > 1e-6 and sd > 1e-6 and yw / sd * dn >= math.sqrt(max(R_ * R_ - yw * yw, 0.0)):
                        return yw / sd, False                                   # throat side wall
                    return R_, False
                bf_ = Frame((0.0, yk, zc), (1, 0, 0))
                P_ = [(rho(t)[0], rho(t)[1], t) for t in ang]
                for i in range(n_):
                    (r0, o0, t0), (r1, o1, t1) = P_[i], P_[i + 1]
                    for x_ in (xa_, xb_):                                       # end plates
                        m_.poly([bf_.Pc(r_in, t0, x_), bf_.Pc(r0, t0, x_), bf_.Pc(r1, t1, x_), bf_.Pc(r_in, t1, x_)], mat)
                    if walls and not (o0 and o1):                               # outer wall (the flange face stays open)
                        m_.poly([bf_.Pc(r0, t0, xa_), bf_.Pc(r0, t0, xb_), bf_.Pc(r1, t1, xb_), bf_.Pc(r1, t1, xa_)], mat)
                if walls:
                    for t_, r_ in ((ang[0], P_[0][0]), (ang[-1], P_[-1][0])):     # closed ends of the arc, above the top ports
                        m_.poly([bf_.Pc(r_in, t_, xa_), bf_.Pc(r_in, t_, xb_), bf_.Pc(r_, t_, xb_), bf_.Pc(r_, t_, xa_)], mat)

            o = new("OPF_Exhaust_Collectors", "OPFPLG_Air")
            xm_ = 0.5 * (xb0 + xt1)
            for yk in ys3:
                collector(o.mesh, yk, xb0, xb1, d["r_sl"], EX_BELT_R, yw_, D_fl, "Exhaust_Liner")
                obox(o.mesh, (0.5 * (xt1 + xb1), yk, z_fl + 0.0015), X3, (0.5 * (xb1 - xt1), yw_, 0.0015), "Exhaust_Liner")   # lip that turns the outboard ports in
                for sy_ in (-1, 1):                                             # flange rails along the opening, bolted to the manifold
                    obox(o.mesh, (xm_, yk + sy_ * (yw_ + 0.008), z_fl + 0.003), X3, ((xt1 - xb0) / 2 + 0.010, 0.008, 0.003), "Exhaust_Liner")
                for sx_ in (-1, 1):
                    obox(o.mesh, (xm_ + sx_ * ((xt1 - xb0) / 2 + 0.005), yk, z_fl + 0.003), X3, (0.005, yw_, 0.003), "Exhaust_Liner")
                for sy_ in (-1, 1):
                    for kx_ in range(3):
                        xb_ = xb0 + 0.006 + (xt1 - xb0 - 0.012) * kx_ / 2
                        pipe(o.mesh, [(xb_, yk + sy_ * (yw_ + 0.008), z_fl + 0.010), (xb_, yk + sy_ * (yw_ + 0.008), z_fl - 0.010)], 0.004, "Bolt", n=6)
            d["ex_flange_z"] = z_fl
            d["ex_neck_y"] = list(ys3)
            d["ex_throat"] = (xt1 - xb0, EX_THROAT_Y)
            d["ex_throat_x"] = (xb0, xt1)
        o = new(f"OPF_{side}_Chest_Gas", "OPFPLG_Air")
        if side == "Intake":
            slab(o.mesh, *sorted((xw, s * xf)), Rch - 0.003, d["r_sl"], gas)
        else:
            for yk in ys3:
                collector(o.mesh, yk, d["ex_belt"]["x0"] + 0.002, d["ex_belt"]["x1"] - 0.002, d["r_sl"] + 0.001, EX_BELT_R - 0.003,
                          yw_ - 0.003, D_fl, gas, walls=False)
        # bolts: tapped into the chest wall; where a bolt falls inside the chest it runs in a printed boss
        o = new(f"OPF_Block_Bolts_{side}", "OPFPLG_Block")
        ob = new(f"OPF_Block_Bosses_{side}", "OPFPLG_Block")
        for yk in ys3:
            bf = Frame((0.0, yk, zc), (1, 0, 0))
            for i in range(16):
                th = 2 * math.pi * (i + 0.5) / 16
                p_ = bf.Pc(d["r_bolt"], th, 0.0)
                if side == "Exhaust" and p_[2] < zc - EX_FLANGE_D:
                    # the lowest bolts sit beside the manifold: shorter, in bosses on the closing wall
                    pipe(o.mesh, [bf.Pc(d["r_bolt"], th, xf - 0.012), bf.Pc(d["r_bolt"], th, d["h0"] + 0.007)], 0.0045, "Bolt", n=6)
                    pipe(ob.mesh, [bf.Pc(d["r_bolt"], th, xf - 0.019), bf.Pc(d["r_bolt"], th, xf)], 0.0075, "Printed_Block", n=8)
                    continue
                pipe(o.mesh, [bf.Pc(d["r_bolt"], th, s * (xf - 0.016)), bf.Pc(d["r_bolt"], th, s * (d["h0"] + 0.007))],
                     0.0045, "Bolt", n=6)
                if in_track(p_[1], p_[2], Rch):
                    pipe(ob.mesh, [bf.Pc(d["r_bolt"], th, xw), bf.Pc(d["r_bolt"], th, s * xf)], 0.0075, "Printed_Block", n=8)
    o = new("OPF_Block_Mounts", "OPFPLG_Block")                         # four lugs under the waist, clear of the pack
    for yk in (ys3[0], ys3[2]):
        for s in (-1, 1):
            obox(o.mesh, (s * 0.025, yk, zc - d["Rb"] - 0.015), X3, (0.015, 0.035, 0.016), "Printed_Block")

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
    # exhaust enters at the bottom of the volute heading aft (same swirl as the rotation), exducer exits axially (+X)
    BOTTOM = math.pi / 2
    t_port, _ = scroll(o.mesh, tf, 0.272, R0, 0.009, rbig, BOTTOM, "Turbine", "turbine")
    o = tnew("OPF_ETurbo_VGT_Actuator")
    obox(o.mesh, (0.30, yT + 0.11, zT + 0.135), X3, (0.025, 0.030, 0.012), "VGT_Actuator")

    def tscale(v):
        return (v[0] * TURBO_KA, yT + (v[1] - yT) * kT, zT + (v[2] - zT) * kT)
    for o in turbo_objs:
        o.mesh.v = [tscale(v) for v in o.mesh.v]
    c_port, t_port = tscale(c_port), tscale(t_port)
    d["c_port"], d["t_port"] = c_port, t_port
    rca = d["r_ca"]

    # ---- gas path: compressor -> centre-fed charge air cooler -> two downcomers -> air chest;
    #      exhaust chest -> rear outlet -> bottom inlet of the turbine volute
    cac = d["cac"]
    dk = d["deck"]
    y_last = d["cyl_y"][2]
    hw = cac["hw"]
    zm, zh = (cac["z0"] + cac["z1"]) / 2, (cac["z1"] - cac["z0"]) / 2
    z_top = zc + d["flange_r"]                                         # top of the chests
    d["routes"] = []

    def route(name, pts, r):
        d["routes"].append((name, [tuple(p) for p in pts], r))

    def ybox(m_, x0_, x1_, secs, mat):
        """Box along y with a varying section: secs = [(y, z_bottom, z_top), ...]."""
        for (ya_, za0, za1), (yb_, zb0, zb1) in zip(secs, secs[1:]):
            for x_ in (x0_, x1_):
                m_.poly([(x_, ya_, za0), (x_, yb_, zb0), (x_, yb_, zb1), (x_, ya_, za1)], mat)
            m_.poly([(x0_, ya_, za1), (x1_, ya_, za1), (x1_, yb_, zb1), (x0_, yb_, zb1)], mat)
            m_.poly([(x0_, ya_, za0), (x0_, yb_, zb0), (x1_, yb_, zb0), (x1_, ya_, za0)], mat)
        for (y_, z0_, z1_) in (secs[0], secs[-1]):
            m_.poly([(x0_, y_, z0_), (x1_, y_, z0_), (x1_, y_, z1_), (x0_, y_, z1_)], mat)

    def xloft(m_, secs, mat):
        """Solid with an x-z outline (same point count in every section) lofted along y; convex outlines only."""
        for (ya_, pa), (yb_, pb) in zip(secs, secs[1:]):
            n_ = len(pa)
            for i in range(n_):
                j = (i + 1) % n_
                m_.poly([(pa[i][0], ya_, pa[i][1]), (pa[j][0], ya_, pa[j][1]), (pb[j][0], yb_, pb[j][1]), (pb[i][0], yb_, pb[i][1])], mat)
        m_.poly([(x_, secs[0][0], z_) for x_, z_ in secs[0][1]][::-1], mat)
        m_.poly([(x_, secs[-1][0], z_) for x_, z_ in secs[-1][1]], mat)

    def tank(x0_, x1_, zb_, zt_o, r_=0.020, grow=0.0):
        """Tank outline: flat bottom, rounded top corners."""
        r_ = max(0.004, min(r_, 0.6 * (zt_o - zb_)))
        pts = [(x0_ - grow, zb_), (x1_ + grow, zb_)]
        for k in range(5):
            a_ = math.pi / 2 * k / 4
            pts.append((x1_ + grow - r_ + r_ * math.cos(a_), zt_o + grow - r_ + r_ * math.sin(a_)))
        for k in range(5):
            a_ = math.pi / 2 * (1 + k / 4)
            pts.append((x0_ - grow + r_ + r_ * math.cos(a_), zt_o + grow - r_ + r_ * math.sin(a_)))
        return pts

    o = new("OPF_Charge_Air_Cooler", "OPFPLG_Air")
    # Cross-section: a narrow cold plenum (neck) on the air-chest side of the block, flaring out under a wide core and
    # hot tank. The wide part sits well above the exhaust chest; a formed double-skin shield follows the underside.
    xc, xa, xb, xn = cac["xc"], cac["x0"], cac["x1"], cac["xn"]
    cac_x = lambda sgn: xb if sgn > 0 else xa                             # the cooler's side on +x / -x
    ya_c, yb_c = cac["y0"], cac["y1"]
    ym_c, hy_c = (ya_c + yb_c) / 2, (yb_c - ya_c) / 2
    zk = cac["zk"]
    obox(o.mesh, ((xa + xn) / 2, ym_c, (cac["zp0"] + zk) / 2), X3, ((xn - xa) / 2, hy_c, (zk - cac["zp0"]) / 2), "Intake_Pipe")
    flare = [(xa, zk), (xn, zk), (xb, cac["z0"] - 0.006), (xb, cac["z0"]), (xa, cac["z0"])]
    xloft(o.mesh, [(ya_c, flare), (yb_c, flare)], "Intake_Pipe")
    # clearance to the exhaust chest top (from its inboard top edge to the neck wall and to the flared underside)
    def seg_dist(p_, a_, b_):
        vx, vz = b_[0] - a_[0], b_[1] - a_[1]
        t_ = max(0.0, min(1.0, ((p_[0] - a_[0]) * vx + (p_[1] - a_[1]) * vz) / (vx * vx + vz * vz)))
        return math.hypot(p_[0] - a_[0] - t_ * vx, p_[1] - a_[1] - t_ * vz)
    z_blk = cac["zp0"] - 0.001                                          # block / chest top
    edge = (d["xe0"], z_blk)                                          # top of the block over the exhaust belts
    d["cac_ex_gap"] = min(edge[0] - xn, seg_dist(edge, flare[1], flare[2]), cac["z0"] - 0.006 - z_blk)
    # heat shield: two thin skins 4 mm apart, standing 10 mm off the cooler, up the neck and out under the flare,
    # with a short turned-up edge at the core's side; open at both ends so air draws through
    sh = [(xn + 0.010, cac["zp0"] + 0.004), (xn + 0.010, zk - 0.007), (xb + 0.008, cac["z0"] - 0.018), (xb + 0.014, cac["z0"] - 0.004)]
    d["cac_shield_gap"] = seg_dist(edge, (sh[1][0] + 0.003, sh[1][1] - 0.003), (sh[2][0] + 0.003, sh[2][1] - 0.003))
    for off in (0.0, 0.003):
        pts_s = [(x_ + off, z_ - off) for x_, z_ in sh]
        for (x1s, z1s), (x2s, z2s) in zip(pts_s, pts_s[1:]):
            o.mesh.poly([(x1s, ya_c - 0.010, z1s), (x2s, ya_c - 0.010, z2s), (x2s, yb_c + 0.010, z2s), (x1s, yb_c + 0.010, z1s)], "Heat_Shield")
    for k in range(6):                                                    # stand-off brackets
        y_ = ya_c + 0.06 + (yb_c - ya_c - 0.12) * k / 5
        obox(o.mesh, (xn + 0.005, y_, zk - 0.014), X3, (0.005, 0.006, 0.004), "Bolt")
        obox(o.mesh, (0.5 * (xn + xb) + 0.004, y_, 0.5 * (zk + cac["z0"]) - 0.008), X3, (0.006, 0.006, 0.005), "Bolt")
    # core: vertical plates (air runs down between them, propane runs fore and aft inside them), framed by a flange
    # top and bottom where the tanks bolt on
    zm, zh = (cac["z0"] + cac["z1"]) / 2, (cac["z1"] - cac["z0"]) / 2
    obox(o.mesh, (xc, ym_c, zm), X3, (hw - 0.006, hy_c - 0.004, zh), "CAC_Core")
    obox(o.mesh, (xc, ym_c, zm), X3, (hw + 0.003, hy_c + 0.003, 0.002), "Hot_Aux_Vapour")      # divider between the hot stage (top) and the cold stage
    n_pl = max(17, int(round((2 * hw - 0.020) / 0.0125)) + 1)
    for k in range(n_pl):
        x_ = xa + 0.010 + (2 * hw - 0.020) * k / (n_pl - 1)
        obox(o.mesh, (x_, ym_c, zm), X3, (0.0012, hy_c - 0.002, zh + 0.002), "CAC_Fin")
    for z_ in (cac["z0"], cac["z1"]):
        for sy in (-1, 1):
            obox(o.mesh, (xc, ym_c + sy * (hy_c + 0.002), z_), X3, (hw + 0.006, 0.004, 0.003), "Intake_Pipe")
        for sx in (-1, 1):
            obox(o.mesh, (xc + sx * (hw + 0.002), ym_c, z_), X3, (0.004, hy_c + 0.006, 0.003), "Intake_Pipe")
    # hot tank: rounded top that follows the skin 22 mm under it, so it is shallow at the front (little flow left)
    # and deep at the rear bay where the riser comes in; ribbed across
    def hp_top(y_):
        return min(body_ztop(0.0, y_), body_ztop(abs(xa), y_), body_ztop(abs(xb), y_), body_ztop(abs(cac["xr0"]), y_)) - 0.022
    ys_hp = [ya_c + (yb_c - ya_c) * k / 10 for k in range(11)]
    secs = [(y_, cac["z1"], hp_top(y_)) for y_ in ys_hp] + [(yb_c + 0.002, cac["zr0"], hp_top(yb_c)),
                                                            (cac["ya"], cac["zr0"], hp_top(cac["ya"]))]
    cac["zh_r"] = max(t for _, _, t in secs)
    cac["hp_secs"] = secs
    xloft(o.mesh, [(y_, tank(xa, xb, zb_, zt_o)) for y_, zb_, zt_o in secs[:11]], "Intake_Hot")
    xloft(o.mesh, [(y_, tank(cac["xr0"], cac["xr1"], cac["zr0"], hp_top(y_))) for y_ in (yb_c, cac["ya"] - 0.012)]
          + [(cac["ya"], tank(cac["xr0"] + 0.010, cac["xr1"] - 0.010, cac["zr0"] + 0.008, hp_top(cac["ya"]) - 0.010, r_=0.012))], "Intake_Hot")
    for k in range(1, 8):                                                 # ribs across the hot tank
        y_ = ya_c + (yb_c - ya_c) * k / 8
        xloft(o.mesh, [(y_ - 0.003, tank(xa, xb, cac["z1"], hp_top(y_ - 0.003), grow=0.003)),
                       (y_ + 0.003, tank(xa, xb, cac["z1"], hp_top(y_ + 0.003), grow=0.003))], "Intake_Pipe")
    o = new("OPF_CAC_Propane_Headers", "OPFPLG_Cooling")
    for sgn in (-1, 1):
        xh_ = cac_x(sgn) - sgn * 0.004
        for z_, r_, mat_ in ((cac["z0"] + 0.006, 0.007, "Aux_Liquid"), (zm - 0.011, 0.009, "Aux_Vapour"),
                             (zm + 0.009, 0.006, "Hot_Aux_Liquid"), (cac["z1"] - 0.010, 0.009, "Hot_Aux_Vapour")):
            pipe(o.mesh, [(xh_, cac["y0"] + 0.005, z_), (xh_, cac["y1"] - 0.005, z_)], r_, mat_, n=10)
    d["cac_floor_open"] = (xa, -d["xi0"])                             # floor opening over the air chest (x range)

    # charge riser: compressor outlet (top of the volute, heading forward) -> up behind the block -> into the
    # hot plenum's rear bay from below
    o = new("OPF_Charge_Air_Pipe", "OPFPLG_Air")
    # inboard low (under the wing root, between the compressor, the intake housing and the motor case), then up
    pts = [c_port, (c_port[0], 1.300, c_port[2] + 0.004), (-0.150, 1.282, 0.825), (-0.070, 1.294, 0.835),
           (-0.022, 1.275, 0.885), (-0.020, 1.262, cac["zr0"] + 0.010)]
    pipe(o.mesh, pts, rca, "Intake_Hot", bend=0.05)
    route("charge riser", pts, rca)

    # exhaust outlet: through the rear end wall of the exhaust chest, down and aft to the turbine inlet
    # exhaust: three belt necks -> bolt-on manifold under the block -> bottom of the turbine volute
    d["r_out"] = 0.065
    # separate exhaust manifold: a flat stainless log bolted under the three belt necks, growing as each cylinder
    # joins, then round into the bottom of the turbine volute. It hangs under the block, clear of the stators.
    def rrect(xc_, zt_o, w_, h_, n_=4, r_=None):
        r_ = min(r_, 0.4999 * min(w_, h_)) if r_ else (min(w_, h_) / 2 * 0.999 if abs(w_ - h_) < 1e-6 else min(0.022, 0.45 * min(w_, h_)))
        out_ = []
        for cx_, cz_, a0_ in ((xc_ + w_ / 2 - r_, zt_o - r_, 0.0), (xc_ - w_ / 2 + r_, zt_o - r_, math.pi / 2),
                              (xc_ - w_ / 2 + r_, zt_o - h_ + r_, math.pi), (xc_ + w_ / 2 - r_, zt_o - h_ + r_, 1.5 * math.pi)):
            out_ += [(cx_ + r_ * math.cos(a0_ + math.pi / 2 * k / n_), cz_ + r_ * math.sin(a0_ + math.pi / 2 * k / n_)) for k in range(n_ + 1)]
        return out_
    xm_ = 0.5 * sum(d["ex_throat_x"])
    z_mt = d["ex_flange_z"] - 0.006                                    # manifold top (under the flange frames)
    y1m, y2m, y3m = d["cyl_y"]
    yt_ = EX_THROAT_Y / 2
    y_pk = ACC_Y0 + ACC_L                                              # rear end of the LTO pack
    xo2 = xm_
    wt_, ht_ = EX_MAN_TOP

    def kh(xc_, zt_o, wt, ht, wb, hb, c_=0.010):
        """Manifold outline (20 points, same order as rrect): an upper part wt x ht that sits up inside the block's open
        underside, on a lower part wb x hb that can be wider because it hangs below the block."""
        zs, zb = zt_o - ht, zt_o - ht - hb
        c2 = min(c_, 0.45 * hb, 0.45 * wb)
        xr, xl, xR, xL = xc_ + wt / 2, xc_ - wt / 2, xc_ + wb / 2, xc_ - wb / 2
        return [(xR, zs), (xr, zs), (xr, zt_o - c_), (xr - c_, zt_o), (xc_ + 0.001, zt_o),
                (xc_ - 0.001, zt_o), (xl + c_, zt_o), (xl, zt_o - c_), (xl, zs), (xL, zs),
                (xL, zs - 0.001), (xL, zb + c2), (xL + c2, zb), (xc_ - 0.002, zb), (xc_ - 0.001, zb),
                (xc_ + 0.001, zb), (xc_ + 0.002, zb), (xR - c2, zb), (xR, zb + c2), (xR, zs - 0.001)]
    B_ = EX_MAN_BOT
    # recessed in the block over the pack; a wider lower part appears as cylinder 2 feeds in, and grows behind the pack
    msecs = [(y1m - yt_ - 0.016, kh(xo2, z_mt - 0.003, wt_ * 0.8, 0.045, wt_ * 0.8, 0.006)),
             (y1m - yt_ - 0.006, kh(xo2, z_mt, wt_, ht_, *B_[0])), (y2m - yt_ - 0.006, kh(xo2, z_mt, wt_, ht_, *B_[0])),
             (y_pk + 0.004, kh(xo2, z_mt, wt_, ht_, *B_[1])), (y_pk + 0.070, kh(xo2, z_mt, wt_, ht_, *B_[2])),
             (y3m - yt_ - 0.006, kh(xo2, z_mt, wt_, ht_, *B_[2])), (y3m + yt_ + 0.006, kh(xo2, z_mt, wt_, ht_, *B_[3]))]
    h1, h3 = ht_ + B_[0][1], ht_ + B_[3][1]
    wp = B_[1][0]
    # ... and carries on as ONE piece to the turbine: it turns round and rises once it is clear of the block's rear end
    ro_ = d["r_out"]
    y_be = y3m + d["flange_r"] + 0.006                                 # just behind the block and the cylinder 3 housing flange
    tail = [(y_be, 0.5 * (xo2 + t_port[0]) - 0.030, z_mt, 0.150, 0.104, 0.040),
            (0.5 * (y_be + t_port[1]) - 0.004, 0.5 * (xo2 + t_port[0]) + 0.022, 0.5 * (z_mt + t_port[2] + ro_), 0.136, 0.126, 0.058),
            (t_port[1] - 0.022, t_port[0], t_port[2] + ro_, 2 * ro_, 2 * ro_, ro_), (t_port[1], t_port[0], t_port[2] + ro_, 2 * ro_, 2 * ro_, ro_)]
    msecs += [(y_, rrect(x_, zt_o, w_, h_, r_=rc_)) for y_, x_, zt_o, w_, h_, rc_ in tail]
    o = new("OPF_Exhaust_Manifold", "OPFPLG_Air")
    xloft(o.mesh, msecs, "Exhaust_Pipe")
    tx_ = d["ex_throat"][0] / 2
    for yn_ in d["ex_neck_y"]:                                         # flange frame round each opening
        for sy_ in (-1, 1):
            obox(o.mesh, (xm_, yn_ + sy_ * (yt_ + 0.008), z_mt + 0.002), X3, (tx_ + 0.010, 0.008, 0.002), "Exhaust_Pipe")
        for sx_ in (-1, 1):
            obox(o.mesh, (xm_ + sx_ * (tx_ + 0.005), yn_, z_mt + 0.002), X3, (0.005, yt_, 0.002), "Exhaust_Pipe")
    d["ex_man"] = dict(z_top=z_mt, z_bot=z_mt - h3, y0=y1m - yt_ - 0.016, y_pk=y_pk,
                       pack_gap1=z_mt - h1 - ACC_TOP_BAY, pack_gap=z_mt - ht_ - B_[1][1] - ACC_TOP_BAY)
    route("exhaust manifold over the pack", [(xo2, y1m - yt_, z_mt - 0.054), (xo2, y_pk + 0.004, z_mt - 0.054)], 0.054)
    route("exhaust manifold behind the pack", [(xo2, y_pk + 0.100, z_mt - h3 / 2), (xo2, y3m + yt_, z_mt - h3 / 2)], h3 / 2)
    # double radiant shield between the manifold and the LTO pack lid
    for z_ in (0.006, 0.011):
        obox(o.mesh, (xo2, 0.5 * (y1m - yt_ - 0.030 + y_pk), ACC_TOP_BAY + z_), X3,
             (wp / 2 + 0.030, 0.5 * (y_pk - y1m + yt_ + 0.030), 0.0008), "Heat_Shield")
    route("exhaust outlet", [(x_, y_, zt_o - h_ / 2) for y_, x_, zt_o, w_, h_, rc_ in tail], ro_)

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

    # ---- power electronics: an inverter on top of each stator housing (the housing wall is its cold plate),
    #      a 900 V bus along each side, DC/DC and controller beside the pack
    inv_hx, inv_hy, inv_h = 0.115, 0.058, 0.056
    x_inv = 0.295                                                      # inverter centre along the housing (x 0.18..0.41)
    u_term = d["so_u1"] - 0.030                                        # stator AC terminal on the housing top
    z_bus, x_bus = zc + d["flange_r"] + 0.011, 0.165                   # bus just above the block top, inboard of the inverters
    d["boxes"] = []
    o_sd = new("OPF_Inverter_Saddles", "OPFPLG_Cooling")
    o = new("OPF_Inverters", "OPFPLG_Electrical")
    o_ac = new("OPF_AC_Leads", "OPFPLG_Electrical")
    o_bus = new("OPF_DC_Bus", "OPFPLG_Electrical")
    taps = {1: [], -1: []}
    for ci, yc in enumerate(d["cyl_y"]):
        th = math.radians(INV_TILT_DEG[ci])
        nrm = (0.0, -math.sin(th), math.cos(th))                       # outward from the housing axis
        tng = (0.0, math.cos(th), math.sin(th))
        for sgn in (-1, 1):
            ex = (1.0, 0.0, 0.0)
            def at(x_, r_):
                return (sgn * x_, yc + nrm[1] * r_, zc + nrm[2] * r_)
            obox(o_sd.mesh, at(x_inv, d["r_ho"] + 0.003), (ex, tng, nrm), (inv_hx, inv_hy, 0.007), "Cold_Plate")
            c_ = at(x_inv, d["r_ho"] + 0.010 + inv_h / 2)
            obox(o.mesh, c_, (ex, tng, nrm), (inv_hx, inv_hy, inv_h / 2), "Inverter")
            obox(o.mesh, at(x_inv, d["r_ho"] + 0.010 + inv_h + 0.0015), (ex, tng, nrm), (inv_hx - 0.008, inv_hy - 0.008, 0.0015), "Inverter_Lid")
            d["boxes"].append((f"inverter cyl{ci + 1}", c_, (ex, tng, nrm), (inv_hx, inv_hy, inv_h / 2 + 0.010)))
            for k in (-1, 0, 1):                                       # three-phase stubs from the stator terminal
                b0 = add(at(u_term, d["r_ho"] - 0.003), mul(tng, 0.030 * k))
                pipe(o_ac.mesh, [b0, add(b0, mul(nrm, 0.016))], 0.006, "AC_Lead", n=8)
            t0 = at(x_inv - inv_hx, d["r_ho"] + 0.010 + inv_h / 2)      # DC terminal on the inboard end -> side bus
            taps[sgn].append(t0[1])
            pipe(o_bus.mesh, [t0, (sgn * (x_bus + 0.006), t0[1], t0[2]), (sgn * x_bus, t0[1], z_bus)], 0.005, "HV_Orange", bend=0.006, n=8)
    # DC/DC (+x) and controller placeholder (-x) stand beside the pack, under the cylinder-1 housings
    x_dc = ACC_W / 2 + 0.043
    dcdc = ((x_dc, 0.280, ACC_TOP0 - 0.055), (0.028, 0.120, 0.075))
    ctrl = ((-x_dc, 0.250, ACC_TOP0 - 0.045), (0.026, 0.075, 0.055))
    o = new("OPF_DCDC_Converter", "OPFPLG_Electrical")
    obox(o.mesh, dcdc[0], X3, dcdc[1], "DCDC")
    o2 = new("OPF_Control_Electronics_Placeholder", "OPFPLG_Electrical")
    obox(o2.mesh, ctrl[0], X3, ctrl[1], "Controller")
    o_cp = new("OPF_Cold_Plates", "OPFPLG_Cooling")
    for (cxyz, hh), sg in ((dcdc, 1), (ctrl, -1)):
        obox(o_cp.mesh, (cxyz[0] - sg * (hh[0] + 0.003), cxyz[1], cxyz[2]), X3, (0.003, hh[1], hh[2] - 0.005), "Cold_Plate")
    d["boxes"] += [("DC/DC", dcdc[0], X3, dcdc[1]), ("controller", ctrl[0], X3, ctrl[1])]
    o = new("OPF_HV_Pack_Link", "OPFPLG_Electrical")                   # DC/DC -> pack, 30 mm long
    pk = (ACC_W / 2 + 0.006, 0.300, ACC_TOP_BAY - 0.024)
    obox(o.mesh, pk, X3, (0.006, 0.022, 0.016), "HV_Orange")
    # side buses: along each side at x 0.165 just above the block, down in front of cylinder 1, cross-link, to
    # the DC/DC; the e-turbo joins the +x bus at the rear
    y_fr, z_x = d["cyl_y"][0] - d["flange_r"] - 0.012, ACC_TOP0 + 0.030
    for sgn in (-1, 1):
        pts = [(sgn * x_bus, max(taps[sgn]) + 0.010, z_bus), (sgn * x_bus, y_fr + 0.04, z_bus), (sgn * x_bus, y_fr, z_bus - 0.03), (sgn * x_bus, y_fr, z_x)]
        pipe(o_bus.mesh, pts, 0.007, "HV_Orange", bend=0.02, n=10)
        route(f"DC bus {'L' if sgn > 0 else 'R'}", pts, 0.007)
    pts = [(-x_bus, y_fr, z_x), (x_bus, y_fr, z_x), (x_dc - 0.010, y_fr + 0.010, z_x), (x_dc - 0.010, dcdc[0][1] - 0.080, dcdc[0][2] + dcdc[1][2])]
    pipe(o_bus.mesh, pts, 0.007, "HV_Orange", bend=0.02, n=10)
    route("DC cross-link to the DC/DC", pts, 0.007)
    pts = [(0.0, yT, zT + 0.115), (0.09, yT - 0.06, 0.80), (x_bus, 1.30, z_bus - 0.022), (x_bus, max(taps[1]) + 0.010, z_bus)]
    pipe(o_bus.mesh, pts, 0.006, "HV_Orange", bend=0.03, n=10)
    route("e-turbo HV feed", pts[1:], 0.006)

    # ---- auxiliary propane circuits (left / right): receiver + pump -> inverter cold plates -> charge air
    #      cooler -> top sector of that side's pusher condenser
    o_rc = new("OPF_Aux_Receivers", "OPFPLG_Cooling")
    for sgn, side in ((1, "L"), (-1, "R")):
        pfr = pusher_frame(sgn)
        zlip = PUSHER_Z0 - Z_LIP_OFF
        th_a, th_h = sector_table(sgn)[3][1], sector_table(sgn)[4][1]
        dth = math.radians(10.0) * sgn
        zr = 0.468
        cyl(o_rc.mesh, Frame((sgn * 0.085, yT, zr), (1, 0, 0)), 0.036, -0.058, 0.058, "Aux_Liquid", n=24)
        obox(o_rc.mesh, (sgn * 0.085, yT - 0.057, zr), X3, (0.030, 0.024, 0.022), "Valve_Actuator")     # feed pump, on the receiver's front
        for e in (-1, 1):                                                                                 # receiver end bosses
            obox(o_rc.mesh, (sgn * 0.085, yT + e * 0.040, zr), X3, (0.014, 0.008, 0.014), "Aux_Liquid")
        y_val = 0.5 * (d["cyl_y"][1] + d["cyl_y"][2])          # lower valley between cylinders 2 and 3
        o = new(f"OPF_Aux_Liquid_Feed_{side}", "OPFPLG_Cooling")
        z_un = zc - d["flange_r"] - 0.018                              # under the chests, behind the pack
        x_af = sgn * 0.085
        if sgn > 0:                                                     # this side runs inboard of the exhaust outlet and under the manifold
            z_un, x_af = d["ex_man"]["z_bot"] - 0.034, -0.020
        box = dcdc if sgn > 0 else ctrl
        (bx, by, bz), (hx_, hy_, hz_) = box
        bx = bx - sgn * (hx_ + 0.003)                                  # the cold plate on the inboard face
        pts_af = [(sgn * 0.085, yT - 0.078, zr), (x_af, yT - 0.125, 0.405), (x_af, y_val + 0.10, z_un), (x_af, y_val, z_un), (sgn * 0.400, y_val, z_un),
                  (bx + (0.016 if sgn > 0 else 0.0), by + hy_ + 0.050, z_un), (bx, by + hy_, bz)]
        pipe(o.mesh, pts_af, 0.008, "Aux_Liquid", bend=0.03, n=10)
        route(f"aux feed {side}", pts_af[1:-1], 0.008)
        # out of the front of the cold plate, up in front of cylinder 1, inboard to the cooler's liquid header
        x_up = sgn * 0.120                                              # inboard of the side bus and the tilted inverters
        pts = [(bx, by - hy_, bz - 0.030), (bx + sgn * 0.012, y_fr - 0.034, bz - 0.030), (bx + sgn * 0.012, y_fr - 0.034, bz + 0.170),
               (x_up, y_fr - 0.034, bz + 0.250), (x_up, y_fr - 0.034, cac["z0"] + 0.010),
               (cac_x(sgn) + sgn * 0.010, y_fr - 0.005, cac["z0"] + 0.010), (cac_x(sgn) - sgn * 0.004, cac["y0"] + 0.012, cac["z0"] + 0.006)]
        pipe(o.mesh, pts, 0.008, "Aux_Liquid", bend=0.03, n=10)
        route(f"cooler liquid feed {side}", pts[1:-1], 0.008)
        o = new(f"OPF_Ext_Vapour_Line_Aux_{side}", "OPFPLG_External")
        # out of the core's rear corner, aft in the 30 mm corridor beside the hot plenum, then up to the old line
        x_v, z_v = (cac["xr1"] + 0.024 if sgn > 0 else -0.132), cac["z1"] - 0.012   # beside the rear bay
        pts = [(cac_x(sgn) - sgn * 0.004, cac["y1"] - 0.010, zm - 0.011), (x_v, cac["y1"] + 0.022, z_v),
               (x_v, cac["ya"] + 0.010, z_v), (sgn * 0.110, cac["ya"] + 0.12, 1.040)]
        route(f"cooler vapour line {side}", pts[1:], 0.015)
        pipe(o.mesh, pts + [(sgn * 0.110, 1.80, 1.040), pfr.Pc(R_OUT, th_a - dth, zlip),
                      pfr.Pc(R_OUT, th_a - dth, HX_Z_LE - 0.005), pfr.Pc(R_RING, th_a - dth, HX_Z_LE - 0.005)],
             0.015, "Aux_Vapour", bend=0.04, n=12)
        o = new(f"OPF_Ext_Liquid_Return_Aux_{side}", "OPFPLG_External")
        z_te = HX_Z_LE + HX_CHORD + 0.005
        pipe(o.mesh, [pfr.Pc(R_RING, th_a + dth, z_te), pfr.Pc(R_OUT, th_a + dth, z_te), pfr.Pc(R_OUT, th_a + dth, zlip),
                      (sgn * 0.070, 1.86, 0.950), (sgn * 0.070, 1.70, 0.560), (sgn * 0.085, yT + 0.10, zr + 0.01),
                      (sgn * 0.085, yT + 0.044, zr)], 0.009, "Aux_Liquid", bend=0.05, n=10)   # into the receiver's rear boss
        # hot-stage circuit: vapour from the upper headers to the Hot sector, liquid back along the same run
        # (pumped; the pump sits on the return in the tail). Both lines run above the cold-stage vapour line.
        o = new(f"OPF_Ext_Hot_Stage_Lines_{side}", "OPFPLG_External")
        for kind, dz, r_, mat_, z_hd, z_hx, th_ in (("vapour", 0.036, 0.013, "Hot_Aux_Vapour", cac["z1"] - 0.010, HX_Z_LE - 0.005, th_h - dth),
                                                   ("liquid", 0.062, 0.007, "Hot_Aux_Liquid", zm + 0.009, z_te, th_h + dth)):
            pts = [(cac_x(sgn) - sgn * 0.004, cac["y1"] - 0.010, z_hd), (x_v, cac["y1"] + 0.022, z_v + dz),
                   (x_v, cac["ya"] + 0.010, z_v + dz), (sgn * 0.110, cac["ya"] + 0.12, 1.040 + dz)]
            route(f"hot-stage {kind} line {side}", pts[1:], r_)
            pipe(o.mesh, pts + [(sgn * 0.110, 1.80, 1.040 + dz), pfr.Pc(R_OUT, th_, zlip), pfr.Pc(R_OUT, th_, z_hx), pfr.Pc(R_RING, th_, z_hx)],
                 r_, mat_, bend=0.04, n=12)
        obox(o.mesh, (sgn * 0.110, 1.62, 1.040 + 0.062), X3, (0.018, 0.035, 0.018), "Valve_Actuator")   # hot-stage feed pump

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
            mv, ml = {"Aux": ("Aux_Vapour", "Aux_Liquid"), "Hot": ("Hot_Aux_Vapour", "Hot_Aux_Liquid")}.get(name, ("Propane_Vapour", "Propane_Liquid"))
            h = span / 2 - math.radians(2.5)
            arc(o.mesh, df, R_RING, z_le - 0.005, th_c - h, th_c + h, 0.015, mv,
                n=max(8, int(span / 0.12)))
            arc(o.mesh, df, R_RING, z_le + chord + 0.005, th_c - h, th_c + h, 0.012, ml,
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
    # centre block beyond the bore walls and galleries: waist skin, two chests (ribbed walls ~40 % solid, inboard
    # end walls, bolt bosses), the bolt-on exhaust shell, mount lugs, injector bosses and internal ribbing
    pitch_, Rb, Rf, Rch = d["pitch"], d["Rb"], d["flange_r"], d["R_ch"]
    rt_area = lambda R: 2 * pitch_ * 2 * R + pi * R * R              # racetrack area
    rt_per = lambda R: 4 * pitch_ + 2 * pi * R                        # racetrack perimeter
    waist_len = d["xi0"] + d["xe0"]
    w_i, w_e = d["blk_face"] - d["xi0"], d["blk_face"] - d["xe0"]
    waist = rt_per(Rb) * waist_len * 0.003 * RHO_AL
    chest_walls = (rt_area(Rf) - rt_area(Rch)) * (w_i + w_e) * 0.40 * RHO_AL
    end_walls = 2 * (rt_area(Rf) - 3 * pi * d["r_sl"] ** 2) * 0.008 * RHO_AL
    bosses = 2 * 18 * pi * (0.0075 ** 2 - 0.0045 ** 2) * 0.5 * (w_i + w_e) * RHO_AL
    # steel exhaust-port inserts in place of the aluminium sleeves
    # exhaust side: closing wall toward the stators (5 mm, ribbed), three stainless port belts with necks and
    # flanges, and the bolt-on manifold with its shield
    wb = w_e - 0.008 - 0.018
    belts = 3 * ((2 * pi * EX_BELT_R * wb + 2 * pi * (EX_BELT_R ** 2 - d["r_sl"] ** 2)) * EX_BELT_T * RHO_SS + 0.5)
    man_len = 2 * pitch_ + 0.18
    manifold = sum(2 * (max(EX_MAN_TOP[0], w_) + EX_MAN_TOP[1] + h_) for w_, h_ in EX_MAN_BOT) / len(EX_MAN_BOT) * man_len * 0.0015 * RHO_SS + 1.5 + 1.0
    shell_ex = belts + manifold + (rt_area(Rf) - 3 * pi * d["r_sl"] ** 2) * 0.005 * 0.6 * RHO_AL
    studs_ex = 0.0
    inserts = 3 * sh(d["r_lo"], d["r_sl"], w_e - 0.008, RHO_SS - RHO_AL)
    ties = waist + chest_walls + end_walls + bosses + shell_ex + studs_ex + inserts + 4 * 0.4 + 5.0
    acc = d.get("acc", dict(kg=LTO_NX * LTO_NY * 0.545))
    m = dict(stators_outer=6 * so, stators_inner=6 * si, moving=6 * d["m_move"], centre_sections=3 * centre,
             housings=6 * housing, block_ties=ties, fasteners=9.0, valves_injectors=9.0,
             exhaust_shell=shell_ex + studs_ex, port_inserts=inserts, air_path=72.0, electronics=90.0, cooling=86.0, pack=acc["kg"] + 14.0)
    m["block"] = m["centre_sections"] + m["housings"] + m["block_ties"] + m["fasteners"]
    m["engine"] = m["stators_outer"] + m["stators_inner"] + m["moving"] + m["block"] + m["valves_injectors"]
    m["package"] = m["engine"] + m["air_path"] + m["electronics"] + m["cooling"] + m["pack"]
    return m


def gas_path(d, P):
    """Mean velocities through the gas path at the continuous point (m/s), with targets."""
    c = CYCLE
    R_ = 287.0
    p_s, T_cac = c["p_s"], 335.0
    rho_c = p_s / (R_ * T_cac)
    rho_h = (p_s + 0.08e5) / (R_ * P["T2"])
    rho_e = p_s * 0.90 / (R_ * P["T_exh"])
    rho_d = 1.06e5 / (R_ * (P["T_exh"] - 160.0))
    Qc, Qh, Qe, Qd = P["m_air"] / rho_c, P["m_air"] / rho_h, P["m_exh"] / rho_e, P["m_exh"] / rho_d
    tab, g = c["motion"], d["g"]
    f_in = sum(1 for x in tab if x + g > d["cb"] - d["h_in"]) / len(tab)
    f_ex = sum(1 for x in tab if x + g > d["cb"] - d["h_ex"]) / len(tab)
    A = lambda r: math.pi * r * r
    man_a = lambda k: 0.94 * (EX_MAN_TOP[0] * EX_MAN_TOP[1] + EX_MAN_BOT[k][0] * EX_MAN_BOT[k][1])
    port = lambda h: 2 * math.pi * d["r_li"] * h * (PORT_ARC_DEG / 360.0) * PORT_OPEN   # ported arc x open share = 60 % of the circumference
    bore_station = lambda w: w * 2 * (d["R_ch"] - d["r_sl"])              # chest section over and under a bore
    w_i, w_e = d["blk_face"] - d["xi0"] - 0.008, d["blk_face"] - d["xe0"] - 0.008
    cac = d["cac"]
    L_core = cac["y1"] - cac["y0"]
    w_core = 2 * cac["hw"] - 0.012
    h_cold = cac["z0"] - cac["zp0"]
    x_open0, x_open1 = d["cac_floor_open"]
    share = (cac["x1"] - x_open1) / (2 * cac["hw"])                   # air that has to cross toward the opening
    v_face = Qh / (w_core * L_core)
    dp_core = 0.10 * ((cac["z1"] - cac["z0"]) / 0.0025) * 0.5 * (0.5 * (rho_h + rho_c)) * (v_face / 0.80) ** 2
    rows = [
        ("charge riser (hot)", Qh / A(d["r_ca"]), 60),
        ("hot plenum where the riser comes in", Qh / ((cac["xr1"] - cac["xr0"]) * (cac["zh_r"] - cac["zr0"])), 45),
        ("cooler core face, air passing straight down", v_face, 8),
        ("cold plenum toward the air chest", Qc * share / (L_core * h_cold), 25),
        ("floor opening into the air chest", Qc / ((x_open1 - x_open0) * L_core), 25),
        ("air chest round each bore", Qc / 3 / bore_station(w_i), 40),
        ("intake ports while open", Qc / 3 / f_in / port(d["h_in"]), 100),
        ("exhaust ports while open", Qe / 3 / f_ex / port(d["h_ex"]), 150),
        ("flange opening under the bore while the ports are open", Qe / 3 / f_ex / ((EX_THROAT_X1 - d["xe0"] - 0.014) * EX_THROAT_Y), 150),
        ("manifold over the pack after cylinder 1", Qe / 3 / man_a(0), 95),
        ("manifold at the pack's rear end (cylinders 1 + 2)", Qe * 2 / 3 / man_a(1), 95),
        ("manifold behind the pack (cylinders 1 + 2)", Qe * 2 / 3 / man_a(2), 95),
        ("manifold after cylinder 3", Qe / man_a(3), 95),
        ("exhaust outlet", Qe / A(d["r_out"]), 95),
        ("turbine inlet", Qe / A(d["scroll_rbig"] * TURBO_K), 110),
        ("downpipe after the turbine", Qd / A(d["r_dp"]), 70),
    ]
    return dict(rows=rows, Q=dict(cold=Qc, hot=Qh, exh=Qe, down=Qd), open=(f_in, f_ex),
                cac_len=L_core, cac_depth=cac["z1"] - cac["z0"], dp_core=dp_core, areas=dict(chest_in=bore_station(w_i), chest_ex=bore_station(w_e)))


def crown_state(d, q_crown_w, T_boil=339.0):
    """Sodium-cooled crown at a given crown heat (W): fluxes and temperatures from the propane to the gas face."""
    na = d["na"]
    fx_gas = q_crown_w / d["A"]
    fx_sink = q_crown_w / na["a_sink"]                    # through the jacket and back-plate walls
    fx_prop = fx_sink / NA_FIN                            # on the finned, propane-wetted side
    T_wp = T_boil + 15.0                                  # wall on the propane side, nucleate boiling
    T_wn = T_wp + fx_sink * NA_T_WALL / NA_K_WALL         # wall on the sodium side
    T_na = T_wn + fx_sink / NA_H_SHAKE                    # bulk sodium
    T_face = T_na + fx_gas / NA_H_SHAKE + fx_gas * NA_T_PLATE / NA_K_PLATE
    return dict(face_margin=TI_T_LIMIT - T_face, q=q_crown_w, fx_gas=fx_gas, fx_sink=fx_sink, fx_prop=fx_prop, T_wn=T_wn, T_na=T_na, T_face=T_face,
                chf_margin=CHF_PROPANE / fx_prop, melt_margin=T_wn - NA_T_MELT)


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
    q_inv1 = r["gen_kw"] * (1 - r["eta_inv"]) / 6 * 1e3                 # each inverter, into its housing's chamber
    q_p = (c["Q_wall"] + c["W_fric"] + (c["E_mech"] - c["E_el"])) * f + hyst + q_inv1
    r["q_piston_kw"] = q_p / 1e3
    r["q_parts"] = dict(wall=c["Q_wall"] * f / 1e3, friction=c["W_fric"] * f / 1e3,
                        stator=(c["E_mech"] - c["E_el"]) * f / 1e3, bounce=hyst / 1e3, inverter=q_inv1 / 1e3)
    r["q_hot_kw"] = m_air * 1005.0 * (T2 - CAC_T_MID) / 2e3             # hot stage of the cooler, per side
    r["q_aux_kw"] = (m_air * 1005.0 * (CAC_T_MID - T_cac) / 1e3 + 4.0 + 3.0) / 2   # cold stage + DC/DC + e-turbo machine
    r["q_total_kw"] = 6 * r["q_piston_kw"] + 2 * (r["q_aux_kw"] + r["q_hot_kw"])
    r["T_cond_hot"] = T_COND_HOT
    # what the core can do with its real size (half the depth per stage), against the 62 C the cycle assumes
    cac = d["cac"]
    v_core = (cac["y1"] - cac["y0"]) * (2 * cac["hw"] - 0.012) * (cac["z1"] - cac["z0"])
    ntu = 0.8 * CAC_BETA * CAC_H_AIR * v_core / (m_air * 1005.0)
    T_m = (T_COND_HOT + 2.0) + (T2 - T_COND_HOT - 2.0) * math.exp(-ntu / 2)
    r["cac_est"] = dict(v=v_core, ntu=ntu, T_mid=T_m, T_out=335.0 - 3.0 + (T_m - 332.0) * math.exp(-ntu / 2))
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
        for q, Tc, frac in [(r["q_piston_kw"], r["T_cond_p"], (1 - (AUX_SPAN_DEG + HOT_SPAN_DEG) / 360.0) / 3)] * 3 + \
                           [(r["q_aux_kw"], r["T_cond_aux"], AUX_SPAN_DEG / 360.0), (r["q_hot_kw"], r["T_cond_hot"], HOT_SPAN_DEG / 360.0)]:
            mi = m_fan * frac
            eps = q * 1e3 / (mi * 1005.0 * (Tc - T_air))
            if eps >= 0.97:
                ok, eps = False, 0.97
            area += -math.log(1 - eps) * mi * 1005.0 / (300.0 * 0.85)
        return area, ok
    r["hx_area_hot"], r["hx_ok_hot"] = fin_area(308.0)
    r["hx_area_std"], r["hx_ok_std"] = fin_area(288.0)
    r["hx_area_pack"] = a_ann * HX_CHORD * 1100.0
    r.update(fan_air=m_fan, q_fan_kw=3 * r["q_piston_kw"] + r["q_aux_kw"] + r["q_hot_kw"],
             hx_dT=(3 * r["q_piston_kw"] + r["q_aux_kw"] + r["q_hot_kw"]) * 1e3 / (m_fan * 1005.0),
             vane_area=0.0)
    r["mep_bar"] = c["imep"] / 1e5
    r["crown"] = crown_state(d, c.get("Q_crown", 0.5 * c["Q_wall"]) * f, 0.5 * (r["T_boil_min"] + r["T_boil_max"]))
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
    L.append(f"    recommended DC link 900 V (SiC), tied to the {d['acc']['v_nom']:.0f} V LTO pack through the DC/DC beside it")
    L.append(f"  PROPANE CHAMBERS (one per piston): gas volume {d['Vb_idc'] * 1e3:.1f} -> {d['Vb_odc'] * 1e3:.1f} L, "
             f"pressure {c['pb_min'] / 1e5:.1f} -> {c['pb_max'] / 1e5:.1f} bar each stroke (boils at {P['T_boil_min'] - 273.15:.0f}-{P['T_boil_max'] - 273.15:.0f} C)")
    q = P["q_parts"]
    K = P["crown"]
    L.append(f"  PISTON: one printed titanium piece (Ti-6242), sodium-cooled crown ({d['na']['m'] * 1e3:.0f} g of sodium, half-filled gallery and a {NA_L_JACKET * 1e3:.0f} mm jacket down the skirt). "
             f"Crown heat {K['q'] / 1e3:.1f} kW = {K['fx_gas'] / 1e6:.2f} MW/m2 on the gas face, spread to {K['fx_prop'] / 1e6:.2f} MW/m2 on the "
             f"finned propane side (limit about {CHF_PROPANE / 1e6:.2f}: margin x{K['chf_margin']:.1f})   {'OK' if K['chf_margin'] >= 1.5 else 'CHECK'}")
    L.append(f"    sodium about {K['T_na'] - 273.15:.0f} C, its cold wall {K['T_wn'] - 273.15:.0f} C ({K['melt_margin']:+.0f} K against freezing at 98 C)   "
             f"{'OK' if K['melt_margin'] >= 15 else 'CHECK'}; gas face about {K['T_face'] - 273.15:.0f} C (the cycle model uses {c.get('T_crown', 480.0) - 273.15:.0f} C; alloy limit about {TI_T_LIMIT - 273.15:.0f} C)   {'OK' if K['face_margin'] >= 50 else 'CHECK'}")
    L.append(f"    gas plate {NA_T_PLATE * 1e3:.1f} mm on printed pillars at {NA_PILLAR_PITCH * 1e3:.0f} mm pitch: about {d['na']['plate_mpa'] * c['p_max'] / 1e6:.0f} MPa bending at peak pressure (rough panel estimate)")
    L.append(f"    heat per circuit {P['q_piston_kw']:.0f} kW (crown + liner {q['wall']:.0f}, stators {q['stator']:.1f}, friction {q['friction']:.1f}, "
             f"bounce losses {q['bounce']:.1f}, inverter on top {q['inverter']:.1f}) -> {P['vap_piston_gps']:.0f} g/s of vapour, "
             f"{P['bleed_frac'] * 100:.0f} % of the swept volume bled per stroke")
    L.append(f"    condenser side held near {P['p_cond'] / 1e5:.1f} bar ({P['T_cond_p'] - 273.15:.0f} C): liquid enters through the check valve "
             f"at the low end of the swing, vapour leaves through the bleed valve at the high end")
    E = P["cac_est"]
    L.append(f"  CHARGE AIR COOLER, two stages: {P['m_air']:.2f} kg/s from {P['T2'] - 273.15:.0f} C to {CAC_T_MID - 273.15:.0f} C in the hot stage (top half of the core, "
             f"{P['q_hot_kw']:.0f} kW per side into its own circuits condensing at {T_COND_HOT - 273.15:.0f} C), then to 62 C in the cold stage "
             f"({P['q_aux_kw']:.0f} kW per auxiliary circuit with the DC/DC, controller and e-turbo machine, condensing at {P['T_cond_aux'] - 273.15:.0f} C)")
    L.append(f"    core as drawn ({E['v'] * 1e3:.1f} L, NTU about {E['ntu']:.1f} at the assumed fin density): about {E['T_mid'] - 273.15:.0f} C between the stages and "
             f"{E['T_out'] - 273.15:.0f} C out, against the 62 C the cycle assumes   {'OK' if E['T_out'] <= 338.0 else 'CHECK'}")
    L.append(f"    condenser sectors per pusher: 3 piston circuits {(360 - AUX_SPAN_DEG - HOT_SPAN_DEG) / 3:.0f} deg each, hot stage {HOT_SPAN_DEG:.0f} deg, auxiliary {AUX_SPAN_DEG:.0f} deg")
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
    G = gas_path(d, P)
    d["flow"] = G
    L.append(f"  GAS PATH (mean velocities at the continuous point; air {P['m_air']:.2f} kg/s, exhaust {P['m_exh']:.2f} kg/s):")
    for name, v, tgt in G["rows"]:
        L.append(f"    {name:48s} {v:5.0f} m/s   target <= {tgt:3.0f}   {'OK' if v <= tgt else 'HIGH'}")
    L.append(f"    charge air cooler: stacked, core {G['cac_len'] * 1000:.0f} mm long x {G['cac_depth'] * 1000:.0f} mm deep in the flow, rough core loss "
             f"{G['dp_core'] / 1000:.1f} kPa; ports open {G['open'][0] * 100:.0f} % (intake) and {G['open'][1] * 100:.0f} % (exhaust) of the cycle")
    L.append(f"    cooler to the block over the exhaust belts: {d['cac_ex_gap'] * 1000:.0f} mm at the closest point (wanted >= {CAC_EX_GAP_MIN * 1000:.0f}), with a double-skin heat shield {d['cac_shield_gap'] * 1000:.0f} mm off it in the gap; the cooler is {(d['cac']['xn'] - d['cac']['x0']) * 1000:.0f} mm wide at the neck and {2 * d['cac']['hw'] * 1000:.0f} mm at the core   {'OK' if d['cac_ex_gap'] >= CAC_EX_GAP_MIN else 'CHECK'}")
    L.append(f"  CENTRE BLOCK: one printed aluminium piece {2 * d['blk_face'] * 1000:.0f} mm wide x {(2 * d['pitch'] + 2 * d['flange_r']) * 1000:.0f} mm long x "
             f"{2 * d['flange_r'] * 1000:.0f} mm tall: a {(d['xi0'] + d['xe0']) * 1000:.0f} mm waist round the combustion zones with a propane gallery in each bore wall "
             f"an air chest ({(d['blk_face'] - d['xi0']) * 1000:.0f} mm) and an exhaust housing ({(d['blk_face'] - d['xe0']) * 1000:.0f} mm) closed toward the stators; "
             f"six stator assemblies bolt to its two faces, 16 x M8 each, carrying about {c['pb_max'] * math.pi * d['r_hi'] ** 2 / 1e3:.0f} kN of chamber pressure load per joint")
    Mx = P["mass"]
    em = d["ex_man"]
    tw_, tl_ = d["ex_throat"]
    a_port = 2 * math.pi * d["r_li"] * d["h_ex"] * (PORT_ARC_DEG / 360.0) * PORT_OPEN
    L.append(f"  PORTS: {N_PORTS} per ring on a {PORT_ARC_DEG:.0f} deg arc, {PORT_OPEN * 100:.0f} % open - exhaust ports centred on straight down, intake ports on straight up. "
             f"Same heights (timing) and the same open area as the old all-round rings: {a_port * 1e4:.0f} cm2 exhaust, {a_port * d['h_in'] / d['h_ex'] * 1e4:.0f} cm2 intake per piston. "
             f"Ports {PORT_ARC_DEG / N_PORTS * PORT_OPEN * math.pi / 180 * d['r_li'] * 1e3:.0f} mm wide, bridges {PORT_ARC_DEG / N_PORTS * (1 - PORT_OPEN) * math.pi / 180 * d['r_li'] * 1e3:.1f} mm (were 18 and 11.8).")
    L.append(f"  EXHAUST: kept apart from the stator assemblies. The exhaust housing's underside is open, and the manifold flange sits {EX_FLANGE_D * 1e3:.0f} mm below each bore axis, "
             f"{(EX_FLANGE_D - d['r_sl']) * 1e3:.0f} mm under the port insert (it was {(d['flange_r'] + 0.004) * 1e3:.0f} mm below the axis, on the block's underside). A short stainless collector wraps the ported arc and opens "
             f"straight down through a {tw_ * 1e3:.0f} x {tl_ * 1e3:.0f} mm flange ({tw_ * tl_ * 1e4:.0f} cm2, x{tw_ * tl_ / a_port:.1f} the port area).")
    L.append(f"    manifold: one stainless piece bolted to the three flanges. Its upper part ({EX_MAN_TOP[0] * 1e3:.0f} x {EX_MAN_TOP[1] * 1e3:.0f} mm) sits up inside the block; a lower part hangs below the block and grows: "
             f"{' / '.join(f'{w_ * 1e3:.0f} x {h_ * 1e3:.0f}' for w_, h_ in EX_MAN_BOT)} mm after cylinder 1 / at the pack's rear end / behind the pack / after cylinder 3, then round into the bottom of the turbine volute. "
             f"Collectors, manifold and closing wall about {Mx['exhaust_shell']:.0f} kg. All 16 bolts of each exhaust-side stator assembly are kept; the lowest four sit beside the manifold in bosses on the closing wall.")
    L.append(f"    manifold to the LTO pack lid: {em['pack_gap1'] * 1000:.0f} mm after cylinder 1, {em['pack_gap'] * 1000:.0f} mm over the last {(em['y_pk'] - d['cyl_y'][1] + EX_THROAT_Y / 2) * 1000:.0f} mm of the pack where cylinder 2 feeds in; "
             f"double radiant shield between (pack lowered {ACC_DROP * 1000:.0f} mm)   {'OK' if em['pack_gap'] >= 0.020 else 'CHECK'}")
    L.append(f"    exhaust-port inserts: a printed steel sleeve carries the exhaust ports and bridges in each bore, with the propane gallery behind it (+{Mx['port_inserts']:.1f} kg over aluminium)")
    M = P["mass"]
    L.append(f"  MASS ESTIMATE (built up from this geometry, about +/-20 %):")
    L.append(f"    stators {M['stators_outer'] + M['stators_inner']:.0f} kg (outer {M['stators_outer'] / 6:.0f} + inner {M['stators_inner'] / 6:.0f} per piston), "
             f"moving parts {M['moving']:.0f} kg")
    L.append(f"    block and casing {M['block']:.0f} kg: bore walls and galleries {M['centre_sections']:.0f}, generator housings "
             f"{M['housings']:.0f}, waist, chests, exhaust collectors and manifold, port inserts and mounts {M['block_ties']:.0f}, fasteners {M['fasteners']:.0f}")
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
    L.append(f"    charge air cooler (spine, between the wing roots): "
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
    acc_ok = (hb - at) >= 0.009 and belly > 0.0 and side > 0.0     # pack is below the bay box by choice; it only has to stay in the skin
    ok_all &= acc_ok
    if ACC_DROP > 0:
        L.append(f"  accumulator lowered {ACC_DROP * 1000:.0f} mm below the bay-box layout (not counted in the engine space):")
    L.append(f"  accumulator: {a['n']} x Toshiba SCiB 20Ah-HP LTO, {a['n']}S, {a['v_nom']:.0f} V nominal, "
             f"{a['kwh']:.1f} kWh, ~{a['kw10']:.0f} kW for 10 s; housings {(hb - at) * 1000:.0f} mm above its lid; "
             f"belly skin {belly * 1000:.0f} mm below it, side skin {side * 1000:.0f} mm from its lower edges   {'OK' if acc_ok else 'CLASH'}")
    L.append(f"  RESULT: {'fits' if ok_all else 'DOES NOT FIT'} - cylinders inside the bay box; e-turbo, cooler, inverters and line trays are "
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
        ("electronics", (215, 38), [o for o in objs if o.coll in ("OPFPLG_Core", "OPFPLG_Block", "OPFPLG_Air", "OPFPLG_Electrical", "OPFPLG_Accumulator") or o.name in ("OPF_Cold_Plates", "OPF_Inverter_Saddles")],
         None, (12, 8)),
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

