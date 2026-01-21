from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

# Story Schemas
class StoryPageBase(BaseModel):
    page_number: int
    template_image_url: str
    face_x: int = 100
    face_y: int = 100
    face_width: int = 300
    face_angle: float = 0.0

class StoryPageResponse(StoryPageBase):
    id: UUID
    story_id: UUID
    
    class Config:
        from_attributes = True

class StoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    price: float = 0.0

class StoryResponse(StoryBase):
    id: UUID
    created_at: datetime
    pages: list[StoryPageResponse] = []
    
    class Config:
        from_attributes = True

class StoryListResponse(StoryBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Order Schemas (updated)
class OrderCreate(BaseModel):
    child_name: str
    story_id: Optional[UUID] = None

class OrderResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    child_name: str
    photo_url: str
    story_id: Optional[UUID] = None
    character_asset_url: Optional[str] = None
    pdf_url: Optional[str] = None
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True
