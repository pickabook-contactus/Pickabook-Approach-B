import os
import shutil
from typing import Optional, Dict
from app.services.ai import replicate as replicate_service
from app.core.config import settings

class GeneratorService:
    def __init__(self, assets_root: str):
        self.assets_root = assets_root

    def generate_character(self, 
                           order_id: str, 
                           identity_data: Dict, 
                           template_data: Dict, 
                           slot_role: str,
                           original_photo_path: str = None) -> str:
        """
        Generates a character for a specific slot using the Identity.
        """
        print(f"Generating character for role: {slot_role}")
        
        # 1. Get Source Face (Identity)
        # Prefer the original full photo if available, as InstantID detects better on full images.
        face_source_path = None
        
        # Check explicit passed path first
        if original_photo_path and os.path.exists(original_photo_path):
             face_source_path = original_photo_path
             print(f"Using original photo for identity source: {face_source_path}")
        else:
            # Check if identity_data has original path
            orig_rel = identity_data.get("original_image_path") # Assuming IdentityService saves this?
            # If not, fall back to crop
            face_ref_rel = identity_data.get("identity_refs", {}).get("face_crop")
            if face_ref_rel:
                face_source_path = os.path.join(self.assets_root, "orders", order_id, face_ref_rel)
                print(f"Using face crop for identity source: {face_source_path}")

        if not face_source_path or not os.path.exists(face_source_path):
             # Last resort fallback if crop missing too
             raise FileNotFoundError("No valid identity source image found (neither original nor crop).")

        # 2. Get Target Control Image (Template Reference)
        template_dir = template_data["dir"]
        ref_image_name = f"ref_{slot_role}.png"
        ref_image_path = os.path.join(template_dir, ref_image_name)
        
        if not os.path.exists(ref_image_path):
            print(f"Warning: Reference image {ref_image_name} not found. Using placeholder.")
            return None

        # 3. Construct Prompt
        attrs = identity_data.get("attributes", {})
        skin_tone = attrs.get("skin_tone_hex", "skin")
        
        prompt = f"full body illustration of a {slot_role}, {skin_tone} skin tone, wearing specified clothes, consistent style"

        # 4. Call Replicate (Refine/InstantID)
        try:
             abs_ref_path = os.path.abspath(ref_image_path)
             abs_face_path = os.path.abspath(face_source_path)
             
             # Call AI
             # Use the robust path handling we know works: file://
             generated_url = replicate_service.refine_face_region(
                 crop_path=abs_ref_path, 
                 source_face_url=f"file://{abs_face_path}", 
                 prompt_suffix="children's book illustration style, soft lighting" 
             )
             
             if not generated_url:
                 raise Exception("AI Generation returned None")

             # 5. Download/Save Result
             output_dir = os.path.join(self.assets_root, "orders", order_id, "generated")
             os.makedirs(output_dir, exist_ok=True)
             
             output_filename = f"gen_{slot_role}_{os.path.basename(template_dir)}.png"
             output_path = os.path.join(output_dir, output_filename)
             
             import requests
             resp = requests.get(generated_url)
             resp.raise_for_status()
             
             with open(output_path, "wb") as f:
                 f.write(resp.content)
                 
             print(f"Generated Character Saved: {output_path}")
             return output_path

        except Exception as e:
            print(f"Generator Error: {e}")
            # Fallback for dev: Copy the reference image as if it were generated
            fallback_path = os.path.join(self.assets_root, "orders", order_id, "generated", f"fallback_{slot_role}.png")
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            shutil.copy2(ref_image_path, fallback_path)
            print(f"FALLBACK: Used reference image : {fallback_path}")
            return fallback_path

if __name__ == "__main__":
    # Test Run
    # Mock settings to avoid import error if env not set
    # But usually settings is loaded from env file
    pass
