import os
import sys
import json
from dotenv import load_dotenv

# Run from backend directory (current dir)
sys.path.append(os.getcwd())

# Load env variables FIRST (before importing app which loads config)
# Try loading from current and parent
load_dotenv(".env")
load_dotenv("../.env")

from app.services.generator_service import GeneratorService
from app.services.compositor.engine import CompositorEngine


def verify_gemini_generation():
    print("🚀 Starting Gemini Verification...")
    
    # Assets are in "assets" relative to backend root
    assets_root = os.path.join(os.getcwd(), "assets")
    generator = GeneratorService(assets_root=assets_root)
    engine = CompositorEngine(assets_root=assets_root)
    
    # Setup test data
    order_id = "test_order_gemini"
    book_id = "magic_of_money"
    page_id = "p001"
    
    # Use existing reference mom as the "Identity Source" (User Photo)
    # This ensures we have a valid face input
    src_img_path = os.path.join(assets_root, "templates", "magic_of_money", "v1", "pages", "p001", "ref_mom.png")
    
    # 1. Simulate Identity Extraction (Mocking the file placement)
    order_dir = os.path.join(assets_root, "orders", order_id)
    os.makedirs(order_dir, exist_ok=True)
    
    # Copy source image as "input.jpg"
    import shutil
    input_photo_path = os.path.join(order_dir, "input.jpg")
    shutil.copy(src_img_path, input_photo_path)
    
    # Create dummy identity.json if needed by Generator
    # The generator usually creates this analysis. Let's see if we can trigger it or need to mock it.
    # GeneratorService.process_identity does the analysis.
    
    # Mock Identity Data
    identity_data = {
        "attributes": {
            "age_group": "child", 
            "gender": "female", 
            "skin_tone_hex": "#f5d0bd"
        },
        "original_image_path": input_photo_path
    }

    # 2. Generate Page
    print("\n2. Generating Page (Gemini)...")
    try:
        # Load Template Data
        template_dir = os.path.join(assets_root, "templates", book_id, "v1", "pages", page_id)
        with open(os.path.join(template_dir, "slot.json"), "r") as f:
            slot_data = json.load(f)
            
        # We need to generate for each slot
        character_map = {}
        for slot in slot_data.get("slots", []):
            role = slot["role"]
            print(f"   Generating Character for Role: {role}...")
            
            tmpl_data = {
                "dir": template_dir
            }
            
            # Call Generator
            # generate_character(order_id, identity_data, template_data, slot_role, original_photo_path)
            # We explicitly pass input_photo_path again to be safe
            char_path = generator.generate_character(
                order_id=order_id,
                identity_data=identity_data,
                template_data=tmpl_data,
                slot_role=role,
                original_photo_path=input_photo_path
            )
            
            if char_path:
                print(f"   ✅ Generated {role}: {char_path}")
                character_map[role] = char_path
            else:
                print(f"   ❌ Failed to generate {role}")

        # 3. Composite
        print("\n3. Compositing Page...")
        if character_map:
            result_path = engine.composite_page(book_id, page_id, character_map, version="v1")
            print(f"\n✨ FINAL RESULT: {result_path}")
        else:
            print("❌ checks failed, no characters to composite.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    verify_gemini_generation()
