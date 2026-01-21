import sys
from app.db.session import SessionLocal
from app.db.models import Order, Story, OrderStatus
from app.worker.tasks import process_order_v2

def repair():
    db = SessionLocal()
    # Target the specific order ID the user is looking at
    order_id = "e8a87d2b-0917-44b0-95fb-1572f8e377ee"
    order = db.query(Order).get(order_id)
    if not order:
        print("Order not found")
        return

    # Find Story
    story = db.query(Story).filter(Story.title == "The Space Adventure").first()
    if not story:
        print("Story not found!")
        return

    print(f"Fixing Order {order_id}...")
    print(f"Old Status: {order.status}")
    print(f"Old Story ID: {order.story_id}")
    
    # FIX: Set the missed story_id
    order.story_id = story.id
    # Reset status so it processes again (though failed is also fine, it's safer to be explicit)
    order.status = OrderStatus.PROCESSING
    order.failure_reason = None
    
    # FORCE REGENERATION: User complained about AI quality, so clear the old face
    order.character_asset_url = None
    
    db.commit()
    print(f"New Story ID: {order.story_id}")

    print("Triggering Task (Idempotent Recovery)...")
    # We call .delay() on the celery task to run it in the (restarted) worker
    task = process_order_v2.delay(order.id, order.photo_url)
    print(f"Task triggered successfully: {task.id}")
    print("Check worker logs for progress.")

if __name__ == "__main__":
    repair()
