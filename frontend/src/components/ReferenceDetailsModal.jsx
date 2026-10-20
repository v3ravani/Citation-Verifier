import React, { useState } from "react";
import { X, ExternalLink, Check, AlertTriangle, XCircle, HelpCircle, Target, Award, ShieldAlert, Copy } from "lucide-react";

export default function ReferenceDetailsModal({ reference, onClose }) {
  const [copiedFmt, setCopiedFmt] = useState(null);

  if (!reference) return null;

  const verif = reference.verification || {};
  const ext = reference.external || {};
  const parsed = reference.parsed || {};
  const breakdown = reference.score_breakdown || {};
  const contexts = reference.citation_occurrences || [];

  const handleCopyCitation = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedFmt(type);
    setTimeout(() => setCopiedFmt(null), 2000);
  };

  // Generate quick citations for this reference
  const title = (ext.title || parsed.title || reference.raw_text.slice(0, 70)).replace(/\.$/, "");
  const authors = ext.authors && ext.authors.length ? ext.authors : parsed.authors || [];
  const year = ext.year || parsed.year;
  const venue = ext.venue || parsed.venue;
  const doi = ext.doi || parsed.doi;

  const authIeee = authors.length ? authors.slice(0, 3).join(", ") + (authors.length > 3 ? " et al." : "") : "Anonymous";
  const ieeeStr = `${authIeee}, "${title}"${venue ? `, ${venue}` : ""}${year ? `, ${year}` : ""}${doi ? `, doi: ${doi}` : ""}.`;

  const authApa = authors.length ? authors.map((a) => {
    const parts = a.split(" ");
    return parts.length > 1 ? `${parts[parts.length - 1]}, ${parts[0][0]}.` : a;
  }).slice(0, 3).join(", ") + (authors.length > 3 ? " et al." : "") : "Anonymous";
  const apaStr = `${authApa} (${year || "n.d."}). ${title}.${venue ? ` ${venue}.` : ""}${doi ? ` https://doi.org/${doi}` : ""}`;

  const citeKey = (authors[0] ? authors[0].split(" ")[0].toLowerCase() : "ref") + (year || "") + (title.split(" ")[0] || "paper").toLowerCase().replace(/[^a-z0-9]/g, "");
  const bibtexStr = `@article{${citeKey},\n  author = {${authors.join(" and ") || "Anonymous"}},\n  title = {{${title}}},\n${venue ? `  journal = {${venue}},\n` : ""}${year ? `  year = {${year}},\n` : ""}${doi ? `  doi = {${doi}},\n` : ""}}`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
            <span style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--accent-primary)" }}>
              {reference.marker || `[${reference.reference_id}]`}
            </span>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
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

        {/* Retraction Alert Banner if flagged */}
        {reference.is_retracted && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem 1rem", backgroundColor: "#fef2f2", border: "1px solid #f87171", borderRadius: "6px", color: "#991b1b", marginBottom: "1.25rem" }}>
            <ShieldAlert size={20} style={{ flexShrink: 0 }} />
            <div style={{ fontSize: "0.8125rem" }}>
              <strong>RETRACTION NOTICE:</strong> This publication is listed as retracted or withdrawn in academic registries. Citing retracted findings compromises research validity.
            </div>
          </div>
        )}

        {/* Section 1: Side-by-Side Metadata Diff */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
          {/* Extracted */}
          <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", padding: "1rem" }}>
            <h4 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.5rem" }}>
              Extracted from Document
            </h4>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-primary)", fontStyle: "italic", marginBottom: "0.75rem", lineHeight: 1.45 }}>
              "{reference.raw_text}"
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "grid", gap: "0.3rem" }}>
              <div><strong>Parsed Title:</strong> {parsed.title || "—"}</div>
              <div><strong>Authors:</strong> {parsed.authors && parsed.authors.length ? parsed.authors.join(", ") : "—"}</div>
              <div><strong>Year:</strong> {parsed.year || "—"}</div>
              <div><strong>DOI:</strong> {parsed.doi || "—"}</div>
            </div>
          </div>

          {/* Matched External */}
          <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", padding: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
              <h4 style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", margin: 0 }}>
                Verified Scholarly Registry Record
              </h4>
              <span style={{ fontSize: "0.6875rem", backgroundColor: "var(--accent-light)", color: "var(--accent-primary)", padding: "0.1rem 0.35rem", borderRadius: "3px", fontWeight: 600 }}>
                {ext.source || "None"}
              </span>
            </div>

            {ext.title ? (
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "grid", gap: "0.3rem" }}>
                <div>
                  <strong>Title:</strong> <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{ext.title}</span>
                  {verif.title_similarity !== undefined && (
                    <span style={{ marginLeft: "0.4rem", fontSize: "0.7rem", color: verif.title_similarity >= 0.85 ? "#16a34a" : "#d97706", fontWeight: 700 }}>
                      ({(verif.title_similarity * 100).toFixed(0)}% match)
                    </span>
                  )}
                </div>
                <div><strong>Authors:</strong> {ext.authors && ext.authors.length ? ext.authors.join(", ") : "—"}</div>
                <div><strong>Year:</strong> {ext.year || "—"} | <strong>Venue:</strong> {ext.venue || "—"}</div>
                <div>
                  <strong>DOI:</strong>{" "}
                  {ext.doi ? (
                    <a href={`https://doi.org/${ext.doi}`} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", display: "inline-flex", alignItems: "center", gap: "0.25rem", textDecoration: "none" }}>
                      {ext.doi} <ExternalLink size={11} />
                    </a>
                  ) : "—"}
                </div>
                {ext.citation_count !== null && ext.citation_count !== undefined && (
                  <div><strong>Citations:</strong> {ext.citation_count} recorded citations</div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic", paddingTop: "0.5rem" }}>
                No confirmed record found across the 7 verified registries.
              </div>
            )}
          </div>
        </div>

        {/* 1-Click Formatted Citations Box */}
        {ext.title && (
          <div style={{ marginBottom: "1.5rem", padding: "0.875rem 1rem", backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase" }}>
                Canonical Formatted Citation
              </span>
              <div style={{ display: "flex", gap: "0.35rem" }}>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() => handleCopyCitation(ieeeStr, "ieee")}
                >
                  {copiedFmt === "ieee" ? <Check size={11} style={{ color: "#16a34a" }} /> : <Copy size={11} />}
                  <span>{copiedFmt === "ieee" ? "Copied" : "Copy IEEE"}</span>
                </button>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() => handleCopyCitation(apaStr, "apa")}
                >
                  {copiedFmt === "apa" ? <Check size={11} style={{ color: "#16a34a" }} /> : <Copy size={11} />}
                  <span>{copiedFmt === "apa" ? "Copied" : "Copy APA"}</span>
                </button>
                <button
                  type="button"
                  className="btn-secondary btn-sm"
                  onClick={() => handleCopyCitation(bibtexStr, "bibtex")}
                >
                  {copiedFmt === "bibtex" ? <Check size={11} style={{ color: "#16a34a" }} /> : <Copy size={11} />}
                  <span>{copiedFmt === "bibtex" ? "Copied" : "Copy BibTeX"}</span>
                </button>
              </div>
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-primary)", lineHeight: 1.45 }}>
              {ieeeStr}
            </div>
          </div>
        )}

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

        {/* Verification Score Breakdown */}
        <div style={{ marginBottom: "1.5rem", padding: "1rem", backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px" }}>
          <h4 style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.75rem" }}>
            Score Attribution Breakdown
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "0.75rem" }}>
            <div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>DOI Exact Match:</span>
              <div style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {breakdown.doi_score || 0} <span style={{ fontSize: "0.7rem", fontWeight: 400 }}>/ 35</span>
              </div>
            </div>
            <div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Title Fuzzy Match:</span>
              <div style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {breakdown.title_score || 0} <span style={{ fontSize: "0.7rem", fontWeight: 400 }}>/ 40</span>
              </div>
            </div>
            <div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Author Overlap:</span>
              <div style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {breakdown.author_score || 0} <span style={{ fontSize: "0.7rem", fontWeight: 400 }}>/ 15</span>
              </div>
            </div>
            <div>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Year Alignment:</span>
              <div style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {breakdown.year_score || 0} <span style={{ fontSize: "0.7rem", fontWeight: 400 }}>/ 10</span>
              </div>
            </div>
          </div>
        </div>

        {/* Context Occurrences */}
        <div>
          <h4 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Target size={16} style={{ color: "var(--accent-primary)" }} />
            <span>In-Text Citation Contexts ({contexts.length})</span>
          </h4>

          {contexts.length === 0 ? (
            <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic", padding: "1rem", backgroundColor: "var(--bg-secondary)", borderRadius: "6px" }}>
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
