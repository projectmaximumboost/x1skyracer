"""Power map for the 1,500 hp OPFPLG: sweep intake manifold (scavenge) pressure and fuelling through this
folder's cycle model and record the frequency each point settles at. Writes power_map_sweep.json.
Run from anywhere: python3 power_map_sweep.py   (then python3 power_map_plot.py)"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x1_opfplg_blender as m, tune_cycle as tc
d = m.design()
out = []
lams = [1.6, 1.85, 2.2, 2.7]
ps = [x / 10 for x in range(20, 47, 2)]
for lam in lams:
    for p in ps:
        P, r = tc.run(m, d, lam=lam, p_s=p * 1e5, T_crown=665.2 + (1.85 - lam) * 60)
        if not r["ok"]:
            out.append(dict(lam=lam, p=p, ok=False, why=r.get("why"))); print(lam, p, "FAIL", r.get("why")); continue
        cyc = tc.pack(d, P, r); m.CYCLE.clear(); m.CYCLE.update(cyc)
        pf = m.performance(d)
        row = dict(lam=lam, p=p, ok=True, f=r["f"], hp=pf["net_hp"], eta=pf["eta"], pmax=r["p_max"] / 1e5,
                   stroke=r["stroke"], cr=r["cr"], conv=r["conv"], peak_margin=pf.get("peak_margin"), cont_margin=pf.get("cont_margin"),
                   turbo_kw=pf.get("turbo_kw"), sig_pk=r.get("sig_pk"), sig_rms=r.get("sig_rms"))
        out.append(row)
        print(f"lam {lam:4.2f} p {p:3.1f}: f {r['f']:5.2f} Hz  {pf['net_hp']:5.0f} hp  eta {pf['eta']:.3f}  pmax {r['p_max']/1e5:4.0f} bar  cr {r['cr']:.1f}  conv {r['conv']*1e3:.2f} mm  margins {pf.get('cont_margin')}/{pf.get('peak_margin')}")
json.dump(out, open(os.path.join(HERE, "power_map_sweep.json"), "w"), indent=1)
