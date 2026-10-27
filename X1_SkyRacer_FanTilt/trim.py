"""Longitudinal trim of the fully loaded X1 SkyRacer (cockpit25), same aero + power models as the PteroSim kit."""
import math, numpy as np
from mass import X1, K, W, CG
G = 9.80665; LBF = 4.44822; RHO = 1.225; HP = 745.7
Wn = W * LBF
S, b, c, yc = K.wing_metrics(); S_m = S / 10.7639; c_m = c / 3.28084
def body(y, z):  # model (y aft, z up) -> body (x fwd, z up) relative to CG
    return np.array([-(y - CG[1]), z - CG[2]])
rF = body(X1.DUCT_YF, X1.DUCT_ZF); rR = body(X1.DUCT_YR, X1.DUCT_ZR)
rP = body(X1.FWD_C[1], X1.FWD_C[2]); rA = body(yc, 0.85)   # pusher centre from the branch model
A_l = math.pi * (K.LIFT_DUCT_ID_IN / 2 * 0.0254) ** 2; A_p = math.pi * (K.PUSH_DUCT_ID_IN / 2 * 0.0254) ** 2
def CL(a_deg):
    a = a_deg; r = math.radians(a)
    if abs(a) <= 14: return 0.25 + 3.5 * r
    if abs(a) >= 30: return 0.95 * math.sin(2 * r)
    return (0.25 + 3.5 * math.radians(14 * np.sign(a))) * (30 - abs(a)) / 16 + 0.95 * math.sin(2 * r) * (abs(a) - 14) / 16
CD0 = K.CDA_M2 / S_m
CD = lambda a_deg: CD0 + 2.5 * math.sin(math.radians(a_deg)) ** 2
# wing incidence (deg): the wings meet the air at body pitch + INC. Default = the branch model's
# chord-weighted mean (full incidence inboard, tips twisted to their duct rings).
INC = X1.wing_incidence_mean() if hasattr(X1, "wing_incidence_mean") else 0.0
def duct_hp(T_n):  # one coaxial duct, kit hover formula (SI)
    return K.COAX_LOSS * T_n ** 1.5 / (K.FM * math.sqrt(2 * RHO * A_l) * K.DUCT_GAIN ** 1.5) / HP
def pusher_hp(T_n, u):  # one pusher, kit formula
    u = max(u, 0.0)
    return T_n / K.FM * (0.5 * u + math.sqrt(0.25 * u * u + T_n / (2 * A_p * K.DUCT_GAIN * RHO))) / HP
def rot(v, a):
    ca, sa = math.cos(a), math.sin(a); return np.array([ca * v[0] - sa * v[1], sa * v[0] + ca * v[1]])
CAP_DUCT = 2 * K.LIFT_MAX_THRUST_LBF * LBF; CAP_P = K.PUSHER_MAX_THRUST_LBF * LBF
def solve(V, th_deg, dp_deg, dl_deg=0.0, dlr_deg=None):
    """Level flight at V (m/s), body pitch th (deg, + nose up). Returns dict or None if infeasible."""
    dlr_deg = dl_deg if dlr_deg is None else dlr_deg
    th = math.radians(th_deg); q = 0.5 * RHO * V * V
    a = th_deg                                     # level flight: alpha = pitch
    # unit thrust directions in body frame (x fwd, z up)
    dF = np.array([math.sin(math.radians(dl_deg)), math.cos(math.radians(dl_deg))])
    dR = np.array([math.sin(math.radians(dlr_deg)), math.cos(math.radians(dlr_deg))])
    dP = np.array([math.cos(math.radians(dp_deg)), math.sin(math.radians(dp_deg))])
    # earth frame
    eF, eR, eP = rot(dF, th), rot(dR, th), rot(dP, th)
    aw = a + INC                                   # wing angle of attack
    L, D = q * S_m * CL(aw), q * S_m * CD(aw)
    Fa = np.array([-D, L]); Ma_aero = q * S_m * c_m * (-0.3 * math.radians(aw))
    rFe, rRe, rPe, rAe = rot(rF, th), rot(rR, th), rot(rP, th), rot(rA, th)
    m2 = lambda r, f: r[0] * f[1] - r[1] * f[0]   # nose-up moment
    Amat = np.array([[eF[0], eR[0], eP[0]], [eF[1], eR[1], eP[1]], [m2(rFe, eF), m2(rRe, eR), m2(rPe, eP)]])
    rhs = -np.array([Fa[0], Fa[1] - Wn, m2(rAe, Fa) + Ma_aero])
    try: TF, TR, TP = np.linalg.solve(Amat, rhs)
    except np.linalg.LinAlgError: return None
    ok = TF >= 0 and TR >= 0 and TP >= 0 and TF <= 2 * CAP_DUCT and TR <= 2 * CAP_DUCT and TP <= 2 * CAP_P
    u = V * math.cos(math.radians(a + dp_deg))
    P = 2 * duct_hp(TF / 2) + 2 * duct_hp(TR / 2) + (2 * pusher_hp(TP / 2, u) if TP > 0 else 0)
    return dict(ok=ok, TF=TF / LBF, TR=TR / LBF, TP=TP / LBF, P=P, L=L / LBF, D=D / LBF,
                lift_hp=2 * duct_hp(max(TF, 0) / 2) + 2 * duct_hp(max(TR, 0) / 2), th=th_deg)
def best(V, dp, dl=0.0, dlr=None, ths=np.arange(-30, 15.01, 0.25)):
    out = None
    for th in ths:
        r = solve(V, th, dp, dl, dlr)
        if r and r["ok"] and (out is None or r["P"] < out["P"]): out = r
    return out
def vmax(P_av, dp, dl=0.0, dlr=None):
    v = 0.0
    for V in np.arange(10, 130, 0.5):
        r = best(V, dp, dl, dlr)
        if r and r["P"] <= P_av: v = V
    return v
MPH = 2.23694
