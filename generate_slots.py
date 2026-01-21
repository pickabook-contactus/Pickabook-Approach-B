from PIL import Image
import json
import os

def get_bbox_from_image(image_path: str, role: str):
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # Simple "White to Transparent" for these samples
        data = img.getdata()
        new_data = []
        for item in data:
            # If pixel is near white, make it transparent
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        
        # Save the fixed transparent image back (optional, but good for testing)
        img.save(image_path)

        bbox = img.getbbox()
        if bbox:
            return {
                "slot_id": role,
                "role": role,
                "bbox_px": {
                    "x": bbox[0],
                    "y": bbox[1],
                    "w": bbox[2] - bbox[0],
                    "h": bbox[3] - bbox[1]
                },
                "z_index": 10 if role == "child" else 5, 
                "rotation_deg": 0,
                "scale_mode": "fit_height"
            }
        else:
            print(f"Warning: Empty image for {role}")
            return None
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def main():
    # Use absolute path based on the script location to avoid CWD issues
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, "backend", "assets", "templates", "book_sample", "v1", "pages", "p001")
    
    print(f"Looking for assets in: {base_dir}")
    if not os.path.exists(base_dir):
        print(f"Error: Directory {base_dir} does not exist.")
        return

    child_path = os.path.join(base_dir, "ref_child.png")
    mom_path = os.path.join(base_dir, "ref_mom.png")

    slots = []
    
    # Process Child
    child_slot = get_bbox_from_image(child_path, "child")
    if child_slot:
        slots.append(child_slot)

    # Process Mom
    mom_slot = get_bbox_from_image(mom_path, "mom")
    if mom_slot:
        slots.append(mom_slot)
        
    # Create slot.json
    output_data = {
        "page_id": "p001",
        "canvas": {
            "width_px": 2048, # Default, will verify
            "height_px": 1536 
        },
        "slots": slots
    }
    
    # Verify canvas size from BG
    bg_path = os.path.join(base_dir, "bg.png")
    if os.path.exists(bg_path):
        bg = Image.open(bg_path)
        output_data["canvas"]["width_px"] = bg.width
        output_data["canvas"]["height_px"] = bg.height

    output_path = os.path.join(base_dir, "slot.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Generated {output_path}")
    print(json.dumps(output_data, indent=2))

if __name__ == "__main__":
    main()
