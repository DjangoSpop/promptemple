"""
Pydantic contracts for research agent data structures.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CitationModel(BaseModel):
    """Citation data structure for research answers."""
    n: int = Field(..., description="Citation number")
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    score: float = Field(default=0.0, description="Relevance score", ge=0.0, le=1.0)
    domain: Optional[str] = Field(None, description="Source domain")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class InsightCard(BaseModel):
    """Evidence-bounded insight card structure."""
    id: str = Field(..., description="Unique card identifier")
    title: str = Field(..., description="Card title", max_length=200)
    content: str = Field(..., description="Card content in markdown", max_length=2000)
    citations: List[CitationModel] = Field(default_factory=list, description="Supporting citations")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    authority: float = Field(..., description="Authority score", ge=0.0, le=1.0)
    domain_cluster: Optional[str] = Field(None, description="Domain cluster this card belongs to")
    tags: List[str] = Field(default_factory=list, description="Semantic tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('citations')
    def validate_citations(cls, v):
        if not v:
            raise ValueError('Card must have at least one citation')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Card content must be at least 50 characters')
        return v
    
    def passes_quality_guards(self, min_authority: float = 0.6, min_confidence: float = 0.5) -> bool:
        """Check if card passes quality guards."""
        return (
            len(self.citations) > 0 and
            self.authority >= min_authority and
            self.confidence >= min_confidence
        )


class SearchResult(BaseModel):
    """Search result structure."""
    url: str = Field(..., description="Result URL")
    title: str = Field(..., description="Result title")
    content: Optional[str] = Field(None, description="Content snippet")
    score: float = Field(default=0.0, description="Search relevance score")
    domain: Optional[str] = Field(None, description="Source domain")


class DomainCluster(BaseModel):
    """Domain-based content cluster."""
    domain: str = Field(..., description="Primary domain")
    urls: List[str] = Field(default_factory=list, description="URLs in cluster")
    total_content: str = Field(..., description="Combined content from all URLs")
    authority_score: float = Field(default=0.0, description="Domain authority score")
    

class ResearchContext(BaseModel):
    """Context for research synthesis."""
    query: str = Field(..., description="Original research query")
    search_results: List[SearchResult] = Field(default_factory=list)
    domain_clusters: List[DomainCluster] = Field(default_factory=list)
    total_sources: int = Field(default=0, description="Total number of sources")


class StreamEventType(str, Enum):
    """SSE event types for streaming."""
    PLANNING = "planning"
    SEARCHING = "searching"
    CLUSTERING = "clustering" 
    FETCHING = "fetching"
    SYNTHESIS = "synthesis"
    CARD = "card"
    UPDATE = "update"
    END = "end"
    ERROR = "error"


class StreamEvent(BaseModel):
    """SSE stream event structure."""
    event: StreamEventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    def to_sse_format(self) -> str:
        """Convert to SSE format string."""
        import json
        return f"event: {self.event.value}\ndata: {json.dumps(self.data, default=str, ensure_ascii=False)}\n\n"


class QualityMetrics(BaseModel):
    """Quality metrics for research content."""
    authority_score: float = Field(..., ge=0.0, le=1.0, description="Source authority")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Content confidence")
    citation_count: int = Field(..., ge=0, description="Number of citations")
    content_length: int = Field(..., ge=0, description="Content length in characters")
    domain_diversity: float = Field(default=0.0, ge=0.0, le=1.0, description="Domain diversity score")
    freshness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Content freshness")


class ResearchPlan(BaseModel):
    """Research execution plan."""
    query: str = Field(..., description="Research query")
    search_terms: List[str] = Field(default_factory=list, description="Derived search terms")
    expected_cards: int = Field(default=3, description="Expected number of cards", ge=1, le=10)
    max_sources: int = Field(default=10, description="Maximum sources to process", ge=5, le=20)
    focus_domains: List[str] = Field(default_factory=list, description="Preferred domains")
    quality_threshold: float = Field(default=0.6, description="Quality threshold", ge=0.0, le=1.0)


class SynthesisResult(BaseModel):
    """Result of synthesis process."""
    cards: List[InsightCard] = Field(default_factory=list, description="Generated cards")
    quality_metrics: QualityMetrics = Field(..., description="Overall quality metrics")
    rejected_cards: int = Field(default=0, description="Number of rejected cards")
    processing_time_ms: int = Field(default=0, description="Processing time in milliseconds")
    sources_used: int = Field(default=0, description="Number of sources used")