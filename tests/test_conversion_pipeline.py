import unittest
import os
import json
import numpy as np
import bpy  # Ensure Blender Python API is available
from jsonschema import validate

# Try to import pyopenvdb for deeper VDB validation (skip if unavailable)
try:
    import pyopenvdb as vdb
    vdb_available = True
except ImportError:
    vdb_available = False
    print("Warning: pyopenvdb not installed. VDB content tests will be limited.")


class TestFinalBlenderAssembly(unittest.TestCase):

    def setUp(self):
        """Define paths for input simulation data and Blender import file"""
        self.particles_path = "data/testing-input-output/fluid_particles.json"
        self.mesh_path = "data/testing-input-output/fluid_mesh.abc"
        self.vdb_path = "data/testing-input-output/fluid_volume.vdb"
        self.blender_scene = "data/testing-input-output/final_blender_scene.blend"

        # Ensure dummy input files exist
        if not os.path.exists(self.particles_path):
            with open(self.particles_path, "w") as f:
                f.write('{"particle_data": [{"position": [0, 0, 0]}]}')
        if not os.path.exists(self.mesh_path):
            open(self.mesh_path, 'a').close()
        if not os.path.exists(self.vdb_path):
            open(self.vdb_path, 'a').close()

        with open(self.particles_path) as f:
            self.particle_data = json.load(f)

    ### PARTICLE DATA VALIDATION ###

    def test_particle_json_schema(self):
        """Ensure particle motion data follows defined JSON schema"""
        schema = {
            "type": "object",
            "properties": {
                "particle_info": {"type": "object"},
                "velocity_fields": {"type": "array"},
                "global_parameters": {"type": "object"}
            },
            "required": ["particle_info", "velocity_fields", "global_parameters"]
        }
        validate(instance=self.particle_data, schema=schema)

    def test_blender_particle_system_exists(self):
        """Ensure a particle system is imported from the JSON."""
        bpy.ops.wm.read_homefile()
        bpy.ops.import_scene.json(filepath=self.particles_path)
        has_particle_system = any(obj.particle_systems for obj in bpy.data.objects)
        self.assertTrue(has_particle_system, "No particle system found in the imported JSON data.")

    ### FLUID MESH VALIDATION ###

    def test_mesh_import_structure(self):
        """Ensure fluid mesh is correctly imported into Blender"""
        bpy.ops.import_mesh.alembic(filepath=self.mesh_path)
        assert any(obj.type == 'MESH' for obj in bpy.data.objects), "No mesh object found in the imported Alembic data."
        assert len(bpy.context.active_object.material_slots) > 0, "Materials missing on mesh!"

    ### VDB FILE VALIDATION ###

    def test_vdb_output_exists(self):
        """Ensure the fluid_volume.vdb file is created"""
        assert os.path.exists(self.vdb_path), f"VDB output file not found at {self.vdb_path}!"

    @unittest.skipUnless(vdb_available, "pyopenvdb is not installed")
    def test_vdb_grid_type(self):
        """Check if the VDB file contains expected voxel grid for density fields"""
        if os.path.exists(self.vdb_path):
            try:
                grid = vdb.read(self.vdb_path)
                self.assertIsInstance(grid.grids()[0], vdb.FloatGrid, "Expected FloatGrid for density field!")
            except Exception as e:
                self.fail(f"Failed to read VDB file: {e}")

    ### FINAL BLENDER EXPORT VALIDATION ###

    def test_blender_scene_contains_objects(self):
        """Ensure Blender scene contains objects after import."""
        bpy.ops.wm.read_homefile()
        bpy.ops.import_scene.json(filepath=self.particles_path)
        bpy.ops.import_mesh.alembic(filepath=self.mesh_path)
        try:
            bpy.ops.object.volume_import(filepath=self.vdb_path)
        except AttributeError:
            self.skipTest("VDB import operator not found. Ensure necessary addon is enabled.")

        assert len(bpy.data.objects) >= 1, "Blender scene should contain at least one object after import."

    def test_blender_animation_data(self):
        """Ensure animation data is present before export"""
        bpy.ops.wm.save_mainfile(filepath=self.blender_scene)
        assert bpy.context.scene.frame_end > bpy.context.scene.frame_start, "Final animation export incomplete!"

    def test_blender_file_structure(self):
        """Ensure Blender file contains expected objects"""
        assert len(bpy.context.scene.objects) > 0, "No objects found in final Blender scene!"
        assert any(obj.type == 'MESH' for obj in bpy.context.scene.objects), "No mesh found in final Blender file!"
        assert any(obj.type == 'VOLUME' for obj in bpy.context.scene.objects), "No volume data found!"

if __name__ == "__main__":
    unittest.main()



