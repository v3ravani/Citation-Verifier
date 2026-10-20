import React, { useMemo } from "react";
import { Calendar, TrendingUp, Clock, Award, History, Layers } from "lucide-react";

export default function CitationTimeline({ references, onSelectYear }) {
  const stats = useMemo(() => {
    const currentYear = new Date().getFullYear();
    const years = [];
    const yearCounts = {};

    references.forEach((r) => {
      const y = (r.external && r.external.year) || (r.parsed && r.parsed.year);
      if (y && typeof y === "number" && y > 1900 && y <= currentYear + 2) {
        years.push(y);
        yearCounts[y] = (yearCounts[y] || 0) + 1;
      }
    });

    years.sort((a, b) => a - b);
    const totalDated = years.length;
    const medianYear = totalDated > 0 ? years[Math.floor(totalDated / 2)] : null;
    const medianAge = medianYear ? currentYear - medianYear : null;

    // Recency: published in last 5 years
    const recentCount = years.filter((y) => currentYear - y <= 5).length;
    const recencyPct = totalDated > 0 ? Math.round((recentCount / totalDated) * 100) : 0;

    // Vintage: older than 15 years
    const vintageCount = years.filter((y) => currentYear - y >= 15).length;
    const vintagePct = totalDated > 0 ? Math.round((vintageCount / totalDated) * 100) : 0;

    // Sorted year list for the bar chart
    const minYear = years.length ? Math.max(years[0], currentYear - 25) : currentYear - 10;
    const chartBars = [];
    let maxCount = 1;

    for (let yr = minYear; yr <= currentYear; yr++) {
      const count = yearCounts[yr] || 0;
      if (count > maxCount) maxCount = count;
      chartBars.push({ year: yr, count });
    }

    return {
      totalDated,
      medianYear,
      medianAge,
      recencyPct,
      vintagePct,
      chartBars,
      maxCount,
    };
  }, [references]);

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Metrics Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.25rem" }}>
        <div className="academic-card" style={{ padding: "1rem 1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>Median Citation Year</span>
            <Calendar size={16} style={{ color: "var(--accent-primary)" }} />
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {stats.medianYear || "N/A"}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            {stats.medianAge !== null ? `Average paper age: ~${stats.medianAge} years` : "No dated references"}
          </div>
        </div>

        <div className="academic-card" style={{ padding: "1rem 1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>Recency Index (≤ 5 Yrs)</span>
            <TrendingUp size={16} style={{ color: "#16a34a" }} />
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>
            {stats.recencyPct}%
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            State-of-the-art recency metric
          </div>
        </div>

        <div className="academic-card" style={{ padding: "1rem 1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>Foundational Vintage (≥ 15 Yrs)</span>
            <History size={16} style={{ color: "var(--accent-primary)" }} />
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-primary)" }}>
            {stats.vintagePct}%
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Foundational classical literature
          </div>
        </div>
      </div>

      {/* Interactive Year Bar Chart */}
      <div className="academic-card" style={{ padding: "1.5rem", marginBottom: "1.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem", flexWrap: "wrap", gap: "0.5rem" }}>
          <div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
              Publication Year Distribution
            </h4>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Distribution of {stats.totalDated} dated references across publication years
            </span>
          </div>

          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", backgroundColor: "var(--bg-secondary)", padding: "0.25rem 0.6rem", borderRadius: "4px", border: "1px solid var(--border-subtle)" }}>
            Timeline span: {stats.chartBars[0]?.year} – {stats.chartBars[stats.chartBars.length - 1]?.year}
          </span>
        </div>

        {/* Visual Bar Graph */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: "0.35rem", height: "160px", padding: "1rem 0", borderBottom: "1px solid var(--border-subtle)", overflowX: "auto" }}>
          {stats.chartBars.map((bar) => {
            const heightPct = bar.count > 0 ? Math.max(12, (bar.count / stats.maxCount) * 100) : 0;
            return (
              <div
                key={bar.year}
                style={{
                  flex: "1 1 24px",
                  minWidth: "22px",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "flex-end",
                  cursor: bar.count > 0 ? "pointer" : "default",
                }}
                onClick={() => bar.count > 0 && onSelectYear && onSelectYear(bar.year)}
                title={`${bar.year}: ${bar.count} reference(s)`}
              >
                {bar.count > 0 && (
                  <span style={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.2rem" }}>
                    {bar.count}
                  </span>
                )}
                <div
                  style={{
                    width: "100%",
                    height: `${heightPct}%`,
                    backgroundColor: bar.count > 0 ? "var(--accent-primary)" : "var(--bg-tertiary)",
                    borderRadius: "3px 3px 0 0",
                    transition: "height 0.2s ease, background-color 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (bar.count > 0) e.currentTarget.style.backgroundColor = "var(--accent-hover)";
                  }}
                  onMouseLeave={(e) => {
                    if (bar.count > 0) e.currentTarget.style.backgroundColor = "var(--accent-primary)";
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Year Labels */}
        <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "0.5rem", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          <span>{stats.chartBars[0]?.year}</span>
          <span>{stats.medianYear ? `Median (${stats.medianYear})` : ""}</span>
          <span>{stats.chartBars[stats.chartBars.length - 1]?.year}</span>
        </div>
      </div>
    </div>
  );
}
