# test_json_structure.py

import pytest


def test_mesh_json_structure(sample_mesh_data):
    assert "mesh_name" in sample_mesh_data, "Missing 'mesh_name' key"
    assert "static_faces" in sample_mesh_data, "Missing 'static_faces' key"
    assert isinstance(sample_mesh_data["static_faces"], list), "'static_faces' should be a list"

    assert "time_steps" in sample_mesh_data, "Missing 'time_steps' key"
    assert isinstance(sample_mesh_data["time_steps"], list), "'time_steps' should be a list"
    assert len(sample_mesh_data["time_steps"]) > 0, "No time steps found"

    first_step = sample_mesh_data["time_steps"][0]
    assert "vertices" in first_step, "Missing 'vertices' in time step"
    assert isinstance(first_step["vertices"], list), "'vertices' should be a list of lists"

    for group in first_step["vertices"]:
        for vertex in group:
            assert len(vertex) == 3, f"Vertex {vertex} must have 3 coordinates"
            assert all(isinstance(coord, (int, float)) for coord in vertex), f"Invalid coordinate in vertex {vertex}"


def test_volume_json_grid_structure(sample_volume_data):
    assert "grid_info" in sample_volume_data, "Missing 'grid_info'"
    grid = sample_volume_data["grid_info"]

    for key in ("dimensions", "voxel_size", "origin"):
        assert key in grid, f"Missing '{key}' in grid_info"
        assert isinstance(grid[key], list), f"'{key}' should be a list"
        assert len(grid[key]) == 3, f"'{key}' should have three components"


def test_time_series_integrity(sample_volume_data):
    assert "time_steps" in sample_volume_data, "Missing 'time_steps'"
    timesteps = sample_volume_data["time_steps"]
    assert isinstance(timesteps, list) and len(timesteps) > 0, "No timesteps found"

    for step in timesteps:
        assert "density_data" in step, "Missing 'density_data'"
        assert "temperature_data" in step, "Missing 'temperature_data'"
        assert "velocity_data" in step, "Missing 'velocity_data'"

        assert isinstance(step["density_data"], list), "'density_data' must be a list"
        assert isinstance(step["temperature_data"], list), "'temperature_data' must be a list"
        assert isinstance(step["velocity_data"], list), "'velocity_data' must be a list"


def test_velocity_vector_field(sample_volume_data):
    for step in sample_volume_data["time_steps"]:
        velocity_data = step["velocity_data"]
        for vector in velocity_data:
            assert isinstance(vector, list), "Each velocity vector must be a list"
            assert len(vector) == 3, f"Velocity vector {vector} must have 3 components"
            assert all(isinstance(comp, (int, float)) for comp in vector), f"Non-numeric velocity component in {vector}"



