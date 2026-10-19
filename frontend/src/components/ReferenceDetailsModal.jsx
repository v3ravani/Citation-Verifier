import React from "react";
import { X, ExternalLink, Check, AlertTriangle, XCircle, HelpCircle, Target, Award } from "lucide-react";

export default function ReferenceDetailsModal({ reference, onClose }) {
  if (!reference) return null;

  const verif = reference.verification || {};
  const ext = reference.external || {};
  const parsed = reference.parsed || {};
  const breakdown = reference.score_breakdown || {};
  const contexts = reference.citation_occurrences || [];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--accent-primary)" }}>
              {reference.marker || `[${reference.reference_id}]`}
            </span>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Reference Audit & Verification Details
            </h3>
            <span className={`status-badge ${verif.status}`}>
              {verif.status ? verif.status.replace("_", " ") : "unverified"}
            </span>
          </div>
          <button
            onClick={onClose}
            className="btn-secondary btn-sm"
            style={{ padding: "0.25rem 0.5rem" }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Section 1: Extracted vs Matched Record */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
          {/* Extracted */}
          <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", padding: "1rem" }}>
            <h4 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.5rem" }}>
              Extracted from PDF
            </h4>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontStyle: "italic", marginBottom: "0.75rem", lineHeight: 1.45 }}>
              "{reference.raw_text}"
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "grid", gap: "0.25rem" }}>
              <div><strong>Parsed Title:</strong> {parsed.title || "—"}</div>
              <div><strong>Authors:</strong> {parsed.authors && parsed.authors.length ? parsed.authors.join(", ") : "—"}</div>
              <div><strong>Year:</strong> {parsed.year || "—"}</div>
              <div><strong>DOI:</strong> {parsed.doi || "—"}</div>
            </div>
          </div>

          {/* Matched External */}
          <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", padding: "1rem" }}>
            <h4 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.5rem", display: "flex", justifyContent: "space-between" }}>
              <span>Verified Scholarly Record</span>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>{ext.source || "None"}</span>
            </h4>
            {ext.title ? (
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "grid", gap: "0.25rem" }}>
                <div><strong>Title:</strong> <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{ext.title}</span></div>
                <div><strong>Authors:</strong> {ext.authors && ext.authors.length ? ext.authors.join(", ") : "—"}</div>
                <div><strong>Year:</strong> {ext.year || "—"} | <strong>Venue:</strong> {ext.venue || "—"}</div>
                <div>
                  <strong>DOI:</strong>{" "}
                  {ext.doi ? (
                    <a href={`https://doi.org/${ext.doi}`} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                      {ext.doi} <ExternalLink size={12} />
                    </a>
                  ) : "—"}
                </div>
                {ext.citation_count !== null && ext.citation_count !== undefined && (
                  <div><strong>Citations Recorded:</strong> {ext.citation_count}</div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic", paddingTop: "0.5rem" }}>
                No confirmed record found in Crossref or Semantic Scholar.
              </div>
            )}
          </div>
        </div>

        {/* Abstract Preview if exists */}
        {ext.abstract && (
          <div style={{ marginBottom: "1.5rem", padding: "0.875rem 1rem", backgroundColor: "var(--bg-primary)", border: "1px solid var(--border-subtle)", borderRadius: "6px" }}>
            <h4 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.375rem" }}>
              Retrieved Abstract (Semantic Evaluation Grounding):
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {ext.abstract}
            </p>
          </div>
        )}

        {/* Section 2: Verification Score Breakdown */}
        <div style={{ marginBottom: "1.5rem", padding: "1rem", backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px" }}>
          <h4 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <Award size={15} style={{ color: "var(--accent-primary)" }} />
            <span>Transparent Score Decomposition</span>
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "0.625rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>Title Similarity</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{(verif.title_similarity * 100).toFixed(0)}%</strong>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>{breakdown.title_points || 0} pts</span>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "0.625rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>Author Match</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{(verif.author_match * 100).toFixed(0)}%</strong>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>{breakdown.author_points || 0} pts</span>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "0.625rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>Year Match</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{verif.year_match === true ? "Matched" : (verif.year_match === false ? "Mismatch" : "N/A")}</strong>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>{breakdown.year_points || 0} pts</span>
            </div>
            <div style={{ backgroundColor: "var(--bg-primary)", padding: "0.625rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>DOI Exact</span>
              <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{verif.doi_match === true ? "Verified" : (verif.doi_match === false ? "Mismatch" : "None")}</strong>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>{breakdown.doi_points || 0} pts</span>
            </div>
            <div style={{ backgroundColor: "var(--accent-light)", padding: "0.625rem", borderRadius: "4px", border: "1px solid var(--status-probable-border)" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--accent-primary)", display: "block", fontWeight: 600 }}>Overall Score</span>
              <strong style={{ fontSize: "1.125rem", color: "var(--accent-primary)" }}>
                {reference.overall_score !== null ? `${reference.overall_score} / 100` : "Unavailable"}
              </strong>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)", display: "block" }}>55% meta, 45% sim</span>
            </div>
          </div>
          {verif.notes && verif.notes.length > 0 && (
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              <strong>Audit Notes:</strong> {verif.notes.join("; ")}
            </div>
          )}
        </div>

        {/* Section 3: In-Text Citation Contexts */}
        <div>
          <h4 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <Target size={16} style={{ color: "var(--accent-primary)" }} />
            <span>In-Text Citation Contexts ({contexts.length})</span>
          </h4>

          {contexts.length === 0 ? (
            <div style={{ padding: "1.25rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              No in-text citation occurrences detected for this reference in the machine-readable body text.
            </div>
          ) : (
            <div style={{ display: "grid", gap: "1rem" }}>
              {contexts.map((ctx, idx) => (
                <div key={idx} style={{ padding: "1rem", border: "1px solid var(--border-subtle)", borderRadius: "6px", backgroundColor: "var(--bg-primary)" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                    <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)" }}>
                      Context {idx + 1} {ctx.page ? `(Page ${ctx.page})` : ""}
                    </span>
                    {ctx.semantic_similarity !== null && (
                      <span className={`status-badge ${ctx.classification}`}>
                        Similarity: {ctx.semantic_similarity.toFixed(3)} ({ctx.classification.replace("_", " ")})
                      </span>
                    )}
                  </div>

                  {/* Context sentence display */}
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: "0.75rem" }}>
                    {ctx.previous_sentence && <span style={{ color: "var(--text-muted)" }}>{ctx.previous_sentence} </span>}
                    <span style={{ backgroundColor: "#FEF08A", color: "#854D0E", padding: "0.125rem 0.25rem", borderRadius: "3px", fontWeight: 500 }}>
                      {ctx.sentence}
                    </span>
                    {ctx.next_sentence && <span style={{ color: "var(--text-muted)" }}> {ctx.next_sentence}</span>}
                  </div>

                  {/* FAISS Candidate Ranking */}
                  {ctx.rank_among_references && (
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                      <strong>FAISS Bibliography Ranking:</strong> Reference ranked <strong>#{ctx.rank_among_references}</strong> out of {ctx.total_candidates} bibliography candidates.
                      {ctx.top_alternative_references && ctx.top_alternative_references.length > 0 && (
                        <div style={{ marginTop: "0.25rem", color: "var(--text-muted)" }}>
                          Top alternatives: {ctx.top_alternative_references.map((alt) => `Ref #${alt.reference_id} (${alt.similarity.toFixed(2)})`).join(", ")}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Overclaim Heuristic Alert */}
                  {ctx.overclaim_flag && (
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", padding: "0.5rem 0.75rem", backgroundColor: "var(--status-unverified-bg)", border: "1px solid var(--status-unverified-border)", borderRadius: "4px", color: "var(--status-unverified-text)", fontSize: "0.75rem" }}>
                      <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: "2px" }} />
                      <div>
                        <strong>Heuristic Review Flag:</strong> {ctx.overclaim_reason}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
