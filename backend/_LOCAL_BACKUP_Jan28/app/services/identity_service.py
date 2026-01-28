import os
import json
import uuid
import shutil
from typing import Dict, Any, Optional
import cv2
import numpy as np
from app.services.ai import validator
from app.services.ai import insight as insight_service

class IdentityService:
    def __init__(self, assets_root: str):
        self.assets_root = assets_root
        self.orders_dir = os.path.join(self.assets_root, "orders")
        os.makedirs(self.orders_dir, exist_ok=True)

    def create_identity(self, order_id: str, photo_path: str, role: str = "child", face_index: int = 0) -> Dict[str, Any]:
        """
        Process a user photo to create an identity.
        role: 'child' or 'mom'
        face_index: 0 for largest face, 1 for second largest, etc.
        """
        # 1. Validation
        print(f"Validating photo: {photo_path}")
        
        # Robust URI conversion for Windows/Linux
        import pathlib
        photo_url = pathlib.Path(os.path.abspath(photo_path)).as_uri()
        
        validation_result = validator.validate_photo(photo_url)
        if not validation_result["valid"]:
             print(f"WARNING: Validation failed ({validation_result['reason']}). Proceeding with best effort...")

        # 2. Setup Order Directory
        order_dir = os.path.join(self.orders_dir, order_id)
        # Use sub-folder per role to avoid overwriting if both come from same input but separate calls
        identity_dir = os.path.join(order_dir, "identity", role) 
        input_dir = os.path.join(order_dir, "input")
        os.makedirs(identity_dir, exist_ok=True)
        os.makedirs(input_dir, exist_ok=True)

        # Copy source image to input dir
        filename = os.path.basename(photo_path)
        dest_path = os.path.join(input_dir, filename)
        if hasattr(os, "symlink"):
             # For dev speed, maybe symlink? No, copy is safer for "upload" simulation
             try:
                shutil.copy2(photo_path, dest_path)
             except shutil.SameFileError:
                pass
        else:
             try:
                shutil.copy2(photo_path, dest_path)
             except shutil.SameFileError:
                pass

        # 3. Attribute Extraction (Heuristic for now)
        # Load image again for processing (validator decoded it but didn't return it)
        img = insight_service._url_to_image(photo_url)
        faces = insight_service.app.get(img)
        
        if not faces:
             raise ValueError("No faces detected during extraction")
        
        # Sort by size to pick the primary subject
        sorted_faces = sorted(faces, key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
        
        if face_index >= len(sorted_faces):
             raise ValueError(f"Requested face_index {face_index} but only found {len(sorted_faces)} faces.")
             
        face = sorted_faces[face_index]
        print(f"Selected face index {face_index}: {int(face.bbox[2]-face.bbox[0])}x{int(face.bbox[3]-face.bbox[1])} px")
        
        # Simple Skin Tone Estimator
        # Get center of face (nose area)
        bbox = face.bbox.astype(int)
        center_x = (bbox[0] + bbox[2]) // 2
        center_y = (bbox[1] + bbox[3]) // 2
        
        # Sample small region
        # Ensure bounds
        sample_img = img[max(0, center_y-5):min(img.shape[0], center_y+5), 
                         max(0, center_x-5):min(img.shape[1], center_x+5)]
        
        # Average Color (BGR)
        avg_color = sample_img.mean(axis=0).mean(axis=0)
        skin_tone_hex = "#{:02x}{:02x}{:02x}".format(int(avg_color[2]), int(avg_color[1]), int(avg_color[0]))

        attributes = {
             "skin_tone_hex": skin_tone_hex,
             "age_group": role, # Use role as proxy? Or infer from face age (face.age)
             "gender_detected": int(face.gender) if hasattr(face, 'gender') else None
        }

        # 4. Save Face Crop (Identity Ref)
        # Crop with some margin
        margin = 50
        x1 = max(0, bbox[0] - margin)
        y1 = max(0, bbox[1] - margin)
        x2 = min(img.shape[1], bbox[2] + margin)
        y2 = min(img.shape[0], bbox[3] + margin)
        
        face_crop = img[int(y1):int(y2), int(x1):int(x2)]
        face_ref_filename = f"face_ref_{role}.png"
        face_ref_path = os.path.join(identity_dir, face_ref_filename)
        cv2.imwrite(face_ref_path, face_crop)

        # 5. Create identity.json
        identity_data = {
             "order_id": order_id,
             "role": role,
             "source_images": [{"path": f"input/{filename}", "primary": True}],
             "attributes": attributes,
             "identity_refs": {"face_crop": f"identity/{role}/{face_ref_filename}"}
        }

        identity_json_path = os.path.join(identity_dir, "identity.json")
        with open(identity_json_path, "w") as f:
             json.dump(identity_data, f, indent=2)

        print(f"Created Identity for Order {order_id} at {identity_json_path}")
        return identity_data

if __name__ == "__main__":
    # Test Run
    assets_dir = os.path.join(os.getcwd(), "backend", "assets")
    service = IdentityService(assets_root="backend/assets")
    
    # Use one of the sample images
    sample_child = "backend/assets/templates/book_sample/v1/pages/p001/ref_child.png"
    # Note: ref_child.png was made transparent/white-removed, so it might fail face detection 
    # if the insightface model expects a full photo. 
    # Better to use the original uploaded file if possible, or 4.png from sample Book
    
    original_child = "sample Book/4.png" # The one with white background is fine for detection usually
    
    try:
        service.create_identity("ORD_TEST_001", original_child, "child")
    except Exception as e:
        print(f"Test Failed: {e}")
