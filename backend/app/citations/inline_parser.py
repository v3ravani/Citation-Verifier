import re
from typing import List, Dict, Any, Optional

# Match numeric bracket citations like [1], [1, 2], [3-5], [2, 4-6, 9]
NUMERIC_CITATION_PATTERN = re.compile(r'\[([0-9\s,\-–—]+)\]')

# Match author-year citations like (Smith, 2020), (Smith & Jones, 2021), (Smith et al., 2020)
AUTHOR_YEAR_PAREN_PATTERN = re.compile(
    r'\(([A-Z][A-Za-z\s,\.\-&]+(?:et\s+al\.?)?),\s*(19\d{2}|20\d{2})\)'
)

# Match narrative citations like Smith et al. (2020) or Jones and Wang (2019)
NARRATIVE_AUTHOR_YEAR_PATTERN = re.compile(
    r'\b([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?)\s+\((19\d{2}|20\d{2})\)'
)

def expand_numeric_range(citation_inner: str) -> List[int]:
    """
    Expands bracket contents like "1, 3-5, 8" into [1, 3, 4, 5, 8].
    Protects against malformed numbers or negative numbers.
    """
    results = []
    # Normalize dashes
    normalized = citation_inner.replace("–", "-").replace("—", "-")
    parts = normalized.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            dash_parts = part.split("-")
            if len(dash_parts) == 2 and dash_parts[0].strip().isdigit() and dash_parts[1].strip().isdigit():
                start_n = int(dash_parts[0].strip())
                end_n = int(dash_parts[1].strip())
                # Range sanity check: range should not be inverted or unreasonably large (<= 25)
                if 1 <= start_n <= end_n and (end_n - start_n) <= 25:
                    results.extend(list(range(start_n, end_n + 1)))
                else:
                    results.append(start_n)
            elif dash_parts[0].strip().isdigit():
                results.append(int(dash_parts[0].strip()))
        elif part.isdigit():
            results.append(int(part))
            
    # Return unique sorted integers
    return sorted(list(set(results)))

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences while respecting common academic abbreviations
    (e.g., et al., e.g., i.e., Fig., Vol., pp.).
    """
    if not text:
        return []
        
    # Replace newlines with spaces within sentences
    cleaned = re.sub(r'\s+', ' ', text)
    
    # Protect common abbreviations by temporarily masking periods
    protected = cleaned
    abbrevs = ["et al.", "e.g.", "i.e.", "Fig.", "Figs.", "Ref.", "Refs.", "Eq.", "Eqs.", "Vol.", "No.", "pp.", "vs.", "al."]
    for idx, ab in enumerate(abbrevs):
        protected = protected.replace(ab, f"__ABBR{idx}__")
        
    # Split on sentence boundaries: period, question mark, exclamation mark followed by space and capital letter or bracket
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z\[\(\"“])', protected)
    
    # Restore abbreviations
    final_sentences = []
    for s in raw_sentences:
        restored = s
        for idx, ab in enumerate(abbrevs):
            restored = restored.replace(f"__ABBR{idx}__", ab)
        restored = restored.strip()
        if len(restored) > 10:
            final_sentences.append(restored)
            
    return final_sentences

def extract_in_text_citations_from_pages(
    pages_data: List[Dict[str, Any]],
    max_page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extracts citation occurrences with sentence context windows from body pages.
    """
    occurrences = []
    context_counter = 1

    for page in pages_data:
        p_num = page["page_number"]
        if max_page and p_num > max_page:
            continue
            
        p_text = page["text"]
        sentences = split_into_sentences(p_text)
        
        for idx, sent in enumerate(sentences):
            prev_sent = sentences[idx - 1] if idx > 0 else ""
            next_sent = sentences[idx + 1] if idx + 1 < len(sentences) else ""
            full_context = f"{prev_sent} {sent} {next_sent}".strip()

            # 1. Numeric citations
            for num_match in NUMERIC_CITATION_PATTERN.finditer(sent):
                inner_str = num_match.group(1).strip()
                ref_nums = expand_numeric_range(inner_str)
                # Filter out obvious false positives (e.g. single year in brackets [2020] or math formula)
                if not ref_nums or any(n > 500 for n in ref_nums):
                    continue
                occurrences.append({
                    "context_id": context_counter,
                    "marker": num_match.group(0),
                    "type": "numeric",
                    "target_ids": ref_nums,
                    "target_authors": [],
                    "target_year": None,
                    "sentence": sent,
                    "previous_sentence": prev_sent,
                    "next_sentence": next_sent,
                    "full_context": full_context,
                    "page": p_num,
                })
                context_counter += 1

            # 2. Author-year parenthetical
            for ay_match in AUTHOR_YEAR_PAREN_PATTERN.finditer(sent):
                raw_authors = ay_match.group(1).strip()
                year = int(ay_match.group(2))
                occurrences.append({
                    "context_id": context_counter,
                    "marker": ay_match.group(0),
                    "type": "author_year",
                    "target_ids": [],
                    "target_authors": [raw_authors],
                    "target_year": year,
                    "sentence": sent,
                    "previous_sentence": prev_sent,
                    "next_sentence": next_sent,
                    "full_context": full_context,
                    "page": p_num,
                })
                context_counter += 1

            # 3. Narrative author-year: Smith et al. (2020)
            for narr_match in NARRATIVE_AUTHOR_YEAR_PATTERN.finditer(sent):
                raw_authors = narr_match.group(1).strip()
                year = int(narr_match.group(2))
                marker = f"{raw_authors} ({year})"
                occurrences.append({
                    "context_id": context_counter,
                    "marker": marker,
                    "type": "narrative_author_year",
                    "target_ids": [],
                    "target_authors": [raw_authors],
                    "target_year": year,
                    "sentence": sent,
                    "previous_sentence": prev_sent,
                    "next_sentence": next_sent,
                    "full_context": full_context,
                    "page": p_num,
                })
                context_counter += 1

    return occurrences
