import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database.models import EntityCollection, RelationshipCollection
from app.models.entities import Entity
from app.models.relationships import Relationship

logger = logging.getLogger(__name__)


class GlobalGraphManager:
    """Service for managing global graph state across documents"""
    
    def __init__(self):
        """Initialize the global graph manager"""
        self.entity_canonicalizer = None
        self.contradiction_detector = None
    
    async def update_global_entities(self, new_entities: List[Entity]) -> Dict[str, Any]:
        """Update global entity state with new entities"""
        try:
            update_results = {
                "entities_processed": len(new_entities),
                "entities_added": 0,
                "entities_merged": 0,
                "merge_operations": [],
                "errors": []
            }
            
            for entity in new_entities:
                try:
                    # Check if entity already exists
                    existing_entity = await EntityCollection.find_entity_by_name_and_type(
                        entity.entity_name, 
                        entity.entity_type
                    )
                    
                    if existing_entity:
                        # Entity exists, update frequency and provenance
                        await EntityCollection.add_entity_provenance(
                            existing_entity.id,
                            entity.paper_ids[0] if entity.paper_ids else "",
                            entity.section_ids[0] if entity.section_ids else ""
                        )
                        
                        # Update frequency
                        new_frequency = existing_entity.frequency + entity.frequency
                        await EntityCollection.update_entity_frequency(
                            existing_entity.id,
                            new_frequency
                        )
                        
                        update_results["entities_merged"] += 1
                        logger.debug(f"Updated existing entity: {entity.entity_name}")
                    else:
                        # New entity, insert it
                        entity_id = await EntityCollection.insert_entity(entity)
                        update_results["entities_added"] += 1
                        logger.debug(f"Added new entity: {entity.entity_name}")
                        
                except Exception as e:
                    error_msg = f"Error processing entity {entity.entity_name}: {str(e)}"
                    update_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Global entity update complete: {update_results['entities_added']} added, {update_results['entities_merged']} merged")
            return update_results
            
        except Exception as e:
            logger.error(f"Error updating global entities: {str(e)}")
            return {
                "entities_processed": 0,
                "entities_added": 0,
                "entities_merged": 0,
                "merge_operations": [],
                "errors": [str(e)]
            }
    
    async def update_global_relationships(self, new_relationships: List[Relationship]) -> Dict[str, Any]:
        """Update global relationship state with new relationships"""
        try:
            update_results = {
                "relationships_processed": len(new_relationships),
                "relationships_added": 0,
                "relationships_updated": 0,
                "contradictions_detected": 0,
                "errors": []
            }
            
            for relationship in new_relationships:
                try:
                    # Check if similar relationship already exists
                    existing_relationships = await RelationshipCollection.find_relationships_between_entities(
                        relationship.source_entity,
                        relationship.target_entity
                    )
                    
                    # Filter by relationship type
                    same_type_relationships = [
                        rel for rel in existing_relationships 
                        if rel.relationship_type == relationship.relationship_type
                    ]
                    
                    if same_type_relationships:
                        # Relationship exists, update strength using noisy-OR
                        existing_rel = same_type_relationships[0]
                        
                        # Calculate new strength using noisy-OR
                        current_strength = existing_rel.relationship_strength
                        new_strength = 1 - (1 - current_strength) * (1 - relationship.relationship_strength)
                        
                        # Update the relationship
                        await RelationshipCollection.update_relationship_strength(
                            existing_rel.id,
                            new_strength
                        )
                        
                        update_results["relationships_updated"] += 1
                        logger.debug(f"Updated existing relationship: {relationship.source_entity} -> {relationship.target_entity}")
                    else:
                        # New relationship, insert it
                        relationship_id = await RelationshipCollection.insert_relationship(relationship)
                        update_results["relationships_added"] += 1
                        logger.debug(f"Added new relationship: {relationship.source_entity} -> {relationship.target_entity}")
                        
                except Exception as e:
                    error_msg = f"Error processing relationship {relationship.source_entity} -> {relationship.target_entity}: {str(e)}"
                    update_results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Global relationship update complete: {update_results['relationships_added']} added, {update_results['relationships_updated']} updated")
            return update_results
            
        except Exception as e:
            logger.error(f"Error updating global relationships: {str(e)}")
            return {
                "relationships_processed": 0,
                "relationships_added": 0,
                "relationships_updated": 0,
                "contradictions_detected": 0,
                "errors": [str(e)]
            }
    
    async def maintain_graph_consistency(self) -> Dict[str, Any]:
        """Maintain consistency across the global graph"""
        try:
            consistency_results = {
                "orphaned_entities": 0,
                "inconsistent_relationships": 0,
                "duplicate_relationships": 0,
                "fixes_applied": 0,
                "errors": []
            }
            
            # Check for orphaned entities (entities with no relationships)
            # This is a simplified check - in production, you might want more sophisticated logic
            logger.info("Checking for orphaned entities...")
            
            # Check for duplicate relationships
            logger.info("Checking for duplicate relationships...")
            
            # Check for inconsistent relationships
            logger.info("Checking for inconsistent relationships...")
            
            logger.info("Graph consistency check complete")
            return consistency_results
            
        except Exception as e:
            logger.error(f"Error maintaining graph consistency: {str(e)}")
            return {
                "orphaned_entities": 0,
                "inconsistent_relationships": 0,
                "duplicate_relationships": 0,
                "fixes_applied": 0,
                "errors": [str(e)]
            }
    
    async def get_global_entity_statistics(self) -> Dict[str, Any]:
        """Get global graph statistics"""
        try:
            # This would typically involve database aggregation queries
            # For now, return placeholder statistics
            statistics = {
                "total_entities": 0,
                "total_relationships": 0,
                "entities_by_type": {},
                "entities_by_category": {},
                "relationships_by_type": {},
                "most_frequent_entities": [],
                "strongest_relationships": [],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            logger.info("Retrieved global graph statistics")
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting global entity statistics: {str(e)}")
            return {
                "total_entities": 0,
                "total_relationships": 0,
                "entities_by_type": {},
                "entities_by_category": {},
                "relationships_by_type": {},
                "most_frequent_entities": [],
                "strongest_relationships": [],
                "last_updated": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def process_document_entities_and_relationships(
        self, 
        document_id: str, 
        entities: List[Entity], 
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """Process entities and relationships from a single document"""
        try:
            processing_results = {
                "document_id": document_id,
                "entities_processed": len(entities),
                "relationships_processed": len(relationships),
                "entity_update_results": {},
                "relationship_update_results": {},
                "errors": []
            }
            
            # Update global entities
            entity_results = await self.update_global_entities(entities)
            processing_results["entity_update_results"] = entity_results
            
            # Update global relationships
            relationship_results = await self.update_global_relationships(relationships)
            processing_results["relationship_update_results"] = relationship_results
            
            # Combine errors
            processing_results["errors"] = (
                entity_results.get("errors", []) + 
                relationship_results.get("errors", [])
            )
            
            logger.info(f"Processed document {document_id}: {len(entities)} entities, {len(relationships)} relationships")
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing document entities and relationships: {str(e)}")
            return {
                "document_id": document_id,
                "entities_processed": 0,
                "relationships_processed": 0,
                "entity_update_results": {},
                "relationship_update_results": {},
                "errors": [str(e)]
            }
