"""
Entity models for extracted entities from documents
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntityType(str, Enum):
    """Fine-grained entity types"""
    METHOD = "method"
    DATASET = "dataset" 
    ORGANISM = "organism"
    GENE = "gene"
    PROTEIN = "protein"
    MOLECULE = "molecule"
    GENETIC_VARIANT = "genetic_variant"
    DISEASE = "disease"
    PHYSIOLOGICAL_PROCESS = "physiological_process"
    ALGORITHM = "algorithm"
    MODEL = "model"
    FRAMEWORK = "framework"
    INSTRUMENT = "instrument"
    SOFTWARE = "software"
    SAMPLE = "sample"
    POPULATION = "population"
    LOCATION = "location"
    ECOSYSTEM = "ecosystem"
    EVENT = "event"
    PHENOMENON = "phenomenon"
    RESULT = "result"
    FINDING = "finding"
    OBSERVATION = "observation"
    METRIC = "metric"
    MEASUREMENT = "measurement"
    INDEX = "index"
    STATISTICAL_PARAMETER = "statistical_parameter"
    AUTHOR = "author"
    INSTITUTION = "institution"
    FUNDING_BODY = "funding_body"
    CONCEPT = "concept"
    HYPOTHESIS = "hypothesis"
    LIMITATION = "limitation"
    POLICY_DOC = "policy_doc"
    REGULATION = "regulation"
    ETHICAL_PRINCIPLE = "ethical_principle"
    TIMEPOINT = "timepoint"
    PERIOD = "period"
    SEASON = "season"
    OTHER = "other"


class EntityCategory(str, Enum):
    """11 general entity categories from requirements"""
    METHODS_AND_APPROACHES = "methods_and_approaches"
    DATA_AND_MATERIALS = "data_and_materials" 
    SUBJECTS_OF_STUDY = "subjects_of_study"
    EVENTS_AND_PHENOMENA = "events_and_phenomena"
    CONDITIONS_AND_STATES = "conditions_and_states"
    RESULTS_AND_FINDINGS = "results_and_findings"
    MEASUREMENTS_AND_INDICATORS = "measurements_and_indicators"
    PEOPLE_AND_ORGANIZATIONS = "people_and_organizations"
    CONCEPTS_AND_IDEAS = "concepts_and_ideas"
    POLICIES_AND_RULES = "policies_and_rules"
    TIME_AND_PLACE = "time_and_place"
    BIOLOGICAL_ENTITIES = "biological_entities"
    TECHNOLOGIES_AND_TOOLS = "technologies_and_tools"
    MEASUREMENTS_AND_METRICS = "measurements_and_metrics"
    DISEASES_AND_DISORDERS = "diseases_and_disorders"
    PHYSIOLOGICAL_PROCESSES = "physiological_processes"
    CHEMICAL_ENTITIES = "chemical_entities"
    OTHER_CONCEPTS = "other_concepts"


class Entity(BaseModel):
    """Entity model matching requirements JSON schema"""
    entity_name: str = Field(..., min_length=1, max_length=200, description="Canonical entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    entity_category: EntityCategory = Field(..., description="Category of entity")
    entity_description: Optional[str] = Field(None, max_length=2000, description="Entity description")
    aliases: List[str] = Field(default_factory=list, description="Alternative names for entity")
    paper_ids: List[str] = Field(default_factory=list, description="Document IDs where entity appears")
    section_ids: List[str] = Field(default_factory=list, description="Section IDs where entity appears")
    frequency: int = Field(default=1, ge=1, description="Frequency of entity across documents")
    
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
    
    @field_validator('entity_name')
    @classmethod
    def validate_entity_name(cls, v):
        """Validate entity name"""
        if not v.strip():
            raise ValueError('Entity name cannot be empty')
        return v.strip()
    
    @field_validator('paper_ids', 'section_ids')
    @classmethod
    def validate_ids(cls, v):
        """Validate ID lists"""
        if v is not None:
            # Remove empty strings
            v = [id_val.strip() for id_val in v if id_val.strip()]
        return v


class EntityResponse(Entity):
    """Entity response model with additional fields"""
    id: str = Field(..., alias="_id", description="Entity ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )