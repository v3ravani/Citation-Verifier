import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

def parse_google_books_volume(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized metadata from a Google Books volume object."""
    info = item.get("volumeInfo", {})
    title = (info.get("title") or "").strip()
    subtitle = info.get("subtitle")
    if subtitle:
        title = f"{title}: {subtitle}"

    authors = info.get("authors", [])
    if isinstance(authors, str):
        authors = [authors]

    year = None
    pub_date = info.get("publishedDate") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pub_date)
    if year_match:
        year = int(year_match.group(1))

    venue = info.get("publisher") or "Google Books Academic Monograph"
    abstract = info.get("description")
    url = info.get("infoLink") or info.get("canonicalVolumeLink")

    # Extract ISBN or DOI if available
    doi = None
    for ident in info.get("industryIdentifiers", []):
        if ident.get("type") in ["ISBN_13", "ISBN_10"]:
            pass  # Could be stored
        elif "doi" in ident.get("type", "").lower():
            doi = ident.get("identifier")

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": abstract,
        "source": "google_books",
    }

async def search_google_books_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Google Books API for academic monographs, textbooks, and treatises."""
    if not query or len(query.strip()) < 4:
        return []

    clean_q = " ".join(query.strip().split()[:14])
    cache_key = f"google_books:q:{clean_q.lower()}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    params = {
        "q": clean_q,
        "maxResults": min(limit, 5),
        "printType": "books",
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(GOOGLE_BOOKS_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                results = [parse_google_books_volume(item) for item in items if item.get("volumeInfo", {}).get("title")]
                metadata_cache.set("crossref", cache_key, results, http_status=200)
                logger.info(f"Google Books search found {len(results)} items for query: {clean_q[:40]}")
                return results
            return []
    except Exception as e:
        logger.debug(f"Google Books API query skipped ({e})")
        return []
