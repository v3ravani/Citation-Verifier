from typing import Tuple, Optional, Dict, Any, List
from rapidfuzz import fuzz
from backend.app.models.schemas import ParsedReference, VerificationResult, ExternalRecord
from backend.app.citations.normalizer import normalize_title
from backend.app.metadata.crossref import fetch_crossref_by_doi, search_crossref_by_query
from backend.app.metadata.semantic_scholar import fetch_s2_by_doi, search_s2_by_query
from backend.app.metadata.openalex import fetch_openalex_by_doi, search_openalex_by_query
from backend.app.metadata.arxiv import extract_arxiv_id, fetch_arxiv_by_id
from backend.app.core.logging_config import logger

def compute_title_similarity(title1: Optional[str], title2: Optional[str]) -> float:
    """Computes normalized fuzzy similarity (0.0 to 1.0) between two titles."""
    if not title1 or not title2:
        return 0.0
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return 0.0
    score = fuzz.token_sort_ratio(norm1, norm2) / 100.0
    return round(score, 3)

def compute_author_match(parsed_authors: List[str], external_authors: List[str], raw_text: str) -> float:
    """Computes similarity of author lists."""
    if not external_authors:
        return 0.0

    if not parsed_authors:
        matches = 0
        for ext in external_authors[:3]:
            surname = ext.split()[-1].lower() if ext.split() else ""
            if len(surname) > 2 and surname in raw_text.lower():
                matches += 1
        return round(min(1.0, matches / max(1, min(len(external_authors), 3))), 2)

    first_ext = external_authors[0].split()[-1].lower() if external_authors[0].split() else ""
    first_parsed = parsed_authors[0].split()[-1].lower() if parsed_authors[0].split() else ""

    if first_ext and (first_ext in first_parsed or first_parsed in first_ext):
        return 1.0

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
    Verifies a parsed reference across Crossref, Semantic Scholar, OpenAlex, and arXiv.
    Synthesizes multi-source consensus.
    """
    crossref_item: Optional[Dict[str, Any]] = None
    s2_item: Optional[Dict[str, Any]] = None
    openalex_item: Optional[Dict[str, Any]] = None
    arxiv_item: Optional[Dict[str, Any]] = None

    # Step 1: Check for explicit arXiv ID
    arxiv_id = extract_arxiv_id(ref.raw_text)
    if arxiv_id:
        arxiv_item = await fetch_arxiv_by_id(arxiv_id)

    # Step 2: DOI lookup across Crossref, S2, and OpenAlex
    if ref.doi:
        crossref_item = await fetch_crossref_by_doi(ref.doi)
        s2_item = await fetch_s2_by_doi(ref.doi)
        openalex_item = await fetch_openalex_by_doi(ref.doi)

    # Step 3: Search queries if direct DOI match wasn't found
    if not any([crossref_item, s2_item, openalex_item, arxiv_item]):
        search_query = ref.title or ref.raw_text[:120]
        search_query = " ".join(search_query.split())
        if len(search_query) > 10:
            cr_results = await search_crossref_by_query(search_query, rows=2)
            if cr_results:
                crossref_item = cr_results[0]
            s2_results = await search_s2_by_query(search_query, limit=2)
            if s2_results:
                s2_item = s2_results[0]
            oa_results = await search_openalex_by_query(search_query, limit=2)
            if oa_results:
                openalex_item = oa_results[0]

    # Collect all available responses
    available_records = [r for r in [crossref_item, s2_item, openalex_item, arxiv_item] if r]

    if not available_records:
        return VerificationResult(
            status="unverified",
            source="none",
            title_similarity=0.0,
            author_match=0.0,
            year_match=None,
            doi_match=False if ref.doi else None,
            verification_score=0.0,
            notes=["No verified scholarly record found in Crossref, Semantic Scholar, OpenAlex, or arXiv."]
        ), None

    # Determine best record and merged attributes
    # Prioritize title from most detailed source
    primary = available_records[0]
    sources_matched = [r["source"] for r in available_records]
    source_label = "+".join(sources_matched)

    title = next((r["title"] for r in available_records if r.get("title")), "")
    authors = next((r["authors"] for r in available_records if r.get("authors")), [])
    year = next((r["year"] for r in available_records if r.get("year")), None)
    venue = next((r["venue"] for r in available_records if r.get("venue")), None)
    doi = next((r["doi"] for r in available_records if r.get("doi")), None)
    url = next((r["url"] for r in available_records if r.get("url")), None)
    # Prefer S2 or OpenAlex abstract
    abstract = (
        (s2_item.get("abstract") if s2_item else None) or
        (openalex_item.get("abstract") if openalex_item else None) or
        (arxiv_item.get("abstract") if arxiv_item else None) or
        (crossref_item.get("abstract") if crossref_item else None)
    )
    citation_count = (
        (s2_item.get("citation_count") if s2_item else None) or
        (openalex_item.get("citation_count") if openalex_item else None)
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

    title_sim = compute_title_similarity(ref.title or ref.raw_text, title)
    author_match = compute_author_match(ref.authors, authors, ref.raw_text)
    year_match = check_year_match(ref.year, year)
    doi_match = (
        (ref.doi.lower() == doi.lower()) if (ref.doi and doi)
        else (False if ref.doi and not doi else None)
    )

    notes = []
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

    # Classification
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
