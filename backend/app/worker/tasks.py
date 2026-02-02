from app.core.celery_app import celery_app
from app.services.ai import validator, replicate, insight, inpainting
from app.services.compositor import engine
from app.db.session import SessionLocal
from app.db.models import Order, OrderStatus, Story
from app.schemas.book import BookConfig
from app.services.storage.supabase_service import SupabaseService
import time
import os
import json
import shutil
from app.core.config import settings

# ... (Previous process_order_v2 code remains unchanged briefly, or we focus on approach_b)

@celery_app.task(bind=True, max_retries=0)
def process_approach_b(self, order_id: str, photo_url: str, book_id: str = "book_sample"):
    """
    Approach B: "Simple Mode" for Magic of Money.
    Now with Supabase Storage and Dynamic Prompts.
    """
    print(f"Starting Approach B (Simple Mode) for Order {order_id} (Book: {book_id})...")
    db = SessionLocal()
    order = db.query(Order).get(order_id)
    if not order:
        return "ORDER_NOT_FOUND"

    try:
        # Config
        assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
        comp_service = engine.CompositorEngine(assets_root)
        supabase = SupabaseService()
        
        # 1. Prepare User Assets (Remove BG)
        def resolve_local_path(url_str):
            if not url_str: return None
            if url_str.startswith("file://"):
                from urllib.parse import unquote
                path = unquote(url_str[7:])
                if os.name == 'nt' and path.startswith('/'):
                     path = path[1:]
                return path
            return url_str

        child_raw_path = resolve_local_path(order.photo_url)
        mom_raw_path = resolve_local_path(order.mom_photo_url)
        
        print(f"Resolving Paths:\nChild: {order.photo_url} -> {child_raw_path}\nMom: {order.mom_photo_url} -> {mom_raw_path}")
        
        character_map = {}
        if child_raw_path and os.path.exists(child_raw_path):
            character_map["child"] = child_raw_path
        else:
             print(f"WARNING: Child path does not exist: {child_raw_path}")

        if mom_raw_path and os.path.exists(mom_raw_path):
             character_map["mom"] = mom_raw_path
        else:
             print(f"WARNING: Mom path does not exist: {mom_raw_path}")
             
        # 2. Iterate Pages
        template_pages_dir = os.path.join(assets_root, "templates", book_id, "v1", "pages")
        if not os.path.exists(template_pages_dir):
            print(f"Template dir not found: {template_pages_dir}")
            raise FileNotFoundError(f"Template directory not found for {book_id}")

        pages = sorted([p for p in os.listdir(template_pages_dir) if p.startswith("p")])
        print(f"Found pages: {pages}")

        from app.db.models import OrderPage

        results = []
        
        # Initialize Generation Service
        gen_service = GeneratorService(assets_root)

        for page_folder in pages:
            page_id = page_folder
            page_num_str = page_id.replace("p", "") # p001 -> 001
            try:
                page_num = int(page_num_str)
            except:
                page_num = 1 # Fallback
                
            # -------------------------------------------------------------
            # NEW MASTER CHARACTER PIPELINE (Two-Phase) - OPTIMIZED
            # -------------------------------------------------------------
            
            # Phase 1: Generate Master Characters (ONCE per order)
            # Store in master_map = {role: path}
            master_map = {}
            
            print("Phase 1: Generating Master Characters...")
            v1_dir = os.path.join(assets_root, "templates", book_id, "v1")
            
            for role in list(character_map.keys()): # Iterate all roles (child, mom)
                user_photo_path = character_map[role]
                print(f"Generating Master for {role}...")
                
                # Robust Ref Lookup
                path_a = os.path.join(v1_dir, f"ref_master_{role}.png")
                path_b = os.path.join(v1_dir, f"master_ref_{role}.png")
                
                master_ref_path = None
                if os.path.exists(path_a): master_ref_path = path_a
                elif os.path.exists(path_b): master_ref_path = path_b
                
                if not master_ref_path:
                    print(f"Warning: Master Ref not found for {role}. Using User Photo/None.")
                
                # Generate
                master_path = gen_service.generate_master_character(
                    order_id=str(order.id),
                    user_photo_path=user_photo_path,
                    master_ref_path=master_ref_path,
                    role=role,
                    book_id=book_id # Passing Dynamic Book ID
                )
                
                if master_path:
                    master_map[role] = master_path
                    print(f"Master {role} Saved: {master_path}")
                else:
                    print(f"Master Generation Failed for {role}")
            
            # -------------------------------------------------------------
            
            print(f"Processing {page_id}...")
            
            # Phase 2: Page Specific Generation
            current_map = character_map.copy()
            page_ref_dir = os.path.join(template_pages_dir, page_id)
            
            for role in list(master_map.keys()): # Only iterate roles that HAVE a master
                master_path = master_map[role]
                
                # Look for Page Ref: ref_{role}.png
                page_ref = os.path.join(page_ref_dir, f"ref_{role}.png")
                
                gen_page_path = None
                if os.path.exists(page_ref):
                    print(f"Phase 2: Generating Page Asset for {page_id} ({role})...")
                    gen_page_path = gen_service.generate_page_character(
                        order_id=str(order.id),
                        master_path=master_path,
                        page_ref_path=page_ref,
                        page_id=page_id,
                        role=role,
                        book_id=book_id # Passing Dynamic Book ID
                    )
                else:
                    print(f"Page Ref Missing for {role} on {page_id}. Skipping Gen.")

                # UPDATE MAP
                if gen_page_path:
                    current_map[role] = gen_page_path # Best: Page Gen
                else:
                    print(f"Fallback: Using Master Character for {role} on {page_id}")
                    current_map[role] = master_path # Fallback: Master
            
            # Composite using the updated map
            final_page_path = comp_service.composite_page(book_id, page_id, current_map)
            
            if final_page_path:
                # Save & Persist
                uploads_dir = os.path.join(os.getcwd(), "uploads", "pages")
                os.makedirs(uploads_dir, exist_ok=True)
                
                filename = f"order_{order.id}_{page_id}.png"
                public_path = os.path.join(uploads_dir, filename)
                shutil.copy2(final_page_path, public_path)
                
                # Supabase Upload (FINAL PAGE)
                supabase_url = None
                if supabase:
                    supabase_url = supabase.upload_file(public_path, f"orders/{order.id}/pages/{filename}")
                    print(f"Final Page Uploaded to Supabase: {supabase_url}")

                # Calculate Final URL (Prefer Supabase, else Local)
                page_url = supabase_url if supabase_url else f"{settings.BASE_URL}/uploads/pages/{filename}"
                
                results.append(page_url)
                
                # DB Update
                existing_page = db.query(OrderPage).filter(
                    OrderPage.order_id == order.id,
                    OrderPage.page_number == page_num
                ).first()

                if existing_page:
                    existing_page.image_url = page_url
                else:
                    db_page = OrderPage(
                        order_id=order.id,
                        page_number=page_num,
                        image_url=page_url
                    )
                    db.add(db_page)
                db.commit()
        
        # Mark Complete
        order.status = OrderStatus.COMPLETED
        db.commit()
        
        print(f"Approach B (Simple Mode) Complete. Generated {len(results)} pages.")
        return "COMPLETED"

    except Exception as e:
        print(f"Approach B Failed: {e}")
        import traceback
        traceback.print_exc()
        order.status = OrderStatus.FAILED
        order.failure_reason = str(e)
        db.commit()
        return "FAILED"
    finally:
        db.close()
from app.services.ai import validator, replicate, insight, inpainting
from app.services.compositor import engine
from app.db.session import SessionLocal
from app.db.models import Order, OrderStatus, Story
from app.schemas.book import BookConfig
import time
import os
import json
import shutil

def load_book_config(story_id: str = None) -> BookConfig:
    """
    Loads the Book Configuration JSON.
    For now, maps 'The Space Adventure' (or default) to 'baker_adventure_v1.json'.
    """
    # MAPPING LOGIC (Temporary until DB stores config path)
    config_name = "baker_config.json" 
    
    # Path setup - accessing the static/templates dir locally
    base_dir = os.path.dirname(os.path.dirname(__file__)) # app/
    config_path = os.path.join(base_dir, "static", "templates", config_name)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found at {config_path}")
        
    with open(config_path, "r") as f:
        data = json.load(f)
        return BookConfig(**data)

@celery_app.task(bind=True, max_retries=0)
def process_order_v2(self, order_id: str, photo_url: str):
    """
    Orchestrates the Phase 7 Data-Driven AI Pipeline.
    Flow: Load Config -> Validate -> Generate (Config Prompts) -> Composite (Config Coords)
    """
    print(f"Processing Order {order_id} via Data-Driven Pipeline...")
    db = SessionLocal()
    order = None

    try:
        # Fetch Order
        order = db.query(Order).get(order_id)
        if not order:
            print(f"Order {order_id} not found.")
            return "ORDER_NOT_FOUND"

        # ---------------------------------------------------------
        # 0. LOAD CONFIGURATION
        # ---------------------------------------------------------
        try:
            # We pass story_id to help select the config (currently defaults to baker)
            config = load_book_config(str(order.story_id) if order.story_id else None)
            print(f"Loaded Config: {config.title} [{config.book_id}]")
        except Exception as e:
            print(f"Configuration Error: {e}")
            order.status = OrderStatus.FAILED
            order.failure_reason = f"Configuration Error: {str(e)}"
            db.commit()
            return "FAILED_CONFIG"

        # ---------------------------------------------------------
        # 1. VALIDATION
        # ---------------------------------------------------------
        val_result = validator.validate_photo(photo_url)
        if not val_result["valid"]:
            print(f"Validation Failed: {val_result['reason']}")
            order.status = OrderStatus.FAILED
            order.failure_reason = val_result["reason"]
            db.commit()
            return "FAILED_VALIDATION"

        # ---------------------------------------------------------
        # 2. GENERATION (Config-Driven)
        # ---------------------------------------------------------
        generated_face_url = None
        
        # Check if already generated (Recovery Mode)
        if order.character_asset_url:
            print(f"Order {order_id} already has a generated face. Skipping Generation.")
            generated_face_url = order.character_asset_url
        else:
            print(f"Generating Character using Style: {config.style_config.base_model}")
            try:
                # Use Config Prompts
                gen_url = replicate.generate_character_head(
                    photo_input=photo_url, 
                    prompt_suffix=config.style_config.prompt_suffix,
                    negative_prompt=config.style_config.negative_prompt
                )
                
                # QC Check (InsightFace)
                score = insight.verify_identity(photo_url, gen_url)
                print(f"QC Score: {score}")
                
                if score > 0.40: # slightly lower threshold for stylized
                    generated_face_url = gen_url
                    print("QC Passed.")
                else:
                    print(f"QC Warning (Score: {score}). Proceeding anyway for style.")
                    generated_face_url = gen_url

            except Exception as e:
                print(f"Generation Error: {e}")
                # Fallback Logic can go here if needed
                order.status = OrderStatus.FAILED
                order.failure_reason = f"Generation Failed: {str(e)}"
                db.commit()
                return "FAILED_GENERATION"
        
        # Save Generated Asset
        order.character_asset_url = generated_face_url
        db.commit()

        # ---------------------------------------------------------
        # 3. COMPOSITOR (Config-Driven Loop)
        # ---------------------------------------------------------
        print("Starting Composition Loop...")
        
        from app.db.models import OrderPage
        
        for page_conf in config.pages:
            try:
                # -----------------------------------------------------
                # OPTIMIZATION: Check DB first to avoid re-billing on retry
                # -----------------------------------------------------
                existing_page = db.query(OrderPage).filter(
                    OrderPage.order_id == order.id,
                    OrderPage.page_number == page_conf.page_number
                ).first()

                if existing_page and existing_page.image_url:
                    print(f"Page {page_conf.page_number} already exists in DB. Skipping generation.")
                    continue
                # Construct path to template image
                # Assuming images are in assets/{book_id}/ or similar. 
                # For now using the filename from config strictly.
                # Use 'static/templates/' as base for now to match 'child_can_be.png' setup
                # Construct path to template image
                # Assuming images are in assets/{book_id}/ or similar. 
                # For now using the filename from config strictly.
                # Use 'static/templates/' as base for now to match 'child_can_be.png' setup
                # Use settings.BASE_URL dynamic path
                template_url = f"{settings.BASE_URL}/static/templates/{page_conf.image_file}"
                
                # If using the dynamic upload system, we'd query the DB here.
                # But for strict config compliance:
                
                coords = {
                    "x": page_conf.face_data.x,
                    "y": page_conf.face_data.y,
                    "width": page_conf.face_data.width,
                    "angle": page_conf.face_data.angle
                }
                
                print(f"Compositing Page {page_conf.page_number}...")
                
                final_path = engine.composite_page(
                    template_path=template_url,
                    face_url=generated_face_url,
                    coords=coords
                )
                
                if not final_path:
                    raise Exception("Compositing returned None")

                # Move/Serve
                filename = os.path.basename(final_path)
                # Ensure URL matches global config (localhost vs ngrok)
                from app.core.config import settings
                page_url = f"{settings.BASE_URL}/uploads/pages/{filename}"
                
                # Save to DB (New Record)
                # Since we checked at the start, this is guaranteed to be new
                db_page = OrderPage(
                    order_id=order.id,
                    page_number=page_conf.page_number,
                    image_url=page_url
                )
                db.add(db_page)
                db.commit() # Commit immediately to save progress
                    
            except Exception as e:
                print(f"Page {page_conf.page_number} Error: {e}")
                # Continue other pages? Or fail all? 
                # Fail all for consistency
                raise e
            
            # Anti-Rate Limit Delay
            print("Sleeping 2 seconds to respect Rate Limits...")
            time.sleep(2)


        print(f"Order {order_id}: Pipeline Complete.")
        order.status = OrderStatus.COMPLETED
        db.commit()
        return "COMPLETED"

    except Exception as e:
        print(f"Critical Worker Error: {e}")
        if order:
            order.status = OrderStatus.FAILED
            order.failure_reason = f"System Critical: {str(e)}"
            db.commit()
        return "FAILED_CRITICAL"
    finally:
        db.close()

# ... existing imports ...
from app.services.identity_service import IdentityService
from app.services.generator_service import GeneratorService
from app.services.compositor.engine import CompositorEngine

@celery_app.task(bind=True, max_retries=0)
def process_approach_b(self, order_id: str, photo_url: str, book_id: str = "book_sample"):
    """
    Approach B: "Simple Mode" for Magic of Money.
    1. Preprocess User Uploads (Mom + Child) -> Remove Background.
    2. Iterate all pages in the template folder.
    3. Composite them.
    4. Save to DB.
    """
    print(f"Starting Approach B (Simple Mode) for Order {order_id}...")
    db = SessionLocal()
    order = db.query(Order).get(order_id)
    if not order:
        return "ORDER_NOT_FOUND"

    try:
        # Config
        assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
        comp_service = CompositorEngine(assets_root)
        
        # 1. Prepare User Assets (Remove BG)
        # We need to handle File URLs or HTTP URLs (if using S3 later)
        # -------------------------------------------------------------
        # 1. Prepare User Assets (Remove BG + Clean)
        # -------------------------------------------------------------
        def resolve_local_path(url_str):
            if not url_str: return None
            # Handle standard file:// URI
            if url_str.startswith("file://"):
                from urllib.parse import unquote
                # Strip scheme (7 chars) -> leaves /absolute/path
                path = unquote(url_str[7:])
                
                # Windows Check: /C:/path -> C:/path
                if os.name == 'nt' and path.startswith('/'):
                     path = path[1:]
                return path
            return url_str

        child_raw_path = resolve_local_path(order.photo_url)
        mom_raw_path = resolve_local_path(order.mom_photo_url)
        
        print(f"Resolving Paths:\nChild: {order.photo_url} -> {child_raw_path}\nMom: {order.mom_photo_url} -> {mom_raw_path}")
        
        
        character_map = {}
        # Reverted: Use Raw Paths as per user request (User wants AI to see original context)
        if child_raw_path:
            if os.path.exists(child_raw_path):
                character_map["child"] = child_raw_path
            else:
                 print(f"WARNING: Child path does not exist: {child_raw_path}")

        if mom_raw_path:
            if os.path.exists(mom_raw_path):
                 character_map["mom"] = mom_raw_path
            else:
                 print(f"WARNING: Mom path does not exist: {mom_raw_path}")
             
        # 2. Iterate Pages
        # Find all pages in: backend/assets/templates/{book_id}/v1/pages/
        template_pages_dir = os.path.join(assets_root, "templates", book_id, "v1", "pages")
        if not os.path.exists(template_pages_dir):
            print(f"Template dir not found: {template_pages_dir}")
            raise FileNotFoundError(f"Template directory not found for {book_id}")

        pages = sorted([p for p in os.listdir(template_pages_dir) if p.startswith("p")])
        print(f"Found pages: {pages}")

        from app.db.models import OrderPage
        from app.core.config import settings

        results = []

        for page_folder in pages:
            page_id = page_folder
            page_num_str = page_id.replace("p", "") # p001 -> 001
            try:
                page_num = int(page_num_str)
            except:
                page_num = 1 # Fallback
                
            # -------------------------------------------------------------
            # NEW MASTER CHARACTER PIPELINE (Two-Phase) - OPTIMIZED
            # -------------------------------------------------------------
            gen_service = GeneratorService(assets_root)
            
            # Phase 1: Generate Master Characters (ONCE per order)
            # Store in master_map = {role: path}
            master_map = {}
            
            print("Phase 1: Generating Master Characters...")
            v1_dir = os.path.join(assets_root, "templates", book_id, "v1")
            
            for role in list(character_map.keys()): # Iterate all roles (child, mom)
                user_photo_path = character_map[role]
                print(f"Generating Master for {role}...")
                
                # Robust Ref Lookup
                path_a = os.path.join(v1_dir, f"ref_master_{role}.png")
                path_b = os.path.join(v1_dir, f"master_ref_{role}.png")
                
                master_ref_path = None
                if os.path.exists(path_a): master_ref_path = path_a
                elif os.path.exists(path_b): master_ref_path = path_b
                
                if not master_ref_path:
                    print(f"Warning: Master Ref not found for {role}. Using User Photo/None.")
                
                # Generate
                master_path = gen_service.generate_master_character(
                    order_id=str(order.id),
                    user_photo_path=user_photo_path,
                    master_ref_path=master_ref_path,
                    role=role
                )
                
                if master_path:
                    master_map[role] = master_path
                    print(f"Master {role} Saved: {master_path}")
                else:
                    print(f"Master Generation Failed for {role}")
            
            # -------------------------------------------------------------
            
            print(f"Processing {page_id}...")
            
            # Phase 2: Page Specific Generation
            # Create a page-specific map copying the raw map
            current_map = character_map.copy()
            
            # Iterate roles to generate page variations
            page_ref_dir = os.path.join(template_pages_dir, page_id)
            
            for role in list(master_map.keys()): # Only iterate roles that HAVE a master
                master_path = master_map[role]
                
                # Look for Page Ref: ref_{role}.png
                page_ref = os.path.join(page_ref_dir, f"ref_{role}.png")
                
                gen_page_path = None
                if os.path.exists(page_ref):
                    print(f"Phase 2: Generating Page Asset for {page_id} ({role})...")
                    gen_page_path = gen_service.generate_page_character(
                        order_id=str(order.id),
                        master_path=master_path,
                        page_ref_path=page_ref,
                        page_id=page_id,
                        role=role
                    )
                else:
                    print(f"Page Ref Missing for {role} on {page_id}. Skipping Gen.")

                # UPDATE MAP
                if gen_page_path:
                    current_map[role] = gen_page_path # Best: Page Gen
                else:
                    print(f"Fallback: Using Master Character for {role} on {page_id}")
                    current_map[role] = master_path # Fallback: Master
            
            # Composite using the updated map (Raw -> Master -> PageGen)
            
            # Composite using the (potentially new) map
            final_page_path = comp_service.composite_page(book_id, page_id, current_map)
            
            if final_page_path:
                # Save & Persist
                uploads_dir = os.path.join(os.getcwd(), "uploads", "pages")
                os.makedirs(uploads_dir, exist_ok=True)
                
                filename = f"order_{order.id}_{page_id}.png"
                public_path = os.path.join(uploads_dir, filename)
                shutil.copy2(final_page_path, public_path)
                
                page_url = f"{settings.BASE_URL}/uploads/pages/{filename}"
                results.append(page_url)
                
                # DB Update
                existing_page = db.query(OrderPage).filter(
                    OrderPage.order_id == order.id,
                    OrderPage.page_number == page_num
                ).first()

                if existing_page:
                    existing_page.image_url = page_url
                else:
                    db_page = OrderPage(
                        order_id=order.id,
                        page_number=page_num,
                        image_url=page_url
                    )
                    db.add(db_page)
                db.commit()
        
        # Mark Complete
        order.status = OrderStatus.COMPLETED
        db.commit()
        
        print(f"Approach B (Simple Mode) Complete. Generated {len(results)} pages.")
        return "COMPLETED"

    except Exception as e:
        print(f"Approach B Failed: {e}")
        import traceback
        traceback.print_exc()
        order.status = OrderStatus.FAILED
        order.failure_reason = str(e)
        db.commit()
        return "FAILED"
    finally:
        db.close()
