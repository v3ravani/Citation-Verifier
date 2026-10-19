import pytest
from pathlib import Path
import fitz
from backend.app.services.pipeline import run_verification_pipeline
from backend.app.core.paths import UPLOADS_DIR, RESULTS_DIR

@pytest.mark.asyncio
async def test_full_pipeline_with_real_references(tmp_path):
    paper_text = """
Attention mechanisms have revolutionized natural language processing by enabling models to attend to different positions dynamically [1].
Recent foundational advances in deep neural architectures demonstrate profound impact across perception tasks [2].
However, claim analysis requires rigorous review [1].

REFERENCES
[1] A. Vaswani et al., "Attention is all you need," in Advances in Neural Information Processing Systems, 2017.
[2] Y. LeCun, Y. Bengio, and G. Hinton, "Deep learning," Nature, vol. 521, no. 7553, pp. 436-444, 2015. https://doi.org/10.1038/nature14539
    """

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Standard letter
    rect = fitz.Rect(50, 50, 560, 740)
    page.insert_textbox(rect, paper_text)
    test_pdf_path = tmp_path / "test_paper.pdf"
    doc.save(str(test_pdf_path))
    doc.close()

    paper_id = "test_e2e_paper_02"
    sha256 = "dummy_sha256_hash_for_testing_wrapped"

    result = await run_verification_pipeline(
        paper_id=paper_id,
        filename="attention_deep_learning_test.pdf",
        sha256=sha256,
        pdf_path=test_pdf_path
    )

    # Assertions
    assert result.paper.id == paper_id
    assert result.summary.references_detected == 2
    assert len(result.references) == 2
    assert result.references[0].reference_id == 1
    assert "Attention is all you need" in (result.references[0].parsed.title or result.references[0].raw_text)

    # Check in-text citations mapped
    assert len(result.references[0].citation_occurrences) >= 1
    occ = result.references[0].citation_occurrences[0]
    assert occ.marker == "[1]"
    assert "natural language processing" in occ.sentence

    # Check graph
    assert len(result.graph.nodes) >= 3
    assert len(result.graph.edges) >= 2

    # Check persisted files
    saved_json = RESULTS_DIR / f"{paper_id}.json"
    saved_txt = RESULTS_DIR / f"{paper_id}_report.txt"
    assert saved_json.exists()
    assert saved_txt.exists()

    # Clean up test artifacts
    saved_json.unlink(missing_ok=True)
    saved_txt.unlink(missing_ok=True)
