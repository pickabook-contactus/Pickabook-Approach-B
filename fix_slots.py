import json
import os
from PIL import Image

# 📂 SETTINGS
INPUT_FOLDER = "backend/assets/templates/magic_of_money/v1/pages"

def fix_coordinates(folder_path):
    print(f"🔧 Fixing Slots in: {folder_path}...\n")
    
    for root, dirs, files in os.walk(folder_path):
        json_path = os.path.join(root, "slot.json")
        if not os.path.exists(json_path):
            continue
            
        print(f"Processing {os.path.basename(root)}...")
        
        # Load JSON once
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  ❌ Error reading JSON: {e}")
            continue

        updated = False
        
        for filename in files:
            if filename.lower().startswith("ref_") and filename.lower().endswith(".png"):
                file_path = os.path.join(root, filename)
                
                try:
                    with Image.open(file_path) as img:
                        bbox = img.getbbox()
                        if bbox:
                            left, top, right, bottom = bbox
                            x, y, w, h = left, top, right - left, bottom - top
                            
                            role = filename.replace("ref_", "").replace(".png", "")
                            
                            # Find matching slot
                            for slot in data.get("slots", []):
                                if slot.get("role") == role:
                                    old_bbox = slot.get("bbox_px", {})
                                    
                                    # Update if changed
                                    if (old_bbox.get("x") != x or 
                                        old_bbox.get("y") != y or 
                                        old_bbox.get("w") != w or 
                                        old_bbox.get("h") != h):
                                        
                                        print(f"  Refining '{role}':")
                                        print(f"    Old: {old_bbox}")
                                        print(f"    New: {{'x': {x}, 'y': {y}, 'w': {w}, 'h': {h}}}")
                                        
                                        slot["bbox_px"] = {"x": x, "y": y, "w": w, "h": h}
                                        updated = True
                except Exception as e:
                    print(f"  ❌ Error processing image {filename}: {e}")

        if updated:
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
            print("  ✅ JSON Updated.")
        else:
            print("  Example matches (No changes needed).")

if __name__ == "__main__":
    if not os.path.exists(INPUT_FOLDER):
         INPUT_FOLDER = os.path.join(os.getcwd(), INPUT_FOLDER)
    fix_coordinates(INPUT_FOLDER)
