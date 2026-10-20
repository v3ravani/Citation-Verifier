import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def parse_pubmed_summary(uid: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts standardized publication metadata from an NCBI PubMed esummary item."""
    raw_title = summary.get("title") or ""
    # Remove HTML markup or trailing brackets
    title = re.sub(r'<[^>]+>', '', raw_title).rstrip(".").strip()

    # Authors
    raw_authors = summary.get("authors") or []
    authors = []
    for a in raw_authors:
        if isinstance(a, dict) and a.get("name"):
            authors.append(a.get("name").strip())
        elif isinstance(a, str):
            authors.append(a.strip())

    # Year
    year = None
    pubdate = summary.get("pubdate") or summary.get("sortpubdate") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pubdate)
    if year_match:
        year = int(year_match.group(1))

    venue = summary.get("source") or summary.get("fulljournalname")

    # DOI and PMID extraction
    doi = None
    for aid in summary.get("articleids", []):
        if aid.get("idtype") == "doi":
            doi = aid.get("value", "").strip().lower()
            break

    # Retraction check from PubMed publication types
    pubtypes = summary.get("pubtype") or []
    is_retracted = any("retract" in pt.lower() for pt in pubtypes)

    url = f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
    if doi:
        url = f"https://doi.org/{doi}"

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "abstract": None,  # esummary doesn't include full abstract
        "citation_count": None,
        "pmid": uid,
        "url": url,
        "is_retracted": is_retracted,
        "is_medline_indexed": bool(summary.get("nlmuniqueid")),
        "source": "pubmed"
    }

async def fetch_pubmed_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Look up publication on PubMed/MEDLINE by DOI."""
    if not doi:
        return None
    clean_doi = doi.strip().lower()
    cache_key = f"pubmed:doi:{clean_doi}"
    cached = metadata_cache.get("pubmed", cache_key)
    if cached is not None:
        return cached

    search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f"{clean_doi}[doi]",
        "retmode": "json",
        "retmax": 1,
        "tool": "CitationVerifier",
        "email": settings.CROSSREF_MAILTO
    }
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(search_url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                if id_list:
                    uid = id_list[0]
                    summary_url = f"{PUBMED_BASE_URL}/esummary.fcgi"
                    sum_params = {
                        "db": "pubmed",
                        "id": uid,
                        "retmode": "json",
                        "tool": "CitationVerifier",
                        "email": settings.CROSSREF_MAILTO
                    }
                    sum_resp = await client.get(summary_url, params=sum_params, headers=headers)
                    if sum_resp.status_code == 200:
                        sum_data = sum_resp.json()
                        item = sum_data.get("result", {}).get(uid, {})
                        if item:
                            parsed = parse_pubmed_summary(uid, item)
                            parsed["doi"] = parsed.get("doi") or clean_doi
                            metadata_cache.set("pubmed", cache_key, parsed, http_status=200)
                            logger.info(f"PubMed match found for DOI: {clean_doi} (PMID {uid})")
                            return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying PubMed for DOI {clean_doi}: {e}")
        return None

async def search_pubmed_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches PubMed/MEDLINE by title or text query."""
    if not query or len(query.strip()) < 5:
        return []
    clean_query = " ".join(query.strip().split())
    cache_key = f"pubmed:query:{clean_query}:{limit}"
    cached = metadata_cache.get("pubmed", cache_key)
    if cached is not None:
        return cached

    search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
    # Search title specifically for high precision
    clean_title = re.sub(r'["“”\(\)\[\]]', ' ', clean_query)
    clean_title = " ".join(clean_title.split()[:12])
    params = {
        "db": "pubmed",
        "term": f"{clean_title}[title]",
        "retmode": "json",
        "retmax": limit,
        "tool": "CitationVerifier",
        "email": settings.CROSSREF_MAILTO
    }
    headers = {"User-Agent": f"CitationVerifier/{settings.APP_VERSION}"}

    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(search_url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                id_list = data.get("esearchresult", {}).get("idlist", [])
                if not id_list:
                    # Fallback to general term search if title field search was too strict
                    params["term"] = clean_title
                    resp2 = await client.get(search_url, params=params, headers=headers)
                    if resp2.status_code == 200:
                        id_list = resp2.json().get("esearchresult", {}).get("idlist", [])

                if id_list:
                    uid_str = ",".join(id_list[:limit])
                    summary_url = f"{PUBMED_BASE_URL}/esummary.fcgi"
                    sum_params = {
                        "db": "pubmed",
                        "id": uid_str,
                        "retmode": "json",
                        "tool": "CitationVerifier",
                        "email": settings.CROSSREF_MAILTO
                    }
                    sum_resp = await client.get(summary_url, params=sum_params, headers=headers)
                    if sum_resp.status_code == 200:
                        result_dict = sum_resp.json().get("result", {})
                        parsed_list = []
                        for uid in id_list[:limit]:
                            u_data = result_dict.get(uid)
                            if u_data and u_data.get("title"):
                                parsed_list.append(parse_pubmed_summary(uid, u_data))
                        if parsed_list:
                            metadata_cache.set("pubmed", cache_key, parsed_list, http_status=200)
                            logger.info(f"PubMed search returned {len(parsed_list)} results for '{clean_query[:35]}'")
                            return parsed_list
            return []
    except Exception as e:
        logger.error(f"Error querying PubMed for '{clean_query[:35]}': {e}")
        return []
