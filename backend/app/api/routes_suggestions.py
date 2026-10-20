from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.citation_suggester import (
    suggest_citations_for_paragraph,
    detect_citation_gaps_in_text,
    ParagraphSuggestionResponse,
    CitationGapsResponse
)
from backend.app.services.result_manager import get_extracted_text, sanitize_paper_id
from backend.app.core.logging_config import logger

router = APIRouter(prefix="/api", tags=["suggestions"])

class SuggestionRequest(BaseModel):
    text: str = Field(..., min_length=15, description="Paragraph or claim text to find citations for.")
    max_claims: Optional[int] = Field(default=3, ge=1, le=10)
    max_per_claim: Optional[int] = Field(default=5, ge=1, le=10)

class CitationGapRequest(BaseModel):
    paper_id: Optional[str] = None
    text: Optional[str] = None
    max_gaps: Optional[int] = Field(default=5, ge=1, le=10)

@router.post("/suggest-citations", response_model=ParagraphSuggestionResponse)
async def suggest_citations(req: SuggestionRequest):
    """
    Analyzes an input paragraph or claim, queries 6 global scholarly registries,
    computes Sentence-BERT semantic similarity, and generates citations formatted in IEEE, APA, and BibTeX.
    """
    try:
        response = await suggest_citations_for_paragraph(
            paragraph=req.text,
            max_claims=req.max_claims or 3,
            max_per_claim=req.max_per_claim or 5
        )
        return response
    except Exception as e:
        logger.error(f"Citation suggestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation suggestion failed: {str(e)}"
        )

@router.post("/detect-citation-gaps", response_model=CitationGapsResponse)
async def detect_citation_gaps(req: CitationGapRequest):
    """
    Scans a paper's text for assertive or factual statements that lack any citation markers,
    and returns relevant scholarly citations that the author should consider citing.
    """
    text_to_scan = req.text or ""
    if req.paper_id:
        try:
            clean_id = sanitize_paper_id(req.paper_id)
            extracted = get_extracted_text(clean_id)
            if extracted:
                text_to_scan = extracted
        except Exception as e:
            logger.warning(f"Failed to load extracted text for {req.paper_id}: {e}")

    if not text_to_scan or len(text_to_scan.strip()) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid paper text available to scan for citation gaps."
        )

    try:
        res = await detect_citation_gaps_in_text(text_to_scan, max_gaps=req.max_gaps or 5)
        res.paper_id = req.paper_id
        return res
    except Exception as e:
        logger.error(f"Citation gap detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Citation gap detection failed: {str(e)}"
        )
