from pathlib import Path
from typing import Optional, List
import re
import fitz  # PyMuPDF
from backend.app.core.paths import UPLOADS_DIR, RESULTS_DIR
from backend.app.models.schemas import AnalysisResult
from backend.app.core.logging_config import logger
from backend.app.services.result_manager import sanitize_paper_id

# Annotation Color Palettes (R, G, B floats in 0.0 - 1.0)
COLOR_GREEN = (0.13, 0.65, 0.34)      # Verified / Strongly related
COLOR_YELLOW = (0.92, 0.68, 0.08)     # Warning / Weak / Probable
COLOR_RED = (0.88, 0.22, 0.22)        # Unverified / Overclaim / Mismatch
COLOR_BLUE = (0.15, 0.45, 0.85)       # Standard reference marker / Banner

def generate_annotated_pdf(paper_id: str, result: AnalysisResult) -> Path:
    """
    Creates an annotated version of the uploaded PDF with exact color-coded highlights,
    bounding boxes, and review text sticky notes directly on the pages.
    """
    clean_id = sanitize_paper_id(paper_id)
    if isinstance(result, dict):
        result = AnalysisResult.model_validate(result)

    original_pdf_path = UPLOADS_DIR / f"{clean_id}.pdf"
    if not original_pdf_path.exists():
        raise FileNotFoundError(f"Original PDF not found for {clean_id}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_pdf_path = RESULTS_DIR / f"{clean_id}_annotated.pdf"

    doc = fitz.open(str(original_pdf_path))

    # 1. Add Professional Audit Header Banner on Page 1
    if len(doc) > 0:
        first_page = doc[0]
        summary = result.summary
        total_refs = summary.references_detected
        ver_count = summary.verified_exact + summary.verified_probable
        unver_count = summary.unverified
        overclaim_count = summary.overclaim_flags
        avg_score = (
            sum(r.verification.verification_score for r in result.references) / max(1, len(result.references))
            if result.references else 0.0
        )

        banner_text = (
            f"CITATION AUDIT REPORT | Integrity Score: {avg_score:.1f}/100 | "
            f"Verified: {ver_count}/{total_refs} | "
            f"Unverified: {unver_count} | Overclaims: {overclaim_count}\n"
            f"Green: Verified Source & Context | Yellow: Metadata Mismatch / Weak | Red: Unverified / Overclaim"
        )
        # Add banner box at top of page 1
        page_rect = first_page.rect
        banner_rect = fitz.Rect(36, 12, page_rect.width - 36, 42)
        banner_annot = first_page.add_rect_annot(banner_rect)
        banner_annot.set_colors(stroke=COLOR_BLUE, fill=(0.95, 0.97, 1.0))
        banner_annot.set_border(width=1.0)
        banner_annot.update()

        first_page.insert_textbox(
            banner_rect,
            banner_text,
            fontsize=7.5,
            fontname="helv",
            color=(0.1, 0.2, 0.45),
            align=fitz.TEXT_ALIGN_CENTER
        )

    # 2. Annotate in-text citations throughout the document pages
    for r in result.references:
        for occ in r.citation_occurrences:
            page_num = (occ.page - 1) if (occ.page and occ.page <= len(doc)) else None
            pages_to_search = [page_num] if page_num is not None else range(len(doc))

            # Determine color and review note based on verification and semantic analysis
            if occ.overclaim_flag:
                annot_color = COLOR_RED
                status_label = "OVERCLAIM REVIEW FLAG"
                review_note = (
                    f"[{status_label}]\n"
                    f"Reference: {r.marker or f'[{r.reference_id}]'}\n"
                    f"Issue: Conclusive claim without sufficient semantic support.\n"
                    f"Reason: {occ.overclaim_reason or 'Overclaim pattern detected.'}\n"
                    f"Context: \"{occ.sentence[:180]}...\"\n"
                    f"Cited Work: {r.external.title if r.external else 'Unverified'}"
                )
            elif occ.classification == "strongly_related":
                annot_color = COLOR_GREEN
                status_label = "VERIFIED CONTEXT (HIGH RELEVANCE)"
                review_note = (
                    f"[{status_label}]\n"
                    f"Reference: {r.marker or f'[{r.reference_id}]'}\n"
                    f"Semantic Similarity: {occ.semantic_similarity:.3f}\n"
                    f"Rank in Bibliography: #{occ.rank_among_references} of {occ.total_candidates}\n"
                    f"Verified Title: {r.external.title if r.external else 'N/A'}\n"
                    f"Source: {r.verification.source}"
                )
            elif occ.classification == "moderately_related":
                annot_color = COLOR_GREEN
                status_label = "VERIFIED CONTEXT (MODERATE)"
                review_note = (
                    f"[{status_label}]\n"
                    f"Reference: {r.marker or f'[{r.reference_id}]'}\n"
                    f"Semantic Similarity: {occ.semantic_similarity:.3f}\n"
                    f"Rank: #{occ.rank_among_references} of {occ.total_candidates}\n"
                    f"Verified Title: {r.external.title if r.external else 'N/A'}"
                )
            elif occ.classification in ["weakly_related", "likely_unrelated"]:
                annot_color = COLOR_YELLOW if occ.classification == "weakly_related" else COLOR_RED
                status_label = "POTENTIAL CITATION MISMATCH"
                top_alt = (occ.top_alternative_references[0].title if occ.top_alternative_references else 'None')
                review_note = (
                    f"[{status_label}]\n"
                    f"Reference: {r.marker or f'[{r.reference_id}]'}\n"
                    f"Low Semantic Similarity: {occ.semantic_similarity:.3f} ({occ.classification})\n"
                    f"Claim: \"{occ.sentence[:160]}...\"\n"
                    f"Closer Alternative Match: {top_alt}"
                )
            else:
                annot_color = COLOR_BLUE
                status_label = "CITATION CONTEXT"
                review_note = (
                    f"[{status_label}]\n"
                    f"Reference: {r.marker or f'[{r.reference_id}]'}\n"
                    f"Status: {r.verification.status.replace('_', ' ').title()}\n"
                    f"Score: {r.verification.verification_score}/100"
                )

            # Search and highlight on page
            for p_idx in pages_to_search:
                page = doc[p_idx]
                marker_query = occ.marker
                quads = page.search_for(marker_query)
                if not quads and "[" in marker_query:
                    # Try inner number search if bracket formatting slightly differed
                    inner = marker_query.replace("[", "").replace("]", "").strip()
                    quads = page.search_for(inner)

                if quads:
                    # Disambiguate which marker rect belongs to this occurrence using sentence context
                    clean_sent = re.sub(r'\[[0-9\s,\-–—]+\]', '', occ.sentence).strip()
                    # Extract a clean, distinctive phrase of 20-30 characters
                    words = [w for w in clean_sent.split() if len(w) > 3]
                    phrase = " ".join(words[:4]) if len(words) >= 4 else clean_sent[:30]
                    
                    matched_rect = quads[0]
                    if phrase:
                        sent_quads = page.search_for(phrase)
                        if sent_quads:
                            target_y = sent_quads[0].y0
                            # Pick marker rect closest in vertical position to the sentence phrase
                            matched_rect = min(quads, key=lambda q: abs(q.y0 - target_y))

                            # If this is an overclaim, highlight the claim phrase itself in soft red
                            if occ.overclaim_flag:
                                claim_highlight = page.add_highlight_annot(sent_quads[0])
                                claim_highlight.set_colors(stroke=COLOR_RED)
                                claim_highlight.set_info(
                                    title="Overclaim Context Flag",
                                    content=f"Claim phrasing flag: {occ.overclaim_reason or 'Overclaim pattern detected.'}"
                                )
                                claim_highlight.update()

                    highlight = page.add_highlight_annot(matched_rect)
                    highlight.set_colors(stroke=annot_color)
                    highlight.set_info(
                        title=f"Citation Verifier: {status_label}",
                        content=review_note
                    )
                    highlight.update()

                    # Add sticky review note right beside the highlight
                    point = fitz.Point(min(page.rect.width - 25, matched_rect.x1 + 4), matched_rect.y0)
                    text_annot = page.add_text_annot(point, review_note)
                    text_annot.set_colors(stroke=annot_color)
                    text_annot.set_info(title=status_label, content=review_note)
                    text_annot.update()
                    break

    # 3. Annotate bibliography references at the end of the document
    last_pages = range(max(0, len(doc) - 4), len(doc))
    for r in result.references:
        status = r.verification.status
        if status == "verified_exact":
            ref_color = COLOR_GREEN
            status_text = "VERIFIED EXACT MATCH"
        elif status == "verified_probable":
            ref_color = COLOR_GREEN
            status_text = "VERIFIED PROBABLE MATCH"
        elif status == "metadata_mismatch":
            ref_color = COLOR_YELLOW
            status_text = "METADATA MISMATCH DETECTED"
        else:
            ref_color = COLOR_RED
            status_text = "UNVERIFIED RECORD / POTENTIAL HALLUCINATION"

        ref_audit_note = (
            f"[{status_text}]\n"
            f"Verification Score: {r.verification.verification_score}/100\n"
            f"Title Sim: {(r.verification.title_similarity * 100):.0f}%\n"
            f"Source: {r.verification.source}\n"
            f"Matched Title: {r.external.title if r.external else 'None'}\n"
            f"DOI: {r.external.doi if r.external else (r.parsed.doi or 'None')}\n"
            f"Authors: {', '.join(r.external.authors[:3]) if (r.external and r.external.authors) else 'N/A'}"
        )

        # Prioritize distinctive title snippet before marker to ensure exact reference match
        queries = []
        if r.parsed and r.parsed.title and len(r.parsed.title) > 15:
            # First 28 chars of title
            queries.append(r.parsed.title[:28])
        if r.marker:
            queries.append(r.marker)
            inner = r.marker.replace("[", "").replace("]", "").strip()
            if inner:
                queries.append(f"{inner}. ")
                queries.append(f"{inner} ")

        found = False
        for p_idx in last_pages:
            page = doc[p_idx]
            for q in queries:
                quads = page.search_for(q)
                if quads:
                    rect = quads[0]
                    # Draw subtle surrounding rectangle
                    box = page.add_rect_annot(rect)
                    box.set_colors(stroke=ref_color)
                    box.set_border(width=1.5)
                    box.set_info(title=f"Ref #{r.reference_id}: {status_text}", content=ref_audit_note)
                    box.update()

                    # Add sticky text note
                    point = fitz.Point(min(page.rect.width - 25, rect.x1 + 6), rect.y0)
                    text_annot = page.add_text_annot(point, ref_audit_note)
                    text_annot.set_colors(stroke=ref_color)
                    text_annot.set_info(title=f"Ref #{r.reference_id}: {status_text}", content=ref_audit_note)
                    text_annot.update()
                    found = True
                    break
            if found:
                break

    doc.save(str(out_pdf_path), garbage=4, deflate=True)
    doc.close()
    logger.info(f"Generated annotated PDF report at {out_pdf_path}")
    return out_pdf_path
