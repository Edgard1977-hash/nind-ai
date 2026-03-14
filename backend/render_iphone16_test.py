"""
Quick test render of iPhone 16 Black - check if it shows FRONT (screen)
"""

import bpy
import os
import math

MODEL_PATH = "/app/backend/iphone_16_model/source/iphone_16_black.glb"
OUTPUT_PATH = "/app/backend/uploads/iphone16_test.png"

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def main():
    clear_scene()
    
    # Import model
    print(f"Loading: {MODEL_PATH}")
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        print("No meshes found!")
        return
    
    print(f"Found {len(meshes)} mesh objects")
    
    # Join all meshes
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    
    phone = bpy.context.active_object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    phone.location = (0, 0, 0)
    
    # Try default orientation first
    phone.rotation_euler = (math.radians(90), 0, 0)
    
    # Scale
    dims = phone.dimensions
    print(f"Model dimensions: {dims}")
    max_dim = max(dims)
    if max_dim > 0:
        scale = 2.0 / max_dim
        phone.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
    
    # Camera - front view
    bpy.ops.object.camera_add(location=(0, -5, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = camera
    camera.data.lens = 50
    
    # Simple lighting
    bpy.ops.object.light_add(type='SUN', location=(2, -3, 4))
    sun = bpy.context.active_object
    sun.data.energy = 3
    
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 2))
    fill = bpy.context.active_object
    fill.data.energy = 150
    fill.data.size = 3
    
    # Render settings - fast
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 540
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.eevee.taa_render_samples = 8
    
    # Render
    scene.render.filepath = OUTPUT_PATH
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
