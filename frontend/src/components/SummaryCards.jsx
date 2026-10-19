import React from "react";
import { CheckCircle2, HelpCircle, AlertTriangle, XCircle, FileText, Target, AlertOctagon } from "lucide-react";

export default function SummaryCards({ summary, onFilterClick, activeFilter }) {
  if (!summary) return null;

  const cards = [
    {
      id: "all",
      label: "References Detected",
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
      id: "metadata_mismatch",
      label: "Metadata Mismatch",
      value: summary.metadata_mismatch,
      icon: AlertTriangle,
      color: "var(--status-mismatch-text)",
      bg: "var(--status-mismatch-bg)",
      border: "var(--status-mismatch-border)",
    },
    {
      id: "unverified",
      label: "Unverified Records",
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
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.875rem", marginBottom: "1.75rem" }}>
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
              padding: "1rem 1.125rem",
              cursor: "pointer",
              transition: "all 0.15s ease",
              boxShadow: isSelected ? "0 0 0 1px var(--accent-primary)" : "none"
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.03em" }}>
                {c.label}
              </span>
              <Icon size={16} style={{ color: c.color }} />
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: c.color, letterSpacing: "-0.02em" }}>
              {c.value}
            </div>
          </div>
        );
      })}
    </div>
  );
}
