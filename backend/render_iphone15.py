import bpy
import os
import sys
import math

# Configuration
MODEL_PATH = "/app/backend/iphone_15_model/source/apple_iphone_15_pro_max_black(2).glb"
OUTPUT_DIR = "/app/backend/iphone_15_renders"
RESOLUTION_X = 1080
RESOLUTION_Y = 2160  # Taller to capture full phone

# Angles to render (degrees)
ANGLES = [0, 10, 20, 30, 40, -10, -20, -30, -40]

def setup_scene():
    """Clear scene and setup for rendering"""
    # Delete all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import GLB model
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    # Get imported objects and join them
    imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not imported_objects:
        print("ERROR: No mesh objects imported!")
        return None
    
    # Select all meshes and join
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported_objects[0]
    
    if len(imported_objects) > 1:
        bpy.ops.object.join()
    
    phone = bpy.context.active_object
    
    # Center and scale
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    phone.location = (0, 0, 0)
    
    # Calculate scale to fit in frame
    dims = phone.dimensions
    max_dim = max(dims)
    scale = 1.5 / max_dim if max_dim > 0 else 1
    phone.scale = (scale, scale, scale)
    bpy.ops.object.transform_apply(scale=True)
    
    return phone

def setup_camera():
    """Create and position camera"""
    # Add camera
    bpy.ops.object.camera_add(location=(0, -3, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(90), 0, 0)
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    return camera

def setup_lighting():
    """Setup studio lighting"""
    # Key light
    bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
    key_light = bpy.context.active_object
    key_light.data.energy = 200
    key_light.data.size = 4
    key_light.rotation_euler = (math.radians(45), math.radians(30), 0)
    
    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 2))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 100
    fill_light.data.size = 3
    fill_light.rotation_euler = (math.radians(45), math.radians(-30), 0)
    
    # Back light
    bpy.ops.object.light_add(type='AREA', location=(0, 2, 3))
    back_light = bpy.context.active_object
    back_light.data.energy = 80
    back_light.data.size = 5

def setup_render_settings():
    """Configure render settings"""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = RESOLUTION_X
    scene.render.resolution_y = RESOLUTION_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True  # Transparent background
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # EEVEE settings for quality
    scene.eevee.taa_render_samples = 32
    scene.eevee.use_soft_shadows = True

def render_angle(phone, angle, output_path):
    """Render phone at specific rotation angle"""
    # Reset rotation
    phone.rotation_euler = (0, 0, 0)
    
    # Apply Y rotation (horizontal turn)
    phone.rotation_euler.z = math.radians(angle)
    
    # Render
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered angle {angle} to {output_path}")

def main():
    """Main render function"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    phone = setup_scene()
    if not phone:
        print("Failed to setup scene")
        return
    
    setup_camera()
    setup_lighting()
    setup_render_settings()
    
    # Render each angle
    for angle in ANGLES:
        output_file = os.path.join(OUTPUT_DIR, f"iphone15_angle_{angle}.png")
        render_angle(phone, angle, output_file)
    
    print(f"Rendering complete! Files saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
