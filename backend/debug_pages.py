

from app.db.session import SessionLocal
from app.db.models import OrderPage
from sqlalchemy import select

def check_pages():
    with SessionLocal() as session:
        order_id = "900a9c49-7210-40c5-8df2-e261b81315da"
        result = session.execute(select(OrderPage).where(OrderPage.order_id == order_id))
        pages = result.scalars().all()
        
        print(f"Found {len(pages)} pages for order {order_id}:")
        for page in pages:
            print(f"Page {page.page_number}: {page.image_url}")

if __name__ == "__main__":
    check_pages()
