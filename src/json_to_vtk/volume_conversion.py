# src/json_to_vtk/volume_conversion.py

from pathlib import Path
import json
import numpy as np
import pyvista as pv
import vtk


def convert_volume_series(json_path: Path, output_dir: Path) -> None:
    """
    Converts a volumetric fluid JSON file to a series of .vti files (one per timestep)
    without using pyvista.UniformGrid.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        volume_data = json.load(f)

    grid_info = volume_data["grid_info"]
    z, y, x = grid_info["dimensions"]
    dx, dy, dz = grid_info["voxel_size"]
    ox, oy, oz = grid_info["origin"]

    dimensions = (x, y, z)
    spacing = (dx, dy, dz)
    origin = (ox, oy, oz)

    n_points = x * y * z

    for i, timestep in enumerate(volume_data["time_steps"]):
        # Create vtkImageData directly
        image = vtk.vtkImageData()
        image.SetDimensions(x, y, z)
        image.SetSpacing(spacing)
        image.SetOrigin(origin)

        grid = pv.wrap(image)

        # Attach scalar fields
        for field in ("density_data", "temperature_data"):
            raw = timestep[field]
            scalar = np.array(raw, dtype=np.float32).reshape((z, y, x))
            grid.point_data[field.replace("_data", "")] = scalar.ravel(order="C")

        # Attach velocity vector field
        velocity_raw = np.array(timestep["velocity_data"], dtype=np.float32)
        if velocity_raw.shape != (n_points, 3):
            raise ValueError(f"Velocity data shape mismatch: expected ({n_points}, 3), got {velocity_raw.shape}")
        grid.point_data["velocity"] = velocity_raw

        output_file = output_dir / f"fluid_data_t{i:04d}.vti"
        grid.save(str(output_file))



