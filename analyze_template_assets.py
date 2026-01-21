import cv2
import numpy as np
import os
import json

BASE_DIR = r"e:\Pickabook Ali\Approach B\pickabook-monorepo\sample Book"
IMG_1 = os.path.join(BASE_DIR, "1.png")
IMG_2 = os.path.join(BASE_DIR, "2.png")
IMG_3 = os.path.join(BASE_DIR, "3.png")

def analyze():
    # 1. Check Sizes
    img1 = cv2.imread(IMG_1)
    img2 = cv2.imread(IMG_2)
    img3 = cv2.imread(IMG_3, cv2.IMREAD_UNCHANGED)
    
    print(f"1.png (Full): {img1.shape if img1 is not None else 'Not Found'}")
    print(f"2.png (Bg): {img2.shape if img2 is not None else 'Not Found'}")
    print(f"3.png (Chars): {img3.shape if img3 is not None else 'Not Found'}")
    
    if img3 is None:
        print("Error: 3.png not found or invalid.")
        return

    # 2. Find Regions (Handle White Background if no Alpha)
    if img3.shape[2] == 4:
        alpha = img3[:, :, 3]
        _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    else:
        # Assuming White Background (255, 255, 255) as "Transparent"
        gray = cv2.cvtColor(img3, cv2.COLOR_BGR2GRAY)
        # Threshold: Any pixel NOT near white is part of the character
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(contours)} contours in 3.png")
    
    slots = []
    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < 5000: continue # Ignore small noise (increased threshold)
        
        # Determine likely role based on height/area
        print(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, area={area}")
        slots.append({"x": x, "y": y, "w": w, "h": h, "area": area})

    # Sort by height to guess Child vs Mom (Mom likely taller)
    slots.sort(key=lambda s: s["h"], reverse=True)
    
    if len(slots) >= 2:
        print("\nPredicted Roles:")
        print(f"Mom (Tallest): {slots[0]}")
        print(f"Child (Next): {slots[1]}")
        
analyze()
