import bpy
import os
import sys
import math

# Paths
MODEL_PATH = "/app/backend/iphone_15_model/source/apple_iphone_15_pro_max_black(2).glb"
OUTPUT_DIR = "/app/backend/iphone_3d_renders"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Resolution
RES_X = 800
RES_Y = 1600

# Angles to render
ANGLES = [-40, -30, -20, -10, 0, 10, 20, 30, 40]

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

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
    
    # Rotate to show screen (front side)
    # Model might be facing wrong direction - adjust as needed
    phone.rotation_euler = (math.radians(90), 0, 0)
    
    # Scale to reasonable size
    dims = phone.dimensions
    max_dim = max(dims)
    if max_dim > 0:
        scale = 2.0 / max_dim
        phone.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
    
    return phone

def setup_camera():
    bpy.ops.object.camera_add(location=(0, -5, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = camera
    
    # Camera settings
    camera.data.type = 'PERSP'
    camera.data.lens = 50
    
    return camera

def setup_lighting():
    # Key light
    bpy.ops.object.light_add(type='AREA', location=(3, -3, 4))
    key = bpy.context.active_object
    key.data.energy = 300
    key.data.size = 3
    key.rotation_euler = (math.radians(45), math.radians(30), 0)
    
    # Fill light  
    bpy.ops.object.light_add(type='AREA', location=(-3, -3, 3))
    fill = bpy.context.active_object
    fill.data.energy = 150
    fill.data.size = 2
    fill.rotation_euler = (math.radians(45), math.radians(-30), 0)
    
    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 2))
    rim = bpy.context.active_object
    rim.data.energy = 100
    rim.data.size = 4

def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # EEVEE settings
    scene.eevee.taa_render_samples = 64
    scene.eevee.use_soft_shadows = True

def render_angle(phone, angle, output_path):
    # Reset rotation
    phone.rotation_euler = (math.radians(90), 0, 0)
    # Apply Y rotation (horizontal turn)
    phone.rotation_euler.z = math.radians(angle)
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered angle {angle} -> {output_path}")

def main():
    clear_scene()
    
    phone = import_model()
    if not phone:
        print("Failed to import model")
        return
    
    setup_camera()
    setup_lighting()
    setup_render()
    
    for angle in ANGLES:
        output_path = os.path.join(OUTPUT_DIR, f"iphone_angle_{angle}.png")
        render_angle(phone, angle, output_path)
    
    print(f"\nDone! Renders saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
