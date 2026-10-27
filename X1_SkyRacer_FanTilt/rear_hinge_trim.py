"""Trim cost of the real-hinge rear wing, fully loaded 3,500 lb (same models as ptilt.py: split wings,
forward-flight lift ducts, momentum pushers at 10 deg). Uses the branch model's chord-weighted mean
incidence of each wing, so the rear stub incidence and the twisted outer panel are counted.
Run here: python3 rear_hinge_trim.py"""
import warnings, math, sys, os, io, contextlib; warnings.filterwarnings("ignore")
sys.path.insert(0, os.getcwd()); sys.argv = [sys.argv[0]]
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("ptilt.py").read().split("if __name__")[0])
def mean_inc(key, x0, c0, c1):
    ri = X1.DUCT_X - X1.DUCT_R1; tot = num = 0.0
    for x in np.linspace(x0, ri, 400):
        c = c0 + (c1 - c0) * (x - x0) / (ri - x0); tot += c; num += c * X1.wing_incidence(x, key)
    return num / tot
iF, iR = mean_inc("F", 0.30, 1.05, 0.95), mean_inc("R", 0.15, 1.20, 1.00)
print(f"mean incidence: front {iF:.2f} deg, rear {iR:.2f} deg; rear wing z {X1.DUCT_ZR} m")
r = best_p(150 / MPH, X1.PUSHER_TILT_DEG, iF=iF, iR=iR)
print(f"150 mph: {r['P']:.0f} hp, pitch {r['th']:+.2f} deg, front/rear ducts {r['TF']:.0f}/{r['TR']:.0f} lbf, "
      f"wings {r['LF']:.0f}/{r['LR']:.0f} lbf")
print(f"top speed {vmax_p(1500, X1.PUSHER_TILT_DEG, iF=iF, iR=iR):.0f} / {vmax_p(K.P_BURST_HP, X1.PUSHER_TILT_DEG, iF=iF, iR=iR):.0f} mph (1,500 / 1,913 hp)")
