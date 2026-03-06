#!/usr/bin/env python3
"""
Blender scene: Man thrown through hotel window at 3am.

Full cinematic sequence with multiple shots:
  Shot 1 (frames 1-30):   Interior — dark room, silhouette near window, tension
  Shot 2 (frames 31-50):  Glass shatters outward — body goes through window
  Shot 3 (frames 51-90):  Exterior — camera follows body falling 10 stories
  Shot 4 (frames 91-120): Street level — impact on pavement below
  Shot 5 (frames 121-150): Hold — stillness, empty street, aftermath

Run:
    blender --background --python scripts/blender_hotel_fall.py

Output: footage/.../blender/hotel_fall.mp4
"""

import math
import os
import random
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Euler

# ── Config ────────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "footage/fern_clone/frank_olson_cia_scientist_lsd_murder_cover_up/blender"
)

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 150  # 5 seconds total
SHARD_COUNT = 50
SHATTER_FRAME = 31  # when glass breaks

random.seed(42)
np.random.seed(42)


# ── Utilities ─────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                  bpy.data.cameras, bpy.data.objects]:
        for item in block:
            block.remove(item)


def make_mat(name, color, roughness=0.5, metallic=0.0, emission=None, glass=False):
    """Create a simple PBR material."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes:
        nodes.remove(n)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    if glass:
        bsdf = nodes.new('ShaderNodeBsdfGlass')
        bsdf.inputs['Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['IOR'].default_value = 1.52
    else:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (*color, 1)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            bsdf.inputs['Emission Color'].default_value = (*emission[:3], 1)
            bsdf.inputs['Emission Strength'].default_value = emission[3] if len(emission) > 3 else 1.0

    bsdf.location = (0, 0)
    links.new(bsdf.outputs[0], output.inputs[0])
    return mat


def keyframe_loc_rot(obj, frame, loc=None, rot=None):
    """Set location and/or rotation and insert keyframes."""
    if loc is not None:
        obj.location = loc
        obj.keyframe_insert(data_path="location", frame=frame)
    if rot is not None:
        obj.rotation_euler = rot
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)


# ── Scene Construction ────────────────────────────────────────────────────────

def build_hotel_room():
    """Build the hotel room: floor, walls, window opening, furniture."""
    wall_mat = make_mat("Wall", (0.14, 0.11, 0.09), roughness=0.85)
    floor_mat = make_mat("Floor", (0.07, 0.05, 0.04), roughness=0.9)
    wood_mat = make_mat("Wood", (0.05, 0.035, 0.025), roughness=0.75)
    bed_mat = make_mat("Bed", (0.12, 0.10, 0.09), roughness=0.95)
    frame_mat = make_mat("Frame", (0.22, 0.19, 0.15), roughness=0.6, metallic=0.3)

    # Floor
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    bpy.context.active_object.name = "Floor"
    bpy.context.active_object.data.materials.append(floor_mat)

    # Ceiling
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 3.2))
    c = bpy.context.active_object
    c.name = "Ceiling"
    c.rotation_euler = (math.pi, 0, 0)
    c.data.materials.append(wall_mat)

    # Walls (back, left, right)
    for name, loc, rot, sc in [
        ("BackWall", (0, -5, 1.6), (math.pi/2, 0, 0), (5, 1, 1.6)),
        ("LeftWall", (-5, 0, 1.6), (math.pi/2, 0, math.pi/2), (5, 1, 1.6)),
        ("RightWall", (5, 0, 1.6), (math.pi/2, 0, -math.pi/2), (5, 1, 1.6)),
    ]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
        w = bpy.context.active_object
        w.name = name
        w.rotation_euler = rot
        w.scale = sc
        w.data.materials.append(wall_mat)

    # Front wall with window hole — built as separate panels
    win_w, win_h = 2.0, 2.4
    win_bot = 0.7
    win_y = 5.0

    for name, loc, sc in [
        ("FWallLeft", (-3.0, win_y, 1.6), (2.0, 0.05, 1.6)),
        ("FWallRight", (3.0, win_y, 1.6), (2.0, 0.05, 1.6)),
        ("FWallTop", (0, win_y, 2.95), (1.0, 0.05, 0.25)),
        ("FWallBot", (0, win_y, 0.3), (1.0, 0.05, 0.3)),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        p = bpy.context.active_object
        p.name = name
        p.scale = sc
        p.data.materials.append(wall_mat)

    # Window frame
    for name, loc, sc in [
        ("WinFrameT", (0, win_y, win_bot + win_h), (1.05, 0.03, 0.04)),
        ("WinFrameB", (0, win_y, win_bot), (1.05, 0.03, 0.04)),
        ("WinFrameL", (-1.0, win_y, win_bot + win_h/2), (0.04, 0.03, win_h/2)),
        ("WinFrameR", (1.0, win_y, win_bot + win_h/2), (0.04, 0.03, win_h/2)),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        f = bpy.context.active_object
        f.name = name
        f.scale = sc
        f.data.materials.append(frame_mat)

    # Beds
    for bx in [-1.8, 1.8]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, -1, 0.35))
        b = bpy.context.active_object
        b.name = f"Bed_{bx:.0f}"
        b.scale = (0.7, 1.0, 0.35)
        b.data.materials.append(bed_mat)

    # Nightstand
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1, 0.3))
    ns = bpy.context.active_object
    ns.name = "Nightstand"
    ns.scale = (0.2, 0.2, 0.3)
    ns.data.materials.append(wood_mat)

    return win_y, win_bot, win_w, win_h


def build_exterior():
    """Build the exterior: building face, street, streetlamps."""
    bldg_mat = make_mat("Building", (0.04, 0.04, 0.06), roughness=0.9)
    street_mat = make_mat("Street", (0.03, 0.03, 0.04), roughness=0.95)
    light_mat = make_mat("StreetLight", (0.9, 0.8, 0.5),
                         emission=(1.0, 0.9, 0.6, 5.0))

    # Building exterior face (tall, extends down 10 stories)
    story_height = 3.2
    total_stories = 12
    bldg_height = story_height * total_stories

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 5.1, -bldg_height/2 + 3.2))
    ext = bpy.context.active_object
    ext.name = "BuildingExterior"
    ext.rotation_euler = (math.pi/2, 0, 0)
    ext.scale = (8, 1, bldg_height/2)
    ext.data.materials.append(bldg_mat)

    # Street below (10 stories down = ~32m below current floor)
    street_level = -(story_height * 9)  # 9 stories below = ground floor
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 8, street_level))
    st = bpy.context.active_object
    st.name = "Street"
    st.data.materials.append(street_mat)

    # Sidewalk
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 7, street_level + 0.05))
    sw = bpy.context.active_object
    sw.name = "Sidewalk"
    sw.scale = (4, 2, 0.05)
    sw.data.materials.append(make_mat("Sidewalk", (0.06, 0.06, 0.07), roughness=0.85))

    # Street lamps
    for lx in [-3, 3]:
        # Pole
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.04, depth=4, location=(lx, 9, street_level + 2))
        pole = bpy.context.active_object
        pole.name = f"LampPole_{lx}"
        pole.data.materials.append(make_mat(f"Pole_{lx}", (0.1, 0.1, 0.1), metallic=0.5))

        # Light
        bpy.ops.object.light_add(type='POINT', location=(lx, 9, street_level + 4.2))
        sl = bpy.context.active_object
        sl.name = f"StreetLamp_{lx}"
        sl.data.energy = 50.0
        sl.data.color = (1.0, 0.85, 0.5)
        sl.data.shadow_soft_size = 0.5

    return street_level


def build_human_figure(win_y):
    """
    Create a simple human silhouette figure near the window.
    Not detailed — just a dark shape (we're in a dark room at 3am).
    """
    body_mat = make_mat("BodyMat", (0.02, 0.02, 0.03), roughness=0.9)

    # Torso
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.2, win_y - 0.8, 1.2))
    torso = bpy.context.active_object
    torso.name = "Torso"
    torso.scale = (0.2, 0.15, 0.35)
    torso.data.materials.append(body_mat)

    # Head
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0.2, win_y - 0.8, 1.65))
    head = bpy.context.active_object
    head.name = "Head"
    head.data.materials.append(body_mat)

    # Arms (simple cylinders)
    for side, ax in [("L", -0.15), ("R", 0.55)]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.05, depth=0.5, location=(ax, win_y - 0.8, 1.15))
        arm = bpy.context.active_object
        arm.name = f"Arm{side}"
        arm.rotation_euler = (0, 0, 0.3 if side == "L" else -0.3)
        arm.data.materials.append(body_mat)

    # Legs
    for side, lx in [("L", 0.1), ("R", 0.3)]:
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.06, depth=0.6, location=(lx, win_y - 0.8, 0.5))
        leg = bpy.context.active_object
        leg.name = f"Leg{side}"
        leg.data.materials.append(body_mat)

    # Parent all body parts to torso for easy animation
    body_parts = [bpy.data.objects[n] for n in ["Head", "ArmL", "ArmR", "LegL", "LegR"]]
    for part in body_parts:
        part.parent = torso

    return torso


def animate_figure(torso, win_y, street_level, shatter_frame=31):
    """
    Animate the figure being pushed through the window and falling.
    """
    # Phase 1: Standing near window (frames 1-30)
    keyframe_loc_rot(torso, 1, loc=(0.2, win_y - 0.8, 1.2), rot=(0, 0, 0))
    keyframe_loc_rot(torso, 20, loc=(0.2, win_y - 0.5, 1.2), rot=(0, 0, 0))

    # Phase 2: Pushed toward window (frames 20-31)
    keyframe_loc_rot(torso, 28, loc=(0.2, win_y - 0.2, 1.2), rot=(0.1, 0, 0))
    keyframe_loc_rot(torso, shatter_frame, loc=(0.2, win_y + 0.3, 1.3), rot=(0.3, 0, 0.1))

    # Phase 3: Through window and falling (frames 31-90)
    gravity = -9.8
    initial_y_vel = 2.0   # forward momentum through window
    initial_z_vel = 1.5   # slight upward from being pushed

    for f in range(shatter_frame + 1, 91):
        dt = (f - shatter_frame) / FPS
        y = win_y + 0.3 + initial_y_vel * dt
        z = 1.3 + initial_z_vel * dt + 0.5 * gravity * dt * dt
        # Tumbling rotation
        rot_x = 0.3 + dt * 3.0
        rot_z = 0.1 + dt * 1.5

        keyframe_loc_rot(torso, f,
                        loc=(0.2, y, max(street_level + 0.3, z)),
                        rot=(rot_x, 0, rot_z))

    # Phase 4: Impact and stillness (frames 91-150)
    keyframe_loc_rot(torso, 91,
                    loc=(0.2, win_y + 3.0, street_level + 0.2),
                    rot=(math.pi/2 + 0.3, 0.2, 0.5))
    # Stay on ground
    for f in [100, 120, 150]:
        keyframe_loc_rot(torso, f,
                        loc=(0.2, win_y + 3.0, street_level + 0.2),
                        rot=(math.pi/2 + 0.3, 0.2, 0.5))


def build_glass_shards(win_y, win_bot, win_w, win_h):
    """Create glass shards that shatter outward."""
    glass_mat = make_mat("Glass", (0.85, 0.9, 1.0), roughness=0.02, glass=True)
    shards = []

    for i in range(SHARD_COUNT):
        sx = random.uniform(-win_w/2 + 0.1, win_w/2 - 0.1)
        sz = random.uniform(win_bot + 0.1, win_bot + win_h - 0.1)
        shard_size = random.uniform(0.04, 0.2)

        bm = bmesh.new()
        vert_count = random.randint(3, 6)
        angles = sorted([random.uniform(0, 2*math.pi) for _ in range(vert_count)])
        verts = []
        for a in angles:
            r = shard_size * random.uniform(0.4, 1.0)
            verts.append(bm.verts.new((math.cos(a)*r, 0, math.sin(a)*r)))
        bm.verts.ensure_lookup_table()
        try:
            bm.faces.new(verts)
        except ValueError:
            bm.free()
            continue

        mesh = bpy.data.meshes.new(f"ShardMesh_{i}")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Shard_{i}", mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (sx, win_y, sz)
        obj.data.materials.append(glass_mat)
        shards.append((obj, sx, sz, shard_size))

    return shards


def animate_shards(shards, win_y, shatter_frame=31):
    """Animate shards: intact before shatter, fly outward after."""
    for obj, sx, sz, size in shards:
        # Before shatter: at window
        keyframe_loc_rot(obj, 1, loc=(sx, win_y, sz), rot=(0, 0, 0))
        keyframe_loc_rot(obj, shatter_frame, loc=(sx, win_y, sz), rot=(0, 0, 0))

        # After shatter: fly outward (same direction as body — away from room)
        speed = random.uniform(1.5, 6.0)
        spread_x = random.uniform(-2.0, 2.0)
        spread_z = random.uniform(-0.5, 2.0)
        rot_speed = (random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))

        for f in range(shatter_frame + 1, TOTAL_FRAMES + 1):
            dt = (f - shatter_frame) / FPS
            x = sx + spread_x * dt
            y = win_y + speed * dt
            z = sz + spread_z * dt - 4.9 * dt * dt  # gravity

            keyframe_loc_rot(obj, f,
                            loc=(x, y, z),
                            rot=(rot_speed[0]*dt, rot_speed[1]*dt, rot_speed[2]*dt))


def setup_cameras(win_y, street_level):
    """
    Create multiple cameras for cinematic coverage:
    - cam_interior: inside room looking at window
    - cam_exterior: outside looking at falling body
    - cam_street: street level looking up
    """
    cameras = {}

    # Camera 1: Interior — starts wide, pushes toward window
    bpy.ops.object.camera_add(location=(0, -3, 1.5))
    cam1 = bpy.context.active_object
    cam1.name = "CamInterior"
    cam1.data.lens = 24
    cam1.data.dof.use_dof = True
    cam1.data.dof.focus_distance = 8.0
    cam1.data.dof.aperture_fstop = 2.0
    cam1.rotation_euler = (math.pi/2, 0, 0)

    # Slow push toward window (frames 1-31)
    keyframe_loc_rot(cam1, 1, loc=(0, -3, 1.5), rot=(math.pi/2, 0, 0))
    keyframe_loc_rot(cam1, 20, loc=(0, -1.5, 1.5), rot=(math.pi/2, 0, 0))
    keyframe_loc_rot(cam1, SHATTER_FRAME, loc=(0, -0.5, 1.5), rot=(math.pi/2, 0, 0))
    # Camera shake at shatter
    for f in range(SHATTER_FRAME+1, SHATTER_FRAME+10):
        shake = 0.04 * max(0, 1 - (f - SHATTER_FRAME) / 10)
        keyframe_loc_rot(cam1, f,
                        loc=(random.uniform(-shake, shake),
                             -0.5 + random.uniform(-shake, shake),
                             1.5 + random.uniform(-shake, shake)))
    keyframe_loc_rot(cam1, SHATTER_FRAME+10, loc=(0, -0.5, 1.5))
    cameras['interior'] = cam1

    # Camera 2: Exterior — looking at the building face, sees body fall
    bpy.ops.object.camera_add(location=(3, 12, 1.5))
    cam2 = bpy.context.active_object
    cam2.name = "CamExterior"
    cam2.data.lens = 35
    cam2.data.dof.use_dof = True
    cam2.data.dof.focus_distance = 7.0
    cam2.data.dof.aperture_fstop = 2.8

    # Looking at the window from outside, then tilts down to follow fall
    keyframe_loc_rot(cam2, 40,
                    loc=(3, 12, 2.0),
                    rot=(math.pi/2 - 0.1, 0, 0.15))
    # Tilt down to follow body
    for f in range(50, 91):
        t = (f - 50) / 40  # 0 to 1
        z = 2.0 - t * (2.0 - street_level - 2)  # pan down
        tilt = (math.pi/2 - 0.1) + t * 0.8  # tilt down
        keyframe_loc_rot(cam2, f,
                        loc=(3, 12, z),
                        rot=(tilt, 0, 0.15))
    cameras['exterior'] = cam2

    # Camera 3: Street level — low angle looking up at building
    bpy.ops.object.camera_add(location=(1, 10, street_level + 1.0))
    cam3 = bpy.context.active_object
    cam3.name = "CamStreet"
    cam3.data.lens = 28
    cam3.data.dof.use_dof = True
    cam3.data.dof.focus_distance = 3.0
    cam3.data.dof.aperture_fstop = 2.0
    # Looking slightly up toward where body lands
    keyframe_loc_rot(cam3, 85,
                    loc=(1, 10, street_level + 1.0),
                    rot=(math.pi/2 + 0.3, 0, 0.1))
    keyframe_loc_rot(cam3, 91,
                    loc=(1, 10, street_level + 1.0),
                    rot=(math.pi/2 - 0.1, 0, 0.1))
    # Subtle drift after impact
    keyframe_loc_rot(cam3, 150,
                    loc=(1.2, 9.5, street_level + 0.8),
                    rot=(math.pi/2 - 0.15, 0, 0.05))
    cameras['street'] = cam3

    return cameras


def setup_camera_switching(cameras):
    """
    Use markers to switch between cameras during the sequence.
    Shot 1 (1-40):   Interior
    Shot 2 (41-85):  Exterior (following fall)
    Shot 3 (86-150): Street level (impact + aftermath)
    """
    scene = bpy.context.scene

    # Set active camera to interior first
    scene.camera = cameras['interior']

    # Add timeline markers for camera switches
    markers = {
        1: cameras['interior'],
        41: cameras['exterior'],
        86: cameras['street'],
    }

    for frame, cam in markers.items():
        marker = scene.timeline_markers.new(f"Shot_{frame}", frame=frame)
        marker.camera = cam


def setup_lighting(win_y, street_level):
    """Cinematic lighting for 3am."""
    # Dim warm lamp inside room
    bpy.ops.object.light_add(type='POINT', location=(0, -1, 1.0))
    lamp = bpy.context.active_object
    lamp.name = "RoomLamp"
    lamp.data.energy = 3.0
    lamp.data.color = (1.0, 0.75, 0.45)
    lamp.data.shadow_soft_size = 0.3

    # Blue moonlight from outside
    bpy.ops.object.light_add(type='AREA', location=(0, 8, 3))
    moon = bpy.context.active_object
    moon.name = "Moonlight"
    moon.rotation_euler = (-math.pi/3, 0, 0)
    moon.data.energy = 30.0
    moon.data.color = (0.35, 0.45, 0.75)
    moon.data.size = 5.0

    # Ambient fill
    bpy.ops.object.light_add(type='POINT', location=(0, 2, 2))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 1.5
    fill.data.color = (0.25, 0.25, 0.35)

    # World background — deep night
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.003, 0.003, 0.012, 1)
        bg.inputs['Strength'].default_value = 1.0


def setup_render():
    """Configure render settings for EEVEE (fast) or CYCLES (quality)."""
    scene = bpy.context.scene
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # Use EEVEE for speed (Blender 5.0 = 'BLENDER_EEVEE')
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 64

    # Enable reflections/refractions for glass
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = True
        scene.eevee.use_ssr_refraction = True

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'

    # Color management for cinematic look
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'High Contrast'
    scene.view_settings.exposure = -0.5  # slightly dark

    # Bloom/glare — use EEVEE built-in if available
    if hasattr(scene.eevee, 'use_bloom'):
        scene.eevee.use_bloom = True
        scene.eevee.bloom_threshold = 0.9
        scene.eevee.bloom_intensity = 0.05


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("BLENDER: Hotel Window Fall — Full Cinematic Sequence")
    print("=" * 60)

    print("\n[1/8] Clearing scene...")
    clear_scene()

    print("[2/8] Building hotel room...")
    win_y, win_bot, win_w, win_h = build_hotel_room()

    print("[3/8] Building exterior (building + street)...")
    street_level = build_exterior()

    print("[4/8] Creating human figure...")
    figure = build_human_figure(win_y)

    print("[5/8] Creating glass shards...")
    shards = build_glass_shards(win_y, win_bot, win_w, win_h)

    print("[6/8] Animating figure + glass...")
    animate_figure(figure, win_y, street_level, SHATTER_FRAME)
    animate_shards(shards, win_y, SHATTER_FRAME)

    print("[7/8] Setting up cameras + lighting...")
    cameras = setup_cameras(win_y, street_level)
    setup_camera_switching(cameras)
    setup_lighting(win_y, street_level)

    print("[8/8] Configuring render...")
    setup_render()

    # Save .blend file
    blend_path = os.path.join(OUTPUT_DIR, "hotel_fall_scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n  Scene saved: {blend_path}")
    print(f"  You can open this in Blender to inspect and tweak before rendering.")

    # Render
    output_path = os.path.join(OUTPUT_DIR, "hotel_fall_")
    bpy.context.scene.render.filepath = output_path

    print(f"\n  Rendering {TOTAL_FRAMES} frames ({TOTAL_FRAMES/FPS:.1f}s)...")
    print(f"  Engine: EEVEE, Samples: 64")
    print(f"  {W}x{H} @ {FPS}fps")
    print(f"  Shots: Interior (1-40) → Exterior Fall (41-85) → Street Impact (86-150)")
    print()

    bpy.ops.render.render(animation=True)

    # Convert to video
    mp4_path = os.path.join(OUTPUT_DIR, "hotel_fall.mp4")
    os.system(
        f'ffmpeg -y -framerate {FPS} -i "{output_path}%04d.png" '
        f'-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p '
        f'"{mp4_path}" 2>/dev/null'
    )

    if os.path.exists(mp4_path):
        size_mb = os.path.getsize(mp4_path) / (1024 * 1024)
        print(f"\n  DONE: {mp4_path} ({size_mb:.1f} MB, {TOTAL_FRAMES/FPS:.1f}s)")
    else:
        print(f"\n  Frames at: {output_path}*.png (convert manually)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
