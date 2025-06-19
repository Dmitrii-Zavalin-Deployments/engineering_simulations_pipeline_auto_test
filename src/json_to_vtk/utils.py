# src/json_to_vtk/utils.py

import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, Tuple


def load_json(path: Path) -> Dict[str, Any]:
    """
    Loads a JSON file and returns the parsed Python object.

    Parameters:
        path (Path): Path to the .json file.

    Returns:
        dict: Parsed JSON data.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def reshape_scalar_field(data: list, dimensions: Tuple[int, int, int]) -> np.ndarray:
    """
    Converts a flat list of scalar values into a 3D NumPy array with Z, Y, X shape.

    Parameters:
        data (list): Flat list of values.
        dimensions (tuple): (Z, Y, X) order from JSON.

    Returns:
        np.ndarray: 3D array reshaped accordingly.
    """
    expected_size = np.prod(dimensions)
    if len(data) != expected_size:
        raise ValueError(f"Expected {expected_size} elements, got {len(data)}")

    return np.array(data, dtype=float).reshape(dimensions)


def reshape_vector_field(data: list, num_points: int) -> np.ndarray:
    """
    Reshapes a list of [x, y, z] vectors into a NumPy array.

    Parameters:
        data (list): List of 3-element vectors.
        num_points (int): Expected number of vectors (should match grid points).

    Returns:
        np.ndarray: (num_points, 3) array.
    """
    array = np.array(data, dtype=float)
    if array.shape != (num_points, 3):
        raise ValueError(f"Expected shape ({num_points}, 3), got {array.shape}")
    return array


def log_info(message: str) -> None:
    print(f"[INFO] {message}")


def log_warning(message: str) -> None:
    print(f"[WARNING] {message}")


def log_error(message: str) -> None:
    print(f"[ERROR] {message}")



