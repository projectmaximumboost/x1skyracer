"""Trim with a forward-flight lift-duct model (momentum theory, Glauert inflow):
  induced power from the inflow through the tilted disk, plus the propulsive work T * V_n of any duct
  thrust that points along the flight path, plus (optional) duct ram drag m_dot * V_t.
  Hover reduces exactly to the PteroSim kit formula."""
import math, numpy as np
import trim as T0
from trim import *
RAM = False
def duct(Tn, V, tilt):
    """One coaxial duct: thrust Tn (N), airspeed V, disk tilt forward of the flight-path normal (rad).
    Returns (shaft power W, ram drag N)."""
    if Tn <= 0: return 0.0, 0.0
    G = K.DUCT_GAIN
    Vn, Vt = V * math.sin(tilt), V * math.cos(tilt)
    v = math.sqrt(Tn / G / (2 * RHO * A_l))
    for _ in range(60):
        vn = Tn / G / (2 * RHO * A_l * math.sqrt(Vt * Vt + (Vn + v) ** 2))
        v = 0.5 * v + 0.5 * vn
    P = K.COAX_LOSS / K.FM * ((Tn / G) * v + Tn * Vn)
    ram = RHO * A_l * max(Vn + v, 0.0) * Vt if RAM else 0.0
    return max(P, 0.0), ram
def solve2(V, th_deg, dp_deg, dl_deg=0.0, dlr_deg=None):
    dlr_deg = dl_deg if dlr_deg is None else dlr_deg
    th = math.radians(th_deg); q = 0.5 * RHO * V * V; aw = th_deg + T0.INC
    dF = np.array([math.sin(math.radians(dl_deg)), math.cos(math.radians(dl_deg))])
    dR = np.array([math.sin(math.radians(dlr_deg)), math.cos(math.radians(dlr_deg))])
    dP = np.array([math.cos(math.radians(dp_deg)), math.sin(math.radians(dp_deg))])
    eF, eR, eP = rot(dF, th), rot(dR, th), rot(dP, th)
    L, D = q * S_m * T0.CL(aw), q * S_m * T0.CD(aw)
    Ma = q * S_m * c_m * (-0.3 * math.radians(aw))
    rFe, rRe, rPe, rAe = rot(T0.rF, th), rot(T0.rR, th), rot(T0.rP, th), rot(T0.rA, th)
    m2 = lambda r, f: r[0] * f[1] - r[1] * f[0]
    tF, tR = math.radians(dl_deg) - th, math.radians(dlr_deg) - th      # disk tilt vs flight path
    Dram = [0.0, 0.0]
    for _ in range(8):
        Fa = np.array([-D - 2 * Dram[0] - 2 * Dram[1], L])
        Mram = 2 * Dram[0] * rFe[1] + 2 * Dram[1] * rRe[1]          # drag (-x) at height r_z: nose-up +
        A = np.array([[eF[0], eR[0], eP[0]], [eF[1], eR[1], eP[1]], [m2(rFe, eF), m2(rRe, eR), m2(rPe, eP)]])
        rhs = -np.array([Fa[0], Fa[1] - Wn, m2(rAe, np.array([-D, L])) + Ma + Mram])
        try: TF, TR, TP = np.linalg.solve(A, rhs)
        except np.linalg.LinAlgError: return None
        (_, Dram[0]), (_, Dram[1]) = duct(max(TF, 0) / 2, V, tF), duct(max(TR, 0) / 2, V, tR)
    ok = TF >= 0 and TR >= 0 and TP >= 0 and TF <= 2 * CAP_DUCT and TR <= 2 * CAP_DUCT and TP <= 2 * CAP_P
    pF, _ = duct(max(TF, 0) / 2, V, tF); pR, _ = duct(max(TR, 0) / 2, V, tR)
    u = V * math.cos(math.radians(aw - T0.INC + dp_deg))
    P = (2 * pF + 2 * pR) / HP + (2 * pusher_hp(TP / 2, u) if TP > 0 else 0)
    return dict(ok=ok, TF=TF / LBF, TR=TR / LBF, TP=TP / LBF, P=P, L=L / LBF, D=D / LBF, ram=2 * sum(Dram) / LBF, th=th_deg)
def best2(V, dp, dl=0.0, dlr=None, tpmin=0.0, ths=np.arange(-20, 15.01, 0.5)):
    out = None
    for th in ths:
        r = solve2(V, th, dp, dl, dlr)
        if r and r["ok"] and r["TP"] >= tpmin and (out is None or r["P"] < out["P"]): out = r
    return out
def vmax2(P_av, dp, dl=0.0, dlr=None, sched=False, tpmin=0.0):
    v = 0.0
    for V in np.arange(30, 110, 1.0):
        r = best_sched(V, dp, tpmin)[0] if sched else best2(V, dp, dl, dlr, tpmin)
        if r and r["P"] <= P_av: v = V
        elif v > 0: break
    return v * MPH
def best_sched(V, dp, tpmin=0.0, cants=np.arange(-5, 30.1, 2.5)):
    out, cb = None, None
    for c in cants:
        r = best2(V, dp, 0, c, tpmin)
        if r and (out is None or r["P"] < out["P"]): out, cb = r, c
    return out, cb
