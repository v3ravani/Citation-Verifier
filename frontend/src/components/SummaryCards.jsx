import React from "react";
import { CheckCircle2, HelpCircle, AlertTriangle, XCircle, FileText, Target, AlertOctagon, ShieldAlert, Award, ShieldCheck } from "lucide-react";

export default function SummaryCards({ summary, onFilterClick, activeFilter }) {
  if (!summary) return null;

  const avgScore = summary.average_integrity_score || (
    summary.references_detected > 0
      ? Math.round(((summary.verified_exact * 100 + summary.verified_probable * 80) / (summary.references_detected * 100)) * 100)
      : 0
  );

  const getScoreRating = (s) => {
    if (s >= 85) return { label: "High Confidence", color: "#065F46", bg: "#ECFDF5" };
    if (s >= 70) return { label: "Acceptable", color: "#1E40AF", bg: "#EFF6FF" };
    if (s >= 50) return { label: "Moderate Risk", color: "#92400E", bg: "#FFFBEB" };
    return { label: "High Risk / Audit Needed", color: "#991B1B", bg: "#FEF2F2" };
  };

  const rating = getScoreRating(avgScore);

  const cards = [
    {
      id: "all",
      label: "References",
      value: summary.references_detected,
      icon: FileText,
      color: "var(--accent-primary)",
      border: "var(--border-subtle)",
    },
    {
      id: "verified_exact",
      label: "Verified Exact",
      value: summary.verified_exact,
      icon: CheckCircle2,
      color: "var(--status-verified-text)",
      bg: "var(--status-verified-bg)",
      border: "var(--status-verified-border)",
    },
    {
      id: "verified_probable",
      label: "Probable Matches",
      value: summary.verified_probable,
      icon: HelpCircle,
      color: "var(--status-probable-text)",
      bg: "var(--status-probable-bg)",
      border: "var(--status-probable-border)",
    },
    {
      id: "peer_reviewed",
      label: "Peer-Reviewed",
      value: summary.peer_reviewed_count || 0,
      icon: ShieldCheck,
      color: "#059669",
      bg: "#ecfdf5",
      border: "#a7f3d0",
    },
    {
      id: "metadata_mismatch",
      label: "Metadata Mismatch",
      value: summary.metadata_mismatch,
      icon: AlertTriangle,
      color: "var(--status-mismatch-text)",
      bg: "var(--status-mismatch-bg)",
      border: "var(--status-mismatch-border)",
    },
    {
      id: "retracted",
      label: "Retraction Watch",
      value: summary.retracted_citations_count || 0,
      icon: ShieldAlert,
      color: (summary.retracted_citations_count || 0) > 0 ? "#dc2626" : "var(--text-muted)",
      bg: (summary.retracted_citations_count || 0) > 0 ? "#fef2f2" : "var(--bg-primary)",
      border: (summary.retracted_citations_count || 0) > 0 ? "#fca5a5" : "var(--border-subtle)",
    },
    {
      id: "hallucination",
      label: "Hallucination Risk",
      value: summary.hallucination_risk_count || 0,
      icon: XCircle,
      color: (summary.hallucination_risk_count || 0) > 0 ? "#dc2626" : "var(--text-muted)",
      bg: (summary.hallucination_risk_count || 0) > 0 ? "#fef2f2" : "var(--bg-primary)",
      border: (summary.hallucination_risk_count || 0) > 0 ? "#fca5a5" : "var(--border-subtle)",
    },
    {
      id: "unverified",
      label: "Unverified",
      value: summary.unverified,
      icon: XCircle,
      color: "var(--status-unverified-text)",
      bg: "var(--status-unverified-bg)",
      border: "var(--status-unverified-border)",
    },
    {
      id: "contexts",
      label: "Citation Contexts",
      value: summary.citation_occurrences,
      icon: Target,
      color: "var(--text-primary)",
      border: "var(--border-subtle)",
    },
    {
      id: "overclaim",
      label: "Overclaim Flags",
      value: summary.overclaim_flags,
      icon: AlertOctagon,
      color: summary.overclaim_flags > 0 ? "var(--status-unverified-text)" : "var(--text-muted)",
      bg: summary.overclaim_flags > 0 ? "var(--status-unverified-bg)" : "var(--bg-primary)",
      border: summary.overclaim_flags > 0 ? "var(--status-unverified-border)" : "var(--border-subtle)",
    },
  ];

  return (
    <div style={{ marginBottom: "1.75rem" }}>
      {/* Retraction Alert Banner if any retracted works exist */}
      {(summary.retracted_citations_count || 0) > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem 1rem", backgroundColor: "#fef2f2", border: "1px solid #f87171", borderRadius: "6px", color: "#991b1b", marginBottom: "1rem" }}>
          <ShieldAlert size={18} style={{ flexShrink: 0 }} />
          <div style={{ fontSize: "0.8125rem" }}>
            <strong>Institutional Retraction Alert:</strong> {summary.retracted_citations_count} citation(s) in this document have been flagged as RETRACTED or subject to an expression of concern in global registries.
          </div>
        </div>
      )}

      {/* Grid of Metric Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(135px, 1fr))", gap: "0.75rem" }}>
        {/* Integrity Gauge Card */}
        <div
          style={{
            backgroundColor: rating.bg,
            border: `1px solid ${rating.color}`,
            borderRadius: "6px",
            padding: "0.875rem 1rem",
            gridColumn: "span 1",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, color: rating.color, textTransform: "uppercase", letterSpacing: "0.03em" }}>
              Integrity Score
            </span>
            <Award size={16} style={{ color: rating.color }} />
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: rating.color, letterSpacing: "-0.02em" }}>
            {avgScore}<span style={{ fontSize: "0.875rem", fontWeight: 500 }}>/100</span>
          </div>
          <div style={{ fontSize: "0.7rem", fontWeight: 600, color: rating.color, marginTop: "0.15rem" }}>
            {rating.label}
          </div>
        </div>

        {cards.map((c) => {
          const Icon = c.icon;
          const isSelected = activeFilter === c.id;
          return (
            <div
              key={c.id}
              onClick={() => onFilterClick && onFilterClick(c.id)}
              style={{
                backgroundColor: c.bg || "var(--bg-primary)",
                border: `1px solid ${isSelected ? "var(--accent-primary)" : c.border || "var(--border-subtle)"}`,
                borderRadius: "6px",
                padding: "0.875rem 1rem",
                cursor: "pointer",
                transition: "all 0.15s ease",
                boxShadow: isSelected ? "0 0 0 1px var(--accent-primary)" : "none",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.35rem" }}>
                <span style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                  {c.label}
                </span>
                <Icon size={15} style={{ color: c.color }} />
              </div>
              <div style={{ fontSize: "1.375rem", fontWeight: 700, color: c.color, letterSpacing: "-0.02em" }}>
                {c.value}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
