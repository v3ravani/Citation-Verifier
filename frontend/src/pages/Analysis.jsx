import React, { useState } from "react";
import { Download, RefreshCw, FileText, Share2, ArrowLeft, Calendar, FileCheck, Hash, Sparkles, ShieldAlert, Clock, FileSpreadsheet, Code2, ShieldCheck, Award } from "lucide-react";
import SummaryCards from "../components/SummaryCards";
import ReferenceTable from "../components/ReferenceTable";
import ReferenceDetailsModal from "../components/ReferenceDetailsModal";
import CitationGraph3D from "../components/CitationGraph3D";
import CitationSuggester from "../components/CitationSuggester";
import CitationGapFinder from "../components/CitationGapFinder";
import CitationTimeline from "../components/CitationTimeline";
import ExecutiveReportView from "../components/ExecutiveReportView";
import {
  getTxtExportUrl,
  getJsonExportUrl,
  getAnnotatedPdfExportUrl,
  getBibtexExportUrl,
  getCsvExportUrl,
  getMarkdownExportUrl,
  getHtmlExportUrl,
  analyzePaperById,
  getAnalysisProgress,
  setUserVerification
} from "../api/client";

export default function Analysis({ result, onBack, onUpdateResult }) {
  const [selectedReference, setSelectedReference] = useState(null);
  const [activeTab, setActiveTab] = useState("table"); // "table", "graph", "gaps", "timeline", "suggester"
  const [activeFilter, setActiveFilter] = useState("all");
  const [isRerunning, setIsRerunning] = useState(false);
  const [rerunProgress, setRerunProgress] = useState({ percent: 10, stage: "Re-running pipeline..." });

  if (!result) return null;

  const paper = result.paper || {};
  const summary = result.summary || {};
  const references = result.references || [];
  const graph = result.graph || { nodes: [], edges: [] };

  const handleToggleUserVerification = async (refItem, verified, note = null) => {
    try {
      const updated = await setUserVerification(paper.id, refItem.reference_id, verified, note);
      onUpdateResult(updated);
      if (selectedReference && selectedReference.reference_id === refItem.reference_id) {
        const matching = updated.references.find((r) => r.reference_id === refItem.reference_id);
        if (matching) setSelectedReference(matching);
      }
    } catch (err) {
      alert(`User verification update failed: ${err.message}`);
    }
  };

  const handleRerun = async () => {
    setIsRerunning(true);
    setRerunProgress({ percent: 15, stage: "Initiating re-analysis across 10 scholarly registries..." });
    let poller = setInterval(async () => {
      const p = await getAnalysisProgress(paper.id);
      if (p) {
        setRerunProgress({
          percent: p.percent || 15,
          stage: p.stage || "Re-running analysis...",
          details: p.details || ""
        });
      }
    }, 250);

    try {
      const refreshed = await analyzePaperById(paper.id, true);
      clearInterval(poller);
      setRerunProgress({ percent: 100, stage: "Completed! Refreshing audit views..." });
      setTimeout(() => {
        onUpdateResult(refreshed);
      }, 350);
    } catch (e) {
      clearInterval(poller);
      alert(`Re-run failed: ${e.message}`);
    } finally {
      setTimeout(() => {
        setIsRerunning(false);
      }, 400);
    }
  };

  const handleSelectReferenceFromGraph = (partialRef) => {
    const full = references.find((r) => r.reference_id === partialRef.reference_id);
    if (full) {
      setSelectedReference(full);
    }
  };

  const handleSelectYearFromTimeline = (year) => {
    setActiveTab("table");
    setActiveFilter("all");
  };

  return (
    <div>
      {/* Top Product Header */}
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "1rem", marginBottom: "1.5rem", paddingBottom: "1.25rem", borderBottom: "1px solid var(--border-subtle)" }}>
        <div>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={onBack}
            style={{ marginBottom: "0.5rem" }}
          >
            <ArrowLeft size={13} />
            <span>Upload Another Document</span>
          </button>

          <h2 style={{ fontSize: "1.375rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.015em", marginBottom: "0.25rem" }}>
            {paper.title_guess || paper.filename}
          </h2>

          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "1rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <FileCheck size={13} /> {paper.filename} ({paper.pages} pages)
            </span>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <Hash size={13} /> SHA-256: <code>{paper.sha256 ? `${paper.sha256.slice(0, 16)}...` : paper.id}</code>
            </span>
            {result.analyzed_at && (
              <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                <Calendar size={13} /> {new Date(result.analyzed_at).toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Product Action Suite */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleRerun}
            disabled={isRerunning}
            title="Re-run verification pipeline with fresh cache"
          >
            <RefreshCw size={13} className={isRerunning ? "spin" : ""} />
            <span>{isRerunning ? "Re-running..." : "Re-run"}</span>
          </button>

          {/* Export Suite */}
          <a
            href={getAnnotatedPdfExportUrl(paper.id)}
            download
            className="btn-primary"
            style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "0.35rem" }}
            title="Download PDF marked up with precise red, yellow, and green highlights plus inline review notes"
          >
            <Download size={13} />
            <span>Annotated PDF</span>
            <span style={{ fontSize: "0.65rem", backgroundColor: "rgba(255,255,255,0.25)", padding: "0.1rem 0.35rem", borderRadius: "10px", fontWeight: 700 }}>Flags & Notes</span>
          </a>

          <a
            href={getHtmlExportUrl(paper.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Open printable standalone executive HTML audit dossier"
          >
            <ShieldCheck size={13} />
            <span>HTML Dossier</span>
          </a>

          <a
            href={getBibtexExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Export verified bibliography in clean BibTeX format"
          >
            <Code2 size={13} />
            <span>BibTeX</span>
          </a>

          <a
            href={getCsvExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Export citation audit spreadsheet in CSV format"
          >
            <FileSpreadsheet size={13} />
            <span>CSV</span>
          </a>

          <a
            href={getMarkdownExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Export executive summary in Markdown format"
          >
            <FileText size={13} />
            <span>MD</span>
          </a>

          <a
            href={getTxtExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Download plain-text report"
          >
            <span>TXT</span>
          </a>

          <a
            href={getJsonExportUrl(paper.id)}
            download
            className="btn-secondary"
            style={{ textDecoration: "none" }}
            title="Download complete JSON analysis result"
          >
            <span>JSON</span>
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
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.25rem", flexWrap: "wrap", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "0.75rem" }}>
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
          <span>3D Citation Graph</span>
        </button>

        <button
          type="button"
          className={`btn-secondary ${activeTab === "gaps" ? "active" : ""}`}
          onClick={() => setActiveTab("gaps")}
          style={{
            backgroundColor: activeTab === "gaps" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "gaps" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "gaps" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "gaps" ? 600 : 500,
          }}
        >
          <ShieldAlert size={15} />
          <span>Citation Gap Finder</span>
        </button>

        <button
          type="button"
          className={`btn-secondary ${activeTab === "timeline" ? "active" : ""}`}
          onClick={() => setActiveTab("timeline")}
          style={{
            backgroundColor: activeTab === "timeline" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "timeline" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "timeline" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "timeline" ? 600 : 500,
          }}
        >
          <Clock size={15} />
          <span>Publication Vintage & Timeline</span>
        </button>

        <button
          type="button"
          className={`btn-secondary ${activeTab === "suggester" ? "active" : ""}`}
          onClick={() => setActiveTab("suggester")}
          style={{
            backgroundColor: activeTab === "suggester" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "suggester" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "suggester" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "suggester" ? 600 : 500,
          }}
        >
          <Sparkles size={15} />
          <span>Reference Discovery Studio</span>
        </button>

        <button
          type="button"
          className={`btn-secondary ${activeTab === "report" ? "active" : ""}`}
          onClick={() => setActiveTab("report")}
          style={{
            backgroundColor: activeTab === "report" ? "var(--accent-light)" : "var(--bg-primary)",
            borderColor: activeTab === "report" ? "var(--accent-primary)" : "var(--border-subtle)",
            color: activeTab === "report" ? "var(--accent-primary)" : "var(--text-secondary)",
            fontWeight: activeTab === "report" ? 600 : 500,
          }}
        >
          <Award size={15} />
          <span>Executive Audit Report</span>
        </button>
      </div>

      {/* Main Tab Views */}
      {activeTab === "table" ? (
        <ReferenceTable
          references={references}
          onSelectReference={setSelectedReference}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          onToggleVerify={handleToggleUserVerification}
        />
      ) : activeTab === "graph" ? (
        <CitationGraph3D
          graph={graph}
          onSelectReference={handleSelectReferenceFromGraph}
        />
      ) : activeTab === "gaps" ? (
        <CitationGapFinder paperId={paper.id} />
      ) : activeTab === "timeline" ? (
        <CitationTimeline
          references={references}
          onSelectYear={handleSelectYearFromTimeline}
        />
      ) : activeTab === "suggester" ? (
        <CitationSuggester />
      ) : (
        <ExecutiveReportView
          result={result}
          onSelectReference={setSelectedReference}
        />
      )}

      {/* Reference Details Modal Drawer */}
      <ReferenceDetailsModal
        reference={selectedReference}
        onClose={() => setSelectedReference(null)}
        onToggleVerify={handleToggleUserVerification}
      />

      {/* Rerun Progress Modal Overlay */}
      {isRerunning && (
        <div className="modal-overlay" style={{ zIndex: 60 }}>
          <div
            className="modal-content"
            style={{
              maxWidth: "540px",
              padding: "2rem",
              textAlign: "center",
              boxShadow: "0 20px 40px -10px rgba(0, 0, 0, 0.2)"
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.75rem", marginBottom: "1rem" }}>
              <RefreshCw size={24} className="spin-slow" style={{ color: "var(--accent-primary)" }} />
              <h3 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0 }}>Re-running Verification Pipeline</h3>
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
              {rerunProgress.stage}
            </p>

            <div className="progress-track-wrapper" style={{ margin: "1rem 0" }}>
              <div
                className="progress-track-fill"
                style={{ width: `${Math.max(5, Math.min(100, rerunProgress.percent))}%` }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8125rem", color: "var(--text-muted)" }}>
              <span>Parallel registries & FAISS</span>
              <strong style={{ fontSize: "1.125rem", color: "var(--accent-primary)", fontFamily: "var(--font-mono)" }}>
                {rerunProgress.percent}%
              </strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
