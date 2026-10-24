import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

BIORXIV_API_BASE = "https://api.biorxiv.org/details"

def parse_biorxiv_entry(item: Dict[str, Any], server: str = "biorxiv") -> Dict[str, Any]:
    """Standardizes a bioRxiv / medRxiv preprint object."""
    title = (item.get("title") or "").strip()
    title = re.sub(r'<[^>]+>', '', title)

    raw_authors = item.get("authors") or ""
    authors = []
    if raw_authors:
        for a in raw_authors.split(";"):
            clean_a = a.strip()
            if clean_a:
                authors.append(clean_a)

    year = None
    pub_date = item.get("date") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pub_date)
    if year_match:
        year = int(year_match.group(1))

    doi = item.get("doi")
    venue = f"{server.capitalize()} Preprints in Life and Health Sciences"
    abstract = item.get("abstract")
    if abstract:
        abstract = re.sub(r'<[^>]+>', '', abstract)
    url = f"https://doi.org/{doi}" if doi else f"https://www.{server}.org/content/{doi}"

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": abstract,
        "source": server,
    }

async def fetch_biorxiv_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work from bioRxiv or medRxiv by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"biorxiv:doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    # Check biorxiv then medrxiv
    for server in ["biorxiv", "medrxiv"]:
        url = f"{BIORXIV_API_BASE}/{server}/{clean_doi}"
        try:
            async with httpx.AsyncClient(timeout=4.5) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    collection = data.get("collection", [])
                    if collection:
                        parsed = parse_biorxiv_entry(collection[-1], server=server)
                        metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                        logger.info(f"{server} lookup success for DOI: {clean_doi}")
                        return parsed
        except Exception:
            continue

    return None

async def search_biorxiv_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches bioRxiv and medRxiv preprints for matching title/abstract."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:10])
    cache_key = f"biorxiv:q:{clean_q.lower()}"
    cached = metadata_cache.get("biorxiv", cache_key)
    if cached is not None:
        return cached

    # Search Europe PMC preprint archive filtered to bioRxiv/medRxiv
    epmc_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    search_term = f'SRC:PPR AND (PUBLISHER:"bioRxiv" OR PUBLISHER:"medRxiv") AND ({clean_q})'
    params = {
        "query": search_term,
        "format": "json",
        "pageSize": min(limit, 3),
        "resultType": "core",
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(epmc_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("resultList", {}).get("result", [])
                items = []
                for it in results:
                    title = (it.get("title") or "").strip().rstrip(".")
                    title = re.sub(r'<[^>]+>', '', title)
                    if not title:
                        continue
                    auth_str = it.get("authorString") or ""
                    authors = [a.strip() for a in auth_str.split(",") if a.strip()]
                    doi = it.get("doi")
                    pub = (it.get("bookOrReportDetails", {}).get("publisher") or "").lower()
                    srv = "medrxiv" if "medrxiv" in pub else "biorxiv"
                    items.append({
                        "title": title,
                        "authors": authors,
                        "year": int(it["pubYear"]) if it.get("pubYear") and it["pubYear"].isdigit() else None,
                        "doi": doi.strip().lower() if doi else None,
                        "venue": f"{srv.capitalize()} Preprints",
                        "abstract": it.get("abstractText"),
                        "citation_count": it.get("citedByCount"),
                        "url": f"https://doi.org/{doi}" if doi else None,
                        "is_retracted": False,
                        "source": srv,
                    })
                metadata_cache.set("biorxiv", cache_key, items, http_status=200)
                logger.info(f"bioRxiv/medRxiv search found {len(items)} preprints for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"bioRxiv/medRxiv search skipped ({e})")
        return []

