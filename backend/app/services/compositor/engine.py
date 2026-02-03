import os
import io
import json
from typing import Dict, Any, Optional
from PIL import Image, ImageFilter, ImageDraw
import requests
import traceback

class CompositorEngine:
    def __init__(self, assets_root: str):
        self.assets_root = assets_root

    def load_template(self, book_id: str, page_id: str, version: str = "v1") -> Dict[str, Any]:
        """Loads template assets (bg, slot.json) for a given page."""
        template_dir = os.path.join(self.assets_root, "templates", book_id, version, "pages", page_id)
        
        bg_path = os.path.join(template_dir, "bg.png")
        slot_path = os.path.join(template_dir, "slot.json")
        style_path = os.path.join(template_dir, "style.json")

        if not os.path.exists(bg_path):
            raise FileNotFoundError(f"Background not found: {bg_path}")
        
        # Load Slot Data
        slots_data = {}
        if os.path.exists(slot_path):
            with open(slot_path, "r") as f:
                slots_data = json.load(f)
        
        return {
            "bg_path": bg_path,
            "slots_data": slots_data,
            "dir": template_dir
        }

    def _remove_white_bg(self, img: Image.Image, threshold: int = 240) -> Image.Image:
        """Converts white (or near-white) pixels to transparent."""
        img = img.convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            # Check if pixel is near white (R,G,B > threshold)
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                new_data.append((255, 255, 255, 0)) # Transparent
            else:
                new_data.append(item)
        img.putdata(new_data)
        return img

    def _load_image(self, path: str) -> Image.Image:
        if path.startswith("http"):
            resp = requests.get(path)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        else:
            if not os.path.exists(path):
                # Fallback for testing if file missing
                print(f"Warning: Image not found {path}, returning placeholder.")
                return Image.new("RGBA", (500, 500), (255, 0, 0, 128))
            img = Image.open(path).convert("RGBA")
        
        # Check if we should remove background (heuristic: if it looks like a reference asset or fallback)
        # For Approach B, we assume characters might need this if they aren't generated PNGs.
        # Simple check: If the corners are white, remove white bg.
        # Or just apply to all character loads? Safe enough for this specific MVP context.
        # Let's apply it if the conversion resulted in an opaque image that was originally likely JPG/PNG-no-alpha
        return self._remove_white_bg(img)

    def _trim_transparency(self, img: Image.Image, threshold: int = 50) -> Image.Image:
        """
        Trims transparent borders.
        Uses a threshold to ignore faint shadows/glows (alpha < threshold).
        Reverted to 50 (from 240) to prevent cutting off non-solid limbs.
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Create a binary mask of the alpha channel based on threshold
        alpha = img.split()[3]
        # Point transform: 0 if < threshold, 255 if >= threshold
        mask = alpha.point(lambda p: 255 if p > threshold else 0)
        
        bbox = mask.getbbox()
        if bbox:
            return img.crop(bbox)
        return img # Empty or full

    def composite_page(self, book_id: str, page_id: str, character_map: Dict[str, str], version: str = "v1") -> str:
        """
        Composites a page by placing characters into their slots.
        
        Args:
            book_id: ID of the book
            page_id: ID of the page
            character_map: Dict mapping slot_role (e.g. 'child') to character image path
            version: Template version
            
        Returns:
            Path to the generated composite image
        """
        try:
            # 1. Load Template
            template = self.load_template(book_id, page_id, version)
            bg_image = Image.open(template["bg_path"]).convert("RGBA")
            
            # DEBUG: Log received character map
            print(f"[ENGINE DEBUG] Received character_map: {character_map}")
            
            # 2. Process Slots
            slots = template["slots_data"].get("slots", [])
            # Sort slots by z_index
            slots.sort(key=lambda x: x.get("z_index", 0))

            for slot in slots:
                role = slot.get("role")
                if role in character_map:
                    # Load Character
                    char_path = character_map[role]
                    print(f"Compositing role '{role}' from {char_path}")
                    char_img = self._load_image(char_path)

                    # Get Slot Position (Moved up for scope visibility)
                    bbox = slot["bbox_px"]
                    slot_x, slot_y = bbox["x"], bbox["y"]

                    # ============================================================
                    # SLOT-BASED PLACEMENT (STRICT)
                    # ============================================================
                    # The user explicitly wants to use slot.json for location.
                    # We simply resize the generated character to the slot dimensions
                    # and place it at the slot coordinates.
                    
                    # 1. Get Target Dimensions
                    target_x, target_y = bbox["x"], bbox["y"]
                    target_w, target_h = bbox["w"], bbox["h"]
                    
                    if target_w <= 0 or target_h <= 0:
                        print(f"Warning: Invalid slot dimensions for {role}: {target_w}x{target_h}")
                        continue

                    # 2. Resize Generated Character to Fit Slot
                    # Maintain Aspect Ratio? 
                    # If we blindly resize to WxH, we might distort.
                    # Best approach for "Storybook": Resize to FIT within box, centered? 
                    # OR if the slot represents the exact character bounds, fill it.
                    # Given checking 'magic_of_money' slots are quite specific, let's try to filling it
                    # but respecting the alpha.
                    
                    # Current Strategy: Exact Resize (Match Slot)
                    # This assumes slot.json w/h matches the aspect ratio of the pose.
                    print(f"Placing {role} at ({target_x}, {target_y}) size {target_w}x{target_h}")
                    
                    resized_char = char_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    
                    # 3. Paste
                    # Use the character's own alpha channel as mask
                    bg_image.alpha_composite(resized_char, (int(target_x), int(target_y)))

            # 5. Save Output
            output_dir = os.path.join(self.assets_root, "orders", "debug_renders")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"composite_{book_id}_{page_id}.png")
            bg_image.save(output_path)
            print(f"Saved composite to {output_path}")
            return output_path

        except Exception as e:
            traceback.print_exc()
            print(f"Composition failed: {e}")
            return None

# Singleton or Service Instantiation
# For now, we can run this file directly to test if we add a main block
if __name__ == "__main__":
    # Test Run
    assets_dir = os.path.join(os.getcwd(), "backend", "assets")
    if not os.path.exists(assets_dir):
        # Fallback if running from root without backend prefix
        assets_dir = os.path.join(os.getcwd(), "assets")
        
    engine = CompositorEngine(assets_root="backend/assets") 
    
    # Path to the reference characters we just copied (renamed for clarity in test)
    # Note: In real app, these come from the Generator
    result = engine.composite_page(
        book_id="book_sample",
        page_id="p001",
        character_map={
            "child": "backend/assets/templates/book_sample/v1/pages/p001/ref_child.png",
            "mom": "backend/assets/templates/book_sample/v1/pages/p001/ref_mom.png"
        }
    )
    print(f"Test Result: {result}")
