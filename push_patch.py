import os
from huggingface_hub import HfApi
from dotenv import load_dotenv

# Load env from root
load_dotenv(".env")
load_dotenv("backend/.env")

token = os.getenv("HF_TOKEN")
if not token:
    print("Error: HF_TOKEN not found in environment.")
    exit(1)

api = HfApi(token=token)
repo_id = "alipickabook/pickabook-backend"
# Handle Windows paths correctly
# Handle Windows paths correctly
# Deploying Infrastructure Updates
files_to_deploy = [
    {
        "local": os.path.join("backend", "start_free_tier.sh"),
        "remote": "start_free_tier.sh"
    }
]

for item in files_to_deploy:
    local_file = item["local"]
    remote_path = item["remote"]

    print(f"Uploading {local_file} to {repo_id}...")

    if not os.path.exists(local_file):
        print(f"❌ Error: File not found at {os.path.abspath(local_file)}")
        continue

    try:
        api.upload_file(
            path_or_fileobj=local_file,
            path_in_repo=remote_path,
            repo_id=repo_id,
            repo_type="space",
            commit_message="Enable Embedded Redis (Unlimited Quota)"
        )
        print(f"✅ Upload success for {remote_path}!")
    except Exception as e:
        print(f"❌ Upload failed for {remote_path}: {e}")
