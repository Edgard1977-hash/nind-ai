"""
Blender script to render iPhone 16 3D model from GLTF
Run with: blender --background --python render_iphone.py -- <args>
"""

import bpy
import sys
import os
import math

def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_camera(rotation_y=15, float_offset=0):
    """Setup camera for iPhone render"""
    # Add camera
    bpy.ops.object.camera_add(location=(0, -3, 0.5 + float_offset * 0.01))
    camera = bpy.context.object
    camera.rotation_euler = (math.radians(90), 0, math.radians(rotation_y))
    
    bpy.context.scene.camera = camera
    return camera

def setup_lighting():
    """Setup 3-point lighting"""
    # Key light
    bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
    key = bpy.context.object
    key.data.energy = 500
    key.data.size = 3
    key.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 2))
    fill = bpy.context.object
    fill.data.energy = 200
    fill.data.size = 2
    
    # Rim light
    bpy.ops.object.light_add(type='AREA', location=(0, 2, 2))
    rim = bpy.context.object
    rim.data.energy = 300
    rim.data.size = 2

def import_gltf(filepath):
    """Import GLTF model"""
    bpy.ops.import_scene.gltf(filepath=filepath)
    
    # Get imported objects
    imported = [obj for obj in bpy.context.selected_objects]
    
    # Center and scale
    for obj in imported:
        if obj.type == 'MESH':
            # Scale to fit view
            obj.scale = (0.15, 0.15, 0.15)
            obj.location = (0, 0, 0)
    
    return imported

def setup_render(width=1080, height=1920, samples=64):
    """Setup render settings"""
    scene = bpy.context.scene
    
    # Resolution
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    
    # Engine
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    
    # Transparent background
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

def render_frame(output_path, rotation_y=15, float_offset=0):
    """Render a single frame"""
    clear_scene()
    
    # Import model
    gltf_path = "/app/backend/iphone_model/source/1b338ec19f15ad72904b (1).gltf"
    import_gltf(gltf_path)
    
    # Setup scene
    setup_lighting()
    setup_camera(rotation_y, float_offset)
    setup_render()
    
    # Render
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    # Get arguments after --
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    output = argv[0] if len(argv) > 0 else "/tmp/iphone_render.png"
    rotation = float(argv[1]) if len(argv) > 1 else 15
    float_off = float(argv[2]) if len(argv) > 2 else 0
    
    render_frame(output, rotation, float_off)
    print(f"Rendered to {output}")
