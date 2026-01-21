import replicate
from app.core.config import settings
import os
import time
from typing import Union, IO
from PIL import Image, ImageDraw

def create_mask(image_path_or_url: str, coords: dict) -> str:
    """
    Creates a black image with a white hole at the specified coordinates.
    Saves it locally and returns the path.
    coords: {"x": int, "y": int, "width": int, "angle": float}
    """
    try:
        # Load Original to get dimensions
        if image_path_or_url.startswith("http"):
            # If http, we might need requests, but for mask generation 
            # we just need size. Ideally should be local path.
            # Fallback size if remote: 1024x1024 (Risk)
            # Ideally tasks.py should download it first.
            width, height = 1024, 1024
        else:
            if image_path_or_url.startswith("file://"):
                image_path_or_url = image_path_or_url.replace("file://", "")
                
            with Image.open(image_path_or_url) as img:
                width, height = img.size
        
        # Create Mask
        # Black Background (Blocked)
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        # White Hole (Inpaint Here)
        # Handle Rotation? 
        # For now, simplistic box. If angle exists, we might need simple rotation.
        # But Inpainting usually handles rects well.
        
        x = coords.get("x", 0)
        y = coords.get("y", 0)
        w = coords.get("width", 200)
        # Assume square or calculate height using aspect ratio?
        # User JSON usually has "width" only for swapper.
        # We need a height. Let's assume generic face ratio 1:1.3 or square?
        # Let's use a Square for safely capturing the head area.
        h = w * 1.3 # Face aspect ratio
        
        # Draw White Ellipse or Rectangle? 
        # Ellipse fits faces better and blends easier.
        draw.ellipse((x, y, x + w, y + h), fill=255)
        
        # Save Mask
        output_dir = "uploads/masks"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = int(time.time())
        mask_path = os.path.join(output_dir, f"mask_{timestamp}.png")
        mask.save(mask_path)
        
        return mask_path
        
    except Exception as e:
        print(f"Mask Generation Error: {e}")
        return None

def inpaint_identity(page_url: str, identity_url: str, coords: dict, prompt: str = "child face, 3d render, pixar style, high quality") -> str:
    """
    Uses 'usamaehsan/controlnet-x-ip-adapter-realistic-vision-v5' to inpaint 
    the identity into the page at coordinates.
    """
    print(f"DEBUG: Inpainting Identity. Page: {page_url[:30]}..., Identity: {identity_url[:30]}...")
    
    if not settings.REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN is not set")

    # 1. Generate Mask Locally
    mask_path = create_mask(page_url, coords)
    if not mask_path:
        raise ValueError("Failed to generate inpainting mask")
        
    print(f"DEBUG: Mask generated at {mask_path}")
    
    try:
        # Prepare Inputs for Replicate
        # We need to open the mask file as binary stream for Replicate python client?
        # Or pass path if local?
        
        # We need to ensure inputs are handled correctly (Path vs URL)
        # Using open() for local files is safest.
        
        # Handle Page Input
        page_input = page_url
        if page_url.startswith("file://") or os.path.exists(page_url.replace("file://","")):
            clean_page_path = page_url.replace("file://", "")
            page_input = open(clean_page_path, "rb")
            
        # Handle Identity Input
        identity_input = identity_url
        if identity_url.startswith("file://") or os.path.exists(identity_url.replace("file://","")):
             clean_id_path = identity_url.replace("file://", "")
             identity_input = open(clean_id_path, "rb")
             
        # Handle Mask Input
        mask_input = open(mask_path, "rb")
        
        # 2. Call Replicate
        model = replicate.models.get("usamaehsan/controlnet-x-ip-adapter-realistic-vision-v5")
        version = model.latest_version
        
        output = replicate.run(
            f"usamaehsan/controlnet-x-ip-adapter-realistic-vision-v5:{version.id}",
            input={
                "prompt": prompt + ", 3d render, pixar style, disney style, digital art, toon shader",
                "negative_prompt": "photorealistic, real photo, photograph, detailed texture, skin pores, realistic, bad anatomy, deformed",
                "inpainting_image": page_input,
                "mask_image": mask_input,
                "ip_adapter_image": identity_input,
                "ip_adapter_weight": 0.85, # Stronger ID/Style transfer
                "num_inference_steps": 30,
                "guidance_scale": 8.0, # Higher guidance for prompt adherence
                "controlnet_conditioning_scale": 0.8
            }
        )
        
        # 3. Parse Output
        result_url = None
        if isinstance(output, list) and len(output) > 0:
            result_url = output[0]
        elif isinstance(output, str):
            result_url = output
            
        print(f"Inpainting Complete: {result_url}")
        return result_url

    except Exception as e:
        print(f"Inpainting Error: {e}")
        return None  # Or raise
