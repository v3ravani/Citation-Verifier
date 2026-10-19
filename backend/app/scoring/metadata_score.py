from typing import Optional, Dict

def calculate_metadata_score(
    doi_match: Optional[bool],
    title_similarity: float,
    author_match: float,
    year_match: Optional[bool],
    doi_present_in_ref: bool
) -> Dict[str, float]:
    """
    Computes transparent, explainable metadata verification score out of 100
    with exact component breakdown.
    """
    if doi_present_in_ref:
        # Standard weights: DOI=35, Title=40, Author=15, Year=10
        doi_pts = 35.0 if doi_match is True else 0.0
        title_pts = round(title_similarity * 40.0, 1)
        author_pts = round(author_match * 15.0, 1)
        year_pts = 10.0 if year_match is True else 0.0
    else:
        # DOI absent in extracted reference: Title=55, Author=25, Year=20
        doi_pts = 0.0
        title_pts = round(title_similarity * 55.0, 1)
        author_pts = round(author_match * 25.0, 1)
        year_pts = 20.0 if year_match is True else 0.0

    total = round(min(100.0, doi_pts + title_pts + author_pts + year_pts), 1)

    return {
        "total_metadata_score": total,
        "doi_points": doi_pts,
        "title_points": title_pts,
        "author_points": author_pts,
        "year_points": year_pts,
    }
