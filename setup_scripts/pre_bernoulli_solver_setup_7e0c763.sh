#!/bin/bash
# setup_scripts/pre_bernoulli_solver_setup_7e0c763.sh

# Turn off 'fail fast' for debugging installation flows
set +e

# Utility function for formatted logging with timestamps
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }

log "🚀 Provisioning lean runtime environment..."

# 0. Pre-installation environment check
log "📋 Initial Environment State:"
python --version
pip list | head -n 5 

# 1. Pip Upgrade
log "📦 Upgrading pip..."
python -m pip install --upgrade pip -v

# 2. Helper Function for Verbose Installation
install_pkg() {
    local pkg=$1
    log "   ↳ Installing $pkg..."
    
    python -m pip install "$pkg" -v 
    
    if [ $? -ne 0 ]; then
        log "   ❌ ERROR: Failed to install $pkg."
        log "   🔍 Running 'pip check' to show conflicts:"
        pip check
        exit 1
    fi
    log "   ✅ $pkg installed successfully."
}

# 3. Dependency Installation Phase
log "📦 Starting dependency installation phase..."

# Foundation (Rule 9: Hybrid Memory)
install_pkg "numpy>=2.0.0"
install_pkg "h5py>=3.12.0"

# Archivist I/O Layer (Rule 10: Cloud Sync)
install_pkg "requests>=2.32.0"
install_pkg "dropbox>=11.36.2"

# Contract Enforcement
install_pkg "jsonschema>=4.23.0"
install_pkg "jsonpath-ng>=1.6.1"

# Legacy Infrastructure (Required by dropbox/third-party)
install_pkg "setuptools>=60.0.0"

log "✅ Environment ready for execution."