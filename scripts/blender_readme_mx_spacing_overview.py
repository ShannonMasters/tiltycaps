#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector


ROWS = ("R1", "R2", "R3", "R4", "Thumb")
ROW_X_SPACING = 24.0
SURFACE_Z_OFFSET = 0.45
MAIN_ROW_Y = 6.0
MAIN_LABEL_Y = -13.5
MAIN_Z_ROTATION_DEG = 180.0
OVERVIEW_CAMERA_LENS = 70
DETAIL_CAMERA_LENS = 72
README_CAMERA_LOCATION = (0, -218, 71)
README_CAMERA_TARGET = (0, -2, 4)
README_CROP_MIN_Y = 0.09
README_CROP_MAX_Y = 0.84
DETAIL_X_POSITIONS = (-36.0, 0.0, 36.0)
DETAIL_OBJECT_Y = 0.0
DETAIL_LABEL_Y = -16.5
DETAIL_Z_ROTATION_DEG = -45.0
OVERVIEW_LABEL_PERSPECTIVE_BLEND = 0.45


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(
        description="Render the README lineup and detail images for the MX-spacing keycap family."
    )
    parser.add_argument("--scene", choices=("overview", "detail"), required=True)
    parser.add_argument("--choc-dir", type=Path, required=True)
    parser.add_argument("--mx-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=96)
    parser.add_argument("--resolution-x", type=int, default=1800)
    parser.add_argument("--resolution-y", type=int, default=1120)
    return parser.parse_args(argv)


def orient_towards(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_material(
    name: str,
    base_color: tuple[float, float, float],
    roughness: float,
    metallic: float = 0.0,
    coat_weight: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat_weight
    return material


def world_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_corner = Vector(
        (
            min(corner.x for corner in corners),
            min(corner.y for corner in corners),
            min(corner.z for corner in corners),
        )
    )
    max_corner = Vector(
        (
            max(corner.x for corner in corners),
            max(corner.y for corner in corners),
            max(corner.z for corner in corners),
        )
    )
    return min_corner, max_corner


def center_object(obj: bpy.types.Object, target_x: float, target_y: float, target_min_z: float) -> None:
    bpy.context.view_layer.update()
    min_corner, max_corner = world_bounds(obj)
    center_x = (min_corner.x + max_corner.x) / 2
    center_y = (min_corner.y + max_corner.y) / 2
    obj.location.x += target_x - center_x
    obj.location.y += target_y - center_y
    obj.location.z += target_min_z - min_corner.z
    bpy.context.view_layer.update()


def import_stl(path: Path) -> bpy.types.Object:
    before = {obj.name for obj in bpy.data.objects}
    if hasattr(bpy.ops.wm, "stl_import"):
        bpy.ops.wm.stl_import(filepath=str(path))
    else:
        bpy.ops.import_mesh.stl(filepath=str(path))

    bpy.context.view_layer.update()
    imported = [obj for obj in bpy.data.objects if obj.name not in before]
    if len(imported) != 1:
        raise RuntimeError(f"Expected one object from {path}, got {len(imported)}")
    return imported[0]


def smooth_mesh(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    subdivision = obj.modifiers.new(name="RenderSubdivision", type="SUBSURF")
    subdivision.subdivision_type = "SIMPLE"
    subdivision.levels = 1
    subdivision.render_levels = 1
    bpy.ops.object.shade_auto_smooth(angle=math.radians(42))
    obj.select_set(False)
    modifier = obj.modifiers.new(name="WeightedNormal", type="WEIGHTED_NORMAL")
    modifier.weight = 75
    modifier.thresh = 0.01
    modifier.keep_sharp = True


def assign_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    mesh = obj.data
    mesh.materials.clear()
    mesh.materials.append(material)


def duplicate_object(source: bpy.types.Object, name: str) -> bpy.types.Object:
    copy = source.copy()
    copy.data = source.data.copy()
    copy.name = name
    bpy.context.scene.collection.objects.link(copy)
    return copy


def set_rotation(obj: bpy.types.Object, x_deg: float = 0.0, y_deg: float = 0.0, z_deg: float = 0.0) -> None:
    obj.rotation_euler = Euler(
        (
            math.radians(x_deg),
            math.radians(y_deg),
            math.radians(z_deg),
        ),
        "XYZ",
    )


def add_flat_text(
    body: str,
    location: tuple[float, float, float],
    size: float,
    material: bpy.types.Material,
    align_x: str = "CENTER",
) -> bpy.types.Object:
    bpy.ops.object.text_add(location=location)
    text = bpy.context.active_object
    text.data.body = body
    text.data.align_x = align_x
    text.data.align_y = "CENTER"
    text.data.size = size
    text.data.extrude = 0.01
    text.data.bevel_depth = 0.0
    text.data.materials.clear()
    text.data.materials.append(material)
    return text


def configure_scene(args: argparse.Namespace) -> tuple[bpy.types.Scene, bpy.types.Material, bpy.types.Material]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = args.resolution_x
    scene.render.resolution_y = args.resolution_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(args.output)
    scene.render.use_border = True
    scene.render.use_crop_to_border = True
    scene.render.border_min_x = 0.0
    scene.render.border_max_x = 1.0
    scene.render.border_min_y = README_CROP_MIN_Y
    scene.render.border_max_y = README_CROP_MAX_Y

    world = bpy.data.worlds.new("OverviewWorld")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (0.94, 0.95, 0.98, 1.0)
    background.inputs["Strength"].default_value = 0.72
    scene.world = world

    keycap_material = create_material(
        "KeycapSpaceGrey",
        base_color=(0.25, 0.29, 0.35),
        roughness=0.31,
        metallic=0.16,
        coat_weight=0.05,
    )
    text_material = create_material(
        "LabelInk",
        base_color=(0.08, 0.10, 0.13),
        roughness=0.44,
    )
    ground_material = create_material(
        "BackdropGround",
        base_color=(0.89, 0.91, 0.94),
        roughness=0.88,
    )

    bpy.ops.mesh.primitive_plane_add(size=220, location=(0, 0, 0))
    plane = bpy.context.active_object
    assign_material(plane, ground_material)

    camera_data = bpy.data.cameras.new("OverviewCamera")
    camera_data.type = "PERSP"
    camera_data.lens = OVERVIEW_CAMERA_LENS if args.scene == "overview" else DETAIL_CAMERA_LENS
    camera = bpy.data.objects.new("OverviewCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = README_CAMERA_LOCATION
    orient_towards(camera, README_CAMERA_TARGET)
    scene.camera = camera

    for name, location, energy, size, color in (
        ("KeyLight", (-46, -62, 66), 3600, 84, (1.0, 0.99, 0.98)),
        ("FillLight", (58, -26, 38), 1550, 72, (0.91, 0.95, 1.0)),
        ("RimLight", (18, 52, 48), 1700, 92, (0.90, 0.95, 1.0)),
    ):
        light_data = bpy.data.lights.new(name, type="AREA")
        light_data.energy = energy
        light_data.shape = "RECTANGLE"
        light_data.size = size
        light_data.size_y = size * 0.55
        light_data.color = color
        light = bpy.data.objects.new(name, light_data)
        scene.collection.objects.link(light)
        light.location = location
        orient_towards(light, (0, 0, 6))

    return scene, keycap_material, text_material


def object_path(directory: Path, row: str) -> Path:
    return directory / f"{row.lower()}.stl"


def homing_path(directory: Path) -> Path:
    return directory / "r3-homing-3-dots.stl"


def overview_label_x(label_x: float) -> float:
    camera_y = README_CAMERA_LOCATION[1]
    object_depth = abs(MAIN_ROW_Y - camera_y)
    label_depth = abs(MAIN_LABEL_Y - camera_y)
    perspective_scale = label_depth / object_depth
    return label_x * (1.0 - (1.0 - perspective_scale) * OVERVIEW_LABEL_PERSPECTIVE_BLEND)


def build_overview_scene(
    args: argparse.Namespace,
    keycap_material: bpy.types.Material,
    text_material: bpy.types.Material,
) -> None:
    x_positions = [(-2 + index) * ROW_X_SPACING for index in range(len(ROWS))]

    for index, row in enumerate(ROWS):
        obj = import_stl(object_path(args.choc_dir, row))
        obj.name = f"top_{row.lower()}"
        smooth_mesh(obj)
        assign_material(obj, keycap_material)
        set_rotation(obj, z_deg=MAIN_Z_ROTATION_DEG)
        center_object(obj, x_positions[index], MAIN_ROW_Y, SURFACE_Z_OFFSET)

        add_flat_text(
            body=row,
            location=(overview_label_x(x_positions[index]), MAIN_LABEL_Y, 0.08),
            size=3.3,
            material=text_material,
        )


def build_detail_scene(
    args: argparse.Namespace,
    keycap_material: bpy.types.Material,
    text_material: bpy.types.Material,
) -> None:
    detail_items = (
        ("R3 3 dots", homing_path(args.choc_dir), False),
        ("Choc stem", object_path(args.choc_dir, "R3"), True),
        ("MX stem", object_path(args.mx_dir, "R3"), True),
    )

    for index, (label, path, flipped) in enumerate(detail_items):
        obj = import_stl(path)
        obj.name = f"detail_{index}"
        smooth_mesh(obj)
        assign_material(obj, keycap_material)
        if flipped:
            set_rotation(obj, x_deg=180.0, z_deg=MAIN_Z_ROTATION_DEG)
        else:
            set_rotation(obj, z_deg=MAIN_Z_ROTATION_DEG)
        center_object(obj, DETAIL_X_POSITIONS[index], DETAIL_OBJECT_Y, SURFACE_Z_OFFSET)

        add_flat_text(
            body="R3 Homing" if label == "R3 3 dots" else label,
            location=(DETAIL_X_POSITIONS[index], DETAIL_LABEL_Y, 0.08),
            size=3.0,
            material=text_material,
        )


def main() -> int:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    _, keycap_material, text_material = configure_scene(args)
    if args.scene == "overview":
        build_overview_scene(args, keycap_material, text_material)
    else:
        build_detail_scene(args, keycap_material, text_material)

    bpy.ops.render.render(write_still=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
