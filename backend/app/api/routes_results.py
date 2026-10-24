import datetime
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import FileResponse, PlainTextResponse
from backend.app.core.paths import RESULTS_DIR, CROSSREF_CACHE_DIR, SEMANTIC_SCHOLAR_CACHE_DIR, UPLOADS_DIR
from backend.app.services.result_manager import get_analysis_result, save_analysis_result, sanitize_paper_id
from backend.app.services.pdf_annotator import generate_annotated_pdf
from backend.app.services.report_generator import (
    generate_bibtex_export,
    generate_csv_export,
    generate_markdown_report,
    generate_html_report,
    generate_txt_report,
    save_txt_report
)
from backend.app.models.schemas import AnalysisResult
from backend.app.core.logging_config import logger

class UserVerificationPayload(BaseModel):
    verified: bool = True
    note: Optional[str] = None

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

@router.post("/result/{paper_id}/reference/{reference_id}/user-verify", response_model=AnalysisResult)
async def set_user_verification(
    paper_id: str,
    reference_id: int,
    payload: UserVerificationPayload
):
    """
    Allows a user to manually verify (or revert verification for) a reference.
    Updates the saved result, recalculates statistics, and clears cached artifacts.
    """
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid paper ID format."
        )

    result_data = get_analysis_result(clean_id)
    if not result_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification result found for paper ID '{clean_id}'."
        )

    result = AnalysisResult.model_validate(result_data)
    target_ref = next((r for r in result.references if r.reference_id == reference_id), None)
    if not target_ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference #{reference_id} not found in paper '{clean_id}'."
        )

    if payload.verified:
        if not target_ref.verification.original_status:
            target_ref.verification.original_status = target_ref.verification.status
        target_ref.verification.is_user_verified = True
        target_ref.verification.user_verification_note = payload.note
        target_ref.verification.user_verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        target_ref.verification.status = "user_verified"
        target_ref.verification.verification_score = max(target_ref.verification.verification_score, 100.0)
        target_ref.hallucination_risk = "LOW"
        user_note = f"Manually verified by user{': ' + payload.note if payload.note else ''}."
        if user_note not in target_ref.verification.notes:
            target_ref.verification.notes.insert(0, user_note)
    else:
        target_ref.verification.is_user_verified = False
        target_ref.verification.status = target_ref.verification.original_status or "unverified"
        target_ref.verification.user_verification_note = None
        target_ref.verification.user_verified_at = None

    # Recalculate summary stats
    v_exact = sum(1 for it in result.references if it.verification.status == "verified_exact")
    v_prob = sum(1 for it in result.references if it.verification.status == "verified_probable")
    v_user = sum(1 for it in result.references if it.verification.status == "user_verified" or it.verification.is_user_verified)
    v_mismatch = sum(1 for it in result.references if it.verification.status == "metadata_mismatch")
    v_unverif = sum(1 for it in result.references if it.verification.status == "unverified" and not it.verification.is_user_verified)
    v_api_unavail = sum(1 for it in result.references if it.verification.status == "api_unavailable")

    result.summary.verified_exact = v_exact
    result.summary.verified_probable = v_prob
    result.summary.user_verified = v_user
    result.summary.metadata_mismatch = v_mismatch
    result.summary.unverified = v_unverif
    result.summary.api_unavailable = v_api_unavail

    # Update graph nodes
    for node in result.graph.nodes:
        if node.id == f"ref_{reference_id}":
            node.status = target_ref.verification.status

    # Invalidate cached annotated PDF so it re-generates fresh on next download
    annotated_pdf = RESULTS_DIR / f"{clean_id}_annotated.pdf"
    if annotated_pdf.exists():
        try:
            annotated_pdf.unlink()
        except OSError:
            pass

    # Save updated analysis result
    save_analysis_result(clean_id, result)
    try:
        report_txt = generate_txt_report(result)
        save_txt_report(clean_id, report_txt)
    except Exception as e:
        logger.warning(f"Could not regenerate txt report: {e}")

    logger.info(f"User verification updated for paper {clean_id}, ref #{reference_id} -> verified={payload.verified}")
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

@router.get("/report/{paper_id}/bibtex")
async def get_bibtex_export(paper_id: str):
    """Generates and downloads clean BibTeX file for all verified references."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid paper ID format.")

    result_data = get_analysis_result(clean_id)
    if not result_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No result found for '{clean_id}'.")

    result = AnalysisResult.model_validate(result_data)
    bibtex_str = generate_bibtex_export(result)

    return Response(
        content=bibtex_str,
        media_type="application/x-bibtex",
        headers={"Content-Disposition": f'attachment; filename="{clean_id}_verified_references.bib"'}
    )

@router.get("/report/{paper_id}/csv")
async def get_csv_export(paper_id: str):
    """Generates and downloads CSV verification audit spreadsheet."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid paper ID format.")

    result_data = get_analysis_result(clean_id)
    if not result_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No result found for '{clean_id}'.")

    result = AnalysisResult.model_validate(result_data)
    csv_str = generate_csv_export(result)

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{clean_id}_citation_audit.csv"'}
    )

@router.get("/report/{paper_id}/markdown")
async def get_markdown_export(paper_id: str):
    """Generates and downloads executive Markdown audit report."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid paper ID format.")

    result_data = get_analysis_result(clean_id)
    if not result_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No result found for '{clean_id}'.")

    result = AnalysisResult.model_validate(result_data)
    md_str = generate_markdown_report(result)

    return Response(
        content=md_str,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{clean_id}_executive_report.md"'}
    )

@router.get("/report/{paper_id}/html")
async def get_html_report(paper_id: str):
    """Generates and displays standalone print-ready HTML audit dossier."""
    try:
        clean_id = sanitize_paper_id(paper_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid paper ID format.")

    result_data = get_analysis_result(clean_id)
    if not result_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No result found for '{clean_id}'.")

    result = AnalysisResult.model_validate(result_data)
    html_str = generate_html_report(result)

    return Response(
        content=html_str,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="{clean_id}_dossier.html"'}
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
