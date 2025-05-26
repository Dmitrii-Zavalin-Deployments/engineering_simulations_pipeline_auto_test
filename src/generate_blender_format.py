import bpy
import json
import os
import numpy as np # For numerical operations, especially with volume data
from mathutils import Vector, Quaternion # For Blender's math types

# --- CONFIGURATION ---
# Determine the project root dynamically.
# This script is expected to be located at: PROJECT_ROOT/src/generate_blender_format.py
# So, we go up one level from the script's own directory to reach the project root.
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
    # Determine the total number of frames from the loaded data
    max_frames = 0
    if mesh_data and 'time_steps' in mesh_data:
        max_frames = max(max_frames, len(mesh_data['time_steps']))
    if volume_data and 'time_steps' in volume_data:
        max_frames = max(max_frames, len(volume_data['time_steps']))

    start_frame = 0
    end_frame = max_frames - 1
    if end_frame < 0: # Handle case with no data
        end_frame = 0

    bpy.context.scene.frame_start = start_frame
    bpy.context.scene.frame_end = end_frame
    
    # Estimate FPS if time_points are available, otherwise default to 24
    if mesh_data and 'time_points' in mesh_data and len(mesh_data['time_points']) > 1:
        # Calculate approximate FPS based on the first two time points
        # Assuming uniform time steps
        fps_estimate = 1 / (mesh_data['time_points'][1] - mesh_data['time_points'][0])
        bpy.context.scene.render.fps = max(1, int(fps_estimate)) # Ensure at least 1 FPS
    else:
        bpy.context.scene.render.fps = 24 # Default FPS

    print(f"Blender: Set animation frames from {start_frame} to {end_frame} at approx {bpy.context.scene.render.fps} FPS.")

    mesh_obj = None
    volume_obj = None

    # --- 4. Process Fluid Mesh Data ---
    print("Blender: Processing fluid mesh data...")
    if mesh_data and 'time_steps' in mesh_data and mesh_data['time_steps']:
        mesh_name = mesh_data.get('mesh_name', "FluidMesh")
        
        # Load static faces once from the top level of the JSON
        static_faces = None
        if 'static_faces' in mesh_data:
            static_faces = np.array(mesh_data['static_faces'])
            print(f"Blender: Loaded {len(static_faces)} static faces.")
        else:
            print("Blender Error: 'static_faces' key not found in fluid_mesh_data.json. Cannot create mesh object.")
            # For a mesh, faces are essential, so we'll return if they are missing.
            return 
            
        # Create initial mesh object using the first frame's vertices and static faces
        first_frame_mesh = mesh_data['time_steps'][0]
        
        # Check if 'vertices' key exists in the first frame data
        if 'vertices' not in first_frame_mesh:
            print(f"Blender Error: 'vertices' key not found in the first time step of mesh data. Cannot create mesh object.")
            return

        vertices = np.array(first_frame_mesh['vertices'])
        
        mesh_blender = bpy.data.meshes.new(mesh_name)
        # Use static_faces here for the initial mesh creation
        mesh_blender.from_pydata(vertices.tolist(), [], static_faces.tolist())
        mesh_blender.update()
        mesh_obj = bpy.data.objects.new(mesh_name, mesh_blender)
        bpy.context.collection.objects.link(mesh_obj)
        
        # Assign a simple material for visibility
        if "MeshMaterial" not in bpy.data.materials:
            mat = bpy.data.materials.new(name="MeshMaterial")
            mat.use_nodes = True
            principled_bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if principled_bsdf:
                # Correct Base Color: must be a 4-item (RGBA) tuple
                principled_bsdf.inputs['Base Color'].default_value = (0.1, 0.5, 0.8, 1.0) # Correct RGBA
                principled_bsdf.inputs['Roughness'].default_value = 0.5
                principled_bsdf.inputs['Metallic'].default_value = 0.0
        else:
            mat = bpy.data.materials["MeshMaterial"]

        if mesh_obj.data.materials:
            mesh_obj.data.materials[0] = mat
        else:
            mesh_obj.data.materials.append(mat)
            
        print(f"Blender: Created initial mesh object: {mesh_obj.name}")

        # Animate mesh by updating geometry per frame
        for frame_idx, frame_data in enumerate(mesh_data['time_steps']):
            if frame_idx > end_frame: # Prevent out of bounds
                break
            bpy.context.scene.frame_set(frame_idx)
            
            if 'vertices' not in frame_data:
                print(f"Blender Warning: 'vertices' key not found for mesh data at frame {frame_idx}. Skipping frame update.")
                continue

            current_vertices = np.array(frame_data['vertices'])

            # Update geometry using the per-frame vertices and the STATIC faces
            mesh_blender.clear_geometry()
            mesh_blender.from_pydata(current_vertices.tolist(), [], static_faces.tolist()) # Use static_faces
            mesh_blender.update()
            
            print(f"Blender: Mesh updated for frame {frame_idx}")
    else:
        print("Blender: No mesh data found or 'time_steps' is empty, skipping mesh creation.")


    # --- 5. Process Fluid Volume Data ---
    print("Blender: Processing fluid volume data...")
    if volume_data and 'time_steps' in volume_data and volume_data['time_steps']:
        volume_name = volume_data.get('volume_name', "FluidVolume")
        
        if 'grid_info' not in volume_data:
            print("Blender Error: 'grid_info' missing in volume data. Cannot create volume object.")
            return

        grid_info = volume_data['grid_info']
        
        # Validate required grid_info keys
        required_grid_keys = ['dimensions', 'voxel_size', 'origin']
        if not all(key in grid_info for key in required_grid_keys):
            print(f"Blender Error: Missing required grid_info keys ({required_grid_keys}) in volume data. Cannot create volume object.")
            return

        num_x, num_y, num_z = grid_info['dimensions']
        dx, dy, dz = grid_info['voxel_size']
        origin_x, origin_y, origin_z = grid_info['origin']

        # Create a single Volume object
        volume_blender = bpy.data.volumes.new(volume_name)
        volume_obj = bpy.data.objects.new(volume_name, volume_blender)
        bpy.context.collection.objects.link(volume_obj)
        print(f"Blender: Created initial volume object: {volume_obj.name}")

        # --- FIX: Use .new_grid() for creating volume grids ---
        # Pre-create all expected grids on the volume data block.
        # This ensures the Attribute Nodes in the material can find them by name and type.
        print("Blender: Pre-creating volume grids on data block using new_grid()...")
        volume_blender.grids.new_grid(name="density", type='FLOAT')
        volume_blender.grids.new_grid(name="temperature", type='FLOAT')
        volume_blender.grids.new_grid(name="velocity_X", type='FLOAT')
        volume_blender.grids.new_grid(name="velocity_Y", type='FLOAT')
        volume_blender.grids.new_grid(name="velocity_Z", type='FLOAT')
        print("Blender: Volume grids pre-created.")

        # Assign a principled volume material
        if "VolumeMaterial" not in bpy.data.materials:
            mat = bpy.data.materials.new(name="VolumeMaterial")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            # Clear existing nodes for a clean setup
            for node in nodes:
                nodes.remove(node)
            
            # Add Principled Volume Shader
            principled_volume = nodes.new(type='ShaderNodeVolumePrincipled')
            principled_volume.location = (0, 0)
            
            # Add Attribute nodes for custom grids - names must match pre-created grids
            density_attr = nodes.new(type='ShaderNodeAttribute')
            density_attr.location = (-300, 200)
            density_attr.attribute_name = 'density' 
            
            temp_attr = nodes.new(type='ShaderNodeAttribute')
            temp_attr.location = (-300, -100)
            temp_attr.attribute_name = 'temperature'

            # Add a ColorRamp for temperature (e.g., blue for cold, red for hot)
            color_ramp_map_range = nodes.new(type='ShaderNodeMapRange')
            color_ramp_map_range.location = (0, -200)
            # You might need to adjust 'From Min/Max' based on your actual temperature range
            color_ramp_map_range.inputs['From Min'].default_value = 273.15 # e.g., 0 Celsius
            color_ramp_map_range.inputs['From Max'].default_value = 373.15 # e.g., 100 Celsius
            color_ramp_map_range.inputs['To Min'].default_value = 0.0 # Map to range 0-1
            color_ramp_map_range.inputs['To Max'].default_value = 1.0

            color_ramp_colors = nodes.new(type='ShaderNodeValToRGB')
            color_ramp_colors.location = (150, -200)
            # Add color stops: blue at 0, red at 1
            color_ramp_colors.color_ramp.elements.new(0.0).color = (0.0, 0.0, 1.0, 1.0) # Blue
            color_ramp_colors.color_ramp.elements.new(1.0).color = (1.0, 0.0, 0.0, 1.0) # Red
            color_ramp_colors.color_ramp.elements[0].position = 0.0
            color_ramp_colors.color_ramp.elements[1].position = 1.0


            # Material Output Node
            material_output = nodes.new(type='ShaderNodeOutputMaterial')
            material_output.location = (300, 0)

            # Link nodes:
            links.new(density_attr.outputs['Factor'], principled_volume.inputs['Density'])
            links.new(temp_attr.outputs['Factor'], color_ramp_map_range.inputs['Value'])
            links.new(color_ramp_map_range.outputs['Result'], color_ramp_colors.inputs['Fac'])
            links.new(color_ramp_colors.outputs['Color'], principled_volume.inputs['Color']) # Color for volume
            links.new(principled_volume.outputs['Volume'], material_output.inputs['Volume'])

        else:
            mat = bpy.data.materials["VolumeMaterial"]

        if volume_obj.data.materials:
            volume_obj.data.materials[0] = mat
        else:
            volume_obj.data.materials.append(mat)
            
        # Set volume object scale and location based on grid info
        # Blender's volume object has its origin at its center by default.
        # So, location should be grid_origin + 0.5 * grid_size
        volume_obj.location = (origin_x + dx * num_x / 2,
                               origin_y + dy * num_y / 2,
                               origin_z + dz * num_z / 2)
        # Scale the object to match the total physical dimensions of the grid
        volume_obj.scale = (dx * num_x, dy * num_y, dz * num_z) 
        print(f"Blender: Volume object positioned at {volume_obj.location} and scaled to {volume_obj.scale}")


        # Animate volume data per frame
        for frame_idx, frame_data in enumerate(volume_data['time_steps']):
            if frame_idx > end_frame: # Prevent out of bounds if volume_data has more frames
                break
            bpy.context.scene.frame_set(frame_idx)

            # --- Process Density Grid ---
            density_grid_name = "density" # This name must match the Attribute Node in the material!
            if 'density_data' in frame_data:
                # Get the already-created grid (no need to check for existence or create again)
                density_grid = volume_blender.grids[density_grid_name]

                density_grid.dimensions = (num_x, num_y, num_z)
                density_grid.origin = (origin_x, origin_y, origin_z)
                density_grid.spacing = (dx, dy, dz)

                density_data = np.array(frame_data['density_data'], dtype=np.float32)
                if len(density_data) != num_x * num_y * num_z:
                    print(f"Blender Warning: Density data size mismatch for frame {frame_idx}. Expected {num_x*num_y*num_z}, Got {len(density_data)}")
                else:
                    # Reshape from flat (assuming X-Y-Z fastest to slowest in simulation output) to (X, Y, Z),
                    # then transpose to (Z, Y, X) and flatten for Blender's foreach_set.
                    # Blender's foreach_set for grids expects data in Z-Y-X order.
                    density_data_reshaped_blender_order = density_data.reshape(num_x, num_y, num_z).transpose(2,1,0).flatten()
                    density_grid.points.foreach_set('value', density_data_reshaped_blender_order)
                    density_grid.keyframe_insert(data_path='points', frame=frame_idx)
                    # print(f"  - Keyframed density grid for frame {frame_idx}") # Commented for less verbose output

            # --- Process Velocity Grids (X, Y, Z components) ---
            # These are for vector fields, e.g., for motion blur or visualizers
            if 'velocity_data' in frame_data:
                velocity_data = np.array(frame_data['velocity_data'], dtype=np.float32) # Assumed (N, 3) for N voxels
                
                # Check if velocity data size matches expected volume size
                expected_velocity_elements = num_x * num_y * num_z * 3
                if len(velocity_data.flatten()) != expected_velocity_elements:
                    print(f"Blender Warning: Velocity data size mismatch for frame {frame_idx}. Expected {expected_velocity_elements}, Got {len(velocity_data.flatten())}. Skipping velocity grids.")
                else:
                    # Reshape velocity data from (num_voxels, 3) to (Nx, Ny, Nz, 3)
                    velocity_data_grid = velocity_data.reshape(num_x, num_y, num_z, 3)

                    # Extract components and transpose each to Blender's (Z,Y,X) order
                    vx_data_blender_order = velocity_data_grid[:,:,:,0].transpose(2,1,0).flatten()
                    vy_data_blender_order = velocity_data_grid[:,:,:,1].transpose(2,1,0).flatten()
                    vz_data_blender_order = velocity_data_grid[:,:,:,2].transpose(2,1,0).flatten()

                    for i, (comp_name_suffix, comp_data) in enumerate(zip(['_X', '_Y', '_Z'], 
                                                                           [vx_data_blender_order, vy_data_blender_order, vz_data_blender_order])):
                        grid_name = "velocity" + comp_name_suffix # e.g., "velocity_X"
                        # Get the already-created grid
                        comp_grid = volume_blender.grids[grid_name]
                        
                        comp_grid.dimensions = (num_x, num_y, num_z)
                        comp_grid.origin = (origin_x, origin_y, origin_z)
                        comp_grid.spacing = (dx, dy, dz)
                        comp_grid.points.foreach_set('value', comp_data)
                        comp_grid.keyframe_insert(data_path='points', frame=frame_idx)
                        # print(f"  - Keyframed {grid_name} grid for frame {frame_idx}") # Commented for less verbose output
            
            # --- Process Temperature Grid ---
            temp_grid_name = "temperature" # This name must match the Attribute Node in the material!
            if 'temperature_data' in frame_data:
                # Get the already-created grid
                temp_grid = volume_blender.grids[temp_grid_name]
                
                temp_grid.dimensions = (num_x, num_y, num_z)
                temp_grid.origin = (origin_x, origin_y, origin_z)
                temp_grid.spacing = (dx, dy, dz)
                
                temperature_data = np.array(frame_data['temperature_data'], dtype=np.float32)
                if len(temperature_data) != num_x * num_y * num_z:
                    print(f"Blender Warning: Temperature data size mismatch for frame {frame_idx}. Expected {num_x*num_y*num_z}, Got {len(temperature_data)}. Skipping temperature grid.")
                else:
                    # Reshape and transpose to Blender's Z-Y-X order
                    temperature_data_reshaped_blender_order = temperature_data.reshape(num_x, num_y, num_z).transpose(2,1,0).flatten()
                    temp_grid.points.foreach_set('value', temperature_data_reshaped_blender_order)
                    temp_grid.keyframe_insert(data_path='points', frame=frame_idx)
                    # print(f"  - Keyframed {temp_grid_name} grid for frame {frame_idx}") # Commented for less verbose output

    else:
        print("Blender: No volume data found or 'time_steps' is empty, skipping volume creation.")


    # --- 6. (Optional) Setup Camera and Lighting ---
    print("Blender: Setting up camera and lighting...")
    
    # Delete default objects (like the default Cube often present in factory settings)
    bpy.ops.object.select_all(action='DESELECT')
    if "Cube" in bpy.data.objects:
        obj = bpy.data.objects["Cube"]
        if obj.type == 'MESH':
            obj.select_set(True)
            bpy.ops.object.delete()
            print("Blender: Deleted default Cube.")

    # Calculate approximate center of the simulation grid for camera/light placement
    center_x, center_y, center_z = 0, 0, 0
    grid_size_magnitude = 10.0 # Default fallback if no valid data to derive bounds
    
    if volume_data and 'grid_info' in volume_data:
        grid_info = volume_data['grid_info']
        num_x, num_y, num_z = grid_info['dimensions']
        dx, dy, dz = grid_info['voxel_size']
        origin_x, origin_y, origin_z = grid_info['origin']
        center_x = origin_x + dx * num_x / 2
        center_y = origin_y + dy * num_y / 2
        center_z = origin_z + dz * num_z / 2
        grid_size_magnitude = np.linalg.norm([dx * num_x, dy * num_y, dz * num_z])
    elif mesh_obj and mesh_obj.data.vertices: # Fallback to mesh centroid if no volume
        mesh_verts = np.array([v.co for v in mesh_obj.data.vertices])
        if mesh_verts.size > 0:
            center_x, center_y, center_z = np.mean(mesh_verts, axis=0)
            # Use bounding box diagonal for size estimate
            grid_size_magnitude = np.linalg.norm(np.max(mesh_verts, axis=0) - np.min(mesh_verts, axis=0))
        
    # Simple camera setup
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
        
    # Position camera to view the scene (adjust multipliers for desired zoom/angle)
    view_distance = grid_size_magnitude * 2.0 # Adjust multiplier for desired zoom level
    cam_obj.location = (center_x + view_distance * 0.8, # Move along X
                        center_y - view_distance * 1.2, # Pull back along Y (Blender's default front view)
                        center_z + view_distance * 0.75) # Move up along Z
        
    # Point camera towards the center of the grid
    look_at_vec = Vector((center_x, center_y, center_z))
    cam_location_vec = Vector(cam_obj.location)
    direction_to_center = look_at_vec - cam_location_vec
    
    cam_obj.rotation_mode = 'QUATERNION' # Use quaternion for rotation to avoid gimbal lock
    cam_obj.rotation_quaternion = direction_to_rotation_quat(direction_to_center)
    
    # Simple light setup (Sun lamp for directional lighting)
    light_data = bpy.data.lights.new(name="SunLight", type='SUN')
    light_obj = bpy.data.objects.new(name="SunLight", object_data=light_data)
    bpy.context.collection.objects.link(light_obj)
    # Position light relative to center, slightly above and to the side
    light_obj.location = (center_x + grid_size_magnitude * 0.5, 
                          center_y + grid_size_magnitude * 0.5, 
                          center_z + grid_size_magnitude * 1.0)
    # Adjust light direction (Euler angles in radians, e.g., to cast shadows from top-right front)
    light_obj.rotation_euler = (np.radians(45), np.radians(0), np.radians(135)) 
    light_data.energy = 5 # Adjust brightness (watts for point/spot/area, intensity for sun)
    print("Blender: Camera and lighting set up.")

    # --- 7. Save the final .blend file ---
    try:
        # compress=True makes the .blend file smaller, good for repositories
        bpy.ops.wm.save_as_mainfile(filepath=output_blend_file_path, compress=True)
        print(f"Blender: Scene saved successfully to: {output_blend_file_path}")
    except Exception as e:
        print(f"Blender Error: Could not save Blender file: {e}")
        # Optionally, re-raise the exception or exit to fail the workflow
        # raise # Uncomment to make the step explicitly fail on save error

    print("--- Blender: Scene assembly complete! ---")

# --- Main execution block when run with Blender's Python ---
# This ensures that assemble_fluid_scene is called only when the script is executed directly
# (e.g., by Blender's --python argument), not when imported as a module.
if __name__ == "__main__":
    assemble_fluid_scene(INPUT_MESH_JSON_PATH, INPUT_VOLUME_JSON_PATH, OUTPUT_BLEND_FILE_PATH)
