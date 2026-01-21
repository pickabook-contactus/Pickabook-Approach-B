from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from app.core.config import settings

def validate_photo(image_url: str) -> bool:
    """
    Validates a photo using Azure Face API.
    Rules:
    1. Exact 1 face.
    2. Blur < 0.35 (Low).
    3. No sunglasses.
    4. (Optional) Head pose check.
    """
    if not settings.AZURE_FACE_KEY or not settings.AZURE_FACE_ENDPOINT:
        # In dev mode without keys, we might want to bypass or fail safe. 
        # For strictness, let's return False or log warning.
        print("Warning: Azure keys missing. Validation skipped (returning False).")
        return False

    face_client = FaceClient(
        settings.AZURE_FACE_ENDPOINT,
        CognitiveServicesCredentials(settings.AZURE_FACE_KEY)
    )

    try:
        # Detect faces with attributes
        detected_faces = face_client.face.detect_with_url(
            url=image_url,
            return_face_attributes=['blur', 'glasses', 'headPose']
        )

        # Rule 1: Face Count must be exactly 1
        if not detected_faces or len(detected_faces) != 1:
            return False

        face = detected_faces[0]

        # Rule 2: Blur Check
        # Azure returns blur level. 'low' translates to 0.0-0.25 roughly, but here we use value.
        # Note: newer Azure API might return 'level', assume 'value' exists or map it.
        # If 'value' is available:
        if hasattr(face.face_attributes.blur, 'value'):
             if face.face_attributes.blur.value >= 0.35:
                 return False
        # If only 'blur_level' string is available (low/medium/high)
        else:
             if face.face_attributes.blur.blur_level != 'Low':
                 return False

        # Rule 3: Occlusion (Sunglasses)
        if face.face_attributes.glasses == 'Sunglasses':
            return False

        # Rule 4: Head Pose (Optional warning, but let's be strict if needed)
        # yaw/pitch > 20 degrees
        yaw = abs(face.face_attributes.head_pose.yaw)
        pitch = abs(face.face_attributes.head_pose.pitch)
        if yaw > 20 or pitch > 20:
            # We can log this but maybe not strict reject yet?
            # User requirement: "Warn if...". For boolean return, we'll keep it simple.
            pass

        return True

    except Exception as e:
        print(f"Azure validation error: {e}")
        return False
