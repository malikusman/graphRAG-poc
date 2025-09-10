"""
Relationship models for entity connections
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RelationshipType(str, Enum):
    """Relationship types between entities"""
    USES = "uses"
    EVALUATED_BY = "evaluated_by"
    ASSOCIATED_WITH = "associated_with"
    IMPROVES = "improves"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CAUSES = "causes"
    TREATS = "treats"
    INTERACTS_WITH = "interacts_with"
    PART_OF = "part_of"
    CONTAINS = "contains"
    DERIVED_FROM = "derived_from"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CO_OCCURS_WITH = "co_occurs_with"
    OTHER = "other"


class RelationshipDirection(str, Enum):
    """Relationship direction"""
    DIRECTED = "directed"  # A -> B
    UNDIRECTED = "undirected"  # A <-> B


class RelationshipBase(BaseModel):
    """Base relationship model"""
    source_entity_id: str = Field(..., description="ID of source entity")
    target_entity_id: str = Field(..., description="ID of target entity")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    direction: RelationshipDirection = Field(default=RelationshipDirection.DIRECTED, description="Relationship direction")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Relationship strength")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in relationship")
    description: Optional[str] = Field(None, max_length=1000, description="Relationship description")
    context: Optional[str] = Field(None, max_length=2000, description="Context where relationship was found")
    
    @field_validator('source_entity_id', 'target_entity_id')
    @classmethod
    def validate_entity_ids(cls, v):
        """Validate entity IDs"""
        if not v or not v.strip():
            raise ValueError('Entity ID cannot be empty')
        return v.strip()
    
    @field_validator('target_entity_id')
    @classmethod
    def validate_different_entities(cls, v, info):
        """Validate that source and target entities are different"""
        if 'source_entity_id' in info.data and v == info.data['source_entity_id']:
            raise ValueError('Source and target entities must be different')
        return v


class RelationshipCreate(RelationshipBase):
    """Relationship creation model"""
    pass


class RelationshipUpdate(BaseModel):
    """Relationship update model"""
    relationship_type: Optional[RelationshipType] = None
    direction: Optional[RelationshipDirection] = None
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    description: Optional[str] = Field(None, max_length=1000)
    context: Optional[str] = Field(None, max_length=2000)


class RelationshipResponse(RelationshipBase):
    """Relationship response model with additional fields"""
    id: str = Field(..., alias="_id", description="Relationship ID")
    source_entity_name: Optional[str] = Field(None, description="Name of source entity")
    target_entity_name: Optional[str] = Field(None, description="Name of target entity")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    provenance: List[Dict[str, Any]] = Field(default_factory=list, description="Source information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class RelationshipListResponse(BaseModel):
    """Response model for relationship listing"""
    relationships: List[RelationshipResponse] = Field(..., description="List of relationships")
    total: int = Field(..., description="Total number of relationships")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of relationships per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class RelationshipStats(BaseModel):
    """Relationship statistics model"""
    total_relationships: int = Field(..., description="Total number of relationships")
    relationships_by_type: Dict[str, int] = Field(..., description="Count of relationships by type")
    relationships_by_direction: Dict[str, int] = Field(..., description="Count of relationships by direction")
    average_strength: float = Field(..., description="Average relationship strength")
    average_confidence: float = Field(..., description="Average confidence score")
    most_common_relationships: List[Dict[str, Any]] = Field(..., description="Most common relationship types")
    bidirectional_relationships: int = Field(..., description="Number of bidirectional relationships")


class RelationshipSearchRequest(BaseModel):
    """Request model for relationship search"""
    source_entity_id: Optional[str] = Field(None, description="Filter by source entity ID")
    target_entity_id: Optional[str] = Field(None, description="Filter by target entity ID")
    relationship_types: Optional[List[RelationshipType]] = Field(None, description="Filter by relationship types")
    min_strength: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum strength")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")
    direction: Optional[RelationshipDirection] = Field(None, description="Filter by direction")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")


class RelationshipSearchResult(BaseModel):
    """Search result model for relationships"""
    relationship: RelationshipResponse = Field(..., description="Relationship information")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    path_length: Optional[int] = Field(None, description="Path length in graph traversal")


class RelationshipPath(BaseModel):
    """Path model for graph traversal"""
    path: List[str] = Field(..., description="List of entity IDs in path")
    relationships: List[RelationshipResponse] = Field(..., description="Relationships in path")
    total_strength: float = Field(..., ge=0.0, le=1.0, description="Combined strength of path")
    total_confidence: float = Field(..., ge=0.0, le=1.0, description="Combined confidence of path")
    path_length: int = Field(..., ge=1, description="Length of path")


class RelationshipConsolidationRequest(BaseModel):
    """Request model for relationship consolidation"""
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    consolidation_method: str = Field(default="noisy_or", description="Method for consolidation")
    min_evidence_count: int = Field(default=1, ge=1, description="Minimum evidence count")


class RelationshipContradictionRequest(BaseModel):
    """Request model for handling relationship contradictions"""
    relationship_id: str = Field(..., description="ID of relationship with contradiction")
    contradiction_type: str = Field(..., description="Type of contradiction")
    resolution_method: str = Field(..., description="Method to resolve contradiction")
    evidence: List[Dict[str, Any]] = Field(..., description="Evidence for contradiction")
    resolution: Optional[str] = Field(None, max_length=1000, description="Resolution description")
