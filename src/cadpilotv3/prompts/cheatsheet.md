cadquery_cheatsheet:
"All dimensions are in mm"

# Importing CadQuery

```python
import cadquery as cq
```


# Workplane creation

A workplane is a 2D reference plane on which you create sketches, shapes, or transformations in a 3D space. It's essentially your "drawing surface" — like a sheet of paper placed in 3D space.

**Rule**: If the user prompt is of the form:  
"Create a workplane in [plane name] plane"  
Then use the following method:

**Method**:
```python
cq.Workplane("plane_name")
```

**Allowed plane names**:
- XY
- YZ
- XZ
- front
- back
- left
- right
- top
- bottom

**Examples**:
- **Prompt**: Create a workplane in "front" plane  
  **Output**:
  ```python
  cq.Workplane("front")
  ```

- **Prompt**: Create a workplane in "XY" plane  
  **Output**:
  ```python
  cq.Workplane("XY")
  ```

**Rule**: If the user prompt is of the form:  
"Create a workplane with an origin at coordinates (x, y, z), direction vector at (x1, y1, z1), and normal vector at (x2, y2, z2)"  
Then use the following method:

**Method**:
```python
cq.Workplane(cq.Plane(cq.Vector(x, y, z), cq.Vector(x1, y1, z1), cq.Vector(x2, y2, z2)))
```

**Example**:
- **Prompt**: Create a workplane with an origin at coordinates (-0.2265625, 0.4609375, 0.0), an x-axis direction vector of (1.0, 0.0, 0.0), and a normal vector of (0.0, 0.0, 1.0)  
  **Output**:
  ```python
  cq.Workplane(cq.Plane(cq.Vector(-0.2265625, 0.4609375, 0.0), cq.Vector(1.0, 0.0, 0.0), cq.Vector(0.0, 0.0, 1.0)))
  ```

# Workplane Operations

Workplane operations which will be shown below are used to create 2D constructs that can be used to create 3D features. Remember all 2D operations require a Workplane object to be created.

**Rule**: Use when user wants to set or shift the origin to (x, y) within the workplane.

**Method**:
```python
.center(x, y)
```

**Examples**:
- **Prompt**: Shift the workplane origin to (5, -3)  
  **Output**:
  ```python
  .center(5, -3)
  ```

**Rule**: Use when user wants to mirror entities about the Y-axis.

**Method**:
```python
.mirrorY()
```

**Examples**:
- **Prompt**: Mirror sketch about Y axis  
  **Output**:
  ```python
  .mirrorY()
  ```

**Rule**: Use when user wants to mirror entities about the X-axis.

**Method**:
```python
.mirrorX()
```

**Examples**:
- **Prompt**: Mirror sketch about X axis  
  **Output**:
  ```python
  .mirrorX()
  ```

**Rule**: Use when user wants to join all pending edges into a wire.

**Method**:
```python
.wire()
```

**Examples**:
- **Prompt**: Connect all edges into a single wire  
  **Output**:
  ```python
  .wire()
  ```

**Rule**: Whenever the sketch is completed with a series of lines, arcs, splines and parametric curves, always close the curve (even if user not mentions it in the prompt)

**Method**:
```python
.close()
```

**Examples**:
  **Output**:
  ```python
  sketch = cq.Workplane("XY").moveTo(0.0, 0.0).threePointArc((0.2, -0.17), (0.45, 0.0)).threePointArc((0.42, 0.012), (0.39, 0.023)).threePointArc((0.22, -0.11), (0.05, 0.02)).threePointArc((0.028, 0.012), (0.0, 0.0)).close()
  ```

**Rule**: Use when the user wants to move all items on the stack by a given vector.

**Method**:
```python
.translate((x, y, z))
```

**Allowed values**:
- vec: Translation vector (x, y, z)

**Examples**:
- **Prompt**: Move the object 10 units in X, 0 in Y, and -5 in Z  
  **Output**:
  ```python
  .translate((10, 0, -5))
  ```

- **Prompt**: Translate geometry by vector (0, 15, 2)  
  **Output**:
  ```python
  .translate((0, 15, 2))
  ```

**Rule**: Use when the user wants to rotate geometry around a custom axis defined by two points.

**Method**:
```python
.rotate((x1, y1, z1), (x2, y2, z2), angleDegrees)
```

**Allowed values**:
- axisStartPoint: Starting point of the axis (x1, y1, z1)
- axisEndPoint: Ending point of the axis (x2, y2, z2)
- angleDegrees: Rotation angle in degrees

**Examples**:
- **Prompt**: Rotate objects 90 degrees around axis from (0, 0, 0) to (0, 0, 1)  
  **Output**:
  ```python
  .rotate((0, 0, 0), (0, 0, 1), 90)
  ```

**Rule**: Use when the user wants to rotate geometry about its center, around an axis defined by a vector from origin to axisEndPoint.

**Method**:
```python
.rotateAboutCenter((x, y, z), angleDegrees)
```

**Allowed values**:
- axisEndPoint: Rotation axis vector endpoint (x, y, z)
- angleDegrees: Rotation angle in degrees

**Examples**:
- **Prompt**: Rotate object about center around Z-axis by 180 degrees  
  **Output**:
  ```python
  .rotateAboutCenter((0, 0, 1), 180)
  ```

- **Prompt**: Rotate the geometry about its center around (1, 0, 0) by 45 degrees  
  **Output**:
  ```python
  .rotateAboutCenter((1, 0, 0), 45)
  ```

**Rule**: Use when user wants to place a predefined sketch at each point on the stack.

**Method**:
```python
.placeSketch(sketch1, sketch2, ...)
```

**Examples**:
- **Prompt**: Place a sketch at current array points  
  **Output**:
  ```python
  .placeSketch(sketch)
  ```


# 2D construction

To create 2D sketches like lines, Arcs, rectangles, circles, splines, parametric curves etc.

**Rule**: Use when the user wants to create a rectangle on the workplane.

**Method**:
```python
.rect(xLen, yLen[, centered=True])
```

**Allowed values**:
- xLen, yLen: Dimensions of the rectangle
- centered: Optional (default True); if False, rectangle is drawn from lower-left corner

**Examples**:
- **Prompt**: Draw a 20x10 rectangle centered at the origin  
  **Output**:
  ```python
  .rect(20, 10)
  ```

- **Prompt**: Draw a 15 by 5 rectangle from corner  
  **Output**:
  ```python
  .rect(15, 5, centered=False)
  ```

**Rule**: Use to draw a circle with the given radius.

**Method**:
```python
.circle(radius[, forConstruction=False])
```

**Allowed values**:
- radius: Radius of the circle
- forConstruction: Optional; if True, marks circle for construction only

**Examples**:
- **Prompt**: Draw a circle with radius 8  
  **Output**:
  ```python
  .circle(8)
  ```

- **Prompt**: Draw a construction circle with radius 5  
  **Output**:
  ```python
  .circle(5, forConstruction=True)
  ```

**Rule**: Use to draw an ellipse with the given X and Y radii.

**Method**:
```python
.ellipse(x_radius, y_radius)
```

**Examples**:
- **Prompt**: Draw an ellipse with radii 10 and 4  
  **Output**:
  ```python
  .ellipse(10, 4)
  ```

**Rule**: Use to draw an elliptical arc with the specified radii.

**Method**:
```python
.ellipseArc(x_radius, y_radius)
```

**Examples**:
- **Prompt**: Draw an elliptical arc with x-radius 8 and y-radius 3  
  **Output**:
  ```python
  .ellipseArc(8, 3)
  ```

**Rule**: Use when the user wants to create a polyline through multiple points.

**Method**:
```python
.polyline([(x1, y1), (x2, y2), ...])
```

**Examples**:
- **Prompt**: Draw a polyline through (0, 0), (4, 4), and (8, 0)  
  **Output**:
  ```python
  .polyline([(0, 0), (4, 4), (8, 0)])
  ```

**Rule**: Use to generate a rectangular array of points.

**Method**:
```python
.rarray(xSpacing, ySpacing, xCount, yCount)
```

**Examples**:
- **Prompt**: Create a 3x2 array with spacing 10 in X and 5 in Y  
  **Output**:
  ```python
  .rarray(10, 5, 3, 2)
  ```

**Rule**: Use when the user wants to place points in a circular pattern.

**Method**:
```python
.polarArray(radius, startAngle, count, totalAngle)
```

**Examples**:
- **Prompt**: Create 8 points around a circle of radius 20 starting at angle 0  
  **Output**:
  ```python
  .polarArray(20, 0, 8, 360)
  ```

**Rule**: Use to draw a rounded slot shape.

**Method**:
```python
.slot2D(length, diameter[, angle=0])
```

**Examples**:
- **Prompt**: Create a horizontal slot 12 units long and 4 units in diameter  
  **Output**:
  ```python
  .slot2D(12, 4)
  ```

- **Prompt**: Create a slot 20x6 rotated at 45 degrees  
  **Output**:
  ```python
  .slot2D(20, 6, angle=45)
  ```

**Rule**: Use when user wants to draw a line to a specific coordinate (x, y).

**Method**:
```python
.lineTo(x, y)
```

**Examples**:
- **Prompt**: Draw a line to point (10, 5)  
  **Output**:
  ```python
  .lineTo(10, 5)
  ```

**Rule**: Use when the user specifies a relative offset line to the current point.

**Method**:
```python
.line(xDist, yDist)
```

**Examples**:
- **Prompt**: Draw a line 5 units right and 3 units up  
  **Output**:
  ```python
  .line(5, 3)
  ```

**Description**: Draw a vertical line relative to the current point.

**Method**:
```python
.vLine(distance)
```

**Examples**:
- **Prompt**: Draw a vertical line upwards by 10 units  
  **Output**:
  ```python
  .vLine(10)
  ```

**Description**: Draw a vertical line to an absolute Y-coordinate.

**Method**:
```python
.vLineTo(yCoord)
```

**Examples**:
- **Prompt**: Draw a vertical line to Y = 15  
  **Output**:
  ```python
  .vLineTo(15)
  ```

**Description**: Draw a horizontal line relative to the current point.

**Method**:
```python
.hLine(distance)
```

**Examples**:
- **Prompt**: Draw a horizontal line 8 units to the right  
  **Output**:
  ```python
  .hLine(8)
  ```

**Description**: Draw a horizontal line to an absolute X-coordinate.

**Method**:
```python
.hLineTo(xCoord)
```

**Examples**:
- **Prompt**: Draw a horizontal line to X = -10  
  **Output**:
  ```python
  .hLineTo(-10)
  ```

**Description**: Draw a line from current point at given angle and distance.

**Method**:
```python
.polarLine(distance, angle)
```

**Examples**:
- **Prompt**: Draw a line 10 units at 45 degrees  
  **Output**:
  ```python
  .polarLine(10, 45)
  ```

**Description**: Draw a line from current point to a point defined by polar coordinates.

**Method**:
```python
.polarLineTo(distance, angle)
```

**Examples**:
- **Prompt**: Draw to polar coordinates with radius 20 and angle 30  
  **Output**:
  ```python
  .polarLineTo(20, 30)
  ```

**Description**: Move to a point (x, y) without drawing a line.

**Method**:
```python
.moveTo(x, y)
```

**Examples**:
- **Prompt**: Move to (5, 5)  
  **Output**:
  ```python
  .moveTo(5, 5)
  ```

**Description**: Move relative to the current point, without drawing.

**Method**:
```python
.move(xDist, yDist)
```

**Examples**:
- **Prompt**: Move 3 units right and 4 units up  
  **Output**:
  ```python
  .move(3, 4)
  ```

**Rule**: Use when the user wants to create a spline through multiple 2D or 3D points.

**Method**:
```python
.spline([(x1, y1), (x2, y2), ...])
```

**Examples**:
- **Prompt**: Create a spline through points (0, 0), (5, 5), and (10, 0)  
  **Output**:
  ```python
  .spline([(0, 0), (5, 5), (10, 0)])
  ```

**Rule**: Use when user asks to create a curve from a mathematical function of one parameter.

**Method**:
```python
.parametricCurve(func, N)
```

**Examples**:
- **Prompt**: Create a parametric curve using lambda t: (t, t*t) with 50 points  
  **Output**:
  ```python
  .parametricCurve(lambda t: (t, t*t), N=50)
  ```

**Rule**: Use when user wants to define a surface using a function of two variables.

**Method**:
```python
.parametricSurface(func, N)
```

**Examples**:
- **Prompt**: Create a parametric surface using lambda u,v: (u,v,u*v) with 10 steps  
  **Output**:
  ```python
  .parametricSurface(lambda u, v: (u, v, u*v), N=10)
  ```

**Rule**: Use when user provides a sagitta to define the arc.

**Method**:
```python
.sagittaArc((x, y), sag)
```

**Examples**:
- **Prompt**: Draw an arc to (10, 0) with sagitta 3  
  **Output**:
  ```python
  .sagittaArc((10, 0), 3)
  ```

**Rule**: Use when user defines an arc using radius and endpoint.

**Method**:
```python
.radiusArc((x, y), radius)
```

**Examples**:
- **Prompt**: Draw an arc to (5, 5) with radius 10  
  **Output**:
  ```python
  .radiusArc((5, 5), 10)
  ```

**Rule**: Use when user wants to draw a tangent arc ending at a specific point.

**Method**:
```python
.tangentArcPoint((x, y))
```

**Examples**:
- **Prompt**: Draw a tangent arc ending at (8, 8)  
  **Output**:
  ```python
  .tangentArcPoint((8, 8))
  ```

**Rule**: Use when user wants to construct an elliptical face with specified radii.

**Method**:
```python
.ellipse(a1, a2[, angle=0, mode='arc', tag=None])
```

**Allowed values**:
- a1, a2: Major and minor radii
- angle: Optional rotation angle in degrees
- mode: Optional mode, e.g., 'arc' or 'segment'
- tag: Optional string tag

**Examples**:
- **Prompt**: Create an ellipse with radii 10 and 5 rotated 30 degrees  
  **Output**:
  ```python
  .ellipse(10, 5, angle=30)
  ```

**Rule**: Use to create a trapezoidal face with specified width, height, and base angles.

**Method**:
```python
.trapezoid(w, h, a1[, a2=0, angle=0])
```

**Allowed values**:
- w: Width
- h: Height
- a1, a2: Base angles in degrees (a2 optional, defaults to 0)
- angle: Optional rotation

**Examples**:
- **Prompt**: Create a trapezoid width 10, height 5, base angle 20 degrees  
  **Output**:
  ```python
  .trapezoid(10, 5, 20)
  ```

**Rule**: Use to create a slot-shaped face.

**Method**:
```python
.slot(w, h[, angle=0, mode='arc', tag=None])
```

**Allowed values**:
- w: Length of slot
- h: Width of slot
- angle: Optional rotation
- mode: Optional mode for ends
- tag: Optional string tag

**Examples**:
- **Prompt**: Create a horizontal slot 15 long and 4 wide  
  **Output**:
  ```python
  .slot(15, 4)
  ```

**Rule**: Use to create a regular polygon face with n sides inscribed in radius r.

**Method**:
```python
.regularPolygon(r, n[, angle=0, mode='arc', tag=None])
```

**Allowed values**:
- r: Radius of circumscribed circle
- n: Number of sides
- angle: Optional rotation
- mode: Optional mode
- tag: Optional string tag

**Examples**:
- **Prompt**: Create a hexagon with radius 10  
  **Output**:
  ```python
  .regularPolygon(10, 6)
  ```

**Rule**: Use to create a polygonal face from a list of points.

**Method**:
```python
.polygon([(x1, y1), (x2, y2), ...][, angle=0, mode='arc', tag=None])
```

**Allowed values**:
- pts: List of 2D points
- angle: Optional rotation
- mode: Optional mode
- tag: Optional string tag

**Examples**:
- **Prompt**: Create a polygon from points (0,0), (5,5), (10,0)  
  **Output**:
  ```python
  .polygon([(0, 0), (5, 5), (10, 0)])
  ```

**Rule**: Use to generate a rectangular grid of points.

**Method**:
```python
.rarray(xs, ys, nx, ny)
```

**Allowed values**:
- xs, ys: Spacing in X and Y directions
- nx, ny: Number of points in X and Y

**Examples**:
- **Prompt**: Create a 4x3 array with 10 spacing in X and 5 in Y  
  **Output**:
  ```python
  .rarray(10, 5, 4, 3)
  ```

**Rule**: Use to generate points in a circular (polar) pattern.

**Method**:
```python
.parray(r, a1, da, n[, rotate=False])
```

**Allowed values**:
- r: Radius
- a1: Start angle in degrees
- da: Angle increment in degrees
- n: Number of points
- rotate: Optional boolean to rotate points

**Examples**:
- **Prompt**: Create 8 points on a circle of radius 20 starting at 0 degrees, 45 degree steps  
  **Output**:
  ```python
  .parray(20, 0, 45, 8)
  ```

**Rule**: Use when user wants to offset selected wires or edges by a specified distance.

**Method**:
```python
.offset(d[, mode='arc', tag=None])
```

**Allowed values**:
- d: Offset distance (positive or negative)
- mode: Optional, offset mode (e.g., 'arc', 'intersection', 'tangent')
- tag: Optional string tag

**Examples**:
- **Prompt**: Offset wires outward by 2 units  
  **Output**:
  ```python
  .offset(2)
  ```

- **Prompt**: Offset wires inward by 1 unit using tangent mode  
  **Output**:
  ```python
  .offset(-1, mode='tangent')
  ```

**Rule**: Use when user wants to add a fillet (rounded corner) to the current selection with specified radius.

**Method**:
```python
.fillet(d)
```

**Allowed values**:
- d: Radius of fillet

**Examples**:
- **Prompt**: Add a fillet with radius 5  
  **Output**:
  ```python
  .fillet(5)
  ```

**Rule**: Use when user wants to add a chamfer (beveled corner) to the current selection with specified distance.

**Method**:
```python
.chamfer(d)
```

**Allowed values**:
- d: Chamfer distance

**Examples**:
- **Prompt**: Add a chamfer with distance 3  
  **Output**:
  ```python
  .chamfer(3)
  ```

**Rule**: Use when user wants to remove internal or redundant wires from the sketch.

**Method**:
```python
.clean()
```

**Examples**:
- **Prompt**: Clean the sketch to remove internal wires  
  **Output**:
  ```python
  .clean()
  ```



# 3D construction

Used to create 3D objects like box, cylinder, sphere etc.

**Rule**: Use when user wants to create a rectangular box solid.

**Method**:
```python
.box(length, width, height)
```

**Allowed values**:
- length, width, height: Dimensions of the box along X, Y, and Z axes respectively (floats)

**Examples**:
- **Prompt**: Create a box 10x20x30  
  **Output**:
  ```python
  .box(10, 20, 30)
  ```

**Rule**: Use when user wants to create a sphere solid.

**Method**:
```python
.sphere(radius)
```

**Allowed values**:
- radius: Radius of the sphere (float)

**Examples**:
- **Prompt**: Create a sphere with radius 15  
  **Output**:
  ```python
  .sphere(15)
  ```

**Rule**: Use when user wants to create a cylindrical solid.

**Method**:
```python
.cylinder(height, radius)
```

**Allowed values**:
- height: Height of the cylinder (float)
- radius: Radius of the cylinder base (float)

**Examples**:
- **Prompt**: Create a cylinder with height 20 and radius 5  
  **Output**:
  ```python
  .cylinder(20, 5)
  ```

**Rule**: Use when user wants to create 3D text on the workplane.

**Method**:
```python
.text(txt, fontsize, distance)
```

**Allowed values**:
- txt: Text string to create
- fontsize: Font size in units
- distance: Extrusion distance (thickness) of the text

**Examples**:
- **Prompt**: Create 3D text "Hello" with font size 10 and thickness 2  
  **Output**:
  ```python
  .text("Hello", 10, 2)
  ```

**Rule**: Use when user wants to create a 3D wedge solid with specified dimensions.

**Method**:
```python
.wedge(dx, dy, dz, xmin, zmin[, centered=True])
```

**Allowed values**:
- dx, dy, dz: Dimensions of the wedge along X, Y, and Z axes respectively (floats)
- xmin, zmin: Minimum X and Z coordinates relative to the workplane origin (floats)
- centered: Optional boolean (default True) indicating if wedge is centered on Y axis

**Examples**:
- **Prompt**: Create a wedge 10x20x30 with xmin=0 and zmin=0  
  **Output**:
  ```python
  .wedge(10, 20, 30, 0, 0)
  ```

- **Prompt**: Create a wedge 5x10x15, xmin=-2, zmin=1, centered on Y axis  
  **Output**:
  ```python
  .wedge(5, 10, 15, -2, 1, centered=True)
  ```

# 3D operations

Used to perform 3D operations on 2D Workplane

**Rule**: Use when user wants to create a counterbored hole on the workplane.

**Method**:
```python
.cboreHole(diameter, cboreDiameter[, depth=None, ...])
```

**Allowed values**:
- diameter: Diameter of the through hole
- cboreDiameter: Diameter of the counterbore
- depth: Optional depth of the hole

**Examples**:
- **Prompt**: Create a counterbored hole with 5mm hole diameter and 10mm counterbore diameter  
  **Output**:
  ```python
  .cboreHole(5, 10)
  ```

**Rule**: Use when user wants to create a countersunk hole on the workplane.

**Method**:
```python
.cskHole(diameter, cskDiameter[, depth=None, ...])
```

**Allowed values**:
- diameter: Diameter of the through hole
- cskDiameter: Diameter of the countersink
- depth: Optional depth of the hole

**Examples**:
- **Prompt**: Create a countersunk hole with 4mm hole diameter and 8mm countersink diameter  
  **Output**:
  ```python
  .cskHole(4, 8)
  ```

**Rule**: Use when user wants to drill a simple hole.

**Method**:
```python
.hole(diameter[, depth=None, clean=True])
```

**Allowed values**:
- diameter: Hole diameter
- depth: Optional hole depth, defaults through entire solid if None
- clean: Optional boolean to clean result

**Examples**:
- **Prompt**: Create a 6mm hole through the entire solid  
  **Output**:
  ```python
  .hole(6)
  ```

- **Prompt**: Create a 3mm hole with 10mm depth  
  **Output**:
  ```python
  .hole(3, 10)
  ```

**Rule**: Use when user wants to extrude all un-extruded wires to make prismatic solids.

**Method**:
```python
.extrude(until[, combine=True, clean=True, ...])
```

**Allowed values**:
- until: Extrusion length or until condition (e.g., a plane)
- combine: Optional boolean to combine with existing solid
- clean: Optional boolean to clean the geometry

**Examples**:
- **Prompt**: Extrude the sketch by 20 units  
  **Output**:
  ```python
  .extrude(20)
  ```

**Rule**: Use when user wants to subtract a solid from the current solid.

**Method**:
```python
.cut(toCut[, clean=True, tol=1e-6])
```

**Allowed values**:
- toCut: Solid to subtract
- clean: Optional boolean to clean after operation
- tol: Optional tolerance

**Examples**:
- **Prompt**: Subtract cylinder from the current solid  
  **Output**:
  ```python
  .cut(cylinder)
  ```

**Rule**: Use to create a blind cut extrusion (cut of specified length) from un-extruded wires.

**Method**:
```python
.cutBlind(until[, clean=True, both=False, taper=0])
```

**Allowed values**:
- until: Cut length
- clean: Optional boolean
- both: Optional boolean to cut both directions
- taper: Optional taper angle in degrees

**Examples**:
- **Prompt**: Cut blind 10 units into the solid  
  **Output**:
  ```python
  .cutBlind(10)
  ```

**Rule**: Use to cut through the entire solid with all un-extruded wires.

**Method**:
```python
.cutThruAll([clean=True, taper=0])
```

**Allowed values**:
- clean: Optional boolean
- taper: Optional taper angle

**Examples**:
- **Prompt**: Cut through entire solid  
  **Output**:
  ```python
  .cutThruAll()
  ```

**Rule**: Use to union all items on the stack or with provided solid.

**Method**:
```python
.union([toUnion=None, clean=True, glue=True, tol=1e-6])
```

**Allowed values**:
- toUnion: Optional solid(s) to union with
- clean: Optional boolean
- glue: Optional boolean to glue solids
- tol: Optional tolerance

**Examples**:
- **Prompt**: Union all items on stack  
  **Output**:
  ```python
  .union()
  ```

- **Prompt**: Union current solid with another solid  
  **Output**:
  ```python
  .union(otherSolid)
  ```

**Rule**: Use to combine all items on the stack into a single object.

**Method**:
```python
.combine([clean=True, glue=True, tol=1e-6])
```

**Allowed values**:
- clean: Optional boolean
- glue: Optional boolean
- tol: Optional tolerance

**Examples**:
- **Prompt**: Combine all solids on stack into one  
  **Output**:
  ```python
  .combine()
  ```

**Rule**: Use to get the intersection of the current solid and another solid.

**Method**:
```python
.intersect(toIntersect[, clean=True, tol=1e-6])
```

**Allowed values**:
- toIntersect: Solid to intersect with
- clean: Optional boolean
- tol: Optional tolerance

**Examples**:
- **Prompt**: Intersect current solid with cylinder  
  **Output**:
  ```python
  .intersect(cylinder)
  ```

**Rule**: Use to create a lofted solid through a sequence of wires or profiles.

**Method**:
```python
.loft([ruled=False, combine=True, clean=True])
```

**Allowed values**:
- ruled: Optional boolean for ruled loft
- combine: Optional boolean
- clean: Optional boolean

**Examples**:
- **Prompt**: Create lofted solid through sketches  
  **Output**:
  ```python
  .loft()
  ```

**Rule**: Use to sweep profile(s) along a path to create a solid.

**Method**:
```python
.sweep(path[, multisection=True, ...])
```

**Allowed values**:
- path: Path to sweep along
- multisection: Optional boolean

**Examples**:
- **Prompt**: Sweep profile along path curve  
  **Output**:
  ```python
  .sweep(path)
  ```

**Rule**: Use to extrude and twist a wire by a specified angle over extrusion length.

**Method**:
```python
.twistExtrude(distance, angleDegrees)
```

**Allowed values**:
- distance: Extrusion length
- angleDegrees: Total twist angle over extrusion

**Examples**:
- **Prompt**: Twist extrude sketch 30 units length and 360 degrees  
  **Output**:
  ```python
  .twistExtrude(30, 360)
  ```

**Rule**: Use to revolve un-revolved wires around an axis to create a solid.

**Method**:
```python
.revolve([angleDegrees=360, axisStart=(0,0,0), axisEnd=(0,0,1)])
```

**Allowed values**:
- angleDegrees: Angle to revolve (default full 360)
- axisStart: Start point of axis
- axisEnd: End point of axis

**Examples**:
- **Prompt**: Revolve profile 360 degrees around Z axis  
  **Output**:
  ```python
  .revolve()
  ```

- **Prompt**: Revolve profile 180 degrees around custom axis  
  **Output**:
  ```python
  .revolve(180, (0,0,0), (1,0,0))
  ```

**Rule**: Use to hollow out a solid by removing faces to create a shell with specified wall thickness.

**Method**:
```python
.shell(thickness[, kind='default'])
```

**Allowed values**:
- thickness: Wall thickness (positive float)
- kind: Optional shell kind or mode (e.g., 'default')

**Examples**:
- **Prompt**: Create a shell with thickness 2mm  
  **Output**:
  ```python
  .shell(2)
  ```

**Rule**: Use to fillet (round) edges of a solid with specified radius.

**Method**:
```python
.fillet(radius)
```

**Allowed values**:
- radius: Radius of fillet (float)

**Examples**:
- **Prompt**: Fillet edges with radius 3mm  
  **Output**:
  ```python
  .fillet(3)
  ```

**Rule**: Use to chamfer (bevel) edges of a solid with specified length(s).

**Method**:
```python
.chamfer(length[, length2=None])
```

**Allowed values**:
- length: Length of chamfer (float)
- length2: Optional second length for asymmetric chamfer

**Examples**:
- **Prompt**: Chamfer edges with length 2mm  
  **Output**:
  ```python
  .chamfer(2)
  ```

- **Prompt**: Chamfer edges with lengths 2mm and 3mm  
  **Output**:
  ```python
  .chamfer(2, 3)
  ```

**Rule**: Use to split a solid on the stack into parts.

**Method**:
```python
.split()
```

**Examples**:
- **Prompt**: Split the solid into parts  
  **Output**:
  ```python
  .split()
  ```

**Rule**: Use to rotate all items on the stack by a specified angle around an axis.

**Method**:
```python
.rotate(axisStartPoint, axisDirection, angleDegrees)
```

**Allowed values**:
- axisStartPoint: Vector or tuple representing start point of axis
- axisDirection: Vector or tuple representing axis direction
- angleDegrees: Angle in degrees (float)

**Examples**:
- **Prompt**: Rotate 45 degrees around Z axis at origin  
  **Output**:
  ```python
  .rotate((0,0,0), (0,0,1), 45)
  ```

**Rule**: Use to rotate all items on the stack by a specified angle about the specified axis going through the center.

**Method**:
```python
.rotateAboutCenter(axisEndPoint, angleDegrees)
```

**Allowed values**:
- axisEndPoint: Vector or tuple representing axis direction
- angleDegrees: Angle in degrees (float)

**Examples**:
- **Prompt**: Rotate 90 degrees about X axis through center  
  **Output**:
  ```python
  .rotateAboutCenter((1,0,0), 90)
  ```

**Rule**: Use to translate (move) all items on the stack by the specified vector.

**Method**:
```python
.translate(vec)
```

**Allowed values**:
- vec: Vector or tuple representing translation vector (x, y, z)

**Examples**:
- **Prompt**: Translate all items by (5, 0, 0)  
  **Output**:
  ```python
  .translate((5, 0, 0))
  ```

**Rule**: Use to mirror a CQ object around a given plane or default plane.

**Method**:
```python
.mirror([mirrorPlane=None])
```

**Allowed values**:
- mirrorPlane: Optional plane (string or object), e.g., "XY", "YZ", or custom plane

**Examples**:
- **Prompt**: Mirror object about YZ plane  
  **Output**:
  ```python
  .mirror("YZ")
  ```

- **Prompt**: Mirror object about default plane  
  **Output**:
  ```python
  .mirror()
  ```



# Import and Export

For file handling, imports and exports

**Rule**: Use to get SVG text representation of the first item on the workplane stack.

**Method**:
```python
.toSvg([opts=None])
```

**Allowed values**:
- opts: Optional dictionary of SVG export options (e.g., scale, color)

**Examples**:
- **Prompt**: Get SVG text of the current sketch  
  **Output**:
  ```python
  .toSvg()
  ```

**Rule**: Use to export the first item on the stack as an SVG file.

**Method**:
```python
.exportSvg(fileName)
```

**Allowed values**:
- fileName: String path and name of the SVG file to export

**Examples**:
- **Prompt**: Export current sketch as "output.svg"  
  **Output**:
  ```python
  .exportSvg("output.svg")
  ```

**Rule**: Use to import a STEP file as a CadQuery Workplane object.

**Method**:
```python
importers.importStep(fileName)
```

**Allowed values**:
- fileName: String path to the STEP file

**Examples**:
- **Prompt**: Import STEP file "part.step"  
  **Output**:
  ```python
  importers.importStep("part.step")
  ```

**Rule**: Use to import a DXF file into a CadQuery Workplane.

**Method**:
```python
importers.importDXF(fileName[, tol=1e-5, ...])
```

**Allowed values**:
- fileName: String path to the DXF file
- tol: Optional tolerance for import

**Examples**:
- **Prompt**: Import DXF file "sketch.dxf"  
  **Output**:
  ```python
  importers.importDXF("sketch.dxf")
  ```

**Rule**: Use to export a CadQuery Workplane or Shape to a file.

**Method**:
```python
exporters.export(w, fname[, exportType='STEP', ...])
```

**Allowed values**:
- w: Workplane or Shape object
- fname: Filename to export to
- exportType: Optional export format string (e.g., 'STEP', 'STL', 'DXF')

**Examples**:
- **Prompt**: Export workplane to "part.stp" as STEP file  
  **Output**:
  ```python
  exporters.export(w, "part.stp", exportType='STEP')
  ```

**Rule**: Use to create a DXF document from CadQuery objects for advanced DXF export.

**Method**:
```python
occ_impl.exporters.dxf.DxfDocument([...])
```

**Allowed values**:
- List of CadQuery objects to add to DXF document

**Examples**:
- **Prompt**: Create a DXF document from multiple shapes  
  **Output**:
  ```python
  dxfDoc = occ_impl.exporters.dxf.DxfDocument([shape1, shape2])
  ```

# Selector string modifiers

Special selectors and modifiers used in CadQuery to filter and select faces, edges, or vertices based on their geometric orientation or properties relative to coordinate directions. These selectors allow targeting specific parts of a 3D model efficiently by specifying directions such as parallel, perpendicular, positive/negative axes, or extremal positions (max/min). They also include selectors based on the type of curve or surface.

**Rule**: Use to select faces or edges parallel to a given direction.

**Method**:
```python
.faces("Parallel to direction") or using ParallelDirSelector
```

**Allowed values**:
- ParallelDirSelector: Selector that filters parallel direction faces or edges

**Examples**:
- **Prompt**: Select faces parallel to the X axis  
  **Output**:
  ```python
  .faces("|X")
  ```

**Rule**: Use to select faces or edges perpendicular to a given direction.

**Method**:
```python
.faces("Perpendicular to direction") or using PerpendicularDirSelector
```

**Allowed values**:
- PerpendicularDirSelector: Selector that filters perpendicular direction faces or edges

**Examples**:
- **Prompt**: Select faces perpendicular to the Y axis  
  **Output**:
  ```python
  .faces("#Y")
  ```

**Rule**: Use to select faces or edges in positive or negative direction along an axis.

**Method**:
```python
.faces("+X"), .faces("-Z"), or using DirectionSelector with +/- sign
```

**Allowed values**:
- + : Positive direction
- - : Negative direction

**Examples**:
- **Prompt**: Select faces in positive Z direction  
  **Output**:
  ```python
  .faces("+Z")
  ```

- **Prompt**: Select faces in negative X direction  
  **Output**:
  ```python
  .faces("-X")
  ```

**Rule**: Use to select faces or edges that are at maximum or minimum extent along a given axis.

**Method**:
```python
.faces(">Z") for max, .faces("<X") for min using DirectionMinMaxSelector
```

**Allowed values**:
- > : Maximum extent
- < : Minimum extent

**Examples**:
- **Prompt**: Select the top face (max in Z direction)  
  **Output**:
  ```python
  .faces(">Z")
  ```

- **Prompt**: Select the leftmost face (min in X direction)  
  **Output**:
  ```python
  .faces("<X")
  ```

**Rule**: Use to select faces or edges by curve or surface type.

**Method**:
```python
.faces("%type") using TypeSelector
```

**Allowed values**:
- % : Specifies curve or surface type selector

**Examples**:
- **Prompt**: Select all faces of a certain curve/surface type  
  **Output**:
  ```python
  .faces("%")
  ```

# Selector Methods

To select different geometric elements—faces, edges, vertices, solids, and shells—within a CadQuery model.

**Rule**: Select faces from the current workplane or object matching the given selector.

**Method**:
```python
.faces(selector)
```

**Allowed values**:
- selector: String or callable defining selection criteria (e.g., ">Z", "not |Z")

**Examples**:
- **Prompt**: Select the top face (max Z)  
  **Output**:
  ```python
  .faces(">Z")
  ```

**Rule**: Select edges matching the given selector.

**Method**:
```python
.edges(selector)
```

**Allowed values**:
- selector: String or callable to filter edges

**Examples**:
- **Prompt**: Select all edges parallel to X axis  
  **Output**:
  ```python
  .edges("|X")
  ```

**Rule**: Select vertices matching the given selector.

**Method**:
```python
.vertices(selector)
```

**Allowed values**:
- selector: String or callable to filter vertices

**Examples**:
- **Prompt**: Select vertices at minimum X  
  **Output**:
  ```python
  .vertices("<X")
  ```

**Rule**: Select solids matching the given selector (useful when multiple solids exist).

**Method**:
```python
.solids(selector)
```

**Allowed values**:
- selector: String or callable to filter solids

**Examples**:
- **Prompt**: Select all solids  
  **Output**:
  ```python
  .solids()
  ```

**Rule**: Select shells matching the given selector.

**Method**:
```python
.shells(selector)
```

**Allowed values**:
- selector: String or callable to filter shells

**Examples**:
- **Prompt**: Select shells with certain property  
  **Output**:
  ```python
  .shells()
  ```