from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.citation_suggester import (
    suggest_citations_for_paragraph,
    ParagraphSuggestionResponse
)
from backend.app.core.logging_config import logger

router = APIRouter(prefix="/api", tags=["suggestions"])

class SuggestionRequest(BaseModel):
    text: str = Field(..., min_length=15, description="Paragraph or claim text to find citations for.")
    max_claims: Optional[int] = Field(default=3, ge=1, le=10)
    max_per_claim: Optional[int] = Field(default=5, ge=1, le=10)

@router.post("/suggest-citations", response_model=ParagraphSuggestionResponse)
async def suggest_citations(req: SuggestionRequest):
    """
    Analyzes an input paragraph or claim, queries OpenAlex, Semantic Scholar, and arXiv,
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
