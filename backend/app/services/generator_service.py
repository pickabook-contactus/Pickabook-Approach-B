import os
import shutil
import requests
from typing import Optional, Dict
from app.services.ai import replicate as replicate_service
from app.core.config import settings


class GeneratorService:
    """
    Two-Phase Character Generation Service
    
    Phase 1: generate_master_character()
        - Creates a canonical cartoon version of the user
        - Uses: User Photo + Master Reference Image
        - Output: Master Character (reused for all pages)
    
    Phase 2: generate_page_character()
        - Creates page-specific poses from the Master
        - Uses: Master Character + Page Reference Image
        - Output: Character in specific pose for that page
    """
    
    def __init__(self, assets_root: str):
        self.assets_root = assets_root
    
    # ============================================================
    # PROMPTS
    # ============================================================
    
    MASTER_CHARACTER_PROMPT = """Use Image 1 as the identity reference (real child).
Use Image 2 as the pose, action, and illustration style reference.

Create a full-body cartoon illustration where:
- The pose, hand position, body posture, stance, and direction exactly match Image 2
- Camera angle, framing, and proportions exactly match Image 2
- Illustration style exactly matches Image 2 (soft, child-friendly, storybook cartoon)

Replace the cartoon character's identity with the child from Image 1 by accurately transferring:
- Face shape and facial proportions
- Eye shape, size, and spacing
- Nose shape
- Smile and mouth shape
- Skin tone
- Hair texture, hair volume, and hairstyle adapted into the same cartoon style

The final character must clearly resemble the child from Image 1, while being fully illustrated in the cartoon style of Image 2.

Do NOT change:
- Pose
- Body proportions
- Camera angle
- Illustration style
- clothes

Cartoon illustration only.
No realism, no photorealistic textures.
High-quality children's storybook illustration.
Warm, joyful, expressive, age-appropriate.
background should be Preferably Transparent or Plain white.

Important:
Identity must match Image 1.
Pose and style must match Image 2.
Do not invent a new face.
Do not alter the pose.
Do not mix realism with cartoon.
soft 3D storybook cartoon, rounded facial features, gentle gradients, warm pastel tones
The Output Image will be the MASTER cartoon version of this person, Output must be perfect for reuse."""

    PAGE_CHARACTER_PROMPT = """You are a professional storyboard artist.

INPUTS:
- Image 1: Master Character (Source for IDENTITY ONLY).
- Image 2: Scene Template (Source for EVERYTHING ELSE).

TASK:
Recreate Image 2 exactly, but replace the character's identity with the character from Image 1.

INSTRUCTIONS:
1. BASE IMAGE (From Image 2):
   - Start with Image 2 as your canvas.
   - Copy the exact body pose, hand gestures, and head angle from Image 2.
   - Copy the exact clothing, lighting, and background from Image 2.
   - Copy the exact eye direction and gaze from Image 2.

2. IDENTITY SWAP (From Image 1):
   - On top of the posed body from Image 2, draw the face and hair from Image 1.
   - You MUST use the exact face shape, eyes, nose, and mouth design from Image 1.
   - You MUST use the exact hair style, color, and texture from Image 1.
   - You MUST use the exact skin tone from Image 1.

STYLE RULES:
- The final image must look like a seamless cartoon illustration.
- The identity from Image 1 must be perfectly preserved.

CRITICAL:
- Do not change the pose or gaze from Image 2.
- Do not change the identity features from Image 1.
- Simple, clean execution.
- White Background"""

    # ============================================================
    # PHASE 1: MASTER CHARACTER GENERATION
    # ============================================================
    
    def generate_master_character(self, 
                                   order_id: str, 
                                   user_photo_path: str,
                                   master_ref_path: str,
                                   role: str = "child") -> str:
        """
        PHASE 1: Creates the Master Character (canonical cartoon version).
        
        Args:
            order_id: The order ID
            user_photo_path: Path to user's original photo (Image 1)
            master_ref_path: Path to master reference image (Image 2)
            role: 'child' or 'mom'
            
        Returns:
            Path to the generated Master Character image
        """
        print(f"\n{'='*60}")
        print(f"PHASE 1: GENERATING MASTER CHARACTER ({role})")
        print(f"{'='*60}")
        
        # Validate inputs
        if not user_photo_path or not os.path.exists(user_photo_path):
            raise FileNotFoundError(f"User photo not found: {user_photo_path}")
        
        if not master_ref_path or not os.path.exists(master_ref_path):
            raise FileNotFoundError(f"Master reference not found: {master_ref_path}")
        
        print(f"Image 1 (Identity): {user_photo_path}")
        print(f"Image 2 (Master Ref): {master_ref_path}")
        print(f"Prompt: MASTER_CHARACTER_PROMPT")
        
        try:
            # Call AI
            generated_url = replicate_service.generate_character_variant(
                reference_image_path=os.path.abspath(master_ref_path),
                identity_image_path=os.path.abspath(user_photo_path),
                prompt=self.MASTER_CHARACTER_PROMPT
            )
            
            if not generated_url:
                raise Exception("AI Generation returned None")
            
            # Save Master Character
            output_dir = os.path.join(self.assets_root, "orders", order_id, "master")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save raw output
            raw_filename = f"master_raw_{role}.png"
            raw_output_path = os.path.join(output_dir, raw_filename)
            
            resp = requests.get(generated_url)
            resp.raise_for_status()
            
            with open(raw_output_path, "wb") as f:
                f.write(resp.content)
            
            print(f"Raw Master Saved: {raw_output_path}")
            
            # Remove background
            from rembg import remove
            
            print("Removing background from Master Character...")
            with open(raw_output_path, "rb") as f:
                raw_data = f.read()
            
            clean_data = remove(raw_data)
            
            # Save final Master
            final_filename = f"master_{role}.png"
            final_output_path = os.path.join(output_dir, final_filename)
            
            with open(final_output_path, "wb") as f:
                f.write(clean_data)
            
            print(f"✅ MASTER CHARACTER SAVED: {final_output_path}")
            print(f"{'='*60}\n")
            return final_output_path
            
        except Exception as e:
            print(f"❌ Master Generation Error: {e}")
            raise

    # ============================================================
    # PHASE 2: PAGE CHARACTER GENERATION
    # ============================================================
    
    def generate_page_character(self,
                                 order_id: str,
                                 master_path: str,
                                 page_ref_path: str,
                                 page_id: str,
                                 role: str = "child") -> str:
        """
        PHASE 2: Creates a page-specific character from the Master.
        
        Args:
            order_id: The order ID
            master_path: Path to Master Character image (Image 1)
            page_ref_path: Path to page reference image (Image 2)
            page_id: Page identifier (e.g., 'p001')
            role: 'child' or 'mom'
            
        Returns:
            Path to the generated page character image
        """
        print(f"\n{'-'*60}")
        print(f"PHASE 2: GENERATING PAGE CHARACTER ({role} for {page_id})")
        print(f"{'-'*60}")
        
        # Validate inputs
        if not master_path or not os.path.exists(master_path):
            raise FileNotFoundError(f"Master character not found: {master_path}")
        
        if not page_ref_path or not os.path.exists(page_ref_path):
            raise FileNotFoundError(f"Page reference not found: {page_ref_path}")
        
        print(f"Image 1 (Master): {master_path}")
        print(f"Image 2 (Page Ref): {page_ref_path}")
        print(f"Prompt: PAGE_CHARACTER_PROMPT")
        
        try:
            # Call AI
            generated_url = replicate_service.generate_character_variant(
                reference_image_path=os.path.abspath(page_ref_path),
                identity_image_path=os.path.abspath(master_path),
                prompt=self.PAGE_CHARACTER_PROMPT
            )
            
            if not generated_url:
                raise Exception("AI Generation returned None")
            
            # Save Page Character
            output_dir = os.path.join(self.assets_root, "orders", order_id, "generated")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save raw output
            raw_filename = f"gen_raw_{role}_{page_id}.png"
            raw_output_path = os.path.join(output_dir, raw_filename)
            
            resp = requests.get(generated_url)
            resp.raise_for_status()
            
            with open(raw_output_path, "wb") as f:
                f.write(resp.content)
            
            print(f"Raw Page Character Saved: {raw_output_path}")
            
            # Remove background
            from rembg import remove
            
            print("Removing background...")
            with open(raw_output_path, "rb") as f:
                raw_data = f.read()
            
            clean_data = remove(raw_data)
            
            # Save final
            final_filename = f"gen_{role}_{page_id}.png"
            final_output_path = os.path.join(output_dir, final_filename)
            
            with open(final_output_path, "wb") as f:
                f.write(clean_data)
            
            print(f"✅ Page Character Saved: {final_output_path}")
            print(f"{'-'*60}\n")
            return final_output_path
            
        except Exception as e:
            print(f"❌ Page Generation Error: {e}")
            # Fallback: use master as-is
            fallback_path = os.path.join(self.assets_root, "orders", order_id, "generated", f"fallback_{role}_{page_id}.png")
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            shutil.copy2(master_path, fallback_path)
            print(f"FALLBACK: Used master character: {fallback_path}")
            return fallback_path

    # ============================================================
    # LEGACY METHOD (for backward compatibility)
    # ============================================================
    
    def generate_character(self, 
                           order_id: str, 
                           identity_data: Dict, 
                           template_data: Dict, 
                           slot_role: str,
                           original_photo_path: str) -> str:
        """
        LEGACY: Single-phase generation (kept for backward compatibility).
        Consider using generate_master_character + generate_page_character instead.
        """
        print("⚠️ Using legacy single-phase generation")
        
        # Validate
        if not original_photo_path or not os.path.exists(original_photo_path):
            raise FileNotFoundError(f"Original photo not found: {original_photo_path}")
        
        template_dir = template_data["dir"]
        ref_image_path = os.path.join(template_dir, f"ref_{slot_role}.png")
        
        if not os.path.exists(ref_image_path):
            print(f"Warning: Reference image not found.")
            return None
        
        # Use the master prompt for single-phase
        try:
            generated_url = replicate_service.generate_character_variant(
                reference_image_path=os.path.abspath(ref_image_path),
                identity_image_path=os.path.abspath(original_photo_path),
                prompt=self.MASTER_CHARACTER_PROMPT
            )
            
            if not generated_url:
                raise Exception("AI Generation returned None")
            
            # Save
            output_dir = os.path.join(self.assets_root, "orders", order_id, "generated")
            os.makedirs(output_dir, exist_ok=True)
            
            raw_output_path = os.path.join(output_dir, f"gen_raw_{slot_role}.png")
            
            resp = requests.get(generated_url)
            resp.raise_for_status()
            
            with open(raw_output_path, "wb") as f:
                f.write(resp.content)
            
            # Remove background
            from rembg import remove
            
            with open(raw_output_path, "rb") as f:
                raw_data = f.read()
            
            clean_data = remove(raw_data)
            
            final_output_path = os.path.join(output_dir, f"gen_{slot_role}.png")
            
            with open(final_output_path, "wb") as f:
                f.write(clean_data)
            
            return final_output_path
            
        except Exception as e:
            print(f"Generator Error: {e}")
            fallback_path = os.path.join(self.assets_root, "orders", order_id, "generated", f"fallback_{slot_role}.png")
            os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
            shutil.copy2(ref_image_path, fallback_path)
            return fallback_path


if __name__ == "__main__":
    pass
