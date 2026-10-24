import os
import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"

def parse_scopus_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Scopus search entry."""
    title = (entry.get("dc:title") or "").strip().rstrip(".")
    creator = entry.get("dc:creator")
    authors = [creator] if creator else []

    year = None
    cover_date = entry.get("prism:coverDate") or ""
    if cover_date:
        m = re.search(r'\b(19\d{2}|20\d{2})\b', cover_date)
        if m:
            year = int(m.group(1))

    doi = entry.get("prism:doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = entry.get("prism:publicationName") or "Scopus Indexed Journal"
    citations = None
    if entry.get("citedby-count"):
        try:
            citations = int(entry["citedby-count"])
        except (ValueError, TypeError):
            pass

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
        "source": "scopus",
    }

async def fetch_scopus_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches Scopus metadata by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"scopus:doi:{clean_doi}"
    cached = metadata_cache.get("scopus", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "SCOPUS_API_KEY", None) or os.getenv("SCOPUS_API_KEY") or os.getenv("ELSEVIER_API_KEY")
    if not key:
        return None

    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    params = {"query": f'DOI("{clean_doi}")', "count": 1}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(SCOPUS_SEARCH_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("search-results", {}).get("entry", [])
                if entries and "dc:title" in entries[0]:
                    parsed = parse_scopus_entry(entries[0])
                    metadata_cache.set("scopus", cache_key, parsed, http_status=200)
                    logger.info(f"Scopus DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"Scopus DOI lookup skipped ({e})")
        return None

async def search_scopus_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Scopus registry for matching articles."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"scopus:q:{clean_q.lower()}"
    cached = metadata_cache.get("scopus", cache_key)
    if cached is not None:
        return cached

    key = getattr(settings, "SCOPUS_API_KEY", None) or os.getenv("SCOPUS_API_KEY") or os.getenv("ELSEVIER_API_KEY")
    if not key:
        return []

    headers = {"X-ELS-APIKey": key, "Accept": "application/json"}
    params = {"query": f'TITLE("{clean_q}")', "count": min(limit, 3)}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(SCOPUS_SEARCH_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("search-results", {}).get("entry", [])
                items = [parse_scopus_entry(e) for e in entries if e.get("dc:title")]
                metadata_cache.set("scopus", cache_key, items, http_status=200)
                logger.info(f"Scopus search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"Scopus search skipped ({e})")
        return []
