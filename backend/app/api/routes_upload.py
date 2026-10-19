import hashlib
import re
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
import fitz
from backend.app.core.config import settings
from backend.app.core.paths import UPLOADS_DIR
from backend.app.core.logging_config import logger
from backend.app.models.schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

def sanitize_filename(filename: str) -> str:
    """Removes path traversal components and illegal characters."""
    clean = Path(filename).name
    # Keep only alphanumeric, dots, dashes, underscores
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', clean)
    return clean or "document.pdf"

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Validates and stores an academic research paper PDF.
    Calculates SHA-256 and creates unique paper_id.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only machine-readable PDF files are accepted."
        )

    # Read content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read uploaded file content."
        )

    # Check zero-byte
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes)."
        )

    # Check size limit
    max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF size exceeds the maximum allowed limit of {settings.MAX_PDF_SIZE_MB} MB."
        )

    # Calculate SHA-256
    sha256_hash = hashlib.sha256(content).hexdigest()
    paper_id = sha256_hash[:16]
    clean_name = sanitize_filename(file.filename)

    # Validate PDF structure and page count using PyMuPDF
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        pages = len(doc)
        doc.close()
    except Exception as e:
        logger.error(f"Invalid PDF stream for {clean_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid or readable PDF document."
        )

    if pages == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The PDF contains zero pages."
        )

    # Store file to uploads directory
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOADS_DIR / f"{paper_id}.pdf"
    try:
        with open(destination, "wb") as f:
            f.write(content)
        # Also store original filename in metadata sidecar
        meta_file = UPLOADS_DIR / f"{paper_id}_meta.txt"
        with open(meta_file, "w", encoding="utf-8") as f:
            f.write(f"{clean_name}\n{sha256_hash}\n{pages}\n")
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store uploaded PDF to local storage."
        )

    logger.info(f"Uploaded PDF {clean_name} saved as paper_id={paper_id} ({pages} pages, {len(content)} bytes)")

    return UploadResponse(
        paper_id=paper_id,
        filename=clean_name,
        sha256=sha256_hash,
        pages=pages,
        status="uploaded",
        message="PDF uploaded and verified successfully."
    )
