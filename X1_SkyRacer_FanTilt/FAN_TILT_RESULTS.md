# X1 SkyRacer fan-tilt study (branch `fan-tilt`, from `cockpit25`)

**Latest (27 Oct 2026):** the rear wing's folding panel is back to full thickness (10 %, was 5.5 %) for strength, with the hinges and heights re-solved. See "Thicker rear wing" at the end; it supersedes some figures in the sections before it.

Earlier: the engine and accumulator were made 3.9 in lower and the belly is deepened under the engine bay, so the lowered rear wing clears the engine by 2.8 in. See "Engine lowered, belly tub" at the end.

Before that, the wings were given real fold hinges, with no parts passing through each other: folded 89.5 × 52.9 in (see "Real fold hinges"). The rear wing is 4.7 in lower, and its outer panel and the rear duct lips changed. Trim: 1,023 hp at 150 mph, 178 / 193 mph.

Earlier the same day the pushers became 0.39 m deep and tilted 10°, not 20°: 1,018 hp at 150 mph, 178 / 193 mph (see "Pusher depth and tilt"). The sections before that one use the earlier flight-sim kit model.

The final setting (pushers 4 in lower at 20°, rear lift ducts canted 10° forward, wings at +5° all the
way to the ducts) cuts power at 150 mph from 1,633 hp to 1,163 hp for the fully loaded 3,500 lb craft.
Top speed rises from 141 to 173 mph on 1,500 hp continuous and from 162 to 192 mph on the 1,913 hp
burst. The craft hovers and lands 6.2° nose-up.

## Fully loaded craft (race configuration, rule 3.3)

| Item | Value |
| --- | --- |
| Weight | 3,500 lb = 2,800 lb dry (kit mass items, 9.852 % lightweighting) + 200 lb propane + 500 lb ballast |
| Ballast | 250 lb per seat at (±0.30, −0.865, 0.616) m, cockpit25 seats |
| CG (model m) | y = +0.168 (aft of the duct midpoint), z = 0.722 |
| Hover split, fans square | front ducts 1,338 lbf, rear ducts 2,162 lbf (62 % rear); 1,066 hp |

## Settings in this branch (x1_skyracer_blender.py)

| Setting | Before | Now |
| --- | --- | --- |
| `PUSHER_Z` (pusher centre height) | 0.90 m | 0.80 m (4 in lower) |
| `PUSHER_TILT_DEG` (exhaust below body axis) | 0° | 20° |
| `LIFT_CANT_F_DEG` (front ducts, thrust forward) | 0° | 0° |
| `LIFT_CANT_R_DEG` (rear ducts, thrust forward) | 0° | 10° |
| `WING_INCIDENCE_DEG` (leading edge up, about mid-chord) | 0° | 5° |
| `RW_HX` (rear wing fold hinge, outboard from centre) | 0.870 m | 0.875 m (5 mm outboard) |

How the wings meet the rings: every wing tip meets its duct ring in the ring's own plane, exactly as
in the original design (tips within about 1 in of the ring mid-plane, inside the 5 in ring wall).

- Both wings, folding panels included, run at +5° from the body to the duct ring.
- Only the tip fillet, where the wing curves into the ring, twists: to 0° at the square front ducts
  and to −10° at the canted rear ducts. The fillets fold with the ducts.
- The +5° rear folding panel pushed the folded height 2 mm over 53 in. Moving the rear fold hinge
  5 mm outboard makes the folded panel hang steeper (74.7° instead of 70.4°), which lowers its top and
  pulls each folded rear duct about 0.5 in inboard. The folded rear ducts sit 4.3 in from the body
  (8.7 in before).

The pusher heat exchangers and the ends of the propane lines move and tilt with the pushers.
All X1 Racing dimension rules pass: folded 86.4 × 52.9 × 215.8 in (limits 90 × 53 × 216 in);
nothing intrudes into the body, pushers or sponsons when folded.

## Trimmed power, fully loaded

| Configuration | hp at 100 mph | hp at 150 mph | V max, 1,500 hp | V max, 1,913 hp | Hover pitch |
| --- | --- | --- | --- | --- | --- |
| Fans square, wings flat (cockpit25) | 1,194 | 1,633 | 141 mph | 162 mph | 0° |
| Pushers lowered 4 in at 20°, rear ducts 10°, wings flat | 983 | 1,320 | 162 mph | 181 mph | 6.2° nose up |
| **+ wings at +5° to the ducts (this branch)** | **887** | **1,163** | **173 mph** | **192 mph** | **6.2° nose up** |

At 150 mph in the final setting the body flies 3.2° nose-down (wings at +1.8°), the wings carry about
800 lbf, the front / rear ducts carry 1,136 / 1,380 lbf and the pushers deliver 772 lbf, well under
their 1,200 lbf cap.

## How the settings were chosen

- **Pusher tilt:** with the ducts square, 0° → 25° tilt gives 141, 144, 147, 148, 149, 149 mph on
  1,500 hp. Tilted, the pushers lift the tail and unload the rear ducts (62 % of the hover load
  because the CG is aft); duct power grows as thrust^1.5, so even loads save power. With the rear cant
  in, 20° is 11 hp better than 15° at 150 mph; 25° adds nothing more.
- **Pusher height:** 0.90 to 0.75 m changes power by under 3 hp, so the pushers were lowered 4 in
  for a sleeker tail. That also keeps the 20° tilted duct under the 53 in folded limit.
- **Duct cant vs wing incidence:** both fix the same problem. With everything square the craft must
  pitch nose-down to use the ducts for thrust, which drives the wings negative. Cant tilts the ducts
  instead; incidence tilts the wings instead. Wing incidence alone keeps the hover level; the rear
  cant adds speed at the cost of a nose-up hover. Front ducts cannot be canted: even 3° toes the
  folded ducts into the nose.

| Option (pushers 4 in lower at 20°) | hp at 150 mph | V max, 1,500 / 1,913 hp | Hover pitch |
| --- | --- | --- | --- |
| Fans square, wings +5° | 1,319 | 161 / 180 mph | level |
| Fans square, wings +7° | 1,264 | 166 / 185 mph | level |
| Wings +5°, rear ducts 5° | 1,244 | 168 / 187 mph | 3.2° |
| **Wings +5°, rear ducts 10° (built)** | **1,163** | **173 / 192 mph** | **6.2°** |
| Wings twisted to 0° over the outer span (first build of this step), rear ducts 10° | 1,198 | 170 / 190 mph | 6.2° |

## Things to know

- **Nose-up hover:** the craft hovers and lands 6.2° nose-up. This is by design: the rear fans need little or no thrust at the start, the front fans lift first to tilt the nose up, and then the whole craft climbs. The tail drops about 0.28 m relative to level as it rotates and still clears the ground.
- **Pusher exhaust** now points 20° down; the lowest aft corner of each pusher duct sits about
  0.35 m off the ground.
- **Flight-model kit not yet updated:** its pusher axes, rear-duct axes, pusher position, wing
  incidence and ballast seats are still the original values.

## Model and limits

Same models as the PteroSim / JSBSim kit: kit aero tables (CL = 0.25 + 3.5 α, CdA 1.80 m², Cm = −0.3 α,
with α taken at the wings: body pitch + 5° incidence), kit lift-duct power (hover momentum theory,
FM 0.75, duct gain 1.13, coax loss 1.12) at all speeds, kit pusher power (momentum theory with inflow),
1,000 lbf per lift fan and 600 lbf per pusher caps, sea level. Level flight, longitudinal trim (forces
and pitch moment balanced), minimum-power pitch chosen at each speed.

- Lift-duct power ignores forward-flight effects: edgewise inflow lowers induced power, duct momentum
  drag raises drag. The two partly cancel; flight test or CFD would settle it.
- The kit aero tables are estimates, not test data, and lump body and wings together.
- Earlier figures of 150 mph cruise and 187 mph top speed came from a different power model; this
  study uses the kit's. Compare configurations rather than reading the absolute speeds.

## Files

- `../x1_skyracer_blender.py`: branch model; builds as X1_SkyRacer_FanTilt.*
- `mass.py`, `trim.py`, `power_vs_speed.py`: the analysis (run `python3 power_vs_speed.py` here)
- `power_vs_speed.png`, `tail_compare.png`, `tail_side.png`, `folded.png`
- `rear_hinge_trim.py`: trim cost of the real-hinge rear wing
- `engine_bay.png`: centreline section before / after lowering the engine
- `spine_louvres.png`: the spine intake louvres bent to the crown

## Pusher depth and tilt (27 Oct 2026)

Each pusher duct is now 0.39 m deep instead of 0.50 m (length / bore 0.59): 9 cm of inlet ahead of the
fan, ending 2 cm behind the heat-exchanger rings. The fan, the heat exchangers and their spacing are
unchanged. The tilt was re-optimised with a momentum pusher model: air enters along the flight path and
leaves along the duct axis, so a tilted duct pays for turning the flow (the kit model ignored this and
favoured large tilts). Model: split front / rear wings (5° / 5°, a quarter of the standard front-wing
downwash on the rear wing), forward-flight lift ducts with propulsive work, rear ducts canted 10°.

| Pusher tilt (exhaust down) | hp at 150 mph | V max, 1,500 / 1,913 hp | Body pitch at 150 mph |
| --- | --- | --- | --- |
| 0° | 1,067 | 176 / 191 mph | +2.0° |
| 5° | 1,031 | 178 / 192 mph | +1.0° |
| **10° (built)** | **1,018** | **178 / 193 mph** | **−0.3°** |
| 15° | 1,027 | 177 / 191 mph | −1.8° |
| 20° (previous) | 1,056 | 173 / 188 mph | −3.5° |

Shortening the ducts saves about 2 hp at 150 mph (less duct skin); the tilt change is worth about
40 hp and 5 mph. At 10° the body flies almost level at 150 mph and the front / rear duct loads are
nearly even (937 / 1,087 lbf). Hover with the pushers idling for cooling stays 7.1° nose-up. All X1
Racing dimension rules pass and the fold is unchanged (86.4 × 52.9 in).

## Real fold hinges (27 Oct 2026)

The earlier fold only fitted the 90 in hauler width because folded panels passed through each other.
Every fold hinge now sits on the skin on the inside of its fold, so the panels open apart:

- **Front wing:** lower skin.
- **Front duct:** upper skin.
- **Rear wing:** upper skin.
- **Rear duct:** lower skin.

Folded: 89.5 × 52.9 in (limits 90 × 53 in). Checked with the folded panels held apart:

- no part of a folded duct, rotor or fillet enters its folded wing panel;
- nothing touches the body, pushers, sponsons or pylons;
- all other X1 Racing rules and the cockpit fit pass.

| Fold | Hinge | Fold angle |
| --- | --- | --- |
| Front wing | lower skin, 0.70 m from the centreline (was 0.64 m) | 84° down |
| Front duct | upper skin at the ring | 174° |
| Rear wing | upper skin, 0.82 m from the centreline (was 0.875 m) | 90° up (panel vertical) |
| Rear duct | lower skin at the ring, axis in the duct ring's plane | 180° (hangs beside the panel) |

### What changed at the rear, and why

1. **Rear wing 4.7 in lower** (`DUCT_ZR` 1.12 → 1.00 m, ducts with it). With a 90° fold the duct hangs
   from the top of the standing panel, so the wing height sets the folded height.
2. **Thinner, twisted outer panel.**
   - Thickness eases from 9 % at the stub to 5.5 % on the folding panel (`REAR_PANEL_TR`). The panel
     thickness is the step between the two rear hinges, so this narrows the fold.
   - The panel twists from 0° at the fold line to −10° at the duct: the duct ring's own plane, so the
     duct hinge axis runs in that plane along the whole chord.
   - A hinge on the upper skin along Y needs an untwisted section at the fold line, so the stub eases
     to 0° there.
3. **Stub incidence +9°** (`REAR_STUB_INC_DEG`, was +5°). This makes up the lift of the twisted outer
   panel: the rear wing's chord-weighted mean is 4.6°, against 5° before.
4. **Rear duct sits 2.2 in higher on the wing tip** (`REAR_DUCT_RAISE` 0.055 m, along the ring axis).
   A 180° fold puts anything below the hinge plane inside the folded panel. The 17-blade lower rotor
   sat below that plane at the front-inboard side of the canted duct.
5. **Lip trim (scallop).** The ring's inboard lower lip, and the fillet under it, are trimmed flat
   just above the hinge plane where the folded panel lies against them. The trim is longest on the
   front-inboard arc and blends out at the ends. Each rear duct keeps at least 4 mm clear of the panel.
6. **Rotor stow index.** The rear lower rotors stop at 8.8° (`REAR_ROTOR_PARK_DEG`) before folding.
   Anywhere between about 6.5° and 10.5°, the blades sit between the panel's root and keep at least
   3 mm clear. At other angles one blade touches the panel root, so this needs a motor-held stop or an
   index pin. The upper rotors clear at any angle.

### Effect on performance (same models as "Pusher depth and tilt")

| Rear wing | Mean rear incidence | hp at 150 mph | V max, 1,500 / 1,913 hp |
| --- | --- | --- | --- |
| Before (+5° to the ducts, 1.12 m) | 5.0° | 1,018 | 178 / 193 mph |
| Real hinges, stub +5° | 2.0° | 1,058 | 176 / 192 mph |
| Real hinges, stub +7° | 3.3° | 1,040 | 177 / 192 mph |
| **Real hinges, stub +9° (built)** | **4.6°** | **1,023** | **178 / 193 mph** |

Run `python3 rear_hinge_trim.py` here for the built line. Hover is essentially unchanged: lowering the canted rear ducts 4.7 in moves their thrust line under 1 in
from the CG.

### Things to know

- **Engine bay:** the lowered rear wing's stub (its spar carry-through) reached about 2.3 in into the
  top of the engine-bay envelope. This is fixed in the next section, which lowers the engine.
- **Stub at +9°:** at the 7–9° nose-up hover and transition attitudes, the stub meets the air at
  16–18°, past its stall. That does no harm in hover, but it adds drag in the early transition.
- **Duct lips:** the trimmed arc slightly reduces the lip on that part of each rear duct. The ring
  there needs local stiffening, because the hinge fitting carries the duct.
- **Hinge loads and locks:** the earlier guidance stands: about 8–14 kN·m at each fold, a hinge plus
  lock pins, and interlocks so the craft can't lift with a fold unlocked.

## Engine lowered, belly tub (27 Oct 2026)

The OPFPLG engine and its LTO accumulator move down 0.10 m (3.9 in) as one unit. That is `ENGINE_DZ`,
the same value in `x1_skyracer_blender.py` and `x1_opfplg_blender.py`. The belly under the bay is
bubbled down and out into a tub to make room, using the same method as the cabin foot well.

| | Before | Now |
| --- | --- | --- |
| Engine-bay envelope (z) | 0.55 to 1.01 m | 0.45 to 0.91 m |
| Engine top | 0.998 m | 0.898 m |
| Lowest rear-wing stub skin over the bay | 0.950 m | 0.950 m |
| Engine vs the rear stub above it | engine top 1.2 in up inside the stub | **2.8 in clear under the stub (3.0 in nearest point)** |
| Accumulator case (z) | 0.496 to 0.630 m | 0.396 to 0.530 m |
| Accumulator to belly skin | 0.7 in | 2.6 in (4.6 in at the keel) |
| Keel under the bay | 0.36 to 0.51 m | 0.28 m (11 in off the ground) from the firewall to y 0.80 m |
| Fuselage volume, firewall to y 1.50 m, below z 0.95 m | 1,111 L | **1,299 L (+188 L, +17 %)** |

How the tub is shaped (`BAY_TUB`):

- **Above z 0.70 m:** the skin is unchanged, so the wing roots, sills, spine and louvres stay where
  they were.
- **Below z 0.70 m:** the skin is blended out to a boxy section no wider than ±0.53 m. That leaves
  about 7.5 in of air gap to each sponson.
- **Keel line:**
  - z 0.28 m from the firewall to y 0.80 m (end of the accumulator);
  - rising to 0.42 m at the aft end of the bay (y 1.45 m), which clears the propane receiver;
  - rejoining the original underside at y 2.05 m, ahead of the pushers.
- **Firewall:** extended down to the new floor.

Checks:

- Every part of the engine and accumulator is inside the skin. The closest point is the e-turbo
  compressor housing, about 1.1 in from the side skin.
- The pusher bores stay clear, and all X1 Racing rules and the cockpit fit pass.
- The fold is unchanged: 89.5 × 52.9 in.
- Inside the skin, the bay contents themselves are unchanged. Wetted area grows a little, but frontal
  area does not: at every height, the tub is narrower than the cabin's foot well ahead of it.

Effects:

- **CG:** the race CG drops from z 0.714 to 0.678 m (1.4 in). `mass.py` now also places the rear
  wing and rear lift units at their lowered heights.
- **Trim:** unchanged at 1,023 hp at 150 mph and 178 / 193 mph.
- **External lines:**
  - The exhaust downpipe moves down with the engine; its outlet is now 9 in off the ground.
  - The propane vapour and liquid lines move with the engine inside the bay, then ease back up to the
    fixed pusher heat exchangers between y 1.50 and 2.10 m.
- **Aft underside:** it now sweeps up at about 20° behind the bay, against about 10° before. That is
  the part to watch for drag; a longer ramp would need the propane receiver moved forward or up.

The OPFPLG fit report in `OPFPLG/fit_report_4.5L.txt` is regenerated for the lowered engine (bay z
0.45 to 0.91 m, all margins OK). `engine_bay.png` shows the centreline section before and after.

## Spine intake louvres (27 Oct 2026)

The engine-bay intake louvres on top of the spine were flat 16 in boards laid across a curved crown.
Their ends stood up to 1.6 in off the skin, and the forward slats ran into the rear wing roots, which
come up through the spine skin ahead of y 1.1 m.

Each slat is now bent to the crown across its whole width. Its aft edge sits on the skin (2–3 mm
gap) and its leading edge is raised 0.95 in for the intake lip, the same along the whole slat.
The slats keep 1.6 in clear of the wing roots:

- **Forward six slats** (y 0.70–1.13 m, between the roots): 8.7 in wide.
- **Aft five slats** (y 1.21–1.55 m, behind where the roots dip under the skin): the full 15.7 in.

Settings: `LOUVRE_HW`, `LOUVRE_CHORD`, `LOUVRE_LIFT`, `LOUVRE_T`, `LOUVRE_ROOT_GAP`.
`spine_louvres.png` shows the result. The total lip opening is about 0.080 m², about 20 % less than the
0.10 m² of the old flat boards, because the forward slats are narrower. If the engine needs more air,
raise the lip (`LOUVRE_LIFT`): 1.2 in instead of 0.95 in gets the area back. All rules and the fold are unchanged.

## Thicker rear wing (27 Oct 2026)

The rear folding panel was thinned to 5.5 % to make the fold fit. It is now 10 % thick (100 mm at its
1.0 m chord), a little thicker than the stub's 9 %, for bending strength and room for spars and hinge
fittings. The thicker panel raises the step between the two rear hinges, so the geometry was re-solved
to keep the fold inside 90 in:

| Setting | Before | Now |
| --- | --- | --- |
| `REAR_PANEL_TR`, outer panel thickness / chord | 0.055 | **0.10** |
| `REAR_FOLD_X`, rear wing fold line from centreline | 0.82 m | 0.78 m (1.6 in inboard: longer panel) |
| `DUCT_ZR`, rear wing / duct height | 1.00 m | 0.96 m (rear wing now 6.3 in below the original) |
| `REAR_DUCT_RAISE`, duct higher on the wing tip | 55 mm | 35 mm (the thicker tip puts the hinge lower) |
| `REAR_ROTOR_PARK_DEG`, lower-rotor stow angle | 8.8° | 2.0° (clear from about 0.5° to 3.5°) |
| `ENGINE_DZ`, engine + accumulator | −0.10 m | −0.13 m (5.1 in lower, keeps the stub clearance) |
| Bay keel (`BAY_TUB` z_bot) | 0.28 m | 0.25 m (9.8 in off the ground) |

Results:

- **Folded:** 89.4 × 52.9 in. Folds at 84° / 174° front and 90° / 180° rear, as before.
- **Clearances in the fold:** nothing touches. The rear ducts and fillets keep 4 to 5 mm from the
  folded panel, and the lower rotors about 5 mm when stopped at 2° (at least 4 mm anywhere from 0.6° to 3.5°).
- **Engine bay:** the engine sits 2.4 in clear below the rear stub (2.7 in at the nearest point).
  The accumulator is 2.5 in from the belly skin, and all bay contents are inside the skin. The OPFPLG
  fit report is regenerated (bay z 0.42 to 0.88 m).
- **Louvres:** the lower wing roots come up through the spine further forward, so the louvre slats
  re-fitted themselves. Now three narrow slats sit between the roots and eight full-width slats follow
  (was six and five), which gives more intake area.
- **Rules and cockpit:** all X1 Racing rules and the cockpit fit pass, and the pusher bores stay clear.
- **Race CG:** z 0.661 m, 0.7 in lower again.

Trim, fully loaded, with the same models as before:

| Rear stub incidence | Mean rear incidence | hp at 150 mph | V max, 1,500 / 1,913 hp |
| --- | --- | --- | --- |
| **+9° (built)** | 4.0° | **1,030** | **177 / 192 mph** |
| +10° | 4.65° | 1,022 | 178 / 193 mph |

The longer twisted panel lowers the mean rear incidence a little. Raising `REAR_STUB_INC_DEG` to 10°
recovers the 8 hp and 1 mph, but takes the stub further past stall in the nose-up transition. It is
left at 9°.
