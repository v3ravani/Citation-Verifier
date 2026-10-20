import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from backend.app.core.paths import UPLOADS_DIR
from backend.app.core.logging_config import logger
from backend.app.models.schemas import (
    PaperMetadata,
    ReferenceItem,
    AnalysisSummary,
    CitationGraph,
    CitationGraphNode,
    CitationGraphEdge,
    AnalysisResult,
    AlternativeReference,
)
from backend.app.pdf.extractor import extract_text_from_pdf, guess_paper_title
from backend.app.pdf.section_detector import detect_reference_section
from backend.app.citations.reference_parser import parse_all_references
from backend.app.citations.inline_parser import extract_in_text_citations_from_pages
from backend.app.citations.mapper import map_citations_to_references
from backend.app.metadata.verifier import verify_reference
from backend.app.scoring.metadata_score import calculate_metadata_score
from backend.app.scoring.citation_score import calculate_overall_citation_score
from backend.app.nlp.embeddings import generate_embeddings
from backend.app.nlp.similarity import classify_semantic_similarity
from backend.app.nlp.overclaim import analyze_claim_strength
from backend.app.search.faiss_index import ReferenceVectorIndex
from backend.app.services.result_manager import save_analysis_result, save_extracted_text
from backend.app.services.report_generator import generate_txt_report, save_txt_report

async def run_verification_pipeline(
    paper_id: str,
    filename: str,
    sha256: str,
    pdf_path: Path
) -> AnalysisResult:
    """
    Executes the comprehensive Citation Verifier pipeline.
    """
    logger.info(f"Starting verification pipeline for paper {paper_id} ({filename})")

    # Step 1: PDF text extraction
    full_text, pages_data = extract_text_from_pdf(pdf_path)
    title_guess = guess_paper_title(full_text, pages_data)
    save_extracted_text(paper_id, full_text)

    # Step 2: Reference section detection
    body_text, ref_section_text, start_page, section_warning = detect_reference_section(pages_data)

    # Step 3: Bibliography parsing
    parsed_refs_with_markers = parse_all_references(ref_section_text)
    parsed_refs = [ref for _, ref in parsed_refs_with_markers]

    # Step 4: In-text citation extraction
    max_body_page = (start_page - 1) if start_page else len(pages_data)
    raw_occurrences = extract_in_text_citations_from_pages(pages_data, max_page=max_body_page)

    # Step 5: Citation-to-reference mapping
    mapped_citations = map_citations_to_references(raw_occurrences, parsed_refs)

    # Step 6: Metadata verification against Crossref & Semantic Scholar
    verified_items: List[ReferenceItem] = []
    for marker, ref in parsed_refs_with_markers:
        try:
            verif_res, ext_rec = await verify_reference(ref)
        except Exception as e:
            logger.error(f"Error verifying reference #{ref.reference_id}: {e}")
            from backend.app.models.schemas import VerificationResult
            verif_res = VerificationResult(
                status="api_unavailable",
                source="error",
                title_similarity=0.0,
                author_match=0.0,
                verification_score=0.0,
                notes=[f"Verification error: {str(e)}"]
            )
            ext_rec = None

        meta_breakdown = calculate_metadata_score(
            doi_match=verif_res.doi_match,
            title_similarity=verif_res.title_similarity,
            author_match=verif_res.author_match,
            year_match=verif_res.year_match,
            doi_present_in_ref=bool(ref.doi)
        )
        verif_res.verification_score = meta_breakdown["total_metadata_score"]

        # Initial review flags
        review_flags = []
        is_retracted = bool(ext_rec and ext_rec.is_retracted)
        if is_retracted:
            review_flags.append("RETRACTION WARNING: This cited work is flagged as retracted or subject to concern in academic registries.")

        if verif_res.status == "metadata_mismatch":
            review_flags.append("Metadata discrepancy detected between citation and scholarly record.")
        elif verif_res.status == "unverified":
            review_flags.append("No verified scholarly record found. Potentially hallucinated, obscure, or malformed.")
        elif verif_res.status == "api_unavailable":
            review_flags.append("External verification APIs were unreachable.")

        item = ReferenceItem(
            reference_id=ref.reference_id,
            marker=marker,
            raw_text=ref.raw_text,
            parsed=ref,
            verification=verif_res,
            external=ext_rec,
            citation_occurrences=mapped_citations.get(ref.reference_id, []),
            score_breakdown=meta_breakdown,
            review_flags=review_flags,
            is_retracted=is_retracted
        )
        verified_items.append(item)

    # Step 7: Local NLP & FAISS Semantic Analysis
    ref_search_texts = []
    ref_ids_for_index = []
    ref_titles_for_index = []

    for item in verified_items:
        # Use abstract if available; fall back to title + venue
        text_for_embedding = ""
        if item.external and item.external.abstract:
            text_for_embedding = f"{item.external.title or ''}. {item.external.abstract}".strip()
        elif item.external and item.external.title:
            text_for_embedding = item.external.title
        elif item.parsed.title:
            text_for_embedding = item.parsed.title
        else:
            text_for_embedding = item.raw_text

        ref_search_texts.append(text_for_embedding)
        ref_ids_for_index.append(item.reference_id)
        ref_titles_for_index.append(
            (item.external.title if item.external and item.external.title else item.parsed.title) or f"Ref {item.reference_id}"
        )

    ref_embeddings = generate_embeddings(ref_search_texts)
    vector_index = ReferenceVectorIndex(dimension=384)
    if ref_embeddings is not None and len(ref_embeddings) > 0:
        vector_index.build_index(ref_ids_for_index, ref_titles_for_index, ref_embeddings)

    # Process all citation occurrences
    all_context_texts = []
    context_ref_pairs = []

    for item in verified_items:
        for occ in item.citation_occurrences:
            all_context_texts.append(occ.full_context or occ.sentence)
            context_ref_pairs.append((item.reference_id, occ))

    context_embeddings = generate_embeddings(all_context_texts) if all_context_texts else None

    # Map search results and score each citation occurrence
    for idx, (ref_id, occ) in enumerate(context_ref_pairs):
        matched_item = next((it for it in verified_items if it.reference_id == ref_id), None)
        abstract = matched_item.external.abstract if (matched_item and matched_item.external) else None

        if context_embeddings is not None and idx < len(context_embeddings):
            ctx_vec = context_embeddings[idx]
            search_res = vector_index.search(ctx_vec, expected_ref_id=ref_id, top_k=3)

            # Cosine similarity is expected_similarity
            occ.semantic_similarity = search_res["expected_similarity"]
            occ.rank_among_references = search_res["expected_rank"]
            occ.total_candidates = len(ref_ids_for_index)
            occ.top_alternative_references = [
                AlternativeReference(
                    reference_id=alt["reference_id"],
                    title=alt["title"],
                    similarity=alt["similarity"]
                )
                for alt in search_res["top_alternatives"]
            ]

            # Classification
            classification_label, class_note = classify_semantic_similarity(occ.semantic_similarity)
            occ.classification = classification_label

            # Overclaim heuristic analysis
            is_overclaim, strength, terms, overclaim_note = analyze_claim_strength(
                sentence=occ.sentence,
                abstract=abstract,
                similarity=occ.semantic_similarity
            )
            occ.overclaim_flag = is_overclaim
            occ.claim_strength = strength
            occ.strong_claim_terms = terms
            occ.overclaim_reason = overclaim_note

            # Check if another reference ranked much higher
            if search_res["expected_rank"] and search_res["expected_rank"] > 2 and search_res["gap_to_top"] >= 0.20:
                alt_name = search_res["top_alternatives"][0]["title"] if search_res["top_alternatives"] else "another reference"
                warning = f"Context may be more relevant to Ref #{search_res['top_alternatives'][0]['reference_id']} ({alt_name[:40]}...)"
                if warning not in matched_item.review_flags:
                    matched_item.review_flags.append(warning)

            if is_overclaim and matched_item:
                flag_text = f"Potential overclaim in context: {terms[:2]}"
                if flag_text not in matched_item.review_flags:
                    matched_item.review_flags.append(flag_text)

        else:
            # Model unavailable or no abstract
            occ.classification = "unavailable"
            is_overclaim, strength, terms, overclaim_note = analyze_claim_strength(
                sentence=occ.sentence,
                abstract=abstract,
                similarity=None
            )
            occ.overclaim_flag = is_overclaim
            occ.claim_strength = strength
            occ.strong_claim_terms = terms
            occ.overclaim_reason = overclaim_note

    # Step 8: Calculate overall score for each reference item
    for item in verified_items:
        sims = [
            occ.semantic_similarity
            for occ in item.citation_occurrences
            if occ.semantic_similarity is not None
        ]
        overall, breakdown = calculate_overall_citation_score(
            metadata_score=item.verification.verification_score,
            context_similarities=sims
        )
        item.overall_score = overall
        item.score_breakdown.update(breakdown)

    # Step 9: Build Citation Graph
    graph_nodes: List[CitationGraphNode] = []
    graph_edges: List[CitationGraphEdge] = []

    # Center node = current paper
    paper_node_id = f"paper_{paper_id[:8]}"
    graph_nodes.append(CitationGraphNode(
        id=paper_node_id,
        label=filename[:25],
        type="paper",
        status="active",
        title=title_guess
    ))

    for item in verified_items:
        node_id = f"ref_{item.reference_id}"
        graph_nodes.append(CitationGraphNode(
            id=node_id,
            label=item.marker or f"[{item.reference_id}]",
            type="reference",
            status=item.verification.status,
            score=item.overall_score,
            title=(item.external.title if item.external and item.external.title else item.parsed.title) or item.raw_text[:60]
        ))
        weight = (item.overall_score / 100.0) if item.overall_score is not None else 0.5
        graph_edges.append(CitationGraphEdge(
            source=paper_node_id,
            target=node_id,
            weight=round(weight, 2),
            label="cites"
        ))

    citation_graph = CitationGraph(nodes=graph_nodes, edges=graph_edges)

    # Step 10: Compile Summary Statistics
    total_refs = len(verified_items)
    v_exact = sum(1 for it in verified_items if it.verification.status == "verified_exact")
    v_prob = sum(1 for it in verified_items if it.verification.status == "verified_probable")
    v_mismatch = sum(1 for it in verified_items if it.verification.status == "metadata_mismatch")
    v_unverif = sum(1 for it in verified_items if it.verification.status == "unverified")
    v_api_unavail = sum(1 for it in verified_items if it.verification.status == "api_unavailable")

    all_occs = [occ for it in verified_items for occ in it.citation_occurrences]
    c_strong = sum(1 for o in all_occs if o.classification == "strongly_related")
    c_mod = sum(1 for o in all_occs if o.classification == "moderately_related")
    c_weak = sum(1 for o in all_occs if o.classification == "weakly_related")
    c_unrelated = sum(1 for o in all_occs if o.classification == "likely_unrelated")
    c_unavail = sum(1 for o in all_occs if o.classification == "unavailable")
    overclaim_cnt = sum(1 for o in all_occs if o.overclaim_flag)
    retracted_cnt = sum(1 for it in verified_items if it.is_retracted)
    
    scored_items = [it.overall_score for it in verified_items if it.overall_score is not None]
    avg_score = round(sum(scored_items) / max(1, len(scored_items)), 1) if scored_items else 0.0

    all_sources = sorted(list(set(
        src
        for it in verified_items
        if it.external and it.external.sources_verified
        for src in it.external.sources_verified
    )))
    if not all_sources:
        all_sources = ["crossref", "semantic_scholar", "openalex", "arxiv", "europe_pmc", "dblp", "datacite"]

    summary = AnalysisSummary(
        references_detected=total_refs,
        verified_exact=v_exact,
        verified_probable=v_prob,
        metadata_mismatch=v_mismatch,
        unverified=v_unverif,
        api_unavailable=v_api_unavail,
        citation_occurrences=len(all_occs),
        strong_context_match=c_strong,
        moderate_context_match=c_mod,
        weak_context_match=c_weak,
        likely_unrelated=c_unrelated,
        context_unavailable=c_unavail,
        overclaim_flags=overclaim_cnt,
        retracted_citations_count=retracted_cnt,
        average_integrity_score=avg_score,
        sources_queried=all_sources,
        graph_nodes_count=len(graph_nodes),
        graph_edges_count=len(graph_edges),
    )

    paper_meta = PaperMetadata(
        id=paper_id,
        filename=filename,
        sha256=sha256,
        pages=len(pages_data),
        title_guess=title_guess,
        upload_time=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    methodology_info = {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "vector_search": "FAISS IndexFlatIP (Normalized Inner Product)",
        "metadata_apis": [
            "Crossref REST API",
            "Semantic Scholar Graph API",
            "OpenAlex Global Works API",
            "arXiv Preprints API",
            "Europe PMC Life Sciences API",
            "DBLP Computer Science Bibliography API",
            "DataCite Global Registry API"
        ],
        "similarity_thresholds": {
            "strongly_related": ">= 0.78",
            "moderately_related": "0.62 - 0.77",
            "weakly_related": "0.45 - 0.61",
            "likely_unrelated": "< 0.45",
        },
        "score_weighting": "55% Metadata Verification, 45% Context Semantic Relevance",
        "overclaim_heuristic": "Assertion vocabulary matched with abstract semantic support",
    }

    result = AnalysisResult(
        paper=paper_meta,
        summary=summary,
        references=verified_items,
        graph=citation_graph,
        methodology=methodology_info,
        analyzed_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    # Persist JSON result and TXT report
    save_analysis_result(paper_id, result)
    txt_report = generate_txt_report(result)
    save_txt_report(paper_id, txt_report)

    logger.info(f"Verification pipeline completed successfully for paper {paper_id}")
    return result
