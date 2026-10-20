import csv
import io
import re
from pathlib import Path
from backend.app.core.paths import RESULTS_DIR
from backend.app.models.schemas import AnalysisResult
from backend.app.services.result_manager import sanitize_paper_id
from backend.app.services.citation_suggester import format_bibtex

def generate_txt_report(result: AnalysisResult) -> str:
    """Generates a comprehensive human-readable TXT report from an AnalysisResult."""
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
    lines.append(f"Retracted citations flagged:{result.summary.retracted_citations_count}")
    lines.append(f"Average integrity score:    {result.summary.average_integrity_score} / 100")
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
        if ref.is_retracted:
            lines.append("RETRACTION STATUS:    [!] RETRACTED OR UNDER RETRACTION NOTICE")

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
                if ctx.overclaim_flag:
                    lines.append(f"    Heuristic Flag:      {ctx.overclaim_reason}")
        else:
            lines.append("In-Text Citation Contexts: None detected in body text.")

        lines.append("")
        lines.append("=" * 60)
        lines.append("")

    lines.append("METHODOLOGY & DISCLOSURES")
    lines.append("-------------------------")
    lines.append("- Multi-registry verification across Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, and DataCite.")
    lines.append("- Semantic relevance evaluated locally using sentence embeddings (all-MiniLM-L6-v2) and FAISS vector ranking.")
    lines.append("- Similarity scores and overclaim alerts are transparent heuristic indicators, not absolute determinations.")
    lines.append("- No external generative AI service was used.")
    return "\n".join(lines)

def generate_bibtex_export(result: AnalysisResult) -> str:
    """Generates standard clean BibTeX file for all verified references."""
    entries = []
    header = [
        f"% BibTeX exported by Citation Verifier",
        f"% Paper: {result.paper.title_guess or result.paper.filename}",
        f"% Verified entries: {result.summary.verified_exact + result.summary.verified_probable}/{result.summary.references_detected}",
        ""
    ]
    entries.append("\n".join(header))

    for ref in result.references:
        # Prefer external record fields if available
        if ref.external and ref.external.title:
            authors = ref.external.authors
            title = ref.external.title
            venue = ref.external.venue
            year = ref.external.year
            doi = ref.external.doi or ref.parsed.doi
        else:
            authors = ref.parsed.authors
            title = ref.parsed.title or ref.raw_text[:60]
            venue = ref.parsed.venue
            year = ref.parsed.year
            doi = ref.parsed.doi

        bib_entry = format_bibtex(authors, title, venue, year, doi)
        entries.append(bib_entry)
        entries.append("")

    return "\n".join(entries)

def generate_csv_export(result: AnalysisResult) -> str:
    """Generates an audit CSV spreadsheet string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Reference_ID",
        "Marker",
        "Verification_Status",
        "Integrity_Score",
        "Verified_Title",
        "Authors",
        "Year",
        "DOI",
        "Registries_Matched",
        "Retracted_Alert",
        "Citation_Occurrences_Count",
        "Overclaim_Flags_Count",
        "Review_Flags"
    ])

    for ref in result.references:
        title = (ref.external.title if ref.external and ref.external.title else ref.parsed.title) or ""
        authors = "; ".join(ref.external.authors if ref.external and ref.external.authors else ref.parsed.authors)
        year = ref.external.year if ref.external and ref.external.year else ref.parsed.year
        doi = ref.external.doi if ref.external and ref.external.doi else ref.parsed.doi
        score = ref.overall_score if ref.overall_score is not None else ref.verification.verification_score
        overclaim_cnt = sum(1 for o in ref.citation_occurrences if o.overclaim_flag)
        flags = " | ".join(ref.review_flags)

        writer.writerow([
            ref.reference_id,
            ref.marker,
            ref.verification.status,
            score,
            title,
            authors,
            year or "",
            doi or "",
            ref.verification.source,
            "YES" if ref.is_retracted else "NO",
            len(ref.citation_occurrences),
            overclaim_cnt,
            flags
        ])

    return output.getvalue()

def generate_markdown_report(result: AnalysisResult) -> str:
    """Generates an executive-grade Markdown audit report."""
    md = []
    p_title = result.paper.title_guess or result.paper.filename
    avg_score = result.summary.average_integrity_score
    retracted = result.summary.retracted_citations_count
    total_refs = result.summary.references_detected
    ver_count = result.summary.verified_exact + result.summary.verified_probable

    md.append(f"# Citation Verification & Research Integrity Audit")
    md.append(f"**Document**: `{result.paper.filename}`  ")
    md.append(f"**Analyzed**: `{result.analyzed_at}` | **Pages**: `{result.paper.pages}` | **SHA-256**: `{result.paper.sha256[:16]}...`  ")
    md.append("")
    md.append("## Executive Summary")
    md.append(f"| Metric | Result |")
    md.append(f"| :--- | :--- |")
    md.append(f"| **Overall Integrity Score** | **{avg_score} / 100** |")
    md.append(f"| **Total References** | {total_refs} |")
    md.append(f"| **Verified Exact / Probable** | {ver_count} ({((ver_count / max(1, total_refs)) * 100):.1f}%) |")
    md.append(f"| **Unverified / Potentially Hallucinated** | {result.summary.unverified} |")
    md.append(f"| **Metadata Mismatches** | {result.summary.metadata_mismatch} |")
    md.append(f"| **Retracted Works Flagged** | {retracted} |")
    md.append(f"| **In-Text Context Occurrences** | {result.summary.citation_occurrences} |")
    md.append(f"| **Overclaim Assertions Flagged** | {result.summary.overclaim_flags} |")
    md.append("")

    if retracted > 0:
        md.append("> [!CAUTION]")
        md.append(f"> **Critical Notice**: {retracted} cited publication(s) in this document have been flagged as RETRACTED or subject to expressions of concern in academic registries.")
        md.append("")

    md.append("## Reference Verification Table")
    md.append("| # | Marker | Status | Score | Title | Matched Registry | Retracted |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for ref in result.references:
        status_label = ref.verification.status.replace("_", " ").title()
        score = ref.overall_score if ref.overall_score is not None else ref.verification.verification_score
        title = (ref.external.title if ref.external and ref.external.title else ref.parsed.title) or ref.raw_text[:45]
        ret_label = "⚠️ **YES**" if ref.is_retracted else "No"
        md.append(f"| {ref.reference_id} | `{ref.marker}` | `{status_label}` | {score} | {title[:55]} | `{ref.verification.source}` | {ret_label} |")

    md.append("")
    md.append("## Methodology & Data Sources")
    md.append("This report was deterministically compiled by Citation Verifier across 7 public scholarly registries: Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, and DataCite. Semantic context relevance is evaluated locally with Sentence-BERT (`all-MiniLM-L6-v2`) and FAISS vector indexing.")
    return "\n".join(md)

def save_txt_report(paper_id: str, report_content: str) -> Path:
    clean_id = sanitize_paper_id(paper_id)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{clean_id}_report.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    return out_path
