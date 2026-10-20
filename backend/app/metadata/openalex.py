import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

OPENALEX_BASE_URL = "https://api.openalex.org"

def reconstruct_openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstructs text from OpenAlex's abstract_inverted_index."""
    if not inverted_index:
        return None
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)
    except Exception:
        return None

def parse_openalex_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes an OpenAlex work object."""
    title = (item.get("title") or "").strip()
    
    authors = []
    for authorship in item.get("authorships", []):
        author_obj = authorship.get("author", {})
        display_name = author_obj.get("display_name", "").strip()
        if display_name:
            authors.append(display_name)

    year = item.get("publication_year")
    
    # Venue / Source
    primary_loc = item.get("primary_location") or {}
    source_obj = primary_loc.get("source") or {}
    venue = source_obj.get("display_name")
    
    # DOI
    raw_doi = item.get("doi") or ""
    clean_doi = raw_doi.replace("https://doi.org/", "").strip() if raw_doi else None

    # Abstract
    abstract = reconstruct_openalex_abstract(item.get("abstract_inverted_index"))

    citation_count = item.get("cited_by_count")
    url = item.get("doi") or primary_loc.get("landing_page_url")

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": citation_count,
        "url": url,
        "source": "openalex",
    }

async def fetch_openalex_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work metadata from OpenAlex by exact DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"openalex:doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    url = f"{OPENALEX_BASE_URL}/works/https://doi.org/{clean_doi}"
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                parsed = parse_openalex_work(data)
                metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                logger.info(f"OpenAlex lookup success for DOI: {clean_doi}")
                return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying OpenAlex by DOI {clean_doi}: {e}")
        return None

async def search_openalex_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches OpenAlex works by title or bibliographic string."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"openalex:query:{clean_query}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    url = f"{OPENALEX_BASE_URL}/works"
    params = {"search": clean_query, "per-page": limit}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = [parse_openalex_work(it) for it in data.get("results", [])]
                metadata_cache.set("crossref", cache_key, results, http_status=200)
                logger.info(f"OpenAlex search found {len(results)} items for query: {clean_query[:40]}")
                return results
            return []
    except Exception as e:
        logger.error(f"Error querying OpenAlex for {clean_query[:40]}: {e}")
        return []
