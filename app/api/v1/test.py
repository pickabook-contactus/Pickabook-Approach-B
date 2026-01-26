"""
Test Endpoint for Cheap Iteration
Allows generating just 1-2 pages instead of full book.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import os
import uuid
import shutil

from app.services import generator_service
from app.services.ai import replicate as replicate_service
from app.services.compositor import engine as compositor_engine
from app.core.config import settings

router = APIRouter()

@router.post("/generate-pages")
async def test_generate_pages(
    mom_image: UploadFile = File(..., description="Mom's identity photo"),
    child_image: UploadFile = File(..., description="Child's identity photo"),
    page_ids: str = Form("p001", description="Comma-separated page IDs, e.g., 'p001,p002'"),
    template_id: str = Form("magic_of_money", description="Template ID"),
    template_version: str = Form("v1", description="Template version")
):
    """
    Test endpoint for cheap iteration.
    Generates only the specified pages instead of full book.
    
    Example: page_ids="p001" will generate only page 1 (2 API calls for Mom + Child).
    """
    try:
        # Parse page IDs
        pages = [p.strip() for p in page_ids.split(",") if p.strip()]
        if not pages:
            raise HTTPException(status_code=400, detail="No page IDs provided")
        
        # Create temp order ID for this test
        test_order_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Setup temp directories
        # Use getattr to avoid AttributeError if ASSETS_ROOT is missing from settings class
        assets_root = getattr(settings, "ASSETS_ROOT", None) or os.path.join(os.getcwd(), "assets")
        order_dir = os.path.join(assets_root, "orders", test_order_id)
        identity_dir = os.path.join(order_dir, "identity")
        os.makedirs(identity_dir, exist_ok=True)
        
        # Save uploaded images
        mom_path = os.path.join(identity_dir, "mom.png")
        child_path = os.path.join(identity_dir, "child.png")
        
        with open(mom_path, "wb") as f:
            shutil.copyfileobj(mom_image.file, f)
        with open(child_path, "wb") as f:
            shutil.copyfileobj(child_image.file, f)
        
        # Build identity data structure (minimal)
        identity_data = {
            "mom": {
                "image_path": mom_path,
                "attributes": {"age_group": "adult", "gender_detected": 0, "hair_color_hex": "brown", "hair_texture": "straight"}
            },
            "child": {
                "image_path": child_path,
                "attributes": {"age_group": "child", "gender_detected": 0, "hair_color_hex": "brown", "hair_texture": "curly"}
            }
        }
        
        
        # Initialize services
        gen_service = generator_service.GeneratorService(assets_root=assets_root)
        comp_engine = compositor_engine.CompositorEngine(assets_root=assets_root)
        
        results = []
        
        # Process each requested page
        for page_id in pages:
            template_dir = os.path.join(
                assets_root, "templates", template_id, template_version, "pages", page_id
            )
            
            if not os.path.exists(template_dir):
                results.append({"page_id": page_id, "error": f"Template page not found: {template_dir}"})
                continue
            
            # Load slot.json
            slot_json_path = os.path.join(template_dir, "slot.json")
            if not os.path.exists(slot_json_path):
                results.append({"page_id": page_id, "error": "slot.json not found"})
                continue
                
            import json
            with open(slot_json_path, "r") as f:
                slot_data = json.load(f)
            
            page_results = {"page_id": page_id, "characters": [], "composite_url": None}
            character_map = {} # For compositor
            
            # Process each slot (mom, child)
            for slot in slot_data.get("slots", []):
                slot_role = slot.get("role")
                if slot_role not in identity_data:
                    continue
                
                try:
                    # Call the same generator logic
                    result = gen_service.generate_character(
                        order_id=test_order_id,
                        template_data={"dir": template_dir, "bbox": slot.get("bbox_px")},
                        slot_role=slot_role,
                        identity_data=identity_data[slot_role],
                        original_photo_path=identity_data[slot_role]["image_path"] # Pass explicitly
                    )
                    page_results["characters"].append({
                        "role": slot_role,
                        "generated_path": result
                    })
                    if result:
                         character_map[slot_role] = result
                         
                except Exception as e:
                    page_results["characters"].append({
                        "role": slot_role,
                        "error": str(e)
                    })
            
            # Composite Page if we have characters
            if character_map:
                try:
                    print(f"Compositing Page {page_id} with map: {character_map}")
                    composite_path = comp_engine.composite_page(
                        book_id=template_id,
                        page_id=page_id,
                        character_map=character_map,
                        version=template_version
                    )
                    if composite_path:
                        # Convert absolute file path to URL accessible via /uploads or static
                        # Assuming composite output is in assets/orders/debug_renders
                        # We need to expose it.
                        # Hack: Copy to uploads/ for public access
                        uploads_dir = os.path.join(os.getcwd(), "uploads")
                        os.makedirs(uploads_dir, exist_ok=True)
                        filename = os.path.basename(composite_path)
                        public_path = os.path.join(uploads_dir, filename)
                        shutil.copy2(composite_path, public_path)
                        
                        # Return full URL
                        # Use settings.BASE_URL if available
                        base_url = settings.BASE_URL
                        page_results["composite_url"] = f"{base_url}/uploads/{filename}"
                except Exception as e:
                    page_results["composite_error"] = str(e)
            
            results.append(page_results)
        
        return {
            "test_order_id": test_order_id,
            "pages_generated": len(pages),
            "api_calls": len(pages) * 2,  # 2 chars per page
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
