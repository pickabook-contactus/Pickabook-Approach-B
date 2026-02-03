import os
import mimetypes
from supabase import create_client, Client
from app.core.config import settings

class SupabaseService:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            print("WARNING: Supabase URL or Key not found in env.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)

    def upload_file(self, file_path: str, bucket_path: str, bucket_name: str = "pickabook-assets") -> str:
        """
        Uploads a file to Supabase Storage and returns the Public URL.
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found for upload: {file_path}")
            return None

        try:
            if not getattr(self, "supabase", None):
                print("[Supabase] Skipped: Client not initialized.")
                return None

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = "application/octet-stream"

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            print(f"[Supabase] Uploading {file_path} to {bucket_name}/{bucket_path}...")
            
            # Upload (Upsert=True to overwrite)
            response = self.supabase.storage.from_(bucket_name).upload(
                file=file_bytes,
                path=bucket_path,
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            
            # Get Public URL
            public_url = self.supabase.storage.from_(bucket_name).get_public_url(bucket_path)
            print(f"[Supabase] Upload Success: {public_url}")
            return public_url

        except Exception as e:
            print(f"[Supabase] Upload Failed: {e}")
            return None
