from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
import os
import uuid

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "pong", "environment": os.getenv("ENVIRONMENT", "dev")}

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        # Simple query to check DB connection
        db.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/redis-check")
def redis_check():
    try:
        from app.core.celery_app import celery_app
        # Inspect active workers
        i = celery_app.control.inspect()
        active = i.active()
        return {"status": "ok", "redis": "connected", "workers": active}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/generate_page")
def generate_page(
    book_id: str = Form("magic_of_money"),
    page_id: str = Form("p001"),
    child_image: UploadFile = File(None),
    mom_image: UploadFile = File(None),
    use_ai_pipeline: bool = Form(True)
):
    """
    CHEAP ITERATION (PRODUCTION MIRROR):
    - Uses server-side 'ref_master_child.png' automatically.
    - Default `use_ai_pipeline=True` (Full Two-Phase AI).
    - To use Simple Mode (Cut/Paste), set `use_ai_pipeline=False`.
    """
    try:
        from app.services.compositor.engine import CompositorEngine
        from app.services.generator_service import GeneratorService
        import os
        import shutil
        import tempfile
        
        # Resolve Assets Path
        base_dir = os.getcwd() 
        assets_root = os.path.join(base_dir, "assets")
        if not os.path.exists(assets_root):
             assets_root = os.path.join(os.path.dirname(base_dir), "assets")
        if not os.path.exists(assets_root):
             assets_root = "/app/backend/assets"
             if not os.path.exists(assets_root):
                return {"error": "Assets directory not found", "cwd": base_dir}

        comp_service = CompositorEngine(assets_root)
        gen_service = GeneratorService(assets_root)
        
        # Prepare Map
        character_map = {}
        
        def save_upload_to_temp(upload_file : UploadFile, remove_bg=False):
            if not upload_file: return None
            t_in = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{upload_file.filename}")
            shutil.copyfileobj(upload_file.file, t_in)
            t_in.close()
            final_path = t_in.name

            if remove_bg:
                try:
                    from rembg import remove
                    with open(t_in.name, 'rb') as f:
                        input_data = f.read()
                    output_data = remove(input_data)
                    t_out = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    t_out.write(output_data)
                    t_out.close()
                    try: os.unlink(t_in.name)
                    except: pass
                    final_path = t_out.name
                except Exception as e:
                    print(f"Background Removal Failed: {e}")
            
            return final_path
            
        # Logic: If AI pipeline, keep original background (InstantID prefers it).
        # If Simple Mode, remove BG.
        should_remove_bg = not use_ai_pipeline
        
        if child_image:
            p = save_upload_to_temp(child_image, remove_bg=should_remove_bg)
            if p: character_map["child"] = p
            
        if mom_image:
            p = save_upload_to_temp(mom_image, remove_bg=should_remove_bg)
            if p: character_map["mom"] = p

        # ---------------------------------------------------------
        # AI PIPELINE LOGIC (Production Mirror)
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # AI PIPELINE LOGIC (Production Mirror)
        # ---------------------------------------------------------
        
        # Generate Unique Test ID
        test_id = str(uuid.uuid4())[:8]

        if use_ai_pipeline:
            print("Executing Two-Phase AI Pipeline (Test Mode)...")
            
            # Iterate over ALL roles (child, mom, etc.)
            for role in list(character_map.keys()):
                user_photo_path = character_map[role]
                print(f"[Phase 1] Generating Master Character for {role}...")
                
                # 1. Locate Master Ref (Robust Check)
                template_v1_dir = os.path.join(assets_root, "templates", book_id, "v1")
                
                # Try "ref_master_{role}.png"
                path_a = os.path.join(template_v1_dir, f"ref_master_{role}.png")
                # Try "master_ref_{role}.png" (Legacy/Duplicate)
                path_b = os.path.join(template_v1_dir, f"master_ref_{role}.png")
                
                master_ref_path = None
                if os.path.exists(path_a):
                     master_ref_path = path_a
                elif os.path.exists(path_b):
                     master_ref_path = path_b
                
                if not master_ref_path:
                    print(f"Warning: Master Ref not found for {role} (Checked {path_a} and {path_b})")
                
                # 2. Generate Master
                master_path = gen_service.generate_master_character(
                    order_id=f"test_{book_id}_{test_id}", 
                    user_photo_path=user_photo_path,
                    master_ref_path=master_ref_path, 
                    role=role
                )
                
                if master_path:
                    print(f"Master Character Saved: {master_path}")
                    
                    # Phase 2: Page Generation
                    print(f"[Phase 2] Generating Page Character for {page_id} ({role})...")
                    template_dir = os.path.join(assets_root, "templates", book_id, "v1", "pages", page_id)
                    # Page Ref: ref_{role}.png
                    page_ref = os.path.join(template_dir, f"ref_{role}.png")
                    
                    gen_path = None
                    if os.path.exists(page_ref):
                        gen_path = gen_service.generate_page_character(
                             order_id=f"test_{book_id}_{test_id}",
                             master_path=master_path,
                             page_ref_path=page_ref,
                             page_id=page_id,
                             role=role
                        )
                    else:
                        print(f"Page Ref Missing: {page_ref}")

                    # UPDATE MAP
                    if gen_path:
                        character_map[role] = gen_path # Best Case: Page Gen
                    else:
                        print(f"Fallback: Using Master Character for {role} (Page Gen failed/skipped)")
                        character_map[role] = master_path # Fallback: Master
                        
                else:
                     print(f"Master Generation Failed: Master generation returned None")
                     # Map stays as User Photo (Raw)
        
        # ---------------------------------------------------------
        
        # Composite
        result_path = comp_service.composite_page(book_id, page_id, character_map)

        if not result_path:
            return {"error": "Composition returned None"}
            
        # Move to uploads
        # Filename with Random ID
        filename = f"test_{test_id}_{book_id}_{page_id}.png"
        upload_path = os.path.join(base_dir, "uploads", "pages", filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        shutil.copy2(result_path, upload_path)
        
        # URL
        from app.core.config import settings
        url = f"{settings.BASE_URL}/uploads/pages/{filename}"
        
        return {
            "status": "success",
            "mode": "AI Two-Phase" if use_ai_pipeline else "Simple Mode (rembg)",
            "url": url
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "trace": traceback.format_exc()}
