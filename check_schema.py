from app.db.session import engine
from sqlalchemy import text

def check_schema():
    with engine.connect() as conn:
        print("Checking schema...")
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders';"))
        for row in result:
            print(f"Column: {row[0]}, Type: {row[1]}")

if __name__ == "__main__":
    check_schema()
