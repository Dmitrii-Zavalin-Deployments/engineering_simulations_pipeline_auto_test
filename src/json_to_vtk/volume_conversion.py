# src/json_to_vtk/volume_conversion.py

from pathlib import Path
import json
import numpy as np
import pyvista as pv


def convert_volume_series(json_path: Path, output_dir: Path) -> None:
    """
    Converts a JSON file with volumetric fluid data into a series of .vti files (one per timestep).

    Parameters:
        json_path (Path): Path to the fluid_volume_data.json input file.
        output_dir (Path): Directory where the .vti files will be saved.
    """
    with open(json_path, "r") as f:
        volume_data = json.load(f)

    grid_info = volume_data["grid_info"]
    dimensions = tuple(reversed(grid_info["dimensions"]))  # Convert from [Z, Y, X] to (X, Y, Z)
    spacing = tuple(grid_info["voxel_size"])
    origin = tuple(grid_info["origin"])

    base_grid = pv.UniformGrid()
    base_grid.dimensions = dimensions
    base_grid.spacing = spacing
    base_grid.origin = origin

    for i, timestep in enumerate(volume_data["time_steps"]):
        grid = base_grid.copy()

        # Convert scalar fields
        for field in ("density_data", "temperature_data"):
            raw = timestep[field]
            array = np.array(raw, dtype=float)
            reshaped = array.reshape(dimensions[::-1])  # back to [Z, Y, X]
            grid.point_data[field.replace("_data", "")] = reshaped.flatten(order="C")

        # Convert velocity vectors
        velocity_raw = np.array(timestep["velocity_data"], dtype=float)
        velocity = velocity_raw.reshape((-1, 3))  # already 3D vectors
        grid.point_data["velocity"] = velocity

        # Export file
        frame_str = f"{i:04d}"
        output_file = output_dir / f"fluid_data_t{frame_str}.vti"
        grid.save(output_file)



