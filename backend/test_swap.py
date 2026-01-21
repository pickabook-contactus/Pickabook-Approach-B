import os
import replicate
from dotenv import load_dotenv
import requests

# Load env for REPLICATE_API_TOKEN
load_dotenv(override=True)

def test_swap():
    try:
        # easel/advanced-face-swap (High Quality)
        MODEL_SLUG = "easel/advanced-face-swap" 
        print(f"Fetching latest version for {MODEL_SLUG}...")
        
        model = replicate.models.get(MODEL_SLUG)
        version = model.latest_version
        print(f"Using Version: {version.id}")

        # Paths
        target_path = "app/static/templates/page1.png"
        face_path = "uploads/5ae39266-7a5e-46b6-8172-2f82fcdfd343_Screenshot 2026-01-06 140147.jpg"

        if not os.path.exists(target_path):
            print(f"Error: Target path {target_path} not found.")
            return
        if not os.path.exists(face_path):
            style_prompt = "3d render, pixar style, disney character, acute features, vibrant, illustration style, white background"
            neg_prompt = "photorealistic, real photo, skin texture"
            
            print(f"Face path {face_path} not found. Generating character head...")
            gen_url = replicate.generate_character_head(
                photo_input=face_path, # Assuming face_path is the input for generation
                prompt_suffix=style_prompt,
                negative_prompt=neg_prompt
            )
            print(f"Generated character head URL: {gen_url}")
            # Assuming gen_url should now be used as the face_path for the swap
            face_path = gen_url # Update face_path to the generated URL
        
        print("Starting Swap (this may take a minute due to cold boot)...")
        
        # If face_path is a URL, we need to handle it differently than a local file
        if face_path.startswith("http://") or face_path.startswith("https://"):
            # Download the generated image to a temporary file
            print(f"Downloading generated face image from {face_path}...")
            r = requests.get(face_path)
            temp_face_path = "temp_generated_face.png" # Or a more robust temporary file name
            with open(temp_face_path, 'wb') as f:
                f.write(r.content)
            print(f"Generated face image saved to {temp_face_path}")
            face_file_obj = open(temp_face_path, "rb")
        else:
            face_file_obj = open(face_path, "rb")

        with open(target_path, "rb") as t, face_file_obj as f:
            output = replicate.run(
                f"{MODEL_SLUG}:{version.id}",
                input={
                    "target_image": t,
                    "swap_image": f,
                    "upscale": True,    # Enable Upscaling
                    "detailer": True    # Enable Detailer
                }
            )

        print(f"Raw Output: {output}")
        
        # Download output
        image_url = ""
        if isinstance(output, str):
            image_url = output
        elif isinstance(output, list) and len(output) > 0:
            image_url = output[0]
        elif hasattr(output, 'read'):
             image_url = str(output)

        if image_url:
            print(f"Downloading result from {image_url}...")
            r = requests.get(image_url)
            output_file = "easel_test_page1.png"
            with open(output_file, 'wb') as f:
                f.write(r.content)
            print(f"Success! Saved to {os.path.abspath(output_file)}")
        else:
            print("Failed to extract image URL from output.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_swap()
