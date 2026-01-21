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
            
            # 2. Process Slots
            slots = template["slots_data"].get("slots", [])
            # Sort slots by z_index (lower index first, so higher index draws on top)
            slots.sort(key=lambda x: x.get("z_index", 0))

            for slot in slots:
                role = slot.get("role")
                if role in character_map:
                    # Load Character
                    char_path = character_map[role]
                    print(f"Compositing role '{role}' from {char_path}")
                    char_img = self._load_image(char_path)

                    # Get Slot Dimensions
                    bbox = slot["bbox_px"]
                    slot_x, slot_y = bbox["x"], bbox["y"]
                    slot_w, slot_h = bbox["w"], bbox["h"]

                    # 3. Scale Character
                    # Simple "Fit Height" logic as per spec (or fit box)
                    # For Version 1, we will fit to height, preserving aspect ratio
                    # But also ensure it doesn't exceed width
                    
                    # Calculate target size
                    scale_h = slot_h / char_img.height
                    target_w = int(char_img.width * scale_h)
                    target_h = slot_h

                    # If width exceeds slot width, scale down by width
                    if target_w > slot_w:
                         scale_w = slot_w / char_img.width
                         target_w = slot_w
                         target_h = int(char_img.height * scale_w)

                    resized_char = char_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                    # 4. Placement (Align Bottom/Feet)
                    # Center horizontally in slot (or use anchor if we had it, for now Center/Bottom)
                    # X: Center of slot
                    final_x = slot_x + (slot_w - target_w) // 2
                    
                    # Y: Bottom of slot (Feet alignment)
                    final_y = slot_y + (slot_h - target_h)

                    # Paste (Alpha Composite)
                    bg_image.alpha_composite(resized_char, (int(final_x), int(final_y)))

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
