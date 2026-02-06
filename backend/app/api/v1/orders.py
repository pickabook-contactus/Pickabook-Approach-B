from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderResponse
from app.worker.tasks import process_order_v2
from app.services.ai import validator
import shutil
import os
import uuid

router = APIRouter()

# ... existing code ...

@router.get("/", response_model=List[OrderResponse])
def get_all_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all orders (for Swagger/Admin use).
    """
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

# Determine upload directory
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload")
def upload_photo(file: UploadFile = File(...)):
    """
    Receives a photo, saves it locally, and validates it using Local Validator.
    """
    try:
        # 1. Save file locally
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        from pathlib import Path
        fake_url = Path(os.path.abspath(file_path)).as_uri()
                
        # Run Validation
        # Enabled for HuggingFace Spaces
        validation_result = validator.validate_photo(fake_url)
        
        # Default Success Response
        return {
            "url": fake_url, 
            "local_path": file_path, 
            "valid": validation_result["valid"],
            "reason": validation_result.get("reason", ""),
            "checks": validation_result.get("checks", {})
        }
    except Exception as e:
        print(f"Upload Endpoint Critical Error: {e}")
        return {
            "url": "",
            "local_path": "",
            "valid": False,
            "reason": f"Server Upload Error: {str(e)}",
            "checks": {}
        }

@router.post("/create", response_model=OrderResponse)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Creates an order order row and triggers the Async Worker.
    """
    # Create DB Row (Status: QUEUED)
    # Note: Prompt says "QUEUED", but Enum has "DRAFT", "PROCESSING". 
    # I'll use PROCESSING as equivalent to Queued/Running for now, or add Queued.
    # Enum in models.py: DRAFT, PROCESSING, COMPLETED, FAILED.
    # Let's use PROCESSING or DRAFT then trigger.
    
    # Default to Space Adventure if no story provided
    if not order_in.story_id:
        # Ideally fetch by title or env var, here we hardcode valid UUID or query it
        # Let's query it dynamically to be safe
        from app.db.models import Story
        default_story = db.query(Story).filter(Story.title == "The Space Adventure").first()
        if default_story:
            order_in.story_id = str(default_story.id)

    db_order = Order(
        child_name=order_in.child_name,
        photo_url=order_in.photo_url,
        mom_name=order_in.mom_name,
        mom_photo_url=order_in.mom_photo_url,
        story_id=order_in.story_id,
        status=OrderStatus.PROCESSING 
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Trigger Celery Task - Approach B
    from app.worker.tasks import process_approach_b
    
    # Use story_id as book_id, defaulting to book_sample if needed
    # (In DB story_id might be a UUID, but for Approach B file structs we use keys like 'book_sample')
    # For MVP, we force "book_sample" unless mapped. 
    # Let's assume order_in.story_id contains the key like "book_sample" if provided, 
    # or if it's a UUID, the task needs to look it up.
    # Given the task.py logic: book_id="book_sample" default.
    # Dynamic Book ID
    # We use story_id as the folder name (book_id)
    target_book_id = order_in.story_id if order_in.story_id else "magic_of_money"
    print(f"Creating Order for Book: {target_book_id}") 
    
    # Pass Mom photo URL to task as well
    # We might need to update task signature to accept kwargs or expanded args
    # For now, let's keep it simple: pass order_id and let task read DB for details?
    # Actually task.py currently takes: (order_id, photo_url, book_id).
    # We should update task signature. For now, let's pass child photo_url as primary, 
    # but the task will read order.mom_photo_url from DB if needed.
    # Actually, task reads 'photo_url' arg, but it also queries DB.
    # Let's rely on DB for the second photo.
    
    # Explicitly pass book_id as kwarg to avoid positional mapping issues with stale workers
    process_approach_b.apply_async(
        args=[str(db_order.id), db_order.photo_url],
        kwargs={"book_id": target_book_id}
    )
    
    return db_order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Fetches order status.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
