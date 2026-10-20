import re
from typing import List, Dict, Any, Optional
import numpy as np
from pydantic import BaseModel
from backend.app.metadata.openalex import search_openalex_by_query
from backend.app.metadata.semantic_scholar import search_s2_by_query
from backend.app.metadata.arxiv import search_arxiv_by_query
from backend.app.nlp.embeddings import generate_embeddings
from backend.app.core.logging_config import logger

class SuggestedCitation(BaseModel):
    title: str
    authors: List[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    source: str
    semantic_similarity: float
    relevance_badge: str
    ieee: str
    apa: str
    bibtex: str

class ClaimSuggestionResult(BaseModel):
    claim: str
    suggestions: List[SuggestedCitation]

class ParagraphSuggestionResponse(BaseModel):
    paragraph: str
    claims_analyzed: int
    results: List[ClaimSuggestionResult]

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
    # Remove common English stop words
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

async def suggest_citations_for_paragraph(paragraph: str, max_claims: int = 3, max_per_claim: int = 5) -> ParagraphSuggestionResponse:
    """
    Analyzes an input paragraph, identifies individual factual claims or topic sentences,
    searches academic databases (OpenAlex, Semantic Scholar, arXiv), embeds claims and candidate
    works with Sentence-BERT, ranks by semantic similarity, and generates citations.
    """
    cleaned = paragraph.strip()
    if not cleaned:
        return ParagraphSuggestionResponse(paragraph="", claims_analyzed=0, results=[])

    # Split into candidate sentences
    raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    candidate_claims = [s.strip() for s in raw_sentences if len(s.strip()) >= 25]

    if not candidate_claims:
        # If no punctuated sentences, treat entire text as one claim
        candidate_claims = [cleaned[:300]]

    claims_to_process = candidate_claims[:max_claims]
    results: List[ClaimSuggestionResult] = []

    for claim in claims_to_process:
        query = extract_search_terms(claim)
        if not query or len(query) < 4:
            query = claim[:60]

        # Multi-source concurrent querying
        oa_records = await search_openalex_by_query(query, limit=5)
        s2_records = await search_s2_by_query(query, limit=5)
        arxiv_records = await search_arxiv_by_query(query, max_results=3)

        # Deduplicate candidates across sources
        candidates: Dict[str, Dict[str, Any]] = {}

        for rec in (oa_records + s2_records + arxiv_records):
            key = (rec.get("doi") or rec.get("title") or "").strip().lower()
            if not key or len(key) < 5:
                continue
            if key not in candidates:
                candidates[key] = rec
            else:
                # Merge fields if missing
                if not candidates[key].get("abstract") and rec.get("abstract"):
                    candidates[key]["abstract"] = rec.get("abstract")
                if not candidates[key].get("citation_count") and rec.get("citation_count"):
                    candidates[key]["citation_count"] = rec.get("citation_count")

        candidate_list = list(candidates.values())
        if not candidate_list:
            results.append(ClaimSuggestionResult(claim=claim, suggestions=[]))
            continue

        # Compute semantic similarities using Sentence-BERT embeddings
        texts_to_embed = [claim] + [
            f"{c.get('title') or ''}. {(c.get('abstract') or '')[:350]}" for c in candidate_list
        ]
        embeddings = generate_embeddings(texts_to_embed)

        claim_emb = embeddings[0]
        cand_embs = embeddings[1:]

        # Cosine similarity (since embeddings are L2 normalized in generate_embeddings, dot product = cosine)
        sim_scores = np.dot(cand_embs, claim_emb)

        suggestions: List[SuggestedCitation] = []
        for idx, rec in enumerate(candidate_list):
            sim = float(sim_scores[idx])
            sim = max(0.0, min(1.0, sim))

            # Determine relevance badge
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
            bibtex = format_bibtex(authors, title, venue, year, doi)

            suggestions.append(SuggestedCitation(
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
                bibtex=bibtex
            ))

        # Sort descending by semantic similarity
        suggestions.sort(key=lambda s: s.semantic_similarity, reverse=True)
        top_suggestions = suggestions[:max_per_claim]

        results.append(ClaimSuggestionResult(
            claim=claim,
            suggestions=top_suggestions
        ))

    return ParagraphSuggestionResponse(
        paragraph=paragraph,
        claims_analyzed=len(results),
        results=results
    )
