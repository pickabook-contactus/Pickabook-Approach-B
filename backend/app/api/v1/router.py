from app.api.v1 import orders, books

api_router = APIRouter()

api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
