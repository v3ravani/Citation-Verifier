import os
import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

WOS_STARTER_URL = "https://api.clarivate.com/apis/wos-starter/v1/documents"

def parse_wos_doc(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Web of Science document record."""
    title = (item.get("title") or "").strip().rstrip(".")

    authors = []
    names = item.get("names", {}).get("authors", [])
    for n in names:
        wos_name = n.get("wosStandard") or n.get("displayName")
        if wos_name:
            authors.append(wos_name)

    year = None
    pub_year = item.get("source", {}).get("publishYear")
    if pub_year:
        try:
            year = int(pub_year)
        except (ValueError, TypeError):
            pass

    doi = item.get("identifiers", {}).get("doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = item.get("source", {}).get("sourceTitle") or "Web of Science Core Collection"
    citations = item.get("citations", {}).get("wos")

    url = f"https://doi.org/{clean_doi}" if clean_doi else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": None,
        "citation_count": citations,
        "url": url,
        "is_retracted": False,
        "source": "wos",
    }

async def fetch_wos_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches Web of Science record by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"wos:doi:{clean_doi}"
    cached = metadata_cache.get("wos", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "WOS_API_KEY", None) or os.getenv("WOS_API_KEY")
    if not key:
        return None

    headers = {"X-ApiKey": key, "Accept": "application/json"}
    params = {"q": f"DO={clean_doi}", "limit": 1}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(WOS_STARTER_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", [])
                if hits:
                    parsed = parse_wos_doc(hits[0])
                    metadata_cache.set("wos", cache_key, parsed, http_status=200)
                    logger.info(f"Web of Science DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"Web of Science lookup skipped ({e})")
        return None

async def search_wos_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Web of Science by title."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"wos:q:{clean_q.lower()}"
    cached = metadata_cache.get("wos", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "WOS_API_KEY", None) or os.getenv("WOS_API_KEY")
    if not key:
        return []

    headers = {"X-ApiKey": key, "Accept": "application/json"}
    params = {"q": f"TI=({clean_q})", "limit": min(limit, 3)}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(WOS_STARTER_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", [])
                items = [parse_wos_doc(h) for h in hits if h.get("title")]
                metadata_cache.set("wos", cache_key, items, http_status=200)
                logger.info(f"Web of Science search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"Web of Science search skipped ({e})")
        return []
