from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UploadResponse(BaseModel):
    paper_id: str
    filename: str
    sha256: str
    pages: int
    status: str = "uploaded"
    message: str

class PaperMetadata(BaseModel):
    id: str
    filename: str
    sha256: str
    pages: int
    title_guess: Optional[str] = None
    upload_time: str

class ParsedReference(BaseModel):
    reference_id: int
    raw_text: str
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None

class VerificationResult(BaseModel):
    status: str = "unverified"  # verified_exact, verified_probable, metadata_mismatch, unverified, api_unavailable
    source: str = "none"        # crossref, semantic_scholar, crossref+semantic_scholar
    title_similarity: float = 0.0
    author_match: float = 0.0
    year_match: Optional[bool] = None
    doi_match: Optional[bool] = None
    verification_score: float = 0.0  # 0 to 100
    notes: List[str] = Field(default_factory=list)

class ExternalRecord(BaseModel):
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None
    url: Optional[str] = None
    is_retracted: bool = False
    sources_verified: List[str] = Field(default_factory=list)
    source: str = ""

class AlternativeReference(BaseModel):
    reference_id: int
    title: Optional[str] = None
    similarity: float

class CitationOccurrence(BaseModel):
    context_id: int
    reference_id: int
    marker: str
    page: Optional[int] = None
    sentence: str
    previous_sentence: str = ""
    next_sentence: str = ""
    full_context: str
    semantic_similarity: Optional[float] = None
    classification: str = "unavailable"  # strongly_related, moderately_related, weakly_related, likely_unrelated, unavailable
    rank_among_references: Optional[int] = None
    total_candidates: int = 0
    top_alternative_references: List[AlternativeReference] = Field(default_factory=list)
    overclaim_flag: bool = False
    overclaim_reason: Optional[str] = None
    claim_strength: str = "neutral"  # strong, moderate, neutral
    strong_claim_terms: List[str] = Field(default_factory=list)

class ReferenceItem(BaseModel):
    reference_id: int
    marker: str = ""
    raw_text: str
    parsed: ParsedReference
    verification: VerificationResult
    external: Optional[ExternalRecord] = None
    citation_occurrences: List[CitationOccurrence] = Field(default_factory=list)
    overall_score: Optional[float] = None  # None if semantic score is unavailable
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    review_flags: List[str] = Field(default_factory=list)
    is_retracted: bool = False
    hallucination_risk: str = "LOW"  # LOW, MODERATE, HIGH
    hallucination_reason: Optional[str] = None
    repaired_citation: Optional[str] = None
    is_peer_reviewed_indexed: bool = False
    indexing_sources: List[str] = Field(default_factory=list)

class AnalysisSummary(BaseModel):
    references_detected: int = 0
    verified_exact: int = 0
    verified_probable: int = 0
    metadata_mismatch: int = 0
    unverified: int = 0
    api_unavailable: int = 0
    citation_occurrences: int = 0
    strong_context_match: int = 0
    moderate_context_match: int = 0
    weak_context_match: int = 0
    likely_unrelated: int = 0
    context_unavailable: int = 0
    overclaim_flags: int = 0
    retracted_citations_count: int = 0
    hallucination_risk_count: int = 0
    peer_reviewed_count: int = 0
    average_integrity_score: float = 0.0
    sources_queried: List[str] = Field(default_factory=list)
    graph_nodes_count: int = 0
    graph_edges_count: int = 0

class CitationGraphNode(BaseModel):
    id: str
    label: str
    type: str  # paper, reference
    status: str
    score: Optional[float] = None
    title: Optional[str] = None

class CitationGraphEdge(BaseModel):
    source: str
    target: str
    weight: Optional[float] = None
    label: Optional[str] = None

class CitationGraph(BaseModel):
    nodes: List[CitationGraphNode] = Field(default_factory=list)
    edges: List[CitationGraphEdge] = Field(default_factory=list)

class AnalysisResult(BaseModel):
    paper: PaperMetadata
    summary: AnalysisSummary
    references: List[ReferenceItem]
    graph: CitationGraph
    methodology: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: str
