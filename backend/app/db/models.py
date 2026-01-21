import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Enum, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

class Base(DeclarativeBase):
    pass

class OrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Story(Base):
    """Represents a book template (e.g., 'The Space Adventure', 'Cinderella')"""
    __tablename__ = "stories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    pages = relationship("StoryPage", back_populates="story", cascade="all, delete-orphan")

class StoryPage(Base):
    """Represents a single page template within a story"""
    __tablename__ = "story_pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    
    # Template path/URL
    template_image_url = Column(String, nullable=False)
    
    # Face placement coordinates
    face_x = Column(Integer, default=100)
    face_y = Column(Integer, default=100)
    face_width = Column(Integer, default=300)
    face_angle = Column(Float, default=0.0)
    
    # Relationship
    story = relationship("Story", back_populates="pages")

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Link to selected story (Loose coupling for flexibility)
    story_id = Column(String, nullable=True)
    
    child_name = Column(String, nullable=False)
    photo_url = Column(String, nullable=False) # Child Photo
    
    # Mom / Secondary Character
    mom_name = Column(String, nullable=True)
    mom_photo_url = Column(String, nullable=True)
    
    # Generated Assets
    character_asset_url = Column(String, nullable=True)
    pdf_url = Column(String, nullable=True)
    
    failure_reason = Column(Text, nullable=True)
    
    
    # Relationship
    # story = relationship("Story") # Removing loose coupling relationship
    generated_pages = relationship("OrderPage", back_populates="order", cascade="all, delete-orphan", order_by="OrderPage.page_number")

class OrderPage(Base):
    """Represents a generated page for a specific order"""
    __tablename__ = "order_pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    
    order = relationship("Order", back_populates="generated_pages")
