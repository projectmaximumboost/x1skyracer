"""
X1 OPFPLG - single free-piston cycle model (one piston of an opposed pair; the pair is symmetric
about the cylinder centre plane, so half the cylinder is modelled).

Time-stepping model, not CFD: closed-cycle thermodynamics with a Wiebe heat release, Hohenberg wall heat
loss, port blow-down, a polytropic propane bounce chamber behind the piston, friction, and an
electromagnetic force law with a force limit. Two cycle-to-cycle controllers stand in for the engine
controller: the generator damping holds the inner dead centre (compression ratio), and the bounce-chamber
bleed valve (mean chamber pressure) holds the outer dead centre.

x = crown distance from the cylinder centre plane (m), positive outward.
"""
import math

R_AIR = 287.0
LHV = 46.35e6          # propane, J/kg
AFR_ST = 15.67


def simulate(P, cycles=140, dt=4e-6, trace=False):
    cycles = P.get('cycles', cycles)
    B, m = P["B"], P["m"]
    A = math.pi * B * B / 4
    x_po, h_p = P["x_po"], P["h_port"]            # port opening position, port height
    x_idc_t = P["x_idc"]                            # target inner dead centre (crown gap)
    x_odc_t = x_po + h_p                            # target outer dead centre (ports just fully open)
    p_s, T_tr = P["p_scav"], P["T_trap"]
    Qf = P["Q_fuel"]                                # fuel energy per cycle, this piston's half (J)
    F_pk, F_cont = P["F_pk"], P["F_cont"]
    Vb0 = P["Vb_idc"]                               # bounce-chamber gas volume at x = x_idc_t
    nb = P.get("n_bounce", 1.10)
    t_burn = P.get("t_burn", 1.5e-3)
    r_in = P.get("r_in", 1.0)                       # generator damping on the inward stroke / outward stroke
    k_ht = P.get("k_ht", 2.2)                       # wall heat-transfer multiplier on Hohenberg (conservative)
    x_s = P.get("x_spring", x_po)                   # electric spring acts outboard of this point
    k_e = P.get("k_e", 0.0)                         # electric spring rate (N/m)
    c = P.get("c0", 600.0)                          # generator damping (N s/m), controlled
    pb0 = P.get("pb0", 16e5)                        # bounce pressure at x_idc_t, controlled (bleed valve)
    T_wall = 480.0
    # start at ODC, ports open
    x, v = x_odc_t, 0.0
    p = p_s
    closed = False
    m_t = 0.0
    out = {}
    hist = []
    for cyc in range(cycles):
        t = 0.0
        E_mech = E_cu = Q_wall = W_gas = W_fric = W_bounce = 0.0
        F2 = 0.0
        x_min, x_max, p_max, v_max, Fem_max = 1e9, -1e9, 0.0, 0.0, 0.0
        pb_max, pb_min, pb_sum = 0.0, 1e9, 0.0
        burn_t0, burned = None, 0.0
        reached_idc = False
        tr = [] if (trace and cyc == cycles - 1) else None
        v_prev = v
        n_steps = 0
        while True:
            V = A * x
            # ---- cylinder gas
            if closed:
                T = p * V / (m_t * R_AIR)
                gam = 1.36 - 5.5e-5 * (T - 350.0)
                gam = max(1.24, min(1.37, gam))
                dQ = 0.0
                if burn_t0 is None and v < 0 and x <= P.get("x_ign", x_idc_t + 0.0012):
                    burn_t0 = t
                if burn_t0 is None and v_prev < 0 <= v:      # ignite at the turn-round at the latest
                    burn_t0 = t
                if burn_t0 is not None and burned < 1.0:
                    s = (t - burn_t0) / t_burn
                    nb_ = 1.0 - math.exp(-6.9 * min(max(s, 0.0), 1.2) ** 3.0)
                    dQ = (nb_ - burned) * Qf * 0.975
                    burned = nb_
                h = k_ht * 130.0 * (p / 1e5) ** 0.8 * T ** -0.4 * (2 * V) ** -0.06 * (P["v_mean_est"] + 1.4) ** 0.8
                A_w = A + math.pi * B * x
                dQw = h * A_w * (T - T_wall) * dt
                Q_wall += dQw
                dV = A * v * dt
                p += ((gam - 1.0) * (dQ - dQw) - gam * p * dV) / V
                if x >= x_po and v > 0:
                    closed = False
            else:
                p += -(p - p_s) / 4.0e-4 * dt
                if x < x_po and v < 0:
                    closed = True
                    p = p_s
                    m_t = p_s * V / (R_AIR * T_tr)
                    burn_t0, burned = None, 0.0
            # ---- bounce chamber (gas volume shrinks as the piston moves outward)
            Vb = Vb0 - A * (x - x_idc_t)
            pb = pb0 * (Vb0 / Vb) ** nb
            pb_eff = pb * (1.0 + 0.012 * (1 if v > 0 else -1))      # gas-spring hysteresis
            # ---- electromagnetic force
            F_em = -c * v * (1.0 if v > 0 else r_in)
            if x > x_s:
                F_em += -k_e * (x - x_s)
            F_em = max(-F_pk, min(F_pk, F_em))
            F_f = -(150.0 + 0.0035 * p * A) * (1 if v > 0 else -1)
            F = (p - pb_eff) * A + F_em + F_f
            v_prev = v
            v += F / m * dt
            x += v * dt
            t += dt
            n_steps += 1
            E_mech += -F_em * v * dt
            F2 += F_em * F_em * dt
            W_gas += p * A * v * dt
            W_fric += -F_f * v * dt
            pb_sum += pb
            if x < x_min: x_min = x
            if x > x_max: x_max = x
            if p > p_max: p_max = p
            if abs(v) > v_max: v_max = abs(v)
            if abs(F_em) > Fem_max: Fem_max = abs(F_em)
            if pb > pb_max: pb_max = pb
            if pb < pb_min: pb_min = pb
            if tr is not None and n_steps % 10 == 0:
                tr.append((t, x, v, p, pb, F_em))
            if v_prev < 0 <= v:
                reached_idc = True
            if reached_idc and v_prev > 0 >= v:       # back at the outer dead centre: cycle complete
                break
            if t > 0.25 or x <= 0.0005 or Vb <= 0.05 * Vb0:
                return dict(ok=False, why="stall" if t > 0.25 else ("crash_idc" if x <= 0.0005 else "crash_odc"),
                            cyc=cyc, c=c, pb0=pb0)
        f = 1.0 / t
        F_rms = math.sqrt(F2 / t)
        # controllers: generator damping holds the outer dead centre, the bleed valve (bounce pressure)
        # holds the inner dead centre / compression ratio
        e_o = x_max - x_odc_t                          # >0: over-travel -> take more out
        c *= max(0.90, min(1.10, 1.0 + 8.0 * e_o))
        c = max(20.0, min(c, 8000.0))
        e_i = x_min - x_idc_t                          # >0: under-compressing -> more bounce pressure
        pb0 *= max(0.96, min(1.04, 1.0 + 25.0 * e_i))
        pb0 = max(2e5, min(pb0, 60e5))
        hist.append((f, x_min, x_max, E_mech, c, pb0))
    cu = P["cu_frac"] * P["P_rated"] * (F_rms / F_cont) ** 2 / f      # J per cycle
    fe = P["fe_frac"] * E_mech
    E_el = E_mech - cu - fe
    V_tr = A * x_po
    cr = x_po / x_min
    out.update(ok=True, f=f, x_min=x_min, x_max=x_max, stroke=x_max - x_min, cr=cr, p_max=p_max,
               v_max=v_max, v_mean=2 * (x_max - x_min) * f, E_mech=E_mech, E_el=E_el, P_el=E_el * f,
               P_mech=E_mech * f, F_rms=F_rms, F_peak=Fem_max, Q_wall=Q_wall, W_gas=W_gas, W_fric=W_fric,
               eta_ind=W_gas / Qf, eta_el=E_el / Qf, wall_frac=Q_wall / Qf, c=c, pb0=pb0,
               pb_min=pb_min, pb_max=pb_max, pb_mean=pb_sum / n_steps, m_trap=m_t,
               imep=W_gas / (A * (x_max - x_min)), gen_eff=E_el / E_mech,
               conv=abs(hist[-1][1] - hist[-6][1]) + abs(hist[-1][2] - hist[-6][2]), trace=tr)
    lam = 0.90 * m_t / (Qf / LHV * AFR_ST)
    out["lam"] = lam
    return out
