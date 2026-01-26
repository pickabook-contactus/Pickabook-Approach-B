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
local_file = os.path.join("backend", "app", "services", "compositor", "engine.py")
remote_path = "app/services/compositor/engine.py"

print(f"Uploading {local_file} to {repo_id}...")

if not os.path.exists(local_file):
    print(f"❌ Error: File not found at {os.path.abspath(local_file)}")
    exit(1)

try:
    api.upload_file(
        path_or_fileobj=local_file,
        path_in_repo=remote_path,
        repo_id=repo_id,
        repo_type="space",
        commit_message="Fix UnboundLocalError: Define slot coords before usage"
    )
    print("✅ Upload success!")
except Exception as e:
    print(f"❌ Upload failed: {e}")
