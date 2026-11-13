# X1 SkyRacer OPFPLG, 1,500 hp continuous, lightweight build

Opposed free-piston linear generator for the X1 SkyRacer, sized from a free-piston cycle model. Three cylinders
across the engine bay, six sodium-filled printed titanium pistons, propane DI, uniflow two-stroke. This is the
lightweight build from the Nov 2026 weight study; the first build (154 x 124 mm, copper windings, steel liners) is the previous commit.

| | |
|---|---|
| Bore x stroke | 150 x 124 mm per piston, 13.1 L swept |
| Pistons | one-piece printed titanium (Ti-6242), sodium-cooled crown, 14.0 kg moving mass each |
| Continuous point | 46.1 Hz, 11.4 m/s mean piston speed, 3.8 bar scavenge, lambda 1.85, 220 bar peak |
| Net to the DC link | 1,520 hp (1,133 kW) at 46.2 % fuel to DC |
| Burst, engine alone | about 1,970 hp at 244 bar peak |
| Generator | cobalt-iron cores, aluminium windings; 80 kPa rms air-gap shear (x1.06 on the 85 kPa yardstick), peak x1.44 |
| Engine mass estimate | about 497 kg: stators 262, moving parts 84, block, exhaust and casing 142, valves 9 |
| Package mass estimate | about 847 kg with air path, electronics, cooling and the LTO pack |
| Moving clearances | crowns 12.5 mm apart at the inner end; carrier disc 10.5 mm from the liner end there and 16 mm from the end cap at the outer end |

Each piston carries a magnet sleeve folded back over the outside of its liner, with stators on both faces. The
outer stator stops 60 % of the stroke short of the outer dead centre, where little generating force is needed.
The sealed volume behind each piston is its own propane circuit: check valve in, spray lance up the hollow
tail onto the crown, bleed valve out to its own condenser sector behind a pusher fan. The bleed valve sets the
chamber pressure, which sets the boiling temperature and the bounce force together.

Printed sodium-cooled pistons (Nov 2026 thermodynamic check): each piston is ONE printed titanium piece (Ti-6242):
a 1.8 mm gas plate held by printed pillars at 8 mm pitch, a sealed half-filled sodium gallery under it, a 75 mm
jacket down the inside of the skirt, and the skirt itself. It is printed hollow with a port, drained of powder,
filled with sodium under argon (133 g) and closed with a welded plug. The sodium shakes between crown and jacket
and spreads the crown heat, 16.5 kW or about 0.93 MW/m2 on the gas face, over a finned wall where the propane sees
about 0.24 MW/m2, x1.7 under its estimated boiling limit of 0.41 MW/m2. Titanium's poor conduction keeps the
jacket's sodium side at about 139 C, 41 K above sodium's freezing point. The gas face runs near 391 C against an
alloy limit of about 540 C; the plate sees roughly 76 MPa in bending at peak pressure. Against the spray-cooled
steel crown: moving mass 14.0 kg (was 14.7), 46.1 Hz (44.9), 46.2 % fuel to DC (45.8), heat per piston circuit
52 kW (59), peak 220 bar (225), stator margin x1.06 (x1.03).

The engine is built round ONE metal-printed aluminium centre block, about 276 mm wide, 1,108 mm long and 364 mm
tall: a slim waist round the combustion zones, an air chest round the three intake port rings and an exhaust
housing round the exhaust port rings. The waist holds the coated bores (20 mm combustion band), the injector bosses
and a propane cooling gallery in each bore wall, one half per piston circuit, carried out to the port bridges in a
thick printed sleeve. The six stator assemblies (4.5 mm housing, both stators, liner extension, end cap) bolt to
the block's two faces with 16 x M8 each.

Ports are on arcs, not all the way round: 12 ports per ring on a 270 degree arc, 80 % open. Exhaust ports are
centred on straight down, intake ports on straight up (under the charge air cooler). Port heights are unchanged, so
the timing is unchanged, and the open area is the same as the old all-round rings: 96 cm2 exhaust and 74 cm2 intake
per piston. A strict 180 degree half cannot hold that area at the same height, so the arc is 270 degrees; the
price is narrower bridges, 5.9 mm against 11.8 mm, with 24 mm wide ports.

Exhaust is kept apart from the stator assemblies. The block has a closing wall on its exhaust face, so the stators
bolt to aluminium and never see exhaust gas. Each bore carries a printed steel exhaust-port insert (ports and
bridges, propane gallery behind it). The exhaust housing's underside is open between its end wall and the closing
wall, so the manifold attaches right under the bores: a short stainless collector wraps each ported arc and opens
straight down through a 64 x 204 mm flange (131 cm2, 1.4 times the port area) 110 mm below the bore axis, 21 mm
under the port insert. It used to be 186 mm below the axis, on the block's underside. All 16 bolts of each
exhaust-side stator assembly are kept; the lowest four sit beside the manifold in bosses on the closing wall.

The manifold is one stainless piece bolted to the three flanges. Its upper part (64 x 70 mm) sits up inside the
block. A lower part hangs below the block and grows as each cylinder joins: none after cylinder 1, 142 x 38 mm by
the pack's rear end where cylinder 2 feeds in, 110 x 50 mm behind the pack, 130 x 74 mm after cylinder 3. Behind
the block it turns round and rises into the bottom of the turbine volute. The LTO pack is lowered 55 mm (belly
skin 61 mm below it, side skin 23 mm from its lower edges); the manifold clears its lid by 51 mm after cylinder 1
and by 23 mm over the last 190 mm of the pack, behind a double radiant shield. Stainless (321 or an HK30 type) is
the starting point at about 520 C mean gas temperature. Wall and bolt sizes are rule of thumb, not stress analysis.

Gas path: the compressor rises behind the block into a hot plenum on top of a stacked charge air cooler in the
spine. The cooler now runs the full length of all three cylinders: the air passes straight down through a wide, shallow
core (1,033 x 236 mm, 60 mm deep in the flow) into a cold plenum sitting on the block, which drains through its floor into the air chest along its whole length. The
exhaust leaves through the manifold under the block into the bottom of the turbine volute. The cold plenum is a narrow neck on the air-chest side
(148 mm wide) that flares out under a 248 mm wide core and a rounded, ribbed hot tank. The wide part sits above
the block's exhaust side, 28 mm clear at the closest point, and a formed double-skin heat shield follows the underside,
16 mm off the chest. Sized for
velocity at the continuous point (see GAS PATH in the fit report):

| Passage | Mean velocity | Target |
|---|---|---|
| Charge riser (hot) | 51 m/s | 60 |
| Hot plenum where the riser comes in (entry bay now 220 mm wide) | 25 m/s | 45 |
| Cooler core face, air passing straight down | 3 m/s | 8 |
| Cold plenum toward the air chest / floor opening | 7 / 6 m/s | 25 |
| Air chest round each bore | 15 m/s | 40 |
| Intake / exhaust ports while open | 53 / 95 m/s | 100 / 150 |
| Flange opening under the bore while the ports are open | 70 m/s | 150 |
| Manifold after cylinder 1 / at the pack's rear end / behind the pack / after cylinder 3 | 87 / 90 / 89 / 95 m/s | 95 |
| Exhaust outlet / turbine inlet (bottom of the volute) | 94 / 100 m/s | 95 / 110 |
| Downpipe, now 244 mm | 69 m/s | 70 |

The rough core loss is about 0.1 kPa. The first build ran its port belts at about 150 m/s (intake) and 290 m/s
(exhaust), its cooler at 31 m/s through a 600 mm core and its downpipe at 100 m/s. The engine and the LTO pack are
at their original heights. `check_clear.py` checks the routed pipes against the block, housings, cooler, turbo,
pack, inverters, DC/DC, controller, skin and wing root; the tightest gaps are behind the block, where the riser passes 6 to 12 mm from
the intake stator housing, the block, the turbo and the rear wing root.

Power electronics: a SiC inverter sits on top of each stator housing (six, one per stator set), in a saddle that
makes the housing wall its cold plate, so the boiling propane in the chamber below (63 to 71 C) cools it and its
heat (about 2.9 kW) goes into that piston's circuit. All six are mounted the same way, turned 40 degrees forward of the top; on
cylinder 3 that clears the rear wing root (19 mm to the estimated lower surface). A 900 V bus runs along each side over the housings, joined in
front of cylinder 1 and taken to the DC/DC beside the LTO pack (15 mm from the side skin); the controller
placeholder sits on the other side of the pack, and the e-turbo joins the +x bus at the rear. The DC/DC, controller
and charge air cooler share the two auxiliary propane circuits. The old electronics deck is gone.

Two-stage charge cooling: the top half of the cooler core is a hot stage that takes the air from 212 C to 110 C on
its own two propane circuits condensing at 82 C; the bottom half is the cold stage (110 C to 62 C) on the two
auxiliary circuits at 59 C. Each pusher condenser now has five sectors sized by heat and temperature: three piston
circuits at 67 degrees each (52 kW each, 66 C), the hot stage at 84 degrees (95 kW) and the auxiliary circuit at
76 degrees (48 kW). Before, one auxiliary sector took 171 degrees, nearly half the annulus, because all the charge
heat left at 59 C. Fin area needed per pusher on a 35 C day falls from 58 to 45 m2 against 56 m2 available. The
hot-stage vapour and liquid lines run above the cold-stage vapour line beside the cooler's entry section.

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

- The stators run at 80 kPa, x1.06 on the 85 kPa continuous yardstick (the first build had x1.19). More margin costs mass.
- 220 bar in a printed aluminium bore needs fatigue testing; a thin steel sleeve adds about 5 kg per cylinder.
- About 600 kW of heat has to leave through the two pusher ducts. With two-stage charge cooling the finned
  condenser covers a 35 C day with about 20 % in hand; hover at full power is not covered. The hot stage runs
  propane at about 32 bar and 82 C, close to its critical point (97 C), where latent heat is low.
- The centre block is over a metre long, so it needs a large-format metal printer. Its cooling channel sizes,
  wall temperatures and the chest walls under boost and exhaust pressure are not analysed yet.
- Sodium crowns: the shaking heat-transfer rate (20 kW/m2 K), the x1.6 fin gain and the propane boiling limit are
  estimates. The thin gas plate and pillars in fatigue, the plug weld, galling of the titanium skirt in the aluminium
  bore, sodium frozen at start-up and a crack into the cylinder are not assessed.
- Charge air cooler thermal size: the 14.6 L two-stage core gives about 78 C charge air at the assumed fin
  density, not the 62 C the cycle assumes (flagged CHECK in the fit report). It needs roughly twice the core.
- The exhaust manifold passes 23 mm over the LTO pack lid behind a double shield. Heat into the pack (LTO cells want
  to stay under about 55 C) and into the aluminium round the collectors is not modelled.
- The exhaust housing's underside is open so the manifold can sit up inside the block. That leaves the exhaust-side
  stator flanges tied to the block by the upper wall, the end wall and the closing wall only; not stress-checked.
  Collector supports, flange seals and the manifold's thermal growth along the block are not designed.
- Port bridges are 5.9 mm (were 11.8 mm) because the ports now sit on 270 degree arcs. Bridge cooling and ring
  support over 24 mm ports are not checked. With ports on one side the scavenge flow is no longer symmetric; the
  cycle model does not see that.
- The cooler's thermal size and the gas-path pressure losses beyond the core are not modelled, only velocities.
  The corner behind the block is tight (6 to 12 mm gaps round the riser).
- The downpipe is 244 mm across where it leaves the fuselage (was 200 mm); the SkyRacer model picks this up.
- At about 847 kg the package is still about 246 kg over the airframe's 1,325 lb budget for generator plus pack.
- Cobalt-iron tooth and yoke sizes, aluminium slot fill and core loss are estimates, not an electromagnetic model.
- Wing-root clearance uses an estimated lower surface; check it in the airframe model. The cylinder 3 inverters
  (19 mm) and the charge riser (11 mm) are the closest.
- 63 to 71 C coolant is warm for SiC inverters; vibration and heat soak from the block on the housing-mounted
  inverters are not assessed.
