# CadPilot v3 User Prompting Guide

This guide explains how to write prompts that work well with CadPilot v3's
multi-agent CAD pipeline. The goal is to help users get consistent, valid,
manufacturable CadQuery models and static assemblies.

## What CadPilot Does

CadPilot turns a natural-language CAD request into:

- a structured design intent
- a geometry plan
- manufacturing-aware parameters
- executable CadQuery code
- sandbox validation results
- repair or replan attempts when needed
- exported CAD files
- a final summary

The system works best when the user prompt clearly describes the object,
dimensions, manufacturing method, required features, and output format.

## How The System Thinks

The pipeline does not directly jump from your prompt to final CAD. It breaks the
task into stages:

1. Understand the design intent.
2. Plan the geometry.
3. Critique the plan.
4. Choose parameters and tolerances.
5. Generate CadQuery code.
6. Execute and inspect the geometry.
7. Repair or replan if needed.
8. Critique the final result.
9. Export files and summarize.

Because of this, good prompts should help the system make strong decisions early.
Ambiguous prompts can still work, but they give the agents more room to invent
details.

## Best Prompt Structure

A strong prompt usually includes:

```text
Create a [single part / static assembly] for [purpose/application].
Use [units] and export [STEP/STL/DXF].
Manufacturing method: [FDM / CNC / sheet metal / generic].
Overall size: [main dimensions].
Required parts/features: [list].
Hole/fastener requirements: [sizes and locations].
Assembly behavior: [static / no motion / closed position / exploded position].
Constraints: [wall thickness, clearance, no decorative features, etc.].
```

## Single-Part Prompt Template

```text
Create a single [manufacturing method]-ready [part name] in CadQuery using millimeters and exporting STEP. Overall size should be about [L] x [W] x [H] mm. Include [main features]. Add [holes/slots/bores] sized for [fastener or component]. Keep wall thickness at least [T] mm, use simple chamfers on external edges, and avoid decorative text or nonfunctional details.
```

Example:

```text
Create a single CNC-machinable bearing pillow block in CadQuery using millimeters and exporting STEP. The block should be about 70 x 32 x 28 mm, with a centered 608 bearing bore, two M5 mounting holes through the base, a raised bearing boss, and small chamfers on external edges. Keep enough material around the bore and holes, avoid decorative features, and make the part a single solid.
```

## Static Assembly Prompt Template

```text
Create a static [number]-part [manufacturing method]-ready [assembly name] in CadQuery using millimeters and exporting STEP. The assembly should include [part A], [part B], and [hardware or extra parts]. Place all parts in the final assembled position. Include [interfaces/features] aligned between parts. This is a static assembly with no moving joints, hinges, animation, or degrees of freedom.
```

Example:

```text
Create a static two-part FDM-printable electronics enclosure assembly in CadQuery using millimeters and exporting STEP, with a 100 x 60 x 30 mm open-top base, 2 mm walls, four internal M3 standoffs near the corners, a flat removable lid sitting closed on top, four aligned M3 clearance holes in the lid, and a small rectangular cable opening on one short side, modeled as separate base and lid parts with no hinges or motion.
```

## What To Include

### Object Type

Be explicit about whether you want:

- `single part`
- `static assembly`
- `multi-part assembly`
- `separate components`
- `one fused solid`

Good:

```text
Create a static three-part assembly with separate upper clamp, lower clamp, and two screw representations.
```

Less clear:

```text
Make a clamp.
```

### Manufacturing Method

Mention the intended manufacturing method:

- FDM printable
- CNC machinable
- laser-cut
- sheet metal
- generic CAD model

This affects wall thickness, fillets, clearances, and feature choices.

Good:

```text
Make it FDM-printable with 2 mm minimum walls and no unsupported thin pins.
```

### Units

Always specify units.

Good:

```text
Use millimeters.
```

Avoid mixing units unless necessary.

### Overall Dimensions

Give approximate or exact size.

Good:

```text
Overall size should be about 100 mm long, 60 mm wide, and 30 mm tall.
```

If a dimension is exact, say so:

```text
The shaft bore must be exactly 8.0 mm diameter.
```

### Required Features

List functional features clearly:

- holes
- slots
- bosses
- standoffs
- ribs
- gussets
- bores
- counterbores
- countersinks
- cable openings
- mounting plates
- alignment lips

Good:

```text
Include four M3 clearance holes on a 31 mm square bolt pattern.
```

### Fasteners And Hardware

Use common fastener names:

- M2
- M3
- M4
- M5
- socket-head cap screw
- countersunk screw
- clearance hole
- threaded insert pocket

Good:

```text
Use M3 clearance holes in the lid aligned with cylindrical standoffs in the base.
```

### Position And Orientation

For assemblies, describe final placement:

```text
Place the lid in the closed position on top of the base.
```

```text
Place the upper clamp half directly above the lower half so the two saddles form one circular tube bore.
```

### Motion And Degrees Of Freedom

If you want static geometry, say so.

Good:

```text
This is a fixed static assembly with no moving joints.
```

If motion is not needed, do not ask for hinges, pivots, linkages, or adjustable
joints.

### Export Format

Specify output:

- STEP for assemblies and CAD exchange
- STL for 3D printing
- DXF for 2D profiles

Good:

```text
Export one STEP file for the full assembly.
```

## What To Avoid

### Avoid Vague Prompts

Weak:

```text
Make a box.
```

Better:

```text
Create a single FDM-printable open-top rectangular storage tray in CadQuery using millimeters and exporting STEP. Overall size should be 120 x 80 x 25 mm, with 2 mm walls, a 2 mm bottom, rounded external corners, and no lid.
```

### Avoid Conflicting Requirements

Bad:

```text
Make it a single part and also model the lid as a separate removable part.
```

Better:

```text
Model the base and lid as separate parts in one static assembly.
```

### Avoid Too Many Decorative Details

The system is better at functional mechanical geometry than decorative organic
styling.

Avoid:

```text
Add futuristic styling, complex surface texture, logos, vents everywhere, and organic curves.
```

Better:

```text
Use simple chamfers, clean rectangular surfaces, and functional vent slots on the side walls.
```

### Avoid Unsupported Complex Mechanisms At First

For early testing, prefer static assemblies.

Harder prompts include:

- gear trains
- moving hinges
- snap fits
- compliant mechanisms
- threads
- complex surface lofts
- exact industrial standard components

These can be added later, but static assemblies are better for baseline testing.

## Prompt Examples

### Electronics Enclosure Assembly

```text
Create a static two-part FDM-printable electronics enclosure assembly in CadQuery using millimeters and exporting STEP, with a 100 x 60 x 30 mm open-top base, 2 mm walls, four internal M3 standoffs near the corners, a flat removable lid sitting closed on top, four aligned M3 clearance holes in the lid, and a small rectangular cable opening on one short side, modeled as separate base and lid parts with no hinges or motion.
```

### Split Clamp Block

```text
Create a static FDM-printable split clamp block assembly in CadQuery using millimeters and exporting STEP. The assembly should clamp a 12 mm diameter tube and include a lower block, upper cap, and two simple M5 screw representations. The two halves should form a circular tube bore with slight clearance, with vertical M5 clearance holes on both sides of the bore, counterbores in the upper cap, and two base mounting holes in the lower block. Place all parts in the assembled position with no motion.
```

### NEMA 17 Motor Mount

```text
Create a static FDM-printable NEMA 17 motor mount assembly in CadQuery using millimeters and exporting STEP. Include one rigid L-bracket body and four simple M3 screw cylinders. The bracket should have a horizontal base plate, vertical motor face plate, centered shaft clearance hole, four M3 clearance holes on a 31 mm square pattern, triangular side gussets, and four M5 base mounting holes. Keep the design stiff, printable, and static with no moving joints.
```

### Camera Mount Assembly

```text
Create a static camera mount assembly in CadQuery using millimeters and exporting STEP. Include a back plate for mounting to a 20 x 20 aluminum extrusion, a front camera plate with four M2 holes, two spacer posts between the plates, and simple M3 screw representations. Place the front plate parallel to the back plate, align the spacer posts and holes, and keep the assembly fixed with no adjustable joints.
```

### Bearing Pillow Block

```text
Create a single CNC-machinable 608 bearing pillow block in CadQuery using millimeters and exporting STEP. The part should be about 70 x 32 x 28 mm, with a centered bearing bore sized for a 608 bearing, two M5 mounting holes through the base, a raised circular boss around the bearing seat, chamfered external edges, and enough material around all holes. Make it one solid part with no moving features.
```

## One-Line Prompt Pattern

For quick testing, use this compact format:

```text
Create a [single part/static assembly] [object] in CadQuery using [units] and exporting [format], with [overall dimensions], [required parts/features], [holes/fasteners], [manufacturing constraints], and [static/no motion/separate parts/fused solid].
```

Example:

```text
Create a static two-part FDM-printable electronics enclosure assembly in CadQuery using millimeters and exporting STEP, with a 100 x 60 x 30 mm open-top base, 2 mm walls, four internal M3 standoffs near the corners, a flat removable lid sitting closed on top, four aligned M3 clearance holes in the lid, and a small rectangular cable opening on one short side, modeled as separate base and lid parts with no hinges or motion.
```

## Debugging Bad Results

If the result is wrong, revise the prompt based on what failed.

### Missing Features

Add explicit feature requirements:

```text
The lid must include four M3 clearance holes aligned with the base standoffs.
```

### Wrong Part Count

State the exact part count:

```text
The assembly must contain exactly two separate CadQuery assembly components: base and lid.
```

### Misaligned Assembly

State placement:

```text
Place the lid directly on top of the base in the closed position, centered in X and Y.
```

### Poor Manufacturability

Add process constraints:

```text
Use 2 mm minimum wall thickness, avoid fragile pins, and keep all holes accessible from straight tool directions.
```

### Too Complex

Reduce scope:

```text
Do not model internal electronics, labels, textures, hinges, seals, or threads.
```

## Recommended Prompting Rules

1. Specify single part vs assembly.
2. Specify static vs moving.
3. Specify units.
4. Specify manufacturing method.
5. Give overall dimensions.
6. List required features.
7. List fastener sizes.
8. State exact part count for assemblies.
9. State final assembled position.
10. Exclude unwanted features.
11. Ask for STEP unless you specifically need STL or DXF.
12. Start simple, then add complexity.


