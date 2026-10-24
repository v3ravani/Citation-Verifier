import httpx
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

UNPAYWALL_BASE_URL = "https://api.unpaywall.org/v2"

def parse_unpaywall_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes an Unpaywall record object."""
    title = (item.get("title") or "").strip()

    authors = []
    for a in item.get("z_authors", []) or []:
        family = a.get("family", "").strip()
        given = a.get("given", "").strip()
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)

    year = item.get("year")
    venue = item.get("journal_name") or item.get("publisher")
    doi = item.get("doi")
    url = item.get("doi_url") or (f"https://doi.org/{doi}" if doi else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": None,
        "source": "unpaywall",
    }

async def fetch_unpaywall_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches verified academic metadata from Unpaywall by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"unpaywall:doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    email = getattr(settings, "CROSSREF_MAILTO", "academic-verify@example.org")
    url = f"{UNPAYWALL_BASE_URL}/{clean_doi}?email={email}"

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                parsed = parse_unpaywall_work(data)
                metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                logger.info(f"Unpaywall lookup success for DOI: {clean_doi}")
                return parsed
            return None
    except Exception as e:
        logger.debug(f"Unpaywall lookup skipped for DOI {clean_doi}: {e}")
        return None
