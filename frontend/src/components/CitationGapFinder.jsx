import React, { useState, useEffect } from "react";
import { AlertCircle, Search, Sparkles, Copy, Check, ExternalLink, ShieldAlert, ArrowRight, Edit3, PlusCircle } from "lucide-react";
import { detectCitationGaps } from "../api/client";

export default function CitationGapFinder({ paperId }) {
  const [activeTab, setActiveTab] = useState("document"); // "document" or "editor"
  const [editorText, setEditorText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [gapsData, setGapsData] = useState(null);
  const [editorGapsData, setEditorGapsData] = useState(null);
  const [error, setError] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  const [activeFormat, setActiveFormat] = useState("ieee"); // "ieee", "apa", "mla", "chicago", "bibtex"

  useEffect(() => {
    if (paperId && !gapsData && !isLoading) {
      loadDocumentGaps();
    }
  }, [paperId]);

  const loadDocumentGaps = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await detectCitationGaps(paperId, null, 6);
      setGapsData(data);
    } catch (err) {
      setError(err.message || "Failed to scan paper text for citation gaps.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleScanEditorText = async () => {
    if (!editorText || editorText.trim().length < 30) {
      setError("Please write or paste at least 30 characters in the drafting editor.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await detectCitationGaps(null, editorText, 6);
      setEditorGapsData(data);
    } catch (err) {
      setError(err.message || "Failed to scan draft text for citation gaps.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (citationText, key) => {
    navigator.clipboard.writeText(citationText);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleInsertCitation = (sug) => {
    const firstAuthor = sug.authors && sug.authors.length ? sug.authors[0].split(" ").pop() : "Anonymous";
    const yearStr = sug.year ? `${sug.year}` : "n.d.";
    const citeMarker = ` [${firstAuthor} et al., ${yearStr}]`;

    setEditorText((prev) => prev + citeMarker);
  };

  const currentGaps = activeTab === "document" ? gapsData : editorGapsData;

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Intro Header */}
      <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
              <ShieldAlert size={18} style={{ color: "var(--accent-primary)" }} />
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                Citation Gap Finder & Real-Time Manuscript Drafter
              </h3>
            </div>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, maxWidth: "750px", lineHeight: 1.5 }}>
              Detects unbacked assertive claims (e.g. <em>"studies have shown"</em>, <em>"outperforms conventional methods"</em>) that lack supporting in-text citations. Queries 10 authoritative registries to suggest peer-reviewed literature.
            </p>
          </div>

          <div style={{ display: "inline-flex", borderRadius: "6px", border: "1px solid var(--border-subtle)", overflow: "hidden" }}>
            <button
              type="button"
              onClick={() => setActiveTab("document")}
              style={{
                padding: "0.4rem 0.85rem",
                fontSize: "0.8125rem",
                fontWeight: activeTab === "document" ? 600 : 500,
                backgroundColor: activeTab === "document" ? "var(--accent-light)" : "var(--bg-primary)",
                color: activeTab === "document" ? "var(--accent-primary)" : "var(--text-secondary)",
                border: "none",
                cursor: "pointer",
              }}
            >
              Paper Audit Scan
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("editor")}
              style={{
                padding: "0.4rem 0.85rem",
                fontSize: "0.8125rem",
                fontWeight: activeTab === "editor" ? 600 : 500,
                backgroundColor: activeTab === "editor" ? "var(--accent-light)" : "var(--bg-primary)",
                color: activeTab === "editor" ? "var(--accent-primary)" : "var(--text-secondary)",
                border: "none",
                borderLeft: "1px solid var(--border-subtle)",
                cursor: "pointer",
              }}
            >
              <span style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem" }}>
                <Edit3 size={13} />
                <span>Live Manuscript Drafter</span>
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Live Manuscript Drafter Pane */}
      {activeTab === "editor" && (
        <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Interactive Manuscript Drafting Workspace
            </label>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {editorText.length} characters
            </span>
          </div>

          <textarea
            rows={5}
            value={editorText}
            onChange={(e) => setEditorText(e.target.value)}
            placeholder="Type or paste sections of your manuscript here to test claim coverage in real time... (e.g. 'Deep learning architectures have proven conclusively that self-attention improves generalization...')"
            style={{
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              borderRadius: "6px",
              border: "1px solid var(--border-subtle)",
              backgroundColor: "var(--bg-primary)",
              color: "var(--text-primary)",
              resize: "vertical",
              marginBottom: "0.75rem",
            }}
          />

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => setEditorText("Recent benchmark studies have shown that self-supervised vision representations outperform supervised baselines on few-shot transfer. However, traditional convolutional models struggle with long-range relational reasoning.")}
            >
              Insert Sample Draft
            </button>

            <button
              type="button"
              className="btn-primary"
              onClick={handleScanEditorText}
              disabled={isLoading || editorText.trim().length < 30}
            >
              <Search size={14} className={isLoading ? "spin" : ""} />
              <span>{isLoading ? "Scanning Draft..." : "Scan Draft for Unbacked Claims"}</span>
            </button>
          </div>
        </div>
      )}

      {error && (
        <div style={{ padding: "1rem", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "6px", color: "#991b1b", fontSize: "0.8125rem", display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.25rem" }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Results Header with Format Picker */}
      {currentGaps && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              {currentGaps.total_gaps_detected > 0
                ? `Detected ${currentGaps.total_gaps_detected} Potential Uncited Assertion(s)`
                : "No Unbacked Assertions Detected — Strong Document Coverage"}
            </h4>

            {/* Format Picker */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", backgroundColor: "var(--bg-secondary)", padding: "0.2rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", padding: "0 0.5rem" }}>Format:</span>
              {["ieee", "apa", "mla", "chicago", "bibtex"].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setActiveFormat(fmt)}
                  style={{
                    padding: "0.2rem 0.55rem",
                    fontSize: "0.75rem",
                    fontWeight: activeFormat === fmt ? 600 : 500,
                    backgroundColor: activeFormat === fmt ? "#FFFFFF" : "transparent",
                    color: activeFormat === fmt ? "var(--accent-primary)" : "var(--text-secondary)",
                    border: activeFormat === fmt ? "1px solid var(--border-subtle)" : "1px solid transparent",
                    borderRadius: "4px",
                    cursor: "pointer",
                    textTransform: "uppercase",
                  }}
                >
                  {fmt}
                </button>
              ))}
            </div>
          </div>

          {currentGaps.gaps.map((gap, gIdx) => (
            <div key={gIdx} className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
              {/* Uncited Sentence */}
              <div style={{ padding: "0.75rem 1rem", backgroundColor: "#fffbeb", borderLeft: "4px solid #d97706", borderRadius: "0 6px 6px 0", marginBottom: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                  <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#b45309", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    Uncited Claim #{gIdx + 1} • Assertion Trigger: "{gap.assertion_phrase}"
                  </span>
                  <span style={{ fontSize: "0.7rem", backgroundColor: "#fef3c7", padding: "0.1rem 0.4rem", borderRadius: "4px", color: "#92400e", fontWeight: 600 }}>
                    Missing Citation Marker
                  </span>
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", fontStyle: "italic", lineHeight: 1.5 }}>
                  "{gap.sentence}"
                </div>
              </div>

              {/* Recommended References */}
              <div>
                <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "0.5rem" }}>
                  Recommended Scholarly Citations to Support this Claim:
                </div>

                {gap.suggestions.length === 0 ? (
                  <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", padding: "0.5rem 0" }}>
                    No direct match found in registries. Consider verifying the exact wording or experimental data.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {gap.suggestions.map((sug, sIdx) => {
                      const copyKey = `gap-${gIdx}-${sIdx}-${activeFormat}`;
                      const isCopied = copiedKey === copyKey;
                      const citeStr =
                        activeFormat === "apa"
                          ? sug.apa
                          : activeFormat === "mla"
                          ? sug.mla || sug.apa
                          : activeFormat === "chicago"
                          ? sug.chicago || sug.apa
                          : activeFormat === "bibtex"
                          ? sug.bibtex
                          : sug.ieee;

                      return (
                        <div key={sIdx} style={{ border: "1px solid var(--border-subtle)", borderRadius: "6px", padding: "0.75rem 1rem", backgroundColor: "#FFFFFF" }}>
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.25rem" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                              <span style={{ fontSize: "0.7rem", fontWeight: 700, padding: "0.1rem 0.4rem", borderRadius: "10px", backgroundColor: "var(--status-verified-bg)", color: "var(--status-verified-text)", border: "1px solid var(--status-verified-border)" }}>
                                {(sug.semantic_similarity * 100).toFixed(0)}% Relevance
                              </span>
                              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 500 }}>
                                Source: {sug.source}
                              </span>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                              {activeTab === "editor" && (
                                <button
                                  type="button"
                                  className="btn-secondary btn-sm"
                                  onClick={() => handleInsertCitation(sug)}
                                  style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem", color: "var(--accent-primary)" }}
                                  title="Insert in-text citation marker into your drafting editor"
                                >
                                  <PlusCircle size={12} />
                                  <span>Insert In Text</span>
                                </button>
                              )}

                              <button
                                type="button"
                                className="btn-secondary btn-sm"
                                onClick={() => handleCopy(citeStr, copyKey)}
                                style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem" }}
                              >
                                {isCopied ? <Check size={12} style={{ color: "#16a34a" }} /> : <Copy size={12} />}
                                <span>{isCopied ? "Copied" : `Copy ${activeFormat.toUpperCase()}`}</span>
                              </button>
                            </div>
                          </div>

                          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
                            {sug.url ? (
                              <a href={sug.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "none", display: "inline-flex", alignItems: "baseline", gap: "0.25rem" }}>
                                {sug.title} <ExternalLink size={11} />
                              </a>
                            ) : sug.title}
                          </div>

                          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                            {sug.authors && sug.authors.length ? sug.authors.slice(0, 3).join(", ") : "Anonymous"}{sug.authors && sug.authors.length > 3 ? " et al." : ""} ({sug.year || "n.d."}) {sug.venue ? `• ${sug.venue}` : ""}
                          </div>

                          <div style={{ marginTop: "0.5rem", padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-secondary)", borderRadius: "4px", fontSize: "0.75rem", fontFamily: activeFormat === "bibtex" ? "monospace" : "inherit", color: "var(--text-primary)", overflowX: "auto" }}>
                            {citeStr}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
