# X1 SkyRacer OPFPLG, 1,500 hp continuous, lightweight build

Opposed free-piston linear generator for the X1 SkyRacer, sized from a free-piston cycle model. Three cylinders
across the engine bay, six pistons, propane DI, uniflow two-stroke. This is the lightweight build from the
Nov 2026 weight study; the first build (154 x 124 mm, copper windings, steel liners) is the previous commit.

| | |
|---|---|
| Bore x stroke | 150 x 124 mm per piston, 13.1 L swept |
| Continuous point | 44.9 Hz, 11.1 m/s mean piston speed, 3.8 bar scavenge, lambda 1.79, 225 bar peak |
| Net to the DC link | 1,519 hp (1,132 kW) at 45.8 % fuel to DC |
| Burst, engine alone | about 1,900 hp at 247 bar peak |
| Generator | cobalt-iron cores, aluminium windings; 82 kPa rms air-gap shear (x1.03 on the 85 kPa yardstick), peak x1.40 |
| Engine mass estimate | about 472 kg: stators 262, moving parts 88, printed block and casing 113, valves 9 |
| Package mass estimate | about 823 kg with air path, electronics, cooling and the LTO pack |
| Moving clearances | crowns 12.5 mm apart at the inner end; carrier disc 10.5 mm from the liner end there and 16 mm from the end cap at the outer end |

Each piston carries a magnet sleeve folded back over the outside of its liner, with stators on both faces. The
outer stator stops 60 % of the stroke short of the outer dead centre, where little generating force is needed.
The sealed volume behind each piston is its own propane circuit: check valve in, spray lance up the hollow
tail onto the crown, bleed valve out to its own condenser sector behind a pusher fan. The bleed valve sets the
chamber pressure, which sets the boiling temperature and the bounce force together.

The engine is built round ONE metal-printed aluminium centre block, about 276 mm wide, 1,108 mm long and 364 mm
tall. It holds the three coated bores (20 mm combustion band, 6 mm elsewhere), the intake and exhaust port
galleries, the injector bosses and, printed into each bore wall, a propane cooling gallery right through the
combustion zone. Each half of a gallery is on that piston's own circuit: liquid from the check valve goes through
the block first, then into the chamber. The intake plenum and exhaust collector are printed onto the block top.
Each side of the block is a bolt face. The six stator assemblies (4.5 mm housing, both stators, liner extension,
end cap) bolt on with 16 x M8 each. Wall and bolt sizes are rule of thumb, not stress analysis.

A 140 x 142 mm long-stroke layout was tried first and dropped: within the bay width its carrier disc ran into the
liner end at the inner dead centre. The script now checks every moving clearance and reports INTERFERENCE.
A charge air cooler sits in the spine over the engine, and the inverters, DC/DC and a placeholder control box
sit on a deck ahead of the rear wing. The LTO pack under the engine is unchanged.

Behind each pusher fan, the condenser is a pack of thin cambered fins with no thick vanes: about 20 degrees at the
leading edge against the rotor swirl, axial at the trailing edge, evenly spaced all the way round. With the
concentric splitter rings they straighten the flow and carry the hub; the propane runs in the rings.

Concept and design stage only. All numbers are sizing estimates.

## Files

- `x1_opfplg_blender.py`: the model. In Blender 3.6 or 4.x: Scripting, New, paste, Run Script. In plain
  Python it writes an OBJ, previews and the fit report. Pistons are keyframed from the cycle model's motion table.
- `fit_report_1500hp.txt`: sizing, energy balance, cooling and fit.
- `X1_OPFPLG_1500hp.glb`: the model with a one-cycle animation.
- `viewer/`: the 3D viewer page. Serve the folder; it loads its data files by relative path.
- `opf_cycle.py`: the free-piston cycle model (Wiebe heat release, wall heat loss, polytropic propane bounce
  chamber, force-limited generator, dead-centre controllers).
- `tune_cycle.py`, `cycle.json`, `trace.json`: the tuned continuous point and the one-cycle trace. The `CYCLE`
  block in `x1_opfplg_blender.py` holds the same values as `cycle.json`.
- `export_web.py`: rebuilds the `viewer/` data and the GLB from the script.
- `preview_*.png`: plain-Python previews.

## Open issues

- The stators run at 82 kPa, x1.03 on the 85 kPa continuous yardstick (the first build had x1.19). More margin costs mass.
- 225 bar in a printed aluminium bore needs fatigue testing; a thin steel sleeve adds about 5 kg per cylinder.
- About 640 kW of heat has to leave through the two pusher ducts. The finned condenser covers a 15 C day and
  is short on a 35 C day; hover at full power is not covered.
- The centre block is over a metre long, so it needs a large-format metal printer. Its cooling channel sizes and
  wall temperatures are not modelled yet.
- At about 823 kg the package is still about 220 kg over the airframe's 1,325 lb budget for generator plus pack.
- Cobalt-iron tooth and yoke sizes, aluminium slot fill and core loss are estimates, not an electromagnetic model.
- Wing-root clearance uses an estimated lower surface; check it in the airframe model.
