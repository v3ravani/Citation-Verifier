import re
import httpx
from typing import Optional, Dict, Any, List
from backend.app.core.logging_config import logger
from backend.app.metadata.cache import metadata_cache

CLINICAL_TRIALS_BASE = "https://clinicaltrials.gov/api/v2/studies"
NCT_REGEX = re.compile(r'\b(NCT\d{8})\b', re.IGNORECASE)

def extract_nct_id(text: str) -> Optional[str]:
    """Extracts a ClinicalTrials.gov NCT identifier (e.g. NCT01234567)."""
    if not text:
        return None
    m = NCT_REGEX.search(text)
    return m.group(1).upper() if m else None

def parse_clinical_study(study: Dict[str, Any]) -> Dict[str, Any]:
    """Standardizes a ClinicalTrials.gov protocol study."""
    protocol = study.get("protocolSection", {})
    id_mod = protocol.get("identificationModule", {})
    title = id_mod.get("briefTitle") or id_mod.get("officialTitle") or ""
    nct_id = id_mod.get("nctId")

    org = id_mod.get("organization", {}).get("fullName") or "ClinicalTrials.gov Registry"

    authors = []
    contacts = protocol.get("contactsLocationsModule", {}).get("centralContacts", [])
    for c in contacts:
        name = c.get("name")
        if name:
            authors.append(name.strip())
    if not authors and id_mod.get("organization"):
        authors.append(id_mod["organization"].get("fullName", "ClinicalTrials.gov Sponsor"))

    year = None
    status_mod = protocol.get("statusModule", {})
    start_date = status_mod.get("startDateStruct", {}).get("date") or status_mod.get("completionDateStruct", {}).get("date")
    if start_date:
        m = re.search(r'\b(19\d{2}|20\d{2})\b', start_date)
        if m:
            year = int(m.group(1))

    desc = protocol.get("descriptionModule", {}).get("briefSummary")
    url = f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else None

    return {
        "title": title.strip().rstrip("."),
        "authors": authors,
        "year": year,
        "doi": None,
        "venue": f"ClinicalTrials.gov ({nct_id})" if nct_id else org,
        "abstract": desc,
        "citation_count": None,
        "url": url,
        "is_retracted": False,
        "source": "clinicaltrials",
    }

async def fetch_clinical_study_by_id(nct_id: str) -> Optional[Dict[str, Any]]:
    """Fetches study metadata from ClinicalTrials.gov by NCT ID."""
    clean_nct = nct_id.strip().upper()
    cache_key = f"clinicaltrials:id:{clean_nct}"
    cached = metadata_cache.get("clinicaltrials", cache_key)
    if cached is not None:
        return cached

    url = f"{CLINICAL_TRIALS_BASE}/{clean_nct}"
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                parsed = parse_clinical_study(data)
                metadata_cache.set("clinicaltrials", cache_key, parsed, http_status=200)
                logger.info(f"ClinicalTrials.gov lookup success for {clean_nct}")
                return parsed
            return None
    except Exception as e:
        logger.debug(f"ClinicalTrials.gov ID lookup skipped: {e}")
        return None

async def search_clinicaltrials_by_query(query: str, limit: int = 2) -> List[Dict[str, Any]]:
    """Searches ClinicalTrials.gov by trial title or keywords."""
    if not query or len(query.strip()) < 5:
        return []

    # Check if query contains explicit NCT ID
    nct = extract_nct_id(query)
    if nct:
        res = await fetch_clinical_study_by_id(nct)
        return [res] if res else []

    clean_q = " ".join(query.strip().split()[:8])
    cache_key = f"clinicaltrials:q:{clean_q.lower()}"
    cached = metadata_cache.get("clinicaltrials", cache_key)
    if cached is not None:
        return cached

    params = {"query.term": clean_q, "pageSize": min(limit, 3)}
    try:
        async with httpx.AsyncClient(timeout=4.5) as client:
            resp = await client.get(CLINICAL_TRIALS_BASE, params=params)
            if resp.status_code == 200:
                data = resp.json()
                studies = data.get("studies", [])
                items = [parse_clinical_study(s) for s in studies if s.get("protocolSection")]
                metadata_cache.set("clinicaltrials", cache_key, items, http_status=200)
                logger.info(f"ClinicalTrials.gov search found {len(items)} for: {clean_q[:40]}")
                return items
            return []
    except Exception as e:
        logger.debug(f"ClinicalTrials.gov search skipped ({e})")
        return []
