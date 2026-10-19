from pathlib import Path
from backend.app.core.paths import RESULTS_DIR
from backend.app.models.schemas import AnalysisResult
from backend.app.services.result_manager import sanitize_paper_id

def generate_txt_report(result: AnalysisResult) -> str:
    """
    Generates a comprehensive, human-readable TXT report from an AnalysisResult.
    """
    lines = []
    lines.append("CITATION VERIFIER REPORT")
    lines.append("========================")
    lines.append("")
    lines.append(f"Paper Title:    {result.paper.title_guess or 'Untitled'}")
    lines.append(f"Filename:       {result.paper.filename}")
    lines.append(f"Pages:          {result.paper.pages}")
    lines.append(f"Analysis ID:    {result.paper.id}")
    lines.append(f"SHA-256:        {result.paper.sha256}")
    lines.append(f"Analyzed At:    {result.analyzed_at}")
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-------")
    lines.append(f"References detected:        {result.summary.references_detected}")
    lines.append(f"Verified exact matches:     {result.summary.verified_exact}")
    lines.append(f"Probable matches:           {result.summary.verified_probable}")
    lines.append(f"Metadata mismatches:        {result.summary.metadata_mismatch}")
    lines.append(f"Unverified records:         {result.summary.unverified}")
    lines.append(f"Citation contexts analyzed: {result.summary.citation_occurrences}")
    lines.append(f"Strong context relevance:   {result.summary.strong_context_match}")
    lines.append(f"Moderate context relevance: {result.summary.moderate_context_match}")
    lines.append(f"Weak context relevance:     {result.summary.weak_context_match}")
    lines.append(f"Likely unrelated contexts:  {result.summary.likely_unrelated}")
    lines.append(f"Contexts unavailable:       {result.summary.context_unavailable}")
    lines.append(f"Potential overclaim flags:  {result.summary.overclaim_flags}")
    lines.append("")
    lines.append("DETAILED REFERENCE AUDIT")
    lines.append("========================")
    lines.append("")

    for ref in result.references:
        lines.append(f"REFERENCE #{ref.reference_id} {ref.marker}")
        lines.append("-" * 40)
        lines.append("Extracted Text:")
        lines.append(f"  {ref.raw_text}")
        lines.append("")
        
        status_label = ref.verification.status.replace("_", " ").title()
        lines.append(f"Verification Status:  {status_label}")
        lines.append(f"Verification Source:  {ref.verification.source}")
        lines.append(f"Verification Score:   {ref.verification.verification_score} / 100")
        lines.append(f"Title Similarity:     {ref.verification.title_similarity}")
        lines.append(f"Author Match:         {ref.verification.author_match}")
        lines.append(f"Year Match:           {'Yes' if ref.verification.year_match is True else ('No' if ref.verification.year_match is False else 'N/A')}")
        lines.append(f"DOI Match:            {'Yes' if ref.verification.doi_match is True else ('No' if ref.verification.doi_match is False else 'N/A')}")

        if ref.external:
            lines.append("")
            lines.append("Matched Scholarly Record:")
            lines.append(f"  Title:    {ref.external.title or 'N/A'}")
            lines.append(f"  Authors:  {', '.join(ref.external.authors) if ref.external.authors else 'N/A'}")
            lines.append(f"  Year:     {ref.external.year or 'N/A'}")
            lines.append(f"  Venue:    {ref.external.venue or 'N/A'}")
            lines.append(f"  DOI:      {ref.external.doi or 'N/A'}")
            lines.append(f"  URL:      {ref.external.url or 'N/A'}")
            if ref.external.abstract:
                preview = ref.external.abstract[:200] + ("..." if len(ref.external.abstract) > 200 else "")
                lines.append(f"  Abstract: {preview}")
            else:
                lines.append("  Abstract: Unavailable from external API")

        if ref.overall_score is not None:
            lines.append(f"Overall Citation Score: {ref.overall_score} / 100")
        else:
            lines.append("Overall Citation Score: Unavailable (insufficient semantic evidence)")

        if ref.review_flags:
            lines.append("Review Warnings:")
            for flag in ref.review_flags:
                lines.append(f"  [!] {flag}")

        if ref.citation_occurrences:
            lines.append("")
            lines.append(f"In-Text Citation Contexts ({len(ref.citation_occurrences)}):")
            for c_idx, ctx in enumerate(ref.citation_occurrences, start=1):
                lines.append(f"  Context {c_idx} (Page {ctx.page or 'N/A'}):")
                lines.append(f"    Target Sentence: \"{ctx.sentence}\"")
                if ctx.semantic_similarity is not None:
                    lines.append(f"    Semantic Similarity: {ctx.semantic_similarity:.3f}")
                    lines.append(f"    Classification:      {ctx.classification.replace('_', ' ').title()}")
                    lines.append(f"    Bibliography Rank:   {ctx.rank_among_references} of {ctx.total_candidates}")
                else:
                    lines.append("    Semantic Similarity: Unavailable (no abstract available)")
                if ctx.overclaim_flag:
                    lines.append(f"    Heuristic Flag:      {ctx.overclaim_reason}")
        else:
            lines.append("In-Text Citation Contexts: None detected in body text.")

        lines.append("")
        lines.append("=" * 60)
        lines.append("")

    lines.append("METHODOLOGY & DISCLOSURES")
    lines.append("-------------------------")
    lines.append("- Citation existence verified using Crossref and/or Semantic Scholar REST APIs.")
    lines.append("- Semantic relevance evaluated locally using sentence embeddings (all-MiniLM-L6-v2) and FAISS vector ranking.")
    lines.append("- Similarity scores and overclaim alerts are transparent heuristic indicators, not absolute determinations.")
    lines.append("- No external generative AI service was used.")
    lines.append("- For full methodology details, visit the Methodology section in Citation Verifier.")

    return "\n".join(lines)

def save_txt_report(paper_id: str, report_content: str) -> Path:
    clean_id = sanitize_paper_id(paper_id)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{clean_id}_report.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    return out_path
