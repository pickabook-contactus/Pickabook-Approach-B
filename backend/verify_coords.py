from PIL import Image, ImageDraw
import os

def verify():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "app", "static", "templates", "child_can_be.png")
    output_dir = os.path.join(base_dir, "uploads", "debug_coords")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Loading template: {img_path}")
    
    try:
        with Image.open(img_path) as img:
            draw = ImageDraw.Draw(img)
            
            # Coords from stories.py
            x = 380
            y = 125
            w = 385
            h = int(w * 1.3) # Estimated face height ratio
            
            # Draw Red Box
            draw.rectangle([x, y, x+w, y+h], outline="red", width=5)
            
            output_path = os.path.join(output_dir, "verification_page.png")
            img.save(output_path)
            print(f"Verification image saved: {output_path}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
