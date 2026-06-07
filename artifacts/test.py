
import math
import cadquery as cq

# All dimensions are in mm

finger_name = "robotic_finger_kinematic_assembly"

link_width = 18.0
link_thickness = 8.0

proximal_length = 52.0
middle_length = 42.0
distal_length = 32.0

joint_pin_diameter = 5.0
joint_bushing_diameter = 8.5
joint_washer_diameter = 12.0
joint_clearance = 0.35

mount_length = 42.0
mount_width = 36.0
mount_height = 18.0

clevis_plate_thickness = 4.0
clevis_plate_gap = link_width + 1.2
clevis_length = 20.0
clevis_height = 18.0

pin_overhang = 5.0
washer_thickness = 1.2
bushing_length = link_width + 0.8

pulley_diameter = 11.0
pulley_width = 4.0
tendon_diameter = 1.6

screw_diameter = 3.2
screw_head_diameter = 6.2
screw_head_height = 2.2

small_chamfer = 0.45

proximal_angle = 22.0
middle_angle = 34.0
distal_angle = 26.0

CUT_EPS = 0.2


def safe_fillet(obj, selector, radius):
    try:
        return obj.edges(selector).fillet(radius)
    except Exception:
        return obj


def safe_chamfer(obj, selector, amount):
    try:
        return obj.edges(selector).chamfer(amount)
    except Exception:
        return obj


def make_y_cylindrical_cutter(x, y_center, z, diameter, depth):
    return (
        cq.Workplane("XZ")
        .center(x, z)
        .circle(diameter / 2)
        .extrude(depth)
        .translate((0, y_center - depth / 2, 0))
    )


def cut_through_hole_y(body, x, z, y_min, y_max, diameter):
    depth = (y_max - y_min) + 2 * CUT_EPS
    y_center = (y_max + y_min) / 2
    cutter = make_y_cylindrical_cutter(x, y_center, z, diameter, depth)
    return body.cut(cutter)


def rotate_xz(x, z, angle_deg):
    a = math.radians(angle_deg)
    return (
        x * math.cos(a) + z * math.sin(a),
        -x * math.sin(a) + z * math.cos(a),
    )


def add_vec(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def loc_y_rotation_at(point, angle_deg):
    return cq.Location(cq.Vector(*point), cq.Vector(0, 1, 0), angle_deg)


def loc_with_local_anchor_at_target(local_anchor_x, local_anchor_z, target, angle_deg):
    rx, rz = rotate_xz(local_anchor_x, local_anchor_z, angle_deg)
    return cq.Location(
        cq.Vector(target[0] - rx, target[1], target[2] - rz),
        cq.Vector(0, 1, 0),
        angle_deg,
    )


def make_rounded_box(length, width, height, fillet_radius=1.2):
    part = cq.Workplane("XY").box(length, width, height)
    part = safe_fillet(part, "|Z", fillet_radius)
    part = safe_chamfer(part, ">Z or <Z", small_chamfer)
    return part


def make_cap_screw(length=8.0):
    shank = cq.Workplane("XY").cylinder(length, screw_diameter / 2)

    head = (
        cq.Workplane("XY")
        .workplane(offset=length / 2 + screw_head_height / 2)
        .cylinder(screw_head_height, screw_head_diameter / 2)
    )
    head = safe_chamfer(head, ">Z or <Z", 0.25)

    socket = (
        cq.Workplane("XY")
        .workplane(offset=length / 2 + screw_head_height + CUT_EPS)
        .polygon(6, 2.0)
        .extrude(-(screw_head_height * 0.65 + CUT_EPS))
    )

    return shank.union(head).cut(socket)


def make_pin(length):
    pin = cq.Workplane("XY").cylinder(length, joint_pin_diameter / 2)
    return safe_chamfer(pin, ">Z or <Z", 0.4)


def make_washer():
    washer = cq.Workplane("XY").cylinder(washer_thickness, joint_washer_diameter / 2)
    bore = cq.Workplane("XY").cylinder(
        washer_thickness + CUT_EPS,
        (joint_pin_diameter + joint_clearance) / 2,
    )
    washer = washer.cut(bore)
    return safe_chamfer(washer, ">Z or <Z", 0.25)


def make_bushing():
    bushing = cq.Workplane("XY").cylinder(bushing_length, joint_bushing_diameter / 2)
    bore = cq.Workplane("XY").cylinder(
        bushing_length + CUT_EPS,
        (joint_pin_diameter + joint_clearance) / 2,
    )
    bushing = bushing.cut(bore)
    return safe_chamfer(bushing, ">Z or <Z", 0.3)


def make_pulley():
    pulley = cq.Workplane("XY").cylinder(pulley_width, pulley_diameter / 2)

    bore = cq.Workplane("XY").cylinder(
        pulley_width + CUT_EPS,
        (joint_pin_diameter + joint_clearance) / 2,
    )

    groove_outer = cq.Workplane("XY").cylinder(
        pulley_width + 2 * CUT_EPS,
        pulley_diameter / 2 + 0.05,
    )
    groove_inner = cq.Workplane("XY").cylinder(
        pulley_width + 3 * CUT_EPS,
        pulley_diameter / 2 - tendon_diameter * 0.55,
    )
    groove = groove_outer.cut(groove_inner)

    pulley = pulley.cut(bore).cut(groove)
    return safe_chamfer(pulley, ">Z or <Z", 0.25)


def make_mount_block():
    block = make_rounded_box(mount_length, mount_width, mount_height, 2.0)

    for x in [-mount_length / 2 + 10, mount_length / 2 - 10]:
        for y in [-mount_width / 2 + 8, mount_width / 2 - 8]:
            block = (
                block.faces(">Z")
                .workplane()
                .center(x, y)
                .cboreHole(
                    screw_diameter,
                    screw_head_diameter,
                    screw_head_height + 0.4,
                    depth=mount_height + CUT_EPS,
                )
            )

    rear_support = (
        cq.Workplane("XY")
        .box(8.0, clevis_plate_gap + 2 * clevis_plate_thickness + 4.0, 28.0)
        .translate((-mount_length / 2 + 4.0, 0, mount_height / 2 + 10.0))
    )
    rear_support = safe_fillet(rear_support, "|Z", 1.0)

    return block.union(rear_support)


def make_phalanx_link(length):
    body = (
        cq.Workplane("XZ")
        .center(length / 2, 0)
        .slot2D(length, link_thickness)
        .extrude(link_width)
        .translate((0, -link_width / 2, 0))
    )
    body = safe_chamfer(body, ">Y or <Y", small_chamfer)

    for x in [0, length]:
        body = cut_through_hole_y(
            body,
            x=x,
            z=0,
            y_min=-link_width / 2,
            y_max=link_width / 2,
            diameter=joint_bushing_diameter + joint_clearance,
        )

    tendon_channel = (
        cq.Workplane("XZ")
        .center(length / 2, link_thickness / 2 + 0.1)
        .slot2D(length * 0.62, tendon_diameter * 2.4)
        .extrude(link_width + CUT_EPS)
        .translate((0, -link_width / 2 - CUT_EPS / 2, 0))
    )
    body = body.cut(tendon_channel)

    for x in [length * 0.30, length * 0.70]:
        body = cut_through_hole_y(
            body,
            x=x,
            z=0,
            y_min=-link_width / 2,
            y_max=link_width / 2,
            diameter=screw_diameter,
        )

    return body


def make_clevis_joint():
    plate_y = clevis_plate_gap / 2 + clevis_plate_thickness / 2

    plate = (
        cq.Workplane("XZ")
        .center(clevis_length / 2, 0)
        .slot2D(clevis_length, clevis_height)
        .extrude(clevis_plate_thickness)
        .translate((0, plate_y - clevis_plate_thickness / 2, 0))
    )
    plate = safe_chamfer(plate, ">Y or <Y", 0.35)

    left_plate = plate
    right_plate = plate.mirror("XZ")

    bridge = (
        cq.Workplane("XY")
        .box(8.0, clevis_plate_gap + 2 * clevis_plate_thickness, clevis_height * 0.72)
        .translate((-4.0, 0, 0))
    )
    bridge = safe_fillet(bridge, "|Z", 0.8)

    clevis = left_plate.union(right_plate).union(bridge)

    clevis = cut_through_hole_y(
        clevis,
        x=clevis_length,
        z=0,
        y_min=-(clevis_plate_gap / 2 + clevis_plate_thickness),
        y_max=(clevis_plate_gap / 2 + clevis_plate_thickness),
        diameter=joint_pin_diameter + joint_clearance,
    )

    return clevis


def make_fingertip_pad():
    pad = (
        cq.Workplane("XZ")
        .center(distal_length, -link_thickness / 2 - 2.3)
        .slot2D(18.0, 6.5)
        .extrude(link_width + 1.0)
        .translate((0, -(link_width + 1.0) / 2, 0))
    )
    return safe_fillet(pad, "|Y", 1.4)


def make_tendon_cable(points):
    cable = None

    for a, b in zip(points[:-1], points[1:]):
        ax, ay, az = a
        bx, by, bz = b

        dx = bx - ax
        dz = bz - az
        length = math.sqrt(dx * dx + dz * dz)

        if length <= 0.001:
            continue

        angle = math.degrees(math.atan2(dz, dx))

        segment = (
            cq.Workplane("YZ")
            .circle(tendon_diameter / 2)
            .extrude(length)
            .rotate((0, 0, 0), (0, 1, 0), -angle)
            .translate((ax, ay, az))
        )

        cable = segment if cable is None else cable.union(segment)

    return cable


base_joint = (0.0, 0.0, mount_height / 2 + 12.0)

angle_1 = proximal_angle
angle_2 = proximal_angle + middle_angle
angle_3 = proximal_angle + middle_angle + distal_angle

p1_dx, p1_dz = rotate_xz(proximal_length, 0, angle_1)
joint_1 = add_vec(base_joint, (p1_dx, 0.0, p1_dz))

p2_dx, p2_dz = rotate_xz(middle_length, 0, angle_2)
joint_2 = add_vec(joint_1, (p2_dx, 0.0, p2_dz))

p3_dx, p3_dz = rotate_xz(distal_length, 0, angle_3)
tip_point = add_vec(joint_2, (p3_dx, 0.0, p3_dz))

assembly = cq.Assembly(name=finger_name)

aluminum = cq.Color(0.68, 0.72, 0.76, 1.0)
dark_steel = cq.Color(0.08, 0.085, 0.09, 1.0)
brass = cq.Color(0.86, 0.62, 0.24, 1.0)
black_polymer = cq.Color(0.01, 0.012, 0.014, 1.0)
blue_cable = cq.Color(0.0, 0.18, 0.8, 1.0)

mount = make_mount_block()
proximal = make_phalanx_link(proximal_length)
middle = make_phalanx_link(middle_length)
distal = make_phalanx_link(distal_length)

base_clevis = make_clevis_joint()
proximal_clevis = make_clevis_joint()
middle_clevis = make_clevis_joint()

pin_length = clevis_plate_gap + 2 * clevis_plate_thickness + 2 * pin_overhang

pin = make_pin(pin_length)
washer = make_washer()
bushing = make_bushing()
pulley = make_pulley()
screw = make_cap_screw(8.0)
pad = make_fingertip_pad()

assembly.add(mount, name="palm_mount_block", color=aluminum)

assembly.add(
    base_clevis,
    name="base_clevis_bracket",
    loc=loc_with_local_anchor_at_target(clevis_length, 0, base_joint, 0),
    color=aluminum,
)

assembly.add(
    proximal,
    name="proximal_phalanx_link",
    loc=loc_y_rotation_at(base_joint, angle_1),
    color=aluminum,
)

assembly.add(
    proximal_clevis,
    name="proximal_output_clevis",
    loc=loc_with_local_anchor_at_target(clevis_length, 0, joint_1, angle_1),
    color=aluminum,
)

assembly.add(
    middle,
    name="middle_phalanx_link",
    loc=loc_y_rotation_at(joint_1, angle_2),
    color=aluminum,
)

assembly.add(
    middle_clevis,
    name="middle_output_clevis",
    loc=loc_with_local_anchor_at_target(clevis_length, 0, joint_2, angle_2),
    color=aluminum,
)

assembly.add(
    distal,
    name="distal_phalanx_link",
    loc=loc_y_rotation_at(joint_2, angle_3),
    color=aluminum,
)

assembly.add(
    pad,
    name="black_polymer_fingertip_pad",
    loc=loc_y_rotation_at(joint_2, angle_3),
    color=black_polymer,
)

joint_points = [base_joint, joint_1, joint_2]

for i, joint in enumerate(joint_points):
    assembly.add(
        pin,
        name=f"joint_{i}_dark_steel_pin",
        loc=cq.Location(cq.Vector(*joint), cq.Vector(1, 0, 0), 90),
        color=dark_steel,
    )

    assembly.add(
        bushing,
        name=f"joint_{i}_brass_bushing",
        loc=cq.Location(cq.Vector(*joint), cq.Vector(1, 0, 0), 90),
        color=brass,
    )

    y_outer = clevis_plate_gap / 2 + clevis_plate_thickness + washer_thickness / 2

    assembly.add(
        washer,
        name=f"joint_{i}_left_washer",
        loc=cq.Location(cq.Vector(joint[0], y_outer, joint[2]), cq.Vector(1, 0, 0), 90),
        color=dark_steel,
    )

    assembly.add(
        washer,
        name=f"joint_{i}_right_washer",
        loc=cq.Location(cq.Vector(joint[0], -y_outer, joint[2]), cq.Vector(1, 0, 0), 90),
        color=dark_steel,
    )

    assembly.add(
        pulley,
        name=f"joint_{i}_tendon_guide_pulley",
        loc=cq.Location(
            cq.Vector(joint[0], 0.0, joint[2] + link_thickness / 2 + 3.5),
            cq.Vector(1, 0, 0),
            90,
        ),
        color=black_polymer,
    )

for x, y in [(-12, -10), (12, -10), (-12, 10), (12, 10)]:
    assembly.add(
        screw,
        name=f"mount_cap_screw_{x}_{y}",
        loc=cq.Location(cq.Vector(x, y, mount_height / 2 + 0.5)),
        color=dark_steel,
    )

for i, joint in enumerate(joint_points):
    screw_y = clevis_plate_gap / 2 + clevis_plate_thickness + pin_overhang + 0.6

    assembly.add(
        screw,
        name=f"joint_{i}_pin_end_screw_left",
        loc=cq.Location(
            cq.Vector(joint[0], screw_y, joint[2]),
            cq.Vector(1, 0, 0),
            90,
        ),
        color=dark_steel,
    )

    assembly.add(
        screw,
        name=f"joint_{i}_pin_end_screw_right",
        loc=cq.Location(
            cq.Vector(joint[0], -screw_y, joint[2]),
            cq.Vector(1, 0, 0),
            -90,
        ),
        color=dark_steel,
    )

tendon_points = [
    (base_joint[0] - 18.0, 0.0, base_joint[2] + link_thickness / 2 + 3.5),
    (base_joint[0], 0.0, base_joint[2] + link_thickness / 2 + 3.5),
    (joint_1[0], 0.0, joint_1[2] + link_thickness / 2 + 3.5),
    (joint_2[0], 0.0, joint_2[2] + link_thickness / 2 + 3.5),
    (tip_point[0] - 6.0, 0.0, tip_point[2] + link_thickness / 2 + 1.0),
]

tendon = make_tendon_cable(tendon_points)
assembly.add(tendon, name="blue_synthetic_tendon_cable", color=blue_cable)

try:
    show_object(assembly)
except NameError:
    assembly.save(f"{finger_name}.step")
