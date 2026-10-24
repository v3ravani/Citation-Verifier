import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

OPENAIRE_API_URL = "https://api.openaire.eu/search/publications"

def parse_openaire_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Standardizes an OpenAIRE publication result."""
    try:
        metadata = item.get("metadata", {}).get("oaf:entity", {}).get("oaf:result", {})
        if not metadata:
            return None

        # Title
        title_obj = metadata.get("title", {})
        title = title_obj.get("$", "") if isinstance(title_obj, dict) else str(title_obj)
        if not title:
            return None

        # Authors
        authors = []
        creator_list = metadata.get("creator", [])
        if isinstance(creator_list, dict):
            creator_list = [creator_list]
        for c in creator_list:
            name = c.get("$", "") if isinstance(c, dict) else str(c)
            if name:
                authors.append(name.strip())

        # Year
        year = None
        date_obj = metadata.get("dateofacceptance", {})
        date_str = date_obj.get("$", "") if isinstance(date_obj, dict) else str(date_obj)
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
        if year_match:
            year = int(year_match.group(1))

        # Venue
        venue_obj = metadata.get("journal", {})
        venue = venue_obj.get("$", "") if isinstance(venue_obj, dict) else str(venue_obj) or "OpenAIRE Research Archive"

        # DOI
        doi = None
        pid_list = metadata.get("pid", [])
        if isinstance(pid_list, dict):
            pid_list = [pid_list]
        for p in pid_list:
            if isinstance(p, dict) and p.get("@classid") == "doi":
                doi = p.get("$")
                break

        url = f"https://doi.org/{doi}" if doi else None

        return {
            "title": title.strip(),
            "authors": authors,
            "year": year,
            "doi": doi,
            "venue": venue,
            "url": url,
            "abstract": None,
            "source": "openaire",
        }
    except Exception:
        return None

async def fetch_openaire_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches publication from OpenAIRE by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"openaire:doi:{clean_doi}"
    cached = metadata_cache.get("openaire", cache_key)
    if cached is not None:
        return cached

    params = {"doi": clean_doi, "format": "json", "size": 1}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(OPENAIRE_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results_wrap = data.get("response", {}).get("results", {}).get("result", [])
                if isinstance(results_wrap, dict):
                    results_wrap = [results_wrap]
                if results_wrap:
                    parsed = parse_openaire_result(results_wrap[0])
                    if parsed:
                        metadata_cache.set("openaire", cache_key, parsed, http_status=200)
                        logger.info(f"OpenAIRE DOI lookup success: {clean_doi}")
                        return parsed
            return None
    except Exception as e:
        logger.debug(f"OpenAIRE DOI lookup skipped for {clean_doi}: {e}")
        return None

async def search_openaire_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches OpenAIRE European Open Access publications."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:10])
    cache_key = f"openaire:q:{clean_q.lower()}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    params = {
        "title": clean_q,
        "format": "json",
        "size": min(limit, 3),
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(OPENAIRE_API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results_wrap = data.get("response", {}).get("results", {}).get("result", [])
                if isinstance(results_wrap, dict):
                    results_wrap = [results_wrap]
                items = []
                for it in results_wrap:
                    parsed = parse_openaire_result(it)
                    if parsed:
                        items.append(parsed)
                metadata_cache.set("crossref", cache_key, items, http_status=200)
                logger.info(f"OpenAIRE search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"OpenAIRE search skipped ({e})")
        return []
