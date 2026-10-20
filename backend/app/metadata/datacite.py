import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

DATACITE_BASE_URL = "https://api.datacite.org"

def parse_datacite_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a DataCite record."""
    attrs = item.get("attributes", {})
    
    # Title
    titles = attrs.get("titles", [])
    title = (titles[0].get("title") if titles else "") or ""
    title = title.strip().rstrip(".")

    # Creators / Authors
    authors = []
    for creator in attrs.get("creators", []):
        name = creator.get("name")
        if not name:
            gn = creator.get("givenName", "")
            fn = creator.get("familyName", "")
            name = f"{gn} {fn}".strip()
        if name:
            authors.append(name)

    # Year
    year = attrs.get("publicationYear")
    if year and str(year).isdigit():
        year = int(year)
    else:
        year = None

    # DOI & Venue / Publisher
    doi = attrs.get("doi")
    clean_doi = doi.strip().lower() if doi else None
    venue = attrs.get("publisher") or attrs.get("container", {}).get("title")

    # Abstract / Description
    abstract = None
    for desc in attrs.get("descriptions", []):
        if desc.get("description"):
            abstract = desc.get("description")
            break

    url = attrs.get("url") or (f"https://doi.org/{clean_doi}" if clean_doi else None)

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
        "source": "datacite"
    }

async def fetch_datacite_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Look up a research dataset, preprint, or work in DataCite by DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"datacite:doi:{clean_doi}"
    cached = metadata_cache.get("datacite", cache_key)
    if cached is not None:
        return cached

    url = f"{DATACITE_BASE_URL}/dois/{clean_doi}"
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})",
        "Accept": "application/vnd.api+json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data:
                    parsed = parse_datacite_work(data)
                    metadata_cache.set("datacite", cache_key, parsed, http_status=200)
                    logger.info(f"DataCite match found for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying DataCite for DOI {clean_doi}: {e}")
        return None

async def search_datacite_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches DataCite registry for works and preprints by query."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"datacite:query:{clean_query}:{limit}"
    cached = metadata_cache.get("datacite", cache_key)
    if cached is not None:
        return cached

    url = f"{DATACITE_BASE_URL}/dois"
    params = {"query": clean_query, "page[size]": limit}
    headers = {
        "User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})",
        "Accept": "application/vnd.api+json"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                items = resp.json().get("data", [])
                parsed = [parse_datacite_work(it) for it in items]
                filtered = [p for p in parsed if p.get("title")]
                metadata_cache.set("datacite", cache_key, filtered, http_status=200)
                logger.info(f"DataCite search found {len(filtered)} results for query: {clean_query[:40]}")
                return filtered
            return []
    except Exception as e:
        logger.error(f"Error querying DataCite for '{clean_query[:40]}': {e}")
        return []
