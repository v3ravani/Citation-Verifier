import React, { useState } from "react";
import { Download, RefreshCw, FileText, Share2, ArrowLeft, Calendar, FileCheck, Hash } from "lucide-react";
import SummaryCards from "../components/SummaryCards";
import ReferenceTable from "../components/ReferenceTable";
import ReferenceDetailsModal from "../components/ReferenceDetailsModal";
import CitationGraph from "../components/CitationGraph";
import { getTxtExportUrl, getJsonExportUrl, analyzePaperById } from "../api/client";

export default function Analysis({ result, onBack, onUpdateResult }) {
  const [selectedReference, setSelectedReference] = useState(null);
  const [activeTab, setActiveTab] = useState("table"); // "table" or "graph"
  const [activeFilter, setActiveFilter] = useState("all");
  const [isRerunning, setIsRerunning] = useState(false);

  if (!result) return null;

  const paper = result.paper || {};
  const summary = result.summary || {};
  const references = result.references || [];
  const graph = result.graph || { nodes: [], edges: [] };

  const handleRerun = async () => {
    setIsRerunning(true);
    try {
      const refreshed = await analyzePaperById(paper.id, true);
      onUpdateResult(refreshed);
    } catch (e) {
      alert(`Re-run failed: ${e.message}`);
    } finally {
      setIsRerunning(false);
    }
  };

  const handleSelectReferenceFromGraph = (partialRef) => {
    const full = references.find((r) => r.reference_id === partialRef.reference_id);
    if (full) {
      setSelectedReference(full);
    }
  };

  return (
    <div>
      {/* Top Bar */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "1rem", marginBottom: "1.5rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border-subtle)" }}>
        <div>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={onBack}
            style={{ marginBottom: "0.5rem" }}
          >
            <ArrowLeft size={14} />
            <span>Upload Another Paper</span>
          </button>

          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em", marginBottom: "0.25rem" }}>
            {paper.title_guess || paper.filename}
          </h2>

          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "1rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <FileCheck size={13} /> {paper.filename} ({paper.pages} pages)
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <Hash size={13} /> ID: <code>{paper.id}</code>
            </span>
            {result.analyzed_at && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                <Calendar size={13} /> {new Date(result.analyzed_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleRerun}
            disabled={isRerunning}
            title="Re-run verification pipeline"
          >
            <RefreshCw size={14} className={isRerunning ? "spin" : ""} />
            <span>{isRerunning ? "Re-running..." : "Re-run"}</span>
          </button>

          <a
            href={getTxtExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
          >
            <Download size={14} />
            <span>Export TXT</span>
          </a>

          <a
            href={getJsonExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
          >
            <Download size={14} />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <SummaryCards
        summary={summary}
        activeFilter={activeFilter}
        onFilterClick={(filterId) => {
          setActiveFilter(filterId);
          setActiveTab("table");
        }}
      />

      {/* View Selector Tabs */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
        <button
          type="button"
          className={`btn-secondary ${activeTab === "table" ? "active" : ""}`}
          onClick={() => setActiveTab("table")}
          style={{
            backgroundColor: activeTab === "table" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "table" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "table" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "table" ? 600 : 500,
          }}
        >
          <FileText size={15} />
          <span>Reference Audit Table ({references.length})</span>
        </button>

        <button
          type="button"
          className={`btn-secondary ${activeTab === "graph" ? "active" : ""}`}
          onClick={() => setActiveTab("graph")}
          style={{
            backgroundColor: activeTab === "graph" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "graph" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "graph" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "graph" ? 600 : 500,
          }}
        >
          <Share2 size={15} />
          <span>Citation Relationship Graph</span>
        </button>
      </div>

      {/* Main View Area */}
      {activeTab === "table" ? (
        <ReferenceTable
          references={references}
          onSelectReference={setSelectedReference}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
        />
      ) : (
        <CitationGraph
          graph={graph}
          onSelectReference={handleSelectReferenceFromGraph}
        />
      )}

      {/* Reference Details Modal Drawer */}
      {selectedReference && (
        <ReferenceDetailsModal
          reference={selectedReference}
          onClose={() => setSelectedReference(null)}
        />
      )}
    </div>
  );
}
