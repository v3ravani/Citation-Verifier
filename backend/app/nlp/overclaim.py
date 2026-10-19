import re
from typing import Tuple, List, Optional

STRONG_CLAIM_PATTERNS = [
    r'\bproves?\b',
    r'\bproven\b',
    r'\balways\b',
    r'\bnever\b',
    r'\bguarantees?\b',
    r'\bcompletely\b',
    r'\beliminates?\b',
    r'\bdefinitive(?:ly)?\b',
    r'\buniversal(?:ly)?\b',
    r'\bsignificantly\s+superior\b',
    r'\bdramatically\s+(?:better|improves?|reduced)\b',
    r'\bconclusively\s+demonstrates?\b',
    r'\birrefutable\b',
    r'\bunquestionabl(?:e|y)\b',
    r'\bflawless(?:ly)?\b',
    r'\boptimal\s+across\s+all\b',
]

MODERATE_CLAIM_PATTERNS = [
    r'\bsuggests?\b',
    r'\bindicates?\b',
    r'\bmay\b',
    r'\bcould\b',
    r'\bassociated\s+with\b',
    r'\bobserved\b',
    r'\bsupports?\b',
    r'\bconsistent\s+with\b',
    r'\btends?\s+to\b',
]

def analyze_claim_strength(
    sentence: str,
    abstract: Optional[str] = None,
    similarity: Optional[float] = None
) -> Tuple[bool, str, List[str], Optional[str]]:
    """
    Evaluates whether a citation sentence uses strong conclusive assertion language
    relative to the available abstract and semantic alignment.
    
    Returns:
        (overclaim_flag, claim_strength, matched_terms, explanation_note)
    """
    if not sentence:
        return False, "neutral", [], None

    sentence_lower = sentence.lower()
    matched_strong = []

    for pattern in STRONG_CLAIM_PATTERNS:
        matches = re.findall(pattern, sentence_lower)
        if matches:
            matched_strong.extend(matches)

    matched_strong = list(set(matched_strong))

    # If no strong terms found, check moderate terms
    if not matched_strong:
        for pattern in MODERATE_CLAIM_PATTERNS:
            if re.search(pattern, sentence_lower):
                return False, "moderate", [], None
        return False, "neutral", [], None

    # Strong terms were found
    terms_repr = ", ".join(f"'{t}'" for t in matched_strong[:3])

    if similarity is not None and similarity < 0.65:
        return (
            True,
            "strong",
            matched_strong,
            f"Heuristic review flag: Citation sentence asserts conclusive phrasing ({terms_repr}) "
            f"with modest semantic similarity ({similarity:.2f}) to the cited abstract."
        )
    elif similarity is None:
        return (
            True,
            "strong",
            matched_strong,
            f"Heuristic review flag: Citation sentence employs assertive claim wording ({terms_repr}), "
            "but cited abstract was unavailable for verification."
        )
    else:
        # High similarity
        return (
            False,
            "strong",
            matched_strong,
            f"Conclusive wording noted ({terms_repr}), but semantic alignment with cited work is strong ({similarity:.2f})."
        )
