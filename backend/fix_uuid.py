from app.db.session import engine
from sqlalchemy import text

def migrate_uuid_to_string():
    with engine.connect() as conn:
        print("Migrating UUID to String...")
        
        # 1. Drop Foreign Key on orders.story_id
        try:
            # Need to find the name of the constraint. usually orders_story_id_fkey
            conn.execute(text("ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_story_id_fkey;"))
            print("Dropped orders FK.")
        except Exception as e:
            print(f"Error dropping FK: {e}")

        # 2. Alter orders.story_id to VARCHAR
        try:
            conn.execute(text("ALTER TABLE orders ALTER COLUMN story_id TYPE VARCHAR;"))
            print("Altered orders.story_id to VARCHAR.")
        except Exception as e:
            print(f"Error altering orders.story_id: {e}")

        # 3. Alter stories.id to VARCHAR (Optional but good for consistency)
        try:
            conn.execute(text("ALTER TABLE stories ALTER COLUMN id TYPE VARCHAR;"))
            print("Altered stories.id to VARCHAR.")
        except Exception as e:
             # This might fail if other FKs point to it, but for now orders was the main one
            print(f"Error altering stories.id: {e}")

        conn.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate_uuid_to_string()
