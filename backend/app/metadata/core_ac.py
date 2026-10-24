import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

CORE_BASE_URL = "https://api.core.ac.uk/v3"

def parse_core_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a CORE scholarly repository record."""
    title = (item.get("title") or "").strip()
    title = re.sub(r'<[^>]+>', '', title).rstrip(".")

    authors = []
    raw_authors = item.get("authors") or []
    for a in raw_authors:
        if isinstance(a, dict):
            name = a.get("name") or ""
        else:
            name = str(a)
        clean = name.strip()
        if clean and clean not in authors:
            authors.append(clean)

    year = item.get("yearPublished")
    if year:
        try:
            year = int(str(year)[:4])
        except (ValueError, TypeError):
            year = None

    doi = item.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    venue = item.get("publisher") or (item.get("journals") and item["journals"][0]) or "CORE Open Access Repository"
    abstract = item.get("abstract")
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract).strip()

    url = item.get("downloadUrl") or (f"https://doi.org/{clean_doi}" if clean_doi else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": item.get("citationCount"),
        "url": url,
        "is_retracted": False,
        "source": "core",
    }

async def fetch_core_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches verified research record from CORE by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"core:doi:{clean_doi}"
    cached = metadata_cache.get("core", cache_key)
    if cached is not None:
        return cached

    url = f"{CORE_BASE_URL}/works/doi/{clean_doi}"
    headers = {"User-Agent": "CitationVerifier/1.0 (academic-verify@example.org)"}
    core_key = getattr(settings, "CORE_API_KEY", None)
    if core_key:
        headers["Authorization"] = f"Bearer {core_key}"

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get("title"):
                    parsed = parse_core_work(data)
                    metadata_cache.set("core", cache_key, parsed, http_status=200)
                    logger.info(f"CORE DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"CORE DOI lookup skipped for {clean_doi}: {e}")
        return None

async def search_core_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches CORE for papers matching query."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:12])
    cache_key = f"core:q:{clean_q.lower()}"
    cached = metadata_cache.get("core", cache_key)
    if cached is not None:
        return cached

    url = f"{CORE_BASE_URL}/search/works"
    params = {"q": clean_q, "limit": min(limit, 3)}
    headers = {"User-Agent": "CitationVerifier/1.0 (academic-verify@example.org)"}
    core_key = getattr(settings, "CORE_API_KEY", None)
    if core_key:
        headers["Authorization"] = f"Bearer {core_key}"

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                items = [parse_core_work(r) for r in results if r.get("title")]
                metadata_cache.set("core", cache_key, items, http_status=200)
                logger.info(f"CORE search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"CORE search skipped ({e})")
        return []
