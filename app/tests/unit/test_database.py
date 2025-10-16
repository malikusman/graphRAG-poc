"""
Unit tests for database operations
"""

import pytest
from datetime import datetime
from app.database.models import (
    DocumentCollection, SectionCollection, EntityCollection, RelationshipCollection
)
from app.models import (
    Document, DocumentStatus,
    Section,
    Entity, EntityType, EntityCategory,
    Relationship, RelationshipType
)


class TestDocumentCollection:
    """Test document collection operations"""
    
    @pytest.mark.asyncio
    async def test_insert_document(self):
        """Test inserting a document"""
        document = Document(
            title="Test Document",
            doi="10.1000/test",
            year=2023,
            status=DocumentStatus.PROCESSED
        )
        
        doc_id = await DocumentCollection.insert_document(document)
        assert doc_id is not None
        assert len(doc_id) == 24  # MongoDB ObjectId length
    
    @pytest.mark.asyncio
    async def test_get_document(self):
        """Test getting a document by ID"""
        document = Document(
            title="Test Document",
            status=DocumentStatus.PROCESSED
        )
        
        doc_id = await DocumentCollection.insert_document(document)
        retrieved_doc = await DocumentCollection.get_document(doc_id)
        
        assert retrieved_doc is not None
        assert retrieved_doc.title == "Test Document"
        assert retrieved_doc.status == DocumentStatus.PROCESSED
    
    @pytest.mark.asyncio
    async def test_update_document_status(self):
        """Test updating document status"""
        document = Document(
            title="Test Document",
            status=DocumentStatus.UPLOADED
        )
        
        doc_id = await DocumentCollection.insert_document(document)
        success = await DocumentCollection.update_document_status(doc_id, DocumentStatus.PROCESSED)
        
        assert success is True
        
        updated_doc = await DocumentCollection.get_document(doc_id)
        assert updated_doc.status == DocumentStatus.PROCESSED


class TestSectionCollection:
    """Test section collection operations"""
    
    @pytest.mark.asyncio
    async def test_insert_section(self):
        """Test inserting a section"""
        section = Section(
            document_id="doc-123",
            title="abstract",
            text="This is the abstract content",
            year=2023
        )
        
        section_id = await SectionCollection.insert_section(section)
        assert section_id is not None
        assert len(section_id) == 24  # MongoDB ObjectId length
    
    @pytest.mark.asyncio
    async def test_get_sections_by_document(self):
        """Test getting sections by document ID"""
        section = Section(
            document_id="doc-123",
            title="abstract",
            text="This is the abstract content"
        )
        
        section_id = await SectionCollection.insert_section(section)
        sections = await SectionCollection.get_sections_by_document("doc-123")
        
        assert len(sections) >= 1
        assert sections[0].title == "abstract"
        assert sections[0].text == "This is the abstract content"
    
    @pytest.mark.asyncio
    async def test_update_section_embedding(self):
        """Test updating section embedding"""
        section = Section(
            document_id="doc-123",
            title="abstract",
            text="This is the abstract content"
        )
        
        section_id = await SectionCollection.insert_section(section)
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        success = await SectionCollection.update_section_embedding(section_id, embedding)
        assert success is True


class TestEntityCollection:
    """Test entity collection operations"""
    
    @pytest.mark.asyncio
    async def test_insert_entity(self):
        """Test inserting an entity"""
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
        
        entity_id = await EntityCollection.insert_entity(entity)
        assert entity_id is not None
        assert len(entity_id) == 24  # MongoDB ObjectId length
    
    @pytest.mark.asyncio
    async def test_find_entity_by_name_and_type(self):
        """Test finding entity by name and type"""
        entity = Entity(
            entity_name="CRISPR-Cas9",
            entity_type=EntityType.METHOD,
            entity_category=EntityCategory.METHODS_AND_APPROACHES
        )
        
        entity_id = await EntityCollection.insert_entity(entity)
        found_entity = await EntityCollection.find_entity_by_name_and_type(
            "CRISPR-Cas9", EntityType.METHOD
        )
        
        assert found_entity is not None
        assert found_entity.entity_name == "CRISPR-Cas9"
        assert found_entity.entity_type == EntityType.METHOD
    
    @pytest.mark.asyncio
    async def test_update_entity_frequency(self):
        """Test updating entity frequency"""
        entity = Entity(
            entity_name="Test Entity",
            entity_type=EntityType.METHOD,
            entity_category=EntityCategory.METHODS_AND_APPROACHES,
            frequency=1
        )
        
        entity_id = await EntityCollection.insert_entity(entity)
        success = await EntityCollection.update_entity_frequency(entity_id, 5)
        
        assert success is True


class TestRelationshipCollection:
    """Test relationship collection operations"""
    
    @pytest.mark.asyncio
    async def test_insert_relationship(self):
        """Test inserting a relationship"""
        relationship = Relationship(
            source_entity="CRISPR-Cas9",
            target_entity="Gene editing",
            relationship_type=RelationshipType.USES,
            relationship_strength=0.8,
            description="CRISPR-Cas9 uses gene editing",
            section_ids=["sec-78"],
            paper_ids=["doc-456"]
        )
        
        rel_id = await RelationshipCollection.insert_relationship(relationship)
        assert rel_id is not None
        assert len(rel_id) == 24  # MongoDB ObjectId length
    
    @pytest.mark.asyncio
    async def test_get_relationships_by_entity(self):
        """Test getting relationships by entity"""
        relationship = Relationship(
            source_entity="CRISPR-Cas9",
            target_entity="Gene editing",
            relationship_type=RelationshipType.USES,
            relationship_strength=0.8
        )
        
        rel_id = await RelationshipCollection.insert_relationship(relationship)
        relationships = await RelationshipCollection.get_relationships_by_entity("CRISPR-Cas9")
        
        assert len(relationships) >= 1
        assert relationships[0].source_entity == "CRISPR-Cas9"
        assert relationships[0].target_entity == "Gene editing"
    
    @pytest.mark.asyncio
    async def test_get_relationships_by_type(self):
        """Test getting relationships by type"""
        relationship = Relationship(
            source_entity="Entity A",
            target_entity="Entity B",
            relationship_type=RelationshipType.ASSOCIATED_WITH,
            relationship_strength=0.7
        )
        
        rel_id = await RelationshipCollection.insert_relationship(relationship)
        relationships = await RelationshipCollection.get_relationships_by_type(RelationshipType.ASSOCIATED_WITH)
        
        assert len(relationships) >= 1
        assert relationships[0].relationship_type == RelationshipType.ASSOCIATED_WITH


if __name__ == "__main__":
    pytest.main([__file__])
