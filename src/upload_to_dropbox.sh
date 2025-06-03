#!/bin/bash

# Define your Dropbox API credentials and target folder
APP_KEY="${APP_KEY}"
APP_SECRET="${APP_SECRET}"
REFRESH_TOKEN="${REFRESH_TOKEN}"
DROPBOX_UPLOAD_BASE_FOLDER="/engineering_simulations_pipeline" # This is the base folder on Dropbox

# Define local directories
LOCAL_INPUT_OUTPUT_DIR="$GITHUB_WORKSPACE/data/testing-input-output"
LOCAL_VTK_OUTPUT_DIR="$GITHUB_WORKSPACE/data/testing-input-output/vtk_output"

echo "🔄 Attempting to upload files from ${LOCAL_INPUT_OUTPUT_DIR} and its subdirectories to Dropbox folder ${DROPBOX_UPLOAD_BASE_FOLDER}..."

# Ensure the base local directory exists
if [ ! -d "$LOCAL_INPUT_OUTPUT_DIR" ]; then
    echo "❌ ERROR: Base directory $LOCAL_INPUT_OUTPUT_DIR does not exist."
    exit 1
fi

# --- Phase 1: Upload individual files directly within LOCAL_INPUT_OUTPUT_DIR ---
# This loop handles files like fluid_mesh_data.json, fluid_particles.npy, 3d_model.obj, etc.
# It explicitly checks if the item is a file to avoid trying to upload subdirectories.
for file in "$LOCAL_INPUT_OUTPUT_DIR"/*; do
    if [ -f "$file" ]; then # Checks if the item is a regular file
        echo "📤 Uploading individual file: $file..."
        python3 src/upload_to_dropbox.py \
            "$file" \
            "$DROPBOX_UPLOAD_BASE_FOLDER" \
            "$REFRESH_TOKEN" \
            "$APP_KEY" \
            "$APP_SECRET"

        if [ $? -eq 0 ]; then
            echo "✅ Successfully uploaded file: $file to Dropbox."
        else
            echo "❌ ERROR: Failed to upload file: $file to Dropbox."
            exit 1
        fi
    fi
done

# --- Phase 2: Upload the entire VTK output directory ---
# This explicitly calls the Python script to handle the recursive upload of the vtk_output folder.
if [ -d "$LOCAL_VTK_OUTPUT_DIR" ]; then # Checks if the vtk_output directory exists
    echo "📤 Uploading VTK output directory recursively: $LOCAL_VTK_OUTPUT_DIR..."
    
    # The Dropbox target path for the VTK output will be a subfolder within your base upload folder.
    # For example, if DROPBOX_UPLOAD_BASE_FOLDER is "/engineering_simulations_pipeline",
    # the VTK files will go into "/engineering_simulations_pipeline/vtk_output" on Dropbox.
    DROPBOX_VTK_TARGET_FOLDER="${DROPBOX_UPLOAD_BASE_FOLDER}/vtk_output"

    python3 src/upload_to_dropbox.py \
        "$LOCAL_VTK_OUTPUT_DIR" \
        "$DROPBOX_VTK_TARGET_FOLDER" \
        "$REFRESH_TOKEN" \
        "$APP_KEY" \
        "$APP_SECRET"
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully uploaded VTK output directory: $LOCAL_VTK_OUTPUT_DIR to Dropbox."
    else
        echo "❌ ERROR: Failed to upload VTK output directory: $LOCAL_VTK_OUTPUT_DIR to Dropbox."
        exit 1
    fi
else
    echo "⚠️ Warning: VTK output directory $LOCAL_VTK_OUTPUT_DIR does not exist or is not a directory. Skipping VTK upload."
fi

echo "🎉 All specified files and directories processed successfully!"


