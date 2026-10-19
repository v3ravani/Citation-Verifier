const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";

export async function uploadPaperFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with HTTP ${response.status}`);
  }

  return response.json();
}

export async function analyzePaperById(paperId, rerun = false) {
  const url = `${API_BASE_URL}/api/analyze/${paperId}${rerun ? "?rerun=true" : ""}`;
  const response = await fetch(url, {
    method: "POST",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed with HTTP ${response.status}`);
  }

  return response.json();
}

export async function getPaperResult(paperId) {
  const response = await fetch(`${API_BASE_URL}/api/result/${paperId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch result (HTTP ${response.status})`);
  }
  return response.json();
}

export function getTxtExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/txt`;
}

export function getJsonExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/json`;
}

export async function fetchCacheStatus() {
  const response = await fetch(`${API_BASE_URL}/api/cache/status`);
  if (!response.ok) return null;
  return response.json();
}
