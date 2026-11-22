import hashlib
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

from fastapi import HTTPException, UploadFile
from cryptography.fernet import Fernet

from .config import settings

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg"}
EXTENSIONS = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}


async def save_upload(upload: UploadFile, user_id: str, document_id: str) -> tuple[str, int, str, Path]:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, PNG and JPEG medical documents are accepted")
    data = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB limit")
    extension = EXTENSIONS[upload.content_type]
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(upload.filename or "document").stem)[:60].strip("-")
    encrypted = bool(settings.file_encryption_key)
    stored_name = f"{user_id}/{document_id}-{safe_stem or 'document'}{extension}{'.enc' if encrypted else ''}"
    target = settings.storage_path / stored_name
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = Fernet(settings.file_encryption_key.encode()).encrypt(data) if settings.file_encryption_key else data
    target.write_bytes(payload)
    return stored_name, len(data), hashlib.sha256(data).hexdigest(), target


def document_path(stored_name: str) -> Path:
    path = (settings.storage_path / stored_name).resolve()
    root = settings.storage_path.resolve()
    if root not in path.parents:
        raise ValueError("Invalid storage path")
    return path


@contextmanager
def processing_file(stored_name: str):
    path = document_path(stored_name)
    if not stored_name.endswith(".enc"):
        yield path
        return
    if not settings.file_encryption_key:
        raise RuntimeError("FILE_ENCRYPTION_KEY is required to read this encrypted document")
    original_suffix = Path(stored_name.removesuffix(".enc")).suffix
    temporary = tempfile.NamedTemporaryFile(suffix=original_suffix, delete=False)
    try:
        temporary.write(Fernet(settings.file_encryption_key.encode()).decrypt(path.read_bytes()))
        temporary.close()
        yield Path(temporary.name)
    finally:
        temporary.close()
        Path(temporary.name).unlink(missing_ok=True)
