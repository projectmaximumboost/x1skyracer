"""Fully loaded (3,500 lb) mass and CG of the X1 SkyRacer branch model, from the PteroSim kit mass items
with the 500 lb ballast moved to the cockpit25 seats."""
import sys, math, io, contextlib, numpy as np
import os
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(_here), os.path.join(os.path.dirname(_here), "X1_SkyRacer_PteroSim")]   # branch model first
with contextlib.redirect_stdout(io.StringIO()):
    import x1_skyracer_blender as X1
    import x1_pterosim_kit as K
# cockpit25 ballast CG: H-point + 0.20 m up the backrest (same rule the kit used: ~0.28 above cushion)
a = math.radians(X1.SEAT_BACK_DEG)
by, bz = X1.H_Y + 0.20 * math.sin(a), X1.H_Z + 0.20 * math.cos(a)
K.BALLAST_SEATS = [("Ballast, left front seat", (X1.SEAT_X, by, bz)), ("Ballast, right front seat", (-X1.SEAT_X, by, bz))]
# heights the branch model has moved since the kit was written: engine + accumulator (ENGINE_DZ), and
# the lowered rear wing with its lift units
_dz_eng = getattr(X1, "ENGINE_DZ", 0.0)
_z_rw = X1.DUCT_ZR - 0.01
_z_ru = X1.DUCT_ZR + getattr(X1, "REAR_DUCT_RAISE", 0.0)
def _moved(n, c):
    if n.startswith(("generator", "accumulator")):
        return (c[0], c[1], c[2] + _dz_eng)
    if n.startswith("lift unit R"):
        return (c[0], c[1], _z_ru)
    if n == "rear wings":
        return (c[0], c[1], _z_rw)
    return c
K.MASS_ITEMS = [(n, lb, _moved(n, c), box) for n, lb, c, box in K.MASS_ITEMS]
with contextlib.redirect_stdout(io.StringIO()):
    m, cg, I = K.mass_properties()
    rotors, tanks, wheels, empties = K.gather()
W = m + K.FUEL_LB + K.BALLAST_LB
CG = (cg * m + sum(np.array(t["loc"]) * t["contents_lb"] for t in tanks)
      + sum(np.array(l) * K.BALLAST_LB / 2 for _, l in K.BALLAST_SEATS)) / W
Irace = K.race_inertia(tanks, CG)
if __name__ == "__main__":
    print(f"dry {m:.0f} lb, propane {K.FUEL_LB:.0f}, ballast {K.BALLAST_LB:.0f} -> {W:.0f} lb")
    print("ballast seats", K.BALLAST_SEATS)
    print("race CG (model m): x %.3f  y %.3f  z %.3f" % tuple(CG))
    print("old-kit ballast CG would give y:", ((cg * m + sum(np.array(t['loc']) * t['contents_lb'] for t in tanks) + np.array([0, -0.85, 0.66]) * 500) / W).round(3))
    print("Iyy slug ft2 %.0f" % Irace[1, 1])
    for r in rotors: print(r["object"], np.round(r["loc"], 3))
    print("front duct y", X1.DUCT_YF, "rear", X1.DUCT_YR, "-> CG frac from front %.3f" % ((CG[1] - X1.DUCT_YF) / (X1.DUCT_YR - X1.DUCT_YF)))
    S, b, c, yc = K.wing_metrics(); print("wing S %.1f ft2  b %.2f ft c %.2f ft  AERORP y %.3f" % (S, b, c, yc))
