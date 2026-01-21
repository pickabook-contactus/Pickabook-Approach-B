import sys
import os
# Ensure app is in path
sys.path.append("/app")

from app.db.session import SessionLocal
from app.db.models import Order, Story
from app.worker.tasks import process_order_v2

def force_repair():
    db = SessionLocal()
    try:
        # Find the main story
        story = db.query(Story).filter(Story.title == "The Space Adventure").first()
        if not story:
            print("Story 'The Space Adventure' not found!")
            return

        order_ids = [
            "e8a87d2b-0917-44b0-95fb-1572f8e377ee", # The original one with "Source Face" error
            "900a9c49-7210-40c5-8df2-e261b81315da"  # The new one with "Placeholder" error
        ]

        for oid in order_ids:
            order = db.query(Order).get(oid)
            if not order:
                print(f"Order {oid} not found, skipping.")
                continue

            print(f"Reparing Order {oid}...")
            
            # 1. Link to Story if missing
            if not order.story_id:
                print(f"  - Linking to Story: {story.title}")
                order.story_id = story.id
            
            # 2. CLEAR generated face to force RE-GENERATION (Critical for e8a8)
            print(f"  - Clearing character_asset_url to force regeneration.")
            order.character_asset_url = None
            
            # 3. Reset Status and CLEANUP Old Pages
            order.status = "PROCESSING"
            order.failure_reason = None
            
            # Explicitly clear old pages to avoid duplicates and stale URLs
            from app.db.models import OrderPage
            db.query(OrderPage).filter(OrderPage.order_id == oid).delete()
            print(f"  - Cleared old OrderPage entries.")
            
            db.commit()
            
            # 4. Trigger Worker
            print(f"  - Triggering Worker Task...")
            process_order_v2.delay(str(order.id), order.photo_url)
            print("  - Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    force_repair()
