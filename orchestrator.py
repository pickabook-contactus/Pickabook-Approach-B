import os
import sys
import json
# Add backend to path so imports work
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.identity_service import IdentityService
from app.services.generator_service import GeneratorService
from app.services.compositor.engine import CompositorEngine

def main():
    print("=== Starting Approach B Full Pipeline Test ===")
    
    # Config
    assets_root = os.path.join(os.getcwd(), "backend", "assets")
    order_id = "ORD_FULL_TEST_001"
    book_id = "book_sample"
    page_id = "p001"
    
    # Inputs
    # Use the real test photo (copied from artifacts)
    user_photo_path = os.path.abspath("test_input.jpg")
    
    # Initialize Services
    id_service = IdentityService(assets_root)
    gen_service = GeneratorService(assets_root)
    comp_service = CompositorEngine(assets_root)
    
    try:
        # 1. Identity Phase (Multi-Face)
        print("\n--- PHASE 1: Identity ---")
        
        # Heuristic: Assuming Index 0 (Largest) is Mom, Index 1 (Second) is Child
        # Note: If image has only 1 face, this will fail on index 1.
        # But user said image has 2 people.
        
        print("Extracting MOM Identity (Index 0)...")
        identity_mom = id_service.create_identity(order_id, user_photo_path, role="mom", face_index=0)
        
        print("Extracting CHILD Identity (Index 1)...")
        identity_child = id_service.create_identity(order_id, user_photo_path, role="child", face_index=1)
        
        print("Identities Created.")

        # 2. Generation Phase
        print("\n--- PHASE 2: Generation ---")
        # Load template data to get reference images
        template = comp_service.load_template(book_id, page_id)
        
        # Generate Child
        child_gen_path = gen_service.generate_character(
            order_id=order_id,
            identity_data=identity_child,
            template_data=template,
            slot_role="child"
        )
        
        # Generate Mom
        mom_gen_path = gen_service.generate_character(
            order_id=order_id,
            identity_data=identity_mom,
            template_data=template,
            slot_role="mom"
        )
        
        # 3. Composition Phase
        print("\n--- PHASE 3: Composition ---")
        character_map = {
            "child": child_gen_path,
            "mom": mom_gen_path
        }
        
        final_page_path = comp_service.composite_page(book_id, page_id, character_map)
        
        print("\n=== SUCCESS ===")
        print(f"Final Page Output: {final_page_path}")
        
    except Exception as e:
        print(f"\n!!! FAILURE !!!")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
