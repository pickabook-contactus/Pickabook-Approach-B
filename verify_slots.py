import json
import os
from PIL import Image

# 📂 SETTINGS: Put your folder path here
INPUT_FOLDER = "backend/assets/templates/magic_of_money/v1/pages"

def find_coordinates(folder_path):
    print(f"🔍 Scanning folder: {folder_path}...\n")
    
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().startswith("ref_") and filename.lower().endswith(".png"):
                file_path = os.path.join(root, filename)
                page_id = os.path.basename(root)
                
                try:
                    with Image.open(file_path) as img:
                        # 1. Get image size (Canvas size)
                        canvas_w, canvas_h = img.size
                        
                        # 2. Find the bounding box of non-transparent pixels
                        # (getbbox returns: left, top, right, bottom)
                        bbox = img.getbbox()
                        
                        if bbox:
                            left, top, right, bottom = bbox
                            
                            # 3. Calculate x, y, w, h
                            x = left
                            y = top
                            w = right - left
                            h = bottom - top
                            
                            print(f"✅ Found Character in: {page_id}/{filename}")
                            print(f"   Image BBox: x={x}, y={y}, w={w}, h={h}")
                            print(f"   Image Mode: {img.mode}")
                            
                            # Check against slot.json
                            json_path = os.path.join(root, "slot.json")
                            if os.path.exists(json_path):
                                with open(json_path, "r") as f:
                                    data = json.load(f)
                                    # Find matching role
                                    role = filename.replace("ref_", "").replace(".png", "")
                                    matched = False
                                    for slot in data.get("slots", []):
                                        if slot.get("role") == role:
                                            matched = True
                                            sj = slot["bbox_px"]
                                            print(f"   Slot JSON : x={sj['x']}, y={sj['y']}, w={sj['w']}, h={sj['h']}")
                                            
                                            # Compare
                                            if abs(sj['x'] - x) > 10 or abs(sj['y'] - y) > 10:
                                                print("   ❌ MISMATCH DETECTED!")
                                            else:
                                                print("   ✅ MATCH!")
                                    if not matched:
                                        print(f"   ⚠️ No slot found for role '{role}' in JSON")
                            else:
                                print("   ⚠️ No slot.json found")
                                
                            print("-" * 40)
                        else:
                            print(f"⚠️ {page_id}/{filename}: Image is completely empty/transparent!")
                            
                except Exception as e:
                    print(f"❌ Error reading {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER):
         # Try absolute path fallback for my environment
         INPUT_FOLDER = os.path.join(os.getcwd(), INPUT_FOLDER)
    
    find_coordinates(INPUT_FOLDER)
