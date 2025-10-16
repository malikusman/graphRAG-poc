import logging
import asyncio
from typing import Dict, Any
from celery import current_task
from bson import ObjectId

from app.tasks.celery_app import celery_app
from app.core.database import get_sync_database
from app.database.models import DocumentCollection, EntityCollection, RelationshipCollection
from app.models import DocumentStatus
from app.services.global_graph_manager import GlobalGraphManager
from app.models.entities import Entity
from app.models.relationships import Relationship

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def update_global_graph(self, document_id: str):
    """
    Update global graph with new document's entities and relationships
    
    Args:
        document_id: Document ID to process
        
    Returns:
        Dict with update results
    """
    try:
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting global graph update..."}
        )
        
        # Get database connection
        db = get_sync_database()
        
        # Get document
        document = db.documents.find_one({"_id": ObjectId(document_id)})
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        logger.info(f"Updating global graph for document {document_id}")
        
        # Step 1: Get document's final entities and relationships (20%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Loading document entities and relationships..."}
        )
        
        # Get entities from the document
        entities_cursor = db.entities.find({"paper_ids": document_id})
        entities = list(entities_cursor)
        
        # Get relationships from the document
        relationships_cursor = db.relationships.find({"paper_ids": document_id})
        relationships = list(relationships_cursor)
        
        logger.info(f"Found {len(entities)} entities and {len(relationships)} relationships for document {document_id}")
        
        # Step 2: Convert to Entity and Relationship objects (40%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Converting to model objects..."}
        )
        
        entity_objects = []
        for entity_data in entities:
            entity = Entity(
                entity_name=entity_data["entity_name"],
                entity_type=entity_data["entity_type"],
                entity_category=entity_data["entity_category"],
                aliases=entity_data.get("aliases", []),
                entity_description=entity_data["entity_description"],
                frequency=entity_data.get("frequency", 1),
                paper_ids=entity_data.get("paper_ids", []),
                section_ids=entity_data.get("section_ids", [])
            )
            entity_objects.append(entity)
        
        relationship_objects = []
        for rel_data in relationships:
            relationship = Relationship(
                source_entity=rel_data["source_entity"],
                target_entity=rel_data["target_entity"],
                relationship_type=rel_data["relationship_type"],
                relationship_strength=rel_data["relationship_strength"],
                description=rel_data["description"],
                paper_ids=rel_data.get("paper_ids", []),
                section_ids=rel_data.get("section_ids", [])
            )
            relationship_objects.append(relationship)
        
        # Step 3: Update global graph (80%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Updating global graph..."}
        )
        
        # Initialize global graph manager
        global_graph_manager = GlobalGraphManager()
        
        # Process entities and relationships
        processing_results = asyncio.run(
            global_graph_manager.process_document_entities_and_relationships(
                document_id, entity_objects, relationship_objects
            )
        )
        
        # Step 4: Finalization (100%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Global graph update complete!"}
        )
        
        result = {
            "current": 100,
            "total": 100,
            "status": "Global graph updated successfully!",
            "result": {
                "document_id": document_id,
                "entities_processed": processing_results["entities_processed"],
                "relationships_processed": processing_results["relationships_processed"],
                "entity_update_results": processing_results["entity_update_results"],
                "relationship_update_results": processing_results["relationship_update_results"],
                "errors": processing_results["errors"]
            }
        }
        
        logger.info(f"Successfully updated global graph for document {document_id}")
        return result
        
    except Exception as e:
        error_msg = f"Error updating global graph for document {document_id}: {str(e)}"
        logger.error(error_msg)
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": error_msg}
        )
        
        return {
            "current": 0,
            "total": 100,
            "status": error_msg,
            "result": {
                "document_id": document_id,
                "error": str(e)
            }
        }


@celery_app.task(bind=True)
def check_graph_consistency(self):
    """
    Periodic task to check and maintain graph consistency
    
    Returns:
        Dict with consistency check results
    """
    try:
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting graph consistency check..."}
        )
        
        # Get database connection
        db = get_sync_database()
        
        logger.info("Starting graph consistency check...")
        
        # Step 1: Check for orphaned entities (25%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 25, "total": 100, "status": "Checking for orphaned entities..."}
        )
        
        # Find entities with no relationships
        orphaned_entities = []
        entities_cursor = db.entities.find({})
        for entity in entities_cursor:
            # Check if entity has any relationships
            relationships_count = db.relationships.count_documents({
                "$or": [
                    {"source_entity": entity["entity_name"]},
                    {"target_entity": entity["entity_name"]}
                ]
            })
            
            if relationships_count == 0:
                orphaned_entities.append(entity["entity_name"])
        
        # Step 2: Check for duplicate relationships (50%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Checking for duplicate relationships..."}
        )
        
        # Find duplicate relationships
        duplicate_relationships = []
        relationships_cursor = db.relationships.find({})
        relationship_groups = {}
        
        for rel in relationships_cursor:
            key = f"{rel['source_entity']}_{rel['target_entity']}_{rel['relationship_type']}"
            if key not in relationship_groups:
                relationship_groups[key] = []
            relationship_groups[key].append(rel)
        
        for key, rels in relationship_groups.items():
            if len(rels) > 1:
                duplicate_relationships.append({
                    "key": key,
                    "count": len(rels),
                    "relationships": [str(rel["_id"]) for rel in rels]
                })
        
        # Step 3: Check for inconsistent relationships (75%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 75, "total": 100, "status": "Checking for inconsistent relationships..."}
        )
        
        # Find relationships with very different strengths for the same entity pair
        inconsistent_relationships = []
        for key, rels in relationship_groups.items():
            if len(rels) > 1:
                strengths = [rel["relationship_strength"] for rel in rels]
                max_strength = max(strengths)
                min_strength = min(strengths)
                
                # If strength difference is too large, mark as inconsistent
                if max_strength - min_strength > 0.5:
                    inconsistent_relationships.append({
                        "key": key,
                        "strength_range": [min_strength, max_strength],
                        "relationships": [str(rel["_id"]) for rel in rels]
                    })
        
        # Step 4: Generate report (100%)
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Graph consistency check complete!"}
        )
        
        result = {
            "current": 100,
            "total": 100,
            "status": "Graph consistency check complete!",
            "result": {
                "orphaned_entities": len(orphaned_entities),
                "duplicate_relationships": len(duplicate_relationships),
                "inconsistent_relationships": len(inconsistent_relationships),
                "orphaned_entity_names": orphaned_entities[:10],  # Limit to first 10
                "duplicate_relationship_details": duplicate_relationships[:5],  # Limit to first 5
                "inconsistent_relationship_details": inconsistent_relationships[:5]  # Limit to first 5
            }
        }
        
        logger.info(f"Graph consistency check complete: {len(orphaned_entities)} orphaned entities, {len(duplicate_relationships)} duplicate relationships, {len(inconsistent_relationships)} inconsistent relationships")
        return result
        
    except Exception as e:
        error_msg = f"Error in graph consistency check: {str(e)}"
        logger.error(error_msg)
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": error_msg}
        )
        
        return {
            "current": 0,
            "total": 100,
            "status": error_msg,
            "result": {
                "error": str(e)
            }
        }


@celery_app.task(bind=True)
def cleanup_orphaned_entities(self, entity_names: list):
    """
    Clean up orphaned entities (entities with no relationships)
    
    Args:
        entity_names: List of entity names to clean up
        
    Returns:
        Dict with cleanup results
    """
    try:
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting orphaned entity cleanup..."}
        )
        
        # Get database connection
        db = get_sync_database()
        
        logger.info(f"Cleaning up {len(entity_names)} orphaned entities...")
        
        # Delete orphaned entities
        deleted_count = 0
        for entity_name in entity_names:
            result = db.entities.delete_one({"entity_name": entity_name})
            if result.deleted_count > 0:
                deleted_count += 1
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Orphaned entity cleanup complete!"}
        )
        
        result = {
            "current": 100,
            "total": 100,
            "status": "Orphaned entity cleanup complete!",
            "result": {
                "entities_to_cleanup": len(entity_names),
                "entities_deleted": deleted_count
            }
        }
        
        logger.info(f"Orphaned entity cleanup complete: {deleted_count} entities deleted")
        return result
        
    except Exception as e:
        error_msg = f"Error in orphaned entity cleanup: {str(e)}"
        logger.error(error_msg)
        
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": error_msg}
        )
        
        return {
            "current": 0,
            "total": 100,
            "status": error_msg,
            "result": {
                "error": str(e)
            }
        }
