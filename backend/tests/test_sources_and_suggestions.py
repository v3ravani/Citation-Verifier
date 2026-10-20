import pytest
import xml.etree.ElementTree as ET
from backend.app.metadata.arxiv import extract_arxiv_id, parse_arxiv_entry, ATOM_NS
from backend.app.metadata.openalex import reconstruct_openalex_abstract, parse_openalex_work
from backend.app.services.citation_suggester import (
    format_ieee,
    format_apa,
    format_bibtex,
    extract_search_terms,
    suggest_citations_for_paragraph,
)
from backend.app.services.pdf_annotator import generate_annotated_pdf
from backend.app.models.schemas import AnalysisResult
from backend.app.services.result_manager import get_analysis_result

def test_extract_arxiv_id():
    assert extract_arxiv_id("Attention Is All You Need arXiv:1706.03762v5 [cs.CL]") == "1706.03762v5"
    assert extract_arxiv_id("Paper preprint at 2103.00020") == "2103.00020"
    assert extract_arxiv_id("arxiv: 1409.0473") == "1409.0473"
    assert extract_arxiv_id("Standard nature paper without preprint") is None

def test_parse_arxiv_entry():
    sample_xml = """<entry xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
        <id>http://arxiv.org/abs/1706.03762v1</id>
        <title> Attention Is All You Need </title>
        <summary> The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. </summary>
        <published>2017-06-12T17:57:34Z</published>
        <author><name>Ashish Vaswani</name></author>
        <author><name>Noam Shazeer</name></author>
        <arxiv:doi>10.5555/3295222.3295349</arxiv:doi>
    </entry>"""
    root = ET.fromstring(sample_xml)
    parsed = parse_arxiv_entry(root)
    assert parsed["title"] == "Attention Is All You Need"
    assert parsed["year"] == 2017
    assert len(parsed["authors"]) == 2
    assert "Ashish Vaswani" in parsed["authors"]
    assert parsed["venue"] == "arXiv Preprint"
    assert "recurrent or convolutional" in parsed["abstract"]

def test_reconstruct_openalex_abstract():
    inverted = {
        "Attention": [0],
        "is": [1],
        "all": [2],
        "you": [3],
        "need": [4]
    }
    reconstructed = reconstruct_openalex_abstract(inverted)
    assert reconstructed == "Attention is all you need"
    assert reconstruct_openalex_abstract(None) is None

def test_parse_openalex_work():
    raw_work = {
        "title": "Deep Learning",
        "publication_year": 2015,
        "doi": "https://doi.org/10.1038/nature14539",
        "authorships": [
            {"author": {"display_name": "Yann LeCun"}},
            {"author": {"display_name": "Yoshua Bengio"}},
            {"author": {"display_name": "Geoffrey Hinton"}},
        ],
        "primary_location": {
            "source": {"display_name": "Nature"},
            "landing_page_url": "https://www.nature.com/articles/nature14539"
        },
        "cited_by_count": 55000,
        "abstract_inverted_index": {
            "Deep": [0],
            "learning": [1],
            "allows": [2],
            "computational": [3],
            "models": [4]
        }
    }
    parsed = parse_openalex_work(raw_work)
    assert parsed["title"] == "Deep Learning"
    assert parsed["year"] == 2015
    assert parsed["doi"] == "10.1038/nature14539"
    assert len(parsed["authors"]) == 3
    assert parsed["venue"] == "Nature"
    assert parsed["citation_count"] == 55000
    assert "Deep learning allows" in parsed["abstract"]

def test_citation_formatters():
    authors = ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"]
    title = "Attention is all you need"
    venue = "Advances in Neural Information Processing Systems"
    year = 2017
    doi = "10.5555/3295222.3295349"

    ieee = format_ieee(authors, title, venue, year, doi)
    assert "A. Vaswani et al." in ieee
    assert '"Attention is all you need"' in ieee
    assert "2017" in ieee

    apa = format_apa(authors, title, venue, year, doi)
    assert "Vaswani, A." in apa
    assert "(2017)" in apa

    bibtex = format_bibtex(authors, title, venue, year, doi)
    assert "@inproceedings{" in bibtex
    assert "vaswani2017attention" in bibtex
    assert "title = {{Attention is all you need}}" in bibtex

def test_extract_search_terms():
    sentence = "We show that convolutional networks conclusively outperform older recurrent neural networks on image classification."
    terms = extract_search_terms(sentence)
    assert "convolutional" in terms.lower()
    assert "networks" in terms.lower()
    assert "classification" in terms.lower()
    assert "that" not in terms.split()
    assert "we" not in terms.split()

@pytest.mark.asyncio
async def test_citation_suggester_empty():
    res = await suggest_citations_for_paragraph("   ")
    assert res.claims_analyzed == 0
    assert len(res.results) == 0

def test_annotated_pdf_generation_content():
    loaded = get_analysis_result("eb774d3c80ab6663")
    assert loaded is not None
    out_pdf = generate_annotated_pdf("eb774d3c80ab6663", loaded)
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 5000
