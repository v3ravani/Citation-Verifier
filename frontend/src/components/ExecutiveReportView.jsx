import React from "react";
import { Download, Printer, ShieldCheck, ShieldAlert, Award, FileCheck, CheckCircle2, AlertTriangle, XCircle, ExternalLink, Code2, FileSpreadsheet, FileText } from "lucide-react";
import {
  getAnnotatedPdfExportUrl,
  getHtmlExportUrl,
  getBibtexExportUrl,
  getCsvExportUrl,
  getMarkdownExportUrl,
  getTxtExportUrl,
  getJsonExportUrl
} from "../api/client";

export default function ExecutiveReportView({ result, onSelectReference }) {
  if (!result) return null;

  const paper = result.paper || {};
  const summary = result.summary || {};
  const references = result.references || [];
  const methodology = result.methodology || {};

  const avgScore = summary.average_integrity_score || 0;
  const retracted = summary.retracted_citations_count || 0;
  const hallucinated = summary.hallucination_risk_count || 0;
  const totalRefs = summary.references_detected || 0;
  const verCount = (summary.verified_exact || 0) + (summary.verified_probable || 0);

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Report Header Card */}
      <div className="academic-card" style={{ padding: "1.75rem", marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "1.25rem", marginBottom: "1.25rem" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.35rem" }}>
              <ShieldCheck size={16} />
              <span>Institutional Research Integrity Dossier</span>
            </div>
            <h2 style={{ fontSize: "1.45rem", fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.02em", margin: "0 0 0.5rem 0" }}>
              {paper.title_guess || paper.filename}
            </h2>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
              <span><strong>Document:</strong> {paper.filename} ({paper.pages} pages)</span>
              <span><strong>SHA-256:</strong> <code>{paper.sha256 ? `${paper.sha256.slice(0, 20)}...` : paper.id}</code></span>
              <span><strong>Analyzed:</strong> {new Date(result.analyzed_at).toLocaleString()}</span>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => window.print()}
              style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
            >
              <Printer size={14} />
              <span>Print Dossier</span>
            </button>
            <a
              href={getHtmlExportUrl(paper.id)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
              style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
            >
              <ExternalLink size={14} />
              <span>Standalone HTML Dossier</span>
            </a>
          </div>
        </div>

        {/* Retraction Warning Banner */}
        {retracted > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "1rem", backgroundColor: "#fef2f2", border: "1px solid #f87171", borderRadius: "6px", color: "#991b1b", marginBottom: "1.25rem" }}>
            <ShieldAlert size={22} style={{ flexShrink: 0 }} />
            <div style={{ fontSize: "0.85rem", lineHeight: 1.45 }}>
              <strong>CRITICAL RETRACTION NOTICE:</strong> {retracted} publication(s) cited in this document are flagged as RETRACTED or subject to formal expressions of concern in global academic registries.
            </div>
          </div>
        )}

        {/* Executive Scorecard */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
          <div style={{ padding: "1rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Document Trust Score</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--accent-primary)", letterSpacing: "-0.02em" }}>
              {avgScore}<span style={{ fontSize: "1rem", fontWeight: 500 }}>/100</span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>Multi-Registry Consensus</div>
          </div>

          <div style={{ padding: "1rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Verified Literature</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "#059669" }}>
              {verCount} <span style={{ fontSize: "1rem", fontWeight: 500, color: "var(--text-muted)" }}>/ {totalRefs}</span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "#059669", fontWeight: 600 }}>
              {((verCount / max(1, totalRefs)) * 100).toFixed(0)}% Confirmation Rate
            </div>
          </div>

          <div style={{ padding: "1rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>Hallucination Risk</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: hallucinated > 0 ? "#dc2626" : "#059669" }}>
              {hallucinated}
            </div>
            <div style={{ fontSize: "0.75rem", color: hallucinated > 0 ? "#dc2626" : "var(--text-muted)", fontWeight: 600 }}>
              {hallucinated > 0 ? "Phantom References Detected" : "Zero Fabricated Records"}
            </div>
          </div>

          <div style={{ padding: "1rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase" }}>In-Text Contexts</div>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)" }}>
              {summary.citation_occurrences || 0}
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 500 }}>
              {summary.strong_context_match || 0} strong • {summary.overclaim_flags || 0} overclaims
            </div>
          </div>
        </div>

        {/* 10 Registries Accordion Badge Grid */}
        <div style={{ marginBottom: "1.5rem" }}>
          <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: "0.5rem" }}>
            Cross-Referenced Against 10 Authoritative Registries
          </h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {[
              { name: "Crossref", role: "Global DOIs & Publishers" },
              { name: "Semantic Scholar", role: "AI Citation Graph & Counts" },
              { name: "OpenAlex", role: "Global Scholarly Knowledge Graph" },
              { name: "arXiv", role: "Preprints (Math, Physics, CS)" },
              { name: "Europe PMC", role: "Biomedical Literature & PMC" },
              { name: "DBLP", role: "Computer Science Bibliography" },
              { name: "DataCite", role: "Datasets, Software, Zenodo" },
              { name: "PubMed / MEDLINE", role: "Gold-Standard Life Sciences" },
              { name: "DOAJ", role: "Open Access Peer-Review Accreditation" },
              { name: "HAL Open Science", role: "CNRS / Inria European Archives" },
            ].map((reg, idx) => (
              <div key={idx} style={{ padding: "0.4rem 0.65rem", backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", fontSize: "0.75rem" }}>
                <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{reg.name}:</span>{" "}
                <span style={{ color: "var(--text-muted)" }}>{reg.role}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Full Reference Audit List */}
        <div>
          <h4 style={{ fontSize: "0.875rem", fontWeight: 700, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.03em", marginBottom: "0.75rem" }}>
            Detailed Bibliographic Audit Trail ({references.length} Entries)
          </h4>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "60px" }}>Ref</th>
                  <th style={{ width: "130px" }}>Status</th>
                  <th style={{ width: "90px" }}>Score</th>
                  <th>Canonical Publication Title & Authors</th>
                  <th style={{ width: "160px" }}>Registries</th>
                  <th style={{ width: "110px" }}>Accreditation</th>
                  <th style={{ width: "100px" }}>DOI</th>
                </tr>
              </thead>
              <tbody>
                {references.map((ref) => {
                  const statusClass = ref.verification.status;
                  const statusText = statusClass.replace("_", " ");
                  const score = ref.overall_score !== null && ref.overall_score !== undefined ? ref.overall_score : ref.verification.verification_score;
                  const title = (ref.external && ref.external.title) || (ref.parsed && ref.parsed.title) || ref.raw_text.slice(0, 60);
                  const authors = ref.external && ref.external.authors && ref.external.authors.length ? ref.external.authors.slice(0, 3).join(", ") : (ref.parsed.authors ? ref.parsed.authors.slice(0, 3).join(", ") : "");
                  const doi = (ref.external && ref.external.doi) || ref.parsed.doi;

                  return (
                    <tr key={ref.reference_id} onClick={() => onSelectReference && onSelectReference(ref)} style={{ cursor: "pointer" }}>
                      <td>
                        <strong>{ref.marker || `[${ref.reference_id}]`}</strong>
                      </td>
                      <td>
                        <span className={`status-badge ${statusClass}`}>
                          {statusText}
                        </span>
                      </td>
                      <td>
                        <strong>{score}</strong>/100
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{title}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          {authors} ({ref.external && ref.external.year ? ref.external.year : (ref.parsed.year || "n.d.")})
                        </div>
                        {ref.is_retracted && (
                          <span style={{ fontSize: "0.65rem", fontWeight: 700, backgroundColor: "#fee2e2", color: "#991b1b", padding: "0.1rem 0.35rem", borderRadius: "3px" }}>
                            RETRACTED
                          </span>
                        )}
                        {ref.hallucination_risk === "HIGH" && (
                          <span style={{ fontSize: "0.65rem", fontWeight: 700, backgroundColor: "#fff1f2", color: "#e11d48", padding: "0.1rem 0.35rem", borderRadius: "3px", marginLeft: "0.3rem" }}>
                            PHANTOM RISK
                          </span>
                        )}
                      </td>
                      <td>
                        <code style={{ fontSize: "0.7rem" }}>{ref.verification.source}</code>
                      </td>
                      <td>
                        {ref.is_peer_reviewed_indexed ? (
                          <span style={{ fontSize: "0.7rem", fontWeight: 600, color: "#065f46" }}>✓ Peer-Reviewed</span>
                        ) : (
                          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Unindexed</span>
                        )}
                      </td>
                      <td>
                        {doi ? (
                          <a href={`https://doi.org/${doi}`} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "none", fontSize: "0.75rem", display: "inline-flex", alignItems: "center", gap: "0.2rem" }}>
                            <span>Link</span>
                            <ExternalLink size={10} />
                          </a>
                        ) : (
                          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Export Suite Footer */}
        <div style={{ marginTop: "1.75rem", paddingTop: "1.25rem", borderTop: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
          <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Institutional Certification: All checks performed with 100% deterministic verification. Zero generative AI hallucinations.
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
            <a href={getAnnotatedPdfExportUrl(paper.id)} download className="btn-primary" style={{ textDecoration: "none" }}>
              <Download size={13} />
              <span>Annotated PDF</span>
            </a>
            <a href={getBibtexExportUrl(paper.id)} download className="btn-secondary" style={{ textDecoration: "none" }}>
              <Code2 size={13} />
              <span>BibTeX</span>
            </a>
            <a href={getCsvExportUrl(paper.id)} download className="btn-secondary" style={{ textDecoration: "none" }}>
              <FileSpreadsheet size={13} />
              <span>CSV</span>
            </a>
            <a href={getMarkdownExportUrl(paper.id)} download className="btn-secondary" style={{ textDecoration: "none" }}>
              <FileText size={13} />
              <span>Markdown</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

function max(a, b) {
  return a > b ? a : b;
}
