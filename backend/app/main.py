from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
import os

app = FastAPI(title=settings.PROJECT_NAME)

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount uploads directory for generated files
uploads_dir = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

from app.db.session import engine
from app.db.models import Base

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


from app.api.v1 import orders, stories, ai

app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(stories.router, prefix="/api/v1/stories", tags=["stories"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Tooling"])

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*", # Keep for fallback if explicit lists fail, but usually explicit is preferred with credentials
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PickaBook API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
