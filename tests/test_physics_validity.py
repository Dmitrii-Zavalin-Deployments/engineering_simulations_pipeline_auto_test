# test_physics_validity.py

import pytest


def test_positive_density_temperature(sample_volume_data):
    """Ensure that scalar fields like density and temperature have physically plausible, non-negative values."""
    for step in sample_volume_data["time_steps"]:
        density = step["density_data"]
        temperature = step["temperature_data"]

        assert all(isinstance(d, (int, float)) and d >= 0 for d in density), "Negative or invalid value in density_data"
        assert all(isinstance(t, (int, float)) and t >= 0 for t in temperature), "Negative or invalid value in temperature_data"


def test_voxel_consistency(sample_volume_data):
    """Ensure voxel and grid size together define a plausible volume."""
    grid = sample_volume_data["grid_info"]

    dimensions = grid["dimensions"]  # [Z, Y, X]
    voxel_size = grid["voxel_size"]  # [dz, dy, dx]

    assert len(dimensions) == 3 and len(voxel_size) == 3, "Grid and voxel_size must have 3 components"

    num_voxels = dimensions[0] * dimensions[1] * dimensions[2]
    total_volume = voxel_size[0] * voxel_size[1] * voxel_size[2] * num_voxels

    # Assert that total volume is a finite positive number
    assert total_volume > 0, "Computed fluid domain volume must be positive"


def test_plausible_velocity_range(sample_volume_data):
    """Optionally validate that velocity magnitudes fall within expected physical bounds."""
    max_reasonable_velocity = 100.0  # m/s — example threshold, can be made scenario-specific

    for step in sample_volume_data["time_steps"]:
        for vector in step["velocity_data"]:
            assert len(vector) == 3, f"Malformed velocity vector: {vector}"
            mag_sq = sum(comp**2 for comp in vector)
            assert mag_sq < max_reasonable_velocity**2, f"Unrealistic velocity magnitude detected: {vector}"


def test_stationary_geometry(sample_mesh_data):
    """Check that the geometry remains constant across all time steps — static boundary."""
    time_steps = sample_mesh_data.get("time_steps", [])
    assert len(time_steps) > 1, "Multiple time steps are required to test geometry stability"

    # Use the first time step as reference
    reference_vertices = time_steps[0]["vertices"]

    for step in time_steps[1:]:
        current_vertices = step["vertices"]
        assert current_vertices == reference_vertices, "Geometry changed across time steps"



