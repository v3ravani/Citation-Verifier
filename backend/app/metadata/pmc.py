import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

PMC_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PMC_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

def parse_pmc_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized metadata from NCBI PMC summary."""
    title = (item.get("title") or "").strip()
    title = re.sub(r'<[^>]+>', '', title)

    authors = []
    for a in item.get("authors", []):
        name = a.get("name", "").strip()
        if name:
            authors.append(name)

    year = None
    pub_date = item.get("pubdate") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pub_date)
    if year_match:
        year = int(year_match.group(1))

    venue = item.get("source") or "PubMed Central"
    doi = None
    for article_id in item.get("articleids", []):
        if article_id.get("idtype") == "doi":
            doi = article_id.get("value")

    pmcid = item.get("pmcid") or f"PMC{item.get('uid')}"
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": None,
        "source": "pmc",
    }

async def search_pmc_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches PubMed Central full-text archive."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:12])
    cache_key = f"pmc:q:{clean_q.lower()}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    search_params = {
        "db": "pmc",
        "term": clean_q,
        "retmode": "json",
        "retmax": min(limit, 3),
    }

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            search_resp = await client.get(PMC_SEARCH_URL, params=search_params)
            if search_resp.status_code != 200:
                return []

            search_data = search_resp.json()
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []

            summary_params = {
                "db": "pmc",
                "id": ",".join(id_list),
                "retmode": "json",
            }
            summary_resp = await client.get(PMC_SUMMARY_URL, params=summary_params)
            if summary_resp.status_code == 200:
                summary_data = summary_resp.json()
                results_dict = summary_data.get("result", {})
                items = []
                for uid in id_list:
                    doc = results_dict.get(uid)
                    if doc and doc.get("title"):
                        items.append(parse_pmc_summary(doc))
                metadata_cache.set("crossref", cache_key, items, http_status=200)
                logger.info(f"PMC search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"PMC search skipped ({e})")
        return []
