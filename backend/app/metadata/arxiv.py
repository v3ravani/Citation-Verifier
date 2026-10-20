import re
import xml.etree.ElementTree as ET
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.config import settings
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

def extract_arxiv_id(text: str) -> Optional[str]:
    """Extracts standard arXiv ID from text (e.g. arXiv:1706.03762 or 1706.03762)."""
    m = re.search(r'\b(?:arxiv:\s*)?([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)\b', text, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

def parse_arxiv_entry(entry: ET.Element) -> Dict[str, Any]:
    """Parses an Atom XML entry from arXiv."""
    title_el = entry.find("atom:title", ATOM_NS)
    title = " ".join(title_el.text.split()) if (title_el is not None and title_el.text) else ""

    summary_el = entry.find("atom:summary", ATOM_NS)
    abstract = " ".join(summary_el.text.split()) if (summary_el is not None and summary_el.text) else None

    published_el = entry.find("atom:published", ATOM_NS)
    year = int(published_el.text[:4]) if (published_el is not None and published_el.text) else None

    authors = []
    for author_el in entry.findall("atom:author", ATOM_NS):
        name_el = author_el.find("atom:name", ATOM_NS)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    id_el = entry.find("atom:id", ATOM_NS)
    url = id_el.text.strip() if (id_el is not None and id_el.text) else None
    
    doi_el = entry.find("arxiv:doi", ATOM_NS)
    doi = doi_el.text.strip() if (doi_el is not None and doi_el.text) else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": "arXiv Preprint",
        "abstract": abstract,
        "citation_count": None,
        "url": url,
        "source": "arxiv",
    }

async def fetch_arxiv_by_id(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """Fetches preprint metadata directly from arXiv API."""
    if not arxiv_id:
        return None
    cache_key = f"arxiv:{arxiv_id}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    params = {"id_list": arxiv_id, "max_results": 1}
    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", ATOM_NS)
                if entries:
                    parsed = parse_arxiv_entry(entries[0])
                    metadata_cache.set("crossref", cache_key, parsed, http_status=200)
                    logger.info(f"arXiv lookup success for: {arxiv_id}")
                    return parsed
            return None
    except Exception as e:
        logger.error(f"Error querying arXiv for {arxiv_id}: {e}")
        return None

async def search_arxiv_by_query(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Searches arXiv preprint repository by query terms."""
    if not query or len(query.strip()) < 3:
        return []
    cleaned_query = " ".join(query.split())
    cache_key = f"arxiv_search:{cleaned_query}:{max_results}"
    cached = metadata_cache.get("crossref", cache_key)
    if cached is not None:
        return cached

    params = {
        "search_query": f"all:{cleaned_query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    try:
        async with httpx.AsyncClient(timeout=settings.API_TIMEOUT_SECONDS) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", ATOM_NS)
                results = []
                for entry in entries:
                    parsed = parse_arxiv_entry(entry)
                    if parsed["title"]:
                        results.append(parsed)
                metadata_cache.set("crossref", cache_key, results, http_status=200)
                return results
            return []
    except Exception as e:
        logger.error(f"Error searching arXiv for '{query}': {e}")
        return []

