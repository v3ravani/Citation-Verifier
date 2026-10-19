import React, { useState } from "react";
import UploadPanel from "../components/UploadPanel";
import { uploadPaperFile, analyzePaperById } from "../api/client";

export default function Home({ onAnalysisComplete }) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState("");
  const [errorMessage, setErrorMessage] = useState(null);

  const handleUpload = async (file) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setProcessingStatus("Uploading document to local server...");

    try {
      // Step 1: Upload
      const uploadRes = await uploadPaperFile(file);
      setProcessingStatus(`Uploaded "${uploadRes.filename}" (${uploadRes.pages} pages). Initiating verification pipeline...`);

      // Step 2: Trigger Analysis
      const result = await analyzePaperById(uploadRes.paper_id);
      setIsProcessing(false);
      onAnalysisComplete(result);
    } catch (err) {
      console.error("Pipeline failure:", err);
      setIsProcessing(false);
      setErrorMessage(err.message || "An unexpected error occurred during processing.");
    }
  };

  return (
    <div style={{ padding: "1rem 0" }}>
      <UploadPanel
        onUploadSuccess={handleUpload}
        isProcessing={isProcessing}
        processingStatus={processingStatus}
        errorMessage={errorMessage}
      />
    </div>
  );
}
