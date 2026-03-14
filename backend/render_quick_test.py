"""
Quick test render of iPhone 15 Pro FRONT view (screen side)
Low samples for fast testing
"""

import bpy
import os
import math

MODEL_PATH = "/app/backend/iphone_15_model/source/apple_iphone_15_pro_max_black(2).glb"
OUTPUT_PATH = "/app/backend/uploads/iphone_front_test.png"

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def main():
    clear_scene()
    
    # Import model
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        print("No meshes!")
        return
    
    # Join all meshes
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    
    phone = bpy.context.active_object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    phone.location = (0, 0, 0)
    
    # FRONT facing - rotate 180 degrees
    phone.rotation_euler = (math.radians(90), 0, math.radians(180))
    
    # Scale
    dims = phone.dimensions
    max_dim = max(dims)
    if max_dim > 0:
        scale = 2.0 / max_dim
        phone.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
    
    # Camera
    bpy.ops.object.camera_add(location=(0, -5, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = camera
    camera.data.lens = 50
    
    # Single key light
    bpy.ops.object.light_add(type='SUN', location=(0, -2, 3))
    light = bpy.context.active_object
    light.data.energy = 3
    
    # Render settings - FAST
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 540
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    
    # Minimal samples for speed
    scene.eevee.taa_render_samples = 8
    
    # Render
    scene.render.filepath = OUTPUT_PATH
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
