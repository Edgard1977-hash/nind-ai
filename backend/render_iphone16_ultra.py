"""
Render iPhone 16 at ultra-smooth angles (step 2°)
Total: 46 images for buttery smooth animation
"""

import bpy
import os
import math

MODEL_PATH = "/app/backend/iphone_16_model/source/iphone_16_black.glb"
OUTPUT_DIR = "/app/backend/iphone_16_renders_ultra"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RES_X = 800
RES_Y = 1600
SAMPLES = 12

# Step 2 degrees: -45 to +45 = 46 images
ANGLES = list(range(-45, 46, 2))

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def import_and_setup_phone():
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        return None
    
    bpy.ops.object.empty_add(location=(0, 0, 0))
    parent = bpy.context.active_object
    parent.name = "iPhone16"
    
    for obj in meshes:
        obj.parent = parent
    
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for obj in meshes:
        for v in obj.data.vertices:
            world_v = obj.matrix_world @ v.co
            min_x, max_x = min(min_x, world_v.x), max(max_x, world_v.x)
            min_y, max_y = min(min_y, world_v.y), max(max_y, world_v.y)
            min_z, max_z = min(min_z, world_v.z), max(max_z, world_v.z)
    
    cx, cy, cz = (min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2
    for obj in meshes:
        obj.location.x -= cx
        obj.location.y -= cy
        obj.location.z -= cz
    
    max_dim = max(max_x-min_x, max_y-min_y, max_z-min_z)
    parent.scale = (2.0/max_dim, 2.0/max_dim, 2.0/max_dim)
    
    return parent

def setup_scene():
    # Camera
    bpy.ops.object.camera_add(location=(0, -5.5, 0))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    cam.data.lens = 55
    
    # Lighting
    bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
    bpy.context.active_object.data.energy = 500
    bpy.context.active_object.data.size = 5
    
    bpy.ops.object.light_add(type='AREA', location=(-3, -4, 3))
    bpy.context.active_object.data.energy = 200
    bpy.context.active_object.data.size = 4
    
    bpy.ops.object.light_add(type='AREA', location=(0, 4, 3))
    bpy.context.active_object.data.energy = 300
    bpy.context.active_object.data.size = 6
    
    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.eevee.taa_render_samples = SAMPLES

def render_angle(phone, angle, path):
    phone.rotation_euler = (0, 0, math.radians(angle))
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {angle}°")

def main():
    print(f"Rendering {len(ANGLES)} angles (step 2°)")
    clear_scene()
    phone = import_and_setup_phone()
    if not phone:
        return
    setup_scene()
    
    for angle in ANGLES:
        sign = '+' if angle >= 0 else ''
        path = os.path.join(OUTPUT_DIR, f"iphone_{sign}{angle:03d}.png")
        render_angle(phone, angle, path)
    
    print("Done!")

if __name__ == "__main__":
    main()
