import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

UPLOAD_DIR = Path("uploads")
MAX_IMAGE_SIZE = 5 * 1024 * 1024  #5MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

FOLDERS = {
    "profile": UPLOAD_DIR / "profiles",
    "product": UPLOAD_DIR / "products",
    "review": UPLOAD_DIR / "reviews",
    "document": UPLOAD_DIR / "documents",
    "banner": UPLOAD_DIR / "banners",
}

# Create a folder if does not exists
for folders in FOLDERS.values():
    folders.mkdir(parents=True, exist_ok=True)

# ─── Validate ─────────────────────────────────────────────────────────────────

def validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise Exception(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"File type not allowed. Allowed: jpeg, png, webp"
        )

async def validate_image_size(file: UploadFile) -> bytes:
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is 5MB"
        )
    return contents

# ─── Upload ───────────────────────────────────────────────────────────────────

async def upload_image(file: UploadFile, folder: str) -> str:
    # validating
    validate_image(file)
    contents = await validate_image_size(file)
    
    # unique filename
    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    
    #save karo
    folder_path = FOLDERS.get(folder, UPLOAD_DIR)
    file_path = folder_path / filename
    
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    # URL return
    return f"/uploads/{folder}s/{filename}"

async def delete_image(url: str) -> None:
    if not url or url.startswith("http"):
        return # S3 URL hai — skip
    path = Path(url.lstrip("/"))
    if path.exists():
        path.unlink()


# ─── S3 placeholder — baad mein replace karenge ───────────────────────────────

async def upload_to_s3(file: UploadFile, folder: str) -> str:
    # TODO: AWS S3 implementation
    # import boto3
    # s3 = boto3.client('s3', ...)
    # s3.upload_fileobj(...)
    # return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    return await upload_image(file, folder)  # abhi local use karo