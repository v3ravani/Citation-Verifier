import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

DBLP_BASE_URL = "https://dblp.org/search/publ/api"

def parse_dblp_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a DBLP publication hit."""
    info = hit.get("info", {})
    raw_title = info.get("title") or ""
    title = raw_title.rstrip(".").strip()

    # Authors in DBLP can be single dict, list of dicts, or string
    authors = []
    author_obj = info.get("authors", {}).get("author")
    if isinstance(author_obj, list):
        for a in author_obj:
            if isinstance(a, dict):
                authors.append(a.get("text", "").strip())
            elif isinstance(a, str):
                authors.append(a.strip())
    elif isinstance(author_obj, dict):
        authors.append(author_obj.get("text", "").strip())
    elif isinstance(author_obj, str):
        authors.append(author_obj.strip())

    year = None
    y_str = info.get("year")
    if y_str and str(y_str).isdigit():
        year = int(y_str)

    venue = info.get("venue")
    doi = info.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    # Electronic edition link or DBLP URL
    url = info.get("ee") or info.get("url")
    if clean_doi and not url:
        url = f"https://doi.org/{clean_doi}"

    return {
        "title": title,
        "authors": [a for a in authors if a],
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": None,  # DBLP does not host full abstracts
        "citation_count": None,
        "url": url,
        "is_retracted": False,
        "source": "dblp"
    }

async def fetch_dblp_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches DBLP record by exact DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"dblp:doi:{clean_doi}"
    cached = metadata_cache.get("dblp", cache_key)
    if cached is not None:
        return cached

    url = DBLP_BASE_URL
    params = {"q": f"doi:{clean_doi}", "format": "json", "h": 1}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                if hits:
                    parsed = parse_dblp_hit(hits[0])
                    metadata_cache.set("dblp", cache_key, parsed, http_status=200)
                    logger.info(f"DBLP match found for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying DBLP by DOI {clean_doi}: {e}")
        return None

async def search_dblp_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches DBLP Computer Science Bibliography by query."""
    if not query or len(query.strip()) < 4:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"dblp:query:{clean_query}:{limit}"
    cached = metadata_cache.get("dblp", cache_key)
    if cached is not None:
        return cached

    url = DBLP_BASE_URL
    params = {"q": clean_query, "format": "json", "h": limit}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                parsed = [parse_dblp_hit(h) for h in hits if h.get("info", {}).get("title")]
                metadata_cache.set("dblp", cache_key, parsed, http_status=200)
                logger.info(f"DBLP search found {len(parsed)} results for query: {clean_query[:40]}")
                return parsed
            return []
    except Exception as e:
        logger.error(f"Error querying DBLP for '{clean_query[:40]}': {e}")
        return []
