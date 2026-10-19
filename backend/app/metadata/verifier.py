from typing import Tuple, Optional, Dict, Any, List
from rapidfuzz import fuzz
from backend.app.models.schemas import ParsedReference, VerificationResult, ExternalRecord
from backend.app.citations.normalizer import normalize_title
from backend.app.metadata.crossref import fetch_crossref_by_doi, search_crossref_by_query
from backend.app.metadata.semantic_scholar import fetch_s2_by_doi, search_s2_by_query
from backend.app.core.logging_config import logger

def compute_title_similarity(title1: Optional[str], title2: Optional[str]) -> float:
    """Computes normalized fuzzy similarity (0.0 to 1.0) between two titles."""
    if not title1 or not title2:
        return 0.0
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return 0.0
    # Token sort ratio handles word reordering and subtitle differences well
    score = fuzz.token_sort_ratio(norm1, norm2) / 100.0
    return round(score, 3)

def compute_author_match(parsed_authors: List[str], external_authors: List[str], raw_text: str) -> float:
    """Computes similarity of author lists."""
    if not external_authors:
        return 0.0

    # If we didn't parse author names, check if external author surnames appear in raw_text
    if not parsed_authors:
        matches = 0
        for ext in external_authors[:3]:
            surname = ext.split()[-1].lower() if ext.split() else ""
            if len(surname) > 2 and surname in raw_text.lower():
                matches += 1
        return round(min(1.0, matches / max(1, min(len(external_authors), 3))), 2)

    # Compare first author surname
    first_ext = external_authors[0].split()[-1].lower() if external_authors[0].split() else ""
    first_parsed = parsed_authors[0].split()[-1].lower() if parsed_authors[0].split() else ""

    if first_ext and (first_ext in first_parsed or first_parsed in first_ext):
        return 1.0

    # Token match across all authors
    matches = 0
    for p in parsed_authors:
        p_surname = p.split()[-1].lower() if p.split() else ""
        for ext in external_authors:
            ext_surname = ext.split()[-1].lower() if ext.split() else ""
            if p_surname and ext_surname and (p_surname in ext_surname or ext_surname in p_surname):
                matches += 1
                break

    return round(min(1.0, matches / max(1, min(len(parsed_authors), len(external_authors)))), 2)

def check_year_match(parsed_year: Optional[int], external_year: Optional[int]) -> Optional[bool]:
    """Checks if publication years match within 1 year margin."""
    if parsed_year is None or external_year is None:
        return None
    return abs(parsed_year - external_year) <= 1

async def verify_reference(
    ref: ParsedReference
) -> Tuple[VerificationResult, Optional[ExternalRecord]]:
    """
    Verifies a parsed reference against Crossref and Semantic Scholar APIs.
    Returns (VerificationResult, Optional[ExternalRecord]).
    """
    crossref_item: Optional[Dict[str, Any]] = None
    s2_item: Optional[Dict[str, Any]] = None

    # Step 1: DOI lookup if available
    if ref.doi:
        crossref_item = await fetch_crossref_by_doi(ref.doi)
        s2_item = await fetch_s2_by_doi(ref.doi)

    # Step 2: Query search if no DOI match
    if not crossref_item and not s2_item:
        search_query = ref.title or ref.raw_text[:120]
        # Clean query
        search_query = " ".join(search_query.split())
        if len(search_query) > 10:
            cr_results = await search_crossref_by_query(search_query, rows=2)
            if cr_results:
                crossref_item = cr_results[0]
            s2_results = await search_s2_by_query(search_query, limit=2)
            if s2_results:
                s2_item = s2_results[0]

    # If neither returned anything
    if not crossref_item and not s2_item:
        return VerificationResult(
            status="unverified",
            source="none",
            title_similarity=0.0,
            author_match=0.0,
            year_match=None,
            doi_match=False if ref.doi else None,
            verification_score=0.0,
            notes=["No verified scholarly record found in Crossref or Semantic Scholar."]
        ), None

    # Select primary external record and synthesize best fields
    primary = crossref_item or s2_item or {}
    secondary = s2_item if primary == crossref_item else crossref_item

    title = primary.get("title") or (secondary.get("title") if secondary else "")
    authors = primary.get("authors") or (secondary.get("authors") if secondary else [])
    year = primary.get("year") or (secondary.get("year") if secondary else None)
    venue = primary.get("venue") or (secondary.get("venue") if secondary else None)
    doi = primary.get("doi") or (secondary.get("doi") if secondary else None)
    url = primary.get("url") or (secondary.get("url") if secondary else None)
    # Prefer S2 abstract because S2 has cleaner extracted abstracts
    abstract = (s2_item.get("abstract") if s2_item else None) or (crossref_item.get("abstract") if crossref_item else None)
    citation_count = s2_item.get("citation_count") if s2_item else None

    source_label = "crossref" if (crossref_item and not s2_item) else (
        "semantic_scholar" if (s2_item and not crossref_item) else "crossref+semantic_scholar"
    )

    external_rec = ExternalRecord(
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        venue=venue,
        abstract=abstract,
        citation_count=citation_count,
        url=url,
        source=source_label
    )

    # Compute comparison metrics
    title_sim = compute_title_similarity(ref.title or ref.raw_text, title)
    author_match = compute_author_match(ref.authors, authors, ref.raw_text)
    year_match = check_year_match(ref.year, year)
    doi_match = (
        (ref.doi.lower() == doi.lower()) if (ref.doi and doi)
        else (False if ref.doi and not doi else None)
    )

    notes = []
    # Scoring computation
    score = 0.0
    if doi_match is True:
        score += 35.0
    elif ref.doi and doi_match is False:
        notes.append(f"DOI mismatch: extracted {ref.doi} vs record {doi}")

    score += title_sim * 40.0

    if author_match >= 0.8:
        score += 15.0
    elif author_match >= 0.4:
        score += 8.0
    else:
        if ref.authors and authors:
            notes.append("Author list difference detected.")

    if year_match is True:
        score += 10.0
    elif year_match is False:
        notes.append(f"Year mismatch: extracted {ref.year} vs record {year}")

    score = round(min(100.0, score), 1)

    # Determine classification
    if doi_match is True or (title_sim >= 0.90 and (year_match is not False) and author_match >= 0.6):
        status = "verified_exact"
    elif title_sim >= 0.80 and (year_match is not False or author_match >= 0.4):
        status = "verified_probable"
    elif title_sim >= 0.60:
        status = "metadata_mismatch"
        notes.append("Probable title match with conflicting bibliographic metadata.")
    else:
        status = "unverified"
        notes.append("Low title similarity; record could not be confirmed.")

    verification_res = VerificationResult(
        status=status,
        source=source_label,
        title_similarity=title_sim,
        author_match=author_match,
        year_match=year_match,
        doi_match=doi_match,
        verification_score=score,
        notes=notes
    )

    return verification_res, external_rec
