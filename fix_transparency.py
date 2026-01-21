from PIL import Image
import os

def make_transparent(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    img = Image.open(path).convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    # Get corner color to assume as background
    bg_color = datas[0] # Top-left pixel
    threshold = 30 # Tolerance
    
    print(f"Processing {path}... BG assumed: {bg_color}")
    
    for item in datas:
        # Distance from bg color
        dist = sum([abs(item[i] - bg_color[i]) for i in range(3)])
        if dist < threshold:
            new_data.append((255, 255, 255, 0)) # Transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(path)
    print(f"Saved transparent: {path}")

base = "backend/assets/templates/mother_and_kid/v1/pages/p001"
make_transparent(os.path.join(base, "ref_child.png"))
make_transparent(os.path.join(base, "ref_mom.png"))
make_transparent(os.path.join(base, "bg.png")) # Just in case
