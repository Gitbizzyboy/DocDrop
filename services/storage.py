import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "csv",
    "jpg", "jpeg", "png", "gif", "tiff", "bmp",
    "txt", "zip", "rar", "7z",
    "heic", "heif",
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, client_id: int) -> dict:
    """
    Save an uploaded file to disk.
    Returns a dict with filename, original_filename, file_size, mime_type.
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    client_folder = os.path.join(upload_folder, str(client_id))
    os.makedirs(client_folder, exist_ok=True)

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(client_folder, stored_filename)

    file.save(filepath)
    file_size = os.path.getsize(filepath)

    return {
        "filename": os.path.join(str(client_id), stored_filename),
        "original_filename": original_filename,
        "file_size": file_size,
        "mime_type": file.content_type or "application/octet-stream",
    }


def get_file_path(filename: str) -> str:
    """Return the absolute path for a stored filename."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return os.path.join(upload_folder, filename)


def delete_file(filename: str) -> bool:
    """Delete a file from storage. Returns True if deleted."""
    path = get_file_path(filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
