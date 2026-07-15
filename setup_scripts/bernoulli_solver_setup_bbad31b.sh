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
log "📦 Installing Python dependencies in batch (Grouped by Architectural Rules)..."

# Write requirements dynamically to a temp file to safely support comments and architecture groupings
cat <<EOF > /tmp/bernoulli_requirements.txt
# Foundation (Rule 9: Hybrid Memory)
numpy>=2.0.0
h5py>=3.12.0

# Archivist I/O Layer (Rule 10: Cloud Sync)
requests>=2.32.0

# Contract Enforcement
jsonschema>=4.23.0
jsonpath-ng>=1.6.1

# Support & Utilities
matplotlib>=3.7.0
setuptools>=60.0.0
gmsh>=4.13.1
EOF

python -m pip install --no-cache-dir -r /tmp/bernoulli_requirements.txt
PIP_EXIT=$?

# Clean up temp file
rm -f /tmp/bernoulli_requirements.txt

if [ $PIP_EXIT -ne 0 ]; then
    log "❌ ERROR: Batch installation failed."
    log "🔍 Running 'pip check' to show dependency conflicts:"
    pip check
    exit 1
fi

log "✅ All dependencies installed successfully."
log "✅ Environment ready for execution."