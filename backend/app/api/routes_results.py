from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import FileResponse, PlainTextResponse
from backend.app.core.paths import RESULTS_DIR, CROSSREF_CACHE_DIR, SEMANTIC_SCHOLAR_CACHE_DIR, UPLOADS_DIR
from backend.app.services.result_manager import get_analysis_result, sanitize_paper_id
from backend.app.services.pdf_annotator import generate_annotated_pdf
from backend.app.core.logging_config import logger

router = APIRouter(prefix="/api", tags=["results"])

@router.get("/result/{paper_id}")
async def get_result(paper_id: str):
    """Returns the persistent JSON verification result for a paper."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    result = get_analysis_result(clean_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification result found for paper ID '{clean_id}'."
        )

    return result

@router.get("/report/{paper_id}/txt")
async def get_txt_report(paper_id: str):
    """Returns human-readable text report for export."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    report_path = RESULTS_DIR / f"{clean_id}_report.txt"
    if not report_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file not found for paper ID '{clean_id}'."
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(
            content=content,
            headers={
                "Content-Disposition": f'attachment; filename="{clean_id}_citation_report.txt"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read report: {str(e)}"
        )

@router.get("/report/{paper_id}/json")
async def get_json_report(paper_id: str):
    """Downloads JSON analysis result as a file."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    json_path = RESULTS_DIR / f"{clean_id}.json"
    if not json_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Result file not found for paper ID '{clean_id}'."
        )

    return FileResponse(
        path=str(json_path),
        media_type="application/json",
        filename=f"{clean_id}_citation_analysis.json"
    )

@router.get("/report/{paper_id}/annotated-pdf")
async def get_annotated_pdf(paper_id: str):
    """
    Generates and returns an annotated version of the uploaded PDF with
    color-coded visual highlights and review sticky text notes on each citation.
    """
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    annotated_path = RESULTS_DIR / f"{clean_id}_annotated.pdf"
    if not annotated_path.exists():
        result = get_analysis_result(clean_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis result found for paper '{clean_id}'."
            )
        try:
            annotated_path = generate_annotated_pdf(clean_id, result)
        except Exception as e:
            logger.error(f"Failed to generate annotated PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not generate annotated PDF: {str(e)}"
            )

    return FileResponse(
        path=str(annotated_path),
        media_type="application/pdf",
        filename=f"{clean_id}_annotated_audit.pdf"
    )

@router.get("/cache/status")
async def get_cache_status():
    """Returns local metadata cache status and metrics."""
    cr_count = len(list(CROSSREF_CACHE_DIR.glob("*.json"))) if CROSSREF_CACHE_DIR.exists() else 0
    s2_count = len(list(SEMANTIC_SCHOLAR_CACHE_DIR.glob("*.json"))) if SEMANTIC_SCHOLAR_CACHE_DIR.exists() else 0

    return {
        "status": "active",
        "crossref_cached_queries": cr_count,
        "semantic_scholar_cached_queries": s2_count,
        "total_cached_queries": cr_count + s2_count
    }
