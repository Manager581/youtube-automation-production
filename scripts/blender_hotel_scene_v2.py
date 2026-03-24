#!/usr/bin/env python3
"""
Blender scene v2: 1950s hotel room at 3am using REAL 3D assets.
Furniture from Polyhaven (CC0), proper lighting, cinematic camera.

This version:
  - Imports real .blend furniture models (not coded primitives)
  - Proper materials with textures
  - Cinematic camera animation (slow push toward window)
  - Dark moody lighting (3am noir feel)
  - Volumetric fog for atmosphere
  - Simple silhouette figure near window

Run:
    blender --background --python scripts/blender_hotel_scene_v2.py
"""

import math
import os
import random
import sys

import bpy
from mathutils import Vector

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(BASE_DIR, "assets/3d_models")
OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/blender"
)

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 150  # 5 seconds
ROOM_W, ROOM_D, ROOM_H = 6.0, 8.0, 3.2  # meters

# ── Utilities ─────────────────────────────────────────────────────────────────

def clear_scene():
    """Remove everything from the default scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                  bpy.data.cameras, bpy.data.objects]:
        for item in block:
            block.remove(item)


def make_material(name, color, roughness=0.5, metallic=0.0, emission_strength=0.0):
    """Create a PBR material."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission_strength > 0:
            bsdf.inputs['Emission Color'].default_value = (*color, 1)
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat


def override_materials(objects, color, roughness=0.8):
    """Replace all materials on imported objects with a scene-matching material."""
    mat = make_material(f"Override_{id(objects)}", color, roughness=roughness)
    for obj in objects:
        if hasattr(obj, 'data') and hasattr(obj.data, 'materials'):
            obj.data.materials.clear()
            obj.data.materials.append(mat)


def import_blend_asset(filepath, link=False):
    """Import all objects from a .blend file into the current scene."""
    if not os.path.exists(filepath):
        print(f"  WARNING: Asset not found: {filepath}")
        return []

    imported = []
    with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            imported.append(obj)

    return imported


def place_asset(objects, location, rotation=(0,0,0), scale=(1,1,1)):
    """Move a group of imported objects to a location."""
    if not objects:
        return
    # Find the root/parent object
    root = objects[0]
    for obj in objects:
        if obj.parent is None:
            root = obj
            break

    root.location = location
    root.rotation_euler = rotation
    root.scale = scale

    # Make sure children follow
    for obj in objects:
        if obj != root and obj.parent is None:
            obj.parent = root


# ── Scene Construction ────────────────────────────────────────────────────────

def build_room():
    """Build room shell: floor, ceiling, 3 walls + front wall with window."""
    # Materials
    # 1950s hotel: self-emitting walls so they're ALWAYS visible regardless of lighting
    wall_mat = make_material("DarkWall", (0.18, 0.16, 0.13), roughness=0.9,
                             emission_strength=0.15)  # Faint self-glow
    floor_mat = make_material("WoodFloor", (0.12, 0.08, 0.05), roughness=0.7,
                              emission_strength=0.05)
    ceiling_mat = make_material("Ceiling", (0.20, 0.18, 0.16), roughness=0.95,
                                emission_strength=0.08)
    trim_mat = make_material("WoodTrim", (0.10, 0.07, 0.04), roughness=0.5)

    hw, hd = ROOM_W/2, ROOM_D/2

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (hw, hd, 1)
    floor.data.materials.append(floor_mat)

    # Ceiling
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, ROOM_H))
    ceil = bpy.context.active_object
    ceil.name = "Ceiling"
    ceil.rotation_euler = (math.pi, 0, 0)
    ceil.scale = (hw, hd, 1)
    ceil.data.materials.append(ceiling_mat)

    # Walls (back, left, right)
    walls = [
        ("BackWall",  (0, -hd, ROOM_H/2), (math.pi/2, 0, 0),        (hw, 1, ROOM_H/2)),
        ("LeftWall",  (-hw, 0, ROOM_H/2), (math.pi/2, 0, math.pi/2), (hd, 1, ROOM_H/2)),
        ("RightWall", (hw, 0, ROOM_H/2),  (math.pi/2, 0, -math.pi/2),(hd, 1, ROOM_H/2)),
    ]
    for name, loc, rot, sc in walls:
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        w = bpy.context.active_object
        w.name = name
        w.rotation_euler = rot
        w.scale = sc
        w.data.materials.append(wall_mat)

    # Front wall with window opening (4 panels around window)
    win_w, win_h = 1.8, 2.2
    win_bot = 0.8
    fy = hd  # front wall y position

    panels = [
        ("FWLeft",  (-hw/2 - win_w/4, fy, ROOM_H/2),   (hw/2 - win_w/4, 0.05, ROOM_H/2)),
        ("FWRight", (hw/2 + win_w/4, fy, ROOM_H/2),     (hw/2 - win_w/4, 0.05, ROOM_H/2)),
        ("FWTop",   (0, fy, win_bot + win_h + (ROOM_H - win_bot - win_h)/2),
                    (win_w/2, 0.05, (ROOM_H - win_bot - win_h)/2)),
        ("FWBot",   (0, fy, win_bot/2),                  (win_w/2, 0.05, win_bot/2)),
    ]
    for name, loc, sc in panels:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        p = bpy.context.active_object
        p.name = name
        p.scale = sc
        p.data.materials.append(wall_mat)

    # Window frame (trim)
    frame_parts = [
        ("WFrameT", (0, fy, win_bot + win_h),     (win_w/2 + 0.05, 0.03, 0.03)),
        ("WFrameB", (0, fy, win_bot),              (win_w/2 + 0.05, 0.03, 0.03)),
        ("WFrameL", (-win_w/2, fy, win_bot + win_h/2), (0.03, 0.03, win_h/2)),
        ("WFrameR", (win_w/2, fy, win_bot + win_h/2),  (0.03, 0.03, win_h/2)),
        ("WFrameM", (0, fy, win_bot + win_h/2),        (0.02, 0.03, win_h/2)),  # center divider
    ]
    for name, loc, sc in frame_parts:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        f = bpy.context.active_object
        f.name = name
        f.scale = sc
        f.data.materials.append(trim_mat)

    # Window glass panes (translucent, glowing with night sky)
    night_glow = make_material("NightSky", (0.05, 0.08, 0.18), roughness=0.1,
                               metallic=0.0, emission_strength=3.0)
    # Left pane
    bpy.ops.mesh.primitive_plane_add(size=1,
        location=(-win_w/4, fy + 0.01, win_bot + win_h/2))
    lp = bpy.context.active_object
    lp.name = "WindowGlassL"
    lp.rotation_euler = (math.pi/2, 0, 0)
    lp.scale = (win_w/4 - 0.03, win_h/2 - 0.03, 1)
    lp.data.materials.append(night_glow)
    # Right pane
    bpy.ops.mesh.primitive_plane_add(size=1,
        location=(win_w/4, fy + 0.01, win_bot + win_h/2))
    rp = bpy.context.active_object
    rp.name = "WindowGlassR"
    rp.rotation_euler = (math.pi/2, 0, 0)
    rp.scale = (win_w/4 - 0.03, win_h/2 - 0.03, 1)
    rp.data.materials.append(night_glow)

    # Baseboard trim around room
    for name, loc, rot, length in [
        ("TrimBack", (0, -hd+0.02, 0.05), (0,0,0), hw),
        ("TrimLeft", (-hw+0.02, 0, 0.05), (0,0,math.pi/2), hd),
        ("TrimRight", (hw-0.02, 0, 0.05), (0,0,math.pi/2), hd),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        t = bpy.context.active_object
        t.name = name
        t.rotation_euler = rot
        t.scale = (length, 0.01, 0.05)
        t.data.materials.append(trim_mat)

    return fy, win_bot, win_w, win_h


def build_bed():
    """Build a 1950s hotel bed from primitives (left side of room)."""
    bed_frame_mat = make_material("BedFrame", (0.08, 0.05, 0.03), roughness=0.6)
    mattress_mat = make_material("Mattress", (0.25, 0.22, 0.20), roughness=0.95,
                                 emission_strength=0.05)  # Slightly visible
    sheet_mat = make_material("Sheets", (0.35, 0.33, 0.30), roughness=0.9,
                              emission_strength=0.08)  # White-ish sheets visible in dark
    pillow_mat = make_material("Pillow", (0.38, 0.36, 0.33), roughness=0.95,
                               emission_strength=0.06)

    bx, by = -1.2, 0.5  # Bed position (left side, middle of room)

    # Bed frame (box spring)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, 0.25))
    frame = bpy.context.active_object
    frame.name = "BedFrame"
    frame.scale = (0.55, 1.0, 0.12)
    frame.data.materials.append(bed_frame_mat)

    # Headboard (against left wall)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by - 1.0, 0.65))
    hb = bpy.context.active_object
    hb.name = "Headboard"
    hb.scale = (0.55, 0.03, 0.35)
    hb.data.materials.append(bed_frame_mat)

    # Mattress
    bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, 0.42))
    matt = bpy.context.active_object
    matt.name = "Mattress"
    matt.scale = (0.52, 0.95, 0.08)
    matt.data.materials.append(mattress_mat)

    # Sheet/blanket (slightly larger, draped look)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by + 0.15, 0.50))
    sheet = bpy.context.active_object
    sheet.name = "Sheet"
    sheet.scale = (0.54, 0.70, 0.04)
    sheet.data.materials.append(sheet_mat)

    # Pillows
    for px in [bx - 0.2, bx + 0.2]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(px, by - 0.7, 0.55))
        p = bpy.context.active_object
        p.name = "Pillow"
        p.scale = (0.18, 0.12, 0.06)
        p.data.materials.append(pillow_mat)

    # Bed legs
    for lx, ly in [(bx-0.5, by-0.9), (bx+0.5, by-0.9), (bx-0.5, by+0.9), (bx+0.5, by+0.9)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.25, location=(lx, ly, 0.125))
        leg = bpy.context.active_object
        leg.name = "BedLeg"
        leg.data.materials.append(bed_frame_mat)


def build_curtains(fy, win_w, win_h, win_bot):
    """Add curtains flanking the window."""
    curtain_mat = make_material("Curtain", (0.15, 0.10, 0.08), roughness=0.95,
                                emission_strength=0.03)
    curtain_h = win_h + 0.4
    curtain_top = win_bot + win_h + 0.2

    for side, cx in [("L", -win_w/2 - 0.15), ("R", win_w/2 + 0.15)]:
        bpy.ops.mesh.primitive_cube_add(size=1,
            location=(cx, fy - 0.05, curtain_top - curtain_h/2))
        c = bpy.context.active_object
        c.name = f"Curtain{side}"
        c.scale = (0.15, 0.02, curtain_h/2)
        c.data.materials.append(curtain_mat)

    # Curtain rod
    rod_mat = make_material("CurtainRod", (0.15, 0.12, 0.08), roughness=0.3, metallic=0.8)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.015, depth=win_w + 0.8,
        location=(0, fy - 0.05, curtain_top))
    rod = bpy.context.active_object
    rod.name = "CurtainRod"
    rod.rotation_euler = (0, math.pi/2, 0)
    rod.data.materials.append(rod_mat)


def build_silhouette_figure(fy):
    """Larger, more recognizable human figure as dark silhouette."""
    body_mat = make_material("BodyDark", (0.02, 0.02, 0.025), roughness=0.95)

    fig_x = 0.3  # Slightly right of center
    fig_y = fy - 0.5  # Just in front of window
    fig_scale = 1.3  # Scale up for visibility

    # Torso
    bpy.ops.mesh.primitive_cube_add(size=1, location=(fig_x, fig_y, 1.15 * fig_scale))
    torso = bpy.context.active_object
    torso.name = "FigureTorso"
    torso.scale = (0.25 * fig_scale, 0.14 * fig_scale, 0.40 * fig_scale)
    torso.data.materials.append(body_mat)

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.13 * fig_scale,
        location=(fig_x, fig_y, 1.72 * fig_scale))
    head = bpy.context.active_object
    head.name = "FigureHead"
    head.data.materials.append(body_mat)
    head.parent = torso

    # Shoulders
    bpy.ops.mesh.primitive_cube_add(size=1, location=(fig_x, fig_y, 1.42 * fig_scale))
    shoulders = bpy.context.active_object
    shoulders.name = "FigureShoulders"
    shoulders.scale = (0.35 * fig_scale, 0.12 * fig_scale, 0.10 * fig_scale)
    shoulders.data.materials.append(body_mat)
    shoulders.parent = torso

    # Arms (thicker, more visible)
    for side, x_off in [("L", -0.30), ("R", 0.30)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05 * fig_scale, depth=0.6 * fig_scale,
            location=(fig_x + x_off * fig_scale, fig_y, 1.05 * fig_scale))
        arm = bpy.context.active_object
        arm.name = f"FigureArm{side}"
        arm.data.materials.append(body_mat)
        arm.parent = torso

    # Legs (thicker)
    for side, x_off in [("L", -0.10), ("R", 0.10)]:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.06 * fig_scale, depth=0.8 * fig_scale,
            location=(fig_x + x_off * fig_scale, fig_y, 0.4 * fig_scale))
        leg = bpy.context.active_object
        leg.name = f"FigureLeg{side}"
        leg.data.materials.append(body_mat)
        leg.parent = torso

    return torso


def furnish_room(fy):
    """Import real furniture assets and place them in the room."""
    hw, hd = ROOM_W/2, ROOM_D/2

    # Muted 1950s hotel furniture colors
    SOFA_COLOR = (0.12, 0.08, 0.06)      # Dark brown leather
    TABLE_COLOR = (0.10, 0.07, 0.04)      # Dark walnut
    LAMP_COLOR = (0.15, 0.12, 0.08)       # Aged brass/wood
    CABINET_COLOR = (0.08, 0.06, 0.04)    # Dark mahogany
    CHAIR_COLOR = (0.11, 0.08, 0.05)      # Dark wood

    placements = [
        # (asset_name, location, rotation_z, scale, override_color)
        ("sofa_02", (-1.5, -2.0, 0), math.pi, (1.2, 1.2, 1.2), SOFA_COLOR),
        ("sofa_02", (1.5, -2.0, 0), math.pi, (1.2, 1.2, 1.2), SOFA_COLOR),
        ("side_table_01", (0, -2.0, 0), 0, (1.0, 1.0, 1.0), TABLE_COLOR),
        ("desk_lamp_arm_01", (0, -1.9, 0.5), 0, (0.8, 0.8, 0.8), LAMP_COLOR),
        ("vintage_cabinet_01", (-2.5, 0.5, 0), math.pi/2, (0.8, 0.8, 0.8), CABINET_COLOR),
        ("painted_wooden_chair_01", (1.8, 1.0, 0), -math.pi/4, (1.0, 1.0, 1.0), CHAIR_COLOR),
        ("modern_coffee_table_01", (0, 0, 0), 0, (0.9, 0.9, 0.9), TABLE_COLOR),
    ]

    placed_count = 0
    for asset_name, loc, rot_z, sc, color in placements:
        filepath = os.path.join(ASSET_DIR, f"{asset_name}.blend")
        if not os.path.exists(filepath):
            print(f"  SKIP: {asset_name} not found")
            continue

        print(f"  Importing {asset_name}...")
        objects = import_blend_asset(filepath)
        if objects:
            override_materials(objects, color)
            place_asset(objects, loc, rotation=(0, 0, rot_z), scale=sc)
            placed_count += 1

    print(f"  Placed {placed_count} furniture pieces")
    return placed_count


def setup_lighting(fy):
    """Cinematic noir lighting for 3am hotel room."""
    # === KEY: Sun light for moonlight (uniform, no falloff, illuminates entire room) ===
    bpy.ops.object.light_add(type='SUN', location=(0, fy + 2, 4))
    sun = bpy.context.active_object
    sun.name = "Moonlight"
    sun.rotation_euler = (-math.pi/3, 0, 0.1)  # Angled from window side
    sun.data.energy = 2.0  # Sun lights use much lower energy
    sun.data.color = (0.5, 0.6, 0.9)  # Cool blue moonlight
    sun.data.angle = 0.05  # Soft shadows

    # === FILL: Large area light inside room for overall visibility ===
    bpy.ops.object.light_add(type='AREA', location=(0, 0, ROOM_H - 0.2))
    fill = bpy.context.active_object
    fill.name = "CeilingFill"
    fill.rotation_euler = (math.pi, 0, 0)  # Pointing down
    fill.data.energy = 150.0
    fill.data.color = (0.35, 0.4, 0.55)  # Cool ambient
    fill.data.size = 6.0

    # === RIM: Backlight on figure silhouette from window ===
    bpy.ops.object.light_add(type='SPOT', location=(0, fy + 1, 2.2))
    rim = bpy.context.active_object
    rim.name = "FigureRim"
    rim.rotation_euler = (-math.pi/3, 0, 0)
    rim.data.energy = 500.0
    rim.data.color = (0.6, 0.7, 1.0)
    rim.data.spot_size = math.pi/3  # 60 degree cone
    rim.data.spot_blend = 0.5

    # === PRACTICAL: Warm desk lamp glow ===
    bpy.ops.object.light_add(type='POINT', location=(-1.5, -1.8, 0.9))
    lamp = bpy.context.active_object
    lamp.name = "DeskLamp"
    lamp.data.energy = 100.0
    lamp.data.color = (1.0, 0.7, 0.35)
    lamp.data.shadow_soft_size = 0.4

    # === HALLWAY: Warm light under door ===
    bpy.ops.object.light_add(type='AREA', location=(0, -ROOM_D/2 + 0.2, 0.3))
    hall = bpy.context.active_object
    hall.name = "HallwayLight"
    hall.rotation_euler = (math.pi/2, 0, 0)
    hall.data.energy = 60.0
    hall.data.color = (1.0, 0.85, 0.55)
    hall.data.size = 3.0

    # === WALL WASH: Side lights to illuminate left/right walls ===
    for side, x, rot_z in [("Left", -ROOM_W/2 + 0.5, math.pi/2), ("Right", ROOM_W/2 - 0.5, -math.pi/2)]:
        bpy.ops.object.light_add(type='AREA', location=(x, 0, 1.5))
        wl = bpy.context.active_object
        wl.name = f"WallWash{side}"
        wl.rotation_euler = (0, 0, rot_z)
        wl.data.energy = 80.0
        wl.data.color = (0.4, 0.45, 0.6)
        wl.data.size = 4.0

    # Night sky world background (slightly brighter for ambient)
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.015, 0.02, 0.05, 1)
        bg.inputs['Strength'].default_value = 1.0


def setup_camera(fy):
    """Cinematic camera: slow push toward window with slight drift."""
    bpy.ops.object.camera_add(location=(0, -3, 1.4))
    cam = bpy.context.active_object
    cam.name = "MainCamera"
    cam.data.lens = 28  # wide angle for room feel
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 5.0
    cam.data.dof.aperture_fstop = 2.8

    bpy.context.scene.camera = cam

    # Keyframe animation: slow push toward window
    # Frame 1: wide shot from back of room
    cam.location = (0.2, -3.0, 1.4)
    cam.rotation_euler = (math.pi/2 - 0.02, 0, 0.01)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.keyframe_insert(data_path="rotation_euler", frame=1)

    # Frame 50: moving closer, slight drift right
    cam.location = (0.1, -1.5, 1.35)
    cam.rotation_euler = (math.pi/2 - 0.01, 0, 0.005)
    cam.keyframe_insert(data_path="location", frame=50)
    cam.keyframe_insert(data_path="rotation_euler", frame=50)

    # Frame 100: close to figure, focused on window
    cam.location = (0.15, 0.5, 1.3)
    cam.rotation_euler = (math.pi/2, 0, 0)
    cam.keyframe_insert(data_path="location", frame=100)
    cam.keyframe_insert(data_path="rotation_euler", frame=100)

    # Frame 150: tight on window/figure silhouette
    cam.location = (0.25, 1.5, 1.35)
    cam.rotation_euler = (math.pi/2 + 0.02, 0, -0.01)
    cam.keyframe_insert(data_path="location", frame=150)
    cam.keyframe_insert(data_path="rotation_euler", frame=150)

    # Smooth interpolation — Blender 5.0 compatible
    action = cam.animation_data.action
    # Try fcurves (Blender <5.0) or layers/strips (Blender 5.0+)
    try:
        curves = action.fcurves
        for fcurve in curves:
            for kfp in fcurve.keyframe_points:
                kfp.interpolation = 'BEZIER'
                kfp.handle_left_type = 'AUTO_CLAMPED'
                kfp.handle_right_type = 'AUTO_CLAMPED'
    except AttributeError:
        # Blender 5.0: fcurves may be on action layers/strips
        if hasattr(action, 'layers'):
            for layer in action.layers:
                for strip in layer.strips:
                    for channelbag in strip.channelbags:
                        for fcurve in channelbag.fcurves:
                            for kfp in fcurve.keyframe_points:
                                kfp.interpolation = 'BEZIER'
                                kfp.handle_left_type = 'AUTO_CLAMPED'
                                kfp.handle_right_type = 'AUTO_CLAMPED'
        else:
            print("  Warning: Could not set Bezier interpolation (API changed)")

    return cam


def setup_render():
    """Configure EEVEE render settings for cinematic output."""
    scene = bpy.context.scene
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # EEVEE for speed
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 64

    # Shadows
    if hasattr(scene.eevee, 'shadow_cube_size'):
        scene.eevee.shadow_cube_size = '1024'
    if hasattr(scene.eevee, 'use_shadow_high_bitdepth'):
        scene.eevee.use_shadow_high_bitdepth = True
    if hasattr(scene.eevee, 'use_soft_shadows'):
        scene.eevee.use_soft_shadows = True

    # Screen-space reflections for glass/floor
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = True

    # Volumetrics for atmosphere/fog
    if hasattr(scene.eevee, 'use_volumetric_lights'):
        scene.eevee.use_volumetric_lights = True
    if hasattr(scene.eevee, 'volumetric_tile_size'):
        scene.eevee.volumetric_tile_size = '8'

    # Bloom
    if hasattr(scene.eevee, 'use_bloom'):
        scene.eevee.use_bloom = True
        scene.eevee.bloom_threshold = 0.8
        scene.eevee.bloom_intensity = 0.08

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'

    # Filmic color management
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.5  # Brighten overall (was -0.3)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("BLENDER v2: Hotel Room with Real Assets")
    print("=" * 60)

    print("\n[1/9] Clearing scene...")
    clear_scene()

    print("[2/9] Building room shell...")
    fy, win_bot, win_w, win_h = build_room()

    print("[3/9] Adding bed...")
    build_bed()

    print("[4/9] Adding curtains...")
    build_curtains(fy, win_w, win_h, win_bot)

    print("[5/9] Importing furniture...")
    furnish_room(fy)

    print("[6/9] Adding figure silhouette...")
    figure = build_silhouette_figure(fy)

    print("[7/9] Setting up lighting...")
    setup_lighting(fy)

    print("[8/9] Setting up camera...")
    cam = setup_camera(fy)

    print("[9/9] Configuring render...")
    setup_render()

    # Save .blend for inspection
    blend_path = os.path.join(OUTPUT_DIR, "hotel_scene_v2.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n  Scene saved: {blend_path}")
    print(f"  Open in Blender to inspect before rendering.")

    # Render
    output_path = os.path.join(OUTPUT_DIR, "hotel_v2_")
    bpy.context.scene.render.filepath = output_path

    print(f"\n  Rendering {TOTAL_FRAMES} frames ({TOTAL_FRAMES/FPS:.1f}s)...")
    print(f"  {W}x{H} @ {FPS}fps, EEVEE 64 samples")
    print()

    bpy.ops.render.render(animation=True)

    # Convert to video
    mp4_path = os.path.join(OUTPUT_DIR, "hotel_scene_v2.mp4")
    os.system(
        f'ffmpeg -y -framerate {FPS} -i "{output_path}%04d.png" '
        f'-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p '
        f'"{mp4_path}" 2>/dev/null'
    )

    if os.path.exists(mp4_path):
        size_mb = os.path.getsize(mp4_path) / (1024 * 1024)
        print(f"\n  DONE: {mp4_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n  Frames at: {output_path}*.png")

    print("=" * 60)


if __name__ == "__main__":
    main()
