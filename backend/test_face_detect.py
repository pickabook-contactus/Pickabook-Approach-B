import cv2
import numpy as np
from insightface.app import FaceAnalysis
import os

app = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

img_path = "/app/app/static/templates/child_can_be.png"
if not os.path.exists(img_path):
    # Try local path relative to backend root
    img_path = "app/static/templates/child_can_be.png"

print(f"Testing Face Detection on: {img_path}")

try:
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to load image")
    else:
        faces = app.get(img)
        print(f"Faces detected: {len(faces)}")
        for i, face in enumerate(faces):
            print(f"Face {i}: bbox={face.bbox}, score={face.det_score}")
except Exception as e:
    print(f"Error: {e}")
