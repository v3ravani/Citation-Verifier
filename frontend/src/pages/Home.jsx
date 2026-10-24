import React, { useState, useRef, useEffect } from "react";
import UploadPanel from "../components/UploadPanel";
import { uploadPaperFile, analyzePaperById, getAnalysisProgress } from "../api/client";

export default function Home({ onAnalysisComplete }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressData, setProgressData] = useState({
    percent: 0,
    stage: "Preparing upload...",
    details: "",
    completed_refs: 0,
    total_refs: 0,
    status: "pending",
  });
  const [errorMessage, setErrorMessage] = useState(null);
  const pollingRef = useRef(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  const handleUpload = async (file) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setProgressData({
      percent: 4,
      stage: "Uploading PDF to local server...",
      details: file.name,
      completed_refs: 0,
      total_refs: 0,
      status: "processing",
    });

    try {
      // Step 1: Upload PDF
      const uploadRes = await uploadPaperFile(file);
      const paperId = uploadRes.paper_id;

      setProgressData((prev) => ({
        ...prev,
        percent: 8,
        stage: `Uploaded "${uploadRes.filename}" (${uploadRes.pages} pages). Initializing pipeline...`,
      }));

      // Step 2: Start real-time progress polling (every 250ms)
      pollingRef.current = setInterval(async () => {
        const prog = await getAnalysisProgress(paperId);
        if (prog) {
          setProgressData((prev) => ({
            ...prev,
            percent: Math.max(prev.percent, prog.percent || 0),
            stage: prog.stage || prev.stage,
            details: prog.details || prev.details,
            completed_refs: prog.completed_refs || prev.completed_refs,
            total_refs: prog.total_refs || prev.total_refs,
            status: prog.status || prev.status,
          }));
        }
      }, 250);

      // Step 3: Trigger complete verification pipeline
      const result = await analyzePaperById(paperId);

      // Stop poller and complete
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }

      setProgressData({
        percent: 100,
        stage: "Verification complete! Rendering comprehensive audit report...",
        details: `${result.references?.length || 0} references verified across 10 scholarly registries.`,
        completed_refs: result.references?.length || 0,
        total_refs: result.references?.length || 0,
        status: "completed",
      });

      // Brief delay so user sees 100% completion animation
      setTimeout(() => {
        setIsProcessing(false);
        onAnalysisComplete(result);
      }, 450);
    } catch (err) {
      console.error("Pipeline failure:", err);
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      setIsProcessing(false);
      setErrorMessage(err.message || "An unexpected error occurred during processing.");
    }
  };

  return (
    <div style={{ padding: "1rem 0" }}>
      <UploadPanel
        onUploadSuccess={handleUpload}
        isProcessing={isProcessing}
        progressData={progressData}
        errorMessage={errorMessage}
      />
    </div>
  );
}
