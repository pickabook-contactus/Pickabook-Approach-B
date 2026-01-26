from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.services.ai import replicate
import shutil
import os
import tempfile

router = APIRouter()

@router.post("/generate_avatar")
async def generate_avatar(
    prompt_suffix: str = Form(...),
    negative_prompt: str = Form("photorealistic, real photo, skin texture, pores, ugly, deformed, blurry, low quality, photograph, hyperrealistic"),
    file: UploadFile = File(...)
):
    """
    Directly calls the Replicate InstantID pipeline.
    Useful for testing prompts and styles via Swagger.
    """
    try:
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Call Replicate
        # We pass the file path directly since our service supports it
        url = replicate.generate_character_head(
            photo_input=tmp_path,
            prompt_suffix=prompt_suffix,
            negative_prompt=negative_prompt
        )

        # Cleanup
        os.unlink(tmp_path)

        return {"url": url}

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
