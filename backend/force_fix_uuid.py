from app.db.session import engine
from sqlalchemy import text

def force_fix():
    print("Starting FORCE MIGRATION: story_id -> VARCHAR")
    with engine.connect() as conn:
        # Constraint names can vary. Let's try to look it up or drop common default.
        # Usually it is 'orders_story_id_fkey'. 
        
        # 1. Drop Constraint
        print("Dropping FK constraint orders_story_id_fkey...")
        try:
            conn.execute(text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_story_id_fkey"))
            print("Dropped orders_story_id_fkey (if existed).")
        except Exception as e:
            print(f"Warning dropping FK: {e}")
            
        # 2. Alter Column with USING cast to avoid "cannot be cast automatically" error
        # "operator does not exist: uuid = character varying" might happen if we don't cast.
        # UUID -> VARCHAR is usually implicit or requires ::text
        print("Altering story_id to VARCHAR...")
        try:
            conn.execute(text("ALTER TABLE orders ALTER COLUMN story_id TYPE VARCHAR USING story_id::text"))
            print("SUCCESS: Altered story_id to VARCHAR.")
        except Exception as e:
            print(f"CRITICAL ERROR altering column: {e}")
            
        conn.commit()
    print("Force Migration Finished.")

if __name__ == "__main__":
    force_fix()
