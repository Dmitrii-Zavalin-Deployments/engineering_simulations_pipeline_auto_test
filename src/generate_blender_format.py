import bpy
import json
import os
import numpy as np # For numerical operations, especially with volume data
from mathutils import Vector, Quaternion # For camera orientation helper

# --- CONFIGURATION ---
# Determine the project root dynamically.
# This script is located at: PROJECT_ROOT/src/generate_blender_format.py
# So, we go up one level from the script's own directory to reach the project root.
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(script_dir) # Go up from 'src' to project root

print(f"Detected PROJECT_ROOT: {PROJECT_ROOT}")

# Input data directory within the project
INPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "testing-input-output")

# Output directory for the .blend file (will be created if it doesn't exist)
# Keeping output in 'data/testing-input-output/output/'
OUTPUT_DIR = os.path.join(INPUT_DATA_DIR, "output")

INPUT_MESH_JSON_FILENAME = "fluid_mesh_data.json"
INPUT_VOLUME_JSON_FILENAME = "fluid_volume_data.json"
OUTPUT_BLEND_FILE_FILENAME = "final_animation_scene.blend"

INPUT_MESH_JSON_PATH = os.path.join(INPUT_DATA_DIR, INPUT_MESH_JSON_FILENAME)
INPUT_VOLUME_JSON_PATH = os.path.join(INPUT_DATA_DIR, INPUT_VOLUME_JSON_FILENAME)
OUTPUT_BLEND_FILE_PATH = os.path.join(OUTPUT_DIR, OUTPUT_BLEND_FILE_FILENAME)

# --- UTILITY FUNCTIONS ---

def load_json_data(filepath):
    """Loads JSON data from a given filepath."""
    if not os.path.exists(filepath):
        print(f"Blender Error: JSON file not found at {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Blender: Successfully loaded {filepath}")
        return data
    except json.JSONDecodeError as e:
        print(f"Blender Error: Could not decode JSON from {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Blender Error: An unexpected error occurred loading {filepath}: {e}")
        return None

def direction_to_rotation_quat(direction_vector):
    """Calculates a quaternion rotation to point an object (like a camera)
    along a given direction vector, with Z-axis generally 'up'.
    """
    if not isinstance(direction_vector, Vector):
        direction_vector = Vector(direction_vector)
    
    loc_z = direction_vector.normalized()
    
    # Try to make Y axis point upwards (or as close as possible)
    # Using Z-axis as reference for cross product
    up_ref = Vector((0.0, 0.0, 1.0))
    if loc_z.dot(up_ref) > 0.999: # Almost pointing straight up
        up_ref = Vector((0.0, 1.0, 0.0)) # Use Y-axis as reference
    elif loc_z.dot(up_ref) < -0.999: # Almost pointing straight down
        up_ref = Vector((0.0, 1.0, 0.0)) # Use Y-axis as reference

    loc_y = up_ref.cross(loc_z).normalized()
    if loc_y.length == 0: # Happens if loc_z was parallel to up_ref, try another axis
        loc_y = Vector((0.0, 1.0, 0.0)).cross(loc_z).normalized()
        if loc_y.length == 0: # Still parallel, use default Y
             loc_y = Vector((0.0, 1.0, 0.0))

    loc_x = loc_y.cross(loc_z).normalized()

    # Create a 3x3 rotation matrix from the orthonormal basis vectors
    mat = (
        Vector(loc_x),
        Vector(loc_y),
        Vector(loc_z)
    ).to_matrix().transposed() # Transpose to get correct column vectors for rotation matrix

    return mat.to_quaternion()


# --- MAIN SCENE ASSEMBLY FUNCTION ---
def assemble_fluid_scene(fluid_mesh_data_path, fluid_volume_data_path, output_blend_file_path):
    """
    Assembles a Blender scene from fluid mesh and volumetric data JSON files.
    Creates animated mesh and volume objects with keyframed data.
    """
    print(f"\n--- Blender: Starting scene assembly ---")
    print(f"Blender: Mesh data: {fluid_mesh_data_path}")
    print(f"Blender: Volume data: {fluid_volume_data_path}")
    print(f"Blender: Output .blend: {output_blend_file_path}")

    # --- 1. Clean up existing scene ---
    # Start with a clean slate: deletes all objects, collections, and reverts settings
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("Blender: Scene cleared to factory defaults.")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_blend_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Blender: Created output directory: {output_dir}")

    # --- 2. Load Input JSON Data ---
    mesh_data = load_json_data(fluid_mesh_data_path)
    volume_data = load_json_data(fluid_volume_data_path)

    if not mesh_data and not volume_data:
        print("Blender Error: No valid mesh or volume data loaded. Aborting scene assembly.")
        return

    # --- 3. Scene Animation Settings ---
    # Assuming 'time_points' is present and consistent in both JSONs, or derive from frames.
    # For simplicity, we'll derive max frames from whatever data is available.
    max_frames = 0
    if mesh_data and 'time_steps' in mesh_data:
        max_frames = max(max_frames, len(mesh_data['time_steps']))
    if volume_data and 'time_steps' in volume_data:
        max_frames = max(max_frames, len(volume_data['time_steps']))

    start_frame = 0
    end_frame = max_frames - 1

    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    
    # Estimate FPS if time_points are available, otherwise default to 24
    if mesh_data and 'time_points' in mesh_data and len(mesh_data['time_points']) > 1:
        fps_estimate = 1 / (mesh_data['time_points'][1] - mesh_data['time_points'][0])
        bpy.context.scene.render.fps = max(1, int(fps_estimate)) # Ensure at least 1 FPS
    else:
        bpy.context.scene.render.fps = 24 # Default

    print(f"Blender: Set animation frames from {start_frame} to {end_frame} at approx {bpy.context.scene.render.fps} FPS.")

    mesh_obj = None
    volume_obj = None

    # --- 4. Process Fluid Mesh Data ---
    print("Blender: Processing fluid mesh data...")
    if mesh_data and 'time_steps' in mesh_data and mesh_data['time_steps']:
        mesh_name = mesh_data.get('mesh_name', "FluidMesh")
        
        # Create initial mesh object using the first frame's data
        first_frame_mesh = mesh_data['time_steps'][0]
        vertices = np.array(first_frame_mesh['vertices'])
        faces = np.array(first_frame_mesh['faces'])
        
        mesh_blender = bpy.data.meshes.new(mesh_name)
        mesh_blender.from_pydata(vertices.tolist(), [], faces.tolist())
        mesh_blender.update()
        mesh_obj = bpy.data.objects.new(mesh_name, mesh_blender)
        bpy.context.collection.objects.link(mesh_obj)
        
        # Assign a simple material for visibility
        if not "MeshMaterial" in bpy.data.materials:
            mat = bpy.data.materials.new(name="MeshMaterial")
            mat.diffuse_color = (0.1, 0.5, 0.8, 1.0) # Blue color
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf:
                bsdf.inputs['Base Color'].default_value = (0.1, 0.5, 0.8, 1.0)
        else:
            mat = bpy.data.materials["MeshMaterial"]

        if mesh_obj.data.materials:
            mesh_obj.data.materials[0] = mat
        else:
            mesh_obj.data.materials.append(mat)
            
        print(f"Blender: Created initial mesh object: {mesh_obj.name}")

        # Animate mesh by updating geometry per frame
        # IMPORTANT: This method (clear_geometry + from_pydata) is suitable if mesh topology
        # *changes* per frame, or for simple meshes where performance isn't a major concern.
        # For meshes with *static topology* but changing vertex positions,
        # using Blender's **Shape Keys** is the canonical and more efficient way to animate.
        # Implementing shape keys is more complex and depends on vertex order consistency.
        # This current approach rebuilds the mesh data block on each frame.
        for frame_idx, frame_data in enumerate(mesh_data['time_steps']):
            if frame_idx > end_frame: # Prevent out of bounds if mesh_data has more frames than volume_data or vice versa
                break
            bpy.context.scene.frame_set(frame_idx)
            current_vertices = np.array(frame_data['vertices'])
            current_faces = np.array(frame_data['faces']) # Re-read faces in case topology changes

            # Update geometry
            mesh_blender.clear_geometry()
            mesh_blender.from_pydata(current_vertices.tolist(), [], current_faces.tolist())
            mesh_blender.update()
            
            # Note: Directly keyframing mesh data blocks is not common.
            # The animation is achieved by changing the geometry at each frame and saving the .blend.
            # For a playable animation *within* Blender, shape keys or Alembic export/import is ideal.
            # This script focuses on creating the correct static state per frame in the final .blend.
            print(f"Blender: Mesh updated for frame {frame_idx}")
    else:
        print("Blender: No mesh data found or 'time_steps' is empty.")


    # --- 5. Process Fluid Volume Data ---
    print("Blender: Processing fluid volume data...")
    if volume_data and 'time_steps' in volume_data and volume_data['time_steps']:
        volume_name = volume_data.get('volume_name', "FluidVolume")
        grid_info = volume_data['grid_info']
        num_x, num_y, num_z = grid_info['dimensions']
        dx, dy, dz = grid_info['voxel_size']
        origin_x, origin_y, origin_z = grid_info['origin']

        # Create a single Volume object
        volume_blender = bpy.data.volumes.new(volume_name)
        volume_obj = bpy.data.objects.new(volume_name, volume_blender)
        bpy.context.collection.objects.link(volume_obj)
        print(f"Blender: Created initial volume object: {volume_obj.name}")

        # Assign a simple material for visibility
        if not "VolumeMaterial" in bpy.data.materials:
            mat = bpy.data.materials.new(name="VolumeMaterial")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            # Clear existing nodes
            for node in nodes:
                nodes.remove(node)
            principled_volume = nodes.new(type='ShaderNodeVolumePrincipled')
            principled_volume.location = (0, 0)
            principled_volume.inputs['Density'].default_value = 10.0 # Default density
            material_output = nodes.new(type='ShaderNodeOutputMaterial')
            material_output.location = (300, 0)
            links.new(principled_volume.outputs['Volume'], material_output.inputs['Volume'])
        else:
            mat = bpy.data.materials["VolumeMaterial"]

        if volume_obj.data.materials:
            volume_obj.data.materials[0] = mat
        else:
            volume_obj.data.materials.append(mat)
            
        # Set volume object scale and location based on grid info
        # Blender's volume object has its origin at its center.
        # So, location should be grid_origin + 0.5 * grid_size
        volume_obj.location = (origin_x + dx * num_x / 2,
                               origin_y + dy * num_y / 2,
                               origin_z + dz * num_z / 2)
        volume_obj.scale = (dx * num_x, dy * num_y, dz * num_z) # Scale object to match grid size


        # Animate volume data per frame
        for frame_idx, frame_data in enumerate(volume_data['time_steps']):
            if frame_idx > end_frame: # Prevent out of bounds
                break
            bpy.context.scene.frame_set(frame_idx)

            # --- Process Density Grid ---
            density_grid_name = "density"
            if 'density_data' in frame_data:
                if density_grid_name not in volume_blender.grids:
                    density_grid = volume_blender.grids.new(density_grid_name, type='FLOAT')
                else:
                    density_grid = volume_blender.grids[density_grid_name]

                density_grid.dimensions = (num_x, num_y, num_z)
                density_grid.origin = (origin_x, origin_y, origin_z) # Grid-level origin (though object location is set)
                density_grid.spacing = (dx, dy, dz) # Grid-level voxel spacing

                density_data = np.array(frame_data['density_data'], dtype=np.float32)
                if len(density_data) != num_x * num_y * num_z:
                    print(f"Blender Warning: Density data size mismatch for frame {frame_idx}. Expected {num_x*num_y*num_z}, Got {len(density_data)}")
                else:
                    # Reshape from flat (X-Y-Z order assumed from simulation) to (Z, Y, X), then transpose to Blender's internal (X,Y,Z) and flatten.
                    # This ensures correct mapping for foreach_set which expects Z-Y-X fastest to slowest index
                    density_data_reshaped_blender_order = density_data.reshape(num_x, num_y, num_z).transpose(2,1,0).flatten()
                    density_grid.points.foreach_set('value', density_data_reshaped_blender_order)
                    density_grid.keyframe_insert(data_path='points', frame=frame_idx)
                    print(f"  - Keyframed density grid for frame {frame_idx}")
            else:
                print(f"Blender Warning: No 'density_data' for frame {frame_idx}.")

            # --- Process Velocity Grids (X, Y, Z components) ---
            if 'velocity_data' in frame_data:
                velocity_data = np.array(frame_data['velocity_data'], dtype=np.float32) # Assumed (N, 3) for N voxels
                if len(velocity_data.flatten()) != num_x * num_y * num_z * 3:
                    print(f"Blender Warning: Velocity data size mismatch for frame {frame_idx}. Expected {num_x*num_y*num_z*3}, Got {len(velocity_data.flatten())}")
                else:
                    # Reshape velocity data from (num_voxels, 3) to (Nx, Ny, Nz, 3)
                    velocity_data_grid = velocity_data.reshape(num_x, num_y, num_z, 3)

                    # Extract components and transpose to Blender's order
                    vx_data_blender_order = velocity_data_grid[:,:,:,0].transpose(2,1,0).flatten()
                    vy_data_blender_order = velocity_data_grid[:,:,:,1].transpose(2,1,0).flatten()
                    vz_data_blender_order = velocity_data_grid[:,:,:,2].transpose(2,1,0).flatten()

                    for i, (comp_name, comp_data) in enumerate(zip(['velocity_X', 'velocity_Y', 'velocity_Z'], 
                                                                    [vx_data_blender_order, vy_data_blender_order, vz_data_blender_order])):
                        if comp_name not in volume_blender.grids:
                            comp_grid = volume_blender.grids.new(comp_name, type='FLOAT')
                        else:
                            comp_grid = volume_blender.grids[comp_name]
                        
                        comp_grid.dimensions = (num_x, num_y, num_z)
                        comp_grid.origin = (origin_x, origin_y, origin_z)
                        comp_grid.spacing = (dx, dy, dz)
                        comp_grid.points.foreach_set('value', comp_data)
                        comp_grid.keyframe_insert(data_path='points', frame=frame_idx)
                        print(f"  - Keyframed {comp_name} grid for frame {frame_idx}")
            else:
                print(f"Blender Warning: No 'velocity_data' for frame {frame_idx}.")

            # --- Process Temperature Grid ---
            temp_grid_name = "temperature"
            if 'temperature_data' in frame_data:
                if temp_grid_name not in volume_blender.grids:
                    temp_grid = volume_blender.grids.new(temp_grid_name, type='FLOAT')
                else:
                    temp_grid = volume_blender.grids[temp_grid_name]
                
                temp_grid.dimensions = (num_x, num_y, num_z)
                temp_grid.origin = (origin_x, origin_y, origin_z)
                temp_grid.spacing = (dx, dy, dz)
                
                temperature_data = np.array(frame_data['temperature_data'], dtype=np.float32)
                if len(temperature_data) != num_x * num_y * num_z:
                    print(f"Blender Warning: Temperature data size mismatch for frame {frame_idx}. Expected {num_x*num_y*num_z}, Got {len(temperature_data)}")
                else:
                    temperature_data_reshaped_blender_order = temperature_data.reshape(num_x, num_y, num_z).transpose(2,1,0).flatten()
                    temp_grid.points.foreach_set('value', temperature_data_reshaped_blender_order)
                    temp_grid.keyframe_insert(data_path='points', frame=frame_idx)
                    print(f"  - Keyframed {temp_grid_name} grid for frame {frame_idx}")
            else:
                print(f"Blender Warning: No 'temperature_data' for frame {frame_idx}.")

    else:
        print("Blender: No volume data found or 'time_steps' is empty.")


    # --- 6. (Optional) Setup Camera and Lighting ---
    print("Blender: Setting up camera and lighting...")
    
    # Delete default cube (if still exists after factory settings, though use_empty=True typically removes it)
    if "Cube" in bpy.data.objects:
        bpy.data.objects["Cube"].select_set(True)
        bpy.ops.object.delete()

    # Calculate approximate center of the simulation grid for camera/light placement
    center_x, center_y, center_z = 0, 0, 0
    if volume_data and 'grid_info' in volume_data:
        grid_info = volume_data['grid_info']
        num_x, num_y, num_z = grid_info['dimensions']
        dx, dy, dz = grid_info['voxel_size']
        origin_x, origin_y, origin_z = grid_info['origin']
        center_x = origin_x + dx * num_x / 2
        center_y = origin_y + dy * num_y / 2
        center_z = origin_z + dz * num_z / 2
    elif mesh_obj and mesh_obj.data.vertices: # Fallback to mesh centroid if no volume
        mesh_verts = np.array([v.co for v in mesh_obj.data.vertices])
        if mesh_verts.size > 0:
            center_x, center_y, center_z = np.mean(mesh_verts, axis=0)

    # Simple camera setup
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
        
    # Position camera to view the scene (adjust as needed based on your simulation bounds)
    # This is a basic position, you'll want to fine-tune this.
    view_distance = max(grid_info['dimensions']) * max(grid_info['voxel_size']) * 1.5 if volume_data and 'grid_info' in volume_data else 10.0 # Adjust as needed
    cam_obj.location = (center_x + view_distance * 0.8,
                        center_y - view_distance * 1.2, # Pull back on Y (Blender's default front view)
                        center_z + view_distance * 0.75)
        
    # Point camera towards the center of the grid
    look_at_vec = Vector((center_x, center_y, center_z))
    cam_location_vec = Vector(cam_obj.location)
    direction_to_center = look_at_vec - cam_location_vec
    
    cam_obj.rotation_mode = 'QUATERNION'
    cam_obj.rotation_quaternion = direction_to_rotation_quat(direction_to_center)
    
    # Simple light setup (Sun lamp)
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    light_obj.location = (center_x + 5, center_y + 5, center_z + 10)
    light_obj.rotation_euler = (0.7, -0.5, 0.3) # Adjust light direction
    light_data.energy = 5
    print("Blender: Camera and lighting set up.")

    # --- 7. Save the final .blend file ---
    try:
        bpy.ops.wm.save_as_mainfile(filepath=output_blend_file_path, compress=True)
        print(f"Blender: Scene saved successfully to: {output_blend_file_path}")
    except Exception as e:
        print(f"Blender Error: Could not save Blender file: {e}")

    print("--- Blender: Scene assembly complete! ---")

# --- Main execution block when run with Blender's Python ---
if __name__ == "__main__":
    assemble_fluid_scene(INPUT_MESH_JSON_PATH, INPUT_VOLUME_JSON_PATH, OUTPUT_BLEND_FILE_PATH)
