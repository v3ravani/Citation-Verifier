import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

OPENCITATIONS_META_URL = "https://opencitations.net/meta/api/v1/metadata"

def parse_opencitations_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes an OpenCitations Meta record."""
    title = (item.get("title") or "").strip()

    # OpenCitations authors: "Family, Given; Family2, Given2"
    raw_author = item.get("author") or ""
    authors = []
    if raw_author:
        for a in raw_author.split(";"):
            clean_a = a.strip()
            if clean_a:
                # "Vaswani, Ashish" -> "Ashish Vaswani"
                if "," in clean_a:
                    parts = clean_a.split(",", 1)
                    authors.append(f"{parts[1].strip()} {parts[0].strip()}")
                else:
                    authors.append(clean_a)

    year = None
    pub_date = item.get("pub_date") or ""
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', pub_date)
    if year_match:
        year = int(year_match.group(1))

    venue = item.get("venue")
    raw_id = item.get("id") or ""
    doi = None
    doi_match = re.search(r'doi:(10\.\d{4,9}/[^\s]+)', raw_id)
    if doi_match:
        doi = doi_match.group(1)

    url = f"https://doi.org/{doi}" if doi else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "url": url,
        "abstract": None,
        "source": "opencitations",
    }

async def fetch_opencitations_by_doi(doi: str) -> Optional[Dict[str, Any]]:
    """Fetches work metadata from OpenCitations Meta API by exact DOI."""
    if not doi:
        return None

    clean_doi = doi.strip().lower()
    cache_key = f"opencitations:doi:{clean_doi}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    url = f"{OPENCITATIONS_META_URL}/doi:{clean_doi}"
    headers = {"User-Agent": "CitationVerifier/1.0 (academic-verify@example.org)"}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    parsed = parse_opencitations_item(data[0])
                    metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                    logger.info(f"OpenCitations lookup success for DOI: {clean_doi}")
                    return parsed
            return None
    except Exception as e:
        logger.debug(f"OpenCitations lookup skipped for {clean_doi}: {e}")
        return None
