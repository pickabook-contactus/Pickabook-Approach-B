from app.db.session import SessionLocal
from app.db.models import Order, Story, StoryPage

def check():
    db = SessionLocal()
    try:
        print("--- RECENT ORDERS ---")
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
        for o in orders:
            print(f"Order ID: {o.id} | StoryID: {o.story_id} | Status: {o.status}")
            
        print("\n--- STORIES ---")
        stories = db.query(Story).all()
        for s in stories:
            print(f"ID: {s.id} | Title: {s.title}")
            
        print("\n--- PAGES for 'The Space Adventure' ---")
        space_story = db.query(Story).filter(Story.title == "The Space Adventure").first()
        if space_story:
            pages = db.query(StoryPage).filter(StoryPage.story_id == space_story.id).all()
            for p in pages:
                print(f"Page {p.page_number} | Template: {p.template_image_url}")
        else:
            print("Space Adventure Story NOT FOUND!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
