import os
import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

DIMENSIONS_API_URL = "https://app.dimensions.ai/api/dsl/v1.0"

def parse_dimensions_publication(pub: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Dimensions publication object."""
    title = (pub.get("title") or "").strip().rstrip(".")

    authors = []
    for a in pub.get("authors", []):
        first = a.get("first_name", "")
        last = a.get("last_name", "")
        name = f"{first} {last}".strip()
        if name:
            authors.append(name)

    year = pub.get("year")
    if year:
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = None

    doi = pub.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = pub.get("journal", {}).get("title") or "Dimensions Research Database"
    abstract = pub.get("abstract")
    citations = pub.get("times_cited")
    url = f"https://doi.org/{clean_doi}" if clean_doi else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": citations,
        "url": url,
        "is_retracted": False,
        "source": "dimensions",
    }

async def fetch_dimensions_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches Dimensions metadata by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"dimensions:doi:{clean_doi}"
    cached = metadata_cache.get("dimensions", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "DIMENSIONS_API_KEY", None) or os.getenv("DIMENSIONS_API_KEY")
    if not key:
        return None

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    query_dsl = f'search publications where doi = "{clean_doi}" return publications[title+authors+year+doi+journal+times_cited+abstract] limit 1'

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.post(DIMENSIONS_API_URL, content=query_dsl, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                pubs = data.get("publications", [])
                if pubs:
                    parsed = parse_dimensions_publication(pubs[0])
                    metadata_cache.set("dimensions", cache_key, parsed, http_status=200)
                    logger.info(f"Dimensions DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"Dimensions DOI lookup skipped ({e})")
        return None

async def search_dimensions_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Dimensions for publications matching title."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8]).replace('"', '')
    cache_key = f"dimensions:q:{clean_q.lower()}"
    cached = metadata_cache.get("dimensions", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "DIMENSIONS_API_KEY", None) or os.getenv("DIMENSIONS_API_KEY")
    if not key:
        return []

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    query_dsl = f'search publications in title_only for "\\"{clean_q}\\"" return publications[title+authors+year+doi+journal+times_cited+abstract] limit {min(limit, 3)}'

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.post(DIMENSIONS_API_URL, content=query_dsl, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                pubs = data.get("publications", [])
                items = [parse_dimensions_publication(p) for p in pubs if p.get("title")]
                metadata_cache.set("dimensions", cache_key, items, http_status=200)
                logger.info(f"Dimensions search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"Dimensions search skipped ({e})")
        return []
