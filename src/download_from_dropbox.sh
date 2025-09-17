#!/bin/bash

# Set environment variables from GitHub Actions secrets
APP_KEY="${APP_KEY}"
APP_SECRET="${APP_SECRET}"
REFRESH_TOKEN="${REFRESH_TOKEN}"
DROPBOX_FOLDER="/engineering_simulations_pipeline"  # Dropbox folder path
LOCAL_FOLDER="./data/testing-input-output"          # Local folder for downloaded files
LOG_FILE="./dropbox_download_log.txt"

# Create the local folder if it doesn't exist
mkdir -p "$LOCAL_FOLDER"

echo "🧹 Cleaning Dropbox folder: deleting all files except .step and flow_data.json..."
python3 src/download_dropbox_files.py delete "$DROPBOX_FOLDER" "$REFRESH_TOKEN" "$APP_KEY" "$APP_SECRET" "$LOG_FILE"

echo "📥 Downloading files from Dropbox..."
python3 src/download_dropbox_files.py download "$DROPBOX_FOLDER" "$LOCAL_FOLDER" "$REFRESH_TOKEN" "$APP_KEY" "$APP_SECRET" "$LOG_FILE"

# Verify downloaded files
if [ "$(ls -A "$LOCAL_FOLDER")" ]; then
    echo "✅ Files successfully downloaded to $LOCAL_FOLDER"
else
    echo "❌ ERROR: No files were downloaded from Dropbox. Check your credentials and folder path."
    exit 1
fi



