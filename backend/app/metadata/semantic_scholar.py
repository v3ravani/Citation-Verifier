import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

PAPER_FIELDS = "title,authors,year,venue,abstract,citationCount,externalIds,url"

def parse_s2_paper(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Semantic Scholar paper record."""
    title = (item.get("title") or "").strip()
    authors = [a.get("name", "").strip() for a in item.get("authors", []) if a.get("name")]
    year = item.get("year")
    venue = item.get("venue")
    abstract = item.get("abstract")
    citation_count = item.get("citationCount")
    url = item.get("url")

    ext_ids = item.get("externalIds") or {}
    doi = ext_ids.get("DOI")

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "abstract": abstract,
        "citation_count": citation_count,
        "doi": doi,
        "url": url,
        "source": "semantic_scholar",
    }

async def fetch_s2_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches paper metadata from Semantic Scholar by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"doi:{clean_doi}"
    cached = metadata_cache.get("semantic_scholar", cache_key)
    if cached is not None:
        logger.info(f"Semantic Scholar cache hit for DOI: {clean_doi}")
        return cached

    url = f"{settings.SEMANTIC_SCHOLAR_BASE_URL.rstrip('/')}/paper/DOI:{clean_doi}"
    params = {"fields": PAPER_FIELDS}
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION}"
    }
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                parsed = parse_s2_paper(data)
                metadata_cache.set("semantic_scholar", cache_key, parsed, http_status=200)
                logger.info(f"Semantic Scholar lookup success for DOI: {clean_doi}")
                return parsed
            elif resp.status_code == 404:
                logger.info(f"Semantic Scholar paper not found for DOI: {clean_doi}")
                metadata_cache.set("semantic_scholar", cache_key, None, http_status=404)
                return None
            elif resp.status_code == 429:
                logger.warning(f"Semantic Scholar rate limit (429) hit for DOI: {clean_doi}")
                return None
            else:
                logger.warning(f"Semantic Scholar status {resp.status_code} for DOI: {clean_doi}")
                return None
    except Exception as e:
        logger.error(f"Error querying Semantic Scholar by DOI {clean_doi}: {e}")
        return None

async def search_s2_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches Semantic Scholar for papers matching query."""
    if not query or len(query.strip()) < 5:
        return []

    clean_query = " ".join(query.strip().split())
    cache_key = f"query:{clean_query}"
    cached = metadata_cache.get("semantic_scholar", cache_key)
    if cached is not None:
        logger.info(f"Semantic Scholar cache hit for query: {clean_query[:40]}...")
        return cached

    url = f"{settings.SEMANTIC_SCHOLAR_BASE_URL.rstrip('/')}/paper/search"
    params = {
        "query": clean_query,
        "limit": limit,
        "fields": PAPER_FIELDS,
    }
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION}"
    }
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                papers = data.get("data", [])
                results = [parse_s2_paper(p) for p in papers if p]
                metadata_cache.set("semantic_scholar", cache_key, results, http_status=200)
                logger.info(f"Semantic Scholar search found {len(results)} items for query: {clean_query[:40]}")
                return results
            elif resp.status_code == 429:
                logger.warning(f"Semantic Scholar rate limit (429) on search: {clean_query[:40]}")
                return []
            else:
                logger.warning(f"Semantic Scholar search status {resp.status_code} for {clean_query[:40]}")
                return []
    except Exception as e:
        logger.error(f"Error searching Semantic Scholar for {clean_query[:40]}: {e}")
        return []
