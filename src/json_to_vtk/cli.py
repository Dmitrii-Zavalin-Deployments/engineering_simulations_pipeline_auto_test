# src/json_to_vtk/cli.py

import argparse
from pathlib import Path
from json_to_vtk.mesh_conversion import convert_static_mesh
from json_to_vtk.volume_conversion import convert_volume_series
from json_to_vtk.pvd_writer import generate_pvd
from json_to_vtk.utils import log_info
import json


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert simulation JSON data to VTK format (.vtp, .vti, .pvd) for ParaView rendering."
    )
    parser.add_argument("--mesh", type=Path, help="Path to fluid_mesh_data.json")
    parser.add_argument("--volume", type=Path, help="Path to fluid_volume_data.json")
    parser.add_argument("--outdir", type=Path, default=Path("output"), help="Directory to store VTK output")
    parser.add_argument("--write-pvd", action="store_true", help="Generate .pvd index file for .vti timesteps")
    return parser.parse_args()


def run():
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    if args.mesh:
        vtp_path = args.outdir / "turbine_geometry.vtp"
        log_info(f"Converting mesh: {args.mesh} → {vtp_path}")
        convert_static_mesh(args.mesh, vtp_path)

    if args.volume:
        log_info(f"Converting volume: {args.volume} → {args.outdir}")
        convert_volume_series(args.volume, args.outdir)

        if args.write_pvd:
            log_info("Generating .pvd index file")
            with open(args.volume, "r", encoding="utf-8") as f:
                volume_data = json.load(f)
            timesteps = [ts["time"] for ts in volume_data["time_steps"]]
            filenames = [f"fluid_data_t{str(i).zfill(4)}.vti" for i in range(len(timesteps))]
            generate_pvd(timesteps, filenames, args.outdir / "turbine_flow_animation.pvd")

    if not args.mesh and not args.volume:
        print("Nothing to convert. Use --mesh and/or --volume.")


if __name__ == "__main__":
    run()



