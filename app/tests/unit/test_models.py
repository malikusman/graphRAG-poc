"""
Unit tests for models
"""

import pytest
from datetime import datetime
from app.models import (
    DocumentCreate, DocumentResponse, DocumentStatus, DocumentType,
    SectionCreate, SectionResponse, SectionType,
    EntityCreate, EntityResponse, EntityType, EntityCategory,
    RelationshipCreate, RelationshipResponse, RelationshipType, RelationshipDirection
)


class TestDocumentModels:
    """Test document models"""
    
    def test_document_create_valid(self):
        """Test valid document creation"""
        doc = DocumentCreate(
            title="Test Document",
            doi="10.1000/test",
            year=2023,
            abstract="This is a test abstract",
            authors=["John Doe", "Jane Smith"],
            journal="Test Journal",
            keywords=["test", "document"],
            language="en",
            file_path="/path/to/file.pdf",
            file_size=1024,
            file_type=DocumentType.PDF
        )
        
        assert doc.title == "Test Document"
        assert doc.doi == "10.1000/test"
        assert doc.year == 2023
        assert len(doc.authors) == 2
        assert doc.file_type == DocumentType.PDF
    
    def test_document_create_invalid_doi(self):
        """Test invalid DOI format"""
        with pytest.raises(ValueError, match="DOI must start with"):
            DocumentCreate(
                title="Test Document",
                doi="invalid-doi"
            )
    
    def test_document_create_invalid_file_size(self):
        """Test invalid file size"""
        with pytest.raises(ValueError, match="File size too large"):
            DocumentCreate(
                title="Test Document",
                file_size=100 * 1024 * 1024  # 100MB
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
    
    def test_section_create_valid(self):
        """Test valid section creation"""
        section = SectionCreate(
            document_id="doc-123",
            section_type=SectionType.ABSTRACT,
            title="Abstract",
            content="This is the abstract content",
            order=1,
            page_number=1
        )
        
        assert section.document_id == "doc-123"
        assert section.section_type == SectionType.ABSTRACT
        assert section.content == "This is the abstract content"
        assert section.word_count == 5  # Auto-calculated
        assert section.char_count == 28  # Auto-calculated
    
    def test_section_create_empty_content(self):
        """Test section with empty content"""
        with pytest.raises(ValueError, match="Section content cannot be empty"):
            SectionCreate(
                document_id="doc-123",
                section_type=SectionType.ABSTRACT,
                content="   "  # Empty after strip
            )
    
    def test_section_response(self):
        """Test section response model"""
        now = datetime.utcnow()
        section = SectionResponse(
            _id="section-123",
            document_id="doc-123",
            section_type=SectionType.METHODS,
            content="Methods content",
            order=2,
            created_at=now,
            updated_at=now
        )
        
        assert section.id == "section-123"
        assert section.section_type == SectionType.METHODS


class TestEntityModels:
    """Test entity models"""
    
    def test_entity_create_valid(self):
        """Test valid entity creation"""
        entity = EntityCreate(
            name="CRISPR-Cas9",
            entity_type=EntityType.METHOD,
            category=EntityCategory.METHODS_AND_APPROACHES,
            description="Gene editing technique",
            aliases=["CRISPR", "Cas9"],
            frequency=5,
            confidence=0.95
        )
        
        assert entity.name == "CRISPR-Cas9"
        assert entity.entity_type == EntityType.METHOD
        assert entity.category == EntityCategory.METHODS_AND_APPROACHES
        assert len(entity.aliases) == 2
        assert entity.confidence == 0.95
    
    def test_entity_create_empty_name(self):
        """Test entity with empty name"""
        with pytest.raises(ValueError, match="Entity name cannot be empty"):
            EntityCreate(
                name="   ",
                entity_type=EntityType.METHOD,
                category=EntityCategory.METHODS_AND_APPROACHES
            )
    
    def test_entity_create_too_many_aliases(self):
        """Test entity with too many aliases"""
        aliases = [f"alias_{i}" for i in range(25)]
        with pytest.raises(ValueError, match="Too many aliases"):
            EntityCreate(
                name="Test Entity",
                entity_type=EntityType.METHOD,
                category=EntityCategory.METHODS_AND_APPROACHES,
                aliases=aliases
            )
    
    def test_entity_response(self):
        """Test entity response model"""
        now = datetime.utcnow()
        entity = EntityResponse(
            _id="entity-123",
            name="Test Entity",
            entity_type=EntityType.DATASET,
            category=EntityCategory.DATA_AND_MATERIALS,
            created_at=now,
            updated_at=now
        )
        
        assert entity.id == "entity-123"
        assert entity.entity_type == EntityType.DATASET


class TestRelationshipModels:
    """Test relationship models"""
    
    def test_relationship_create_valid(self):
        """Test valid relationship creation"""
        rel = RelationshipCreate(
            source_entity_id="entity-1",
            target_entity_id="entity-2",
            relationship_type=RelationshipType.USES,
            direction=RelationshipDirection.DIRECTED,
            strength=0.8,
            confidence=0.9,
            description="Entity 1 uses Entity 2"
        )
        
        assert rel.source_entity_id == "entity-1"
        assert rel.target_entity_id == "entity-2"
        assert rel.relationship_type == RelationshipType.USES
        assert rel.strength == 0.8
        assert rel.confidence == 0.9
    
    def test_relationship_create_same_entities(self):
        """Test relationship with same source and target entities"""
        with pytest.raises(ValueError, match="Source and target entities must be different"):
            RelationshipCreate(
                source_entity_id="entity-1",
                target_entity_id="entity-1",  # Same as source
                relationship_type=RelationshipType.USES
            )
    
    def test_relationship_create_invalid_strength(self):
        """Test relationship with invalid strength"""
        with pytest.raises(ValueError):
            RelationshipCreate(
                source_entity_id="entity-1",
                target_entity_id="entity-2",
                relationship_type=RelationshipType.USES,
                strength=1.5  # Invalid: > 1.0
            )
    
    def test_relationship_response(self):
        """Test relationship response model"""
        now = datetime.utcnow()
        rel = RelationshipResponse(
            _id="rel-123",
            source_entity_id="entity-1",
            target_entity_id="entity-2",
            relationship_type=RelationshipType.IMPROVES,
            created_at=now,
            updated_at=now
        )
        
        assert rel.id == "rel-123"
        assert rel.relationship_type == RelationshipType.IMPROVES


if __name__ == "__main__":
    pytest.main([__file__])
