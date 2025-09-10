"""
Entity models for extracted entities from documents
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Entity types for scientific documents"""
    METHOD = "method"
    DATASET = "dataset"
    ORGANISM = "organism"
    METRIC = "metric"
    GENE = "gene"
    PROTEIN = "protein"
    DISEASE = "disease"
    DRUG = "drug"
    TECHNIQUE = "technique"
    TOOL = "tool"
    SOFTWARE = "software"
    ALGORITHM = "algorithm"
    MODEL = "model"
    CONCEPT = "concept"
    LOCATION = "location"
    PERSON = "person"
    ORGANIZATION = "organization"
    OTHER = "other"


class EntityCategory(str, Enum):
    """Entity categories for organization"""
    METHODS_AND_APPROACHES = "methods_and_approaches"
    DATA_AND_MATERIALS = "data_and_materials"
    BIOLOGICAL_ENTITIES = "biological_entities"
    MEASUREMENTS_AND_METRICS = "measurements_and_metrics"
    DISEASES_AND_CONDITIONS = "diseases_and_conditions"
    DRUGS_AND_COMPOUNDS = "drugs_and_compounds"
    TECHNIQUES_AND_TOOLS = "techniques_and_tools"
    CONCEPTS_AND_THEORIES = "concepts_and_theories"
    LOCATIONS_AND_ENVIRONMENTS = "locations_and_environments"
    TEMPORAL_CONCEPTS = "temporal_concepts"
    PEOPLE_AND_ORGANIZATIONS = "people_and_organizations"
    OTHER = "other"


class EntityBase(BaseModel):
    """Base entity model"""
    name: str = Field(..., min_length=1, max_length=200, description="Canonical entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    category: EntityCategory = Field(..., description="Category of entity")
    description: Optional[str] = Field(None, max_length=2000, description="Entity description")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for entity")
    frequency: int = Field(default=1, ge=1, description="Frequency of entity across documents")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score for entity")
    
    @field_validator('aliases')
    @classmethod
    def validate_aliases(cls, v):
        """Validate aliases list"""
        if v is not None:
            # Remove empty strings and duplicates
            v = list(set([alias.strip() for alias in v if alias.strip()]))
            if len(v) > 20:  # Reasonable limit
                raise ValueError('Too many aliases (max 20)')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate entity name"""
        if not v.strip():
            raise ValueError('Entity name cannot be empty')
        return v.strip()


class EntityCreate(EntityBase):
    """Entity creation model"""
    pass


class EntityUpdate(BaseModel):
    """Entity update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    entity_type: Optional[EntityType] = None
    category: Optional[EntityCategory] = None
    description: Optional[str] = Field(None, max_length=2000)
    aliases: Optional[List[str]] = None
    frequency: Optional[int] = Field(None, ge=1)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('aliases')
    @classmethod
    def validate_aliases(cls, v):
        """Validate aliases list"""
        if v is not None:
            v = list(set([alias.strip() for alias in v if alias.strip()]))
            if len(v) > 20:
                raise ValueError('Too many aliases (max 20)')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate entity name"""
        if v is not None and not v.strip():
            raise ValueError('Entity name cannot be empty')
        return v.strip() if v else v


class EntityResponse(EntityBase):
    """Entity response model with additional fields"""
    id: str = Field(..., alias="_id", description="Entity ID")
    canonical_id: Optional[str] = Field(None, description="Canonical ID (e.g., MeSH, HGNC)")
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


class EntityListResponse(BaseModel):
    """Response model for entity listing"""
    entities: List[EntityResponse] = Field(..., description="List of entities")
    total: int = Field(..., description="Total number of entities")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of entities per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class EntityStats(BaseModel):
    """Entity statistics model"""
    total_entities: int = Field(..., description="Total number of entities")
    entities_by_type: Dict[str, int] = Field(..., description="Count of entities by type")
    entities_by_category: Dict[str, int] = Field(..., description="Count of entities by category")
    average_frequency: float = Field(..., description="Average frequency across entities")
    average_confidence: float = Field(..., description="Average confidence score")
    most_frequent_entities: List[Dict[str, Any]] = Field(..., description="Most frequent entities")
    entities_with_canonical_ids: int = Field(..., description="Number of entities with canonical IDs")


class EntitySearchRequest(BaseModel):
    """Request model for entity search"""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    entity_types: Optional[List[EntityType]] = Field(None, description="Filter by entity types")
    categories: Optional[List[EntityCategory]] = Field(None, description="Filter by categories")
    min_frequency: Optional[int] = Field(None, ge=1, description="Minimum frequency")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    include_aliases: bool = Field(default=True, description="Whether to search in aliases")


class EntitySearchResult(BaseModel):
    """Search result model for entities"""
    entity: EntityResponse = Field(..., description="Entity information")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match score")
    matched_field: str = Field(..., description="Field that matched (name, alias, description)")
    matched_text: str = Field(..., description="Text that matched the query")


class EntityMergeRequest(BaseModel):
    """Request model for merging entities"""
    source_entity_id: str = Field(..., description="ID of entity to merge from")
    target_entity_id: str = Field(..., description="ID of entity to merge into")
    merge_aliases: bool = Field(default=True, description="Whether to merge aliases")
    merge_descriptions: bool = Field(default=True, description="Whether to merge descriptions")
    merge_metadata: bool = Field(default=True, description="Whether to merge metadata")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for merge")


class EntityCanonicalizationRequest(BaseModel):
    """Request model for entity canonicalization"""
    entity_id: str = Field(..., description="ID of entity to canonicalize")
    canonical_id: str = Field(..., description="Canonical ID to assign")
    canonical_source: str = Field(..., description="Source of canonical ID (e.g., MeSH, HGNC)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in canonicalization")
