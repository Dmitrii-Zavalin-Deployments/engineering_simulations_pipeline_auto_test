# tests/test_conversion_logic.py

import numpy as np
import pyvista as pv
import pytest

from json_to_vtk.mesh_conversion import convert_static_mesh
from json_to_vtk.volume_conversion import convert_volume_series


def test_face_formatting_for_polydata(sample_mesh_data):
    """Check that face definitions are correctly formatted for PyVista PolyData."""
    static_faces = sample_mesh_data["static_faces"]

    for face in static_faces:
        assert isinstance(face, list), "Face must be a list of vertex indices"
        assert len(face) >= 3, "Face must have at least 3 vertices"
        assert all(isinstance(i, int) for i in face), "Vertex indices must be integers"


def test_polydata_export(create_temp_input_files):
    """Write the mesh to .vtp and verify point and face data structure."""
    mesh_out = create_temp_input_files["output_dir"] / "turbine_geometry.vtp"

    convert_static_mesh(
        create_temp_input_files["mesh_path"],
        mesh_out
    )

    output = pv.read(mesh_out)
    assert isinstance(output, pv.PolyData), "Output is not a PolyData object"
    assert output.n_points > 0, "PolyData contains no points"
    assert output.n_cells > 0, "PolyData contains no cells"


def test_image_data_dimensions(create_temp_input_files):
    """Verify that each .vti file has the expected grid dimensions."""
    convert_volume_series(
        create_temp_input_files["volume_path"],
        create_temp_input_files["output_dir"]
    )

    first_vti = create_temp_input_files["output_dir"] / "fluid_data_t0000.vti"
    grid = pv.read(first_vti)
    expected_shape = (1, 1, 3)  # X, Y, Z from [3, 1, 1] reversed

    assert hasattr(grid, "dimensions"), "Output grid has no 'dimensions' attribute"
    assert grid.dimensions == expected_shape, f"Expected dimensions {expected_shape}, got {grid.dimensions}"


def test_grid_alignment(sample_volume_data, create_temp_input_files):
    """Ensure grid origin and spacing match JSON definition."""
    convert_volume_series(
        create_temp_input_files["volume_path"],
        create_temp_input_files["output_dir"]
    )

    vti = pv.read(create_temp_input_files["output_dir"] / "fluid_data_t0000.vti")
    grid_info = sample_volume_data["grid_info"]

    assert np.allclose(vti.origin, grid_info["origin"]), f"Origin mismatch: {vti.origin} vs {grid_info['origin']}"
    assert np.allclose(vti.spacing, grid_info["voxel_size"]), f"Spacing mismatch: {vti.spacing} vs {grid_info['voxel_size']}"


def test_scalar_field_attachment(create_temp_input_files):
    """Check that scalar fields (density and temperature) are present in the .vti output."""
    convert_volume_series(
        create_temp_input_files["volume_path"],
        create_temp_input_files["output_dir"]
    )

    grid = pv.read(create_temp_input_files["output_dir"] / "fluid_data_t0000.vti")
    scalar_arrays = grid.point_data

    assert any(key.lower() == "density" for key in scalar_arrays.keys()), "Missing 'density' field"
    assert any(key.lower() == "temperature" for key in scalar_arrays.keys()), "Missing 'temperature' field"


def test_vector_field_attachment(create_temp_input_files):
    """Verify that a single vector field (velocity) is attached to the .vti file."""
    convert_volume_series(
        create_temp_input_files["volume_path"],
        create_temp_input_files["output_dir"]
    )

    grid = pv.read(create_temp_input_files["output_dir"] / "fluid_data_t0000.vti")

    vector_field = grid.point_data.get("velocity")
    if vector_field is None:
        vector_field = grid.point_data.get("Velocity")

    assert vector_field is not None, "Missing 'velocity' vector field"
    assert vector_field.shape[1] == 3, f"Velocity field must have 3 components per vector, got shape {vector_field.shape}"



