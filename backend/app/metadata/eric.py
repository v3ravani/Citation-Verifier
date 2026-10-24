import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

ERIC_API_URL = "https://api.ies.ed.gov/eric/"

def parse_eric_doc(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes an ERIC document object."""
    title = (item.get("title") or "").strip()

    raw_authors = item.get("author") or []
    if isinstance(raw_authors, str):
        raw_authors = [raw_authors]

    authors = []
    for a in raw_authors:
        clean = a.strip()
        if clean:
            if "," in clean:
                parts = clean.split(",", 1)
                authors.append(f"{parts[1].strip()} {parts[0].strip()}")
            else:
                authors.append(clean)

    year = None
    pub_year = item.get("publicationdateyear")
    if pub_year:
        try:
            year = int(pub_year)
        except (ValueError, TypeError):
            pass

    venue = item.get("source") or "ERIC Educational Resources Archive"
    abstract = item.get("description")
    eric_id = item.get("id")
    url = f"https://eric.ed.gov/?id={eric_id}" if eric_id else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": None,
        "venue": venue,
        "url": url,
        "abstract": abstract,
        "source": "eric",
    }

async def search_eric_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches ERIC database for educational and social science publications."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:10])
    cache_key = f"eric:q:{clean_q.lower()}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    params = {
        "search": clean_q,
        "rows": min(limit, 3),
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(ERIC_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                items = [parse_eric_doc(d) for d in docs if d.get("title")]
                metadata_cache.set("crossref", cache_key, items, http_status=200)
                logger.info(f"ERIC search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"ERIC search skipped ({e})")
        return []
