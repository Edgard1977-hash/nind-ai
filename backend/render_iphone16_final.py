"""
Final ultra-smooth render: 91 angles (step 1°)
"""
import bpy
import os
import math

MODEL_PATH = "/app/backend/iphone_16_model/source/iphone_16_black.glb"
OUTPUT_DIR = "/app/backend/iphone_16_renders_final"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RES_X = 800
RES_Y = 1600
SAMPLES = 12

ANGLES = list(range(-45, 46, 1))  # 91 angles

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

def setup():
    bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        return None
    
    bpy.ops.object.empty_add(location=(0, 0, 0))
    parent = bpy.context.active_object
    for obj in meshes:
        obj.parent = parent
    
    # Center
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for obj in meshes:
        for v in obj.data.vertices:
            w = obj.matrix_world @ v.co
            min_x, max_x = min(min_x, w.x), max(max_x, w.x)
            min_y, max_y = min(min_y, w.y), max(max_y, w.y)
            min_z, max_z = min(min_z, w.z), max(max_z, w.z)
    
    cx, cy, cz = (min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2
    for obj in meshes:
        obj.location.x -= cx
        obj.location.y -= cy
        obj.location.z -= cz
    
    max_dim = max(max_x-min_x, max_y-min_y, max_z-min_z)
    parent.scale = (2.0/max_dim,)*3
    
    # Camera
    bpy.ops.object.camera_add(location=(0, -5.5, 0))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    cam.data.lens = 55
    
    # Lights
    for loc, energy, size in [((4,-4,5), 500, 5), ((-3,-4,3), 200, 4), ((0,4,3), 300, 6)]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        bpy.context.active_object.data.energy = energy
        bpy.context.active_object.data.size = size
    
    # Render
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x = RES_X
    s.render.resolution_y = RES_Y
    s.render.film_transparent = True
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGBA'
    s.eevee.taa_render_samples = SAMPLES
    
    return parent

def main():
    print(f"Rendering {len(ANGLES)} angles")
    clear_scene()
    phone = setup()
    if not phone:
        return
    
    for angle in ANGLES:
        phone.rotation_euler = (0, 0, math.radians(angle))
        sign = '+' if angle >= 0 else ''
        path = os.path.join(OUTPUT_DIR, f"iphone_{sign}{angle:03d}.png")
        bpy.context.scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"{angle}°")
    
    print("Done!")

if __name__ == "__main__":
    main()
