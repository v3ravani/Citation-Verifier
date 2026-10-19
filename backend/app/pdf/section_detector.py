import re
from typing import Tuple, List, Dict, Any, Optional
from backend.app.core.logging_config import logger

# Common section headers for bibliographies
REFERENCE_HEADER_PATTERNS = [
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:REFERENCES|References)\b',
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:BIBLIOGRAPHY|Bibliography)\b',
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:WORKS\s+CITED|Works\s+Cited)\b',
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:LITERATURE\s+CITED|Literature\s+Cited)\b',
]

# Sections that might follow references
TERMINATING_HEADER_PATTERNS = [
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:APPENDIX|Appendix|Appendices)\b',
    r'^(?:[0-9IVXLCDM]+\.?\s*)?(?:BIOGRAPHY|Biography|BIOGRAPHIES|Biographies|Authors?\s+Biography)\b',
]

def detect_reference_section(
    pages_data: List[Dict[str, Any]]
) -> Tuple[str, str, Optional[int], Optional[str]]:
    """
    Detects and extracts the reference section from document pages.
    
    Returns:
        (body_text, references_text, start_page_number, warning_message)
    """
    combined_header_regex = re.compile("|".join(REFERENCE_HEADER_PATTERNS), re.IGNORECASE)
    terminating_regex = re.compile("|".join(TERMINATING_HEADER_PATTERNS), re.IGNORECASE)

    found_page_idx = None
    found_line_idx = None
    header_matched_text = None

    # Search backwards from the end of the document to find the primary References header
    # Usually in the last 40% of the document
    num_pages = len(pages_data)
    min_page_idx = max(0, int(num_pages * 0.4)) if num_pages > 2 else 0

    for page_idx in range(num_pages - 1, min_page_idx - 1, -1):
        lines = pages_data[page_idx]["text"].split("\n")
        for line_idx, line in enumerate(lines):
            stripped = line.strip()
            # Headers are typically relatively short
            if 3 <= len(stripped) <= 50 and combined_header_regex.match(stripped):
                found_page_idx = page_idx
                found_line_idx = line_idx
                header_matched_text = stripped
                break
        if found_page_idx is not None:
            break

    # If found by heading
    if found_page_idx is not None:
        logger.info(f"Detected reference section header '{header_matched_text}' on page {found_page_idx + 1}")
        
        # Build body text: all pages before found_page_idx, plus lines before header on found_page_idx
        body_parts = []
        for p in range(found_page_idx):
            body_parts.append(pages_data[p]["text"])
            
        target_page_lines = pages_data[found_page_idx]["text"].split("\n")
        body_parts.append("\n".join(target_page_lines[:found_line_idx]))
        body_text = "\n\n".join(body_parts)

        # Build reference text: lines after header on found_page_idx, plus following pages
        ref_parts = ["\n".join(target_page_lines[found_line_idx + 1:])]
        
        for p in range(found_page_idx + 1, num_pages):
            p_text = pages_data[p]["text"]
            # Check if an appendix or biography starts
            p_lines = p_text.split("\n")
            term_idx = None
            for l_idx, l in enumerate(p_lines):
                if 3 <= len(l.strip()) <= 40 and terminating_regex.match(l.strip()):
                    term_idx = l_idx
                    break
            if term_idx is not None:
                ref_parts.append("\n".join(p_lines[:term_idx]))
                break
            else:
                ref_parts.append(p_text)

        references_text = "\n\n".join(ref_parts)
        return body_text, references_text, pages_data[found_page_idx]["page_number"], None

    # Fallback heuristic: Look for bracketed entries [1], [2], [3] in the last 30% of pages
    logger.warning("No explicit reference header found. Trying heuristic fallback based on numbered entries.")
    for page_idx in range(num_pages - 1, min_page_idx - 1, -1):
        text = pages_data[page_idx]["text"]
        matches = re.findall(r'^\s*\[\d+\]', text, re.MULTILINE)
        if len(matches) >= 3:
            # We found a page with dense references
            # Use this page as the start of references
            body_parts = [pages_data[p]["text"] for p in range(page_idx)]
            ref_parts = [pages_data[p]["text"] for p in range(page_idx, num_pages)]
            warning = "Reference section detected via heuristic pattern matching (no standard heading found)."
            return "\n\n".join(body_parts), "\n\n".join(ref_parts), pages_data[page_idx]["page_number"], warning

    # If completely not found
    warning = "Could not detect a distinct reference section in the document."
    logger.warning(warning)
    full_text = "\n\n".join([p["text"] for p in pages_data])
    return full_text, "", None, warning
