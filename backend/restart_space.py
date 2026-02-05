from huggingface_hub import HfApi, login
import os

SPACE_ID = "alipickabook/pickabook-backend"
HF_TOKEN = os.getenv("HF_TOKEN")

def restart_space():
    print("Logging in...")
    login(token=HF_TOKEN)
    api = HfApi()
    
    print(f"Restarting Space: {SPACE_ID}...")
    api.restart_space(repo_id=SPACE_ID)
    print("Space restart triggered. This will force a rebuild/reload of all assets.")

if __name__ == "__main__":
    restart_space()
