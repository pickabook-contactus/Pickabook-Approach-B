import requests
import json
import os
import time

API_URL = "http://localhost:8000/api/v1/orders/create"

# Use absolute path to a file we know exists
# e.g. the bg.png we just verified
REAL_FILE_PATH = r"E:\Pickabook Ali\Approach B\pickabook-monorepo\backend\assets\templates\magic_of_money\v1\pages\p001\bg.png"
if not os.path.exists(REAL_FILE_PATH):
    print(f"Warning: Test file not found at {REAL_FILE_PATH}")
    # Try alternate
    REAL_FILE_PATH = os.path.abspath("backend/assets/templates/child_can_be.png")

# Format as file URI with 3 slashes for Windows: file:///C:/...
# urllib.request.pathname2url handles spaces and slashes correctly
from urllib.request import pathname2url
file_uri = "file:///" + pathname2url(REAL_FILE_PATH).lstrip('/')

def verify_order():
    print(f"Using Test File URI: {file_uri}")
    
    payload = {
        "child_name": "Test Child",
        "photo_url": file_uri,
        "mom_name": "Test Mom",
        "mom_photo_url": file_uri, # Use same for mom for testing
        "story_id": "magic_of_money"
    }
    
    try:
        print(f"Sending POST to {API_URL}...")
        resp = requests.post(API_URL, json=payload)
        
        if resp.status_code == 200:
            print("✅ SUCCESS: Order created!")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"❌ FAILED: Status {resp.status_code}")
            print(resp.text)

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    verify_order()
