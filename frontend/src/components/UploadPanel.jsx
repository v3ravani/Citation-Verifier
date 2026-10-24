import React, { useState, useRef } from "react";
import {
  Upload,
  FileUp,
  AlertCircle,
  ShieldCheck,
  CheckCircle2,
  Search,
  Cpu,
  BarChart3,
  Loader2,
  Clock,
  Layers,
  Zap,
  Globe
} from "lucide-react";

export default function UploadPanel({
  onUploadSuccess,
  isProcessing,
  progressData = {},
  errorMessage,
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const percent = progressData?.percent || 0;
  const stage = progressData?.stage || "Processing document...";
  const details = progressData?.details || "";
  const completedRefs = progressData?.completed_refs || 0;
  const totalRefs = progressData?.total_refs || 0;

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndProcessFile(files[0]);
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      validateAndProcessFile(files[0]);
    }
  };

  const validateAndProcessFile = (file) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Only PDF files are supported. Please select a valid research paper in PDF format.");
      return;
    }
    if (file.size > 30 * 1024 * 1024) {
      alert("File size exceeds 30 MB limit.");
      return;
    }
    onUploadSuccess(file);
  };

  // Pipeline 4-Stage Roadmap status evaluation
  const stages = [
    {
      id: 1,
      title: "PDF & Text Extraction",
      desc: "PyMuPDF text parsing & bibliography detection",
      min: 0,
      max: 20,
    },
    {
      id: 2,
      title: "Parallel Registry Verification",
      desc: "Concurrent queries across 10 scholarly engines",
      min: 20,
      max: 75,
    },
    {
      id: 3,
      title: "Sentence-BERT Semantic NLP",
      desc: "FAISS vector ranking & claim strength analysis",
      min: 75,
      max: 90,
    },
    {
      id: 4,
      title: "3D Graph & Audit Dossier",
      desc: "Graph topology, hallucination risk & canonical repair",
      min: 90,
      max: 100,
    },
  ];

  return (
    <div style={{ maxWidth: "880px", margin: "0 auto" }}>
      {/* Hero Intro */}
      <div style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1
          style={{
            fontSize: "2.125rem",
            fontWeight: 700,
            color: "var(--text-primary)",
            marginBottom: "0.75rem",
            letterSpacing: "-0.025em",
          }}
        >
          Verify citations beyond the bibliography.
        </h1>
        <p
          style={{
            fontSize: "1.0625rem",
            color: "var(--text-secondary)",
            maxWidth: "700px",
            margin: "0 auto",
            lineHeight: 1.6,
          }}
        >
          Concurrently verify references across 10 global academic registries (Crossref, Semantic
          Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite, PubMed/MEDLINE, DOAJ, HAL Open
          Science), detect AI hallucination risks, and audit claim semantic relevance.
        </p>
      </div>

      {/* Main Upload / Processing Panel */}
      {isProcessing ? (
        <div
          className="progress-dashboard"
          style={{
            marginBottom: "2rem",
            border: "1px solid var(--accent-light)",
            backgroundColor: "var(--bg-primary)",
          }}
        >
          {/* Header Row: Title & Percentage */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "1rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <div
                style={{
                  width: "40px",
                  height: "40px",
                  borderRadius: "10px",
                  backgroundColor: "var(--accent-light)",
                  color: "var(--accent-primary)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Loader2 size={22} className="spin-slow" />
              </div>
              <div>
                <h3
                  style={{
                    fontSize: "1.125rem",
                    fontWeight: 700,
                    color: "var(--text-primary)",
                    margin: 0,
                  }}
                >
                  Verifying Manuscript Citations
                </h3>
                <span style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
                  Multi-registry parallel engine active
                </span>
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <span className="progress-badge-pct">{percent}%</span>
            </div>
          </div>

          {/* Progress Bar Track */}
          <div className="progress-track-wrapper">
            <div
              className="progress-track-fill"
              style={{ width: `${Math.max(5, Math.min(100, percent))}%` }}
            />
          </div>

          {/* Current Stage & Real-time Details */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: "1rem",
              marginTop: "0.5rem",
              marginBottom: "1.5rem",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "0.9375rem",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                  marginBottom: "0.2rem",
                }}
              >
                {stage}
              </div>
              {details && (
                <div
                  style={{
                    fontSize: "0.8125rem",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                    maxWidth: "580px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {details}
                </div>
              )}
            </div>

            {totalRefs > 0 && (
              <div
                style={{
                  padding: "0.3rem 0.65rem",
                  backgroundColor: "var(--bg-tertiary)",
                  borderRadius: "6px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: "var(--accent-primary)",
                  whiteSpace: "nowrap",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {completedRefs} / {totalRefs} refs checked
              </div>
            )}
          </div>

          {/* Real-Time Telemetry Badges */}
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.5rem",
              paddingBottom: "1.25rem",
              borderBottom: "1px solid var(--border-subtle)",
              marginBottom: "1.25rem",
            }}
          >
            <div className="progress-step-pill active">
              <Zap size={13} style={{ color: "#2563eb" }} />
              <span>Parallel Workers (15 Concurrent)</span>
            </div>
            <div className="progress-step-pill">
              <Globe size={13} style={{ color: "var(--text-muted)" }} />
              <span>10 Authoritative Registries Queried</span>
            </div>
            <div className="progress-step-pill">
              <Layers size={13} style={{ color: "var(--text-muted)" }} />
              <span>Local Sentence-BERT & FAISS Vector Index</span>
            </div>
          </div>

          {/* 4-Stage Roadmap */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "0.75rem",
            }}
          >
            {stages.map((st) => {
              const isCompleted = percent >= st.max;
              const isActive = percent >= st.min && percent < st.max;
              const isPending = percent < st.min;

              return (
                <div
                  key={st.id}
                  style={{
                    padding: "0.75rem",
                    borderRadius: "8px",
                    backgroundColor: isActive
                      ? "var(--accent-light)"
                      : isCompleted
                      ? "var(--bg-secondary)"
                      : "var(--bg-primary)",
                    border: `1px solid ${
                      isActive
                        ? "#93c5fd"
                        : isCompleted
                        ? "var(--status-verified-border)"
                        : "var(--border-subtle)"
                    }`,
                    transition: "all 0.2s ease",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      marginBottom: "0.25rem",
                    }}
                  >
                    {isCompleted ? (
                      <CheckCircle2 size={16} style={{ color: "#059669" }} />
                    ) : isActive ? (
                      <Loader2 size={16} className="spin-slow" style={{ color: "#2563eb" }} />
                    ) : (
                      <Clock size={16} style={{ color: "var(--text-muted)" }} />
                    )}
                    <span
                      style={{
                        fontSize: "0.8125rem",
                        fontWeight: 600,
                        color: isActive
                          ? "var(--accent-primary)"
                          : isCompleted
                          ? "var(--text-primary)"
                          : "var(--text-muted)",
                      }}
                    >
                      {st.title}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      lineHeight: 1.3,
                    }}
                  >
                    {st.desc}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Standard Drag & Drop Upload Box */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${isDragOver ? "var(--accent-primary)" : "var(--border-strong)"}`,
            borderRadius: "10px",
            padding: "3.25rem 2rem",
            textAlign: "center",
            backgroundColor: isDragOver ? "var(--accent-light)" : "var(--bg-primary)",
            transition: "all 0.15s ease",
            marginBottom: "1.5rem",
            boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.04)",
          }}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="application/pdf"
            style={{ display: "none" }}
          />

          <div
            style={{
              width: "52px",
              height: "52px",
              margin: "0 auto 1.25rem",
              color: "var(--accent-primary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "var(--accent-light)",
              borderRadius: "10px",
              border: "1px solid #bfdbfe",
            }}
          >
            <FileUp size={26} />
          </div>

          <div>
            <h3
              style={{
                fontSize: "1.1875rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: "0.5rem",
              }}
            >
              Drag and drop your research paper PDF here
            </h3>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-muted)",
                marginBottom: "1.5rem",
              }}
            >
              Supports academic PDFs (IEEE, APA, arXiv, ACM, Nature, Springer, Elsevier) up to 30 MB
            </p>
            <button
              type="button"
              className="btn-primary"
              style={{ padding: "0.625rem 1.5rem", fontSize: "0.9375rem" }}
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              <Upload size={17} />
              <span>Choose PDF Document</span>
            </button>
          </div>
        </div>
      )}

      {/* Error Message if any */}
      {errorMessage && (
        <div
          style={{
            padding: "1rem 1.25rem",
            backgroundColor: "var(--status-unverified-bg)",
            border: "1px solid var(--status-unverified-border)",
            borderRadius: "8px",
            color: "var(--status-unverified-text)",
            display: "flex",
            alignItems: "flex-start",
            gap: "0.75rem",
            marginBottom: "2rem",
          }}
        >
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <strong style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem" }}>
              Processing Limitation or Error
            </strong>
            <span style={{ fontSize: "0.8125rem" }}>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Privacy Notice */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          padding: "0.875rem 1.125rem",
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "8px",
          marginBottom: "2.5rem",
        }}
      >
        <ShieldCheck size={20} style={{ color: "var(--accent-primary)", flexShrink: 0 }} />
        <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
          <strong>Deterministic Integrity Architecture:</strong> Files are stored locally on the
          host filesystem. Academic metadata is verified concurrently across 10 global authoritative
          registries (Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite,
          PubMed/MEDLINE, DOAJ, HAL). Retracted citations are actively flagged. Zero generative LLMs
          are used to fabricate or summarize facts.
        </span>
      </div>

      {/* Methodology 4-Step Architecture Cards */}
      <div>
        <h2
          style={{
            fontSize: "0.8125rem",
            fontWeight: 700,
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            marginBottom: "1rem",
            textAlign: "center",
          }}
        >
          Verification Pipeline Architecture
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
            gap: "1rem",
          }}
        >
          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <FileUp size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>
              1. Extract
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              PyMuPDF parses machine text, separates bibliography, and maps in-text citation markers.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <Search size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>
              2. Parallel Verify
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Concurrent lookups across 10 scholarly registries verify titles, authors, DOIs, and
              retractions.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <Cpu size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>
              3. Vector Compare
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Local Sentence-BERT embeddings and FAISS index rank candidate claim relevance and
              detect overclaims.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <BarChart3 size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>
              4. 3D Audit Dossier
            </h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Interactive 3D graph, hallucination detector, 1-click canonical citation repairs & PDF
              review export.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
