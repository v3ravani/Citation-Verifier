import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

ZENODO_API_URL = "https://zenodo.org/api/records"

def parse_zenodo_record(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a Zenodo record object."""
    meta = item.get("metadata", {})
    title = (meta.get("title") or "").strip()

    authors = []
    for c in meta.get("creators", []):
        name = c.get("name", "").strip()
        if name:
            if "," in name:
                parts = name.split(",", 1)
                authors.append(f"{parts[1].strip()} {parts[0].strip()}")
            else:
                authors.append(name)

    year = None
    pub_date = meta.get("publication_date") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pub_date)
    if year_match:
        year = int(year_match.group(1))

    doi = item.get("doi") or meta.get("doi")
    venue = "Zenodo Open Science Repository (CERN)"
    abstract = meta.get("description")
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract)
    url = item.get("links", {}).get("html") or (f"https://doi.org/{doi}" if doi else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": abstract,
        "source": "zenodo",
    }

async def fetch_zenodo_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work from Zenodo by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"zenodo:doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    url = f"{ZENODO_API_URL}?q=doi:\"{clean_doi}\"&size=1"
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    parsed = parse_zenodo_record(hits[0])
                    metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                    logger.info(f"Zenodo DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"Zenodo lookup skipped for {clean_doi}: {e}")
        return None

async def search_zenodo_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches Zenodo for records matching title or keywords."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:12])
    cache_key = f"zenodo:q:{clean_q.lower()}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    url = f"{ZENODO_API_URL}?q={clean_q}&size={min(limit, 3)}"
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                results = [parse_zenodo_record(h) for h in hits if h.get("metadata", {}).get("title")]
                metadata_cache.set("crossref", cache_key, results, http_status=200)
                logger.info(f"Zenodo search found {len(results)} items for: {clean_q[:40]}")
                return results
            return []
    except Exception as e:
        logger.debug(f"Zenodo search skipped ({e})")
        return []
