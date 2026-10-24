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
    lines.append(f"User verified records:      {getattr(result.summary, 'user_verified', 0)}")
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
    md.append("This report was deterministically compiled by Citation Verifier across 10 authoritative scholarly registries: Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite, PubMed/MEDLINE, DOAJ, and HAL Open Science. Semantic context relevance is evaluated locally with Sentence-BERT (`all-MiniLM-L6-v2`) and FAISS vector indexing.")
    return "\n".join(md)

def generate_html_report(result: AnalysisResult) -> str:
    """Generates an executive, print-ready, standalone institutional HTML audit report."""
    p_title = result.paper.title_guess or result.paper.filename
    avg_score = result.summary.average_integrity_score
    retracted = result.summary.retracted_citations_count
    total_refs = result.summary.references_detected
    ver_count = result.summary.verified_exact + result.summary.verified_probable
    hallucination_cnt = getattr(result.summary, "hallucination_risk_count", 0)

    rows = []
    for ref in result.references:
        status_label = ref.verification.status.replace("_", " ").title()
        score = ref.overall_score if ref.overall_score is not None else ref.verification.verification_score
        title = (ref.external.title if ref.external and ref.external.title else ref.parsed.title) or ref.raw_text[:50]
        authors = ", ".join(ref.external.authors[:3]) if ref.external and ref.external.authors else ", ".join(ref.parsed.authors[:3])
        year = ref.external.year if ref.external and ref.external.year else ref.parsed.year
        doi = ref.external.doi if ref.external and ref.external.doi else ref.parsed.doi
        
        status_color = "#10b981" if ref.verification.status == "verified_exact" else ("#3b82f6" if ref.verification.status == "verified_probable" else ("#f59e0b" if ref.verification.status == "metadata_mismatch" else "#ef4444"))
        ret_badge = '<span class="badge badge-danger">RETRACTED</span>' if ref.is_retracted else '<span class="badge badge-neutral">Clean</span>'
        hal_badge = f'<span class="badge badge-{"danger" if ref.hallucination_risk == "HIGH" else ("warning" if ref.hallucination_risk == "MODERATE" else "success")}">{ref.hallucination_risk}</span>' if hasattr(ref, "hallucination_risk") else ''
        doi_link = f'<a href="https://doi.org/{doi}" target="_blank">{doi}</a>' if doi else '<span style="color:#94a3b8">None</span>'

        rows.append(f"""
        <tr>
            <td><strong>#{ref.reference_id}</strong> <small style="color:#64748b">{ref.marker}</small></td>
            <td><span class="status-pill" style="border-left: 3px solid {status_color};">{status_label}</span></td>
            <td><strong>{score}</strong>/100</td>
            <td>
                <div style="font-weight:600; color:#0f172a;">{title}</div>
                <div style="font-size:0.8rem; color:#64748b;">{authors} ({year or 'n.d.'})</div>
            </td>
            <td><code style="font-size:0.75rem;">{ref.verification.source}</code></td>
            <td>{doi_link}</td>
            <td>{hal_badge}</td>
            <td>{ret_badge}</td>
        </tr>
        """)

    table_rows = "\n".join(rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Citation Verifier Executive Audit Report - {p_title}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #0f172a; margin: 0; padding: 2rem; background-color: #f8fafc; }}
    .container {{ max-width: 1050px; margin: 0 auto; background: #ffffff; padding: 2.5rem; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #e2e8f0; padding-bottom: 1.5rem; margin-bottom: 1.5rem; }}
    .brand {{ font-size: 1.5rem; font-weight: 800; color: #1e293b; letter-spacing: -0.02em; }}
    .subbrand {{ font-size: 0.85rem; color: #059669; font-weight: 600; text-transform: uppercase; }}
    .print-btn {{ background: #0f172a; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; cursor: pointer; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 1rem; }}
    .kpi-title {{ font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 0.25rem; }}
    .kpi-val {{ font-size: 1.75rem; font-weight: 800; color: #0f172a; }}
    .alert-box {{ background: #fef2f2; border: 1px solid #f87171; color: #991b1b; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.9rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.85rem; }}
    th {{ background: #f1f5f9; text-align: left; padding: 0.75rem 0.5rem; font-weight: 600; color: #334155; border-bottom: 2px solid #cbd5e1; }}
    td {{ padding: 0.75rem 0.5rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.45rem; border-radius: 4px; font-size: 0.7rem; font-weight: 700; }}
    .badge-danger {{ background: #fee2e2; color: #991b1b; }}
    .badge-warning {{ background: #fef3c7; color: #92400e; }}
    .badge-success {{ background: #dcfce7; color: #166534; }}
    .badge-neutral {{ background: #f1f5f9; color: #475569; }}
    .status-pill {{ padding-left: 0.5rem; }}
    .footer {{ margin-top: 2.5rem; border-top: 1px solid #e2e8f0; padding-top: 1rem; font-size: 0.75rem; color: #64748b; text-align: center; }}
    @media print {{
        body {{ background: white; padding: 0; }}
        .container {{ box-shadow: none; padding: 0; max-width: 100%; }}
        .print-btn {{ display: none; }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <div class="brand">VERITAS Citation Verifier</div>
            <div class="subbrand">Institutional Research Integrity Dossier</div>
            <div style="margin-top:0.5rem; font-size:0.9rem; color:#334155;">
                <strong>Document:</strong> {p_title} ({result.paper.pages} pages)<br>
                <strong>SHA-256:</strong> <code>{result.paper.sha256}</code> | <strong>Analyzed:</strong> {result.analyzed_at}
            </div>
        </div>
        <div>
            <button class="print-btn" onclick="window.print()">Print / Export PDF</button>
        </div>
    </div>

    {"<div class='alert-box'><strong>CRITICAL RETRACTION WARNING:</strong> " + str(retracted) + " publication(s) cited in this document have been flagged as retracted or subject to expressions of concern in global registries.</div>" if retracted > 0 else ""}

    <div class="kpi-grid">
        <div class="kpi-card" style="border-top: 3px solid #10b981;">
            <div class="kpi-title">Integrity Score</div>
            <div class="kpi-val" style="color: #059669;">{avg_score}<span style="font-size:1rem; font-weight:500;">/100</span></div>
            <div style="font-size:0.75rem; color:#059669; font-weight:600;">Institutional Consensus</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total References</div>
            <div class="kpi-val">{total_refs}</div>
            <div style="font-size:0.75rem; color:#64748b;">{ver_count} verified ({((ver_count / max(1, total_refs)) * 100):.1f}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Hallucination Risk</div>
            <div class="kpi-val" style="color: {'#dc2626' if hallucination_cnt > 0 else '#16a34a'};">{hallucination_cnt}</div>
            <div style="font-size:0.75rem; color:#64748b;">Non-existent citations flagged</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Retractions</div>
            <div class="kpi-val" style="color: {'#dc2626' if retracted > 0 else '#64748b'};">{retracted}</div>
            <div style="font-size:0.75rem; color:#64748b;">Global Retraction Watch</div>
        </div>
    </div>

    <h3 style="font-size: 1.1rem; color: #1e293b; margin-bottom: 0.5rem;">Audit Trail & Bibliographic Verification</h3>
    <table>
        <thead>
            <tr>
                <th>Ref</th>
                <th>Status</th>
                <th>Score</th>
                <th>Title & Authors</th>
                <th>Registries</th>
                <th>DOI</th>
                <th>Hallucination</th>
                <th>Retraction</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>

    <div class="footer">
        Verified deterministically by VERITAS Citation Verifier across 10 global registries (Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite, PubMed/MEDLINE, DOAJ, HAL). All context embeddings executed via Sentence-BERT (all-MiniLM-L6-v2) & FAISS vector search without third-party generative LLMs.
    </div>
</div>
</body>
</html>"""
    return html

def save_txt_report(paper_id: str, report_content: str) -> Path:
    clean_id = sanitize_paper_id(paper_id)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{clean_id}_report.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    return out_path

