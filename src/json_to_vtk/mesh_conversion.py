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
    with open(json_path, "r") as f:
        mesh_data = json.load(f)

    faces = mesh_data.get("static_faces")
    time_steps = mesh_data.get("time_steps", [])
    if not time_steps:
        raise ValueError("No time_steps found in mesh JSON.")

    # Use the vertices from the first time step
    vertex_groups = time_steps[0].get("vertices", [])
    vertices = [tuple(coord) for group in vertex_groups for coord in group]

    # Prepare faces for PyVista: [n_pts, i1, i2, i3, ..., n_pts, j1, j2, j3, ...]
    formatted_faces = []
    for face in faces:
        formatted_faces.append(len(face))
        formatted_faces.extend(face)

    # Create PolyData
    points = np.array(vertices)
    cells = np.array(formatted_faces)
    mesh = pv.PolyData(points, cells)

    # Write to .vtp
    mesh.save(str(output_path))



