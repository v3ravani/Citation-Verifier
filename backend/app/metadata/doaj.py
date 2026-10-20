import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

DOAJ_BASE_URL = "https://doaj.org/api/v2/search/articles"

def parse_doaj_article(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized publication metadata from a DOAJ article hit."""
    bib = item.get("bibjson", {})
    raw_title = bib.get("title") or ""
    title = raw_title.rstrip(".").strip()

    # Authors
    authors = []
    for a in bib.get("author", []):
        name = a.get("name", "").strip()
        if name:
            authors.append(name)

    # Year
    year = None
    y = bib.get("year")
    if y and str(y).isdigit():
        year = int(y)

    venue = bib.get("journal", {}).get("title")
    
    # DOI
    doi = None
    for ident in bib.get("identifier", []):
        if ident.get("type", "").lower() == "doi":
            doi = ident.get("id", "").strip().lower()
            break

    abstract = bib.get("abstract")
    
    # Link
    url = None
    for link in bib.get("link", []):
        if link.get("type") == "fulltext":
            url = link.get("url")
            break
    if not url and doi:
        url = f"https://doi.org/{doi}"

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": None,
        "url": url,
        "is_retracted": False,
        "is_doaj_indexed": True,
        "source": "doaj"
    }

async def fetch_doaj_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Look up Open Access peer-reviewed publication on DOAJ by DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"doaj:doi:{clean_doi}"
    cached = metadata_cache.get("doaj", cache_key)
    if cached is not None:
        return cached

    url = f"{DOAJ_BASE_URL}/doi:{clean_doi}"
    params = {"pageSize": 1}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    parsed = parse_doaj_article(results[0])
                    parsed["doi"] = parsed.get("doi") or clean_doi
                    metadata_cache.set("doaj", cache_key, parsed, http_status=200)
                    logger.info(f"DOAJ verified Open Access peer-reviewed record found for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying DOAJ for DOI {clean_doi}: {e}")
        return None

async def search_doaj_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches DOAJ verified Open Access literature by title query."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"doaj:query:{clean_query}:{limit}"
    cached = metadata_cache.get("doaj", cache_key)
    if cached is not None:
        return cached

    # Limit search query length for URL safety
    truncated_query = " ".join(clean_query.split()[:10])
    url = f"{DOAJ_BASE_URL}/{truncated_query}"
    params = {"pageSize": limit}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                parsed = [parse_doaj_article(r) for r in results if r.get("bibjson", {}).get("title")]
                metadata_cache.set("doaj", cache_key, parsed, http_status=200)
                logger.info(f"DOAJ search found {len(parsed)} results for query: {clean_query[:35]}")
                return parsed
            return []
    except Exception as e:
        logger.error(f"Error querying DOAJ for '{clean_query[:35]}': {e}")
        return []
