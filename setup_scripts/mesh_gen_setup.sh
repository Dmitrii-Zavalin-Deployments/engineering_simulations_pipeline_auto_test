#!/bin/bash
# setup_scripts/mesh_gen_setup.sh
# Lean Runtime: Only local physics and contract enforcement dependencies.

set -e  # Fail fast

echo "🚀 Provisioning lean runtime environment (Excluding redundant I/O stack)..."

# 1. Install heavy binary physics stack via Conda
conda install -y -c conda-forge pythonocc-core

# 2. Upgrade pip
python -m pip install --upgrade pip

# 3. Install required runtime dependencies only
# We removed 'dropbox' as it is handled by the parent Aggregator environment.
pip install \
    numpy>=2.0.0 \
    h5py>=3.12.0 \
    requests>=2.32.0 \
    jsonschema>=4.23.0

echo "✅ Environment ready for execution."