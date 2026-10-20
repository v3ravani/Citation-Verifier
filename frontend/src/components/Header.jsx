import React from "react";
import { BookOpen, FileText, Info, ShieldCheck, Sparkles } from "lucide-react";

export default function Header({ onNavigate, activeView, onOpenMethodology }) {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="brand-section" onClick={() => onNavigate("home")}>
          <div className="brand-icon">
            <BookOpen size={18} />
          </div>
          <div>
            <span className="brand-title">Citation Verifier</span>
          </div>
          <span className="brand-badge">Institutional Edition</span>
          <span style={{ fontSize: "0.7rem", backgroundColor: "#ecfdf5", color: "#065f46", border: "1px solid #a7f3d0", padding: "0.15rem 0.5rem", borderRadius: "12px", display: "inline-flex", alignItems: "center", gap: "0.3rem", fontWeight: 600 }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#10b981", display: "inline-block" }} />
            7 Indices Active
          </span>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-btn ${activeView === "home" ? "active" : ""}`}
            onClick={() => onNavigate("home")}
          >
            <FileText size={15} />
            <span>Document Audit</span>
          </button>

          <button
            className={`nav-btn ${activeView === "suggester" ? "active" : ""}`}
            onClick={() => onNavigate("suggester")}
          >
            <Sparkles size={15} />
            <span>Citation Suggester</span>
          </button>

          <button className="nav-btn" onClick={onOpenMethodology}>
            <Info size={15} />
            <span>Methodology</span>
          </button>

          <a
            href="https://github.com/v3ravani/Citation-Verifier"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-btn"
            style={{ textDecoration: "none" }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
            </svg>
            <span>GitHub</span>
          </a>
        </nav>
      </div>
    </header>
  );
}
