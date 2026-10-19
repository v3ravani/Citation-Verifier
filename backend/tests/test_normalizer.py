import pytest
from backend.app.citations.normalizer import (
    extract_doi,
    extract_year,
    normalize_title,
    extract_authors,
)

def test_extract_doi():
    text1 = "Paper available at https://doi.org/10.1145/3372278.3390678."
    assert extract_doi(text1) == "10.1145/3372278.3390678"

    text2 = "doi: 10.1038/s41586-020-2649-2; published in Nature"
    assert extract_doi(text2) == "10.1038/s41586-020-2649-2"

    text3 = "No DOI in this reference text."
    assert extract_doi(text3) is None

def test_extract_year():
    assert extract_year("Smith, J. (2021). Neural approaches...") == 2021
    assert extract_year("Published in Proc. IEEE, 2018, pp. 10-15") == 2018
    assert extract_year("No year mentioned here") is None

def test_normalize_title():
    t1 = "Attention Is All You Need!"
    t2 = "attention is all you need"
    assert normalize_title(t1) == normalize_title(t2)

    t3 = "BERT: Pre-training of Deep Bidirectional Transformers..."
    assert "pre training of deep bidirectional transformers" in normalize_title(t3)

def test_extract_authors():
    ref = "A. Vaswani, N. Shazeer, N. Parmar, and J. Uszkoreit, 'Attention is all you need,' in NeurIPS 2017."
    authors = extract_authors(ref)
    assert len(authors) >= 2
    assert any("Vaswani" in a for a in authors)
