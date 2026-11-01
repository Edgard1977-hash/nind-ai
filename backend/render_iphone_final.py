"""
Blender script to render iPhone 16 3D model with custom screen content
Supports: rotation animation, floating animation, screen replacement
"""

import bpy
import sys
import math
import os

def clear_scene():
    """Clear all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Clear orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def setup_camera(rotation_y=12, float_offset=0, distance=2.6):
    """Setup camera with rotation and float offset"""
    angle = math.radians(rotation_y)
    x = math.sin(angle) * distance
    y = -math.cos(angle) * distance
    z = 0.3 + float_offset * 0.003  # Subtle float in camera
    
    bpy.ops.object.camera_add(location=(x, y, z))
    camera = bpy.context.object
    camera.rotation_euler = (math.radians(90), 0, math.radians(rotation_y))
    
    bpy.context.scene.camera = camera
    return camera

def setup_lighting():
    """Setup professional 3-point lighting"""
    # Key light - main illumination
    bpy.ops.object.light_add(type='AREA', location=(3, -2, 4))
    key = bpy.context.object
    key.data.energy = 700
    key.data.size = 5
    key.rotation_euler = (math.radians(45), 0, math.radians(30))
    
    # Fill light - soften shadows
    bpy.ops.object.light_add(type='AREA', location=(-3, -2, 3))
    fill = bpy.context.object
    fill.data.energy = 250
    fill.data.size = 4
    
    # Rim light - edge definition
    bpy.ops.object.light_add(type='AREA', location=(0, 3, 2))
    rim = bpy.context.object
    rim.data.energy = 350
    rim.data.size = 3

def replace_screen_material(screen_image_path):
    """Replace screen material with custom image"""
    if not os.path.exists(screen_image_path):
        print(f"Screen image not found: {screen_image_path}")
        return
    
    # Find screen material (usually has 'screen' or 'display' in name)
    screen_mat = None
    for mat in bpy.data.materials:
        name_lower = mat.name.lower()
        if 'screen' in name_lower or 'display' in name_lower or 'emissive' in name_lower:
            screen_mat = mat
            break
    
    if not screen_mat:
        # Try to find by emission
        for mat in bpy.data.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'EMISSION' or (hasattr(node, 'inputs') and 'Emission' in str(node.inputs)):
                        screen_mat = mat
                        break
    
    if screen_mat and screen_mat.use_nodes:
        nodes = screen_mat.node_tree.nodes
        links = screen_mat.node_tree.links
        
        # Load image
        img = bpy.data.images.load(screen_image_path)
        
        # Create image texture node
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = img
        
        # Find emission or principled node
        for node in nodes:
            if node.type == 'EMISSION':
                links.new(tex_node.outputs['Color'], node.inputs['Color'])
                node.inputs['Strength'].default_value = 1.0
                break
            elif node.type == 'BSDF_PRINCIPLED':
                links.new(tex_node.outputs['Color'], node.inputs['Emission'])
                node.inputs['Emission Strength'].default_value = 1.0
                break
        
        print(f"Screen material replaced with: {screen_image_path}")
    else:
        print("Could not find screen material")

def setup_render(width=1080, height=1920, samples=24):
    """Configure render settings"""
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    
    # Use Eevee for speed
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    
    # Transparent background for compositing
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

def render_frame(output_path, rotation_y=12, float_offset=0, screen_image=None):
    """Render a single frame of the iPhone"""
    clear_scene()
    
    gltf_path = "/app/backend/iphone_model/source/iphone_simple.gltf"
    
    try:
        bpy.ops.import_scene.gltf(filepath=gltf_path)
        print("GLTF imported")
    except Exception as e:
        print(f"Import failed: {e}")
        return False
    
    # Scale model
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.scale = (0.12, 0.12, 0.12)
            # Apply float offset to model position
            obj.location.z += float_offset * 0.002
    
    # Replace screen if image provided
    if screen_image:
        replace_screen_material(screen_image)
    
    setup_lighting()
    setup_camera(rotation_y, float_offset)
    setup_render()
    
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")
    return True

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    output = argv[0] if len(argv) > 0 else "/tmp/iphone_render.png"
    rotation = float(argv[1]) if len(argv) > 1 else 12
    float_off = float(argv[2]) if len(argv) > 2 else 0
    screen_img = argv[3] if len(argv) > 3 else None
    
    render_frame(output, rotation, float_off, screen_img)
