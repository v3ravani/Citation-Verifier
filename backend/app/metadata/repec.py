import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

REPEC_SEARCH_BASE = "https://econpapers.repec.org/scripts/search.pf"

def parse_repec_html_item(title: str, author_str: str, year_str: str, handle_or_url: str) -> Dict[str, Any]:
    """Standardizes a RePEc / EconPapers record."""
    authors = [a.strip() for a in author_str.split(",") if a.strip()] if author_str else []
    year = None
    if year_str:
        m = re.search(r'\b(19\d{2}|20\d{2})\b', year_str)
        if m:
            year = int(m.group(1))

    return {
        "title": title.strip().rstrip("."),
        "authors": authors,
        "year": year,
        "doi": None,
        "venue": "RePEc / IDEAS Economics Archive",
        "abstract": None,
        "citation_count": None,
        "url": handle_or_url,
        "is_retracted": False,
        "source": "repec",
    }

async def search_repec_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches RePEc / EconPapers for economics research papers."""
    if not query or len(query.strip()) < 5:
        return []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"repec:q:{clean_q.lower()}"
    cached = metadata_cache.get("repec", cache_key)
    if cached is not None:
        return cached

    # Query EconPapers search
    params = {"ft": clean_q}
    headers = {"User-Agent": "CitationVerifier/1.0 (academic-verify@example.org)"}

    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(REPEC_SEARCH_BASE, params=params, headers=headers)
            if resp.status_code == 200:
                html = resp.text
                # Match title links from EconPapers search result: <a href="/article/...">(.*?)</a>
                matches = re.findall(r'<a\s+href="(/paper/[^"]+|/article/[^"]+)"[^>]*><b>(.*?)</b></a>', html, re.IGNORECASE)
                items = []
                for link, raw_title in matches[:limit]:
                    clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                    if clean_title and len(clean_title) > 6:
                        full_url = f"https://econpapers.repec.org{link}"
                        items.append(parse_repec_html_item(clean_title, "", "", full_url))
                metadata_cache.set("repec", cache_key, items, http_status=200)
                logger.info(f"RePEc search found {len(items)} items for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"RePEc search skipped ({e})")
        return []
