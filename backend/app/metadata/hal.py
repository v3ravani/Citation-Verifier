import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

HAL_BASE_URL = "https://api.archives-ouvertes.fr/search"

def parse_hal_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a HAL open-science document record."""
    titles = doc.get("title_s") or []
    title = titles[0].rstrip(".").strip() if titles else ""

    authors = doc.get("authFullName_s") or []
    year = doc.get("producedDateY_i")
    venue = doc.get("journalTitle_s")
    
    doi = doc.get("doiId_s")
    clean_doi = doi.strip().lower() if doi else None

    abstracts = doc.get("abstract_s") or []
    abstract = abstracts[0] if abstracts else None

    url = doc.get("uri_s")
    if not url and clean_doi:
        url = f"https://doi.org/{clean_doi}"

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
        "source": "hal"
    }

async def fetch_hal_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Look up publication on HAL Open Science archive by DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"hal:doi:{clean_doi}"
    cached = metadata_cache.get("hal", cache_key)
    if cached is not None:
        return cached

    params = {
        "q": f'doiId_s:"{clean_doi}"',
        "wt": "json",
        "fl": "docid,title_s,authFullName_s,producedDateY_i,doiId_s,uri_s,abstract_s,journalTitle_s",
        "rows": 1
    }
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(HAL_BASE_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                if docs:
                    parsed = parse_hal_doc(docs[0])
                    parsed["doi"] = parsed.get("doi") or clean_doi
                    metadata_cache.set("hal", cache_key, parsed, http_status=200)
                    logger.info(f"HAL Open Science record matched for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying HAL by DOI {clean_doi}: {e}")
        return None

async def search_hal_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches HAL Open Science archive by title or query."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"hal:query:{clean_query}:{limit}"
    cached = metadata_cache.get("hal", cache_key)
    if cached is not None:
        return cached

    # Limit search words for query syntax safety
    safe_q = " ".join(clean_query.split()[:10])
    params = {
        "q": safe_q,
        "wt": "json",
        "fl": "docid,title_s,authFullName_s,producedDateY_i,doiId_s,uri_s,abstract_s,journalTitle_s",
        "rows": limit
    }
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(HAL_BASE_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                parsed = [parse_hal_doc(d) for d in docs if d.get("title_s")]
                metadata_cache.set("hal", cache_key, parsed, http_status=200)
                logger.info(f"HAL search returned {len(parsed)} results for query: {clean_query[:35]}")
                return parsed
            return []
    except Exception as e:
        logger.error(f"Error querying HAL for '{clean_query[:35]}': {e}")
        return []
