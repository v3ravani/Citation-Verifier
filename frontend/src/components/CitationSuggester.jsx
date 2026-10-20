import React, { useState } from "react";
import { Sparkles, Copy, Check, ExternalLink, BookOpen, Quote, AlertCircle, Search } from "lucide-react";
import { suggestCitations } from "../api/client";

const EXAMPLE_PARAGRAPHS = [
  {
    title: "Transformer Architectures",
    text: "Deep neural networks powered by multi-head self-attention mechanisms have fundamentally transformed natural language processing. By capturing long-range dependencies across sequence tokens without recurrence, these models achieve unprecedented generalization on downstream language understanding benchmarks.",
  },
  {
    title: "Climate Change Economics",
    text: "Climate change adaptation requires targeted finance mechanisms to protect vulnerable coastal communities against rising sea levels and extreme weather events. Developing nations face significant funding deficits in implementing robust localized resilience strategies.",
  },
  {
    title: "Quantum Error Correction",
    text: "Surface codes provide a viable pathway toward fault-tolerant quantum computing by encoding logical qubits into topological degrees of freedom. Active syndrome measurement detects phase-flip and bit-flip errors before coherence is lost.",
  },
];

export default function CitationSuggester() {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [copiedFormat, setCopiedFormat] = useState({}); // { `${claimIdx}-${candIdx}-${format}`: true }
  const [activeFormat, setActiveFormat] = useState("ieee"); // "ieee", "apa", "bibtex"

  const handleAnalyze = async () => {
    if (!inputText || inputText.trim().length < 15) {
      setError("Please enter a paragraph of at least 15 characters to analyze.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await suggestCitations(inputText, 3, 4);
      setResults(data);
    } catch (err) {
      setError(err.message || "Failed to find citation suggestions.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedFormat((prev) => ({ ...prev, [key]: true }));
    setTimeout(() => {
      setCopiedFormat((prev) => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const getBadgeColor = (badge) => {
    switch (badge) {
      case "Highly Relevant":
        return { bg: "#ecfdf5", border: "#a7f3d0", text: "#065f46" };
      case "Moderately Relevant":
        return { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af" };
      case "Supporting Context":
        return { bg: "#fefce8", border: "#fef08a", text: "#854d0e" };
      default:
        return { bg: "#f8fafc", border: "#e2e8f0", text: "#475569" };
    }
  };

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Introduction Card */}
      <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
          <Sparkles size={18} style={{ color: "var(--accent-primary)" }} />
          <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
            Paragraph Citation Suggester & Claim Assistant
          </h3>
        </div>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
          Draft or paste any paragraph of your research paper. The verifier will extract your core claims, search peer-reviewed scholarly records across <strong>OpenAlex</strong>, <strong>Semantic Scholar</strong>, and <strong>arXiv</strong>, rank candidates with local <strong>Sentence-BERT</strong> embeddings, and generate verified citations in <strong>IEEE</strong>, <strong>APA</strong>, and <strong>BibTeX</strong> formats.
        </p>

        {/* Quick Example Templates */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "0.75rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)" }}>Example Claims:</span>
          {EXAMPLE_PARAGRAPHS.map((ex) => (
            <button
              key={ex.title}
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => {
                setInputText(ex.text);
                setError(null);
              }}
              style={{ fontSize: "0.75rem", padding: "0.2rem 0.6rem" }}
            >
              {ex.title}
            </button>
          ))}
        </div>
      </div>

      {/* Input Textarea Area */}
      <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.5rem" }}>
        <label htmlFor="paragraph-input" style={{ display: "block", fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
          Research Draft Paragraph or Statement:
        </label>
        <textarea
          id="paragraph-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste or type a research paragraph, methodology claim, or literature review argument..."
          rows={5}
          style={{
            width: "100%",
            padding: "0.75rem",
            fontSize: "0.875rem",
            fontFamily: "inherit",
            lineHeight: 1.5,
            border: "1px solid var(--border-subtle)",
            borderRadius: "6px",
            backgroundColor: "#FFFFFF",
            color: "var(--text-primary)",
            resize: "vertical",
            outline: "none",
            marginBottom: "0.75rem",
          }}
        />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            {inputText.length} characters • Analyzed with zero hallucination guarantee
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={handleAnalyze}
            disabled={isLoading || !inputText.trim()}
            style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
          >
            {isLoading ? (
              <>
                <span className="spin" style={{ display: "inline-block", width: "14px", height: "14px", border: "2px solid #FFFFFF", borderTopColor: "transparent", borderRadius: "50%" }} />
                <span>Searching Scholarly Indices...</span>
              </>
            ) : (
              <>
                <Search size={15} />
                <span>Find & Suggest Citations</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: "0.75rem", padding: "0.5rem 0.75rem", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "4px", color: "#991b1b", fontSize: "0.8125rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results Section */}
      {results && results.results && (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", flexWrap: "wrap", gap: "0.5rem" }}>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              Scholarly Recommendations ({results.results.reduce((acc, c) => acc + c.suggestions.length, 0)} Verified Works Found)
            </h4>

            {/* Global Citation Format Switcher */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", backgroundColor: "var(--bg-secondary)", padding: "0.2rem", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", padding: "0 0.5rem" }}>Format:</span>
              {["ieee", "apa", "bibtex"].map((fmt) => (
                <button
                  key={fmt}
                  type="button"
                  onClick={() => setActiveFormat(fmt)}
                  style={{
                    padding: "0.25rem 0.6rem",
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

          {results.results.map((claimRes, claimIdx) => (
            <div key={claimIdx} className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
              {/* Claim Box */}
              <div style={{ padding: "0.6rem 0.75rem", backgroundColor: "var(--bg-secondary)", borderLeft: "3px solid var(--accent-primary)", borderRadius: "0 4px 4px 0", marginBottom: "1rem" }}>
                <div style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.2rem" }}>
                  Analyzed Claim #{claimIdx + 1}
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-primary)", fontStyle: "italic" }}>
                  "{claimRes.claim}"
                </div>
              </div>

              {/* Suggestions List */}
              {claimRes.suggestions.length === 0 ? (
                <div style={{ fontSize: "0.8125rem", color: "var(--text-muted)", textAlign: "center", padding: "1rem" }}>
                  No high-confidence academic matches found for this specific phrasing. Try adjusting keywords.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
                  {claimRes.suggestions.map((cand, candIdx) => {
                    const badgeStyle = getBadgeColor(cand.relevance_badge);
                    const copyKey = `${claimIdx}-${candIdx}-${activeFormat}`;
                    const isCopied = copiedFormat[copyKey];
                    const citationString = activeFormat === "ieee" ? cand.ieee : activeFormat === "apa" ? cand.apa : cand.bibtex;

                    return (
                      <div
                        key={candIdx}
                        style={{
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "6px",
                          padding: "0.875rem",
                          backgroundColor: "#FFFFFF",
                        }}
                      >
                        {/* Top Bar: Relevance Badge, Sim Score, Source */}
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.4rem" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                            <span
                              style={{
                                fontSize: "0.7rem",
                                fontWeight: 700,
                                padding: "0.15rem 0.5rem",
                                borderRadius: "12px",
                                backgroundColor: badgeStyle.bg,
                                border: `1px solid ${badgeStyle.border}`,
                                color: badgeStyle.text,
                              }}
                            >
                              {cand.relevance_badge}
                            </span>
                            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                              {(cand.semantic_similarity * 100).toFixed(0)}% Semantic Match
                            </span>
                          </div>

                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            <span style={{ textTransform: "capitalize" }}>Source: {cand.source}</span>
                            {cand.citation_count !== null && (
                              <span>• {cand.citation_count} Citations</span>
                            )}
                          </div>
                        </div>

                        {/* Title */}
                        <h5 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", margin: "0 0 0.35rem 0", lineHeight: 1.35 }}>
                          {cand.url ? (
                            <a href={cand.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-primary)", textDecoration: "none", display: "inline-flex", alignItems: "baseline", gap: "0.25rem" }}>
                              {cand.title}
                              <ExternalLink size={12} />
                            </a>
                          ) : (
                            cand.title
                          )}
                        </h5>

                        {/* Authors & Venue */}
                        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                          <span>{cand.authors && cand.authors.length > 0 ? cand.authors.join(", ") : "Unknown Authors"}</span>
                          {cand.year && <span> ({cand.year})</span>}
                          {cand.venue && <span> • <em>{cand.venue}</em></span>}
                          {cand.doi && <span> • DOI: <code>{cand.doi}</code></span>}
                        </div>

                        {/* Abstract Snippet */}
                        {cand.abstract && (
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.45, marginBottom: "0.75rem", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                            {cand.abstract}
                          </div>
                        )}

                        {/* Formatted Citation Output Box & Copy Button */}
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", backgroundColor: "var(--bg-secondary)", padding: "0.5rem 0.75rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
                          <div style={{ fontSize: "0.75rem", fontFamily: activeFormat === "bibtex" ? "monospace" : "inherit", color: "var(--text-primary)", overflowX: "auto", whiteSpace: activeFormat === "bibtex" ? "pre-wrap" : "normal" }}>
                            {citationString}
                          </div>

                          <button
                            type="button"
                            className="btn-secondary btn-sm"
                            onClick={() => handleCopy(citationString, copyKey)}
                            style={{ flexShrink: 0, display: "inline-flex", alignItems: "center", gap: "0.3rem" }}
                            title={`Copy ${activeFormat.toUpperCase()} citation`}
                          >
                            {isCopied ? <Check size={12} style={{ color: "#16a34a" }} /> : <Copy size={12} />}
                            <span style={{ fontSize: "0.7rem" }}>{isCopied ? "Copied" : "Copy"}</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
