# tests/test_physics_validity.py

import pytest
import sys
from pathlib import Path

# Add src/ to sys.path to support future imports from json_to_vtk
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_positive_density_temperature(sample_volume_data):
    """Ensure scalar fields like density and temperature are non-negative and valid floats/ints."""
    for step in sample_volume_data["time_steps"]:
        density = step["density_data"]
        temperature = step["temperature_data"]

        assert all(isinstance(d, (int, float)) and d >= 0 for d in density), "Negative or invalid value in density_data"
        assert all(isinstance(t, (int, float)) and t >= 0 for t in temperature), "Negative or invalid value in temperature_data"


def test_voxel_consistency(sample_volume_data):
    """Ensure that voxel volume and grid dimensions define a finite, nonzero fluid domain."""
    grid = sample_volume_data["grid_info"]

    dimensions = grid["dimensions"]  # [Z, Y, X]
    voxel_size = grid["voxel_size"]  # [dz, dy, dx]

    assert len(dimensions) == 3 and len(voxel_size) == 3, "Grid and voxel_size must have 3 components"

    num_voxels = dimensions[0] * dimensions[1] * dimensions[2]
    voxel_volume = voxel_size[0] * voxel_size[1] * voxel_size[2]

    total_volume = num_voxels * voxel_volume
    assert total_volume > 0, "Computed fluid domain volume must be positive"


def test_plausible_velocity_range(sample_volume_data):
    """Ensure that velocity vectors fall within a physically reasonable magnitude threshold."""
    max_reasonable_velocity = 100.0  # meters/second

    for step in sample_volume_data["time_steps"]:
        for vector in step["velocity_data"]:
            assert len(vector) == 3, f"Malformed velocity vector: {vector}"
            magnitude_squared = sum(comp ** 2 for comp in vector)
            assert magnitude_squared < max_reasonable_velocity ** 2, f"Unrealistic velocity: {vector}"


def test_stationary_geometry(sample_mesh_data):
    """Verify that the mesh geometry does not change between time steps (static structure)."""
    time_steps = sample_mesh_data.get("time_steps", [])
    assert len(time_steps) > 1, "Multiple time steps are required to test geometry stability"

    reference = time_steps[0]["vertices"]
    for step in time_steps[1:]:
        assert step["vertices"] == reference, "Geometry changed across time steps"



