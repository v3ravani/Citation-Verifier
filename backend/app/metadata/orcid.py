import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

ORCID_SEARCH_URL = "https://pub.orcid.org/v3.0/expanded-search"

def parse_orcid_work_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Standardizes an ORCID expanded-search item."""
    try:
        title = item.get("work-title") or item.get("title")
        if isinstance(title, dict):
            title = title.get("title", {}).get("value")
        if not title:
            return None
        title = str(title).strip().rstrip(".")

        authors = []
        fn = item.get("family-names") or ""
        gn = item.get("given-names") or ""
        name = f"{gn} {fn}".strip()
        if name:
            authors.append(name)

        year = None
        pub_year = item.get("publication-year") or item.get("publication-date")
        if pub_year:
            m = re.search(r'\b(19\d{2}|20\d{2})\b', str(pub_year))
            if m:
                year = int(m.group(1))

        doi = None
        ext_ids = item.get("external-ids", {}).get("external-id", []) if isinstance(item.get("external-ids"), dict) else []
        if isinstance(ext_ids, dict):
            ext_ids = [ext_ids]
        for eid in ext_ids:
            if eid.get("external-id-type", "").lower() == "doi":
                doi = eid.get("external-id-value")
                break

        venue = item.get("journal-title") or "ORCID Registry of Works"
        url = f"https://doi.org/{doi}" if doi else (item.get("url") or None)

        return {
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi.strip().lower() if doi else None,
            "venue": venue,
            "abstract": None,
            "citation_count": None,
            "url": url,
            "is_retracted": False,
            "source": "orcid",
        }
    except Exception:
        return None

async def fetch_orcid_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches works registered under ORCID by DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"orcid:doi:{clean_doi}"
    cached = metadata_cache.get("orcid", cache_key)
    if cached is not None:
        return cached

    headers = {"Accept": "application/json", "User-Agent": "CitationVerifier/1.0"}
    params = {"q": f'digital-object-ids:"{clean_doi}"', "rows": 1}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(ORCID_SEARCH_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("expanded-result", [])
                if results:
                    parsed = parse_orcid_work_result(results[0])
                    if parsed:
                        metadata_cache.set("orcid", cache_key, parsed, http_status=200)
                        logger.info(f"ORCID DOI lookup success: {clean_doi}")
                        return parsed
            return None
    except Exception as e:
        logger.debug(f"ORCID DOI lookup skipped for {clean_doi}: {e}")
        return None

async def search_orcid_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches ORCID registry for academic works matching title/authors."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:10])
    cache_key = f"orcid:q:{clean_q.lower()}"
    cached = metadata_cache.get("orcid", cache_key)
    if cached is not None:
        return cached

    headers = {"Accept": "application/json", "User-Agent": "CitationVerifier/1.0"}
    params = {"q": f'"{clean_q}"', "rows": min(limit, 3)}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(ORCID_SEARCH_URL, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("expanded-result", [])
                items = []
                for r in results:
                    parsed = parse_orcid_work_result(r)
                    if parsed and parsed.get("title"):
                        items.append(parsed)
                metadata_cache.set("orcid", cache_key, items, http_status=200)
                logger.info(f"ORCID search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"ORCID search skipped ({e})")
        return []
