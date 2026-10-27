"""Pusher tilt optimisation, fully loaded 3,500 lb. Split front/rear wings (5/5 deg, downwash 0.25),
forward-flight lift ducts (rear canted 10 deg), and a momentum pusher: air enters along the flight path at V
and leaves along the duct axis at v_e, so a tilted duct pays for turning the flow."""
import warnings, math, sys; warnings.filterwarnings("ignore")
sys.argv = [sys.argv[0], "0.25"]
exec(open("split.py").read().split("def solve(")[0])
import numpy as np
ETA_P = 0.75
DCDA_SHORT = -0.004            # m2: 22 % less pusher duct skin (both)
def forces(V, th, phi, ve):
    t = math.radians(th); et = rot(np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))]), t)
    md = RHO * A_p * ve
    return 2 * md * (ve * et - V * np.array([1.0, 0.0])), 2 * 0.5 * md * max(ve * ve - V * V, 0.0) / ETA_P / HP
def solve_p(V, th, phi, iF=5, iR=5, dR=10, dcda=DCDA_SHORT):
    t = math.radians(th); q = 0.5 * RHO * V * V
    aF = th + iF; clF = clw(aF); eps = DOWNWASH * math.degrees(2 * clF / (math.pi * AR_F))
    aR = th + iR - eps; clR = clw(aR)
    LF, LR = q * SF * clF, q * SR * clR
    D = q * (K.CDA_M2 + dcda) + q * (SF + SR) * 2.5 * math.sin(math.radians(th + 5)) ** 2
    m2 = lambda r, f: r[0] * f[1] - r[1] * f[0]
    Ma = m2(rot(rWF, t), np.array([0, LF])) + m2(rot(rWR, t), np.array([0, LR])) + q * (SF * cF + SR * cR) * CM0 + m2(rot(trim.rA, t), np.array([-D, 0]))
    eF = rot(np.array([0, 1.0]), t); eR = rot(np.array([math.sin(math.radians(dR)), math.cos(math.radians(dR))]), t)
    rFe, rRe, rPe = rot(trim.rF, t), rot(trim.rR, t), rot(trim.rP, t)
    A = np.array([[eF[1], eR[1]], [m2(rFe, eF), m2(rRe, eR)]])
    def resid(ve):
        Fp, Pp = forces(V, th, phi, ve)
        TF, TR = np.linalg.solve(A, np.array([Wn - LF - LR - Fp[1], -(Ma + m2(rPe, Fp))]))
        return TF * eF[0] + TR * eR[0] + Fp[0] - D, TF, TR, Fp, Pp
    lo, hi = 0.0, 260.0
    if resid(hi)[0] < 0: return None
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if resid(mid)[0] < 0: lo = mid
        else: hi = mid
    _, TF, TR, Fp, Pp = resid(hi)
    if min(TF, TR) < 0 or max(TF, TR) > 2 * CAP_DUCT: return None
    Tp_axis = np.linalg.norm(Fp) / 2 / LBF
    if Tp_axis > K.PUSHER_MAX_THRUST_LBF: return None
    pF, _ = duct(TF / 2, V, -t); pR, _ = duct(TR / 2, V, math.radians(dR) - t)
    return dict(P=(2 * pF + 2 * pR) / HP + Pp, th=th, TF=TF / LBF, TR=TR / LBF, Tp=Tp_axis, ve=hi, LF=LF / LBF, LR=LR / LBF)
def best_p(V, phi, **kw):
    out = None
    for th in np.arange(-12, 10.01, 0.25):
        r = solve_p(V, th, phi, **kw)
        if r and (out is None or r["P"] < out["P"]): out = r
    return out
def vmax_p(P, phi, **kw):
    v = 0
    for V in np.arange(60, 100, 0.5):
        r = best_p(V, phi, **kw)
        if r and r["P"] <= P: v = V
    return v * MPH
if __name__ == "__main__":
    print("long duct (0.50 m), 20 deg:", end=" "); r = best_p(150 / MPH, 20, dcda=0.0); print(f"{r['P']:.0f} hp @150, Vmax {vmax_p(1500, 20, dcda=0.0):.0f}/{vmax_p(K.P_BURST_HP, 20, dcda=0.0):.0f}")
    print("short duct (0.39 m):")
    print("tilt | hp@150 | Vmax 1500/1913 | 150 mph: pitch, pusher thrust lbf, front/rear duct lbf")
    for phi in (0, 3, 5, 8, 10, 12, 15, 20, 25):
        r = best_p(150 / MPH, phi)
        print(f" {phi:3d} | {r['P']:5.0f}  | {vmax_p(1500, phi):4.0f} / {vmax_p(K.P_BURST_HP, phi):4.0f} | {r['th']:+5.2f}, {r['Tp']:4.0f}, {r['TF']:4.0f}/{r['TR']:4.0f}")
