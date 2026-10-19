import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

def clean_crossref_abstract(raw_abstract: Optional[str]) -> Optional[str]:
    """Removes JATS XML tags often returned by Crossref."""
    if not raw_abstract:
        return None
    cleaned = re.sub(r'<[^>]+>', '', raw_abstract)
    return " ".join(cleaned.split())

def parse_crossref_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized metadata fields from a Crossref work object."""
    titles = item.get("title", [])
    title = titles[0].strip() if titles else ""

    authors = []
    for a in item.get("author", []):
        family = a.get("family", "").strip()
        given = a.get("given", "").strip()
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
        elif a.get("name"):
            authors.append(a.get("name").strip())

    year = None
    date_parts = (
        item.get("issued", {}).get("date-parts") or
        item.get("published-print", {}).get("date-parts") or
        item.get("published-online", {}).get("date-parts")
    )
    if date_parts and len(date_parts[0]) > 0:
        try:
            year = int(date_parts[0][0])
        except (ValueError, TypeError):
            year = None

    venues = item.get("container-title", [])
    venue = venues[0].strip() if venues else None

    doi = item.get("DOI")
    url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
    raw_abstract = item.get("abstract")
    abstract = clean_crossref_abstract(raw_abstract)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": abstract,
        "source": "crossref",
    }

async def fetch_crossref_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work metadata from Crossref using exact DOI lookup."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        logger.info(f"Crossref cache hit for DOI: {clean_doi}")
        return cached

    url = f"{settings.CROSSREF_BASE_URL.rstrip('/')}/works/{clean_doi}"
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                item = data.get("message", {})
                parsed = parse_crossref_work(item)
                metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                logger.info(f"Crossref lookup success for DOI: {clean_doi}")
                return parsed
            elif resp.status_code == 404:
                logger.info(f"Crossref DOI not found: {clean_doi}")
                metadata_cache.set("crossref", cache_key, None, http_status=404)
                return None
            else:
                logger.warning(f"Crossref returned status {resp.status_code} for DOI {clean_doi}")
                return None
    except Exception as e:
        logger.error(f"Error querying Crossref by DOI {clean_doi}: {e}")
        return None

async def search_crossref_by_query(query: str, rows: int = 3) -> List[Dict[str, Any]]:
    """Searches Crossref using bibliographic / title query."""
    if not query or len(query.strip()) < 5:
        return []

    clean_query = " ".join(query.strip().split())
    cache_key = f"query:{clean_query}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        logger.info(f"Crossref cache hit for query: {clean_query[:40]}...")
        return cached

    url = f"{settings.CROSSREF_BASE_URL.rstrip('/')}/works"
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"
    }
    params = {
        "query.bibliographic": clean_query,
        "rows": rows,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                results = [parse_crossref_work(it) for it in items]
                metadata_cache.set("crossref", cache_key, results, http_status=200)
                logger.info(f"Crossref search found {len(results)} items for query: {clean_query[:40]}")
                return results
            else:
                logger.warning(f"Crossref search returned status {resp.status_code} for {clean_query[:40]}")
                return []
    except Exception as e:
        logger.error(f"Error querying Crossref by search query {clean_query[:40]}: {e}")
        return []
