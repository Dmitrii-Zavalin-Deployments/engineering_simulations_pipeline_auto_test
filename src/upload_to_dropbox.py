import dropbox
import os
import requests
import sys

# Function to refresh the access token
def refresh_access_token(refresh_token, client_id, client_secret):
    """Refreshes the Dropbox access token using the refresh token."""
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        # Provide more detailed error message for debugging
        raise Exception(f"Failed to refresh access token: Status Code {response.status_code}, Response: {response.text}")

# Function to upload a single file to Dropbox
def upload_single_file_to_dropbox(local_file_path, dropbox_file_path, refresh_token, client_id, client_secret):
    """Uploads a local file to a specified path on Dropbox."""
    try:
        # Refresh the access token before each upload attempt
        access_token = refresh_access_token(refresh_token, client_id, client_secret)
        dbx = dropbox.Dropbox(access_token)

        # Open the local file in binary read mode
        with open(local_file_path, "rb") as f:
            # Upload the file, overwriting if it already exists
            dbx.files_upload(f.read(), dropbox_file_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ Successfully uploaded file to Dropbox: {dropbox_file_path}")
        return True # Indicate success
    except Exception as e:
        print(f"❌ Failed to upload file '{local_file_path}' to Dropbox: {e}")
        return False # Indicate failure

# NEW FUNCTION: To upload a directory recursively
def upload_directory_to_dropbox(local_dir_path, dropbox_base_path, refresh_token, client_id, client_secret):
    """Uploads a local directory and its contents recursively to a specified base path on Dropbox."""
    success = True
    for root, _, files in os.walk(local_dir_path):
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            # Calculate the relative path from the local_dir_path
            # e.g., if local_dir_path is '/a/b' and local_file_path is '/a/b/c/file.txt', relative_path will be 'c/file.txt'
            relative_path = os.path.relpath(local_file_path, local_dir_path)
            
            # Construct the full destination path on Dropbox
            # Use os.path.join for platform independence, then replace backslashes with forward slashes for Dropbox
            dropbox_file_path = os.path.join(dropbox_base_path, relative_path).replace("\\", "/") 
            
            print(f"📤 Uploading {local_file_path} to Dropbox: {dropbox_file_path}...")
            if not upload_single_file_to_dropbox(local_file_path, dropbox_file_path, refresh_token, client_id, client_secret):
                success = False
                print(f"❌ Failed to upload {local_file_path}. Continuing with other files, but overall upload will be marked as failed.")
    return success

# Entry point for the script
if __name__ == "__main__":
    # The script expects 5 command-line arguments:
    # 1. local_path (absolute path to the file OR directory to upload)
    # 2. dropbox_destination_path (the destination folder/file in Dropbox)
    # 3. refresh_token
    # 4. client_id (APP_KEY)
    # 5. client_secret (APP_SECRET)
    if len(sys.argv) != 6:
        print("Usage: python src/upload_to_dropbox.py <local_path> <dropbox_destination_path> <refresh_token> <client_id> <client_secret>")
        sys.exit(1) # Exit with an error code for incorrect usage

    # Parse command-line arguments
    local_path_to_upload = sys.argv[1]
    dropbox_destination_path = sys.argv[2] # This can be a target folder or a specific file path on Dropbox
    refresh_token = sys.argv[3]
    client_id = sys.argv[4]
    client_secret = sys.argv[5]

    # Verify that the local path exists before attempting any action
    if not os.path.exists(local_path_to_upload):
        print(f"❌ Error: The local path '{local_path_to_upload}' was not found. Please ensure it exists.")
        sys.exit(1) # Exit with an error code if the path is not found

    # Determine if the path is a file or a directory and call the appropriate upload function
    if os.path.isfile(local_path_to_upload):
        # If it's a file, ensure the Dropbox destination path is properly formed for a file
        # If dropbox_destination_path ends with a '/', it's a folder, so append filename.
        # Otherwise, assume dropbox_destination_path is the full desired file path.
        if dropbox_destination_path.endswith('/'):
            dropbox_file_path = f"{dropbox_destination_path}{os.path.basename(local_path_to_upload)}"
        else:
            dropbox_file_path = dropbox_destination_path # Assume it's already the full target file path

        print(f"Attempting to upload single file: {local_path_to_upload} to {dropbox_file_path}")
        if not upload_single_file_to_dropbox(local_path_to_upload, dropbox_file_path, refresh_token, client_id, client_secret):
            sys.exit(1) # Exit with an error code if the upload itself fails

    elif os.path.isdir(local_path_to_upload):
        print(f"Attempting to upload directory: {local_path_to_upload} to Dropbox base path: {dropbox_destination_path}")
        if not upload_directory_to_dropbox(local_path_to_upload, dropbox_destination_path, refresh_token, client_id, client_secret):
            sys.exit(1) # Exit with an error code if the directory upload fails

    else:
        print(f"❌ Error: '{local_path_to_upload}' is neither a file nor a directory. Cannot upload.")
        sys.exit(1) # Exit with an error code for unsupported path type


