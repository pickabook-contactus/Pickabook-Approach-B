import os
import shutil
from typing import Optional, Dict
from app.services.ai import replicate as replicate_service
from app.core.config import settings
from app.utils.image_processing import process_character_output
from app.services.storage.supabase_service import SupabaseService
import json

class GeneratorService:
    # PROMPTS
    MASTER_CHARACTER_PROMPT = (
        "Use Image 1 as the identity reference (real person).\n"
        "Use Image 2 as the style and body reference.\n\n"
        "TASK:\n"
        "Create a high-quality soft 3D storybook cartoon illustration.\n"
        "The character must have the exact body pose, clothes, and proportions of Image 2.\n"
        "The character must have the facial identity (hair, skin, features) of Image 1, adapted to the cartoon style of Image 2.\n\n"
        "STYLE RULES:\n"
        "- Soft 3D Storybook Cartoon.\n"
        "- Rounded facial features, gentle gradients, warm pastel tones.\n"
        "- No photorealism, but utilize soft 3D shading.\n"
        "- Child-friendly, expressive, joyful.\n\n"
        "NEGATIVE PROMPT (FORBIDDEN):\n"
        "- Two people, multiple characters, twin sisters, clone.\n"
        "- Collage, split screen, before and after, comparison.\n"
        "- Photorealistic clothes, texture artifacts.\n\n"
        "CRITICAL:\n"
        "- Identity must match Image 1 (Face, Hair, Skin).\n"
        "- CLOTHING must match Image 2 (Structure). Do NOT use clothing from Image 1.\n"
        "- Pose and Body must match Image 2 exactly.\n"
        "- Output a SINGLE character on a white background."
    )


    
    PAGE_CHARACTER_PROMPT = (
        "ROLE: Expert Digital Compositor.\n\n"
        "INPUTS:\n"
        "- Image 1: IDENTITY Source (Face, Hair, Skin Tone).\n"
        "- Image 2: STRUCTURE Source (Pose, Clothing, Style, Lighting).\n\n"
        "OBJECTIVE:\n"
        "Generate a single character that perfectly combines the STRUCTURE of Image 2 with the IDENTITY of Image 1.\n\n"
        "INSTRUCTIONS:\n"
        "1.  **Analyze Image 2 (The Target):**\n"
        "    - Lock onto the character's exact pose, hand position, and head tilt.\n"
        "    - Lock onto the exact clothing design, folds, and textures.\n"
        "    - Lock onto the artistic rendering style (shading, outline, color palette).\n"
        "    - **CRITICAL:** The output MUST look like it belongs in the same visual world as Image 2.\n\n"
        "2.  **Inject Image 1 (The Identity):**\n"
        "    - Replace *only* the facial features, Skin colour, and hair with those from Image 1.\n"
        "    - Keep the expression consistent with the mood of Image 2 (e.g., if Image 2 is smiling, the output must smile).\n\n"
        "3.  **Final Checks:**\n"
        "    - **orientation:** Match the Left/Right facing direction of Image 2. DO NOT MIRROR.\n"
        "    - **Background:** Pure White.\n\n"
        "NEGATIVE PROMPT:\n"
        "- Changing the clothes.\n"
        "- Changing the pose.\n"
        "- Changing the art style to look like Image 1.\n"
        "- Distorted hands, extra limbs."
    )


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
        raw_prompt = prompts.get("master_character_prompt", self.MASTER_CHARACTER_PROMPT)
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
        raw_prompt = prompts.get("page_character_prompt", self.PAGE_CHARACTER_PROMPT)
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
