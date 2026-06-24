#!/bin/bash
# setup_scripts/mesh_gen_setup.sh
# Lean Runtime: Only local physics and contract enforcement dependencies.

set -e  # Fail fast

echo "🚀 Provisioning lean runtime environment..."

# 1. Install heavy binary physics stack via Conda
echo "📦 Installing pythonocc-core..."
conda install -y -c conda-forge pythonocc-core
echo "✅ pythonocc-core installed successfully."

# 2. Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip
echo "✅ Pip upgraded."

# 3. Install required runtime dependencies with explicit logging
echo "📦 Installing dependencies..."

echo "   ↳ Installing numpy..."
pip install numpy>=2.0.0
echo "   ✅ numpy installed."

echo "   ↳ Installing h5py..."
pip install h5py>=3.12.0
echo "   ✅ h5py installed."

echo "   ↳ Installing requests..."
pip install requests>=2.32.0
echo "   ✅ requests installed."

echo "   ↳ Installing jsonschema..."
pip install jsonschema>=4.23.0
echo "   ✅ jsonschema installed."

echo "✅ Environment ready for execution."