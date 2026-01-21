from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.db.models import OrderStatus

class OrderCreate(BaseModel):
    child_name: str
    photo_url: str
    mom_name: Optional[str] = None
    mom_photo_url: Optional[str] = None
    story_id: Optional[str] = None

class OrderResponse(BaseModel):
    id: UUID
    status: OrderStatus
    created_at: datetime
    child_name: str
    photo_url: str
    mom_name: Optional[str] = None
    mom_photo_url: Optional[str] = None
    character_asset_url: Optional[str] = None
    pdf_url: Optional[str] = None
    failure_reason: Optional[str] = None
    
    class OrderPageSchema(BaseModel):
        page_number: int
        image_url: str
        
        class Config:
            from_attributes = True

    generated_pages: list[OrderPageSchema] = []

    class Config:
        from_attributes = True

class OrderStatusSchema(BaseModel):
    id: UUID
    status: OrderStatus
