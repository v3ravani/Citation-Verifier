import React, { useState } from "react";
import { Sparkles, Copy, Check, ExternalLink, BookOpen, Quote, AlertCircle, Search, Filter, ShieldCheck, Clock, Award } from "lucide-react";
import { suggestCitations, searchLiterature } from "../api/client";

const EXAMPLE_PARAGRAPHS = [
  {
    title: "Transformer Architectures",
    text: "Deep neural networks powered by multi-head self-attention mechanisms have fundamentally transformed natural language processing. By capturing long-range dependencies across sequence tokens without recurrence, these models achieve unprecedented generalization on downstream language understanding benchmarks.",
  },
  {
    title: "Climate Change Adaptation",
    text: "Climate change adaptation requires targeted finance mechanisms to protect vulnerable coastal communities against rising sea levels and extreme weather events. Developing nations face significant funding deficits in implementing robust localized resilience strategies.",
  },
  {
    title: "Quantum Error Correction",
    text: "Surface codes provide a viable pathway toward fault-tolerant quantum computing by encoding logical qubits into topological degrees of freedom. Active syndrome measurement detects phase-flip and bit-flip errors before coherence is lost.",
  },
];

export default function CitationSuggester() {
  const [activeMode, setActiveMode] = useState("paragraph"); // "paragraph" or "topic"
  const [inputText, setInputText] = useState("");
  const [topicQuery, setTopicQuery] = useState("");
  const [filterMode, setFilterMode] = useState("general"); // "general", "seminal", "recent", "open_access"
  const [isLoading, setIsLoading] = useState(false);
  const [paragraphResults, setParagraphResults] = useState(null);
  const [topicResults, setTopicResults] = useState(null);
  const [error, setError] = useState(null);
  const [copiedFormat, setCopiedFormat] = useState({});
  const [activeFormat, setActiveFormat] = useState("ieee"); // "ieee", "apa", "mla", "chicago", "bibtex"

  const handleAnalyzeParagraph = async () => {
    if (!inputText || inputText.trim().length < 15) {
      setError("Please enter a paragraph of at least 15 characters to analyze.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await suggestCitations(inputText, 3, 5);
      setParagraphResults(data);
    } catch (err) {
      setError(err.message || "Failed to find citation suggestions.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchTopic = async () => {
    if (!topicQuery || topicQuery.trim().length < 3) {
      setError("Please enter a topic or research question (at least 3 characters).");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await searchLiterature(topicQuery, filterMode, 8);
      setTopicResults(data);
    } catch (err) {
      setError(err.message || "Failed to search literature.");
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

  const renderCitationCard = (cand, candIdx, keyPrefix) => {
    const badgeStyle = getBadgeColor(cand.relevance_badge);
    const formattedText =
      activeFormat === "apa"
        ? cand.apa
        : activeFormat === "mla"
        ? cand.mla || cand.apa
        : activeFormat === "chicago"
        ? cand.chicago || cand.apa
        : activeFormat === "bibtex"
        ? cand.bibtex
        : cand.ieee;

    return (
      <div
        key={candIdx}
        style={{
          border: "1px solid var(--border-subtle)",
          borderRadius: "6px",
          padding: "1rem",
          backgroundColor: "var(--bg-primary)",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem", marginBottom: "0.5rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.25rem" }}>
              <span
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  backgroundColor: badgeStyle.bg,
                  color: badgeStyle.text,
                  border: `1px solid ${badgeStyle.border}`,
                  padding: "0.125rem 0.45rem",
                  borderRadius: "12px",
                }}
              >
                {cand.relevance_badge} ({(cand.semantic_similarity * 100).toFixed(0)}%)
              </span>
              <span style={{ fontSize: "0.6875rem", backgroundColor: "var(--bg-secondary)", color: "var(--text-muted)", padding: "0.125rem 0.35rem", borderRadius: "3px" }}>
                Source: {cand.source}
              </span>
              {cand.citation_count !== null && cand.citation_count !== undefined && (
                <span style={{ fontSize: "0.6875rem", color: "var(--accent-primary)", fontWeight: 600 }}>
                  ★ {cand.citation_count} citations
                </span>
              )}
            </div>
            <h5 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", margin: 0, lineHeight: 1.35 }}>
              {cand.title}
            </h5>
          </div>

          {cand.url && (
            <a
              href={cand.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "var(--accent-primary)",
                flexShrink: 0,
                display: "inline-flex",
                alignItems: "center",
                gap: "0.25rem",
                fontSize: "0.75rem",
                textDecoration: "none",
              }}
            >
              <span>View</span>
              <ExternalLink size={12} />
            </a>
          )}
        </div>

        <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
          <span>{cand.authors && cand.authors.length ? cand.authors.join(", ") : "Anonymous"}</span>
          {cand.year && <span> ({cand.year})</span>}
          {cand.venue && <span> • <em>{cand.venue}</em></span>}
          {cand.doi && <span style={{ marginLeft: "0.5rem" }}>• DOI: <code>{cand.doi}</code></span>}
        </div>

        {cand.abstract && (
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.45, marginBottom: "0.75rem", backgroundColor: "var(--bg-secondary)", padding: "0.5rem 0.75rem", borderRadius: "4px" }}>
            {cand.abstract.length > 250 ? `${cand.abstract.slice(0, 250)}...` : cand.abstract}
          </p>
        )}

        {/* Citation copy box */}
        <div style={{ backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "4px", padding: "0.625rem 0.75rem", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem" }}>
          <code style={{ fontSize: "0.75rem", color: "var(--text-primary)", whiteSpace: "pre-wrap", wordBreak: "break-all", maxHeight: activeFormat === "bibtex" ? "120px" : "none", overflowY: "auto", display: "block", flex: 1 }}>
            {formattedText}
          </code>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={() => handleCopy(formattedText, `${keyPrefix}-${candIdx}`)}
            style={{ flexShrink: 0 }}
          >
            {copiedFormat[`${keyPrefix}-${candIdx}`] ? (
              <>
                <Check size={12} style={{ color: "#16a34a" }} />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy size={12} />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Introduction Card */}
      <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Sparkles size={18} style={{ color: "var(--accent-primary)" }} />
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
              Reference Recommendation & Discovery Studio
            </h3>
          </div>

          <div style={{ display: "inline-flex", borderRadius: "6px", border: "1px solid var(--border-subtle)", overflow: "hidden" }}>
            <button
              type="button"
              onClick={() => setActiveMode("paragraph")}
              style={{
                padding: "0.4rem 0.85rem",
                fontSize: "0.8125rem",
                fontWeight: activeMode === "paragraph" ? 600 : 500,
                backgroundColor: activeMode === "paragraph" ? "var(--accent-light)" : "var(--bg-primary)",
                color: activeMode === "paragraph" ? "var(--accent-primary)" : "var(--text-secondary)",
                border: "none",
                cursor: "pointer",
              }}
            >
              Paragraph Claim Suggester
            </button>
            <button
              type="button"
              onClick={() => setActiveMode("topic")}
              style={{
                padding: "0.4rem 0.85rem",
                fontSize: "0.8125rem",
                fontWeight: activeMode === "topic" ? 600 : 500,
                backgroundColor: activeMode === "topic" ? "var(--accent-light)" : "var(--bg-primary)",
                color: activeMode === "topic" ? "var(--accent-primary)" : "var(--text-secondary)",
                border: "none",
                borderLeft: "1px solid var(--border-subtle)",
                cursor: "pointer",
              }}
            >
              Topic & Milestone Literature Search
            </button>
          </div>
        </div>

        <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
          Search across <strong>10 authoritative scholarly registries</strong> (Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite, PubMed/MEDLINE, DOAJ, and HAL Open Science). Candidate works are semantically ranked via local <strong>Sentence-BERT</strong> (all-MiniLM-L6-v2) embeddings with one-click export in <strong>IEEE, APA, MLA, Chicago, and BibTeX</strong>.
        </p>
      </div>

      {/* Mode 1: Paragraph Claim Suggester */}
      {activeMode === "paragraph" ? (
        <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
            <label style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
              Draft Research Text or Paragraph
            </label>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              {inputText.length} characters
            </span>
          </div>

          <textarea
            rows={4}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Paste a paragraph from your paper to extract factual claims and discover matching literature..."
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

          {/* Example Prompts */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Load Sample:</span>
            {EXAMPLE_PARAGRAPHS.map((ex, i) => (
              <button
                key={i}
                type="button"
                className="btn-secondary btn-sm"
                onClick={() => setInputText(ex.text)}
                style={{ fontSize: "0.75rem" }}
              >
                {ex.title}
              </button>
            ))}
          </div>

          {error && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem", backgroundColor: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "6px", color: "#991b1b", fontSize: "0.8125rem", marginBottom: "1rem" }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end" }}>
            <button
              type="button"
              className="btn-primary"
              onClick={handleAnalyzeParagraph}
              disabled={isLoading || inputText.trim().length < 15}
            >
              <Sparkles size={14} className={isLoading ? "spin" : ""} />
              <span>{isLoading ? "Searching 10 Registries & Embedding..." : "Find Supporting Citations"}</span>
            </button>
          </div>
        </div>
      ) : (
        /* Mode 2: Topic & Literature Explorer */
        <div className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", alignItems: "center", marginBottom: "1rem" }}>
            <div style={{ position: "relative", flex: "1 1 320px" }}>
              <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
              <input
                type="text"
                placeholder="Search topic or question (e.g. 'self-supervised visual representation learning', 'CRISPR off-target detection')..."
                value={topicQuery}
                onChange={(e) => setTopicQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearchTopic()}
                style={{
                  width: "100%",
                  padding: "0.6rem 0.75rem 0.6rem 2.25rem",
                  fontSize: "0.875rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-subtle)",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                }}
              />
            </div>

            {/* Filter Mode Selector */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Filter size={14} style={{ color: "var(--text-muted)" }} />
              <select
                value={filterMode}
                onChange={(e) => setFilterMode(e.target.value)}
                style={{
                  padding: "0.55rem 0.75rem",
                  fontSize: "0.8125rem",
                  borderRadius: "6px",
                  border: "1px solid var(--border-subtle)",
                  backgroundColor: "var(--bg-primary)",
                  color: "var(--text-primary)",
                  cursor: "pointer",
                }}
              >
                <option value="general">Relevance Composite</option>
                <option value="seminal">★ Seminal / Highly Cited</option>
                <option value="recent">⚡ Recent Advances (2022-2026)</option>
                <option value="open_access">🔓 Verified Open Access</option>
              </select>
            </div>

            <button
              type="button"
              className="btn-primary"
              onClick={handleSearchTopic}
              disabled={isLoading || topicQuery.trim().length < 3}
            >
              <Search size={14} className={isLoading ? "spin" : ""} />
              <span>{isLoading ? "Searching..." : "Explore Literature"}</span>
            </button>
          </div>

          {error && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.75rem", backgroundColor: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "6px", color: "#991b1b", fontSize: "0.8125rem" }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>
      )}

      {/* Format Selector Bar */}
      {(paragraphResults || topicResults) && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.25rem", paddingBottom: "0.75rem", borderBottom: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Select Citation Output Standard:
          </div>
          <div style={{ display: "inline-flex", borderRadius: "6px", border: "1px solid var(--border-subtle)", overflow: "hidden" }}>
            {["ieee", "apa", "mla", "chicago", "bibtex"].map((fmt) => (
              <button
                key={fmt}
                type="button"
                onClick={() => setActiveFormat(fmt)}
                style={{
                  padding: "0.3rem 0.75rem",
                  fontSize: "0.75rem",
                  fontWeight: activeFormat === fmt ? 700 : 500,
                  backgroundColor: activeFormat === fmt ? "var(--accent-primary)" : "var(--bg-primary)",
                  color: activeFormat === fmt ? "#ffffff" : "var(--text-secondary)",
                  border: "none",
                  borderLeft: fmt !== "ieee" ? "1px solid var(--border-subtle)" : "none",
                  cursor: "pointer",
                  textTransform: "uppercase",
                }}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results View for Mode 1: Paragraph Claims */}
      {activeMode === "paragraph" && paragraphResults && (
        <div>
          {paragraphResults.results.map((item, claimIdx) => (
            <div key={claimIdx} className="academic-card" style={{ padding: "1.25rem", marginBottom: "1.25rem" }}>
              <div style={{ marginBottom: "1rem", borderLeft: "3px solid var(--accent-primary)", paddingLeft: "0.75rem" }}>
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-primary)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                  Extracted Assertive Claim #{claimIdx + 1}:
                </span>
                <p style={{ fontSize: "0.9375rem", fontWeight: 500, color: "var(--text-primary)", margin: "0.25rem 0 0 0", lineHeight: 1.45 }}>
                  "{item.claim}"
                </p>
              </div>

              <div style={{ fontSize: "0.8125rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                Empirical Supporting Works ({item.suggestions.length}):
              </div>

              {item.suggestions.length === 0 ? (
                <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic", margin: 0 }}>
                  No high-confidence publications matched this specific claim sentence.
                </p>
              ) : (
                <div style={{ display: "grid", gap: "0.75rem" }}>
                  {item.suggestions.map((cand, candIdx) =>
                    renderCitationCard(cand, candIdx, `p-${claimIdx}`)
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Results View for Mode 2: Topic Search */}
      {activeMode === "topic" && topicResults && (
        <div className="academic-card" style={{ padding: "1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
              Literature Recommendations for "{topicResults.query}" ({topicResults.total_found} works)
            </h4>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Filter: <strong>{topicResults.filter_mode}</strong>
            </span>
          </div>

          {topicResults.results.length === 0 ? (
            <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)", fontStyle: "italic" }}>
              No publications found matching this query under the selected filter.
            </p>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {topicResults.results.map((cand, candIdx) =>
                renderCitationCard(cand, candIdx, `t`)
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
