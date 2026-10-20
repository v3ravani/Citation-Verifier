import re
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from pydantic import BaseModel, Field
from backend.app.metadata.crossref import search_crossref_by_query
from backend.app.metadata.openalex import search_openalex_by_query
from backend.app.metadata.semantic_scholar import search_s2_by_query
from backend.app.metadata.arxiv import search_arxiv_by_query
from backend.app.metadata.europe_pmc import search_europe_pmc_by_query
from backend.app.metadata.dblp import search_dblp_by_query
from backend.app.metadata.datacite import search_datacite_by_query
from backend.app.metadata.pubmed import search_pubmed_by_query
from backend.app.metadata.doaj import search_doaj_by_query
from backend.app.metadata.hal import search_hal_by_query
from backend.app.nlp.embeddings import generate_embeddings
from backend.app.core.logging_config import logger

class SuggestedCitation(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    source: str = ""
    semantic_similarity: float = 0.0
    relevance_badge: str = "Supporting Context"
    ieee: str = ""
    apa: str = ""
    mla: str = ""
    chicago: str = ""
    bibtex: str = ""

class ClaimSuggestionResult(BaseModel):
    claim: str
    suggestions: List[SuggestedCitation]

class ParagraphSuggestionResponse(BaseModel):
    paragraph: str
    claims_analyzed: int
    results: List[ClaimSuggestionResult]

class TopicSearchResponse(BaseModel):
    query: str
    filter_mode: str
    total_found: int
    results: List[SuggestedCitation]

class CitationGapItem(BaseModel):
    sentence: str
    assertion_phrase: str
    suggestions: List[SuggestedCitation]

class CitationGapsResponse(BaseModel):
    paper_id: Optional[str] = None
    total_gaps_detected: int
    gaps: List[CitationGapItem]

def format_ieee(authors: List[str], title: str, venue: Optional[str], year: Optional[int], doi: Optional[str]) -> str:
    """Formats a bibliographic record in standard IEEE format."""
    auth_str = ""
    if authors:
        formatted = []
        for a in authors[:3]:
            parts = a.split()
            if len(parts) >= 2:
                initials = " ".join([f"{p[0]}." for p in parts[:-1]])
                formatted.append(f"{initials} {parts[-1]}")
            else:
                formatted.append(a)
        if len(authors) > 3:
            auth_str = f"{formatted[0]} et al."
        elif len(formatted) == 2:
            auth_str = f"{formatted[0]} and {formatted[1]}"
        else:
            auth_str = ", ".join(formatted)
    else:
        auth_str = "Anonymous"

    t = title.rstrip(".")
    v = f", {venue}" if venue else ""
    y = f", {year}" if year else ""
    d = f", doi: {doi}" if doi else ""
    return f'{auth_str}, "{t}"{v}{y}{d}.'

def format_apa(authors: List[str], title: str, venue: Optional[str], year: Optional[int], doi: Optional[str]) -> str:
    """Formats a bibliographic record in standard APA 7th format."""
    auth_str = ""
    if authors:
        formatted = []
        for a in authors[:5]:
            parts = a.split()
            if len(parts) >= 2:
                initials = " ".join([f"{p[0]}." for p in parts[:-1]])
                formatted.append(f"{parts[-1]}, {initials}")
            else:
                formatted.append(a)
        if len(authors) > 5:
            auth_str = f"{formatted[0]} et al."
        elif len(formatted) == 2:
            auth_str = f"{formatted[0]}, & {formatted[1]}"
        else:
            auth_str = ", ".join(formatted)
    else:
        auth_str = "Anonymous"

    y = f" ({year})" if year else " (n.d.)"
    t = f". {title.rstrip('.')}"
    v = f". {venue}" if venue else ""
    d = f". https://doi.org/{doi}" if doi else ""
    return f"{auth_str}{y}{t}{v}{d}."

def format_mla(authors: List[str], title: str, venue: Optional[str], year: Optional[int], doi: Optional[str]) -> str:
    """Formats a bibliographic record in MLA 9th edition format."""
    if not authors:
        auth_str = "Anonymous."
    elif len(authors) == 1:
        parts = authors[0].split()
        auth_str = f"{parts[-1]}, {' '.join(parts[:-1])}." if len(parts) >= 2 else f"{authors[0]}."
    elif len(authors) == 2:
        p1 = authors[0].split()
        p2 = authors[1]
        a1 = f"{p1[-1]}, {' '.join(p1[:-1])}" if len(p1) >= 2 else authors[0]
        auth_str = f"{a1}, and {p2}."
    else:
        parts = authors[0].split()
        a1 = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) >= 2 else authors[0]
        auth_str = f"{a1}, et al."

    v_str = f" *{venue}*," if venue else ""
    y_str = f" {year}." if year else ""
    d_str = f" DOI: https://doi.org/{doi}" if doi else ""
    return f'{auth_str} "{title.rstrip(".")}."{v_str}{y_str}{d_str}'.strip()

def format_chicago(authors: List[str], title: str, venue: Optional[str], year: Optional[int], doi: Optional[str]) -> str:
    """Formats a bibliographic record in Chicago 17th author-date format."""
    if not authors:
        auth_str = "Anonymous."
    else:
        parts = authors[0].split()
        auth_str = f"{parts[-1]}, {' '.join(parts[:-1])}." if len(parts) >= 2 else f"{authors[0]}."

    y_str = f" {year}." if year else " n.d."
    v_str = f" *{venue}*." if venue else ""
    d_str = f" https://doi.org/{doi}." if doi else ""
    return f'{auth_str}{y_str} "{title.rstrip(".")}."{v_str}{d_str}'.strip()

def format_bibtex(authors: List[str], title: str, venue: Optional[str], year: Optional[int], doi: Optional[str]) -> str:
    """Formats a bibliographic record in standard BibTeX @article or @inproceedings format."""
    first_author_surname = "author"
    if authors and authors[0]:
        first_author_surname = re.sub(r'[^a-zA-Z]', '', authors[0].split()[-1].lower())
    y_str = str(year) if year else "nodate"
    first_title_word = re.sub(r'[^a-zA-Z]', '', (title.split()[0] if title.split() else "paper").lower())
    cite_key = f"{first_author_surname}{y_str}{first_title_word}"

    auth_str = " and ".join(authors) if authors else "Anonymous"
    entry_type = "article" if venue and ("journal" in venue.lower() or "transactions" in venue.lower()) else "inproceedings"

    lines = [
        f"@{entry_type}{{{cite_key},",
        f"  author = {{{auth_str}}},",
        f"  title = {{{{{title}}}}},",
    ]
    if venue:
        lines.append(f"  journal = {{{venue}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    lines.append("}")
    return "\n".join(lines)

def extract_search_terms(sentence: str) -> str:
    """Extracts significant keywords for scholarly API search queries."""
    stopwords = {
        "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
        "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
        "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
        "we", "our", "us", "this", "that", "these", "those", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "would",
        "could", "might", "must", "show", "shows", "demonstrate", "study", "paper", "presents",
        "conclusively", "outperform", "outperforms", "better", "higher", "lower", "older", "novel"
    }
    words = re.findall(r'\b[A-Za-z0-9\-]{3,}\b', sentence)
    meaningful = [w for w in words if w.lower() not in stopwords]
    return " ".join(meaningful[:10])

def build_suggested_citation(rec: Dict[str, Any], sim: float = 0.5) -> SuggestedCitation:
    """Builds a complete SuggestedCitation object from an external record dictionary."""
    if sim >= 0.70:
        badge = "Highly Relevant"
    elif sim >= 0.50:
        badge = "Moderately Relevant"
    elif sim >= 0.35:
        badge = "Supporting Context"
    else:
        badge = "Peripheral Topic"

    title = rec.get("title") or "Untitled Publication"
    authors = rec.get("authors") or []
    year = rec.get("year")
    venue = rec.get("venue")
    doi = rec.get("doi")
    url = rec.get("url") or (f"https://doi.org/{doi}" if doi else None)
    abstract = rec.get("abstract")
    citation_count = rec.get("citation_count")
    source = rec.get("source") or "Academic Source"

    ieee = format_ieee(authors, title, venue, year, doi)
    apa = format_apa(authors, title, venue, year, doi)
    mla = format_mla(authors, title, venue, year, doi)
    chicago = format_chicago(authors, title, venue, year, doi)
    bibtex = format_bibtex(authors, title, venue, year, doi)

    return SuggestedCitation(
        title=title,
        authors=authors,
        year=year,
        venue=venue,
        doi=doi,
        url=url,
        abstract=abstract,
        citation_count=citation_count,
        source=source,
        semantic_similarity=round(sim, 3),
        relevance_badge=badge,
        ieee=ieee,
        apa=apa,
        mla=mla,
        chicago=chicago,
        bibtex=bibtex
    )

async def search_all_sources(query: str, limit_per_source: int = 3) -> List[Dict[str, Any]]:
    """Concurrently queries all 10 academic registries to assemble candidate literature."""
    tasks = await asyncio.gather(
        search_crossref_by_query(query, rows=limit_per_source),
        search_openalex_by_query(query, limit=limit_per_source),
        search_s2_by_query(query, limit=limit_per_source),
        search_arxiv_by_query(query, max_results=limit_per_source),
        search_europe_pmc_by_query(query, limit=limit_per_source),
        search_dblp_by_query(query, limit=limit_per_source),
        search_datacite_by_query(query, limit=limit_per_source),
        search_pubmed_by_query(query, limit=limit_per_source),
        search_doaj_by_query(query, limit=limit_per_source),
        search_hal_by_query(query, limit=limit_per_source),
        return_exceptions=True
    )

    candidates: Dict[str, Dict[str, Any]] = {}
    for t_res in tasks:
        if isinstance(t_res, Exception) or not t_res:
            continue
        for rec in t_res:
            key = (rec.get("doi") or rec.get("title") or "").strip().lower()
            if not key or len(key) < 5:
                continue
            if key not in candidates:
                candidates[key] = rec
            else:
                if not candidates[key].get("abstract") and rec.get("abstract"):
                    candidates[key]["abstract"] = rec.get("abstract")
                if not candidates[key].get("citation_count") and rec.get("citation_count"):
                    candidates[key]["citation_count"] = rec.get("citation_count")

    return list(candidates.values())

async def suggest_citations_for_paragraph(
    paragraph: str, max_claims: int = 3, max_per_claim: int = 5
) -> ParagraphSuggestionResponse:
    """
    Analyzes an input paragraph, identifies individual factual claims or topic sentences,
    searches all 10 academic registries, embeds claims with Sentence-BERT, and ranks citations.
    """
    cleaned = paragraph.strip()
    if not cleaned:
        return ParagraphSuggestionResponse(paragraph="", claims_analyzed=0, results=[])

    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    candidate_claims = [s.strip() for s in raw_sentences if len(s.strip()) >= 25]

    if not candidate_claims:
        candidate_claims = [cleaned[:300]]

    claims_to_process = candidate_claims[:max_claims]
    results: List[ClaimSuggestionResult] = []

    for claim in claims_to_process:
        query = extract_search_terms(claim)
        if not query or len(query) < 4:
            query = claim[:60]

        candidate_list = await search_all_sources(query, limit_per_source=3)
        if not candidate_list:
            results.append(ClaimSuggestionResult(claim=claim, suggestions=[]))
            continue

        texts_to_embed = [claim] + [
            f"{c.get('title') or ''}. {(c.get('abstract') or '')[:350]}" for c in candidate_list
        ]
        embeddings = generate_embeddings(texts_to_embed)

        claim_emb = embeddings[0]
        cand_embs = embeddings[1:]

        sim_scores = np.dot(cand_embs, claim_emb)
        suggestions: List[SuggestedCitation] = []
        for idx, rec in enumerate(candidate_list):
            sim = float(sim_scores[idx])
            sim = max(0.0, min(1.0, sim))
            suggestions.append(build_suggested_citation(rec, sim))

        suggestions.sort(key=lambda s: s.semantic_similarity, reverse=True)
        results.append(ClaimSuggestionResult(
            claim=claim,
            suggestions=suggestions[:max_per_claim]
        ))

    return ParagraphSuggestionResponse(
        paragraph=paragraph,
        claims_analyzed=len(results),
        results=results
    )

async def search_reference_recommendations(
    query: str,
    filter_mode: str = "general",
    limit: int = 8
) -> TopicSearchResponse:
    """
    Directly searches literature recommendations across all 10 scholarly registries.
    filter_mode can be 'general', 'seminal' (highest citations), 'recent' (>= 2022), or 'open_access'.
    """
    clean_q = " ".join(query.strip().split())
    if not clean_q:
        return TopicSearchResponse(query="", filter_mode=filter_mode, total_found=0, results=[])

    candidates = await search_all_sources(clean_q, limit_per_source=4)
    if not candidates:
        return TopicSearchResponse(query=clean_q, filter_mode=filter_mode, total_found=0, results=[])

    # Sentence-BERT embedding for semantic ranking against the user's research query
    texts = [clean_q] + [f"{c.get('title') or ''}. {(c.get('abstract') or '')[:350]}" for c in candidates]
    embs = generate_embeddings(texts)
    q_emb = embs[0]
    c_embs = embs[1:]

    sim_scores = np.dot(c_embs, q_emb)
    formatted: List[SuggestedCitation] = []
    for idx, c in enumerate(candidates):
        sim = float(sim_scores[idx])
        sim = max(0.0, min(1.0, sim))
        formatted.append(build_suggested_citation(c, sim))

    # Apply filters
    if filter_mode == "seminal":
        formatted.sort(key=lambda x: (x.citation_count or 0), reverse=True)
    elif filter_mode == "recent":
        formatted = [x for x in formatted if x.year and x.year >= 2022]
        formatted.sort(key=lambda x: (x.year or 0, x.semantic_similarity), reverse=True)
    elif filter_mode == "open_access":
        formatted = [x for x in formatted if x.source in ["doaj", "europe_pmc", "pubmed", "hal", "arxiv", "datacite"]]
        formatted.sort(key=lambda x: x.semantic_similarity, reverse=True)
    else:
        # Default: composite score (semantic similarity + citation boost)
        def composite(x: SuggestedCitation) -> float:
            c_boost = min(0.2, (x.citation_count or 0) / 1000.0 * 0.1)
            return x.semantic_similarity + c_boost
        formatted.sort(key=composite, reverse=True)

    top_results = formatted[:limit]
    return TopicSearchResponse(
        query=clean_q,
        filter_mode=filter_mode,
        total_found=len(top_results),
        results=top_results
    )

ASSERTIVE_GAP_PATTERNS = [
    r'\b(?:has\s+been\s+shown|have\s+been\s+shown|has\s+shown|have\s+shown)\b',
    r'\b(?:demonstrates?\s+that|demonstrated\s+that)\b',
    r'\b(?:studies\s+show|research\s+shows|previous\s+works?|prior\s+works?)\b',
    r'\b(?:proven\s+that|proves\s+that)\b',
    r'\b(?:it\s+is\s+well\s+known|it\s+is\s+widely\s+accepted)\b',
    r'\b(?:outperforms?\b|significantly\s+improves?)\b',
    r'\b(?:state-of-the-art\s+results?|benchmark\s+performance)\b',
    r'\b(?:conventional\s+methods?|traditional\s+approaches?)\b'
]

async def detect_citation_gaps_in_text(full_text: str, max_gaps: int = 5) -> CitationGapsResponse:
    """
    Scans document body text for assertive claims that lack any in-text citation markers,
    and queries scholarly indices to suggest authoritative supporting citations.
    """
    if not full_text:
        return CitationGapsResponse(total_gaps_detected=0, gaps=[])

    raw_sentences = re.split(r'(?<=[.!?])\s+', full_text)
    gap_candidates = []

    for s in raw_sentences:
        clean_s = s.strip()
        if len(clean_s) < 35 or len(clean_s) > 300:
            continue

        # Check if sentence already contains citation markers [1], (Smith, 2020), etc.
        if re.search(r'\[[0-9,\s\-–]+\]', clean_s) or re.search(r'\([A-Z][a-zA-Z\s,\.&]+,\s*(?:19|20)\d{2}\)', clean_s):
            continue

        for pat in ASSERTIVE_GAP_PATTERNS:
            m = re.search(pat, clean_s, re.IGNORECASE)
            if m:
                gap_candidates.append((clean_s, m.group(0)))
                break

    # Deduplicate and limit candidates
    unique_candidates = []
    seen = set()
    for sent, phrase in gap_candidates:
        if sent not in seen:
            seen.add(sent)
            unique_candidates.append((sent, phrase))
        if len(unique_candidates) >= max_gaps:
            break

    if not unique_candidates:
        return CitationGapsResponse(total_gaps_detected=0, gaps=[])

    # Suggest citations for each detected gap
    gaps: List[CitationGapItem] = []
    for sent, phrase in unique_candidates:
        resp = await suggest_citations_for_paragraph(sent, max_claims=1, max_per_claim=3)
        suggestions = resp.results[0].suggestions if resp.results else []
        gaps.append(CitationGapItem(
            sentence=sent,
            assertion_phrase=phrase,
            suggestions=suggestions
        ))

    return CitationGapsResponse(
        total_gaps_detected=len(gaps),
        gaps=gaps
    )
