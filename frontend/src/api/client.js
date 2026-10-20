// Use relative URL so Vite proxy forwards requests to backend with zero CORS issues
const API_BASE_URL = import.meta.env.VITE_API_URL || "";

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

export function getAnnotatedPdfExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/annotated-pdf`;
}

export function getBibtexExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/bibtex`;
}

export function getCsvExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/csv`;
}

export function getMarkdownExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/markdown`;
}

export function getHtmlExportUrl(paperId) {
  return `${API_BASE_URL}/api/report/${paperId}/html`;
}

export async function suggestCitations(text, maxClaims = 3, maxPerClaim = 5) {
  const response = await fetch(`${API_BASE_URL}/api/suggest-citations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      text,
      max_claims: maxClaims,
      max_per_claim: maxPerClaim,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Citation suggestion failed (HTTP ${response.status})`);
  }

  return response.json();
}

export async function detectCitationGaps(paperId, text = null, maxGaps = 5) {
  const response = await fetch(`${API_BASE_URL}/api/detect-citation-gaps`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      paper_id: paperId,
      text: text,
      max_gaps: maxGaps,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Citation gap detection failed (HTTP ${response.status})`);
  }

  return response.json();
}

export async function fetchCacheStatus() {
  const response = await fetch(`${API_BASE_URL}/api/cache/status`);
  if (!response.ok) return null;
  return response.json();
}

export async function searchLiterature(query, filterMode = "general", limit = 8) {
  const response = await fetch(`${API_BASE_URL}/api/search-references`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      filter_mode: filterMode,
      limit,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Literature search failed (HTTP ${response.status})`);
  }

  return response.json();
}

