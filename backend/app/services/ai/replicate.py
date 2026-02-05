import replicate
from app.core.config import settings
import time
import os
from typing import Union, IO

def generate_character_head(
    photo_input: Union[str, IO], 
    prompt_suffix: str, 
    negative_prompt: str = "photorealistic, real photo, skin texture, pores, ugly, deformed, blurry, low quality"
) -> str:
    """
    Returns the URL of the generated image as a string.
    """
    import requests
    import tempfile

    if not settings.REPLICATE_API_TOKEN:
         raise ValueError("REPLICATE_API_TOKEN is not set")
    
    # Explicitly initialize client with token
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

    # HANDLE INPUT: Parse photo_input to ensure it's an accessible file/URL
    final_input = photo_input
    opened_file = None
    
    if isinstance(photo_input, str):
        # Case A: Localhost URL (Replicate can't reach this) -> Download it
        if "localhost" in photo_input or "127.0.0.1" in photo_input:
            print(f"Detected Localhost URL: {photo_input}. Downloading...")
            try:
                # If running in docker, localhost might refer to host? 
                # Hopefully container networking handles it or we need 'host.docker.internal'
                # But safer to assume we can access it if we are in same network
                # Actually, easier: If it's /uploads, map it to local file system if possible
                if "localhost" in photo_input or "127.0.0.1" in photo_input:
                    print(f"Detected Localhost URL: {photo_input}. converting to internal network...")
                    # Replace localhost with 'backend' for docker internal networking
                    internal_url = photo_input.replace("localhost", "backend").replace("127.0.0.1", "backend")
                    
                    print(f"Downloading from internal URL: {internal_url}")
                    try:
                        resp = requests.get(internal_url, timeout=10)
                        resp.raise_for_status()
                        
                        # Save to temp file
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        tf.write(resp.content)
                        tf.close()
                        
                        print(f"Saved temp input file to: {tf.name}")
                        opened_file = open(tf.name, "rb")
                        final_input = opened_file
                    except Exception as e:
                        print(f"Internal download FAILED: {e}. Url was: {internal_url}")
                        # CRITICAL: Do not silent fail. If we can't get the file, Replicate will fail anyway.
                        # Let's try one last desperate attempt using OS path if it matches /app/uploads
                        if "/uploads/" in photo_input:
                             local_fallback = os.path.join("/app", "uploads", photo_input.split("/uploads/")[-1])
                             if os.path.exists(local_fallback):
                                 print(f"Fallback: Found file locally at {local_fallback}")
                                 opened_file = open(local_fallback, "rb")
                                 final_input = opened_file
                             else:
                                 print("Fallback failed. Sending raw string (Will likely fail).")

            except Exception as e:
                print(f"Local map/network logic failed: {e}")

        # Case C: Local File Path -> Open it
        if isinstance(final_input, str) and not final_input.startswith("http"):
            # Strip file:// prefix if present
            click_path = final_input
            if click_path.startswith("file://"):
                click_path = click_path.replace("file://", "")
                
            if os.path.exists(click_path):
                 print(f"Opening local file path: {click_path}")
                 opened_file = open(click_path, "rb")
                 final_input = opened_file
            else:
                 print(f"Warning: File path does not exist: {click_path}")

    # FORCE CHECK: If final_input is still a localhost string, fail early
    if isinstance(final_input, str) and "localhost" in final_input:
        print("CRITICAL ERROR: final_input is still localhost URL. Replicate will reject this.")
    
    print(f"DEBUG: final_input type: {type(final_input)}")
    
    # Mock Mode
    if os.getenv("USE_MOCK_AI", "False").lower() == "true":
        print("Mock Mode: Simulating AI generation...")
        time.sleep(5)
        return "https://via.placeholder.com/500x500.png?text=Mock+AI+Generation"

    # Specific Model requested by User: ByteDance PuLID
    model_id = "bytedance/pulid:43d309c37ab4e62361e5e29b8e9e867fb2dcbcec77ae91206a8d95ac5dd451a0"

    # Construct the Full Prompt dynamically
    full_prompt = f"illustration of a happy child, {prompt_suffix}"

    # Helper for Retry Logic
    def run_with_retry(model, input_data, retries=3, delay=5):
        for attempt in range(retries):
            try:
                return client.run(model, input=input_data)
            except Exception as e:
                # Check for Rate Limit (429)
                error_str = str(e).lower()
                if "429" in error_str or "throttled" in error_str:
                    print(f"Rate Limit Hit (Attempt {attempt+1}/{retries}). Sleeping {delay}s...")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff
                else:
                    raise e
        raise Exception("Max Retry Attempts reached for Replicate Model")

    try:
        output = run_with_retry(
            model_id,
            input_data={
                "main_face_image": final_input,
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "identity_scale": 0.20, # V2.1 Snapshot: 0.20 (Vibe Only)
                "cfg_scale": 1.2, # V2.1 Snapshot: 3.0 (LIMIT 1.5 - Adjusted to 1.2 for safety)
                "num_steps": 30, # V2.1 Snapshot: 30
                "image_width": 1024,
                "image_height": 1024,
                "generation_mode": "fidelity"
            }
        )
        
        # 1. Output is usually a list of strings (URLs)
        if isinstance(output, list) and len(output) > 0:
            return str(output[0])
        
        # 2. Output might be a single string
        if isinstance(output, str):
            return output
            
        # 3. Fallback: Convert whatever it is to string (e.g. FileOutput object)
        # Note: If it's a FileOutput object, str() usually gives the URL or path.
        return str(output)

    except Exception as e:
        print(f"Replicate Error: {e}")
        # IMPORTANT: RAISE the error so the worker knows it failed!
        raise e

def swap_face(source_url: str, target_url: Union[str, IO]) -> str:
    """
    Swaps face from source_url into target_url using Replicate.
    Handles local file paths by opening them as streams.
    """
    print(f"DEBUG: swap_face called with source={str(source_url)[:50]}..., target={str(target_url)[:50]}...")
    
    # Helper for Retry Logic (Redefined here or moved to validation util if shared)
    def run_with_retry(model, input_data, retries=3, delay=5):
        for attempt in range(retries):
            try:
                return client.run(model, input=input_data)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "throttled" in error_str:
                    print(f"Swap Rate Limit Hit (Attempt {attempt+1}/{retries}). Sleeping {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e
        raise Exception("Max Retries for Swap")

    # Handle local file paths for source_url
    source_input = source_url
    opened_source_file = None
    opened_target_file = None # Track target too if needed (it is passed in open)
    temp_source_path = None
    
    if isinstance(source_url, str):
        if source_url.startswith("file://"):
            local_path = source_url.replace("file://", "")
            print(f"DEBUG: Opening local source file: {local_path}")
            opened_source_file = open(local_path, "rb")
            source_input = opened_source_file
        elif os.path.exists(source_url): # plain path
             print(f"DEBUG: Opening local source file: {source_url}")
             opened_source_file = open(source_url, "rb")
             source_input = opened_source_file
        elif source_url.startswith("http"):
             # FORCE DOWNLOAD to local temp to avoid Replicate URL issues
             import requests
             import tempfile
             print(f"DEBUG: Downloading source URL to temp file: {source_url}")
             try:
                 r = requests.get(source_url, stream=True)
                 r.raise_for_status()
                 tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                 for chunk in r.iter_content(chunk_size=8192): 
                     tf.write(chunk)
                 tf.close()
                 temp_source_path = tf.name
                 print(f"DEBUG: Source saved to {temp_source_path}")
                 opened_source_file = open(temp_source_path, "rb")
                 source_input = opened_source_file
             except Exception as dl_err:
                 print(f"Warning: Failed to download source URL: {dl_err}. Sending as URL.")

    # Log types
    print(f"DEBUG INPUTS: target_image type={type(target_url)}, swap_image type={type(source_input)}")
             
    try:
        if not settings.REPLICATE_API_TOKEN:
             raise ValueError("REPLICATE_API_TOKEN is not set")
        
        # Explicitly initialize client with token
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

        # Mock Mode
        if os.getenv("USE_MOCK_AI", "False").lower() == "true":
            print("Mock Mode: Simulating Cloud Face Swap...")
            time.sleep(3)
            return str(target_url) # Return original as mock result

        # ...
        output = client.run(
            "maker-space-2000/pulid-refined-face-swap:4c14de554b4247858c2807f61ad88fe04944d6739818ae9fb5e6924b43445cd7",
            input=input_data
        )

        # -------------------------------------------------------------------------
        # STAGE 1: Face Swap (Reliable but Low Res)
        # Using codeplugtech/face-swap which is stable
        # -------------------------------------------------------------------------
        print("STAGE 1: Swapping Face...")
        swap_model = client.models.get("codeplugtech/face-swap")
        swap_version = swap_model.latest_version
        swap_model_id = f"codeplugtech/face-swap:{swap_version.id}"
        
        swap_output = run_with_retry(
            swap_model_id,
            input_data={
                "input_image": target_url, 
                "swap_image": source_input,
                "enhance": False # CRITCAL: Disable Face Enhance (GFPGAN) to prevent realistic skin artifacts
            }
        )
        # Normalize Output
        swapped_url = None
        if isinstance(swap_output, str): swapped_url = swap_output
        elif isinstance(swap_output, list) and len(swap_output) > 0: swapped_url = swap_output[0]
        elif hasattr(swap_output, 'read'): swapped_url = str(swap_output)
        
        if not swapped_url:
            print("Stage 1 Failed: No swap output.")
            return None
            
        print(f"Stage 1 Complete: {swapped_url}")
        
        # STAGE 2: Upscaling [REMOVED by User Request]
        # Saving costs and preventing realism artifacts
        return swapped_url

    except Exception as e:
        print(f"Replicate Swap Error: {e}")
        raise e
    finally:
        if opened_source_file:
            print("Closing local source file...")
            opened_source_file.close()
            
        if temp_source_path and os.path.exists(temp_source_path):
             print(f"Removing temp source file: {temp_source_path}")
             try:
                 os.remove(temp_source_path)
             except:
                 pass

def refine_face_region(crop_path: str, source_face_url: str, prompt_suffix: str) -> str:
    """
    Refines a specific crop using InstantID (In-Place Generation).
    Uses the crop as 'ControlNet' input to keep layout, but re-paints pixels.
    """
    print(f"Refining Face Region: {crop_path} using Identity: {str(source_face_url)[:30]}...")
    print("DEBUG: Retry Logic Active v2") # Confirmation print
    
    # Helper for Retry Logic
    def run_with_retry(model, input_data, retries=3, delay=5):
        for attempt in range(retries):
            try:
                return client.run(model, input=input_data)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "throttled" in error_str:
                    print(f"Refine Rate Limit Hit (Attempt {attempt+1}/{retries}). Sleeping {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e
        raise Exception("Max Retries for Refine")
    
    # 1. Prepare Inputs (Handle Local/Remote)
    if not os.path.exists(crop_path):
        raise FileNotFoundError(f"Crop path not found: {crop_path}")
        
    opened_crop = open(crop_path, "rb")
    
    # Source Face (Identity)
    final_source = source_face_url
    opened_source = None
    
    if isinstance(source_face_url, str) and not source_face_url.startswith("http"):
         if source_face_url.startswith("file://"):
             clean = source_face_url.replace("file://", "")
             if os.path.exists(clean):
                 opened_source = open(clean, "rb")
                 final_source = opened_source
    
    # explicit client init for refine function too
    if not settings.REPLICATE_API_TOKEN:
         raise ValueError("REPLICATE_API_TOKEN is not set")
    client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)

    # Use standard InstantID for refinement as it supports ControlNet/Image input
    # dynamic fetch to avoid "Invalid Version" 422 errors
    try:
        model = client.models.get("zsxkib/instant-id")
        refine_model_id = f"zsxkib/instant-id:{model.latest_version.id}"
        print(f"DEBUG: Fetched latest Refine Model ID: {refine_model_id}")
    except Exception as e:
        print(f"Error fetching latest model version: {e}")
        # Fallback to a known hash if fetch fails (rare) or re-raise
        raise e
    
    # Use the "Happy" prompt logic
    full_prompt = f"illustration of a happy child, {prompt_suffix}"
    negative = "glasses, sunglasses, glasses marks, nose pads, shadow of glasses, sad eyes, crying eyes, spooky, deformed, blurry, bad anatomy"

    try:
        output = run_with_retry(
            refine_model_id,
            input_data={
                "image": opened_crop, # Control Image (The pasted crop)
                "face_image": final_source, # The Identity (Master Face)
                "prompt": full_prompt + ", perfect round eyes, large pupils", # Force Round Eyes
                "negative_prompt": negative + ", double eyebrows, multiple eyebrows, eyebrow shadows", # Ban Double Eyebrows
                "ip_adapter_scale": 0.30, # V2.1 Snapshot: 0.30 (Lowered)
                "control_strength": 0.30, # V2.1 Snapshot: 0.30 (Lowered)
                "identity_strength": 0.50, # Moderate default
                "num_inference_steps": 30,
                "guidance_scale": 3.0 # V2.1 Snapshot: 3.0
            }
        )
        
        if isinstance(output, list) and len(output) > 0:
            return str(output[0])
        elif isinstance(output, str):
            return output
            
        return str(output)
        
    except Exception as e:
        print(f"Refine Error: {e}")
        return None 
    finally:
        if opened_crop: opened_crop.close()
        if opened_source: opened_source.close()

def generate_character_variant(
    reference_image_path: str,
    identity_image_path: str,
    prompt: str,
    style_strength: float = 0.9,
    negative_prompt: str = ""
) -> str:
    """
    Generates a character variant using Google Gemini (via Replicate).
    - Passes [Identity, Reference] as separate images.
    - Prompt references them as Image 1 and Image 2.
    """
    import requests
    
    print(f"Generating Variant (Gemini). Ref={reference_image_path}, Identity={identity_image_path}")
    
    opened_files = []
    
    try:
        if not settings.REPLICATE_API_TOKEN:
             raise ValueError("REPLICATE_API_TOKEN is not set")
        
        client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
        
        # 1. Prepare Images as List [Image 1 (Identity), Image 2 (Reference)]
        # This matches the Prompt which says "Use Image 1 as Identity... Use Image 2 as Reference"
        
        # Identity (Image 1)
        id_path_clean = identity_image_path
        if isinstance(identity_image_path, str) and identity_image_path.startswith("file://"):
            id_path_clean = identity_image_path.replace("file://", "")
        
        f1 = open(id_path_clean, "rb")
        opened_files.append(f1)
        
        # Reference (Image 2)
        f2 = open(reference_image_path, "rb")
        opened_files.append(f2)
        
        images_list = [f1, f2]
        
        # Model ID - Dynamic Lookup based on User Specs
        # User confirmed: "google/gemini-2.5-flash-image"
        # Input Key: "image_input" (Array)
        model_name = "google/gemini-2.5-flash-image"
        
        full_model_id = model_name # Default
        try:
            model = client.models.get(model_name)
            version = model.latest_version
            full_model_id = f"{model_name}:{version.id}"
            print(f"Resolved Model Version: {full_model_id}")
        except Exception as e:
            print(f"Failed to resolve version for {model_name}: {e}")
            full_model_id = model_name
        
        print(f"--- [GEMINI] Generating Variant ---")
        print(f"Model: {full_model_id}")
        print(f"Input Count: {len(images_list)}")
        print(f"Prompt (First 200 chars): {prompt[:200]}...")
        print(f"Prompt (Last 200 chars): ...{prompt[-200:]}")
        
        output = client.run(
            full_model_id,
            input={
                "image_input": images_list, 
                "prompt": prompt + " (Vertical Portrait Layout, 3:4 Aspect Ratio)", 
                "safety_settings": "BLOCK_NONE",
                "safety_filter_level": "block_none",
                "aspect_ratio": "3:4"
            }
        )
        
        if isinstance(output, list) and len(output) > 0:
            return str(output[0])
        elif isinstance(output, str):
            return output
            
        return str(output)
        
    except Exception as e:
        print(f"Generate Variant (Gemini) Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        for f in opened_files:
            try: f.close()
            except: pass


