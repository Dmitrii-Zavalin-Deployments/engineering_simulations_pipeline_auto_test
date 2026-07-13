#!/bin/bash

# Keep 'set +e' to handle errors manually
set +e

# Utility function for formatted logging
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }

log "🚀 Provisioning runtime environment (Cold Start)..."

# 0. Pre-installation environment check
log "📋 Initial Environment State:"
python --version
pip list | head -n 5 

# 1. Conda Installation 
# Note: Ensure 'conda-solver: libmamba' is set in your Actions YAML for maximum speed
log "📦 Installing base binary layers via Conda..."
conda install -y -c conda-forge pythonocc-core gmsh numpy pip
if [ $? -ne 0 ]; then 
    log "❌ ERROR: Conda install failed."
    exit 1
fi
log "✅ Base Conda dependencies installed."

# 2. Pip Upgrade
log "📦 Upgrading pip..."
python -m pip install --upgrade pip

# 3. Batched Dependency Installation
# Installing in one batch is significantly faster than individual calls
# because it allows Pip to resolve the full dependency tree in a single pass.
log "📦 Installing Python dependencies in batch..."
python -m pip install --no-cache-dir \
    "numpy>=2.0.0" \
    "h5py>=3.12.0" \
    "requests>=2.32.0" \
    "jsonschema>=4.23.0" \
    "matplotlib>=3.7.0" \
    "setuptools>=60.0.0" \
    "dropbox>=11.36.2" \
    "gmsh>=4.13.1" \
    "jsonpath-ng>=1.6.1"

if [ $? -ne 0 ]; then
    log "❌ ERROR: Batch installation failed."
    log "🔍 Running 'pip check' to show dependency conflicts:"
    pip check
    exit 1
fi

log "✅ All dependencies installed successfully."
log "✅ Environment ready for execution."