"""
MongoDB collection schemas and database operations
"""

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.models import (
    Document, DocumentResponse, DocumentStatus,
    Section, SectionResponse,
    Entity, EntityResponse, EntityType, EntityCategory,
    Relationship, RelationshipResponse, RelationshipType
)


class DocumentCollection:
    """MongoDB collection for documents"""
    
    @staticmethod
    async def get_collection() -> AsyncIOMotorCollection:
        """Get documents collection"""
        db = await get_database()
        return db.documents
    
    @staticmethod
    async def create_indexes():
        """Create indexes for documents collection"""
        collection = await DocumentCollection.get_collection()
        
        indexes = [
            IndexModel([("title", TEXT)]),  # Text search on title
            IndexModel([("doi", ASCENDING)], unique=True, sparse=True),  # Unique DOI
            IndexModel([("year", DESCENDING)]),  # Sort by year
            IndexModel([("status", ASCENDING)]),  # Filter by status
            IndexModel([("created_at", DESCENDING)]),  # Sort by creation time
        ]
        
        await collection.create_indexes(indexes)
        print("✅ Created indexes for documents collection")
    
    @staticmethod
    async def insert_document(document: Document) -> str:
        """Insert a new document"""
        collection = await DocumentCollection.get_collection()
        
        doc_dict = document.model_dump()
        doc_dict["created_at"] = datetime.utcnow()
        doc_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(doc_dict)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_document(doc_id: str) -> Optional[DocumentResponse]:
        """Get document by ID"""
        collection = await DocumentCollection.get_collection()
        
        doc = await collection.find_one({"_id": ObjectId(doc_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            return DocumentResponse(**doc)
        return None
    
    @staticmethod
    async def update_document_status(doc_id: str, status: DocumentStatus) -> bool:
        """Update document status"""
        collection = await DocumentCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0


class SectionCollection:
    """MongoDB collection for sections"""
    
    @staticmethod
    async def get_collection() -> AsyncIOMotorCollection:
        """Get sections collection"""
        db = await get_database()
        return db.sections
    
    @staticmethod
    async def create_indexes():
        """Create indexes for sections collection"""
        collection = await SectionCollection.get_collection()
        
        indexes = [
            IndexModel([("document_id", ASCENDING)]),  # Filter by document
            IndexModel([("title", ASCENDING)]),  # Filter by section type
            IndexModel([("text", TEXT)]),  # Text search on content
            IndexModel([("year", DESCENDING)]),  # Sort by year
            IndexModel([("created_at", DESCENDING)]),  # Sort by creation time
        ]
        
        await collection.create_indexes(indexes)
        print("✅ Created indexes for sections collection")
    
    @staticmethod
    async def insert_section(section: Section) -> str:
        """Insert a new section"""
        collection = await SectionCollection.get_collection()
        
        section_dict = section.model_dump()
        section_dict["created_at"] = datetime.utcnow()
        section_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(section_dict)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_sections_by_document(doc_id: str) -> List[SectionResponse]:
        """Get all sections for a document"""
        collection = await SectionCollection.get_collection()
        
        cursor = collection.find({"document_id": doc_id})
        sections = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            sections.append(SectionResponse(**doc))
        return sections
    
    @staticmethod
    async def update_section_embedding(section_id: str, embedding: List[float]) -> bool:
        """Update section embedding"""
        collection = await SectionCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(section_id)},
            {"$set": {"embedding": embedding, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0


class EntityCollection:
    """MongoDB collection for entities"""
    
    @staticmethod
    async def get_collection() -> AsyncIOMotorCollection:
        """Get entities collection"""
        db = await get_database()
        return db.entities
    
    @staticmethod
    async def create_indexes():
        """Create indexes for entities collection"""
        collection = await EntityCollection.get_collection()
        
        indexes = [
            IndexModel([("entity_name", TEXT)]),  # Text search on entity name
            IndexModel([("entity_type", ASCENDING)]),  # Filter by entity type
            IndexModel([("entity_category", ASCENDING)]),  # Filter by category
            IndexModel([("frequency", DESCENDING)]),  # Sort by frequency
            IndexModel([("paper_ids", ASCENDING)]),  # Filter by paper IDs
            IndexModel([("section_ids", ASCENDING)]),  # Filter by section IDs
            IndexModel([("created_at", DESCENDING)]),  # Sort by creation time
            # Compound index for entity name and type (for uniqueness)
            IndexModel([("entity_name", ASCENDING), ("entity_type", ASCENDING)]),
        ]
        
        await collection.create_indexes(indexes)
        print("✅ Created indexes for entities collection")
    
    @staticmethod
    async def insert_entity(entity: Entity) -> str:
        """Insert a new entity"""
        collection = await EntityCollection.get_collection()
        
        entity_dict = entity.model_dump()
        entity_dict["created_at"] = datetime.utcnow()
        entity_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(entity_dict)
        return str(result.inserted_id)
    
    @staticmethod
    async def find_entity_by_name_and_type(entity_name: str, entity_type: EntityType) -> Optional[EntityResponse]:
        """Find entity by name and type"""
        collection = await EntityCollection.get_collection()
        
        doc = await collection.find_one({
            "entity_name": entity_name,
            "entity_type": entity_type
        })
        if doc:
            doc["_id"] = str(doc["_id"])
            return EntityResponse(**doc)
        return None
    
    @staticmethod
    async def update_entity_frequency(entity_id: str, frequency: int) -> bool:
        """Update entity frequency"""
        collection = await EntityCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(entity_id)},
            {"$set": {"frequency": frequency, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def add_entity_provenance(entity_id: str, paper_id: str, section_id: str) -> bool:
        """Add provenance information to entity"""
        collection = await EntityCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(entity_id)},
            {
                "$addToSet": {
                    "paper_ids": paper_id,
                    "section_ids": section_id
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0


class RelationshipCollection:
    """MongoDB collection for relationships"""
    
    @staticmethod
    async def get_collection() -> AsyncIOMotorCollection:
        """Get relationships collection"""
        db = await get_database()
        return db.relationships
    
    @staticmethod
    async def create_indexes():
        """Create indexes for relationships collection"""
        collection = await RelationshipCollection.get_collection()
        
        indexes = [
            IndexModel([("source_entity", ASCENDING)]),  # Filter by source entity
            IndexModel([("target_entity", ASCENDING)]),  # Filter by target entity
            IndexModel([("relationship_type", ASCENDING)]),  # Filter by relationship type
            IndexModel([("relationship_strength", DESCENDING)]),  # Sort by strength
            IndexModel([("paper_ids", ASCENDING)]),  # Filter by paper IDs
            IndexModel([("section_ids", ASCENDING)]),  # Filter by section IDs
            IndexModel([("created_at", DESCENDING)]),  # Sort by creation time
            # Compound index for relationship lookup
            IndexModel([("source_entity", ASCENDING), ("target_entity", ASCENDING)]),
        ]
        
        await collection.create_indexes(indexes)
        print("✅ Created indexes for relationships collection")
    
    @staticmethod
    async def insert_relationship(relationship: Relationship) -> str:
        """Insert a new relationship"""
        collection = await RelationshipCollection.get_collection()
        
        relationship_dict = relationship.model_dump()
        relationship_dict["created_at"] = datetime.utcnow()
        relationship_dict["updated_at"] = datetime.utcnow()
        
        result = await collection.insert_one(relationship_dict)
        return str(result.inserted_id)
    
    @staticmethod
    async def get_relationships_by_entity(entity_name: str) -> List[RelationshipResponse]:
        """Get all relationships for an entity"""
        collection = await RelationshipCollection.get_collection()
        
        cursor = collection.find({
            "$or": [
                {"source_entity": entity_name},
                {"target_entity": entity_name}
            ]
        })
        relationships = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            relationships.append(RelationshipResponse(**doc))
        return relationships
    
    @staticmethod
    async def get_relationships_by_type(relationship_type: RelationshipType) -> List[RelationshipResponse]:
        """Get relationships by type"""
        collection = await RelationshipCollection.get_collection()
        
        cursor = collection.find({"relationship_type": relationship_type})
        relationships = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            relationships.append(RelationshipResponse(**doc))
        return relationships


async def initialize_database():
    """Initialize database with collections and indexes"""
    print("🚀 Initializing database collections and indexes...")
    
    # Create indexes for all collections
    await DocumentCollection.create_indexes()
    await SectionCollection.create_indexes()
    await EntityCollection.create_indexes()
    await RelationshipCollection.create_indexes()
    
    print("✅ Database initialization complete!")
