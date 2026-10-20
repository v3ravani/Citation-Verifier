import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

EUROPE_PMC_BASE_URL = "https://europepmc.org/RestWebService/v1.0"

def parse_europe_pmc_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a Europe PMC publication record."""
    title = (item.get("title") or "").strip().rstrip(".")
    
    # Authors
    author_str = item.get("authorString") or ""
    authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []

    # Year
    year = None
    pub_year = item.get("pubYear")
    if pub_year and str(pub_year).isdigit():
        year = int(pub_year)

    venue = item.get("journalTitle") or item.get("bookTitle")
    doi = item.get("doi")
    clean_doi = doi.strip().lower() if doi else None

    abstract = item.get("abstractText")
    citation_count = item.get("citedByCount")
    
    # Retraction check
    is_retracted = False
    if item.get("isRetracted") == "Y" or item.get("hasRetraction") == "Y":
        is_retracted = True

    url = f"https://doi.org/{clean_doi}" if clean_doi else (f"https://europepmc.org/article/MED/{item.get('pmid')}" if item.get("pmid") else None)

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": clean_doi,
        "venue": venue,
        "abstract": abstract,
        "citation_count": citation_count,
        "url": url,
        "is_retracted": is_retracted,
        "source": "europe_pmc"
    }

async def fetch_europe_pmc_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Look up publication on Europe PMC by DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"europe_pmc:doi:{clean_doi}"
    cached = metadata_cache.get("europe_pmc", cache_key)
    if cached is not None:
        return cached

    url = f"{EUROPE_PMC_BASE_URL}/search"
    params = {"query": f'DOI:"{clean_doi}"', "format": "json", "pageSize": 1}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("resultList", {}).get("result", [])
                if results:
                    parsed = parse_europe_pmc_item(results[0])
                    metadata_cache.set("europe_pmc", cache_key, parsed, http_status=200)
                    logger.info(f"Europe PMC match found for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying Europe PMC for DOI {clean_doi}: {e}")
        return None

async def search_europe_pmc_by_query(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Searches Europe PMC biomedical and preprint corpus by text query."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"europe_pmc:query:{clean_query}:{limit}"
    cached = metadata_cache.get("europe_pmc", cache_key)
    if cached is not None:
        return cached

    url = f"{EUROPE_PMC_BASE_URL}/search"
    params = {"query": clean_query, "format": "json", "pageSize": limit}
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION} (mailto:{settings.CROSSREF_MAILTO})"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("resultList", {}).get("result", [])
                parsed = [parse_europe_pmc_item(r) for r in results if r.get("title")]
                metadata_cache.set("europe_pmc", cache_key, parsed, http_status=200)
                logger.info(f"Europe PMC search found {len(parsed)} results for query: {clean_query[:40]}")
                return parsed
            return []
    except Exception as e:
        logger.error(f"Error querying Europe PMC for '{clean_query[:40]}': {e}")
        return []
