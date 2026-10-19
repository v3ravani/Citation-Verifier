import React, { useState, useMemo } from "react";
import { Search, Filter, ArrowUpDown, ChevronRight, AlertTriangle } from "lucide-react";

export default function ReferenceTable({ references, onSelectReference, activeFilter, onFilterChange }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("id_asc");

  // Filter & Search Logic
  const filteredReferences = useMemo(() => {
    return references.filter((ref) => {
      // 1. Status Filter
      if (activeFilter === "verified_exact" && ref.verification.status !== "verified_exact") return false;
      if (activeFilter === "verified_probable" && ref.verification.status !== "verified_probable") return false;
      if (activeFilter === "metadata_mismatch" && ref.verification.status !== "metadata_mismatch") return false;
      if (activeFilter === "unverified" && ref.verification.status !== "unverified") return false;
      if (activeFilter === "overclaim" && (!ref.citation_occurrences || !ref.citation_occurrences.some((c) => c.overclaim_flag))) return false;

      // 2. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const raw = (ref.raw_text || "").toLowerCase();
        const title = ((ref.external && ref.external.title) || (ref.parsed && ref.parsed.title) || "").toLowerCase();
        const doi = ((ref.parsed && ref.parsed.doi) || (ref.external && ref.external.doi) || "").toLowerCase();
        const authors = (ref.parsed && ref.parsed.authors ? ref.parsed.authors.join(" ") : "").toLowerCase();
        if (!raw.includes(q) && !title.includes(q) && !doi.includes(q) && !authors.includes(q)) {
          return false;
        }
      }

      return true;
    });
  }, [references, activeFilter, searchQuery]);

  // Sorting
  const sortedReferences = useMemo(() => {
    return [...filteredReferences].sort((a, b) => {
      if (sortBy === "id_asc") return a.reference_id - b.reference_id;
      if (sortBy === "id_desc") return b.reference_id - a.reference_id;
      if (sortBy === "meta_score_desc") return (b.verification.verification_score || 0) - (a.verification.verification_score || 0);
      if (sortBy === "overall_desc") return (b.overall_score || 0) - (a.overall_score || 0);
      if (sortBy === "sim_desc") {
        const getAvgSim = (item) => {
          const sims = (item.citation_occurrences || [])
            .map((c) => c.semantic_similarity)
            .filter((s) => s !== null && s !== undefined);
          return sims.length > 0 ? sims.reduce((acc, v) => acc + v, 0) / sims.length : -1;
        };
        return getAvgSim(b) - getAvgSim(a);
      }
      return 0;
    });
  }, [filteredReferences, sortBy]);

  return (
    <div className="academic-card" style={{ padding: "1.25rem" }}>
      {/* Table Controls */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "1rem", marginBottom: "1.25rem" }}>
        {/* Search */}
        <div style={{ position: "relative", minWidth: "280px", flex: "1 1 300px" }}>
          <Search size={16} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          <input
            type="text"
            placeholder="Search by title, author, DOI, or reference text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem 0.75rem 0.5rem 2.25rem",
              fontSize: "0.875rem",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              backgroundColor: "var(--bg-primary)",
              color: "var(--text-primary)"
            }}
          />
        </div>

        {/* Filter and Sort */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <Filter size={15} style={{ color: "var(--text-muted)" }} />
            <select
              value={activeFilter}
              onChange={(e) => onFilterChange(e.target.value)}
              style={{
                padding: "0.45rem 0.75rem",
                fontSize: "0.8125rem",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                backgroundColor: "var(--bg-primary)",
                color: "var(--text-primary)",
                cursor: "pointer"
              }}
            >
              <option value="all">All References ({references.length})</option>
              <option value="verified_exact">Verified Exact Only</option>
              <option value="verified_probable">Probable Matches Only</option>
              <option value="metadata_mismatch">Metadata Mismatches Only</option>
              <option value="unverified">Unverified Only</option>
              <option value="overclaim">Flagged Contexts Only</option>
            </select>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <ArrowUpDown size={15} style={{ color: "var(--text-muted)" }} />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                padding: "0.45rem 0.75rem",
                fontSize: "0.8125rem",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                backgroundColor: "var(--bg-primary)",
                color: "var(--text-primary)",
                cursor: "pointer"
              }}
            >
              <option value="id_asc">Sort: Number (# Asc)</option>
              <option value="id_desc">Sort: Number (# Desc)</option>
              <option value="meta_score_desc">Sort: Metadata Score</option>
              <option value="overall_desc">Sort: Overall Score</option>
              <option value="sim_desc">Sort: Semantic Similarity</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="data-table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: "70px" }}>Ref</th>
              <th>Extracted Reference & Title</th>
              <th style={{ width: "160px" }}>Verification Status</th>
              <th style={{ width: "120px" }}>Meta Score</th>
              <th style={{ width: "130px" }}>Context Relevance</th>
              <th style={{ width: "110px" }}>Overall Score</th>
              <th style={{ width: "80px", textAlign: "right" }}>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {sortedReferences.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", padding: "2.5rem 1rem", color: "var(--text-muted)" }}>
                  No references match the active filter or search criteria.
                </td>
              </tr>
            ) : (
              sortedReferences.map((ref) => {
                const statusClass = ref.verification.status;
                const statusText = statusClass.replace("_", " ");
                const hasFlags = ref.review_flags && ref.review_flags.length > 0;
                const title = (ref.external && ref.external.title) || (ref.parsed && ref.parsed.title) || ref.raw_text.slice(0, 80);

                // Avg context similarity
                const validSims = (ref.citation_occurrences || [])
                  .map((c) => c.semantic_similarity)
                  .filter((s) => s !== null && s !== undefined);
                const avgSim = validSims.length > 0 ? (validSims.reduce((a, b) => a + b, 0) / validSims.length).toFixed(2) : null;

                return (
                  <tr
                    key={ref.reference_id}
                    onClick={() => onSelectReference(ref)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>
                      <span style={{ fontWeight: 600, color: "var(--accent-primary)" }}>
                        {ref.marker || `[${ref.reference_id}]`}
                      </span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem", lineHeight: 1.35 }}>
                        {title}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "450px" }}>
                        {ref.raw_text}
                      </div>
                      {hasFlags && (
                        <div style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem", marginTop: "0.375rem", fontSize: "0.6875rem", color: "var(--status-mismatch-text)", backgroundColor: "var(--status-mismatch-bg)", border: "1px solid var(--status-mismatch-border)", padding: "0.125rem 0.375rem", borderRadius: "3px" }}>
                          <AlertTriangle size={12} />
                          <span>{ref.review_flags[0]}</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${statusClass}`}>
                        {statusText}
                      </span>
                      <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                        Source: {ref.verification.source}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                        {ref.verification.verification_score}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> / 100</span>
                    </td>
                    <td>
                      {avgSim !== null ? (
                        <div>
                          <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                            {avgSim}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> sim</span>
                          <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                            {ref.citation_occurrences.length} context{ref.citation_occurrences.length === 1 ? "" : "s"}
                          </div>
                        </div>
                      ) : (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                          Unavailable
                        </span>
                      )}
                    </td>
                    <td>
                      {ref.overall_score !== null ? (
                        <div>
                          <span style={{ fontWeight: 600, color: "var(--accent-primary)" }}>
                            {ref.overall_score}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}> / 100</span>
                        </div>
                      ) : (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                          Unavailable
                        </span>
                      )}
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <button
                        type="button"
                        className="btn-secondary btn-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectReference(ref);
                        }}
                      >
                        <span>View</span>
                        <ChevronRight size={14} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
