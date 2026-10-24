import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

FIGSHARE_API_URL = "https://api.figshare.com/v2/articles"

def parse_figshare_article(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Figshare research repository article object."""
    title = (item.get("title") or "").strip()
    title = re.sub(r'<[^>]+>', '', title).rstrip(".")

    authors = []
    for a in item.get("authors", []):
        if isinstance(a, dict):
            name = a.get("full_name") or a.get("name")
        else:
            name = str(a)
        if name and name.strip():
            authors.append(name.strip())

    year = None
    pub_date = item.get("published_date") or item.get("timeline", {}).get("posted") or ""
    if pub_date:
        m = re.search(r'\b(19\d{2}|20\d{2})\b', str(pub_date))
        if m:
            year = int(m.group(1))

    doi = item.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = "Figshare Open Repository"
    abstract = item.get("description")
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract).strip()

    url = item.get("url_public_html") or (f"https://doi.org/{clean_doi}" if clean_doi else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": None,
        "url": url,
        "is_retracted": False,
        "source": "figshare",
    }

async def fetch_figshare_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work from Figshare by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"figshare:doi:{clean_doi}"
    cached = metadata_cache.get("figshare", cache_key)
    if cached is not None:
        return cached

    url = f"{FIGSHARE_API_URL}?doi={clean_doi}"
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    parsed = parse_figshare_article(data[0])
                    metadata_cache.set("figshare", cache_key, parsed, http_status=200)
                    logger.info(f"Figshare DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"Figshare DOI lookup skipped for {clean_doi}: {e}")
        return None

async def search_figshare_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Figshare repository for publications and dataset papers."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:10])
    cache_key = f"figshare:q:{clean_q.lower()}"
    cached = metadata_cache.get("figshare", cache_key)
    if cached is not None:
        return cached

    url = f"{FIGSHARE_API_URL}/search"
    payload = {"search_for": clean_q, "page_size": min(limit, 3)}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    items = [parse_figshare_article(d) for d in data if d.get("title")]
                    metadata_cache.set("figshare", cache_key, items, http_status=200)
                    logger.info(f"Figshare search found {len(items)} items for: {clean_q[:40]}")
                    return items
            return []
    except Exception as e:
        logger.debug(f"Figshare search skipped ({e})")
        return []
