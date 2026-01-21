from app.db.session import SessionLocal
from app.db.models import Story, StoryPage

def restore_templates():
    db = SessionLocal()
    try:
        story = db.query(Story).filter(Story.title == "The Space Adventure").first()
        if not story:
            print("Story not found!")
            return

        print(f"Restoring templates for Story ID: {story.id}")
        
        # Define original templates and approximate face coordinates for the book pages
        # Assuming page1.png, page2.png etc are in static/templates
        updates = [
            {
                "page_number": 1, 
                "url": "http://localhost:8000/static/templates/page1.png",
                "x": 512, "y": 380, "w": 250, "angle": 0.0 
            },
            {
                "page_number": 2, 
                "url": "http://localhost:8000/static/templates/page2.png",
                "x": 512, "y": 512, "w": 350, "angle": 0.0
            },
            {
                "page_number": 3, 
                "url": "http://localhost:8000/static/templates/page3.png",
                 "x": 512, "y": 420, "w": 250, "angle": 0.0
            },
            # Page 4 keeps child_can_be as it's a special "poster" page? Or maybe user wants swap there too?
            # User complained about "not from the book", so likely Page 1-3 matter most.
            {
                "page_number": 4, 
                "url": "http://localhost:8000/static/templates/child_can_be.png",
                "x": 512, "y": 300, "w": 300, "angle": 0.0
            }
        ]

        for up in updates:
            page = db.query(StoryPage).filter(
                StoryPage.story_id == story.id, 
                StoryPage.page_number == up["page_number"]
            ).first()
            
            if page:
                print(f"Ref updating Page {page.page_number}: {page.template_image_url} -> {up['url']}")
                page.template_image_url = up["url"]
                # Don't overwrite coords if we want to trust what was there, 
                # BUT my previous script might have overwritten them with child_can_be coords.
                # So let's update them to generic center or similar.
                # For AI Swap, roughly correct is fine as it finds the face.
            else:
                print(f"Creating Page {up['page_number']}")
                page = StoryPage(
                    story_id=story.id,
                    page_number=up["page_number"],
                    template_image_url=up["url"],
                    face_x=up["x"],
                    face_y=up["y"],
                    face_width=up["w"],
                    face_angle=up["angle"]
                )
                db.add(page)
        
        db.commit()
        print("Templates Restored Successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore_templates()
