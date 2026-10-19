import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import Home from "./pages/Home";
import Analysis from "./pages/Analysis";
import MethodologyModal from "./components/MethodologyModal";
import { getPaperResult } from "./api/client";

export default function App() {
  const [currentView, setCurrentView] = useState("home");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isMethodologyOpen, setIsMethodologyOpen] = useState(false);

  // Check URL params for paper_id on initial mount (e.g., ?paper_id=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paperId = params.get("paper_id");
    if (paperId) {
      getPaperResult(paperId)
        .then((res) => {
          setAnalysisResult(res);
          setCurrentView("analysis");
        })
        .catch((err) => {
          console.warn("Could not load paper from URL param:", err);
        });
    }
  }, []);

  const handleAnalysisComplete = (result) => {
    setAnalysisResult(result);
    setCurrentView("analysis");
    // Update URL query param without reload
    if (result && result.paper && result.paper.id) {
      const url = new URL(window.location);
      url.searchParams.set("paper_id", result.paper.id);
      window.history.pushState({}, "", url);
    }
  };

  const handleBackToUpload = () => {
    setCurrentView("home");
    const url = new URL(window.location);
    url.searchParams.delete("paper_id");
    window.history.pushState({}, "", url);
  };

  return (
    <div className="app-container">
      <Header
        activeView={currentView}
        onNavigate={(view) => {
          if (view === "home") handleBackToUpload();
        }}
        onOpenMethodology={() => setIsMethodologyOpen(true)}
      />

      <main className="main-content">
        {currentView === "home" ? (
          <Home onAnalysisComplete={handleAnalysisComplete} />
        ) : (
          <Analysis
            result={analysisResult}
            onBack={handleBackToUpload}
            onUpdateResult={(updated) => setAnalysisResult(updated)}
          />
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <div>
            <strong>Citation Verifier</strong> — Deterministic Research Integrity & Semantic Citation Verification
          </div>
          <div>
            Powered by PyMuPDF, Crossref, Semantic Scholar, Sentence-BERT & FAISS
          </div>
        </div>
      </footer>

      <MethodologyModal
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
      />
    </div>
  );
}
