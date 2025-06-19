# tests/conftest.py

import json
import pytest
from pathlib import Path
import sys
import os

# Ensure `src/` is in sys.path so we can import json_to_vtk modules
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_mesh_data():
    """Mocked mesh JSON structure reflecting real-world turbine geometry format with multiple time steps."""
    vertices_frame = [
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
        [[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0]]
    ]

    return {
        "mesh_name": "FluidSurface",
        "static_faces": [
            [0, 1, 314, 313],
            [10, 11, 12, 13],
            [20, 21, 22, 23],
            [30, 31, 32, 33]
        ],
        "time_steps": [
            {"time": 0.01, "frame": 0, "vertices": vertices_frame},
            {"time": 0.02, "frame": 1, "vertices": vertices_frame}
        ]
    }


@pytest.fixture
def sample_volume_data():
    """Mocked volumetric fluid data structure with multiple time steps and vector/scalar fields."""
    return {
        "volume_name": "FluidVolume",
        "metadata": {
            "source_navier_stokes": "navier_stokes_results.json",
            "source_initial_data": "initial_data.json",
            "generated_timestamp": "2025-06-19T17:41:18.882852"
        },
        "grid_info": {
            "dimensions": [3, 1, 1],  # Z, Y, X
            "voxel_size": [0.1, 0.1, 0.1],
            "origin": [0.0, 0.0, 0.0]
        },
        "time_steps": [
            {
                "time": 0.01,
                "frame": 0,
                "density_data": [1025.1686, 1024.9879, 1024.8434],
                "velocity_data": [
                    [0.0, 0.0, 0.0],
                    [0.1, 0.0, 0.0],
                    [0.2, 0.0, 0.0]
                ],
                "temperature_data": [0.34438, 0.34436, 0.34434]
            },
            {
                "time": 0.02,
                "frame": 1,
                "density_data": [1025.3493, 1025.0602, 1024.9157],
                "velocity_data": [
                    [0.0, 0.1, 0.0],
                    [0.1, 0.1, 0.0],
                    [0.2, 0.1, 0.0]
                ],
                "temperature_data": [0.34441, 0.34437, 0.34435]
            }
        ]
    }


@pytest.fixture
def create_temp_input_files(tmp_path, sample_mesh_data, sample_volume_data):
    """Creates fluid_mesh_data.json and fluid_volume_data.json as temporary files for testing."""
    mesh_path = tmp_path / "fluid_mesh_data.json"
    volume_path = tmp_path / "fluid_volume_data.json"

    mesh_path.write_text(json.dumps(sample_mesh_data, indent=2))
    volume_path.write_text(json.dumps(sample_volume_data, indent=2))

    return {
        "mesh_path": mesh_path,
        "volume_path": volume_path,
        "output_dir": tmp_path
    }



