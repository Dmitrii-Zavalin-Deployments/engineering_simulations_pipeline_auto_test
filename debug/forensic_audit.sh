#!/usr/bin/env bash
# ==============================================================================
# FORENSIC AUDIT: CONFIGURATION MIGRATION COLLISION DIAGNOSTIC (FIXED PATHS)
# ==============================================================================
set -euo pipefail

echo "========================================================================="
echo "📊 STEP 1: TARGET ENVIRONMENT & DIRECTORY INVENTORY"
echo "========================================================================="
echo "Checking contents of pipelines/ directory:"
ls -la pipelines/

echo -e "\nChecking contents of configs/ directory:"
ls -la configs/

echo -e "\nChecking Git tracking status for target pipeline files:"
git ls-files pipelines/ || echo "⚠️ No pipeline files tracked in Git index."

echo "========================================================================="
echo "🔍 STEP 2: LOCATING SMOKING-GUN MIGRATION CODE"
echo "========================================================================="
# Search actual project directories and safely manage grep exit codes
set +e
TARGET_SCRIPT=$(grep -rlE "is already versioned correctly|Renaming" setup_scripts/ tests/ 2>/dev/null | head -n 1)
set -e

if [ -z "${TARGET_SCRIPT}" ]; then
    echo "❌ CRITICAL: Could not locate the source script executing the file renames."
    exit 1
else
    echo "🎯 Found anomaly source code file: ${TARGET_SCRIPT}"
fi

echo "========================================================================="
echo "📜 STEP 3: SOURCE AUDIT (LINE-BY-LINE)"
echo "========================================================================="
cat -n "${TARGET_SCRIPT}"

echo "========================================================================="
echo "🛠️ STEP 4: AUTOMATED PATCH INJECTIONS (PROPOSED REMEDIATION)"
echo "========================================================================="
echo "Review the automated sed repair commands below. Un-comment the appropriate"
echo "line in your workflow step to bypass or forcefully resolve the collision."
echo ""

# ------------------------------------------------------------------------------
# SED REPAIR INJECTIONS (PROPOSED HOOKS)
# ------------------------------------------------------------------------------

# OPTION A: If the target script is a Bash script using 'git mv', force overwrite (-f):
# # sed -i 's/git mv/git mv -f/g' "${TARGET_SCRIPT}"

# OPTION B: If it is a Python script using subprocess for 'git mv', inject the force flag:
# # sed -i 's/"git", "mv"/"git", "mv", "-f"/g' "${TARGET_SCRIPT}"

# OPTION C: If it uses native OS 'mv', force overwrite:
# # sed -i 's/mv /mv -f /g' "${TARGET_SCRIPT}"

# OPTION D: Force clean the conflicting destination files directly in the tracking index before renaming:
# # sed -i '/Renaming/i git rm -f "$destination" 2>/dev/null || true' "${TARGET_SCRIPT}"

echo "Audit completed successfully."