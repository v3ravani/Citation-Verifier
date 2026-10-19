from typing import List, Dict, Any
from backend.app.models.schemas import ParsedReference, CitationOccurrence
from backend.app.citations.normalizer import normalize_title

def match_author_year(citation_author: str, citation_year: int, ref: ParsedReference) -> bool:
    """
    Checks if an author-year citation matches a parsed reference.
    """
    if ref.year and citation_year and abs(ref.year - citation_year) > 1:
        return False
        
    clean_cit_author = citation_author.lower().replace("et al.", "").replace("et al", "").strip()
    author_tokens = [t.strip() for t in clean_cit_author.split() if len(t.strip()) > 2]
    
    # Check against parsed reference authors or raw text
    for token in author_tokens:
        for ref_author in ref.authors:
            if token in ref_author.lower():
                return True
        if token in ref.raw_text.lower():
            return True
            
    return False

def map_citations_to_references(
    raw_occurrences: List[Dict[str, Any]],
    references: List[ParsedReference]
) -> Dict[int, List[CitationOccurrence]]:
    """
    Maps extracted in-text citations to parsed bibliography references.
    
    Returns a dict: {reference_id: [CitationOccurrence, ...]}
    """
    mapped: Dict[int, List[CitationOccurrence]] = {r.reference_id: [] for r in references}
    ref_by_id = {r.reference_id: r for r in references}

    for occ in raw_occurrences:
        matched_ref_ids = set()
        
        if occ["type"] == "numeric":
            for target_id in occ["target_ids"]:
                if target_id in ref_by_id:
                    matched_ref_ids.add(target_id)
        else:
            # Author-year matching
            cit_authors = occ.get("target_authors", [])
            cit_year = occ.get("target_year")
            if cit_authors and cit_year:
                first_author = cit_authors[0]
                for ref in references:
                    if match_author_year(first_author, cit_year, ref):
                        matched_ref_ids.add(ref.reference_id)

        for ref_id in matched_ref_ids:
            occurrence_obj = CitationOccurrence(
                context_id=occ["context_id"],
                reference_id=ref_id,
                marker=occ["marker"],
                page=occ.get("page"),
                sentence=occ["sentence"],
                previous_sentence=occ.get("previous_sentence", ""),
                next_sentence=occ.get("next_sentence", ""),
                full_context=occ["full_context"],
                classification="unavailable"
            )
            mapped[ref_id].append(occurrence_obj)

    return mapped
