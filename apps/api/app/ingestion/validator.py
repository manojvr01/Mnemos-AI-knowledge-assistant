import hashlib
from typing import Tuple

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Magic byte signatures
PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"

SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def validate_file(filename: str, content: bytes) -> Tuple[str, str]:
    """
    Validate file extension, size, and magic signature.
    Returns (normalized_mime_type, sha256_hash).
    Raises ValueError on validation failure.
    """
    # 1. Size check
    file_size = len(content)
    if file_size == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds maximum permitted limit of 50 MB ({file_size} bytes).")

    # 2. Extension check
    lower_filename = filename.lower()
    matched_ext = None
    for ext, mime in SUPPORTED_EXTENSIONS.items():
        if lower_filename.endswith(ext):
            matched_ext = ext
            break

    if not matched_ext:
        allowed = ", ".join(SUPPORTED_EXTENSIONS.keys())
        raise ValueError(f"Unsupported file format '{filename}'. Allowed formats: {allowed}")

    # 3. Magic signature verification
    if matched_ext == ".pdf":
        if not content.startswith(PDF_MAGIC):
            raise ValueError("Corrupted or invalid PDF file header (missing %PDF- magic signature).")
        mime_type = "application/pdf"

    elif matched_ext == ".docx":
        if not content.startswith(DOCX_MAGIC):
            raise ValueError("Corrupted or invalid DOCX file header (missing PK zip signature).")
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif matched_ext == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("latin-1")
            except Exception as e:
                raise ValueError("Text file could not be decoded as valid UTF-8 or ASCII.") from e
        mime_type = "text/plain"
    else:
        raise ValueError(f"Unsupported extension: {matched_ext}")

    # 4. Cryptographic SHA-256 hash
    sha256 = hashlib.sha256(content).hexdigest()

    return mime_type, sha256
