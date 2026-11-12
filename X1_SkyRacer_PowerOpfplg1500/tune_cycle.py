"""Run the cycle model on the script's geometry and write the CYCLE block (per piston)."""
import math, os, sys, json
from opf_cycle import simulate, LHV, AFR_ST

def run(m, d, lam=1.9, p_s=3.8e5, T_trap=380.0, cycles=160):
    """One operating point. Generator losses are worked out here from the force trace: winding loss follows
    force squared over the stator area actually covering the magnets, core loss is a share of converted energy."""
    A = d["A"]
    mt = p_s * A * d["x_po"] / (287.0 * T_trap)
    Qf = 0.90 * mt / AFR_ST / lam * LHV
    P = dict(B=d["B"], m=d["m_move"], x_po=d["x_po"], h_port=d["cb"] - d["x_po"], x_idc=d["g"], p_scav=p_s,
             T_trap=T_trap, Q_fuel=Qf, F_pk=d["F_pk"], F_cont=d["F_cont"], Vb_idc=d["Vb_idc"], r_in=1.0,
             v_mean_est=10.5, cu_frac=0.0, fe_frac=0.0, P_rated=1.0, pb0=22e5)
    r = simulate(P, cycles=cycles, trace=True)
    if not r["ok"]:
        return P, r
    c0 = m.Q_CU_REF / 85e3 ** 2 * m.K_RES
    go, gi = d["A_out"] * m.T_SLOT / 0.024, d["A_in"] * (m.T_SLOT - 0.002) / 0.022
    tr = r["trace"]; xmin = min(q[1] for q in tr)
    e_cu = f2a = sig_pk = 0.0
    for a, b in zip(tr, tr[1:]):
        dt = b[0] - a[0]; F = a[5]
        co, ci = m.stator_cover(d, a[1] - xmin)
        G = max(go * co + gi * ci, 1e-6); Ac = max(d["A_out"] * co + d["A_in"] * ci, 1e-6)
        e_cu += c0 * F * F / G * dt
        f2a += (F / Ac) ** 2 * dt
        sig_pk = max(sig_pk, abs(F) / Ac)
    r["e_cu"] = e_cu; r["sig_rms"] = math.sqrt(f2a * r["f"]); r["sig_pk"] = sig_pk
    r["E_el"] = r["E_mech"] * (1 - m.FE_FRAC) - e_cu
    r["P_el"] = r["E_el"] * r["f"]
    r.update(Qf=Qf, lam_set=lam, p_s=p_s, T_trap=T_trap)
    return P, r

def pack(d, P, r):
    g = lambda k, nd=6: round(float(r[k]), nd)
    out = dict(f=g("f", 3), stroke=g("stroke", 5), x_min=g("x_min", 5), x_max=g("x_max", 5), cr=g("cr", 2), p_max=g("p_max", 0),
               v_mean=g("v_mean", 3), v_max=g("v_max", 3), Qf=round(r["Qf"], 2), E_el=g("E_el", 2), E_mech=g("E_mech", 2),
               W_gas=g("W_gas", 2), Q_wall=g("Q_wall", 2), W_fric=g("W_fric", 2), F_rms=g("F_rms", 0), F_peak=g("F_peak", 0),
               pb_min=g("pb_min", 0), pb_max=g("pb_max", 0), pb_mean=g("pb_mean", 0), m_trap=g("m_trap", 6), p_s=r["p_s"],
               lam=round(r["lam"], 3), T_trap=r["T_trap"], imep=g("imep", 0), motion=[])
    for k in ("e_cu", "sig_rms", "sig_pk"):
        if k in r: out[k] = round(float(r[k]), 2)
    return out

def tune(target_hp=1520.0, p_s=3.8e5, here=None):
    here = here or os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here if os.path.exists(os.path.join(here, 'x1_opfplg_blender.py')) else os.path.join(here, 'build'))
    import x1_opfplg_blender as m
    d = m.design()
    lam = 1.85
    for it in range(8):
        P, r = run(m, d, lam=lam, p_s=p_s)
        assert r["ok"], r
        cyc = pack(d, P, r)
        m.CYCLE.clear(); m.CYCLE.update(cyc)
        perf = m.performance(d)
        print("lam %.3f f %.2f net %.0f hp eta %.3f Frms %.2f kN shear %.0f/%.0f kPa pmax %.0f" % (
            lam, r["f"], perf["net_hp"], perf["eta"], r["F_rms"] / 1e3, r["sig_rms"] / 1e3, r["sig_pk"] / 1e3, r["p_max"] / 1e5))
        if abs(perf["net_hp"] - target_hp) < 4: break
        lam *= (perf["net_hp"] / target_hp) ** 0.9
    Pb, rb = run(m, d, lam=1.60, p_s=4.1e5)
    cyc["burst"] = dict(p_s=4.1e5, lam=1.60, bus_hp=round(6 * rb["P_el"] * 0.985 / 745.7, 0), p_max=round(rb["p_max"], 0),
                        f=round(rb["f"], 2), F_rms=round(rb["F_rms"], 0), sig_pk=round(rb["sig_pk"], 0))
    tr = r["trace"]
    T = 1.0 / r["f"]
    i0 = min(range(len(tr)), key=lambda i: tr[i][1])            # inner dead centre
    rot = tr[i0:] + [(q[0] + T,) + tuple(q[1:]) for q in tr[:i0]]
    t0, xmin = rot[0][0], rot[0][1]
    ts = [q[0] - t0 for q in rot]; xs = [q[1] - xmin for q in rot]
    ts.append(T); xs.append(0.0)
    N, tab, j = 96, [], 0
    for k in range(N):                                         # equal time steps through one cycle
        t = T * k / N
        while ts[j + 1] < t: j += 1
        f_ = (t - ts[j]) / (ts[j + 1] - ts[j])
        tab.append(round(xs[j] + (xs[j + 1] - xs[j]) * f_, 6))
    cyc["motion"] = tab
    json.dump(cyc, open(os.path.join(here, 'cycle.json'), 'w'), indent=1)
    step = max(1, len(tr) // 240)                              # one-cycle trace for the viewer, from the inner dead centre
    json.dump([[round((q[0] - t0) * 1e3, 4), round(q[1] * 1e3, 3), round(q[2], 3), round(q[3] / 1e5, 2), round(q[4] / 1e5, 3), round(q[5] / 1e3, 3)]
               for q in rot[::step]], open(os.path.join(here, 'trace.json'), 'w'))
    return cyc

if __name__ == "__main__":
    tune()
