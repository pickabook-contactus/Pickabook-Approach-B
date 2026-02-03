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
    Seeds the database with stories corresponding to the available file templates.
    """
    # Define the templates we want to represent in the DB
    # Mapping Folder Name (Template ID) -> DB Story Details
    templates_to_seed = [
        {
            "id": "magic_of_money",
            "title": "The Magic of Money",
            "description": "A wonderful journey teaching the value of money. (Includes Mom & Child)",
            "cover_url": f"{settings.BASE_URL}/static/templates/magic_of_money/cover.png",
            "price": 24.99
        },
        {
            "id": "mother_and_kid",
            "title": "Mother and Kid",
            "description": "A heartwarming tale of love and bonding.",
            "cover_url": f"{settings.BASE_URL}/static/templates/mother_and_kid/cover.png",
            "price": 24.99
        },
        {
            "id": "book_sample",
            "title": "Book Sample",
            "description": "A simple demo book to test the generation pipeline.",
            "cover_url": f"{settings.BASE_URL}/static/templates/book_sample/cover.png",
            "price": 19.99
        }
    ]

    results = []

    for tmpl in templates_to_seed:
        # Check if exists by title
        existing = db.query(Story).filter(Story.title == tmpl["title"]).first()
        story_id = None
        
        if existing:
            story_id = existing.id
            print(f"Update existing story: {tmpl['title']}")
            existing.cover_image_url = tmpl["cover_url"]
            existing.description = tmpl["description"] # Update description
            db.commit()
        else:
            print(f"Creating new story: {tmpl['title']}")
            new_story = Story(
                title=tmpl["title"],
                description=tmpl["description"],
                cover_image_url=tmpl["cover_url"],
                price=tmpl["price"]
            )
            db.add(new_story)
            db.flush()
            story_id = new_story.id
        
        # We also need to ensure Pages exist? 
        # For now, let's just ensure the Story record exists so it shows on Home.
        # The 'pages' logic in seed_stories was for the old DB-driven generator.
        # The new Phase 2 uses the 'prompts.json' file, so DB pages are less critical 
        # UNLESS the frontend 'Read' view relies on them.
        
        # Let's seed dummy pages just in case frontend crashes without them
        if db.query(StoryPage).filter(StoryPage.story_id == story_id).count() == 0:
             # Add a dummy page
             dummy_page = StoryPage(
                 story_id=story_id,
                 page_number=1,
                 template_image_url=f"{settings.BASE_URL}/static/templates/{tmpl['id']}/pages/p001/bg.png", # Best guess path
                 face_x=100, face_y=100, face_width=100, face_angle=0
             )
             db.add(dummy_page)
             db.commit()

        results.append({"title": tmpl["title"], "id": str(story_id)})

    return {
        "message": "Seeded Templates",
        "stories": results
    }
