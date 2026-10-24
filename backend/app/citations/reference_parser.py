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

    # First check if references are inline delimited by slashes, e.g.:
    # "1 UNEP ...  /  2 World Bank ...  /  3 Skerritt ..."
    if " / " in ref_text and re.search(r'\s+/\s+\d+\b', ref_text):
        slash_tokens = re.split(r'\s+/\s+(?=\d+\b)', ref_text)
        entries = []
        for token in slash_tokens:
            m = re.match(r'^\s*(\d+)\s+(.*)', token, re.DOTALL)
            if m:
                idx = int(m.group(1))
                entries.append((idx, f"[{idx}]", " ".join(m.group(2).split())))
            elif len(token.strip()) > 15:
                entries.append((len(entries) + 1, f"[{len(entries) + 1}]", " ".join(token.split())))
        if len(entries) >= 2:
            return entries

    lines = ref_text.splitlines()
    entries = []

    # Check for [1], [2] style
    numeric_bracket_pattern = re.compile(r'^\s*\[(\d+)\]\s*(.*)$')
    # Check for 1., 2. style
    numbered_dot_pattern = re.compile(r'^\s*(\d+)[\.:]\s+(.*)$')
    # Check for 1 Author style without punctuation after number
    numbered_space_pattern = re.compile(r'^\s*(\d+)\s+([A-Z][A-Za-z\s,\.\-&]+.*)$')
    # Check for APA author (year) style at line start
    apa_start_pattern = re.compile(r'^[A-Z][A-Za-z\s,\.\-&]+\s*\((19\d{2}|20\d{2})\)')

    current_idx = None
    current_marker = ""
    current_lines = []

    # Detect predominant style
    total_bracket = len(re.findall(r'^\s*\[\d+\]', ref_text, re.MULTILINE))
    total_dot = len(re.findall(r'^\s*\d+[\.:]\s+', ref_text, re.MULTILINE))
    total_num_space = len(re.findall(r'^\s*\d+\s+[A-Z]', ref_text, re.MULTILINE))

    if total_bracket >= 2:
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

    elif total_num_space >= 2:
        for line in lines:
            m = numbered_space_pattern.match(line)
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

    cleaned_entries = []
    for idx, marker, raw in entries:
        clean_raw = " ".join(raw.split())
        if len(clean_raw) > 15:
            cleaned_entries.append((idx or len(cleaned_entries) + 1, marker, clean_raw))

    return cleaned_entries

def extract_reference_title(raw_text: str) -> Optional[str]:
    """
    Extracts the publication title from a raw reference string with high precision.
    Supports IEEE, APA, Harvard, Chicago, Nature, Science, and ACM formats while
    safely handling author initials, numbers in titles, subtitles, and punctuation.
    """
    if not raw_text:
        return None

    # Strip leading numerical markers like "[1]", "1.", "1)", "(1)"
    text_clean = re.sub(r'^\s*(?:\[\d+\]|\(\d+\)|\d+[\.:\)]|\d+\s+)\s*', '', raw_text).strip()

    # 1. Quoted titles: "Title of Paper", “Title”, 'Title'
    quote_match = re.search(r'["“\'‘«]([^"”\'’»]{8,300})["”\'’»]', text_clean)
    if quote_match:
        cand = quote_match.group(1).strip().rstrip(".,")
        if len(cand) >= 10 and not any(w in cand.lower() for w in ["vol.", "pp.", "proceedings of", "http://", "https://"]):
            return cand

    # 2. APA style: Author (Year[a-z]?). Title of Work. Journal / Publisher...
    # Uses lookahead to stop before journal/venue indicator or next section
    apa_match = re.search(r'\((?:19\d{2}|20\d{2})[a-z]?\)[\.:,]?\s+([A-Za-z0-9][^\n\r]{7,300}?)(?=\.\s+(?:In\s|Proc|Journal|Vol|arXiv|doi|http|https|[A-Z][a-z]+|\d+)|$)', text_clean)
    if apa_match:
        cand = apa_match.group(1).strip().rstrip(".,")
        # Strip trailing dot if not an abbreviation
        if len(cand) >= 10 and not any(w in cand.lower() for w in ["vol.", "pp.", "proceedings"]):
            return cand

    # 3. Harvard / Elsevier style: Authors, Year. Title of paper. Journal...
    harvard_match = re.search(r'(?:,\s*|\.\s*)(?:19\d{2}|20\d{2})[a-z]?[\.,]\s+([A-Za-z0-9][^\n\r]{7,300}?)(?=\.\s+(?:In\s|Proc|Journal|Vol|arXiv|doi|http|https|[A-Z][a-z]+|\d+)|$)', text_clean)
    if harvard_match:
        cand = harvard_match.group(1).strip().rstrip(".,")
        if len(cand) >= 10 and not any(w in cand.lower() for w in ["vol.", "pp.", "proceedings"]):
            return cand

    # 4. In-style: "Title. In: Proceedings of..." or "Title. In Advances in..."
    in_match = re.search(r'([A-Za-z0-9][^\.]{8,250})\.\s*(?:In\s|In:|in\s)', text_clean)
    if in_match:
        cand = in_match.group(1).strip().rstrip(".,")
        if len(cand) >= 10 and not any(w in cand.lower() for w in ["vol.", "pp.", "proceedings"]):
            return cand

    # 5. Sentence segment analysis: protects against splitting on author initials like "D. ", "A. "
    masked = re.sub(r'\b([A-Z])\.\s*', r'\1_DOT_ ', text_clean)
    for abbr in ["et al.", "eds.", "ed.", "vol.", "no.", "pp.", "trans.", "univ.", "dept.", "inc.", "co."]:
        masked = masked.replace(abbr, abbr.replace(".", "_DOT_"))

    parts = re.split(r'\.\s+', masked)
    if len(parts) >= 2:
        for p in parts[1:]:
            cand = p.replace("_DOT_", ".").strip().rstrip(".,")
            # Exclude short fragments, page numbers, or venue indicators
            if len(cand) >= 14 and not any(w in cand.lower() for w in ["vol.", "pp.", "pages", "proceedings", "doi:", "http://", "https://", "isbn"]):
                return cand

    # 6. Fallback: segment following year
    year_match = re.search(r'\b(?:19\d{2}|20\d{2})\b[\.,]?\s+(.+)', text_clean)
    if year_match:
        post_year = year_match.group(1).strip()
        first_segment = re.split(r'\.\s+', post_year)[0].strip().rstrip(".,")
        if len(first_segment) >= 12 and not any(w in first_segment.lower() for w in ["vol.", "pp.", "doi:"]):
            return first_segment

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
