#!/usr/bin/env python3
"""
Blender script: Hotel window glass shattering at 3am.

Creates a dark hotel room scene with:
- Window with venetian blinds
- Glass pane that shatters into Voronoi-pattern shards
- Shards animated flying outward toward camera
- Dark moody lighting (one dim lamp, blue moonlight outside)
- Night city visible through the broken window

Run headless:
    blender --background --python scripts/blender_glass_shatter.py

Output: footage/.../blender/glass_shatter_####.png (frame sequence)
        footage/.../blender/glass_shatter.mp4 (final video)
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
RESOLUTION_X = 1920
RESOLUTION_Y = 1080
FPS = 30
TOTAL_FRAMES = 150  # 5 seconds
SHARD_COUNT = 40    # number of glass fragments
RENDER_ENGINE = "EEVEE"  # EEVEE for speed, CYCLES for quality
RENDER_SAMPLES = 64  # for EEVEE: 64 is fine; for CYCLES: 128+ recommended

random.seed(42)
np.random.seed(42)


def clear_scene():
    """Remove all default objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Remove default collections' objects
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for light in bpy.data.lights:
        bpy.data.lights.remove(light)
    for cam in bpy.data.cameras:
        bpy.data.cameras.remove(cam)


def create_material(name, color, roughness=0.5, metallic=0.0,
                    emission=None, alpha=1.0, glass=False):
    """Create a PBR material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear defaults
    for n in nodes:
        nodes.remove(n)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    if glass:
        # Glass shader for window
        bsdf = nodes.new('ShaderNodeBsdfGlass')
        bsdf.inputs['Color'].default_value = (*color[:3], 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['IOR'].default_value = 1.52  # glass
        mat.blend_method = 'HASHED' if hasattr(mat, 'blend_method') else 'OPAQUE'
    else:
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (*color[:3], 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emission:
            bsdf.inputs['Emission Color'].default_value = (*emission[:3], 1.0)
            bsdf.inputs['Emission Strength'].default_value = emission[3] if len(emission) > 3 else 1.0

    bsdf.location = (0, 0)
    links.new(bsdf.outputs[0], output.inputs[0])

    return mat


def create_room():
    """Create the hotel room geometry."""
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor_mat = create_material("FloorMat", (0.08, 0.06, 0.05), roughness=0.85)
    floor.data.materials.append(floor_mat)

    # Ceiling
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 3.0))
    ceiling = bpy.context.active_object
    ceiling.name = "Ceiling"
    ceiling.rotation_euler = (math.pi, 0, 0)
    ceil_mat = create_material("CeilingMat", (0.12, 0.11, 0.10), roughness=0.9)
    ceiling.data.materials.append(ceil_mat)

    # Back wall (behind camera)
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, -4, 1.5))
    back_wall = bpy.context.active_object
    back_wall.name = "BackWall"
    back_wall.rotation_euler = (math.pi / 2, 0, 0)
    back_wall.scale = (1, 1, 0.375)  # 3m tall
    wall_mat = create_material("WallMat", (0.15, 0.12, 0.10), roughness=0.8)
    back_wall.data.materials.append(wall_mat)

    # Side walls
    for side, x_pos in [("Left", -4), ("Right", 4)]:
        bpy.ops.mesh.primitive_plane_add(size=8, location=(x_pos, 0, 1.5))
        wall = bpy.context.active_object
        wall.name = f"{side}Wall"
        wall.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        wall.scale = (1, 1, 0.375)
        wall.data.materials.append(wall_mat)

    # Front wall (with window opening) — two sections around window
    window_width = 2.0
    window_height = 2.2
    window_bottom = 0.8
    window_center_x = 0.0
    window_center_y = 4.0  # front wall

    # Left section of front wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-2.5, 4, 1.5))
    left_wall = bpy.context.active_object
    left_wall.name = "FrontWallLeft"
    left_wall.scale = (1.5, 0.05, 1.5)
    left_wall.data.materials.append(wall_mat)

    # Right section
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.5, 4, 1.5))
    right_wall = bpy.context.active_object
    right_wall.name = "FrontWallRight"
    right_wall.scale = (1.5, 0.05, 1.5)
    right_wall.data.materials.append(wall_mat)

    # Top section (above window)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4, 2.85))
    top_wall = bpy.context.active_object
    top_wall.name = "FrontWallTop"
    top_wall.scale = (1.0, 0.05, 0.15)
    top_wall.data.materials.append(wall_mat)

    # Bottom section (below window)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 4, 0.35))
    bot_wall = bpy.context.active_object
    bot_wall.name = "FrontWallBot"
    bot_wall.scale = (1.0, 0.05, 0.35)
    bot_wall.data.materials.append(wall_mat)

    # Window frame
    frame_mat = create_material("FrameMat", (0.25, 0.22, 0.18), roughness=0.6, metallic=0.3)
    for name, loc, scale in [
        ("FrameTop", (0, 4, 2.7), (1.05, 0.03, 0.04)),
        ("FrameBot", (0, 4, 0.75), (1.05, 0.03, 0.04)),
        ("FrameLeft", (-1.0, 4, 1.725), (0.04, 0.03, 0.975)),
        ("FrameRight", (1.0, 4, 1.725), (0.04, 0.03, 0.975)),
        ("FrameMid", (0, 4, 1.725), (0.02, 0.03, 0.975)),
    ]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        frame = bpy.context.active_object
        frame.name = name
        frame.scale = scale
        frame.data.materials.append(frame_mat)

    return window_center_x, window_center_y, window_bottom, window_width, window_height


def create_venetian_blinds(win_x, win_y, win_bottom, win_w, win_h):
    """Create venetian blind slats above window — intact (key forensic detail)."""
    blind_mat = create_material("BlindMat", (0.3, 0.28, 0.25), roughness=0.7, metallic=0.2)
    slat_count = 8
    slat_height = 0.025

    for i in range(slat_count):
        y_offset = win_h * (i + 1) / (slat_count + 1) + win_bottom
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(win_x, win_y - 0.02, y_offset)
        )
        slat = bpy.context.active_object
        slat.name = f"BlindSlat_{i}"
        slat.scale = (win_w / 2 - 0.05, 0.01, slat_height)

        if i >= 5:
            # Bottom blinds slightly askew (disturbed but not destroyed)
            slat.rotation_euler = (random.uniform(-0.05, 0.05),
                                   random.uniform(-0.02, 0.02),
                                   random.uniform(-0.03, 0.03))
        slat.data.materials.append(blind_mat)


def create_glass_shards(win_x, win_y, win_bottom, win_w, win_h, count=40):
    """
    Create glass shards using Voronoi-like pattern.
    Each shard is a separate object for individual animation.
    """
    glass_mat = create_material("GlassMat", (0.85, 0.9, 1.0), roughness=0.02, glass=True)

    # Generate Voronoi seed points within window bounds
    half_w = win_w / 2 - 0.05
    half_h = win_h / 2 - 0.05
    center_z = win_bottom + win_h / 2

    # Create seed points — more dense near center (impact point)
    seeds = []
    for _ in range(count):
        # Gaussian distribution centered on impact point
        x = np.clip(np.random.normal(0, half_w * 0.5), -half_w, half_w)
        z = np.clip(np.random.normal(center_z, half_h * 0.4), win_bottom, win_bottom + win_h)
        seeds.append((x + win_x, z))

    shards = []
    for i, (sx, sz) in enumerate(seeds):
        # Create a shard as a simple polygon
        shard_size = random.uniform(0.05, 0.25)
        vertices = random.randint(3, 6)

        # Generate irregular polygon vertices
        bm = bmesh.new()
        angles = sorted([random.uniform(0, 2 * math.pi) for _ in range(vertices)])
        verts = []
        for angle in angles:
            r = shard_size * random.uniform(0.5, 1.0)
            vx = math.cos(angle) * r
            vz = math.sin(angle) * r
            verts.append(bm.verts.new((vx, 0, vz)))
        bm.verts.ensure_lookup_table()

        # Create face
        try:
            bm.faces.new(verts)
        except ValueError:
            bm.free()
            continue

        # Create mesh and object
        mesh = bpy.data.meshes.new(f"ShardMesh_{i}")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Shard_{i}", mesh)
        bpy.context.collection.objects.link(obj)

        # Position at window surface
        obj.location = (sx, win_y + 0.01, sz)
        obj.data.materials.append(glass_mat)

        # Give each shard a slight thickness (solidify would be ideal but let's extrude)
        # Actually just use the flat polygon — glass is thin

        shards.append({
            'obj': obj,
            'origin_x': sx,
            'origin_z': sz,
            'size': shard_size,
        })

    return shards


def animate_shards(shards, total_frames, shatter_frame=30):
    """
    Animate glass shards flying outward from window.
    Before shatter_frame: glass is intact (shards form a flat plane)
    At shatter_frame: explosion outward
    After: shards fly toward camera with gravity and rotation
    """
    for shard_info in shards:
        obj = shard_info['obj']
        ox = shard_info['origin_x']
        oz = shard_info['origin_z']
        size = shard_info['size']

        # Before shatter: glass is at window position
        obj.location = (ox, 4.01, oz)
        obj.rotation_euler = (0, 0, 0)
        obj.keyframe_insert(data_path="location", frame=1)
        obj.keyframe_insert(data_path="rotation_euler", frame=1)
        obj.keyframe_insert(data_path="location", frame=shatter_frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=shatter_frame)

        # At shatter: each shard gets an outward velocity
        # Direction: mostly toward camera (-Y), some spread in X and Z
        speed = random.uniform(2.0, 8.0)
        spread_x = random.uniform(-1.5, 1.5)
        spread_z = random.uniform(-1.0, 2.0)  # slight upward bias

        # Rotation speed
        rot_x = random.uniform(-3, 3)
        rot_y = random.uniform(-3, 3)
        rot_z = random.uniform(-3, 3)

        # Gravity
        gravity = -9.8

        # Animate frames after shatter
        for f in range(shatter_frame + 1, total_frames + 1):
            dt = (f - shatter_frame) / FPS  # seconds since shatter

            new_x = ox + spread_x * dt
            new_y = 4.01 - speed * dt  # flying toward camera
            new_z = oz + spread_z * dt + 0.5 * gravity * dt * dt

            obj.location = (new_x, new_y, max(-0.5, new_z))
            obj.rotation_euler = (rot_x * dt, rot_y * dt, rot_z * dt)

            obj.keyframe_insert(data_path="location", frame=f)
            obj.keyframe_insert(data_path="rotation_euler", frame=f)

            # Make shards smaller as they get further (if they've passed camera)
            if new_y < -2:
                obj.scale = (max(0.01, 1 - ((-2 - new_y) / 5)),) * 3
                obj.keyframe_insert(data_path="scale", frame=f)


def create_furniture():
    """Add basic hotel room furniture for depth."""
    dark_wood = create_material("DarkWood", (0.06, 0.04, 0.03), roughness=0.7)
    bed_mat = create_material("BedMat", (0.15, 0.13, 0.12), roughness=0.9)

    # Two beds (simplified as boxes)
    for bx, name in [(-1.8, "BedLeft"), (1.8, "BedRight")]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, 0, 0.4))
        bed = bpy.context.active_object
        bed.name = name
        bed.scale = (0.8, 1.2, 0.4)
        bed.data.materials.append(bed_mat)

    # Nightstand between beds
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.35))
    nightstand = bpy.context.active_object
    nightstand.name = "Nightstand"
    nightstand.scale = (0.25, 0.25, 0.35)
    nightstand.data.materials.append(dark_wood)


def create_lighting():
    """Set up dark, moody lighting for 3am hotel room."""
    # Dim table lamp on nightstand (warm, very low)
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 0.9))
    lamp = bpy.context.active_object
    lamp.name = "TableLamp"
    lamp.data.energy = 5.0  # very dim
    lamp.data.color = (1.0, 0.8, 0.5)  # warm
    lamp.data.shadow_soft_size = 0.3

    # Blue moonlight from outside the window
    bpy.ops.object.light_add(type='AREA', location=(0, 6, 2.5))
    moonlight = bpy.context.active_object
    moonlight.name = "Moonlight"
    moonlight.rotation_euler = (-math.pi / 4, 0, 0)
    moonlight.data.energy = 20.0
    moonlight.data.color = (0.4, 0.5, 0.8)  # cold blue
    moonlight.data.size = 3.0

    # Very faint fill light (ambient)
    bpy.ops.object.light_add(type='POINT', location=(0, -2, 2.5))
    fill = bpy.context.active_object
    fill.name = "FillLight"
    fill.data.energy = 1.0  # barely there
    fill.data.color = (0.3, 0.3, 0.4)

    # Set world to near-black
    world = bpy.data.worlds.get("World")
    if world is None:
        world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.005, 0.005, 0.015, 1.0)
        bg.inputs['Strength'].default_value = 1.0


def create_camera():
    """Set up camera inside the room looking at the window."""
    bpy.ops.object.camera_add(location=(0, -2.5, 1.6))
    cam = bpy.context.active_object
    cam.name = "MainCamera"
    cam.rotation_euler = (math.pi / 2 - 0.05, 0, 0)  # looking slightly up at window

    cam.data.lens = 28  # wide angle for room interior
    cam.data.clip_start = 0.1
    cam.data.clip_end = 100

    # Depth of field for cinematic look
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 6.5  # focus on window
    cam.data.dof.aperture_fstop = 2.8

    bpy.context.scene.camera = cam

    # Slight camera shake after the shatter (keyframe)
    shatter_frame = 30
    cam.keyframe_insert(data_path="location", frame=1)
    cam.keyframe_insert(data_path="rotation_euler", frame=1)
    cam.keyframe_insert(data_path="location", frame=shatter_frame)
    cam.keyframe_insert(data_path="rotation_euler", frame=shatter_frame)

    # Camera shake
    for f in range(shatter_frame + 1, shatter_frame + 15):
        shake_intensity = 0.03 * max(0, 1 - (f - shatter_frame) / 15)
        cam.location = (
            random.uniform(-shake_intensity, shake_intensity),
            -2.5 + random.uniform(-shake_intensity, shake_intensity),
            1.6 + random.uniform(-shake_intensity, shake_intensity),
        )
        cam.keyframe_insert(data_path="location", frame=f)

    # Return to rest
    cam.location = (0, -2.5, 1.6)
    cam.keyframe_insert(data_path="location", frame=shatter_frame + 15)

    return cam


def setup_render():
    """Configure render settings."""
    scene = bpy.context.scene
    scene.render.resolution_x = RESOLUTION_X
    scene.render.resolution_y = RESOLUTION_Y
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    if RENDER_ENGINE == "CYCLES":
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = RENDER_SAMPLES
        scene.cycles.use_denoising = True
        # Use GPU if available
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
        bpy.context.preferences.addons['cycles'].preferences.get_devices()
        for device in bpy.context.preferences.addons['cycles'].preferences.devices:
            device.use = True
        scene.cycles.device = 'GPU'
    else:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.eevee.taa_render_samples = RENDER_SAMPLES
        # Enable screen space reflections for glass
        scene.eevee.use_ssr = True
        scene.eevee.use_ssr_refraction = True

    # Output settings
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Compositing — add slight bloom/glare for glass sparkle
    scene.use_nodes = True
    tree = scene.node_tree
    # Clear existing
    for n in tree.nodes:
        tree.nodes.remove(n)

    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (0, 0)

    # Glare for glass sparkle
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.mix = 0.1  # subtle
    glare.threshold = 0.8
    glare.location = (300, 0)

    composite = tree.nodes.new('CompositorNodeComposite')
    composite.location = (600, 0)

    tree.links.new(render_layers.outputs['Image'], glare.inputs['Image'])
    tree.links.new(glare.outputs['Image'], composite.inputs['Image'])


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("BLENDER: Hotel Window Glass Shatter at 3am")
    print("=" * 60)

    print("\n[1/7] Clearing scene...")
    clear_scene()

    print("[2/7] Creating room geometry...")
    win_x, win_y, win_bottom, win_w, win_h = create_room()

    print("[3/7] Creating venetian blinds...")
    create_venetian_blinds(win_x, win_y, win_bottom, win_w, win_h)

    print("[4/7] Creating glass shards...")
    shards = create_glass_shards(win_x, win_y, win_bottom, win_w, win_h, count=SHARD_COUNT)

    print("[5/7] Adding furniture and lighting...")
    create_furniture()
    create_lighting()

    print("[6/7] Setting up camera and animation...")
    create_camera()
    animate_shards(shards, TOTAL_FRAMES, shatter_frame=30)

    print("[7/7] Configuring render...")
    setup_render()

    # Save .blend file for manual inspection/tweaking
    blend_path = os.path.join(OUTPUT_DIR, "glass_shatter_scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n  Scene saved: {blend_path}")
    print(f"  (Open in Blender to inspect/tweak before rendering)")

    # Render animation
    output_path = os.path.join(OUTPUT_DIR, "glass_shatter_")
    bpy.context.scene.render.filepath = output_path

    print(f"\n  Rendering {TOTAL_FRAMES} frames to: {OUTPUT_DIR}/")
    print(f"  Engine: {RENDER_ENGINE}, Samples: {RENDER_SAMPLES}")
    print(f"  Resolution: {RESOLUTION_X}x{RESOLUTION_Y} @ {FPS}fps")
    print(f"  This may take a few minutes...\n")

    bpy.ops.render.render(animation=True)

    # Convert frame sequence to video
    mp4_path = os.path.join(OUTPUT_DIR, "glass_shatter.mp4")
    print(f"\n  Converting frames to video: {mp4_path}")
    os.system(
        f'ffmpeg -y -framerate {FPS} -i "{output_path}%04d.png" '
        f'-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p '
        f'"{mp4_path}" 2>/dev/null'
    )

    if os.path.exists(mp4_path):
        size_mb = os.path.getsize(mp4_path) / (1024 * 1024)
        print(f"\n  DONE: {mp4_path} ({size_mb:.1f} MB)")
    else:
        print(f"\n  Video conversion failed. Frames are at: {output_path}*.png")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
