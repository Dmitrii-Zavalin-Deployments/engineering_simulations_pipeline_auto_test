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

    # Load vertices from first time step
    vertex_data = time_steps[0].get("vertices", [])

    # Flatten: support both [[[], [], []], ...] and [[], [], []] structures
    if all(isinstance(entry, (list, tuple)) and len(entry) == 3 for entry in vertex_data):
        vertices = [tuple(coord) for coord in vertex_data]
    else:
        # Assume list of layers/groups of vertices
        vertices = []
        for group in vertex_data:
            if not isinstance(group, list):
                raise ValueError(f"Invalid vertex group: {group}")
            for coord in group:
                if not isinstance(coord, (list, tuple)) or len(coord) != 3:
                    raise ValueError(f"Invalid vertex coordinate: {coord}")
                vertices.append(tuple(coord))

    if not vertices:
        raise ValueError("No valid vertices found in mesh.")

    # Prepare faces for PyVista: [n_pts, i1, i2, ..., n_pts, j1, j2, ...]
    formatted_faces = []
    for face in faces:
        formatted_faces.append(len(face))
        formatted_faces.extend(face)

    points = np.array(vertices, dtype=float)
    cells = np.array(formatted_faces, dtype=int)

    mesh = pv.PolyData(points, cells)
    mesh.save(str(output_path))



