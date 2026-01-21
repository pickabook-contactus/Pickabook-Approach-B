from sqlalchemy import create_engine, text
import os
import sys

# Get DB config from env
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "db")
POSTGRES_DB = os.getenv("POSTGRES_DB", "app")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Construct DATABASE_URL if not set (for local runs mainly)
# Note: When running inside container, 'db' host resolves. If running from host, might need localhost
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

def migrate():
    print(f"Connecting to database...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # 1. Create Stories table if not exists
            print("Creating stories table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR NOT NULL,
                    description TEXT,
                    cover_image_url VARCHAR,
                    price FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc') NOT NULL
                );
            """))

            # 2. Create StoryPages table if not exists
            print("Creating story_pages table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS story_pages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    story_id UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
                    page_number INTEGER NOT NULL,
                    template_image_url VARCHAR NOT NULL,
                    face_x INTEGER DEFAULT 100,
                    face_y INTEGER DEFAULT 100,
                    face_width INTEGER DEFAULT 300,
                    face_angle FLOAT DEFAULT 0.0
                );
            """))

            # 3. Add story_id column to orders table if not exists
            print("Checking orders table for story_id...")
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='orders' AND column_name='story_id';
            """))
            
            if not result.fetchone():
                print("Adding story_id column to orders table...")
                conn.execute(text("""
                    ALTER TABLE orders 
                    ADD COLUMN story_id UUID REFERENCES stories(id);
                """))
            else:
                print("story_id column already exists.")
            
            # 4. Create OrderPages table
            print("Creating order_pages table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS order_pages (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    page_number INTEGER NOT NULL,
                    image_url VARCHAR NOT NULL
                );
            """))
                
            conn.commit()
            print("Migration completed successfully!")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
