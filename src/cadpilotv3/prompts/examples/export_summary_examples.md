## Agent 7 - Export & Manufacturing Report Few-Shots

### Example 1 - FDM Static Assembly Manufacturing Report

INPUT:
```json
{
  "component": "two_part_electronics_enclosure",
  "spec": {
    "component_type": "assembly",
    "manufacturing_process": "FDM",
    "units": "mm",
    "constraints": [
      "min_wall_2mm",
      "flat_base_required",
      "bolt_pattern_required",
      "no_floating_geometry"
    ]
  },
  "parameters": {
    "OUTER_L": {
      "value": 100.0,
      "unit": "mm",
      "description": "Overall enclosure length.",
      "is_derived": false
    },
    "OUTER_W": {
      "value": 60.0,
      "unit": "mm",
      "description": "Overall enclosure width.",
      "is_derived": false
    },
    "BASE_H": {
      "value": 30.0,
      "unit": "mm",
      "description": "Height of the open-top base shell.",
      "is_derived": false
    },
    "LID_TOP_T": {
      "value": 5.0,
      "unit": "mm",
      "description": "Thickness of the lid top plate.",
      "is_derived": false
    },
    "WALL_T": {
      "value": 2.0,
      "unit": "mm",
      "description": "Nominal FDM wall thickness.",
      "is_derived": false
    },
    "M3_CLEAR_D": {
      "value": 3.4,
      "unit": "mm",
      "description": "M3 screw clearance hole diameter.",
      "is_derived": false
    },
    "STANDOFF_OD": {
      "value": 8.0,
      "unit": "mm",
      "description": "Outside diameter of base standoffs.",
      "is_derived": false
    },
    "LIP_CLEARANCE": {
      "value": 0.4,
      "unit": "mm",
      "description": "Total clearance between lid lip and base opening.",
      "is_derived": false
    },
    "OVERALL_H": {
      "value": 35.0,
      "unit": "mm",
      "description": "Overall assembled enclosure height.",
      "is_derived": true,
      "derived_from": "BASE_H + LID_TOP_T"
    }
  },
  "validation": {
    "geometry_report": {
      "part_count": 2,
      "bounding_box_mm": [100.0, 60.0, 35.0],
      "volume_mm3": 42000.0,
      "assembly_valid": true
    }
  },
  "export_files": [
    {
      "format": "STEP",
      "filename": "two_part_electronics_enclosure_assembly.step",
      "filepath": "output/two_part_electronics_enclosure_assembly.step",
      "size_kb": 88.0,
      "contents": "Base and removable lid STEP assembly"
    },
    {
      "format": "STL",
      "filename": "two_part_electronics_enclosure_base_lid.stl",
      "filepath": "output/two_part_electronics_enclosure_base_lid.stl",
      "size_kb": 156.5,
      "contents": "Printable STL geometry for base and lid"
    }
  ],
  "warnings": []
}
```

OUTPUT:
```json
{
  "export_files": [
    {
      "format": "STEP",
      "filename": "two_part_electronics_enclosure_assembly.step",
      "filepath": "output/two_part_electronics_enclosure_assembly.step",
      "size_kb": 88.0,
      "contents": "Base and removable lid STEP assembly"
    },
    {
      "format": "STL",
      "filename": "two_part_electronics_enclosure_base_lid.stl",
      "filepath": "output/two_part_electronics_enclosure_base_lid.stl",
      "size_kb": 156.5,
      "contents": "Printable STL geometry for base and lid"
    }
  ],
  "assembly_report_markdown": "# Two Part Electronics Enclosure\n*Generated: 2026-05-02T00:00:00Z*\n*CadQuery 2.x | Units: mm*\n\n---\n\n## Overview\nThis is a fixed two-part FDM electronics enclosure made from a separate open-top base and removable screw-on lid. The base provides the printed shell, internal M3 standoffs, and cable opening, while the lid closes over the base with a shallow alignment lip. The assembly has no moving joints; fit quality depends on printed hole sizing, lip clearance, and flatness of the mating rim. The exported STEP assembly is appropriate for CAD review and the STL export is appropriate for slicer preparation.\n\n---\n\n## Manufactured Item Summary\n\n| Item | Value |\n|------|-------|\n| Manufacturing process | FDM |\n| Artifact type | assembly |\n| Part count | 2 |\n| Overall bounding box | 100.0 x 60.0 x 35.0 mm |\n| Total reported volume | 42000.0 mm^3 |\n| Primary constraints | min_wall_2mm, flat_base_required, bolt_pattern_required, no_floating_geometry |\n\n---\n\n## Part List\n\n| Part | Manufacturing Role | Process Notes | Reported Volume | Reported Bounding Box | Qty |\n|------|--------------------|---------------|-----------------|-----------------------|-----|\n| base_shell | Open-top printed housing with standoffs and cable entry | Print bottom-down to keep the base flat and make the walls self-supporting | not separately reported | not separately reported | 1 |\n| removable_lid | Printed cover with clearance holes and internal alignment lip | Print top face down for best exterior finish, or lip-up if support cleanup inside the lip is unacceptable | not separately reported | not separately reported | 1 |\n\n---\n\n## Key Dimensions\n\n### Envelope\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| OUTER_L | 100.0 mm | Sets the X envelope and should be checked against printer bed capacity and enclosure installation clearance. |\n| OUTER_W | 60.0 mm | Sets the Y envelope and controls lid/base rim length. |\n| BASE_H | 30.0 mm | Determines internal usable height before lid closure and affects wall slenderness during printing. |\n| LID_TOP_T | 5.0 mm | Provides stiffness around screw holes and enough material for shallow recesses or countersink-like detail. |\n\n### Wall and Interface Geometry\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| WALL_T | 2.0 mm | Minimum wall thickness should print as multiple perimeters with a 0.4 mm nozzle and meets the 2 mm wall constraint. |\n| LIP_CLEARANCE | 0.4 mm | Total clearance is suitable for a non-force-fit FDM lid, but should be test fit on the target printer. |\n\n### Fasteners and Holes\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| M3_CLEAR_D | 3.4 mm | Provides normal FDM clearance for M3 screws; printed holes may need drilling to final size. |\n| STANDOFF_OD | 8.0 mm | Leaves material around the M3 screw path so standoffs are less likely to split during fastening. |\n\n### Derived Values\n\n| Parameter | Value | Derived From | Manufacturing Relevance |\n|-----------|-------|--------------|-------------------------|\n| OVERALL_H | 35.0 mm | BASE_H + LID_TOP_T | Confirms the assembled height used for fit checks and enclosure packaging. |\n\n---\n\n## Assembly and Fit Instructions\n\n1. Remove all brim, support, and stringing from the base rim, cable opening, lid lip, and screw holes. Check: The lid lip can enter the base opening by hand without shaving plastic from the rim.\n2. Place the base_shell on a flat surface with the open side facing upward. Check: The bottom does not rock and the top rim is visibly level.\n3. Install or prepare the M3 fastening method at the four standoffs, using pilot drilling or heat-set inserts if required by the intended screw type. Check: Each fastener starts straight without cracking the standoff wall.\n4. Lower the removable_lid onto the base_shell so the lip enters the base opening and the four lid holes align with the standoffs. Check: The lid seats flush around the rim with no corner lifted more than the expected print variation.\n5. Insert the M3 screws through the lid holes and tighten gradually in a diagonal pattern. Check: The lid remains flat and seated; stop tightening if the standoff begins to whiten, split, or deform.\n\n---\n\n## Manufacturing Plan\n\n### Process Strategy\nUse FDM as two separate printed components rather than a fused model. Slice with at least 3 perimeters for 2.0 mm walls when using a 0.4 mm nozzle, 4-5 top and bottom layers, and moderate infill such as 20-35 percent gyroid or grid for the lid and bottom plate. Keep the base and lid as separate bodies in the slicer so each part can use the most stable orientation.\n\n### Orientation, Setup, or Workholding\nPrint the base_shell with the flat bottom on the build plate and the open side up. This produces the cleanest outside bottom, keeps the walls vertical, and avoids support inside the enclosure. Print the removable_lid with the visible top face on the build plate if surface finish is most important, or lip-up if the printer bridges the screw holes cleanly and support removal around the lip would be difficult.\n\n### Material Recommendation\nPETG is the preferred general material because it handles screw loading and moderate heat better than PLA while remaining easy to print. ASA is a better alternative for warmer electronics environments or UV exposure, but it needs enclosure temperature control to reduce warping. PLA is acceptable only for low-temperature indoor use where screw preload and creep are not critical.\n\n### Supports, Tool Access, or Secondary Operations\nThe base should need no support if printed bottom-down. The cable opening may bridge depending on its height; use local support only if the slicer shows a long unsupported span. Drill M3 clearance holes to 3.4 mm after printing if the slicer undersizes holes, and clear the cable opening with a small file if elephant foot closes the lower edge.\n\n---\n\n## Critical Tolerances and Inspection\n\n| Feature | Recommended Tolerance or Check | Inspection Method | Reason |\n|---------|--------------------------------|-------------------|--------|\n| Lid lip fit | 0.4 mm total printed clearance, adjust after test print if binding occurs | Trial fit plus calipers across lip and opening | Controls whether the lid seats without forcing the base walls outward. |\n| M3 lid holes | 3.4 mm clearance after post-processing | 3.4 mm drill or go/no-go screw check | Prevents screw drag from misaligning the lid during fastening. |\n| Base flatness | No visible rocking on a flat plate | Surface plate or known-flat table | A warped base makes the enclosure hard to mount and can twist the lid. |\n| Standoff integrity | No cracking or whitening during screw insertion | Visual inspection during first assembly | Standoffs carry screw preload and are the highest-risk printed features. |\n\n---\n\n## Post-Processing and Quality Checks\n\n- Remove brim and support material with flush cutters and a deburring tool, paying special attention to the lid lip and cable opening.\n- Lightly drill lid holes and standoff pilot holes only if screws do not pass cleanly by hand.\n- Deburr the cable opening with a needle file so wire insulation is not cut by a sharp printed edge.\n- Test-fit the lid before installing electronics; if the lid binds, sand the lip evenly rather than forcing the base walls outward.\n- Perform one full assembly with the intended screws and verify that all four corners sit flush.\n\n---\n\n## Manufacturing Risks\n\n| Risk | Why It Matters | Mitigation |\n|------|----------------|------------|\n| Lid lip too tight | FDM dimensional variation can make the 0.4 mm clearance insufficient on some printers | Print a small lip/opening test coupon or sand the lip uniformly after first fit. |\n| Standoff splitting | Printed layer lines and undersized pilot holes can crack around M3 screws | Drill pilot/clearance holes to final size and tighten screws gradually in a diagonal pattern. |\n| Base warping | A long thin enclosure base can lift at corners and prevent the lid from seating | Use PETG/ASA bed adhesion settings, avoid excessive cooling, and keep the flat bottom on the build plate. |\n\n---\n\n## Export Files\n\n| Format | Filename | Size | Contents |\n|--------|----------|------|----------|\n| STEP | two_part_electronics_enclosure_assembly.step | 88.0 KB | Base and removable lid STEP assembly |\n| STL | two_part_electronics_enclosure_base_lid.stl | 156.5 KB | Printable STL geometry for base and lid |",
  "user_facing_warnings": []
}
```

### Example 2 - CNC Single-Part Manufacturing Report With Warning

INPUT:
```json
{
  "component": "bearing_pillow_block_608",
  "spec": {
    "component_type": "single_part",
    "manufacturing_process": "CNC",
    "units": "mm",
    "constraints": [
      "no_internal_undercuts",
      "through_holes_only",
      "press_fit_bearing_seat",
      "deburr_edges"
    ]
  },
  "parameters": {
    "BLOCK_L": {
      "value": 80.0,
      "unit": "mm",
      "description": "Overall block length.",
      "is_derived": false
    },
    "BLOCK_W": {
      "value": 35.0,
      "unit": "mm",
      "description": "Overall block width.",
      "is_derived": false
    },
    "BLOCK_H": {
      "value": 35.0,
      "unit": "mm",
      "description": "Overall block height.",
      "is_derived": false
    },
    "BEARING_SEAT_D": {
      "value": 22.0,
      "unit": "mm",
      "description": "Nominal diameter for the 608 bearing outside diameter.",
      "is_derived": false
    },
    "SHAFT_CLEAR_D": {
      "value": 8.4,
      "unit": "mm",
      "description": "Clearance bore for an 8 mm shaft.",
      "is_derived": false
    },
    "M6_CLEAR_D": {
      "value": 6.6,
      "unit": "mm",
      "description": "M6 mounting screw clearance diameter.",
      "is_derived": false
    },
    "MOUNT_HOLE_SPACING": {
      "value": 55.0,
      "unit": "mm",
      "description": "Spacing between base mounting holes.",
      "is_derived": false
    },
    "BOSS_D": {
      "value": 32.0,
      "unit": "mm",
      "description": "Raised bearing boss outside diameter.",
      "is_derived": false
    },
    "BOSS_RADIAL_WALL": {
      "value": 5.0,
      "unit": "mm",
      "description": "Radial wall between bearing seat and boss outside.",
      "is_derived": true,
      "derived_from": "(BOSS_D - BEARING_SEAT_D) / 2"
    }
  },
  "validation": {
    "geometry_report": {
      "part_count": 1,
      "bounding_box_mm": [80.0, 35.0, 35.0],
      "volume_mm3": 54000.0,
      "assembly_valid": true
    }
  },
  "export_files": [
    {
      "format": "STEP",
      "filename": "bearing_pillow_block_608.step",
      "filepath": "output/bearing_pillow_block_608.step",
      "size_kb": 64.2,
      "contents": "CNC-machined bearing pillow block"
    }
  ],
  "warnings": [
    "Bearing seat fit must be verified against the actual bearing and machining process before production."
  ]
}
```

OUTPUT:
```json
{
  "export_files": [
    {
      "format": "STEP",
      "filename": "bearing_pillow_block_608.step",
      "filepath": "output/bearing_pillow_block_608.step",
      "size_kb": 64.2,
      "contents": "CNC-machined bearing pillow block"
    }
  ],
  "assembly_report_markdown": "# Bearing Pillow Block 608\n*Generated: 2026-05-02T00:00:00Z*\n*CadQuery 2.x | Units: mm*\n\n---\n\n## Overview\nThis is a single-piece CNC-machined pillow block for holding a 608 bearing in a raised central boss. The design uses a rectangular base with two M6 through mounting holes, a bearing seat, and an 8 mm shaft clearance bore. It has no moving geometry by itself, but the bearing seat and shaft bore are functional interfaces and should be machined and inspected more tightly than the outside envelope. The exported STEP file is suitable for CAM setup, drawing creation, and supplier quotation.\n\n---\n\n## Manufactured Item Summary\n\n| Item | Value |\n|------|-------|\n| Manufacturing process | CNC |\n| Artifact type | single part |\n| Part count | 1 |\n| Overall bounding box | 80.0 x 35.0 x 35.0 mm |\n| Total reported volume | 54000.0 mm^3 |\n| Primary constraints | no_internal_undercuts, through_holes_only, press_fit_bearing_seat, deburr_edges |\n\n---\n\n## Part List\n\n| Part | Manufacturing Role | Process Notes | Reported Volume | Reported Bounding Box | Qty |\n|------|--------------------|---------------|-----------------|-----------------------|-----|\n| bearing_pillow_block_608 | Machined bearing support block with base mounting holes and precision bearing seat | Mill from rectangular stock, finish bore the bearing seat, and deburr all exposed edges | 54000.0 mm^3 | 80.0 x 35.0 x 35.0 mm | 1 |\n\n---\n\n## Key Dimensions\n\n### Envelope\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| BLOCK_L | 80.0 mm | Sets stock length and mounting footprint. |\n| BLOCK_W | 35.0 mm | Sets stock width and minimum vise grip area. |\n| BLOCK_H | 35.0 mm | Sets final height and bearing centerline envelope. |\n\n### Bearing and Shaft Interfaces\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| BEARING_SEAT_D | 22.0 mm | Critical functional diameter for the 608 bearing outside diameter; finish machine and inspect rather than relying on rough milling. |\n| SHAFT_CLEAR_D | 8.4 mm | Provides clearance for an 8 mm shaft through the mounted bearing region. |\n| BOSS_D | 32.0 mm | Provides radial material around the bearing seat for stiffness and press-fit support. |\n\n### Mounting Holes\n\n| Parameter | Value | Manufacturing Relevance |\n|-----------|-------|-------------------------|\n| M6_CLEAR_D | 6.6 mm | Standard clearance for M6 fasteners; drill through from an accessible face. |\n| MOUNT_HOLE_SPACING | 55.0 mm | Controls bolt pattern alignment to the mating plate or fixture. |\n\n### Derived Values\n\n| Parameter | Value | Derived From | Manufacturing Relevance |\n|-----------|-------|--------------|-------------------------|\n| BOSS_RADIAL_WALL | 5.0 mm | (BOSS_D - BEARING_SEAT_D) / 2 | Confirms there is enough wall around the bearing seat for stiffness and press-fit load. |\n\n---\n\n## Assembly and Fit Instructions\n\n1. Deburr the base mounting holes, bearing seat edge, and shaft clearance bore after machining. Check: No burrs remain that can prevent the bearing or mounting screws from seating flat.\n2. Clean the bearing seat and confirm the seat diameter against the intended bearing fit before pressing. Check: The bore gauge reading matches the specified shop fit for the selected bearing and material.\n3. Align the 608 bearing square to the bearing seat and press it in using an arbor press and a flat driver that contacts only the bearing outer race. Check: The bearing face seats flush and the inner race rotates freely without roughness.\n4. Place the block on the mating plate and insert two M6 fasteners through the mounting holes. Check: Both screws pass freely through the 6.6 mm clearance holes without pulling the block sideways.\n5. Tighten the M6 fasteners evenly against the base. Check: The block remains flat against the mating surface with no visible rocking or gap under the base.\n\n---\n\n## Manufacturing Plan\n\n### Process Strategy\nMachine the part from rectangular bar or plate stock using a 3-axis CNC mill. Rough the outside profile and boss features first, drill the through holes from accessible faces, then finish the bearing seat with a boring head, circular interpolation, or reamer-sized operation depending on required fit. Avoid hidden undercuts; all functional holes are accessible as through features.\n\n### Orientation, Setup, or Workholding\nUse the bottom face as the primary datum and one long side as the secondary datum. First operation: face the top, rough/finish the boss, drill the shaft clearance and M6 holes, and finish the bearing seat. Second operation if needed: flip onto parallels, face the bottom to final height, and break all bottom edges. Keep enough stock for vise grip before final contouring.\n\n### Material Recommendation\n6061-T6 aluminum is the preferred general CNC material because it machines cleanly, is stable, and is strong enough for a small bearing support. Acetal is a good low-friction, corrosion-resistant alternative for light-duty fixtures but will not hold a press fit as consistently under heat. Mild steel or stainless steel should be used only if higher load or wear resistance is required because machining time and tool wear increase.\n\n### Supports, Tool Access, or Secondary Operations\nUse spot drilling before drilling the M6 clearance holes and shaft bore. Finish the bearing seat with a controlled finishing pass and inspect before pressing the bearing. Add small chamfers or deburr breaks on all handled edges, but keep chamfers away from the bearing seating shoulder unless a lead-in is intentionally required.\n\n---\n\n## Critical Tolerances and Inspection\n\n| Feature | Recommended Tolerance or Check | Inspection Method | Reason |\n|---------|--------------------------------|-------------------|--------|\n| Bearing seat diameter | Fit to selected 608 bearing and material; typically controlled more tightly than +/-0.05 mm | Bore gauge or calibrated plug gauge | Bearing retention and alignment depend on this diameter. |\n| Shaft clearance bore | 8.4 mm clearance, verify no tool marks or burrs restrict shaft passage | Pin gauge or shaft trial fit | Prevents shaft rubbing after bearing installation. |\n| M6 clearance holes | 6.6 mm through, position matched to 55.0 mm spacing | Calipers, transfer pins, or CMM for bolt pattern | Ensures the block bolts down without side loading. |\n| Base flatness | Flat enough to seat without rocking on mating plate | Surface plate and feeler gauge | A bowed base can misalign the bearing axis. |\n| Bearing seat perpendicularity | Seat axis square to base within shop tolerance | Indicator sweep or CMM | Prevents bearing skew and uneven shaft loading. |\n\n---\n\n## Post-Processing and Quality Checks\n\n- Deburr every hole edge with a hand deburring tool or small chamfer mill.\n- Clean chips from the bearing seat and shaft bore before inspection.\n- Inspect the bearing seat before pressing the bearing; do not correct an undersized bore by forcing the bearing in.\n- Test mount the block with two M6 screws and verify that both screws pass freely through the clearance holes.\n- After bearing installation, spin the bearing by hand and check for roughness, tilt, or binding.\n\n---\n\n## Manufacturing Risks\n\n| Risk | Why It Matters | Mitigation |\n|------|----------------|------------|\n| Bearing seat fit mismatch | A too-tight seat can damage the bearing; a too-loose seat can allow creep or misalignment | Machine a test bore in matching stock or finish bore the seat after measuring the actual bearing OD. |\n| Burrs in functional holes | Burrs can prevent the bearing, shaft, or mounting screws from seating correctly | Deburr and inspect all hole edges before assembly. |\n| Datum error between operations | Flipping the part without controlled datums can shift the bearing axis relative to the base | Use the bottom and long side as repeatable datums and verify setup before finishing bores. |\n\n---\n\n## Export Files\n\n| Format | Filename | Size | Contents |\n|--------|----------|------|----------|\n| STEP | bearing_pillow_block_608.step | 64.2 KB | CNC-machined bearing pillow block |\n\n---\n\n## Warnings\nWarning: Bearing seat fit must be verified against the actual bearing and machining process before production.",
  "user_facing_warnings": [
    "Bearing seat fit must be verified against the actual bearing and machining process before production."
  ]
}
```
