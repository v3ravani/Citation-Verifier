import React from "react";
import { X, BookOpen, Search, Cpu, BarChart2, ShieldAlert } from "lucide-react";

export default function MethodologyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "780px" }}>
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <BookOpen size={20} style={{ color: "var(--accent-primary)" }} />
            <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Citation Verifier — Methodology & Scientific Disclosure
            </h3>
          </div>
          <button onClick={onClose} className="btn-secondary btn-sm" style={{ padding: "0.25rem 0.5rem" }}>
            <X size={16} />
          </button>
        </div>

        <div style={{ display: "grid", gap: "1.25rem", fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          {/* Section 1 */}
          <div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.375rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
              <Search size={16} style={{ color: "var(--accent-primary)" }} />
              <span>1. Academic Metadata Verification</span>
            </h4>
            <p>
              References are extracted from the bibliography section of uploaded PDFs using PyMuPDF. Every parsed entry is verified deterministically against the <strong>Crossref REST API</strong> and <strong>Semantic Scholar Graph API</strong>. When an explicit DOI exists, exact resolution is prioritized. In the absence of a DOI, fuzzy title and bibliographic matching is performed using normalized token-sort ratios via RapidFuzz.
            </p>
          </div>

          {/* Section 2 */}
          <div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.375rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
              <Cpu size={16} style={{ color: "var(--accent-primary)" }} />
              <span>2. Local Semantic Alignment via Sentence-BERT & FAISS</span>
            </h4>
            <p>
              In-text citation sentences and their surrounding 3-sentence context windows are encoded locally into 384-dimensional dense vectors using <code>sentence-transformers/all-MiniLM-L6-v2</code>. Cosine similarity is computed against retrieved paper abstracts. An in-memory <strong>FAISS IndexFlatIP</strong> ranks the expected reference against all other bibliography candidates to detect potential misattribution.
            </p>
            <div style={{ marginTop: "0.5rem", padding: "0.75rem", backgroundColor: "var(--bg-secondary)", borderRadius: "4px", fontSize: "0.8125rem" }}>
              <strong>Heuristic Similarity Thresholds:</strong>
              <ul style={{ paddingLeft: "1.25rem", marginTop: "0.25rem" }}>
                <li><code>&gt;= 0.78</code>: Strongly related citation context</li>
                <li><code>0.62 – 0.77</code>: Moderately related citation context</li>
                <li><code>0.45 – 0.61</code>: Weakly related citation context</li>
                <li><code>&lt; 0.45</code>: Likely unrelated / potential misattribution</li>
              </ul>
            </div>
          </div>

          {/* Section 3 */}
          <div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.375rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
              <BarChart2 size={16} style={{ color: "var(--accent-primary)" }} />
              <span>3. Overclaim Heuristic Rule</span>
            </h4>
            <p>
              Strong assertive terminology (e.g., <em>"proves"</em>, <em>"conclusively demonstrates"</em>, <em>"eliminates"</em>, <em>"guarantees"</em>) in a citation sentence is evaluated against semantic alignment scores and abstract evidence. If assertive language is unaccompanied by strong semantic support in the cited abstract, a transparent heuristic review flag is raised.
            </p>
          </div>

          {/* Section 4 */}
          <div style={{ padding: "0.875rem 1rem", backgroundColor: "var(--status-mismatch-bg)", border: "1px solid var(--status-mismatch-border)", borderRadius: "6px", color: "var(--status-mismatch-text)" }}>
            <h4 style={{ fontSize: "0.875rem", fontWeight: 700, marginBottom: "0.25rem", display: "flex", alignItems: "center", gap: "0.375rem" }}>
              <ShieldAlert size={16} />
              <span>Ethical Limitations & Scientific Disclosures</span>
            </h4>
            <ul style={{ paddingLeft: "1.25rem", fontSize: "0.8125rem", lineHeight: 1.5 }}>
              <li><strong>Similarity does not prove factual truth:</strong> High embedding similarity reflects topical overlap, not experimental validity.</li>
              <li><strong>Abstract completeness:</strong> Abstracts may not mention secondary findings or auxiliary claims cited in the paper.</li>
              <li><strong>No generative AI:</strong> All analysis is deterministic and locally evaluated. No generative LLMs are used to hallucinate ratings.</li>
              <li><strong>Peer review support:</strong> This tool is designed to assist academic researchers and peer reviewers, not replace critical human evaluation.</li>
            </ul>
          </div>
        </div>

        <div style={{ marginTop: "1.5rem", textAlign: "right" }}>
          <button onClick={onClose} className="btn-primary">
            <span>Close Disclosure</span>
          </button>
        </div>
      </div>
    </div>
  );
}
