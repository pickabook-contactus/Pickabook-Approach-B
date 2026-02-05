from huggingface_hub import HfApi, login
import os

SPACE_ID = "alipickabook/pickabook-backend"
# Use existing token from env or hardcode for this script
HF_TOKEN = os.getenv("HF_TOKEN")

def force_upload():
    print("Logging in...")
    login(token=HF_TOKEN)
    api = HfApi()

    local_assets = os.path.join(os.path.dirname(__file__), "assets")
    
    print(f"Force uploading {local_assets} to {SPACE_ID}/assets...")
    
    # Upload folder contents to the 'assets' folder in the repo
    # path_in_repo="assets" means it puts "assets/..." into "assets/..."? 
    # No, upload_folder uploads CONTENTS of folder_path to path_in_repo.
    # So if we want repo/assets/templates, we upload local/assets to repo/assets.
    
    api.upload_folder(
        folder_path=local_assets,
        path_in_repo="assets",
        repo_id=SPACE_ID,
        repo_type="space"
    )
    print("Upload Complete.")

if __name__ == "__main__":
    force_upload()
