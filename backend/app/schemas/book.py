from pydantic import BaseModel, Field
from typing import List, Optional

class Dimension(BaseModel):
    width: int
    height: int

class StyleConfig(BaseModel):
    base_model: str = "pixar"
    prompt_suffix: str
    negative_prompt: str

class FaceData(BaseModel):
    x: int
    y: int
    width: int
    angle: float = 0.0

class TextData(BaseModel):
    x: int
    y: int
    width: int
    color: str = "#333333"
    max_font_size: int = 60
    content: Optional[str] = None # If text is dynamic

class PageConfig(BaseModel):
    page_number: int
    image_file: str # Filename relative to config
    face_data: Optional[FaceData] = None
    text_data: Optional[TextData] = None

class BookConfig(BaseModel):
    book_id: str
    title: str
    dimensions: Dimension
    style_config: StyleConfig
    pages: List[PageConfig]
