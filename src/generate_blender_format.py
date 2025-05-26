import bpy
import json
import os
import mathutils

# --- CONFIGURATION ---
# Determine the project root dynamically.
# This script is located at: PROJECT_ROOT/src/generate_blender_format.py
# So, we go up two levels from the script's own directory.
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(script_dir) # Go up from 'src' to project root

print(f"Detected PROJECT_ROOT: {PROJECT_ROOT}")

# Input data directory within the project
INPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "testing-input-output")

# Output directory for the .blend file (will be created if it doesn't exist)
OUTPUT_DIR = os.path.join(INPUT_DATA_DIR, "output")

INPUT_MESH_JSON_FILENAME = "fluid_mesh_data.json"
INPUT_VOLUME_JSON_FILENAME = "fluid_volume_data.json"
OUTPUT_BLEND_FILE_FILENAME = "final_animation_scene.blend"

INPUT_MESH_JSON_PATH = os.path.join(INPUT_DATA_DIR, INPUT_MESH_JSON_FILENAME)
INPUT_VOLUME_JSON_PATH = os.path.join(INPUT_DATA_DIR, INPUT_VOLUME_JSON_FILENAME)
OUTPUT_BLEND_FILE_PATH = os.path.join(OUTPUT_DIR, OUTPUT_BLEND_FILE_FILENAME)

# --- UTILITY FUNCTIONS ---

def clear_scene():
    """Deletes all objects, meshes, and collections in the current scene."""
    # Delete all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clean up orphaned data (meshes, materials, etc.)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.volumes:
        if block.users == 0:
            bpy.data.volumes.remove(block)
    for block in bpy.data.collections:
        if block.users == 0:
            bpy.data.collections.remove(block)

    print("Scene cleared.")

def load_json_data(filepath):
    """Loads JSON data from a given filepath."""
    if not os.path.exists(filepath):
        print(f"Error: JSON file not found at {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded {filepath}")
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading {filepath}: {e}")
        return None

def create_mesh_object(name, vertices, faces):
    """Creates a new Blender mesh object."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces) # No edges needed for faces
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Optional: Assign a simple material for visibility
    if not "MeshMaterial" in bpy.data.materials:
        mat = bpy.data.materials.new(name="MeshMaterial")
        mat.diffuse_color = (0.1, 0.5, 0.8, 1.0) # Blue color
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.1, 0.5, 0.8, 1.0)
    else:
        mat = bpy.data.materials["MeshMaterial"]

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj

def create_volume_object(name):
    """Creates a new Blender volume object."""
    volume = bpy.data.volumes.new(name)
    obj = bpy.data.objects.new(name, volume)
    bpy.context.collection.objects.link(obj)

    # Optional: Assign a simple material for visibility
    if not "VolumeMaterial" in bpy.data.materials:
        mat = bpy.data.materials.new(name="VolumeMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear existing nodes
        for node in nodes:
            nodes.remove(node)

        # Add Volume Principled BSDF and Output
        principled_volume = nodes.new(type='ShaderNodeVolumePrincipled')
        principled_volume.location = (0, 0)
        principled_volume.inputs['Density'].default_value = 10.0 # Default density

        material_output = nodes.new(type='ShaderNodeOutputMaterial')
        material_output.location = (300, 0)

        # Link
        links.new(principled_volume.outputs['Volume'], material_output.inputs['Volume'])
    else:
        mat = bpy.data.materials["VolumeMaterial"]

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj

# --- MAIN SCRIPT EXECUTION ---
if __name__ == "__main__":
    clear_scene()

    print("\n--- Starting Blender Scene Assembly ---")

    # Load all simulation data
    mesh_data_all_frames = load_json_data(INPUT_MESH_JSON_PATH)
    volume_data_all_frames = load_json_data(INPUT_VOLUME_JSON_PATH)

    if not mesh_data_all_frames and not volume_data_all_frames:
        print("No valid mesh or volume data loaded. Exiting.")
        exit()

    # Determine the full frame range
    all_frames = set()
    if mesh_data_all_frames:
        all_frames.update(int(f) for f in mesh_data_all_frames.keys())
    if volume_data_all_frames:
        all_frames.update(int(f) for f in volume_data_all_frames.keys())

    if not all_frames:
        print("No animation frames found in JSON data. Exiting.")
        exit()

    start_frame = min(all_frames)
    end_frame = max(all_frames)

    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    print(f"Setting scene frame range: {start_frame} to {end_frame}")

    mesh_obj = None
    volume_obj = None

    # Iterate through each frame to create and keyframe objects
    for frame_num in range(start_frame, end_frame + 1):
        print(f"Processing Frame: {frame_num}")
        bpy.context.scene.frame_set(frame_num) # Move to the current frame

        # --- Process Mesh Data ---
        frame_mesh_data = mesh_data_all_frames.get(str(frame_num))
        if frame_mesh_data:
            vertices = [tuple(v) for v in frame_mesh_data['vertices']] # Ensure tuples for from_pydata
            faces = [tuple(f) for f in frame_mesh_data['faces']]

            if not mesh_obj:
                # First frame: create the mesh object
                mesh_obj = create_mesh_object("FluidMesh", vertices, faces)
            
            if mesh_obj: # Ensure mesh_obj was created
                current_mesh_data = mesh_obj.data
                current_mesh_data.clear_geometry() # Clear existing verts/edges/faces
                current_mesh_data.from_pydata(vertices, [], faces)
                current_mesh_data.update()

        # --- Process Volume Data ---
        frame_volume_data = volume_data_all_frames.get(str(frame_num))
        if frame_volume_data:
            if not volume_obj:
                volume_obj = create_volume_object("FluidVolume")

            blender_volume_data = volume_obj.data

            for grid_name, grid_info in frame_volume_data.items():
                dimensions = grid_info['dimensions']
                origin = grid_info['origin']
                spacing = grid_info['spacing']
                grid_data = grid_info['data']

                # Ensure grid exists or create it
                if grid_name not in blender_volume_data.grids:
                    grid = blender_volume_data.grids.new(grid_name, type='FLOAT')
                else:
                    grid = blender_volume_data.grids[grid_name]

                # Update grid properties
                grid.dimensions = dimensions
                grid.origin = origin
                grid.spacing = spacing

                # Populate grid data using foreach_set (very efficient!)
                grid.points.foreach_set(grid_data)

                # Keyframe the grid data
                grid.keyframe_insert(data_path='points', frame=frame_num)
                print(f"  - Keyframed volume grid '{grid_name}' for frame {frame_num}")

    # --- Final Steps ---
    print("\n--- Scene Assembly Complete ---")

    # Set active object for easier viewing after script runs
    if mesh_obj:
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
    elif volume_obj:
        bpy.context.view_layer.objects.active = volume_obj
        volume_obj.select_set(True)

    # Ensure the output directory exists before saving
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured output directory exists: {OUTPUT_DIR}")

    # Save the final .blend file
    try:
        bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND_FILE_PATH, compress=True)
        print(f"Blender file saved successfully to: {OUTPUT_BLEND_FILE_PATH}")
    except Exception as e:
        print(f"Error saving Blender file: {e}")

    print("--- Script Finished ---")
