"""Plot power_map_sweep.json: net DC-bus power vs manifold pressure and vs settled piston frequency.
Writes power_map.png next to this script."""
import json, sys, os, numpy as np, matplotlib
HERE = os.path.dirname(os.path.abspath(__file__))
matplotlib.use("Agg")
import matplotlib.pyplot as plt
rows = [r for r in json.load(open(os.path.join(HERE, "power_map_sweep.json"))) if r["ok"]]
INK, INK2, SURF, GRID = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
SER = {1.6: "#2a78d6", 1.85: "#eb6834", 2.2: "#1baf7a", 2.7: "#eda100"}
NAME = {1.6: "λ 1.60  (burst fuelling)", 1.85: "λ 1.85  (continuous setting)", 2.2: "λ 2.20", 2.7: "λ 2.70  (lean, part load)"}
P_LIM = 244.0
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "figure.facecolor": SURF, "axes.facecolor": SURF})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(15.5, 6.8), sharey=True)
def seg_plot(ax, xs, ys, ok_cont, ok_p, color, label):
    # solid: within the generator's continuous rating; dashed: burst only; dotted: over the 244 bar peak-pressure limit
    for i in range(len(xs) - 1):
        if not (ok_p[i] and ok_p[i + 1]): st, lw = ":", 1.6
        elif ok_cont[i] and ok_cont[i + 1]: st, lw = "-", 2.2
        else: st, lw = "--", 2.0
        ax.plot(xs[i:i + 2], ys[i:i + 2], color=color, ls=st, lw=lw, solid_capstyle="round")
    ax.plot([], [], color=color, lw=2.2, label=label)
for lam in (1.6, 1.85, 2.2, 2.7):
    rr = sorted([r for r in rows if r["lam"] == lam], key=lambda r: r["p"])
    p = [r["p"] for r in rr]; hp = [r["hp"] for r in rr]; f = [r["f"] * 60 for r in rr]
    okc = [r["cont_margin"] >= 1.0 for r in rr]; okp = [r["pmax"] <= P_LIM for r in rr]
    seg_plot(a1, p, hp, okc, okp, SER[lam], NAME[lam])
    seg_plot(a2, f, hp, okc, okp, SER[lam], NAME[lam])
    a2.text(f[-1] + 25, hp[-1], f"λ {lam:g}", fontsize=9, color=INK2, va="center")
for ax in (a1, a2):
    for y, t in ((1500, "1,500 hp continuous"), (2000, "2,000 hp burst")):
        ax.axhline(y, color=INK2, lw=0.8, ls=(0, (4, 3)))
        ax.text(ax.get_xlim()[0] if False else 0.01, y + 25, t, transform=ax.get_yaxis_transform(), fontsize=8.5, color=INK2)
    ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
# operating points from the engine's own cycle file
cont = (3.8, 1518, 46.09); burst = (4.1, 1973, 48.83)
for ax, xi in ((a1, 0), (a2, 2)):
    for pt, lab, dy in ((cont, "continuous: 3.8 bar, λ 1.85, 46.1 Hz, 220 bar", -26), (burst, "burst: 4.1 bar, λ 1.60, 48.8 Hz, 244 bar", 16)):
        x = pt[xi] * (60 if xi == 2 else 1)
        ax.plot(x, pt[1], "o", ms=9, mfc=SURF, mec=INK, mew=2, zorder=5)
        ax.annotate(lab, (x, pt[1]), xytext=(-12, dy), textcoords="offset points", ha="right", fontsize=8.5, color=INK,
                    bbox=dict(boxstyle="round,pad=0.25", fc=SURF, ec="none", alpha=0.9))
a1.set_xlabel("Intake manifold (scavenge) pressure, bar absolute")
a1.set_ylabel("Net power to the DC bus, hp")
a1.set_title("Power vs manifold pressure", loc="left", fontsize=12, color=INK, pad=10)
a2.set_xlabel("Piston frequency, cycles per minute (Hz × 60)  -  the free-piston stand-in for rpm")
a2.set_title("Power vs the frequency the engine settles at", loc="left", fontsize=12, color=INK, pad=10)
sec = a2.secondary_xaxis("top", functions=(lambda c: c / 60, lambda h: h * 60))
sec.set_xlabel("Hz", color=INK2); sec.tick_params(colors=INK2); sec.spines["top"].set_visible(False)
a1.set_ylim(250, 2500)
from matplotlib.lines import Line2D
h, l = a1.get_legend_handles_labels()
h += [Line2D([], [], color=INK2, lw=2.2), Line2D([], [], color=INK2, lw=2.0, ls="--"), Line2D([], [], color=INK2, lw=1.6, ls=":")]
l += ["within generator continuous rating", "burst only (over continuous rating)", "over the 244 bar peak-pressure limit"]
a1.legend(h, l, frameon=False, loc="lower right", fontsize=8.8)
fig.text(0.01, 0.012, "From the 1,500 hp build's own cycle model (opf_cycle.py / tune_cycle.py via power_map_sweep.py): 150 x 124 mm, 13.1 L, 14.0 kg pistons, "
         "CR held at 16 by the controller,\n380 K trapped charge. Frequency is an output, not an input: it is set by piston mass, gas pressures and generator load.",
         fontsize=8, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(os.path.join(HERE, "power_map.png"), dpi=130)
