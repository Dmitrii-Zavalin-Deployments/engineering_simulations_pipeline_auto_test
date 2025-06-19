# src/json_to_vtk/mesh_conversion.py

from pathlib import Path
import json
import pyvista as pv
import numpy as np


def convert_static_mesh(json_path: Path, output_path: Path) -> None:
    """
    Converts a JSON mesh file into a .vtp (VTK PolyData) file.

    Parameters:
        json_path (Path): Path to the fluid_mesh_data.json file.
        output_path (Path): Path where the output .vtp file will be written.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        mesh_data = json.load(f)

    faces = mesh_data.get("static_faces")
    time_steps = mesh_data.get("time_steps", [])
    if not time_steps:
        raise ValueError("No time_steps found in mesh JSON.")

    vertex_groups = time_steps[0].get("vertices", [])
    vertices = []

    try:
        for group in vertex_groups:
            if isinstance(group, list) and all(isinstance(coord, (list, tuple)) and len(coord) == 3 for coord in group):
                vertices.extend(tuple(coord) for coord in group)
            else:
                raise TypeError(f"Invalid vertex structure in group: {group}")
    except Exception as e:
        raise ValueError(f"Error parsing vertex groups: {e}")

    if not vertices:
        raise ValueError("No valid vertices extracted from JSON input.")

    # Prepare faces for PyVista: [n_pts, i1, i2, ..., n_pts, j1, j2, ...]
    formatted_faces = []
    for face in faces:
        formatted_faces.append(len(face))
        formatted_faces.extend(face)

    points = np.array(vertices, dtype=float)
    cells = np.array(formatted_faces, dtype=int)
    mesh = pv.PolyData(points, cells)

    mesh.save(str(output_path))



