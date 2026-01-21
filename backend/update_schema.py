from app.db.session import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Migrating schema...")
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN mom_name VARCHAR;"))
            print("Added mom_name column.")
        except Exception as e:
            print(f"mom_name error (maybe exists): {e}")
            
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN mom_photo_url VARCHAR;"))
            print("Added mom_photo_url column.")
        except Exception as e:
            print(f"mom_photo_url error (maybe exists): {e}")

        conn.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
