import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

OSF_PREPRINTS_URL = "https://api.osf.io/v2/preprints/"

def parse_osf_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Standardizes an OSF preprint/node record."""
    try:
        attrs = item.get("attributes", {})
        title = (attrs.get("title") or "").strip()
        if not title:
            return None

        year = None
        pub_date = attrs.get("date_published") or attrs.get("date_created") or ""
        if pub_date:
            m = re.search(r'\b(19\d{2}|20\d{2})\b', str(pub_date))
            if m:
                year = int(m.group(1))

        doi = attrs.get("doi")
        clean_doi = doi.strip().lower() if doi else None

        venue = "Open Science Framework (OSF Preprints)"
        abstract = attrs.get("description")
        url = item.get("links", {}).get("html") or (f"https://doi.org/{clean_doi}" if clean_doi else None)

        return {
            "title": title.rstrip("."),
            "authors": [],
            "year": year,
            "doi": clean_doi,
            "venue": venue,
            "abstract": abstract,
            "citation_count": None,
            "url": url,
            "is_retracted": False,
            "source": "osf",
        }
    except Exception:
        return None

async def fetch_osf_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work from OSF by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"osf:doi:{clean_doi}"
    cached = metadata_cache.get("osf", cache_key)
    if cached is not None:
        return cached

    params = {"filter[doi]": clean_doi, "page[size]": 1}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(OSF_PREPRINTS_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", [])
                if items:
                    parsed = parse_osf_item(items[0])
                    if parsed:
                        metadata_cache.set("osf", cache_key, parsed, http_status=200)
                        logger.info(f"OSF DOI lookup success: {clean_doi}")
                        return parsed
            return None
    except Exception as e:
        logger.debug(f"OSF DOI lookup skipped for {clean_doi}: {e}")
        return None

async def search_osf_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches OSF preprints and repository nodes."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"osf:q:{clean_q.lower()}"
    cached = metadata_cache.get("osf", cache_key)
    if cached is not None:
        return cached

    params = {"filter[title]": clean_q, "page[size]": min(limit, 3)}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(OSF_PREPRINTS_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for it in data.get("data", []):
                    parsed = parse_osf_item(it)
                    if parsed and parsed.get("title"):
                        items.append(parsed)
                metadata_cache.set("osf", cache_key, items, http_status=200)
                logger.info(f"OSF search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"OSF search skipped ({e})")
        return []
