import bpy
import sys
import os
import math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    # Clear all materials too
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

def setup_camera(rotation_y=12, distance=2.5):
    # Calculate camera position
    angle = math.radians(rotation_y)
    x = math.sin(angle) * distance
    y = -math.cos(angle) * distance
    z = 0.5
    
    bpy.ops.object.camera_add(location=(x, y, z))
    camera = bpy.context.object
    
    # Point camera at origin
    direction = bpy.context.object.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # Adjust to look at phone center (which is around z=0)
    camera.rotation_euler = (math.radians(90), 0, math.radians(rotation_y))
    
    bpy.context.scene.camera = camera
    return camera

def setup_lighting():
    # Key light - soft area light
    bpy.ops.object.light_add(type='AREA', location=(3, -2, 4))
    key = bpy.context.object
    key.data.energy = 800
    key.data.size = 5
    key.rotation_euler = (math.radians(45), 0, math.radians(30))
    
    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-3, -2, 3))
    fill = bpy.context.object
    fill.data.energy = 300
    fill.data.size = 4
    
    # Back light  
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 2))
    rim = bpy.context.object
    rim.data.energy = 400
    rim.data.size = 3

def create_simple_material(name, color):
    """Create a simple material without textures"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    
    # Get principled BSDF
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.8
        bsdf.inputs['Roughness'].default_value = 0.3
    
    return mat

def import_and_fix_gltf(filepath):
    """Import GLTF and replace materials with simple ones"""
    try:
        bpy.ops.import_scene.gltf(
            filepath=filepath,
            import_shading='FLAT'  # Use flat shading to avoid material issues
        )
    except Exception as e:
        print(f"Import error: {e}")
        # Try importing without materials
        return None
    
    # Get all mesh objects
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    
    # Create replacement materials
    titanium_mat = create_simple_material("Titanium", (0.75, 0.75, 0.77))
    glass_mat = create_simple_material("Glass", (0.1, 0.1, 0.12))
    screen_mat = create_simple_material("Screen", (0.02, 0.02, 0.02))
    
    # Replace materials on all meshes
    for obj in meshes:
        for slot in obj.material_slots:
            name = slot.material.name.lower() if slot.material else ""
            if "screen" in name or "display" in name:
                slot.material = screen_mat
            elif "glass" in name:
                slot.material = glass_mat
            else:
                slot.material = titanium_mat
    
    return meshes

def setup_render(width=1080, height=1920, samples=32):
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    
    # Use Eevee for faster rendering
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    
    # Transparent background
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

def render_frame(output_path, rotation_y=12):
    clear_scene()
    
    gltf_path = "/app/backend/iphone_model/source/1b338ec19f15ad72904b (1).gltf"
    
    # Try direct import first
    try:
        bpy.ops.import_scene.gltf(filepath=gltf_path)
        print("GLTF imported successfully")
    except Exception as e:
        print(f"GLTF import failed: {e}")
        return False
    
    # Scale and position
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.scale = (0.13, 0.13, 0.13)
    
    setup_lighting()
    setup_camera(rotation_y)
    setup_render()
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    return True

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    output = argv[0] if len(argv) > 0 else "/tmp/iphone_render.png"
    rotation = float(argv[1]) if len(argv) > 1 else 12
    
    success = render_frame(output, rotation)
    print(f"Render {'successful' if success else 'failed'}: {output}")
