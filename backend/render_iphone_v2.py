import bpy
import sys
import math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def setup_camera(rotation_y=12, distance=2.8):
    angle = math.radians(rotation_y)
    x = math.sin(angle) * distance
    y = -math.cos(angle) * distance
    z = 0.3
    
    bpy.ops.object.camera_add(location=(x, y, z))
    camera = bpy.context.object
    camera.rotation_euler = (math.radians(90), 0, math.radians(rotation_y))
    
    bpy.context.scene.camera = camera
    return camera

def setup_lighting():
    # Key light
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

def setup_render(width=1080, height=1920, samples=32):
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

def render_frame(output_path, rotation_y=12):
    clear_scene()
    
    gltf_path = "/app/backend/iphone_model/source/iphone_simple.gltf"
    
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
