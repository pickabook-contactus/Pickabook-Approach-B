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
    
    # -------------------------------------------------------------
    # PRELOAD AI MODELS
    # -------------------------------------------------------------
    print("--- [STARTUP] Preloading AI Models... ---")
    try:
        # 1. Preload REMBG (u2net)
        print("[STARTUP] Loading REMBG (u2net)...")
        from rembg import remove, new_session
        import numpy as np
        # Dummy inference to provoke download/cache
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        remove(dummy_img) 
        print("[STARTUP] REMBG Loaded.")
        
        # 2. Preload InsightFace (buffalo_s)
        print("[STARTUP] Loading InsightFace (buffalo_s)...")
        from app.services.ai.insight import get_app
        get_app() # Trigger lazy load
        print("[STARTUP] InsightFace Loaded.")
        
    except Exception as e:
        print(f"[STARTUP] WARNING: Model preload failed: {e}")
    print("--- [STARTUP] AI Models Ready. ---")


from app.api.v1 import orders, stories, ai, test, books

app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(stories.router, prefix="/api/v1/stories", tags=["stories"])
app.include_router(books.router, prefix="/api/v1/books", tags=["books"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Tooling"])
app.include_router(test.router, prefix="/api/v1/test", tags=["test"])

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://pickabook-approach-b.vercel.app",  # Explicit Vercel Origin
]

# Add origins from config
if settings.BACKEND_CORS_ORIGINS:
    origins.extend(settings.BACKEND_CORS_ORIGINS)

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
