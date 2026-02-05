import os
import shutil
from typing import Optional, Dict
from app.services.ai import replicate as replicate_service
from app.core.config import settings
from app.utils.image_processing import process_character_output
from app.services.storage.supabase_service import SupabaseService
import json

class GeneratorService:


    def __init__(self, assets_root: str):
        self.assets_root = assets_root
        self.supabase = SupabaseService()

    def _load_book_prompts(self, book_id: str):
        try:
            prompt_path = os.path.join(self.assets_root, "templates", book_id, "v1", "prompts.json")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r") as f:
                    data = json.load(f)
                    print(f"Loaded dynamic prompts from {book_id}")
                    return data
        except Exception as e:
            print(f"Failed to load prompts for {book_id}: {e}")
        return {}


    def generate_master_character(self, 
                               order_id: str, 
                               user_photo_path: str,
                               master_ref_path: str = None,
                               role: str = "child",
                               attributes: Dict = None,
                               book_id: str = "book_sample") -> str:
        """
        Phase 1: Generate a Canonical 'Master' Character from user photo.
        Returns path to the generated master image.
        """
        print(f"[Phase 1] Generating Master Character for {role}...")
        
        # 1. Setup paths
        output_dir = os.path.join(self.assets_root, "orders", order_id, "master")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"master_{role}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Check cache
        # Force Overwrite: Delete existing file to ensure new prompt is used
        if os.path.exists(output_path):
             os.remove(output_path)
             print(f"Removed cached file: {output_path}")

        # 2. Prepare Inputs
        attrs = attributes or {}
        skin_tone = attrs.get("skin_tone_hex", "fair")
        
        # Dynamic Prompt Load
        prompts = self._load_book_prompts(book_id)
        raw_prompt = prompts.get("master_character_prompt")
        if not raw_prompt:
             raise ValueError(f"CRITICAL: Missing 'master_character_prompt' for book {book_id}. Check assets/templates/{book_id}/v1/prompts.json")
             
        prompt = raw_prompt.format(role=role, skin_tone=skin_tone)
        
        # If no master ref provided, use a generic one or the user photo itself as ref (Identity+Ref = same)
        # Ideally we have a 'neutral pose' ref.
        # Fallback: Use the user photo as both if master_ref missing, but that's weak for style structure.
        # Better: user_photo is Identity. Ref can be None (if model supports it) or a generic 'standing' pose.
        # Replicate service 'generate_character_variant' typically takes REF + ID.
        # If master_ref_path is None, we might fail or need a fallback.
        
        ref_path_to_use = master_ref_path if master_ref_path else user_photo_path
        
        try:
            generated_url = replicate_service.generate_character_variant(
                reference_image_path=ref_path_to_use, 
                identity_image_path=user_photo_path,
                prompt=prompt,
                style_strength=0.9 # High fidelity to master style/pose? or loosen for Identity?
            )
            
            if not generated_url:
                raise Exception("Master generation returned None")
                
            # Download
            import requests
            resp = requests.get(generated_url)
            resp.raise_for_status()
            
            # Post-Process: Rembg + Auto-Crop (Fixes Side-by-Side hallucinations)
            processed_data = process_character_output(resp.content)
            
            with open(output_path, "wb") as f:
                f.write(processed_data)
            
            print(f"Master Character Saved: {output_path}")
            
            # Supabase Upload
            if self.supabase:
                public_url = self.supabase.upload_file(output_path, f"orders/{order_id}/master/{os.path.basename(output_path)}")
                print(f"Master Uploaded: {public_url}")
                
            return output_path
            
        except Exception as e:
            print(f"Master Generation Failed: {e}")
            # Fallback: Just return user photo (converted to png if needed)
            # This allows pipeline to continue even if Phase 1 fails (degrading to Simple Mode effectively)
            return user_photo_path

    def generate_page_character(self,
                             order_id: str,
                             master_path: str,
                             page_ref_path: str,
                             page_id: str,

                             role: str = "child",
                             book_id: str = "book_sample") -> str:
        """
        Phase 2: Generate Page Specific Character using Master as Identity.
        """
        print(f"[Phase 2] Generating Page Character for {page_id} ({role})...")
        
        output_dir = os.path.join(self.assets_root, "orders", order_id, "generated")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"gen_{role}_{page_id}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Force Overwrite: Delete existing file to ensure new prompt is used
        if os.path.exists(output_path):
             os.remove(output_path)
             print(f"Removed cached file: {output_path}")
             
        # Prompt
        prompts = self._load_book_prompts(book_id)
        raw_prompt = prompts.get("page_character_prompt")
        if not raw_prompt:
             raise ValueError(f"CRITICAL: Missing 'page_character_prompt' for book {book_id}. Check assets/templates/{book_id}/v1/prompts.json")

        prompt = raw_prompt.format(role=role)
        
        print(f"[Phase 2] Page Gen Prompt Constructed.")
        print(f"[Phase 2] Inputs: Identity={master_path}, Ref={page_ref_path}")
        
        try:
            # Identity = Master Character
            # Reference = Page Template (Pose)
            generated_url = replicate_service.generate_character_variant(
                reference_image_path=page_ref_path, 
                identity_image_path=master_path,
                prompt=prompt,
                style_strength=0.95 # STRICT adherence to Page Pose
            )
            
            if not generated_url:
                 raise Exception("Page generation returned None")

            import requests
            resp = requests.get(generated_url)
            resp.raise_for_status()
            
            # Post-Process: Rembg + Auto-Crop
            processed_data = process_character_output(resp.content)
            
            with open(output_path, "wb") as f:
                f.write(processed_data)
            
            # Supabase Upload
            if self.supabase:
                public_url = self.supabase.upload_file(output_path, f"orders/{order_id}/assets/gen_{role}_{page_id}.png")
                print(f"Page Asset Uploaded: {public_url}")

            return output_path

        except Exception as e:
            print(f"Page Generation Failed [{page_id}]: {e}")
            # Fallback: Return Master (Better than nothing) or None?
            # Or return the original 'Simple Mode' fallback via direct composition?
            # Let's return None to signal failure, so engine can fallback to 'Simple Mode' (User Photo)
            return None
