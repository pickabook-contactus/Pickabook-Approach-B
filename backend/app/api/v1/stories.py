from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Story, StoryPage
from app.db.schemas import StoryResponse, StoryListResponse
from app.core.config import settings
from typing import List
import uuid
import os
import shutil
import json

router = APIRouter()

@router.get("", response_model=List[StoryListResponse])
def list_stories(db: Session = Depends(get_db)):
    """Get all available story templates"""
    stories = db.query(Story).all()
    return stories

@router.get("/{story_id}", response_model=StoryResponse)
def get_story(story_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific story with all its page templates"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.post("", response_model=StoryResponse)
def create_story(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(19.99),
    cover_image: UploadFile = File(...),
    # We accept a list of files for pages
    page_images: List[UploadFile] = File(...),
    # Metadata as a JSON string: [{"filename": "page1.png", "x": 100...}, ...]
    pages_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Create a new Story with cover and pages.
    Requires multipart/form-data.
    """
    try:
        # 1. Parse Metadata
        try:
            pages_meta = json.loads(pages_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in pages_json")
            
        # 2. Create Story Record
        new_story = Story(
            title=title,
            description=description,
            price=price,
            cover_image_url="" # Will update after save
        )
        db.add(new_story)
        db.flush() # Get ID
        
        # 3. Setup Directories
        base_upload_dir = "uploads/stories"
        story_dir = os.path.join(base_upload_dir, str(new_story.id))
        os.makedirs(story_dir, exist_ok=True)
        
        # 4. Save Cover Image
        cover_filename = f"cover_{cover_image.filename}"
        cover_path = os.path.join(story_dir, cover_filename)
        
        with open(cover_path, "wb") as buffer:
            shutil.copyfileobj(cover_image.file, buffer)
            
        # Construct Public URL (Assuming localhost for now, should be env based really)
        # Using relative path for robustness if accessed via proxy, but schema expects URL.
        # Let's use the static mount convention: http://localhost:8000/uploads/...
        new_story.cover_image_url = f"{settings.BASE_URL}/{convert_path_to_url(cover_path)}"
        
        # 5. Process Pages
        # Create a map of filename -> content for easy access if needed, or just iterate zip?
        # The list 'page_images' contains the actual files. 
        # The JSON 'pages_meta' contains the logic.
        
        # Helper: Map filename to file object
        file_map = {f.filename: f for f in page_images}
        
        for i, meta in enumerate(pages_meta):
            # meta should have: filename, x, y, width, angle(opt)
            fname = meta.get("filename")
            if not fname or fname not in file_map:
                print(f"Warning: Metadata references {fname} but file not uploaded. Skipping.")
                continue
                
            file_obj = file_map[fname]
            
            # Save Page Image
            # Use index to keep order safe? or original name? 
            # Let's use clean naming: page_{i+1}_{fname}
            page_filename = f"page_{i+1}_{fname}"
            page_path = os.path.join(story_dir, page_filename)
            
            with open(page_path, "wb") as buffer:
                file_obj.file.seek(0) # Ensure start
                shutil.copyfileobj(file_obj.file, buffer)
                
            page_url = f"{settings.BASE_URL}/{convert_path_to_url(page_path)}"
            
            # Create DB Record
            new_page = StoryPage(
                story_id=new_story.id,
                page_number=i + 1,
                template_image_url=page_url,
                face_x=meta.get("x", 100),
                face_y=meta.get("y", 100),
                face_width=meta.get("w", 300),
                face_angle=meta.get("angle", 0.0)
            )
            db.add(new_page)
            
        db.commit()
        db.refresh(new_story)
        return new_story
        
    except Exception as e:
        db.rollback()
        print(f"Error creating story: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{story_id}", response_model=StoryResponse)
def update_story(
    story_id: uuid.UUID,
    title: str = Form(None),
    description: str = Form(None),
    price: float = Form(None),
    # Optional: Update coordinates via JSON
    pages_json: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Update Story details and Page Coordinates.
    Does NOT support replacing images yet (use Create for that or separate endpoint).
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    # Update Fields
    if title: story.title = title
    if description: story.description = description
    if price is not None: story.price = price
    
    # Update Coordinates
    if pages_json:
        try:
            pages_updates = json.loads(pages_json)
            # Expect list of objects: {"page_number": 1, "x": 100...}
            for update in pages_updates:
                p_num = update.get("page_number")
                if p_num is None: continue
                
                page = db.query(StoryPage).filter(
                    StoryPage.story_id == story.id,
                    StoryPage.page_number == p_num
                ).first()
                
                if page:
                    if "x" in update: page.face_x = update["x"]
                    if "y" in update: page.face_y = update["y"]
                    if "w" in update: page.face_width = update["w"]
                    if "a" in update: page.face_angle = update["a"]
                    
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in pages_json")
            
    db.commit()
    db.refresh(story)
    return story

def convert_path_to_url(path: str) -> str:
    # Converts "uploads\\stories\\...\\file.png" to "uploads/stories/.../file.png"
    return path.replace("\\", "/")

@router.post("/seed")
def seed_stories(db: Session = Depends(get_db)):
    """
    Development helper to seed demo stories.
    Creates 'The Space Adventure' with 3 sample pages.
    """
    # Check if already seeded
    existing = db.query(Story).filter(Story.title == "The Space Adventure").first()
    space_story_id = None
    
    if existing:
        space_story_id = existing.id
        print("Story already exists. Checking for updates...")
        # Force update cover image in case BASE_URL changed (e.g. localhost -> render)
        existing.cover_image_url = "https://via.placeholder.com/400x600?text=Space+Adventure"
        db.commit()
    else:
        # Create The Space Adventure
        space_story = Story(
            title="The Space Adventure",
            description="Join Captain [Child Name] on an epic journey through the cosmos! Explore mysterious planets, meet friendly aliens, and save the galaxy.",
            cover_image_url="https://via.placeholder.com/400x600?text=Space+Adventure",
            price=19.99
        )
        db.add(space_story)
        db.flush()
        space_story_id = space_story.id
        
    # UPSERT ALL PAGES (1-4) using the "Child Can Be" template for consistency
    custom_url = f"{settings.BASE_URL}/static/templates/child_can_be.png"
    
    # Define all 4 pages with identical settings (for now)
    target_pages = [
        {"num": 1, "url": custom_url, "x": 380, "y": 125, "w": 385, "a": 0.0},
        {"num": 2, "url": custom_url, "x": 380, "y": 125, "w": 385, "a": 0.0},
        {"num": 3, "url": custom_url, "x": 380, "y": 125, "w": 385, "a": 0.0},
        {"num": 4, "url": custom_url, "x": 380, "y": 125, "w": 385, "a": 0.0},
    ]

    for p_data in target_pages:
        page = db.query(StoryPage).filter(
            StoryPage.story_id == space_story_id,
            StoryPage.page_number == p_data["num"]
        ).first()
        
        if not page:
            print(f"Creating Page {p_data['num']}...")
            new_page = StoryPage(
                story_id=space_story_id,
                page_number=p_data["num"],
                template_image_url=p_data["url"],
                face_x=p_data["x"],
                face_y=p_data["y"],
                face_width=p_data["w"],
                face_angle=p_data["a"]
            )
            db.add(new_page)
        else:
            print(f"Updating Page {p_data['num']}...")
            page.template_image_url = p_data["url"]
            page.face_x = p_data["x"]
            page.face_y = p_data["y"]
            page.face_width = p_data["w"]
            page.face_angle = p_data["a"]
            
    db.commit()
    
    return {
        "message": "Successfully seeded/updated The Space Adventure",
        "story_id": str(space_story_id)
    }
