import os
import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

ADS_API_BASE = "https://api.adsabs.harvard.edu/v1/search/query"

def parse_ads_doc(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a NASA ADS record."""
    titles = item.get("title") or []
    title = (titles[0] if isinstance(titles, list) and titles else str(titles)).strip().rstrip(".")

    authors = item.get("author") or []
    if isinstance(authors, str):
        authors = [authors]

    year = item.get("year")
    if year:
        try:
            year = int(str(year)[:4])
        except (ValueError, TypeError):
            year = None

    doi_list = item.get("doi") or []
    doi = doi_list[0] if isinstance(doi_list, list) and doi_list else None
    clean_doi = doi.strip().lower() if doi else None

    venue = item.get("pub") or "NASA ADS Astrophysics & Physical Sciences Archive"
    abstract = item.get("abstract")
    bibcode = item.get("bibcode")
    url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract" if bibcode else (f"https://doi.org/{clean_doi}" if clean_doi else None)

    return {
        "title": title,
        "authors": authors[:10],
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": item.get("citation_count"),
        "url": url,
        "is_retracted": False,
        "source": "nasa_ads",
    }

async def fetch_nasa_ads_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches NASA ADS record by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"nasa_ads:doi:{clean_doi}"
    cached = metadata_cache.get("nasa_ads", cache_key)
    if cached is not None:
        return cached

    token = getattr(settings, "NASA_ADS_API_KEY", None) or os.getenv("NASA_ADS_API_KEY") or os.getenv("ADS_DEV_KEY")
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}", "User-Agent": "CitationVerifier/1.0"}
    params = {"q": f'doi:"{clean_doi}"', "fl": "title,author,year,doi,pub,abstract,bibcode,citation_count", "rows": 1}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(ADS_API_BASE, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                if docs:
                    parsed = parse_ads_doc(docs[0])
                    metadata_cache.set("nasa_ads", cache_key, parsed, http_status=200)
                    logger.info(f"NASA ADS DOI lookup success: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"NASA ADS lookup skipped ({e})")
        return None

async def search_nasa_ads_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches NASA ADS by title/keywords."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"nasa_ads:q:{clean_q.lower()}"
    cached = metadata_cache.get("nasa_ads", cache_key)
    if cached is not None:
        return cached

    token = getattr(settings, "NASA_ADS_API_KEY", None) or os.getenv("NASA_ADS_API_KEY") or os.getenv("ADS_DEV_KEY")
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}", "User-Agent": "CitationVerifier/1.0"}
    params = {"q": f'title:"{clean_q}"', "fl": "title,author,year,doi,pub,abstract,bibcode,citation_count", "rows": min(limit, 3)}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(ADS_API_BASE, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                items = [parse_ads_doc(d) for d in docs if d.get("title")]
                metadata_cache.set("nasa_ads", cache_key, items, http_status=200)
                logger.info(f"NASA ADS search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"NASA ADS search skipped ({e})")
        return []
