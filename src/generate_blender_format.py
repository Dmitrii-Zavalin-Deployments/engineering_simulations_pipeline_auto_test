import json

def load_fluid_data(file_path):
    """Load processed fluid dynamics data from JSON."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None

def convert_to_blender_format(fluid_data):
    """Convert fluid parameters to Blender-compatible format."""
    blender_data = {
        "fluid_simulation": {
            "velocity": {
                "x": fluid_data.get("adjusted_velocity_x", 0.0),
                "y": fluid_data.get("adjusted_velocity_y", 0.0),
                "z": fluid_data.get("adjusted_velocity_z", 0.0)
            },
            "resolution": 128,  # Example simulation resolution
            "time_step": 0.05  # Example time step for animation
        }
    }
    return blender_data

def save_output(file_path, output_data):
    """Save Blender-compatible fluid parameters to JSON."""
    try:
        with open(file_path, 'w') as file:
            json.dump(output_data, file, indent=4)
        print(f"Blender-compatible output saved to {file_path}")
    except Exception as e:
        print(f"Error saving output: {e}")

if __name__ == "__main__":
    input_path = "testing-input-output/fluid_flow_parameters.json"
    output_path = "testing-input-output/blender_fluid_parameters.json"

    fluid_data = load_fluid_data(input_path)
    if fluid_data:
        blender_data = convert_to_blender_format(fluid_data)
        save_output(output_path, blender_data)
    else:
        print("Failed to generate Blender-compatible data due to missing or invalid input.")


