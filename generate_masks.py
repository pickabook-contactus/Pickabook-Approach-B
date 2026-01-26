import json
import os
from PIL import Image, ImageDraw

# Configuration
# Path relative to where I run the script
PAGES_DIR = "backend/assets/templates/magic_of_money/v1/pages"
SLOT_COLORS = {
    "child": (255, 0, 255, 255),   # Magenta #FF00FF
    "mom": (0, 255, 255, 255),     # Cyan #00FFFF
    "dad": (255, 255, 0, 255)      # Yellow #FFFF00
}

def generate_masks_from_json():
    print(f"Scanning for slot.json in {PAGES_DIR}...")
    # Walk through every page folder
    for root, dirs, files in os.walk(PAGES_DIR):
        if "slot.json" in files:
            json_path = os.path.join(root, "slot.json")
            mask_path = os.path.join(root, "slot_mask.png")
            
            # 1. Read coordinates
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading {json_path}: {e}")
                continue
            
            # Get canvas size (default to 2048x1536 if missing)
            width = data.get("canvas", {}).get("width_px", 2048)
            height = data.get("canvas", {}).get("height_px", 1536)
            
            # 2. Create Blank Transparent Image
            mask_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(mask_img)
            
            # 3. Paint the slots
            for slot in data.get("slots", []):
                role = slot.get("role", "unknown")
                # Default to white if role color not defined
                color = SLOT_COLORS.get(role, (255, 255, 255, 255)) 
                
                bbox = slot.get("bbox_px")
                if not bbox: continue
                
                x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]
                
                # Draw the rectangle
                draw.rectangle([x, y, x + w, y + h], fill=color)
                print(f"  Painted {role} slot on {os.path.basename(root)}")

            # 4. Save the Mask
            mask_img.save(mask_path)
            print(f"✅ Generated: {mask_path}")

if __name__ == "__main__":
    generate_masks_from_json()
