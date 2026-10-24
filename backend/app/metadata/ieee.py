import os
import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

IEEE_API_BASE = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

def parse_ieee_article(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes an IEEE Xplore article object."""
    title = (item.get("title") or "").strip().rstrip(".")

    authors = []
    author_list = item.get("authors", {}).get("authors", [])
    for a in author_list:
        name = a.get("full_name") or f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
        if name:
            authors.append(name)

    year = item.get("publication_year")
    if year:
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = None

    doi = item.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = item.get("publication_title") or "IEEE Xplore Digital Library"
    abstract = item.get("abstract")
    url = item.get("html_url") or (f"https://doi.org/{clean_doi}" if clean_doi else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": item.get("citing_paper_count"),
        "url": url,
        "is_retracted": False,
        "source": "ieee",
    }

async def fetch_ieee_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches IEEE publication by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"ieee:doi:{clean_doi}"
    cached = metadata_cache.get("ieee", cache_key)
    if cached is not None:
        return cached

    api_key = getattr(settings, "IEEE_API_KEY", None) or os.getenv("IEEE_API_KEY")
    if not api_key:
        return None

    params = {"doi": clean_doi, "apikey": api_key, "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(IEEE_API_BASE, params=params)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                if articles:
                    parsed = parse_ieee_article(articles[0])
                    metadata_cache.set("ieee", cache_key, parsed, http_status=200)
                    logger.info(f"IEEE Xplore DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"IEEE lookup skipped ({e})")
        return None

async def search_ieee_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches IEEE Xplore for publications."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"ieee:q:{clean_q.lower()}"
    cached = metadata_cache.get("ieee", cache_key)
    if cached is not None:
        return cached

    api_key = getattr(settings, "IEEE_API_KEY", None) or os.getenv("IEEE_API_KEY")
    if not api_key:
        return []

    params = {"querytext": clean_q, "max_records": min(limit, 3), "apikey": api_key, "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(IEEE_API_BASE, params=params)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])
                items = [parse_ieee_article(a) for a in articles if a.get("title")]
                metadata_cache.set("ieee", cache_key, items, http_status=200)
                logger.info(f"IEEE search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"IEEE search skipped ({e})")
        return []
