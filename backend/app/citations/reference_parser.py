import re
from typing import List, Optional
from backend.app.models.schemas import ParsedReference
from backend.app.citations.normalizer import extract_doi, extract_year, extract_authors, normalize_title
from backend.app.core.logging_config import logger

def split_raw_references(ref_text: str) -> List[tuple[int, str, str]]:
    """
    Splits bibliography text into individual reference entries.
    Returns list of tuples: (index, marker, raw_entry_text)
    """
    if not ref_text or not ref_text.strip():
        return []

    lines = ref_text.splitlines()
    entries = []

    # Check for [1], [2] style
    numeric_bracket_pattern = re.compile(r'^\s*\[(\d+)\]\s*(.*)$')
    # Check for 1., 2. style
    numbered_dot_pattern = re.compile(r'^\s*(\d+)\.\s+(.*)$')
    # Check for APA author (year) style at line start
    apa_start_pattern = re.compile(r'^[A-Z][A-Za-z\s,\.\-&]+\s*\((19\d{2}|20\d{2})\)')

    current_idx = None
    current_marker = ""
    current_lines = []

    # Detect predominant style
    total_bracket = len(re.findall(r'^\s*\[\d+\]', ref_text, re.MULTILINE))
    total_dot = len(re.findall(r'^\s*\d+\.\s', ref_text, re.MULTILINE))

    if total_bracket >= 2:
        # Numeric bracket style [1]
        for line in lines:
            m = numeric_bracket_pattern.match(line)
            if m:
                if current_lines:
                    entries.append((current_idx, current_marker, " ".join(current_lines).strip()))
                    current_lines = []
                current_idx = int(m.group(1))
                current_marker = f"[{current_idx}]"
                current_lines.append(m.group(2))
            else:
                if current_lines is not None:
                    current_lines.append(line.strip())
        if current_lines:
            entries.append((current_idx, current_marker, " ".join(current_lines).strip()))

    elif total_dot >= 2:
        # Numbered dot style: 1.
        for line in lines:
            m = numbered_dot_pattern.match(line)
            if m:
                if current_lines:
                    entries.append((current_idx, current_marker, " ".join(current_lines).strip()))
                    current_lines = []
                current_idx = int(m.group(1))
                current_marker = f"[{current_idx}]"
                current_lines.append(m.group(2))
            else:
                if current_lines is not None:
                    current_lines.append(line.strip())
        if current_lines:
            entries.append((current_idx, current_marker, " ".join(current_lines).strip()))

    else:
        # APA / unnumbered style - split by blank lines or author-year pattern
        gen_idx = 1
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if apa_start_pattern.match(stripped) and current_lines:
                entries.append((gen_idx, f"Ref {gen_idx}", " ".join(current_lines).strip()))
                gen_idx += 1
                current_lines = [stripped]
            else:
                current_lines.append(stripped)
        if current_lines:
            entries.append((gen_idx, f"Ref {gen_idx}", " ".join(current_lines).strip()))

    # Clean entries
    cleaned_entries = []
    for idx, marker, raw in entries:
        clean_raw = " ".join(raw.split())
        # Filter out noise entries (e.g. empty or page footers)
        if len(clean_raw) > 15:
            cleaned_entries.append((idx or len(cleaned_entries) + 1, marker, clean_raw))

    return cleaned_entries

def extract_reference_title(raw_text: str) -> Optional[str]:
    """
    Extracts the publication title from a raw reference string.
    """
    if not raw_text:
        return None

    # IEEE style: title in quotes: "Title of Paper,"
    quote_match = re.search(r'["“]([^"”]+)["”]', raw_text)
    if quote_match and len(quote_match.group(1).strip()) > 10:
        return quote_match.group(1).strip().rstrip(".,")

    # APA style: Author (Year). Title. Journal / Venue.
    apa_match = re.search(r'\((?:19\d{2}|20\d{2})\)\.?\s+([^\.]+)\.', raw_text)
    if apa_match and len(apa_match.group(1).strip()) > 10:
        return apa_match.group(1).strip().rstrip(".,")

    # Fallback: remove authors and year, take the next segment before next period
    text_clean = re.sub(r'^\s*\[?\d+\]?\.?\s*', '', raw_text)
    parts = text_clean.split(". ")
    if len(parts) >= 2:
        # Often parts[1] is the title
        candidate = parts[1].strip()
        if len(candidate) > 15 and not any(w in candidate.lower() for w in ["vol", "pp", "pages", "proceedings"]):
            return candidate.rstrip(".,")
    if len(parts) >= 1 and len(parts[0]) > 25:
        return parts[0].strip().rstrip(".,")

    return None

def parse_reference(ref_id: int, raw_text: str) -> ParsedReference:
    """
    Parses a single raw reference string into a structured ParsedReference.
    """
    doi = extract_doi(raw_text)
    year = extract_year(raw_text)
    authors = extract_authors(raw_text)
    title = extract_reference_title(raw_text)

    # Heuristic venue extraction
    venue = None
    venue_match = re.search(r'(?:in\s+)?([A-Z][A-Za-z\s]+(?:Conference|Symposium|Workshop|Transactions|Journal|Letters|Review|Communications))', raw_text)
    if venue_match:
        venue = venue_match.group(1).strip()

    # URL if present and not DOI
    url = None
    url_match = re.search(r'https?://[^\s]+', raw_text)
    if url_match:
        url = url_match.group(0).rstrip(".,;)>]")

    return ParsedReference(
        reference_id=ref_id,
        raw_text=raw_text,
        title=title,
        authors=authors,
        year=year,
        venue=venue,
        doi=doi,
        url=url
    )

def parse_all_references(ref_text: str) -> List[tuple[str, ParsedReference]]:
    """
    Parses all references from the extracted bibliography text.
    Returns list of (marker, ParsedReference).
    """
    entries = split_raw_references(ref_text)
    results = []
    for ref_id, marker, raw in entries:
        parsed = parse_reference(ref_id, raw)
        results.append((marker, parsed))
    logger.info(f"Parsed {len(results)} references from bibliography text.")
    return results
