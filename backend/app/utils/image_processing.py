
import io
import cv2
import numpy as np
from PIL import Image
from rembg import remove

def process_character_output(image_bytes: bytes) -> bytes:
    """
    Processes the raw output from AI (Gemini):
    1. Removes background (ensure transparency).
    2. Detects distinct character islands (contours).
    3. If multiple islands found (e.g. Master Ref + Result), filters to keep the best one.
       Heuristic: Keep the SINGLE LARGEST island.
       (Usually Master Ref and Result are separate).
    
    Returns: Bytes of the processed, single-character PNG.
    """
    try:
        # 1. Remove Background
        # Input might already be transparent or white bg. rembg handles both.
        # [REVERTED] Disabled alpha_matting to match "Earlier" behavior which worked better.
        output_png = remove(image_bytes)
        
        # Convert to CV2 for analysis
        # Load as numpy array
        nparr = np.frombuffer(output_png, np.uint8)
        img_rgba = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        
        if img_rgba is None:
            raise ValueError("Failed to decode image after rembg")

        # 2. Extract Alpha Channel
        if img_rgba.shape[2] == 4:
            alpha = img_rgba[:, :, 3]
        else:
            # Create alpha from grayscale threshold if missing
            gray = cv2.cvtColor(img_rgba, cv2.COLOR_BGR2GRAY)
            _, alpha = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        # [REVERTED] No manual Erosion or Blur.
        # Relying on rembg alpha_matting for clean edges.
        
        # Apply mask back to image (Just ensures we have correct alpha buffer)
        img_rgba[:, :, 3] = alpha

        # 2. Find Contours (Islands)
        contours, hierarchy = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # No content? Return original rembg output
            return output_png
            
        # Filter tiny noise
        valid_contours = [c for c in contours if cv2.contourArea(c) > 5000] # Min area threshold (adjustable)
        
        if len(valid_contours) <= 1:
             # 0 or 1 character -> Good.
             return output_png
        
        print(f"[AutoCorret] Detected {len(valid_contours)} island characters. Keeping largest.")
        
        # 3. Multiple Characters Detected (The "Double Mom" Bug)
        # Select the Largest Area
        best_contour = max(valid_contours, key=cv2.contourArea)
        
        # Create a mask for the best contour
        mask = np.zeros_like(alpha)
        cv2.drawContours(mask, [best_contour], -1, 255, thickness=cv2.FILLED)
        
        # Apply mask to alpha channel
        # Everything outside the mask becomes transparent (0)
        img_rgba[:, :, 3] = cv2.bitwise_and(alpha, mask)
        
        # Encode back to bytes
        success, encoded_img = cv2.imencode(".png", img_rgba)
        if success:
            return encoded_img.tobytes()
        else:
            return output_png
            
    except Exception as e:
        print(f"Post-processing failed: {e}. Returning raw.")
        return image_bytes

def clean_image_file(input_path: str) -> str:
    """
    Reads an image from disk, cleans it (BG Remove + Erosion + Blur), 
    and saves it to a new path (appended _cleaned.png).
    Returns path to cleaned image.
    """
    if not input_path or not os.path.exists(input_path):
        return None
        
    try:
        # Check cache
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cleaned.png"
        
        if os.path.exists(output_path):
            return output_path
            
        with open(input_path, "rb") as f:
            raw_bytes = f.read()
            
        clean_bytes = process_character_output(raw_bytes)
        
        with open(output_path, "wb") as f:
            f.write(clean_bytes)
            
        print(f"[AutoClean] Cleaned {input_path} -> {output_path}")
        return output_path
    except Exception as e:
        print(f"[AutoClean] Failed to clean {input_path}: {e}")
        return input_path # Fallback
