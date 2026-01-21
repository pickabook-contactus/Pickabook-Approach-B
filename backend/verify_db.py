import os
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env manually since we are running a standalone script
load_dotenv(dotenv_path="e:/Pickabook Ali/New Reop 8th Jan/pickabook-monorepo/.env")

db_url = os.getenv("DATABASE_URL")
print(f"Connecting to: {db_url.split('@')[1] if '@' in db_url else 'Invalid URL'}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, status, customer_email FROM orders ORDER BY created_at DESC LIMIT 5;"))
        rows = result.fetchall()
        print("\n✅ CONNECTION SUCCESSFUL!")
        print(f"Found {len(rows)} recent orders:")
        for row in rows:
            print(f" - ID: {row[0]} | Status: {row[1]} | Email: {row[2]}")
            
except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
