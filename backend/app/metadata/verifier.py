import asyncio
import re
from typing import Tuple, Optional, Dict, Any, List
from rapidfuzz import fuzz
from backend.app.models.schemas import ParsedReference, VerificationResult, ExternalRecord
from backend.app.citations.normalizer import normalize_title
from backend.app.metadata.crossref import fetch_crossref_by_doi, search_crossref_by_query
from backend.app.metadata.semantic_scholar import fetch_s2_by_doi, search_s2_by_query
from backend.app.metadata.openalex import fetch_openalex_by_doi, search_openalex_by_query
from backend.app.metadata.arxiv import extract_arxiv_id, fetch_arxiv_by_id
from backend.app.metadata.europe_pmc import fetch_europe_pmc_by_doi, search_europe_pmc_by_query
from backend.app.metadata.dblp import fetch_dblp_by_doi, search_dblp_by_query
from backend.app.metadata.datacite import fetch_datacite_by_doi, search_datacite_by_query
from backend.app.core.logging_config import logger

def compute_title_similarity(title1: Optional[str], title2: Optional[str]) -> float:
    """Computes normalized fuzzy similarity (0.0 to 1.0) between two titles."""
    if not title1 or not title2:
        return 0.0
    
    # Strip leading citation numbers or bracket prefixes
    clean1 = re.sub(r'^(?:\[\d+\]|\d+\.|\d+\))\s*', '', title1).strip()
    clean2 = re.sub(r'^(?:\[\d+\]|\d+\.|\d+\))\s*', '', title2).strip()

    norm1 = normalize_title(clean1)
    norm2 = normalize_title(clean2)
    if not norm1 or not norm2:
        return 0.0

    # Token sort ratio handles rearranged words and sub-titles
    token_score = fuzz.token_sort_ratio(norm1, norm2) / 100.0
    partial_score = fuzz.partial_ratio(norm1, norm2) / 100.0
    
    # If one title is cleanly contained in the other and longer than 15 chars
    if len(norm1) >= 15 and len(norm2) >= 15:
        if norm1 in norm2 or norm2 in norm1:
            return round(max(token_score, 0.95), 3)

    combined = max(token_score, partial_score * 0.9)
    return round(combined, 3)

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
    Verifies a parsed reference across 7 scholarly registries:
    Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, and DataCite.
    Queries sources concurrently and synthesizes multi-source consensus.
    """
    crossref_item: Optional[Dict[str, Any]] = None
    s2_item: Optional[Dict[str, Any]] = None
    openalex_item: Optional[Dict[str, Any]] = None
    arxiv_item: Optional[Dict[str, Any]] = None
    europe_pmc_item: Optional[Dict[str, Any]] = None
    dblp_item: Optional[Dict[str, Any]] = None
    datacite_item: Optional[Dict[str, Any]] = None

    # Step 1: Check for explicit arXiv ID
    arxiv_id = extract_arxiv_id(ref.raw_text)
    if arxiv_id:
        arxiv_item = await fetch_arxiv_by_id(arxiv_id)

    # Step 2: Concurrent DOI lookup across all 6 DOI-indexed registries
    if ref.doi:
        doi_clean = ref.doi.strip().lower()
        results = await asyncio.gather(
            fetch_crossref_by_doi(doi_clean),
            fetch_s2_by_doi(doi_clean),
            fetch_openalex_by_doi(doi_clean),
            fetch_europe_pmc_by_doi(doi_clean),
            fetch_dblp_by_doi(doi_clean),
            fetch_datacite_by_doi(doi_clean),
            return_exceptions=True
        )
        if not isinstance(results[0], Exception) and results[0]:
            crossref_item = results[0]
        if not isinstance(results[1], Exception) and results[1]:
            s2_item = results[1]
        if not isinstance(results[2], Exception) and results[2]:
            openalex_item = results[2]
        if not isinstance(results[3], Exception) and results[3]:
            europe_pmc_item = results[3]
        if not isinstance(results[4], Exception) and results[4]:
            dblp_item = results[4]
        if not isinstance(results[5], Exception) and results[5]:
            datacite_item = results[5]

    # Step 3: Search queries if direct ID match wasn't found
    all_direct_records = [r for r in [crossref_item, s2_item, openalex_item, arxiv_item, europe_pmc_item, dblp_item, datacite_item] if r]
    if not all_direct_records:
        raw_query = ref.title or ref.raw_text[:120]
        # Clean leading brackets or numbers
        clean_q = re.sub(r'^(?:\[\d+\]|\d+\.|\d+\))\s*', '', raw_query).strip()
        search_query = " ".join(clean_q.split())
        if len(search_query) > 10:
            search_tasks = await asyncio.gather(
                search_crossref_by_query(search_query, rows=2),
                search_s2_by_query(search_query, limit=2),
                search_openalex_by_query(search_query, limit=2),
                search_europe_pmc_by_query(search_query, limit=2),
                search_dblp_by_query(search_query, limit=2),
                search_datacite_by_query(search_query, limit=2),
                return_exceptions=True
            )
            if not isinstance(search_tasks[0], Exception) and search_tasks[0]:
                crossref_item = search_tasks[0][0]
            if not isinstance(search_tasks[1], Exception) and search_tasks[1]:
                s2_item = search_tasks[1][0]
            if not isinstance(search_tasks[2], Exception) and search_tasks[2]:
                openalex_item = search_tasks[2][0]
            if not isinstance(search_tasks[3], Exception) and search_tasks[3]:
                europe_pmc_item = search_tasks[3][0]
            if not isinstance(search_tasks[4], Exception) and search_tasks[4]:
                dblp_item = search_tasks[4][0]
            if not isinstance(search_tasks[5], Exception) and search_tasks[5]:
                datacite_item = search_tasks[5][0]

    # Collect all available responses
    available_records = [
        r for r in [crossref_item, s2_item, openalex_item, arxiv_item, europe_pmc_item, dblp_item, datacite_item]
        if r
    ]

    if not available_records:
        return VerificationResult(
            status="unverified",
            source="none",
            title_similarity=0.0,
            author_match=0.0,
            year_match=None,
            doi_match=False if ref.doi else None,
            verification_score=0.0,
            notes=["No verified scholarly record found across Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, or DataCite."]
        ), None

    # Determine best record and merged attributes
    sources_matched = [r["source"] for r in available_records]
    source_label = "+".join(sources_matched)

    title = next((r["title"] for r in available_records if r.get("title")), "")
    authors = next((r["authors"] for r in available_records if r.get("authors")), [])
    year = next((r["year"] for r in available_records if r.get("year")), None)
    venue = next((r["venue"] for r in available_records if r.get("venue")), None)
    doi = next((r["doi"] for r in available_records if r.get("doi")), None)
    url = next((r["url"] for r in available_records if r.get("url")), None)
    
    # Retraction check across all sources
    is_retracted = any(r.get("is_retracted") for r in available_records)

    # Prefer S2, Europe PMC, OpenAlex, or arXiv for detailed abstract
    abstract = (
        (s2_item.get("abstract") if s2_item else None) or
        (europe_pmc_item.get("abstract") if europe_pmc_item else None) or
        (openalex_item.get("abstract") if openalex_item else None) or
        (arxiv_item.get("abstract") if arxiv_item else None) or
        (datacite_item.get("abstract") if datacite_item else None) or
        (crossref_item.get("abstract") if crossref_item else None)
    )
    citation_count = (
        (s2_item.get("citation_count") if s2_item else None) or
        (openalex_item.get("citation_count") if openalex_item else None) or
        (europe_pmc_item.get("citation_count") if europe_pmc_item else None)
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
        is_retracted=is_retracted,
        sources_verified=sources_matched,
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
    # Retraction alert note
    if is_retracted:
        notes.append("RETRACTION ALERT: This cited work is flagged as RETRACTED or subject to an expression of concern in academic databases.")

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

    # Multi-source consensus bonus
    if len(sources_matched) >= 2 and (doi_match or title_sim >= 0.85):
        score += 5.0
        notes.append(f"Multi-registry consensus confirmed across {len(sources_matched)} sources ({', '.join(sources_matched)}).")

    score = round(min(100.0, score), 1)

    # Classification
    if is_retracted:
        status = "metadata_mismatch"
    elif doi_match is True or (title_sim >= 0.88 and (year_match is not False) and author_match >= 0.5):
        status = "verified_exact"
    elif title_sim >= 0.78 and (year_match is not False or author_match >= 0.4):
        status = "verified_probable"
    elif title_sim >= 0.58:
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
