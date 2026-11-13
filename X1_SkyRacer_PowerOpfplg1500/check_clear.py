"""Clearance check for routed pipes and the new gas path against the engine's solids, the skin and the wing root."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build'))
import x1_opfplg_blender as m

def seg_pts(pts, step=0.01):
    out = []
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); n = max(1, int(L / step))
        out += [tuple(a[k] + (b[k] - a[k]) * i / n for k in range(3)) for i in range(n)]
    return out + [pts[-1]]

def run(verbose=True):
    d, objs = m.build()
    zc, ys = d["zc"], d["cyl_y"]
    def solids(p):
        """Signed clearance (m) from point p to each solid; negative = inside."""
        x, y, z = p; out = {}
        ax = abs(x)
        # stator housings (round, x from h0 to END) and their flanges
        for k, yk in enumerate(ys):
            r = math.hypot(y - yk, z - zc)
            if d["h0"] - 0.008 <= ax <= d["END"]:
                out[f"housing cyl{k+1}"] = r - (d["flange_r"] if ax < d["h0"] or ax > d["END"] - d["t_cap"] - 0.010 else d["r_ho"])
        # block: chests (racetrack R = flange_r) and waist (R = Rb)
        R = d["flange_r"] if (x <= -d["xi0"] or x >= d["xe0"]) and ax <= d["blk_face"] else (d["Rb"] if ax < d["blk_face"] else None)
        if R is not None:
            if ys[0] <= y <= ys[2]: dr = abs(z - zc) - R
            else: dr = min(math.hypot(y - ys[0], z - zc), math.hypot(y - ys[2], z - zc)) - R
            out["block"] = dr
        # pack
        a0, a1 = m.ACC_TOP_BAY - m.ACC_H, m.ACC_TOP_BAY
        dx, dy, dz = ax - m.ACC_W / 2, max(m.ACC_Y0 - y, y - m.ACC_Y0 - m.ACC_L), max(a0 - z, z - a1)
        out["pack"] = max(dx, dy, dz)
        # charge air cooler and the deck
        cac = d["cac"]
        out["CAC"] = min(max(abs(x - cac["xc"]) - cac["hw"], cac["y0"] - y, y - cac["y1"], cac["zp0"] - z, z - cac["zh_r"]),   # plenums + core
                         max(cac["xr0"] - x, x - cac["xr1"], cac["y1"] - y, y - cac["ya"], cac["zr0"] - z, z - cac["zh_r"]))   # rear bay
        for nm_, c_, ax3, hh in d.get("boxes", []):                   # inverters, DC/DC, controller (oriented boxes)
            v_ = [p[k] - c_[k] for k in range(3)]
            q_ = [abs(sum(v_[k] * ax3[j][k] for k in range(3))) - hh[j] for j in range(3)]
            o_ = math.sqrt(sum(max(t, 0.0) ** 2 for t in q_))
            out[nm_] = min(out.get(nm_, 9), o_ if o_ > 0 else max(q_))
        # skin and wing root
        out["skin side"] = m.body_x(y, z) - ax
        out["belly"] = z - m.belly_z(y)
        out["skin top"] = m.body_ztop(x, y) - z
        wl = m.wing_low(y)
        if wl is not None and ax > 0.15: out["wing root"] = wl - z
        return out
    # turbo housings as vertex clouds
    turbo = [v for o in objs if o.name.startswith("OPF_ETurbo") and o.name != "OPF_ETurbo_Rotor" for v in o.mesh.v]
    routes = list(d["routes"])
    for o in objs:   # other pipe objects we care about, as rough polylines through their vertex centroids per ring
        pass
    report = []
    for name, pts, r in routes:
        worst = {}
        s0, s1 = {"charge riser": (0.075, 0.11), "exhaust outlet": (0.08, 0.08), "e-turbo HV feed": (0.0, 0.0),
                  "DC cross-link to the DC/DC": (0.0, 0.03)}.get(name, (0.0, 0.0))
        for p in seg_pts(pts):
            if math.dist(p, pts[0]) < s0 or math.dist(p, pts[-1]) < s1:   # ends sit in the parts they connect
                continue
            for k, v in solids(p).items():
                if k == "block" and name.startswith("exhaust manifold"):   # recessed into the block's open underside by design
                    continue
                if k in ("skin side", "belly", "skin top", "wing root"):
                    v = v - r
                else:
                    v = v - r
                worst[k] = min(worst.get(k, 9), v)
        tmin = min(math.dist(p, q) for p in seg_pts(pts[1:], 0.02) for q in turbo[::7]) - r
        if name not in ("exhaust outlet", "exhaust manifold behind the pack", "e-turbo HV feed"): worst["turbo"] = tmin
        report.append((name, worst))
    # routes against each other
    JOINTS = [{"DC bus L", "DC cross-link to the DC/DC"}, {"DC bus R", "DC cross-link to the DC/DC"},
              {"DC bus L", "e-turbo HV feed"}, {"exhaust manifold behind the pack", "exhaust outlet"}, {"exhaust manifold over the pack", "exhaust manifold behind the pack"}]
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            (n1, p1, r1), (n2, p2, r2) = routes[i], routes[j]
            if {n1, n2} in JOINTS:
                continue    # these lines are joined on purpose (bus tees)
            dmin = min(math.dist(a, b) for a in seg_pts(p1, 0.01) for b in seg_pts(p2, 0.01)) - r1 - r2
            if dmin < 0.03:
                report.append((f"{n1} vs {n2}", {"gap": dmin}))
    if verbose:
        for name, w in report:
            print(f"{name:32s} " + "  ".join(f"{k} {v*1000:+.0f}" for k, v in sorted(w.items(), key=lambda kv: kv[1])))
    return report

if __name__ == "__main__":
    run()
    d, objs = m.build()
    for nm in ("OPF_Aux_Liquid_Feed_L", "OPF_Aux_Liquid_Feed_R", "OPF_DCDC_Converter", "OPF_Control_Electronics_Placeholder", "OPF_Inverters", "OPF_Charge_Air_Cooler", "OPF_Exhaust_Manifold", "OPF_Charge_Air_Pipe"):
        o = [o for o in objs if o.name == nm][0]
        side = min(m.body_x(v[1], v[2]) - abs(v[0]) for v in o.mesh.v)
        bel = min(v[2] - m.belly_z(v[1]) for v in o.mesh.v)
        top = min(m.body_ztop(v[0], v[1]) - v[2] for v in o.mesh.v)
        print(f"{nm:28s} skin side {side*1000:+.0f} mm, belly {bel*1000:+.0f} mm, top {top*1000:+.0f} mm")
    a0 = m.ACC_TOP_BAY - m.ACC_H
    ys_ = [m.ACC_Y0 + m.ACC_L * k / 40 for k in range(41)]
    print("pack: bottom", round(a0, 3), "belly min", round(min(a0 - m.belly_z(y) for y in ys_) * 1000), "mm; side min",
          round(min(m.body_x(y, z) - m.ACC_W / 2 for y in ys_ for z in (a0, m.ACC_TOP_BAY)) * 1000), "mm",
          [ (round(z,3), round(min(m.body_x(y, z) for y in ys_),3)) for z in (a0, a0+0.05, m.ACC_TOP_BAY)])
