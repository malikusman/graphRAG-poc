"""
Unit tests for models
"""

import pytest
from datetime import datetime
from app.models import (
    Document, DocumentResponse, DocumentStatus,
    Section, SectionResponse,
    Entity, EntityResponse, EntityType, EntityCategory,
    Relationship, RelationshipResponse, RelationshipType
)


class TestDocumentModels:
    """Test document models"""
    
    def test_document_valid(self):
        """Test valid document creation"""
        doc = Document(
            title="Test Document",
            doi="10.1000/test",
            year=2023,
            status=DocumentStatus.PROCESSED
        )
        
        assert doc.title == "Test Document"
        assert doc.doi == "10.1000/test"
        assert doc.year == 2023
        assert doc.status == DocumentStatus.PROCESSED
    
    def test_document_invalid_doi(self):
        """Test invalid DOI format"""
        with pytest.raises(ValueError, match="DOI must start with"):
            Document(
                title="Test Document",
                doi="invalid-doi",
                status=DocumentStatus.PROCESSED
            )
    
    def test_document_response(self):
        """Test document response model"""
        now = datetime.utcnow()
        doc = DocumentResponse(
            _id="test-id",
            title="Test Document",
            status=DocumentStatus.PROCESSED,
            created_at=now,
            updated_at=now
        )
        
        assert doc.id == "test-id"
        assert doc.status == DocumentStatus.PROCESSED
        assert doc.created_at == now


class TestSectionModels:
    """Test section models"""
    
    def test_section_valid(self):
        """Test valid section creation"""
        section = Section(
            document_id="doc-123",
            title="abstract",
            text="This is the abstract content",
            year=2023
        )
        
        assert section.document_id == "doc-123"
        assert section.title == "abstract"
        assert section.text == "This is the abstract content"
        assert section.year == 2023
    
    def test_section_empty_text(self):
        """Test section with empty text"""
        with pytest.raises(ValueError, match="Section text cannot be empty"):
            Section(
                document_id="doc-123",
                title="abstract",
                text="   "  # Empty after strip
            )
    
    def test_section_response(self):
        """Test section response model"""
        now = datetime.utcnow()
        section = SectionResponse(
            _id="section-123",
            document_id="doc-123",
            title="methods",
            text="Methods content",
            created_at=now,
            updated_at=now
        )
        
        assert section.id == "section-123"
        assert section.title == "methods"


class TestEntityModels:
    """Test entity models"""
    
    def test_entity_valid(self):
        """Test valid entity creation"""
        entity = Entity(
            entity_name="CRISPR-Cas9",
            entity_type=EntityType.METHOD,
            entity_category=EntityCategory.METHODS_AND_APPROACHES,
            entity_description="Gene editing technique",
            aliases=["CRISPR", "Cas9"],
            paper_ids=["doc-123"],
            section_ids=["sec-45"],
            frequency=5
        )
        
        assert entity.entity_name == "CRISPR-Cas9"
        assert entity.entity_type == EntityType.METHOD
        assert entity.entity_category == EntityCategory.METHODS_AND_APPROACHES
        assert len(entity.aliases) == 2
        assert len(entity.paper_ids) == 1
        assert len(entity.section_ids) == 1
    
    def test_entity_empty_name(self):
        """Test entity with empty name"""
        with pytest.raises(ValueError, match="Entity name cannot be empty"):
            Entity(
                entity_name="   ",
                entity_type=EntityType.METHOD,
                entity_category=EntityCategory.METHODS_AND_APPROACHES
            )
    
    def test_entity_too_many_aliases(self):
        """Test entity with too many aliases"""
        aliases = [f"alias_{i}" for i in range(25)]
        with pytest.raises(ValueError, match="Too many aliases"):
            Entity(
                entity_name="Test Entity",
                entity_type=EntityType.METHOD,
                entity_category=EntityCategory.METHODS_AND_APPROACHES,
                aliases=aliases
            )
    
    def test_entity_response(self):
        """Test entity response model"""
        now = datetime.utcnow()
        entity = EntityResponse(
            _id="entity-123",
            entity_name="Test Entity",
            entity_type=EntityType.DATASET,
            entity_category=EntityCategory.DATA_AND_MATERIALS,
            created_at=now,
            updated_at=now
        )
        
        assert entity.id == "entity-123"
        assert entity.entity_type == EntityType.DATASET


class TestRelationshipModels:
    """Test relationship models"""
    
    def test_relationship_valid(self):
        """Test valid relationship creation"""
        rel = Relationship(
            source_entity="CRISPR-Cas9",
            target_entity="Gene editing",
            relationship_type=RelationshipType.USES,
            relationship_strength=0.8,
            description="CRISPR-Cas9 uses gene editing",
            section_ids=["sec-78"],
            paper_ids=["doc-456"]
        )
        
        assert rel.source_entity == "CRISPR-Cas9"
        assert rel.target_entity == "Gene editing"
        assert rel.relationship_type == RelationshipType.USES
        assert rel.relationship_strength == 0.8
        assert len(rel.section_ids) == 1
        assert len(rel.paper_ids) == 1
    
    def test_relationship_same_entities(self):
        """Test relationship with same source and target entities"""
        with pytest.raises(ValueError, match="Source and target entities must be different"):
            Relationship(
                source_entity="Entity-1",
                target_entity="Entity-1",  # Same as source
                relationship_type=RelationshipType.USES,
                relationship_strength=0.5
            )
    
    def test_relationship_invalid_strength(self):
        """Test relationship with invalid strength"""
        with pytest.raises(ValueError):
            Relationship(
                source_entity="Entity-1",
                target_entity="Entity-2",
                relationship_type=RelationshipType.USES,
                relationship_strength=1.5  # Invalid: > 1.0
            )
    
    def test_relationship_response(self):
        """Test relationship response model"""
        now = datetime.utcnow()
        rel = RelationshipResponse(
            _id="rel-123",
            source_entity="Entity-1",
            target_entity="Entity-2",
            relationship_type=RelationshipType.ASSOCIATED_WITH,
            relationship_strength=0.7,
            created_at=now,
            updated_at=now
        )
        
        assert rel.id == "rel-123"
        assert rel.relationship_type == RelationshipType.ASSOCIATED_WITH


if __name__ == "__main__":
    pytest.main([__file__])