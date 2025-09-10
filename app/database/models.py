"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class EntityType(str, Enum):
    """Entity types"""
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
    OTHER = "other"


class EntityCategory(str, Enum):
    """Entity categories"""
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
    OTHER = "other"


class RelationshipType(str, Enum):
    """Relationship types"""
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
    OTHER = "other"


# Document Models
class DocumentBase(BaseModel):
    """Base document model"""
    title: str
    doi: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation model"""
    pass


class DocumentUpdate(BaseModel):
    """Document update model"""
    title: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    abstract: Optional[str] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(DocumentBase):
    """Document response model"""
    id: str = Field(alias="_id")
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    
    class Config:
        populate_by_name = True


# Section Models
class SectionBase(BaseModel):
    """Base section model"""
    document_id: str
    section_type: str
    content: str
    order: int


class SectionCreate(SectionBase):
    """Section creation model"""
    pass


class SectionResponse(SectionBase):
    """Section response model"""
    id: str = Field(alias="_id")
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


# Entity Models
class EntityBase(BaseModel):
    """Base entity model"""
    name: str
    entity_type: EntityType
    category: EntityCategory
    description: Optional[str] = None
    aliases: List[str] = []
    frequency: int = 1


class EntityCreate(EntityBase):
    """Entity creation model"""
    pass


class EntityUpdate(BaseModel):
    """Entity update model"""
    name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    category: Optional[EntityCategory] = None
    description: Optional[str] = None
    aliases: Optional[List[str]] = None
    frequency: Optional[int] = None


class EntityResponse(EntityBase):
    """Entity response model"""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    provenance: List[Dict[str, Any]] = []
    
    class Config:
        populate_by_name = True


# Relationship Models
class RelationshipBase(BaseModel):
    """Base relationship model"""
    source_entity: str
    target_entity: str
    relationship_type: RelationshipType
    strength: float = Field(ge=0.0, le=1.0)
    description: Optional[str] = None


class RelationshipCreate(RelationshipBase):
    """Relationship creation model"""
    pass


class RelationshipUpdate(BaseModel):
    """Relationship update model"""
    relationship_type: Optional[RelationshipType] = None
    strength: Optional[float] = Field(None, ge=0.0, le=1.0)
    description: Optional[str] = None


class RelationshipResponse(RelationshipBase):
    """Relationship response model"""
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    provenance: List[Dict[str, Any]] = []
    
    class Config:
        populate_by_name = True


# Query Models
class GraphPath(BaseModel):
    """Graph path model"""
    path: List[str]
    entities: List[EntityResponse]
    relationships: List[RelationshipResponse]
    total_strength: float


class QuerySource(BaseModel):
    """Query source model"""
    document_id: str
    document_title: str
    section_id: str
    section_type: str
    content: str
    relevance_score: float
    doi: Optional[str] = None

