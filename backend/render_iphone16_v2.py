"""
Render iPhone 16 - FIXED ORIENTATION
Phone standing vertically with screen facing camera
"""

import bpy
import os
import math

MODEL_PATH = "/app/backend/iphone_16_model/source/iphone_16_black.glb"
OUTPUT_DIR = "/app/backend/iphone_16_renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Render settings
RES_X = 1080
RES_Y = 2160
SAMPLES = 16

# Angles to render
ANGLES = [-40, -30, -20, -10, 0, 10, 20, 30, 40]

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def import_and_setup_phone():
    """Import model and orient for front view"""
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        return None
    
    # Create parent empty
    bpy.ops.object.empty_add(location=(0, 0, 0))
    parent = bpy.context.active_object
    parent.name = "iPhone16"
    
    # Parent all meshes
    for obj in meshes:
        obj.parent = parent
    
    # Get bounds
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for obj in meshes:
        for v in obj.data.vertices:
            world_v = obj.matrix_world @ v.co
            min_x = min(min_x, world_v.x)
            max_x = max(max_x, world_v.x)
            min_y = min(min_y, world_v.y)
            max_y = max(max_y, world_v.y)
            min_z = min(min_z, world_v.z)
            max_z = max(max_z, world_v.z)
    
    # Center
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    cz = (min_z + max_z) / 2
    for obj in meshes:
        obj.location.x -= cx
        obj.location.y -= cy
        obj.location.z -= cz
    
    # Scale to fit in frame
    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    
    print(f"Model dimensions: X={size_x:.2f}, Y={size_y:.2f}, Z={size_z:.2f}")
    
    max_dim = max(size_x, size_y, size_z)
    scale = 2.0 / max_dim
    parent.scale = (scale, scale, scale)
    
    return parent

def setup_camera():
    # Camera at -Y looking at origin
    bpy.ops.object.camera_add(location=(0, -5.5, 0))
    camera = bpy.context.active_object
    # Looking straight at origin
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = camera
    camera.data.lens = 55
    return camera

def setup_lighting():
    # Key light
    bpy.ops.object.light_add(type='AREA', location=(4, -4, 5))
    key = bpy.context.active_object
    key.data.energy = 500
    key.data.size = 5
    key.rotation_euler = (math.radians(50), 0, math.radians(40))
    
    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-3, -4, 3))
    fill = bpy.context.active_object
    fill.data.energy = 200
    fill.data.size = 4
    
    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 4, 3))
    rim = bpy.context.active_object
    rim.data.energy = 300
    rim.data.size = 6

def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_soft_shadows = True

def render_angle(phone, angle, output_path):
    """
    The model appears to be:
    - X = width
    - Y = depth (thin side)
    - Z = height
    
    Screen faces -Y direction
    Camera is at -Y looking at +Y
    
    To rotate phone horizontally while showing screen:
    - Rotate around Z axis (vertical axis)
    """
    # Reset rotation
    phone.rotation_euler = (0, 0, 0)
    
    # Rotate around Z axis (horizontal rotation)
    phone.rotation_euler.z = math.radians(angle)
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered angle {angle}° -> {output_path}")

def main():
    print("=" * 50)
    print("iPhone 16 Render - FIXED ORIENTATION")
    print("=" * 50)
    
    clear_scene()
    
    print("Importing model...")
    phone = import_and_setup_phone()
    if not phone:
        print("Failed!")
        return
    
    print("Setting up scene...")
    setup_camera()
    setup_lighting()
    setup_render()
    
    print(f"Rendering {len(ANGLES)} angles...")
    for angle in ANGLES:
        output_path = os.path.join(OUTPUT_DIR, f"iphone16_angle_{angle}.png")
        render_angle(phone, angle, output_path)
    
    print("\nDone!")

if __name__ == "__main__":
    main()
