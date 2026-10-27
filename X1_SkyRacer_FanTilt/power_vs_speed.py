"""Run: python3 power_vs_speed.py  -> power_vs_speed.png and the summary table (fully loaded 3,500 lb).
Needs numpy + matplotlib. Each configuration sets pusher height, pusher tilt, duct cants and mean wing incidence."""
import warnings; warnings.filterwarnings("ignore")
import trim
from trim import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
INC_FINAL = trim.INC                                 # mean incidence of the branch model's wings
cfgs = [("Fans square, wings flat (cockpit25)", 0.90, 0, 0, 0, 0.0, "#888888", "-"),
        ("Pushers lowered 4 in at 20°, rear ducts 10°, wings flat", 0.80, 20, 0, 10, 0.0, "#c9a27a", "-"),
        ("Final: + wings at +5° to the rings (tips twist into the ducts)", 0.80, 20, 0, 10, INC_FINAL, "#CC5500", "-")]
sp = np.arange(0, 196, 5)
fig, ax = plt.subplots(figsize=(10, 5.6))
rows = []
for name, z, dp, dF, dR, inc, col, ls in cfgs:
    trim.rP = body(2.271, z); trim.INC = inc
    P = [(lambda r: r["P"] if r else np.nan)(best(max(v, 0.2) / MPH, dp, dF, dR)) for v in sp]
    ax.plot(sp, P, ls, color=col, lw=2.6 if "Final" in name else 2.0, label=name)
    a, b_ = best(100 / MPH, dp, dF, dR), best(150 / MPH, dp, dF, dR); h = best(0.1, 0, dF, dR)
    rows.append((name, a["P"], b_["P"], vmax(1500, dp, dF, dR) * MPH, vmax(K.P_BURST_HP, dp, dF, dR) * MPH, h["th"], b_))
ax.axhline(1500, color="k", lw=1); ax.text(60, 1515, "1,500 hp continuous", fontsize=9)
ax.axhline(K.P_BURST_HP, color="k", lw=1, ls=":"); ax.text(60, K.P_BURST_HP + 15, "1,913 hp burst (generator + LTO pack)", fontsize=9)
ax.set_xlabel("Airspeed (mph)"); ax.set_ylabel("Shaft power to fans (hp)"); ax.set_ylim(700, 2100); ax.set_xlim(0, 200)
ax.set_title("X1 SkyRacer, fully loaded 3,500 lb: trimmed power vs speed", loc="left")
ax.grid(alpha=.25); ax.legend(loc="upper left", fontsize=9.5, frameon=False, bbox_to_anchor=(0.01, 0.80))
for s in ("top", "right"): ax.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig("power_vs_speed.png", dpi=110)
for n, p1, p2, v1, v2, hp_, b_ in rows:
    print(f"{n:62s} {p1:5.0f} {p2:5.0f} {v1:4.0f} {v2:4.0f} hover {hp_:+.1f} | 150: th {b_['th']:+.1f} TF {b_['TF']:.0f} TR {b_['TR']:.0f} TP {b_['TP']:.0f} wing {b_['L']:.0f}")
