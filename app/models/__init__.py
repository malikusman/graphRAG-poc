"""
Models package for GraphRAG system
"""

# Document models
from .documents import (
    DocumentStatus,
    DocumentType,
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentStats,
)

# Section models
from .sections import (
    SectionType,
    SectionBase,
    SectionCreate,
    SectionUpdate,
    SectionResponse,
    SectionListResponse,
    SectionStats,
    SectionSearchRequest,
    SectionSearchResult,
)

# Entity models
from .entities import (
    EntityType,
    EntityCategory,
    EntityBase,
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityListResponse,
    EntityStats,
    EntitySearchRequest,
    EntitySearchResult,
    EntityMergeRequest,
    EntityCanonicalizationRequest,
)

# Relationship models
from .relationships import (
    RelationshipType,
    RelationshipDirection,
    RelationshipBase,
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipResponse,
    RelationshipListResponse,
    RelationshipStats,
    RelationshipSearchRequest,
    RelationshipSearchResult,
    RelationshipPath,
    RelationshipConsolidationRequest,
    RelationshipContradictionRequest,
)

__all__ = [
    # Document models
    "DocumentStatus",
    "DocumentType",
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentStats",
    
    # Section models
    "SectionType",
    "SectionBase",
    "SectionCreate",
    "SectionUpdate",
    "SectionResponse",
    "SectionListResponse",
    "SectionStats",
    "SectionSearchRequest",
    "SectionSearchResult",
    
    # Entity models
    "EntityType",
    "EntityCategory",
    "EntityBase",
    "EntityCreate",
    "EntityUpdate",
    "EntityResponse",
    "EntityListResponse",
    "EntityStats",
    "EntitySearchRequest",
    "EntitySearchResult",
    "EntityMergeRequest",
    "EntityCanonicalizationRequest",
    
    # Relationship models
    "RelationshipType",
    "RelationshipDirection",
    "RelationshipBase",
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    "RelationshipListResponse",
    "RelationshipStats",
    "RelationshipSearchRequest",
    "RelationshipSearchResult",
    "RelationshipPath",
    "RelationshipConsolidationRequest",
    "RelationshipContradictionRequest",
]
