
from app.db.session import SessionLocal
from app.db.models import OrderPage
from sqlalchemy import delete

def clean_pages():
    with SessionLocal() as session:
        order_id = "900a9c49-7210-40c5-8df2-e261b81315da"
        print(f"Deleting pages for order {order_id}...")
        stmt = delete(OrderPage).where(OrderPage.order_id == order_id)
        result = session.execute(stmt)
        session.commit()
        print(f"Deleted {result.rowcount} pages.")

if __name__ == "__main__":
    clean_pages()
