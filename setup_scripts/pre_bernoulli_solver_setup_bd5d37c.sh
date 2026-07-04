#!/bin/bash
# setup_scripts/pre_bernoulli_solver_setup.sh

# Turn off 'fail fast' for debugging installation flows
set +e

# Utility function for formatted logging with timestamps
log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }

log "🚀 Provisioning lean runtime environment..."

# 0. Pre-installation environment check
log "📋 Initial Environment State:"
python --version
pip list | head -n 5 
echo "   (truncated list...)"

# 1. Conda Installation
log "📦 Installing pythonocc-core..."
conda install -y -c conda-forge -c defaults pythonocc-core pip --debug -vv
if [ $? -ne 0 ]; then 
    log "❌ ERROR: Conda install failed. Check dependencies above."
    exit 1
fi
log "✅ pythonocc-core installed."

# 2. Pip Upgrade
log "📦 Upgrading pip..."
python -m pip install --upgrade pip -v

# 3. Helper Function for Verbose Installation
install_pkg() {
    local pkg=$1
    log "   ↳ Installing $pkg..."
    
    # -v adds verbose logging to show exactly what dependency metadata is being checked
    python -m pip install "$pkg" -v 
    
    if [ $? -ne 0 ]; then
        log "   ❌ ERROR: Failed to install $pkg."
        log "   🔍 Running 'pip check' to show conflicts:"
        pip check
        exit 1
    fi
    log "   ✅ $pkg installed successfully."
}

# 4. Dependency Installation
log "📦 Starting dependency installation phase..."
install_pkg "numpy>=2.0.0"
install_pkg "h5py>=3.12.0"
install_pkg "requests>=2.32.0"
install_pkg "jsonschema>=4.23.0"

# Inject setuptools to provide 'pkg_resources' required by legacy/third-party packages like dropbox
install_pkg "setuptools>=60.0.0"

install_pkg "dropbox>=11.36.2"

log "✅ Environment ready for execution."