import cadquery as cq
import math
import os
from cadquery import exporters

COMPONENT_NAME = "adjustable_phone_tablet_stand"

BASE_PLATE_W = 170.0
BASE_PLATE_D = 170.0
BASE_PLATE_T = 10.0
BASE_BOLT_N = 4.0
BASE_BOLT_R = 65.0
M6_CLEARANCE_D = 6.6
ALIGN_PIN_N = 2.0
ALIGN_PIN_D = 8.0
ALIGN_PIN_H = 6.0
COLUMN_W = 40.0
COLUMN_D = 40.0
COLUMN_H = 400.0
COLUMN_WALL_T = 3.0
JOINT_BOSS_D = 18.0
JOINT_BOSS_L = 20.0
JOINT_PIN_D = 8.0
JOINT_PIN_L = 44.0
JOINT_CLEARANCE = 0.3
LOWER_ARM_L = 170.0
LOWER_ARM_W = 30.0
LOWER_ARM_H = 20.0
UPPER_ARM_L = 170.0
UPPER_ARM_W = 30.0
UPPER_ARM_H = 20.0
TILT_PIN_D = 8.0
TILT_PIN_L = 44.0
TILT_BOSS_L = 20.0
HOLDER_W = 120.0
HOLDER_H = 40.0
HOLDER_T = 15.0
JAW_SLOT_W = 12.0
JAW_SLOT_L = 30.0
JAW_W = 10.0
JAW_L = 28.0
JAW_H = 40.0
JAW_OFFSET_X = 40.0
JAW_PAD_W = 20.0
JAW_PAD_H = 30.0
JAW_PAD_T = 4.0
JAW_PIN_D = 5.0
JAW_PIN_L = 12.0
SPRING_D = 8.0
SPRING_L = 30.0

CUT_EPS = 0.2
EDGE_CHAMFER = 1.0
ARM_BORE_D = JOINT_PIN_D + JOINT_CLEARANCE
TILT_BORE_D = TILT_PIN_D + JOINT_CLEARANCE
ALIGN_PIN_OFFSET_X = 12.0
ALIGN_PIN_OFFSET_Y = 0.0
COLUMN_TOP_Z = COLUMN_H
BASE_TOP_Z = BASE_PLATE_T
COLUMN_WORLD_CENTER_Z = COLUMN_H / 2.0
LOWER_ARM_WORLD_CENTER_Z = COLUMN_H
UPPER_ARM_WORLD_CENTER_Z = COLUMN_H + LOWER_ARM_L
HOLDER_WORLD_CENTER_Z = COLUMN_H + LOWER_ARM_L + UPPER_ARM_L
HOLDER_SLOT_CENTER_Z = HOLDER_H / 2.0
HOLDER_SLOT_CENTER_Y = (HOLDER_T - JAW_SLOT_L) / 2.0
JAW_BORE_Z = JAW_H / 2.0
JAW_PAD_Z = JAW_H / 2.0
FASTENER_BODY_D = 6.0
FASTENER_BODY_L = BASE_PLATE_T + 16.0

BUILD_MANIFEST = {
    "component": COMPONENT_NAME,
    "artifact_type": "assembly",
    "features": [
        {
            "id": "base_bolt_pattern",
            "host_part": "base_plate",
            "type": "pattern",
            "operation": "cut",
            "axis": "Z",
            "center_mm": [0.0, 0.0, BASE_PLATE_T / 2.0],
            "dimensions_mm": {
                "count": int(BASE_BOLT_N),
                "diameter": M6_CLEARANCE_D,
                "pattern_radius": BASE_BOLT_R,
                "depth": BASE_PLATE_T + 2 * CUT_EPS,
            },
            "count_group": "base_bolt_pattern",
            "required": True,
        },
        {
            "id": "base_alignment_pins",
            "host_part": "base_plate",
            "type": "boss",
            "operation": "add",
            "axis": "Z",
            "center_mm": [0.0, 0.0, BASE_PLATE_T + ALIGN_PIN_H / 2.0],
            "dimensions_mm": {
                "count": int(ALIGN_PIN_N),
                "diameter": ALIGN_PIN_D,
                "height": ALIGN_PIN_H,
                "offset_x": ALIGN_PIN_OFFSET_X,
                "offset_y": ALIGN_PIN_OFFSET_Y,
            },
            "count_group": "base_alignment_pins",
            "required": True,
        },
        {
            "id": "column_base_mount_bore",
            "host_part": "vertical_support_column",
            "type": "bore",
            "operation": "cut",
            "axis": "Z",
            "center_mm": [0.0, 0.0, ALIGN_PIN_H / 2.0],
            "dimensions_mm": {
                "diameter": ALIGN_PIN_D,
                "depth": ALIGN_PIN_H,
                "count": int(ALIGN_PIN_N),
                "offset_x": ALIGN_PIN_OFFSET_X,
                "offset_y": ALIGN_PIN_OFFSET_Y,
            },
            "count_group": "base_alignment_pins",
            "required": True,
        },
        {
            "id": "column_lower_arm_joint_boss",
            "host_part": "vertical_support_column",
            "type": "boss",
            "operation": "add",
            "axis": "Y",
            "center_mm": [0.0, 0.0, COLUMN_TOP_Z],
            "dimensions_mm": {
                "diameter": JOINT_BOSS_D,
                "length": JOINT_BOSS_L,
            },
            "count_group": "column_lower_arm_joint",
            "required": True,
        },
        {
            "id": "lower_arm_base_joint_bore",
            "host_part": "lower_arm_segment",
            "type": "bore",
            "operation": "cut",
            "axis": "Y",
            "center_mm": [0.0, 0.0, 0.0],
            "dimensions_mm": {
                "diameter": ARM_BORE_D,
                "depth": JOINT_BOSS_L,
            },
            "count_group": "column_lower_arm_joint",
            "required": True,
        },
        {
            "id": "lower_arm_upper_joint_bore",
            "host_part": "lower_arm_segment",
            "type": "bore",
            "operation": "cut",
            "axis": "Y",
            "center_mm": [0.0, 0.0, LOWER_ARM_L],
            "dimensions_mm": {
                "diameter": ARM_BORE_D,
                "depth": JOINT_BOSS_L,
            },
            "count_group": "lower_upper_arm_joint",
            "required": True,
        },
        {
            "id": "upper_arm_lower_joint_bore",
            "host_part": "upper_arm_segment",
            "type": "bore",
            "operation": "cut",
            "axis": "Y",
            "center_mm": [0.0, 0.0, 0.0],
            "dimensions_mm": {
                "diameter": ARM_BORE_D,
                "depth": JOINT_BOSS_L,
            },
            "count_group": "lower_upper_arm_joint",
            "required": True,
        },
        {
            "id": "upper_arm_holder_joint_bore",
            "host_part": "upper_arm_segment",
            "type": "bore",
            "operation": "cut",
            "axis": "Y",
            "center_mm": [0.0, 0.0, UPPER_ARM_L],
            "dimensions_mm": {
                "diameter": TILT_BORE_D,
                "depth": TILT_BOSS_L,
            },
            "count_group": "upper_arm_holder_joint",
            "required": True,
        },
        {
            "id": "arm_hinge_joint_pins",
            "host_part": "arm_hinge_joints",
            "type": "fastener",
            "operation": "add",
            "axis": "Y",
            "center_mm": [0.0, 0.0, COLUMN_H + LOWER_ARM_L / 2.0],
            "dimensions_mm": {
                "count": 2,
                "diameter": JOINT_PIN_D,
                "length": JOINT_PIN_L,
            },
            "count_group": "arm_hinge_joints",
            "required": True,
        },
        {
            "id": "holder_tilt_joint_pin",
            "host_part": "holder_tilt_joint",
            "type": "fastener",
            "operation": "add",
            "axis": "Y",
            "center_mm": [0.0, 0.0, 0.0],
            "dimensions_mm": {
                "diameter": TILT_PIN_D,
                "length": TILT_PIN_L,
            },
            "count_group": "holder_tilt_joint",
            "required": True,
        },
        {
            "id": "holder_tilt_joint_bore",
            "host_part": "device_holder",
            "type": "bore",
            "operation": "cut",
            "axis": "Y",
            "center_mm": [0.0, 0.0, 0.0],
            "dimensions_mm": {
                "diameter": TILT_BORE_D,
                "depth": TILT_BOSS_L,
            },
            "count_group": "holder_tilt_joint",
            "required": True,
        },
        {
            "id": "holder_jaw_slots",
            "host_part": "device_holder",
            "type": "slot",
            "operation": "cut",
            "axis": "X",
            "center_mm": [0.0, HOLDER_SLOT_CENTER_Y, HOLDER_SLOT_CENTER_Z],
            "dimensions_mm": {
                "count": 2,
                "width": JAW_SLOT_W,
                "length": JAW_SLOT_L,
                "offset_x": JAW_OFFSET_X,
                "depth": HOLDER_T,
            },
            "count_group": "holder_jaw_slots",
            "required": True,
        },
        {
            "id": "jaw_contact_pads",
            "host_part": "device_gripper_jaws",
            "type": "pad",
            "operation": "add",
            "axis": "Y",
            "center_mm": [0.0, JAW_L + JAW_PAD_T / 2.0, JAW_PAD_Z],
            "dimensions_mm": {
                "count": 2,
                "width": JAW_PAD_W,
                "height": JAW_PAD_H,
                "thickness": JAW_PAD_T,
            },
            "count_group": "jaw_contact_pads",
            "required": True,
        },
        {
            "id": "jaw_slide_or_pivot_bores",
            "host_part": "device_gripper_jaws",
            "type": "bore",
            "operation": "cut",
            "axis": "X",
            "center_mm": [0.0, JAW_L / 2.0, JAW_BORE_Z],
            "dimensions_mm": {
                "diameter": JAW_PIN_D,
                "depth": JAW_PIN_L,
                "count": 2,
            },
            "count_group": "jaw_slide_or_pivot_bores",
            "required": True,
        },
        {
            "id": "jaw_spring_or_screw_body",
            "host_part": "jaw_spring_or_screw",
            "type": "fastener",
            "operation": "add",
            "axis": "Y",
            "center_mm": [0.0, 0.0, HOLDER_WORLD_CENTER_Z + HOLDER_H / 2.0],
            "dimensions_mm": {
                "diameter": SPRING_D,
                "length": SPRING_L,
            },
            "count_group": "jaw_spring_or_screw",
            "required": True,
        },
        {
            "id": "fastener_bodies",
            "host_part": "fasteners",
            "type": "fastener",
            "operation": "add",
            "axis": None,
            "center_mm": [0.0, 0.0, BASE_PLATE_T / 2.0],
            "dimensions_mm": {
                "varies": 1.0,
                "count": int(BASE_BOLT_N),
                "body_diameter": FASTENER_BODY_D,
                "body_length": FASTENER_BODY_L,
            },
            "count_group": "all_fasteners",
            "required": True,
        },
    ],
    "part_frames": [
        {
            "part": "base_plate",
            "center_mm": [0.0, 0.0, BASE_PLATE_T / 2.0],
            "bbox_mm": [BASE_PLATE_W, BASE_PLATE_D, BASE_PLATE_T + ALIGN_PIN_H],
        },
        {
            "part": "vertical_support_column",
            "center_mm": [0.0, 0.0, COLUMN_WORLD_CENTER_Z],
            "bbox_mm": [COLUMN_W, COLUMN_D + JOINT_BOSS_L, COLUMN_H],
        },
        {
            "part": "lower_arm_segment",
            "center_mm": [0.0, 0.0, LOWER_ARM_WORLD_CENTER_Z + LOWER_ARM_L / 2.0],
            "bbox_mm": [LOWER_ARM_W, LOWER_ARM_W, LOWER_ARM_L + LOWER_ARM_H],
        },
        {
            "part": "upper_arm_segment",
            "center_mm": [0.0, 0.0, UPPER_ARM_WORLD_CENTER_Z + UPPER_ARM_L / 2.0],
            "bbox_mm": [UPPER_ARM_W, UPPER_ARM_W, UPPER_ARM_L + UPPER_ARM_H],
        },
        {
            "part": "device_holder",
            "center_mm": [0.0, 0.0, HOLDER_WORLD_CENTER_Z + HOLDER_H / 2.0],
            "bbox_mm": [HOLDER_W, HOLDER_T, HOLDER_H],
        },
        {
            "part": "jaw_left",
            "center_mm": [-JAW_OFFSET_X, HOLDER_SLOT_CENTER_Y + JAW_L / 2.0, HOLDER_WORLD_CENTER_Z + JAW_H / 2.0],
            "bbox_mm": [JAW_W, JAW_L + JAW_PAD_T, JAW_H],
        },
        {
            "part": "jaw_right",
            "center_mm": [JAW_OFFSET_X, HOLDER_SLOT_CENTER_Y + JAW_L / 2.0, HOLDER_WORLD_CENTER_Z + JAW_H / 2.0],
            "bbox_mm": [JAW_W, JAW_L + JAW_PAD_T, JAW_H],
        },
        {
            "part": "arm_hinge_pin_column_lower",
            "center_mm": [0.0, 0.0, COLUMN_H],
            "bbox_mm": [JOINT_PIN_D, JOINT_PIN_L, JOINT_PIN_D],
        },
        {
            "part": "arm_hinge_pin_lower_upper",
            "center_mm": [0.0, 0.0, COLUMN_H + LOWER_ARM_L],
            "bbox_mm": [JOINT_PIN_D, JOINT_PIN_L, JOINT_PIN_D],
        },
        {
            "part": "holder_tilt_joint",
            "center_mm": [0.0, 0.0, HOLDER_WORLD_CENTER_Z],
            "bbox_mm": [TILT_PIN_D, TILT_PIN_L, TILT_PIN_D],
        },
        {
            "part": "jaw_spring_or_screw",
            "center_mm": [0.0, 0.0, HOLDER_WORLD_CENTER_Z + HOLDER_H / 2.0],
            "bbox_mm": [SPRING_D, SPRING_L, SPRING_D],
        },
        {
            "part": "base_fastener_1",
            "center_mm": [BASE_BOLT_R, 0.0, BASE_PLATE_T / 2.0],
            "bbox_mm": [FASTENER_BODY_D, FASTENER_BODY_D, FASTENER_BODY_L],
        },
        {
            "part": "base_fastener_2",
            "center_mm": [0.0, BASE_BOLT_R, BASE_PLATE_T / 2.0],
            "bbox_mm": [FASTENER_BODY_D, FASTENER_BODY_D, FASTENER_BODY_L],
        },
        {
            "part": "base_fastener_3",
            "center_mm": [-BASE_BOLT_R, 0.0, BASE_PLATE_T / 2.0],
            "bbox_mm": [FASTENER_BODY_D, FASTENER_BODY_D, FASTENER_BODY_L],
        },
        {
            "part": "base_fastener_4",
            "center_mm": [0.0, -BASE_BOLT_R, BASE_PLATE_T / 2.0],
            "bbox_mm": [FASTENER_BODY_D, FASTENER_BODY_D, FASTENER_BODY_L],
        },
    ],
    "assembly_constraints": [
        {
            "id": "column_on_base_centered",
            "type": "centered",
            "parts": ["base_plate", "vertical_support_column"],
            "axes": ["X", "Y"],
            "feature_refs": ["base_alignment_pins", "column_base_mount_bore"],
            "target": "column and base share X/Y centerlines",
            "tolerance_mm": 0.25,
        },
        {
            "id": "column_lower_arm_joint_coaxial",
            "type": "coaxial",
            "parts": ["vertical_support_column", "lower_arm_segment", "arm_hinge_joints"],
            "axes": ["Y"],
            "feature_refs": ["column_lower_arm_joint_boss", "lower_arm_base_joint_bore", "arm_hinge_joint_pins"],
            "target": "joint axes are colinear",
            "tolerance_mm": 0.25,
        },
        {
            "id": "lower_upper_arm_joint_coaxial",
            "type": "coaxial",
            "parts": ["lower_arm_segment", "upper_arm_segment", "arm_hinge_joints"],
            "axes": ["Y"],
            "feature_refs": ["lower_arm_upper_joint_bore", "upper_arm_lower_joint_bore", "arm_hinge_joint_pins"],
            "target": "joint axes are colinear",
            "tolerance_mm": 0.25,
        },
        {
            "id": "upper_arm_holder_joint_coaxial",
            "type": "coaxial",
            "parts": ["upper_arm_segment", "device_holder", "holder_tilt_joint"],
            "axes": ["Y"],
            "feature_refs": ["upper_arm_holder_joint_bore", "holder_tilt_joint_bore", "holder_tilt_joint_pin"],
            "target": "joint axes are colinear",
            "tolerance_mm": 0.25,
        },
        {
            "id": "jaws_centered_in_holder_slots",
            "type": "centered",
            "parts": ["device_holder", "device_gripper_jaws"],
            "axes": ["X"],
            "feature_refs": ["holder_jaw_slots", "jaw_slide_or_pivot_bores"],
            "target": "jaws are symmetrically positioned in slots",
            "tolerance_mm": 0.25,
        },
    ],
}


def make_z_cylindrical_cutter(x: float, y: float, z_center: float, diameter: float, depth: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .center(x, y)
        .cylinder(depth, diameter / 2.0, centered=(True, True, True))
        .translate((0.0, 0.0, z_center))
    )


def cut_through_hole_z(body: cq.Workplane, x: float, y: float, bottom_z: float, top_z: float, diameter: float) -> cq.Workplane:
    depth = (top_z - bottom_z) + 2.0 * CUT_EPS
    z_center = (top_z + bottom_z) / 2.0
    cutter = make_z_cylindrical_cutter(x, y, z_center, diameter, depth)
    return body.cut(cutter)


def make_y_cylinder(diameter: float, length: float, x: float, y_center: float, z: float) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(
        diameter / 2.0,
        length,
        pnt=cq.Vector(x, y_center - length / 2.0, z),
        dir=cq.Vector(0.0, 1.0, 0.0),
    )
    return cq.Workplane("XZ").add(solid)


def make_x_cylinder(diameter: float, length: float, x_center: float, y: float, z: float) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(
        diameter / 2.0,
        length,
        pnt=cq.Vector(x_center - length / 2.0, y, z),
        dir=cq.Vector(1.0, 0.0, 0.0),
    )
    return cq.Workplane("YZ").add(solid)


def cut_through_hole_y(body: cq.Workplane, x: float, z: float, y_min: float, y_max: float, diameter: float) -> cq.Workplane:
    depth = (y_max - y_min) + 2.0 * CUT_EPS
    y_center = (y_min + y_max) / 2.0
    cutter = make_y_cylinder(diameter, depth, x, y_center, z)
    return body.cut(cutter)


def cut_through_hole_x(body: cq.Workplane, y: float, z: float, x_min: float, x_max: float, diameter: float) -> cq.Workplane:
    depth = (x_max - x_min) + 2.0 * CUT_EPS
    x_center = (x_min + x_max) / 2.0
    cutter = make_x_cylinder(diameter, depth, x_center, y, z)
    return body.cut(cutter)


def make_base_plate() -> cq.Workplane:
    plate = cq.Workplane("XY").box(BASE_PLATE_W, BASE_PLATE_D, BASE_PLATE_T, centered=(True, True, False))
    plate = plate.edges("|Z").chamfer(EDGE_CHAMFER)

    for angle_deg in [0.0, 90.0, 180.0, 270.0]:
        angle_rad = math.radians(angle_deg)
        x = BASE_BOLT_R * math.cos(angle_rad)
        y = BASE_BOLT_R * math.sin(angle_rad)
        plate = cut_through_hole_z(plate, x, y, 0.0, BASE_PLATE_T, M6_CLEARANCE_D)

    for x in (-ALIGN_PIN_OFFSET_X, ALIGN_PIN_OFFSET_X):
        pin = (
            cq.Workplane("XY")
            .center(x, ALIGN_PIN_OFFSET_Y)
            .circle(ALIGN_PIN_D / 2.0)
            .extrude(ALIGN_PIN_H)
            .translate((0.0, 0.0, BASE_PLATE_T))
        )
        plate = plate.union(pin)

    return plate.clean()


def make_vertical_support_column() -> cq.Workplane:
    outer = cq.Workplane("XY").box(COLUMN_W, COLUMN_D, COLUMN_H, centered=(True, True, False))
    inner_w = COLUMN_W - 2.0 * COLUMN_WALL_T
    inner_d = COLUMN_D - 2.0 * COLUMN_WALL_T
    inner_h = COLUMN_H - COLUMN_WALL_T

    if inner_w > 0.0 and inner_d > 0.0 and inner_h > 0.0:
        inner = (
            cq.Workplane("XY")
            .box(inner_w, inner_d, inner_h, centered=(True, True, False))
            .translate((0.0, 0.0, COLUMN_WALL_T))
        )
        column = outer.cut(inner)
    else:
        column = outer

    for x in (-ALIGN_PIN_OFFSET_X, ALIGN_PIN_OFFSET_X):
        bore = (
            cq.Workplane("XY")
            .center(x, ALIGN_PIN_OFFSET_Y)
            .circle(ALIGN_PIN_D / 2.0)
            .extrude(ALIGN_PIN_H + CUT_EPS)
        )
        column = column.cut(bore)

    boss = make_y_cylinder(JOINT_BOSS_D, JOINT_BOSS_L, 0.0, 0.0, COLUMN_H)
    column = column.union(boss)

    return column.clean()


def make_arm_segment(length_z: float, width_x: float, thickness_y: float, height_z: float, distal_bore_diameter: float) -> cq.Workplane:
    arm = cq.Workplane("XY").box(width_x, thickness_y, length_z, centered=(True, True, False))
    arm = arm.edges("|Z").chamfer(EDGE_CHAMFER)

    arm = cut_through_hole_y(
        arm,
        0.0,
        0.0,
        -thickness_y / 2.0,
        thickness_y / 2.0,
        ARM_BORE_D,
    )
    arm = cut_through_hole_y(
        arm,
        0.0,
        length_z,
        -thickness_y / 2.0,
        thickness_y / 2.0,
        distal_bore_diameter,
    )

    return arm.clean()


def make_lower_arm_segment() -> cq.Workplane:
    return make_arm_segment(LOWER_ARM_L, LOWER_ARM_W, LOWER_ARM_W, LOWER_ARM_H, ARM_BORE_D)


def make_upper_arm_segment() -> cq.Workplane:
    return make_arm_segment(UPPER_ARM_L, UPPER_ARM_W, UPPER_ARM_W, UPPER_ARM_H, TILT_BORE_D)


def make_device_holder() -> cq.Workplane:
    holder = cq.Workplane("XY").box(HOLDER_W, HOLDER_T, HOLDER_H, centered=(True, True, False))
    holder = holder.edges("|Z").chamfer(EDGE_CHAMFER)

    holder = cut_through_hole_y(
        holder,
        0.0,
        0.0,
        -HOLDER_T / 2.0,
        HOLDER_T / 2.0,
        TILT_BORE_D,
    )

    for x in (-JAW_OFFSET_X, JAW_OFFSET_X):
        slot = (
            cq.Workplane("YZ")
            .workplane(offset=x - JAW_SLOT_W / 2.0)
            .rect(JAW_SLOT_L, JAW_H)
            .extrude(JAW_SLOT_W)
            .translate((0.0, HOLDER_SLOT_CENTER_Y, 0.0))
        )
        holder = holder.cut(slot)

    return holder.clean()


def make_jaw() -> cq.Workplane:
    jaw_body = cq.Workplane("XY").box(JAW_W, JAW_L, JAW_H, centered=(True, True, False))
    pad = (
        cq.Workplane("XY")
        .box(JAW_PAD_W, JAW_PAD_T, JAW_PAD_H, centered=(True, True, False))
        .translate((0.0, JAW_L, (JAW_H - JAW_PAD_H) / 2.0))
    )
    jaw = jaw_body.union(pad)
    jaw = cut_through_hole_x(
        jaw,
        JAW_L / 2.0,
        JAW_BORE_Z,
        -JAW_W / 2.0,
        JAW_W / 2.0,
        JAW_PIN_D,
    )
    return jaw.clean()


def make_arm_hinge_pin() -> cq.Workplane:
    return make_y_cylinder(JOINT_PIN_D, JOINT_PIN_L, 0.0, 0.0, 0.0).clean()


def make_holder_tilt_pin() -> cq.Workplane:
    return make_y_cylinder(TILT_PIN_D, TILT_PIN_L, 0.0, 0.0, 0.0).clean()


def make_spring_or_screw() -> cq.Workplane:
    return make_y_cylinder(SPRING_D, SPRING_L, 0.0, 0.0, 0.0).clean()


def make_base_fastener() -> cq.Workplane:
    shaft = cq.Workplane("XY").circle(FASTENER_BODY_D / 2.0).extrude(FASTENER_BODY_L)
    head = (
        cq.Workplane("XY")
        .circle((FASTENER_BODY_D * 1.6) / 2.0)
        .extrude(4.0)
        .translate((0.0, 0.0, BASE_PLATE_T))
    )
    return shaft.union(head).clean()


def build_assembly() -> cq.Assembly:
    base_plate = make_base_plate()
    column = make_vertical_support_column()
    lower_arm = make_lower_arm_segment()
    upper_arm = make_upper_arm_segment()
    holder = make_device_holder()
    jaw_left = make_jaw()
    jaw_right = make_jaw()
    hinge_pin_a = make_arm_hinge_pin()
    hinge_pin_b = make_arm_hinge_pin()
    tilt_pin = make_holder_tilt_pin()
    spring_body = make_spring_or_screw()
    base_fastener = make_base_fastener()

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(base_plate, name="base_plate", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(column, name="vertical_support_column", loc=cq.Location(cq.Vector(0.0, 0.0, BASE_PLATE_T)))
    assembly.add(lower_arm, name="lower_arm_segment", loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + BASE_PLATE_T)))
    assembly.add(upper_arm, name="upper_arm_segment", loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + LOWER_ARM_L + BASE_PLATE_T)))
    assembly.add(holder, name="device_holder", loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + LOWER_ARM_L + UPPER_ARM_L + BASE_PLATE_T)))
    assembly.add(
        jaw_left,
        name="jaw_left",
        loc=cq.Location(cq.Vector(-JAW_OFFSET_X, HOLDER_SLOT_CENTER_Y, COLUMN_H + LOWER_ARM_L + UPPER_ARM_L + BASE_PLATE_T)),
    )
    assembly.add(
        jaw_right,
        name="jaw_right",
        loc=cq.Location(cq.Vector(JAW_OFFSET_X, HOLDER_SLOT_CENTER_Y, COLUMN_H + LOWER_ARM_L + UPPER_ARM_L + BASE_PLATE_T)),
    )
    assembly.add(
        hinge_pin_a,
        name="arm_hinge_pin_column_lower",
        loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + BASE_PLATE_T)),
    )
    assembly.add(
        hinge_pin_b,
        name="arm_hinge_pin_lower_upper",
        loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + LOWER_ARM_L + BASE_PLATE_T)),
    )
    assembly.add(
        tilt_pin,
        name="holder_tilt_joint",
        loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + LOWER_ARM_L + UPPER_ARM_L + BASE_PLATE_T)),
    )
    assembly.add(
        spring_body,
        name="jaw_spring_or_screw",
        loc=cq.Location(cq.Vector(0.0, 0.0, COLUMN_H + LOWER_ARM_L + UPPER_ARM_L + HOLDER_H / 2.0 + BASE_PLATE_T)),
    )

    bolt_positions = [
        (BASE_BOLT_R, 0.0),
        (0.0, BASE_BOLT_R),
        (-BASE_BOLT_R, 0.0),
        (0.0, -BASE_BOLT_R),
    ]
    for index, (x, y) in enumerate(bolt_positions, start=1):
        assembly.add(
            base_fastener,
            name=f"base_fastener_{index}",
            loc=cq.Location(cq.Vector(x, y, -3.0)),
        )

    return assembly


def validate_geometry(assembly: cq.Assembly) -> dict:
    results = {
        "is_assembly": isinstance(assembly, cq.Assembly),
        "base_plate_dims_positive": BASE_PLATE_W > 0.0 and BASE_PLATE_D > 0.0 and BASE_PLATE_T > 0.0,
        "column_dims_positive": COLUMN_W > 0.0 and COLUMN_D > 0.0 and COLUMN_H > 0.0,
        "arm_dims_positive": LOWER_ARM_L > 0.0 and UPPER_ARM_L > 0.0 and LOWER_ARM_W > 0.0 and UPPER_ARM_W > 0.0,
        "holder_dims_positive": HOLDER_W > 0.0 and HOLDER_H > 0.0 and HOLDER_T > 0.0,
        "jaw_slot_clearance_ok": JAW_SLOT_W > JAW_W and JAW_SLOT_L >= JAW_L,
        "column_wall_valid": COLUMN_WALL_T > 0.0 and COLUMN_W > 2.0 * COLUMN_WALL_T and COLUMN_D > 2.0 * COLUMN_WALL_T,
        "joint_pin_fit_ok": ARM_BORE_D > JOINT_PIN_D and TILT_BORE_D > TILT_PIN_D,
        "alignment_pin_count_ok": int(ALIGN_PIN_N) >= 2,
        "base_bolt_count_ok": int(BASE_BOLT_N) == 4,
        "manifest_feature_count": len(BUILD_MANIFEST["features"]),
        "manifest_part_frame_count": len(BUILD_MANIFEST["part_frames"]),
        "manifest_constraint_count": len(BUILD_MANIFEST["assembly_constraints"]),
        "build_manifest": BUILD_MANIFEST,
    }
    return results


def export_all(assembly: cq.Assembly, output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    output_paths = []

    step_path = os.path.join(output_dir, f"{COMPONENT_NAME}.step")
    assembly.save(step_path)
    output_paths.append(step_path)

    return output_paths


if __name__ == "__main__":
    assembly = build_assembly()
    validate_geometry(assembly)
    export_all(assembly, "./output")
