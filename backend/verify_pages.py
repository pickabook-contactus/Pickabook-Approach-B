from sqlalchemy import create_engine, text
import os

# Get DB config from env
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

def verify():
    print(f"Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("\n--- Checking Orders ---")
            result = conn.execute(text("SELECT id, status, created_at, child_name FROM orders ORDER BY created_at DESC LIMIT 5;"))
            orders = result.fetchall()
            for o in orders:
                print(f"Order: {o.id} | Status: {o.status} | Child: {o.child_name}")
                
            print("\n--- Checking Order Pages ---")
            result = conn.execute(text("SELECT * FROM order_pages;"))
            pages = result.fetchall()
            print(f"Total Pages Found: {len(pages)}")
            for p in pages:
                print(f"Page: Order {p.order_id} | # {p.page_number} | URL: {p.image_url}")

    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
