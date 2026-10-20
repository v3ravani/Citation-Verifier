import React, { useState, useRef } from "react";
import { Upload, FileUp, AlertCircle, ShieldCheck, CheckCircle2, Search, Cpu, BarChart3 } from "lucide-react";

export default function UploadPanel({ onUploadSuccess, isProcessing, processingStatus, errorMessage }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

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

  return (
    <div style={{ maxWidth: "860px", margin: "0 auto" }}>
      {/* Hero Intro */}
      <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.75rem", letterSpacing: "-0.02em" }}>
          Verify citations beyond the bibliography.
        </h1>
        <p style={{ fontSize: "1.0625rem", color: "var(--text-secondary)", maxWidth: "680px", margin: "0 auto", lineHeight: 1.6 }}>
          Inspect whether references exist, compare extracted metadata across 7 global scholarly registries (Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite), and verify whether cited sources are semantically relevant to the claims they support.
        </p>
      </div>

      {/* Upload Box */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragOver ? "var(--accent-primary)" : "var(--border-strong)"}`,
          borderRadius: "8px",
          padding: "3rem 2rem",
          textAlign: "center",
          backgroundColor: isDragOver ? "var(--accent-light)" : "var(--bg-primary)",
          transition: "all 0.15s ease",
          marginBottom: "1.5rem"
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="application/pdf"
          style={{ display: "none" }}
        />

        <div style={{ width: "48px", height: "48px", margin: "0 auto 1rem", color: "var(--accent-primary)", display: "flex", alignItems: "center", justifyContent: "center", backgroundColor: "var(--bg-secondary)", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
          <FileUp size={24} />
        </div>

        {isProcessing ? (
          <div>
            <div style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
              {processingStatus || "Processing document..."}
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", maxWidth: "450px", margin: "0 auto" }}>
              Extracting text, querying 7 global scholarly registries, verifying retractions, and computing local sentence embeddings...
            </p>
          </div>
        ) : (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
              Drag and drop your research paper PDF here
            </h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
              Supports machine-readable academic PDFs (IEEE, APA, arXiv, ACM, Nature, Springer) up to 30 MB
            </p>
            <button
              type="button"
              className="btn-primary"
              onClick={() => fileInputRef.current && fileInputRef.current.click()}
            >
              <Upload size={16} />
              <span>Choose PDF Document</span>
            </button>
          </div>
        )}
      </div>

      {/* Error Message if any */}
      {errorMessage && (
        <div style={{ padding: "1rem 1.25rem", backgroundColor: "var(--status-unverified-bg)", border: "1px solid var(--status-unverified-border)", borderRadius: "6px", color: "var(--status-unverified-text)", display: "flex", alignItems: "flex-start", gap: "0.75rem", marginBottom: "2rem" }}>
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <strong style={{ display: "block", marginBottom: "0.25rem", fontSize: "0.875rem" }}>Processing Limitation or Error</strong>
            <span style={{ fontSize: "0.8125rem" }}>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Privacy Notice */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.875rem 1rem", backgroundColor: "var(--bg-secondary)", border: "1px solid var(--border-subtle)", borderRadius: "6px", marginBottom: "2.5rem" }}>
        <ShieldCheck size={18} style={{ color: "var(--accent-primary)", flexShrink: 0 }} />
        <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
          <strong>Privacy & Architecture:</strong> Files are stored locally on the host filesystem. Academic metadata is queried directly from 7 authoritative registries (Crossref, Semantic Scholar, OpenAlex, arXiv, Europe PMC, DBLP, DataCite). Retracted works are automatically checked. No external generative AI or LLM API is used.
        </span>
      </div>

      {/* Methodology 4-Step Cards */}
      <div>
        <h2 style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "1rem", textAlign: "center" }}>
          Verification Pipeline Architecture
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: "1rem" }}>
          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <FileUp size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>1. Extract</h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              PyMuPDF parses machine text, separates bibliography, and maps in-text citation markers.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <Search size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>2. Verify</h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Multi-source lookups across Crossref, Semantic Scholar, OpenAlex & arXiv verify titles, authors, and DOIs.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <Cpu size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>3. Compare</h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Local Sentence-BERT models encode contexts; FAISS vector index ranks candidate relevance.
            </p>
          </div>

          <div className="academic-card" style={{ padding: "1.25rem" }}>
            <div style={{ color: "var(--accent-primary)", marginBottom: "0.5rem" }}>
              <BarChart3 size={20} />
            </div>
            <h4 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem" }}>4. Audit</h4>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.45 }}>
              Explainable verification scoring, citation alignment, and heuristic overclaim detection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
