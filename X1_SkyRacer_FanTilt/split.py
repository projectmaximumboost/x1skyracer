import warnings, math, sys; warnings.filterwarnings("ignore")
import numpy as np, trim, trim2
from trim import *
from trim2 import duct
trim.rP = body(2.271, 0.80)
ring_in = X1.DUCT_X - X1.DUCT_R1
SF = 2 * (ring_in - 0.30) * 1.00; SR = 2 * (ring_in - 0.15) * 1.10           # m2, as the kit
cF, cR = 1.00, 1.10
rWF = body(X1.DUCT_YF - cF / 4, X1.DUCT_ZF)                                   # quarter-chord points
rWR = body(X1.DUCT_YR - cR / 4, X1.DUCT_ZR - 0.01)
CM0 = -0.07                                                                    # 3 % camber section
DOWNWASH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0                  # rear wing sees front downwash
AR_F = (2 * ring_in) ** 2 / SF
def clw(a): return trim.CL(a)                                                  # kit section curve
def solve(V, th, iF, iR, dp=20, dR=10, ram=False):
    t = math.radians(th); q = 0.5 * RHO * V * V
    aF = th + iF; clF = clw(aF)
    eps = DOWNWASH * math.degrees(2 * clF / (math.pi * AR_F))
    aR = th + iR - eps; clR = clw(aR)
    LF, LR = q * SF * clF, q * SR * clR
    D = q * K.CDA_M2 + q * (SF + SR) * 2.5 * math.sin(math.radians(th + (iF + iR) / 2)) ** 2
    rf, rr = rot(rWF, t), rot(rWR, t)
    m2 = lambda r, f: r[0] * f[1] - r[1] * f[0]
    Ma = m2(rf, np.array([0, LF])) + m2(rr, np.array([0, LR])) + q * (SF * cF + SR * cR) * CM0 + m2(rot(trim.rA, t), np.array([-D, 0]))
    eF = rot(np.array([0, 1.0]), t); eR = rot(np.array([math.sin(math.radians(dR)), math.cos(math.radians(dR))]), t)
    eP = rot(np.array([math.cos(math.radians(dp)), math.sin(math.radians(dp))]), t)
    A = np.array([[eF[0], eR[0], eP[0]], [eF[1], eR[1], eP[1]], [m2(rot(trim.rF, t), eF), m2(rot(trim.rR, t), eR), m2(rot(trim.rP, t), eP)]])
    rhs = -np.array([-D, LF + LR - Wn, Ma])
    TF, TR, TP = np.linalg.solve(A, rhs)
    if min(TF, TR, TP) < 0 or max(TF, TR) > 2 * CAP_DUCT or TP > 2 * CAP_P: return None
    pF, _ = duct(TF / 2, V, -t); pR, _ = duct(TR / 2, V, math.radians(dR) - t)
    u = V * math.cos(math.radians(th + dp))
    P = (2 * pF + 2 * pR) / HP + 2 * pusher_hp(TP / 2, u)
    return dict(P=P, TF=TF / LBF, TR=TR / LBF, TP=TP / LBF, LF=LF / LBF, LR=LR / LBF, th=th, aF=aF, aR=aR)
def best(V, iF, iR):
    out = None
    for th in np.arange(-15, 12.01, 0.25):
        r = solve(V, th, iF, iR)
        if r and (out is None or r["P"] < out["P"]): out = r
    return out
def vmax(P, iF, iR):
    v = 0
    for V in np.arange(40, 100, 0.5):
        r = best(V, iF, iR)
        if r and r["P"] <= P: v = V
    return v * MPH
# static pitch derivative of the wings alone (per rad of alpha), about the CG: + = nose-up = destabilising
aw = 3.5
dM = (rWF[0] * SF * aw + rWR[0] * SR * aw * (1 - DOWNWASH * 2 * aw / (math.pi * AR_F))) / (SF + SR)
print(f"downwash factor {DOWNWASH}: wings-only pitch stiffness {dM:+.3f} m (+ = unstable); front arm {rWF[0]:+.2f} m, rear arm {rWR[0]:+.2f} m")
print("front/rear inc | hp@150 | Vmax 1500/1913 | 150 mph: pitch, front/rear wing lbf, front/rear duct lbf, wing AoA F/R")
for iF, iR in ((5, 5), (3, 5), (2, 5), (0, 5), (0, 7), (2, 7), (5, 7), (7, 5)):
    r = best(150 / MPH, iF, iR)
    print(f"  {iF:2d} / {iR:2d}     | {r['P']:5.0f}  | {vmax(1500, iF, iR):4.0f} / {vmax(K.P_BURST_HP, iF, iR):4.0f} | {r['th']:+5.2f}, {r['LF']:4.0f}/{r['LR']:4.0f}, {r['TF']:4.0f}/{r['TR']:4.0f}, {r['aF']:+.1f}/{r['aR']:+.1f}")
