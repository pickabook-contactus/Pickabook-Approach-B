import cv2
import numpy as np
import urllib.request
import app.services.ai.insight as insight_service

# NOTE: We access insight_service.app dynamically to avoid import-time reference staleness.

def validate_photo(photo_url: str) -> dict:
    """
    Validates a photo for clarity and single-face presence.
    Returns: {"valid": bool, "reason": str}
    """
    # 0. Safety Check for AI Model
    model = insight_service.get_app()
    if model is None:
        print("WARNING: FaceAnalysis app failed to load. Skipping Face/Gender checks.")
        return {
             "valid": False, 
             "reason": "AI System could not initialize. Check server logs.",
             "checks": {"face_detected": False}
        }

    try:
        # 1. Download & Decode
        # urllib handles 'http', 'https', and 'file://' schemes automatically.
        with urllib.request.urlopen(photo_url) as resp:
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
            img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is None:
            return {"valid": False, "reason": "Could not decode image."}

        height, width = img.shape[:2]
        min_dim = min(height, width)
        
        # 2. Blur Check (Laplacian Variance)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_sharp = blur_score >= 100
        
        # 3. Face Count Check
        print(f"Detecting faces in {photo_url}...")
        faces = model.get(img)
        face_count = len(faces)
        has_one_face = face_count == 1
        
        # 4. Resolution Check
        is_high_res = min_dim >= 500
        
        # Overall Validity
        is_valid = bool(is_sharp and has_one_face and is_high_res)
        
        failure_reasons = []
        if not is_sharp: failure_reasons.append("Image is too blurry")
        if not has_one_face: failure_reasons.append(f"Found {int(face_count)} faces (expected 1)")
        if not is_high_res: failure_reasons.append(f"Low resolution ({int(min_dim)}px < 500px)")
        
        return {
            "valid": is_valid,
            "reason": "; ".join(failure_reasons) if failure_reasons else "All checks passed",
            "checks": {
                "face_detected": bool(has_one_face),
                "is_sharp": bool(is_sharp),
                "is_high_res": bool(is_high_res),
                "face_count": int(face_count),
                "blur_score": int(blur_score),
                "resolution": f"{int(width)}x{int(height)}"
            }
        }

    except Exception as e:
        print(f"Validation Critical Error: {e}")
        return {
            "valid": False, 
            "reason": f"System Error processing photo: {str(e)}",
            "checks": {
                "face_detected": False,
                "is_sharp": False,
                "is_high_res": False
            }
        }
