"""
Relationship models for entity connections
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RelationshipType(str, Enum):
    """Relationship types between entities"""
    USES = "uses"
    EVALUATED_BY = "evaluated_by"
    ASSOCIATED_WITH = "associated_with"  
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    CAUSES = "causes"
    TREATS = "treats"
    MEASURES = "measures"
    CONTAINS = "contains"
    INTERACTS_WITH = "interacts_with"
    REGULATES = "regulates"
    INHIBITS = "inhibits"
    ACTIVATES = "activates"
    BINDS_TO = "binds_to"
    EXPRESSES = "expresses"
    MUTATES = "mutates"
    OVEREXPRESSES = "overexpresses"
    KNOCKDOWN = "knockdown"
    KNOCKOUT = "knockout"
    UPREGULATES = "upregulates"
    DOWNREGULATES = "downregulates"
    INCREASES = "increases"
    DECREASES = "decreases"
    ENHANCES = "enhances"
    SUPPRESSES = "suppresses"
    PREVENTS = "prevents"
    PROMOTES = "promotes"
    INDUCES = "induces"
    TARGETS = "targets"
    CULTURED_IN = "cultured_in"
    SUPPLEMENTED_WITH = "supplemented_with"
    DERIVED_FROM = "derived_from"
    ENCODED_BY = "encoded_by"


class Relationship(BaseModel):
    """Relationship model matching requirements JSON schema"""
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    relationship_strength: float = Field(..., ge=0.0, le=1.0, description="Relationship strength")
    description: Optional[str] = Field(None, max_length=1000, description="Relationship description")
    section_ids: List[str] = Field(default_factory=list, description="Section IDs where relationship was found")
    paper_ids: List[str] = Field(default_factory=list, description="Document IDs where relationship was found")
    
    @field_validator('source_entity', 'target_entity')
    @classmethod
    def validate_entity_names(cls, v):
        """Validate entity names"""
        if not v or not v.strip():
            raise ValueError('Entity name cannot be empty')
        return v.strip()
    
    @field_validator('target_entity')
    @classmethod
    def validate_different_entities(cls, v, info):
        """Validate that source and target entities are different"""
        if 'source_entity' in info.data and v == info.data['source_entity']:
            raise ValueError('Source and target entities must be different')
        return v
    
    @field_validator('section_ids', 'paper_ids')
    @classmethod
    def validate_ids(cls, v):
        """Validate ID lists"""
        if v is not None:
            # Remove empty strings
            v = [id_val.strip() for id_val in v if id_val.strip()]
        return v


class RelationshipResponse(Relationship):
    """Relationship response model with additional fields"""
    id: str = Field(..., alias="_id", description="Relationship ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )