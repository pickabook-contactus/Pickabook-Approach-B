from app.db.session import SessionLocal
from app.db.models import Story, StoryPage

def fix_pages():
    db = SessionLocal()
    try:
        story = db.query(Story).filter(Story.title == "The Space Adventure").first()
        if not story:
            print("Story not found!")
            return

        print(f"Updating pages for Story: {story.id}")
        
        custom_url = "http://localhost:8000/static/templates/child_can_be.png"
        target_coords = {"x": 340, "y": 180, "w": 345, "a": 0.0}
        
        # Update/Upsert pages 1-4
        for i in range(1, 5):
            page = db.query(StoryPage).filter(
                StoryPage.story_id == story.id,
                StoryPage.page_number == i
            ).first()
            
            if not page:
                print(f"Creating Page {i}")
                page = StoryPage(
                    story_id=story.id,
                    page_number=i,
                    template_image_url=custom_url,
                    face_x=target_coords["x"],
                    face_y=target_coords["y"],
                    face_width=target_coords["w"],
                    face_angle=target_coords["a"]
                )
                db.add(page)
            else:
                print(f"Updating Page {i} from {page.template_image_url}")
                page.template_image_url = custom_url
                page.face_x = target_coords["x"]
                page.face_y = target_coords["y"]
                page.face_width = target_coords["w"]
                page.face_angle = target_coords["a"]
                
        db.commit()
        print("Pages 1-4 updated successfully to use child_can_be.png")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_pages()
