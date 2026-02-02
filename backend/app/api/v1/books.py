from fastapi import APIRouter
import os
from app.core.config import settings

router = APIRouter()

@router.get("/")
def get_books():
    """
    List available books by scanning the assets/templates directory.
    Returns a list of book IDs (folder names) and their titles.
    """
    # Define Assets Root
    # Assuming backend/assets
    assets_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets")
    templates_dir = os.path.join(assets_root, "templates")
    
    if not os.path.exists(templates_dir):
        return []

    books = []
    for folder_name in os.listdir(templates_dir):
        folder_path = os.path.join(templates_dir, folder_name)
        if os.path.isdir(folder_path):
            # Try to read metadata if exists, else use folder name title
            # For now, Simple: Book ID = Folder Name
            title = folder_name.replace("_", " ").title()
            
            books.append({
                "id": folder_name,
                "title": title,
                "cover_url": f"/static/templates/{folder_name}/cover.png" # Placeholder
            })
            
    return books
