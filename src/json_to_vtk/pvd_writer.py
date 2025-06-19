# src/json_to_vtk/pvd_writer.py

from pathlib import Path
from typing import List
import xml.etree.ElementTree as ET


def generate_pvd(timesteps: List[float], filenames: List[str], output_path: Path) -> None:
    """
    Creates a .pvd file that indexes a sequence of .vti files for ParaView time-series animation.

    Parameters:
        timesteps (List[float]): Simulation time values corresponding to each frame.
        filenames (List[str]): Relative or absolute paths to .vti files.
        output_path (Path): Path to the output .pvd file.
    """
    if len(timesteps) != len(filenames):
        raise ValueError("Mismatch between number of timesteps and filenames")

    vtkfile = ET.Element("VTKFile", type="Collection", version="0.1", byte_order="LittleEndian")
    collection = ET.SubElement(vtkfile, "Collection")

    for time, fname in zip(timesteps, filenames):
        ET.SubElement(collection, "DataSet", {
            "timestep": str(time),
            "group": "",
            "part": "0",
            "file": fname
        })

    tree = ET.ElementTree(vtkfile)
    tree.write(output_path, xml_declaration=True, encoding="utf-8")



