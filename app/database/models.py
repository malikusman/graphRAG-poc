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
from app.utils.math_utils import calculate_noisy_or_strength


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
            IndexModel([("doi", ASCENDING)], sparse=True),  # DOI index (not unique)
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
    async def get_documents(skip: int = 0, limit: int = 100) -> List[Document]:
        """Get documents with pagination"""
        collection = await DocumentCollection.get_collection()
        
        documents = []
        cursor = collection.find().skip(skip).limit(limit).sort("created_at", -1)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            documents.append(Document(**doc))
        return documents
    
    @staticmethod
    async def update_document_status(doc_id: str, status: DocumentStatus) -> bool:
        """Update document status"""
        collection = await DocumentCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_document_job_id(doc_id: str, job_id: str) -> bool:
        """Update document job_id"""
        collection = await DocumentCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"job_id": job_id, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def delete_document(doc_id: str) -> bool:
        """Delete document by ID"""
        collection = await DocumentCollection.get_collection()
        
        result = await collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count > 0


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
    
    @staticmethod
    async def find_similar_entities_by_name(entity_name: str, threshold: float = 0.8) -> List[EntityResponse]:
        """Find entities with similar names using text similarity"""
        collection = await EntityCollection.get_collection()
        
        # Use MongoDB text search for similar entity names
        # This is a simplified approach - in production, you might want to use embeddings
        query = {
            "$or": [
                {"entity_name": {"$regex": entity_name, "$options": "i"}},
                {"aliases": {"$regex": entity_name, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(query)
        entities = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entities.append(EntityResponse(**doc))
        
        return entities
    
    @staticmethod
    async def find_entities_by_type_and_category(entity_type: str, category: str) -> List[EntityResponse]:
        """Find entities by type and category"""
        collection = await EntityCollection.get_collection()
        
        query = {
            "entity_type": entity_type,
            "entity_category": category
        }
        
        cursor = collection.find(query)
        entities = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entities.append(EntityResponse(**doc))
        
        return entities
    
    @staticmethod
    async def merge_entities(source_id: str, target_id: str) -> bool:
        """Merge two entities, keeping the target and updating references"""
        collection = await EntityCollection.get_collection()
        
        try:
            # Get source and target entities
            source_entity = await collection.find_one({"_id": ObjectId(source_id)})
            target_entity = await collection.find_one({"_id": ObjectId(target_id)})
            
            if not source_entity or not target_entity:
                return False
            
            # Merge aliases
            merged_aliases = list(set(
                source_entity.get("aliases", []) + 
                target_entity.get("aliases", []) +
                [source_entity["entity_name"]]
            ))
            
            # Merge paper_ids and section_ids
            merged_paper_ids = list(set(
                source_entity.get("paper_ids", []) + 
                target_entity.get("paper_ids", [])
            ))
            merged_section_ids = list(set(
                source_entity.get("section_ids", []) + 
                target_entity.get("section_ids", [])
            ))
            
            # Update target entity with merged data
            await collection.update_one(
                {"_id": ObjectId(target_id)},
                {
                    "$set": {
                        "aliases": merged_aliases,
                        "paper_ids": merged_paper_ids,
                        "section_ids": merged_section_ids,
                        "frequency": len(merged_paper_ids),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update all relationships that reference the source entity
            from app.database.models import RelationshipCollection
            rel_collection = await RelationshipCollection.get_collection()
            
            # Update relationships where source_entity is the source
            await rel_collection.update_many(
                {"source_entity": source_entity["entity_name"]},
                {"$set": {"source_entity": target_entity["entity_name"]}}
            )
            
            # Update relationships where source_entity is the target
            await rel_collection.update_many(
                {"target_entity": source_entity["entity_name"]},
                {"$set": {"target_entity": target_entity["entity_name"]}}
            )
            
            # Delete the source entity
            await collection.delete_one({"_id": ObjectId(source_id)})
            
            return True
            
        except Exception as e:
            print(f"Error merging entities: {str(e)}")
            return False
    
    @staticmethod
    async def get_entity_frequency_stats(entity_name: str) -> Dict[str, Any]:
        """Get frequency statistics for an entity across documents"""
        collection = await EntityCollection.get_collection()
        
        entity = await collection.find_one({"entity_name": entity_name})
        if not entity:
            return {"entity_name": entity_name, "frequency": 0, "paper_count": 0, "section_count": 0}
        
        return {
            "entity_name": entity_name,
            "frequency": entity.get("frequency", 0),
            "paper_count": len(entity.get("paper_ids", [])),
            "section_count": len(entity.get("section_ids", [])),
            "aliases": entity.get("aliases", []),
            "entity_type": entity.get("entity_type"),
            "entity_category": entity.get("entity_category")
        }


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
    
    @staticmethod
    async def find_relationships_between_entities(source: str, target: str) -> List[RelationshipResponse]:
        """Find all relationships between two entities"""
        collection = await RelationshipCollection.get_collection()
        
        query = {
            "$or": [
                {"source_entity": source, "target_entity": target},
                {"source_entity": target, "target_entity": source}
            ]
        }
        
        cursor = collection.find(query)
        relationships = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            relationships.append(RelationshipResponse(**doc))
        
        return relationships
    
    @staticmethod
    async def find_conflicting_relationships(source: str, target: str) -> List[RelationshipResponse]:
        """Find potentially conflicting relationships between entities"""
        collection = await RelationshipCollection.get_collection()
        
        # Find relationships between the same entities with different types
        # that might be contradictory (e.g., "increases" vs "decreases")
        conflicting_types = [
            ("increases", "decreases"),
            ("activates", "inhibits"),
            ("supports", "contradicts"),
            ("causes", "prevents"),
            ("treats", "causes")
        ]
        
        relationships = []
        
        for type1, type2 in conflicting_types:
            # Find relationships with conflicting types
            query = {
                "$or": [
                    {"source_entity": source, "target_entity": target, "relationship_type": type1},
                    {"source_entity": source, "target_entity": target, "relationship_type": type2},
                    {"source_entity": target, "target_entity": source, "relationship_type": type1},
                    {"source_entity": target, "target_entity": source, "relationship_type": type2}
                ]
            }
            
            cursor = collection.find(query)
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                relationships.append(RelationshipResponse(**doc))
        
        return relationships
    
    @staticmethod
    async def consolidate_relationship_strength(relationship_id: str) -> float:
        """Calculate consolidated strength for a relationship using noisy-OR"""
        collection = await RelationshipCollection.get_collection()
        
        relationship = await collection.find_one({"_id": ObjectId(relationship_id)})
        if not relationship:
            return 0.0
        
        # Get all relationships with the same source, target, and type
        query = {
            "source_entity": relationship["source_entity"],
            "target_entity": relationship["target_entity"],
            "relationship_type": relationship["relationship_type"]
        }
        
        cursor = collection.find(query)
        strengths = []
        
        async for doc in cursor:
            strengths.append(doc.get("relationship_strength", 0.0))
        
        if not strengths:
            return 0.0
        
        # Calculate noisy-OR using centralized utility function
        return calculate_noisy_or_strength(strengths)
    
    @staticmethod
    async def get_relationship_evidence_count(relationship_id: str) -> int:
        """Get number of evidence sources for a relationship"""
        collection = await RelationshipCollection.get_collection()
        
        relationship = await collection.find_one({"_id": ObjectId(relationship_id)})
        if not relationship:
            return 0
        
        # Count unique paper_ids that support this relationship
        return len(relationship.get("paper_ids", []))
    
    @staticmethod
    async def update_relationship_strength(relationship_id: str, new_strength: float) -> bool:
        """Update relationship strength after consolidation"""
        collection = await RelationshipCollection.get_collection()
        
        result = await collection.update_one(
            {"_id": ObjectId(relationship_id)},
            {
                "$set": {
                    "relationship_strength": new_strength,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0


async def initialize_database():
    """Initialize database with collections and indexes"""
    print("🚀 Initializing database collections and indexes...")
    
    # Create indexes for all collections
    await DocumentCollection.create_indexes()
    await SectionCollection.create_indexes()
    await EntityCollection.create_indexes()
    await RelationshipCollection.create_indexes()
    
    print("✅ Database initialization complete!")
