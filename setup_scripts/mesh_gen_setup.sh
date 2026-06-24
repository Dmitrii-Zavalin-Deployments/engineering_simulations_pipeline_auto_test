#!/bin/bash
# setup_scripts/mesh_gen_setup.sh

# Turn off 'fail fast' so we can see the full pip error log
set +e 

echo "🚀 Provisioning lean runtime environment..."

# 1. Conda (Keep -e logic here as these are binary installs)
conda install -y -c conda-forge -c defaults pythonocc-core --debug -vv
if [ $? -ne 0 ]; then echo "❌ Conda install failed"; exit 1; fi

# 2. Pip (Handle failures gracefully)
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

echo "📦 Installing dependencies..."

# Use a function to handle pip installs with error logging
install_pkg() {
    echo "   ↳ Installing $1..."
    pip install "$1"
    if [ $? -ne 0 ]; then
        echo "   ❌ ERROR: Failed to install $1. Checking dependency graph..."
        pip check # This is the smoking gun command that shows conflicts
        exit 1
    fi
    echo "   ✅ $1 installed."
}

install_pkg "numpy>=2.0.0"
install_pkg "h5py>=3.12.0"
install_pkg "requests>=2.32.0"
install_pkg "jsonschema>=4.23.0"

echo "✅ Environment ready for execution."