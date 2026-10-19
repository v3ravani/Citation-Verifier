import re
from typing import Optional, List

# Standard DOI pattern: 10.NNNN/...
DOI_REGEX = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)', re.IGNORECASE)

# Year pattern: 1900-2099
YEAR_REGEX = re.compile(r'\b(19\d{2}|20\d{2})\b')

def extract_doi(text: str) -> Optional[str]:
    """
    Extracts and standardizes a DOI from a text string.
    Removes trailing periods, commas, or parentheses.
    """
    if not text:
        return None
    match = DOI_REGEX.search(text)
    if not match:
        return None
    doi = match.group(1)
    # Clean trailing punctuation often attached in citations
    doi = doi.rstrip(".,;)>]")
    return doi.lower()

def extract_year(text: str) -> Optional[int]:
    """
    Extracts the most likely publication year from a reference string.
    Prioritizes parenthesized years like (2021) or years near the beginning/end.
    """
    if not text:
        return None
    
    # Check parenthesized years first: (2020) or [2020]
    paren_match = re.search(r'[\(\[]\s*(19\d{2}|20\d{2})\s*[\)\]]', text)
    if paren_match:
        return int(paren_match.group(1))
        
    # Check general years
    years = YEAR_REGEX.findall(text)
    if years:
        # If multiple years, return the first plausible publication year (usually early in APA/IEEE)
        for y in years:
            year_int = int(y)
            if 1950 <= year_int <= 2030:
                return year_int
        return int(years[0])
        
    return None

def normalize_title(title: str) -> str:
    """
    Normalizes a title for fuzzy comparison:
    converts to lowercase, removes punctuation, trims extra spaces.
    """
    if not title:
        return ""
    # Strip quotes
    clean = re.sub(r'["“”\'‘’«»]', '', title)
    # Replace punctuation with space
    clean = re.sub(r'[^\w\s]', ' ', clean)
    # Collapse whitespace and lowercase
    return " ".join(clean.lower().split())

def extract_authors(raw_text: str) -> List[str]:
    """
    Heuristically extracts author names or primary author surnames from a reference.
    """
    if not raw_text:
        return []
        
    # Remove initial index like "[1]" or "1."
    text = re.sub(r'^\s*\[?\d+\]?\.?\s*', '', raw_text)
    
    # In APA/IEEE, authors usually appear before the year or title
    # Look for text before first open paren or before quotes
    author_chunk = text
    if "(" in text:
        author_chunk = text.split("(", 1)[0]
    elif '"' in text:
        author_chunk = text.split('"', 1)[0]
    elif '“' in text:
        author_chunk = text.split('“', 1)[0]
    elif ':' in text and len(text.split(':', 1)[0]) < 100:
        # Sometimes "Authors: Title"
        author_chunk = text.split(':', 1)[0]
        
    # Split by commas or 'and' / '&'
    tokens = re.split(r'[,;&]|\band\b', author_chunk)
    authors = []
    for token in tokens:
        cleaned = re.sub(r'[^A-Za-z\s\-]', '', token).strip()
        # Author names typically have at least 2 characters and no common reference words
        if 2 <= len(cleaned) <= 35:
            words = cleaned.split()
            # Ignore if contains words like 'eds', 'vol', 'pp', 'proceedings', 'journal'
            lower = cleaned.lower()
            if any(w in lower for w in ['vol', 'pp', 'proceedings', 'journal', 'editor', 'press', 'arxiv']):
                continue
            if words:
                authors.append(cleaned)
                
    return authors[:10]  # Cap at 10 authors
