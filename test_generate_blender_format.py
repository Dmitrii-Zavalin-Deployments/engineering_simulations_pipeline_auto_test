import unittest
import json
import os
from generate_blender_format import load_fluid_data, convert_to_blender_format, save_output

class TestBlenderFluidConversion(unittest.TestCase):
    """Unit tests for fluid dynamics data conversion for Blender."""

    @classmethod
    def setUpClass(cls):
        """Prepare mock data and output file path."""
        cls.input_path = "testing-input-output/mock_fluid_data.json"
        cls.output_path = "testing-input-output/mock_blender_data.json"

    def setUp(self):
        """Create test input JSON files."""
        valid_data = {
            "adjusted_velocity_x": 1.5,
            "adjusted_velocity_y": -0.8,
            "adjusted_velocity_z": 0.3
        }
        invalid_data = "Invalid JSON String"
        missing_fields = {}

        # Write valid test data
        with open(self.input_path, 'w') as f:
            json.dump(valid_data, f)

        self.invalid_data_content = invalid_data
        self.missing_data_content = missing_fields

    def tearDown(self):
        """Remove generated test files."""
        if os.path.exists(self.input_path):
            os.remove(self.input_path)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    def test_load_valid_fluid_data(self):
        """Test loading valid fluid dynamics input data."""
        data = load_fluid_data(self.input_path)
        self.assertIsInstance(data, dict)
        self.assertIn("adjusted_velocity_x", data)

    def test_load_invalid_fluid_data(self):
        """Test behavior when input JSON is corrupted."""
        with open(self.input_path, 'w') as f:
            f.write(self.invalid_data_content)
        
        data = load_fluid_data(self.input_path)
        self.assertIsNone(data)

    def test_load_missing_fields(self):
        """Test handling when required fields are missing."""
        with open(self.input_path, 'w') as f:
            json.dump(self.missing_data_content, f)
        
        data = load_fluid_data(self.input_path)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("adjusted_velocity_x", 0.0), 0.0)

    def test_conversion_to_blender_format(self):
        """Test fluid data conversion logic."""
        test_data = {
            "adjusted_velocity_x": 2.2,
            "adjusted_velocity_y": -1.1,
            "adjusted_velocity_z": 0.7
        }
        converted_data = convert_to_blender_format(test_data)
        
        self.assertIn("fluid_simulation", converted_data)
        self.assertEqual(converted_data["fluid_simulation"]["velocity"]["x"], 2.2)

    def test_save_output_json(self):
        """Test saving Blender-compatible JSON output."""
        blender_data = {
            "fluid_simulation": {
                "velocity": {"x": 1.0, "y": 2.0, "z": -1.0},
                "resolution": 128,
                "time_step": 0.05
            }
        }
        save_output(self.output_path, blender_data)
        self.assertTrue(os.path.exists(self.output_path))

        # Validate written JSON structure
        with open(self.output_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data["fluid_simulation"]["velocity"]["x"], 1.0)

if __name__ == "__main__":
    unittest.main()
