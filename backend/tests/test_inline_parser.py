import pytest
from backend.app.citations.inline_parser import (
    expand_numeric_range,
    split_into_sentences,
    extract_in_text_citations_from_pages,
)

def test_expand_numeric_range_simple():
    assert expand_numeric_range("1") == [1]
    assert expand_numeric_range("1, 2, 3") == [1, 2, 3]

def test_expand_numeric_range_hyphen():
    assert expand_numeric_range("3-5") == [3, 4, 5]
    assert expand_numeric_range("1, 3-5, 8") == [1, 3, 4, 5, 8]
    assert expand_numeric_range("10–12") == [10, 11, 12]  # en-dash

def test_expand_numeric_range_sanity():
    # Protection against inverted or massive range
    assert expand_numeric_range("5-2") == [5]
    assert expand_numeric_range("1-1000") == [1]

def test_split_into_sentences():
    text = "Recent models achieve great results [1]. For example, Vaswani et al. proposed Transformers. Does this scale? Yes, it scales well."
    sentences = split_into_sentences(text)
    assert len(sentences) >= 3
    # Check that 'et al.' does not break the sentence prematurely
    assert any("Vaswani et al. proposed Transformers" in s for s in sentences)

def test_extract_in_text_citations():
    pages = [{
        "page_number": 1,
        "text": "Deep neural networks have achieved remarkable breakthroughs in computer vision [1]. Recent self-attention models [2, 4-5] extend this capability. However, Smith et al. (2020) demonstrated notable limitations in low-resource regimes."
    }]
    citations = extract_in_text_citations_from_pages(pages)
    assert len(citations) >= 3
    
    # Check numeric [1]
    c1 = next(c for c in citations if c["marker"] == "[1]")
    assert c1["target_ids"] == [1]
    assert "computer vision" in c1["sentence"]

    # Check range [2, 4-5]
    c2 = next(c for c in citations if "[2, 4-5]" in c["marker"])
    assert c2["target_ids"] == [2, 4, 5]

    # Check author-year
    c3 = next(c for c in citations if "Smith et al." in c["marker"])
    assert c3["target_year"] == 2020
