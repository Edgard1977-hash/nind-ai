"""
Blender script to render iPhone 15 Pro FRONT view (screen side)
The previous renders showed the BACK of the phone - we need the FRONT
"""

import bpy
import os
import sys
import math

# Paths
MODEL_PATH = "/app/backend/iphone_15_model/source/apple_iphone_15_pro_max_black(2).glb"
OUTPUT_DIR = "/app/backend/iphone_15_renders_front"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Resolution - high quality
RES_X = 1080
RES_Y = 2160

# Angles to render (Y rotation)
ANGLES = [-40, -30, -20, -10, 0, 10, 20, 30, 40]

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def import_model():
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    # Get all imported mesh objects
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        print("No meshes found!")
        return None
    
    # Join all meshes into one object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    
    phone = bpy.context.active_object
    
    # Center origin
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    phone.location = (0, 0, 0)
    
    # Rotate to show FRONT (screen) - add 180 degrees rotation
    # Base rotation to stand up + 180 to show front
    phone.rotation_euler = (math.radians(90), 0, math.radians(180))
    
    # Scale to reasonable size
    dims = phone.dimensions
    max_dim = max(dims)
    if max_dim > 0:
        scale = 2.0 / max_dim
        phone.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
    
    return phone

def setup_camera():
    # Camera looking at front of phone
    bpy.ops.object.camera_add(location=(0, -5, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = camera
    
    # Camera settings
    camera.data.type = 'PERSP'
    camera.data.lens = 50
    
    return camera

def setup_lighting():
    # Key light - front-left
    bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
    key = bpy.context.active_object
    key.data.energy = 400
    key.data.size = 4
    key.rotation_euler = (math.radians(45), math.radians(30), 0)
    
    # Fill light - front-right
    bpy.ops.object.light_add(type='AREA', location=(-3, -3, 3))
    fill = bpy.context.active_object
    fill.data.energy = 200
    fill.data.size = 3
    fill.rotation_euler = (math.radians(45), math.radians(-30), 0)
    
    # Rim light - back
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 2))
    rim = bpy.context.active_object
    rim.data.energy = 150
    rim.data.size = 4
    
    # Screen illumination - soft front light
    bpy.ops.object.light_add(type='AREA', location=(0, -2, 1))
    screen = bpy.context.active_object
    screen.data.energy = 100
    screen.data.size = 2

def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # EEVEE settings for quality
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_soft_shadows = True
    scene.eevee.shadow_cube_size = '1024'
    scene.eevee.shadow_cascade_size = '1024'

def render_angle(phone, angle, output_path):
    # Reset to front-facing base rotation
    phone.rotation_euler = (math.radians(90), 0, math.radians(180))
    # Apply Y rotation (horizontal turn)
    phone.rotation_euler.z = math.radians(180 + angle)
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered angle {angle} -> {output_path}")

def main():
    clear_scene()
    
    print(f"Loading model from: {MODEL_PATH}")
    phone = import_model()
    if not phone:
        print("Failed to import model")
        return
    
    print("Setting up camera...")
    setup_camera()
    
    print("Setting up lighting...")
    setup_lighting()
    
    print("Configuring render settings...")
    setup_render()
    
    print(f"Rendering {len(ANGLES)} angles...")
    for angle in ANGLES:
        output_path = os.path.join(OUTPUT_DIR, f"iphone15_front_angle_{angle}.png")
        render_angle(phone, angle, output_path)
    
    print(f"\nDone! Front-facing renders saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
