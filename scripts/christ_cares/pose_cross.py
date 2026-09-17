# Poses the subject on the cross, per stage 7 of research/christ_cares/crucifixion_medical_stages_v1.json:
# arms roughly horizontal with wrists slightly above shoulder level (Roman-era graffiti),
# 65-75 deg from vertical (Zugibe's volunteers), body sagging forward, knees out,
# heels nailed through the calcaneus to the sides of the upright (Zias & Sekeles; Ingham & Duhig).
# Run inside Blender: exec(open(path).read()); pose_on_cross()  /  rest_pose()
import bpy, math, mathutils

RIG = "Subject_Body.rig"
FK = {"spine03": 6, "spine02": 6, "spine01": 5, "neck01": 18, "neck02": 16, "neck03": 12, "head": 22}
FOOT_PLANTARFLEX = -45
FINGER_CURL = {2: (25, 35, 20), 3: (30, 40, 25), 4: (45, 55, 35), 5: (50, 60, 40)}   # thumb (1) stays straight

def _pb():
    return bpy.data.objects[RIG].pose.bones

def rest_pose():
    """Clear the pose and mute the rig constraints (for flat wound-map checks)."""
    for pb in _pb():
        pb.matrix_basis.identity()
        for c in pb.constraints:
            c.mute = True
    bpy.context.view_layer.update()

def pose_on_cross():
    rig = bpy.data.objects[RIG]
    pb = rig.pose.bones
    for p in pb:
        p.matrix_basis.identity()
        for c in p.constraints:
            c.mute = False
    for name, deg in FK.items():
        pb[name].rotation_mode = 'XYZ'
        pb[name].rotation_euler = (math.radians(deg), 0, 0)
    for s in ("L", "R"):
        pb[f"foot.{s}"].rotation_mode = 'XYZ'
        pb[f"foot.{s}"].rotation_euler = (math.radians(FOOT_PLANTARFLEX), 0, 0)
        for f, degs in FINGER_CURL.items():                 # median-nerve claw (Edwards)
            for j, d in zip((1, 2, 3), degs):
                b = pb[f"finger{f}-{j}.{s}"]
                b.rotation_mode = 'XYZ'
                b.rotation_euler = (math.radians(d), 0, 0)
    bpy.context.view_layer.update()

def show_cross(on=True):
    for n in ("Stipes", "Patibulum", "Nail_wrist.L", "Nail_wrist.R",
              "Nail_heel.L", "Nail_heel.R", "Loincloth", "Ground"):
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = not on
            o.hide_viewport = False

def set_stage(stage):
    """stage: one of wounds_s3_scourged / s4_thorns / s5_crossbar / s6_nailed / s9_spear, or None."""
    body = bpy.data.objects["Subject_Body"]
    img = bpy.data.images.get(stage) if stage else None
    for slot in body.material_slots:
        tex = slot.material.node_tree.nodes.get("WoundTex")
        if tex:
            tex.image = img
    # the crown is only on his head from stage 4 onward
    crown = bpy.data.objects.get("CrownOfThorns")
    if crown:
        worn = bool(stage) and stage not in ("wounds_s3_scourged",)
        crown.hide_render = not worn
        crown.hide_viewport = not worn
