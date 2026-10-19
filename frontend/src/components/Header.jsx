import React from "react";
import { BookOpen, FileText, Info } from "lucide-react";

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
          <span className="brand-badge">Research Integrity v1.0</span>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-btn ${activeView === "home" ? "active" : ""}`}
            onClick={() => onNavigate("home")}
          >
            <FileText size={16} />
            <span>Upload Document</span>
          </button>

          <button className="nav-btn" onClick={onOpenMethodology}>
            <Info size={16} />
            <span>Methodology</span>
          </button>

          <a
            href="https://github.com/v3ravani/Citation-Verifier"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-btn"
            style={{ textDecoration: "none" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
            </svg>
            <span>GitHub</span>
          </a>
        </nav>
      </div>
    </header>
  );
}
