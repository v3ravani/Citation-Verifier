import hashlib
from fastapi import APIRouter, HTTPException, status, Query
from backend.app.core.paths import UPLOADS_DIR
from backend.app.core.logging_config import logger
from backend.app.models.schemas import AnalysisResult
from backend.app.services.result_manager import get_analysis_result, sanitize_paper_id
from backend.app.services.progress_manager import get_progress, fail_progress
from backend.app.services.pipeline import run_verification_pipeline
from backend.app.pdf.extractor import ScannedPDFError, PDFExtractionError

router = APIRouter(prefix="/api", tags=["analysis"])

@router.get("/analyze/{paper_id}/progress")
async def get_analysis_progress_endpoint(paper_id: str):
    """
    Returns real-time verification progress including percentage, stage description,
    and reference counters.
    """
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )
    return get_progress(clean_id)

@router.post("/analyze/{paper_id}", response_model=AnalysisResult)
async def analyze_paper(paper_id: str, rerun: bool = Query(default=False)):
    """
    Executes or retrieves the complete citation verification pipeline for a paper.
    """
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    # If rerun is not requested, return cached result if already processed
    if not rerun:
        existing = get_analysis_result(clean_id)
        if existing:
            logger.info(f"Returning previously cached analysis for paper_id={clean_id}")
            return existing

    pdf_path = UPLOADS_DIR / f"{clean_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uploaded paper with ID '{clean_id}' was not found. Please upload the PDF first."
        )

    # Read original filename if sidecar exists
    filename = "document.pdf"
    sha256 = clean_id
    meta_path = UPLOADS_DIR / f"{clean_id}_meta.txt"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                if lines:
                    filename = lines[0]
                if len(lines) > 1:
                    sha256 = lines[1]
        except Exception:
            pass

    try:
        result = await run_verification_pipeline(
            paper_id=clean_id,
            filename=filename,
            sha256=sha256,
            pdf_path=pdf_path
        )
        return result
    except ScannedPDFError as e:
        logger.warning(f"Scanned PDF uploaded: {e}")
        fail_progress(clean_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except PDFExtractionError as e:
        logger.error(f"PDF extraction error for {clean_id}: {e}")
        fail_progress(clean_id, f"PDF extraction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text from PDF: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error analyzing paper {clean_id}: {e}")
        fail_progress(clean_id, f"Verification pipeline error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification pipeline failed: {str(e)}"
        )
