"""
Query-related models for GraphRAG system
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QuerySource(BaseModel):
    """Source information for a query result"""
    document_id: str = Field(..., description="Document ID")
    document_title: str = Field(..., description="Document title")
    section_id: str = Field(..., description="Section ID")
    section_type: str = Field(..., description="Section type (abstract, methods, etc.)")
    content: str = Field(..., description="Content text from the section")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    doi: Optional[str] = Field(None, description="Document DOI")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GraphPath(BaseModel):
    """Graph path connecting entities through relationships"""
    path: List[str] = Field(..., description="List of entity names in the path")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entity details")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="Relationship details")
    total_strength: float = Field(..., ge=0.0, le=1.0, description="Total path strength")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional path metadata")


class QueryResponse(BaseModel):
    """Complete query response"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[QuerySource] = Field(..., description="Source documents/sections")
    graph_paths: List[GraphPath] = Field(default_factory=list, description="Graph traversal paths")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Response confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


# For API compatibility, also provide dict-based versions
class QueryResponseDict(BaseModel):
    """Query response using dict format for API compatibility"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents/sections")
    graph_paths: List[Dict[str, Any]] = Field(default_factory=list, description="Graph traversal paths")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Response confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")
