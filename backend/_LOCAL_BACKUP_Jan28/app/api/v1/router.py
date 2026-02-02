from fastapi import APIRouter
from app.api.v1 import orders

api_router = APIRouter()

api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
