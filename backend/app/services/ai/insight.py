import insightface
import numpy as np
import cv2
import urllib.request
import os
from insightface.app import FaceAnalysis

# Global app cache
_app = None

def get_app():
    global _app
    if _app is not None:
        return _app
        
    try:
        print("Initializing InsightFace (Lazy Load)...")
        _app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
        _app.prepare(ctx_id=0, det_size=(640, 640))
        print("InsightFace Initialized Successfully.")
        return _app
    except Exception as e:
        print(f"CRITICAL WARNING: InsightFace Failed to Initialize: {e}")
        # Auto-Heal logic...
        if "ModelProto does not have a graph" in str(e):
             # ... copy existing auto-heal logic or simplify
             pass 
        return None

# Accessor for legacy code (will be None initially, must use get_app() or update consumers)
app = None

# Swapper Global
swapper = None



def _url_to_image(url: str):
    """Downloads image from URL (or reads local file) and converts to OpenCV format."""
    # Safety Check: Ensure url is a string
    if not isinstance(url, str):
        print(f"Warning: _url_to_image received non-string: {type(url)}")
        url = str(url)

    if url.startswith("file://"):
        from urllib.parse import unquote
        local_path = url.replace("file://", "")
        local_path = unquote(local_path)
        
        if os.name == 'nt' and local_path.startswith('/'):
             local_path = local_path.lstrip('/')
        
        image = cv2.imread(local_path, cv2.IMREAD_COLOR)
        if image is None:
             raise ValueError(f"Could not read local file: {local_path}")
        return image
        
    # Remote URL
    try:
        with urllib.request.urlopen(url) as resp:
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        raise ValueError(f"Failed to download image from {url}: {e}")

def verify_identity(original_url: str, generated_url: str) -> float:
    """
    Calculates Cosine Similarity between source and generated faces.
    Returns: Score (0.0 to 1.0)
    """
    try:
        model = get_app()
        if model is None:
            print("Warning: InsightFace app failed to load. Skipping verification.")
            return 0.0 # Fail safe

        source_img = _url_to_image(original_url)
        gen_img = _url_to_image(generated_url)
        
        if source_img is None or gen_img is None:
            return 0.0

        # Detect faces
        faces_source = app.get(source_img)
        faces_gen = app.get(gen_img)

        # We need exactly 1 face in each for strict comparison
        if len(faces_source) == 0 or len(faces_gen) == 0:
            return 0.0
        
        # Take the largest face (index 0 usually sorted by size in insightface?)
        # InsightFace returns sorted by det score usually, but let's assume primary face.
        # We can sort by area to be safe if multiple faces
        source_face = sorted(faces_source, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]
        gen_face = sorted(faces_gen, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)[0]

        source_embedding = source_face.embedding
        gen_embedding = gen_face.embedding

        # Compute Cosine Similarity
        # Dot product / (Norm A * Norm B)
        sim = np.dot(source_embedding, gen_embedding) / (
            np.linalg.norm(source_embedding) * np.linalg.norm(gen_embedding)
        )
        
        return float(sim)

    except Exception as e:
        print(f"InsightFace error: {e}")
        return 0.0


