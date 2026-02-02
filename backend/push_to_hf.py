"""
Push backend to HuggingFace Spaces using huggingface_hub library.
Uses token authentication to avoid git-lfs issues.
"""
from huggingface_hub import HfApi, upload_folder, login
import os

# Configuration
SPACE_ID = "alipickabook/pickabook-backend"
HF_TOKEN = os.getenv("HF_TOKEN")
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

def push_to_hf():
    print(f"Pushing {BACKEND_DIR} to HuggingFace Space: {SPACE_ID}")
    
    # Login with token
    print("Logging in to HuggingFace...")
    login(token=HF_TOKEN)
    
    api = HfApi()
    
    # Create README.md explicitly with UTF-8 to prevent encoding errors
    readme_path = os.path.join(BACKEND_DIR, "README.md")
    print(f"Writing clean README to {readme_path}...")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("title: Pickabook Backend\n")
        f.write("sdk: docker\n")
        f.write("app_port: 7860\n")
        f.write("---\n\n")
        f.write("# Pickabook Backend\n\n")
        f.write("Backend service for Pickabook Custom Book Generator.\n")
        f.write("Updated: 2026-01-28 Auto-Deploy (Script-Generated)\n")

    # Upload the entire backend folder
    print("Starting upload...")
    result = upload_folder(
        folder_path=BACKEND_DIR,
        repo_id=SPACE_ID,
        repo_type="space",
        ignore_patterns=[
            "*.pyc",
            "__pycache__",
            ".env",
            "uploads/*",
            "assets/orders/*",
            "assets/models/*",
            "_LOCAL_BACKUP*",
            "*.log",
            "e/*",
            ".git*",
            "push_to_hf.py",  # Don't upload this script
        ],
        commit_message="Deploy Two-Phase Master Character Pipeline (Fix Encoding)"
    )
    
    print(f"✅ Upload complete!")
    print(f"Space URL: https://huggingface.co/spaces/{SPACE_ID}")
    return result

if __name__ == "__main__":
    push_to_hf()
