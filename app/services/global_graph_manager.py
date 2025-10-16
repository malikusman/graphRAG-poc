import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.database.models import EntityCollection, RelationshipCollection
from app.models.entities import Entity, EntityType, EntityCategory
from app.models.relationships import Relationship, RelationshipType
from app.services.entity_canonicalizer import EntityCanonicalizer
from app.services.contradiction_detector import ContradictionDetector
from app.services.contradiction_resolver import ContradictionResolver
from app.services.relationship_consolidator import RelationshipConsolidator
from app.utils.math_utils import calculate_noisy_or_strength

logger = logging.getLogger(__name__)


class GlobalGraphManager:
    """Enhanced service for managing global graph state across documents with integrated Reduce phase services"""
    
    def __init__(self):
        """Initialize the enhanced global graph manager with all Reduce phase services"""
        # Initialize enhanced Reduce phase services
        self.entity_canonicalizer = EntityCanonicalizer()
        self.contradiction_detector = ContradictionDetector()
        self.contradiction_resolver = ContradictionResolver()
        self.relationship_consolidator = RelationshipConsolidator()
        
        # Global graph state cache
        self._global_entities_cache = {}
        self._global_relationships_cache = {}
        self._cache_last_updated = None
        self._cache_ttl_seconds = 300  # 5 minutes cache TTL
    
    async def load_global_graph_state(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Load existing global entities and relationships from database with caching"""
        try:
            # Check if cache is still valid
            if not force_refresh and self._is_cache_valid():
                logger.debug("Using cached global graph state")
                return {
                    "global_entities": list(self._global_entities_cache.values()),
                    "global_relationships": list(self._global_relationships_cache.values()),
                    "cache_hit": True
                }
            
            logger.info("Loading global graph state from database...")
            
            # Load all entities from database
            entities_collection = await EntityCollection.get_collection()
            entities_cursor = entities_collection.find({})
            global_entities = []
            async for entity_doc in entities_cursor:
                entity_doc["_id"] = str(entity_doc["_id"])
                global_entities.append(entity_doc)
            
            # Load all relationships from database
            relationships_collection = await RelationshipCollection.get_collection()
            relationships_cursor = relationships_collection.find({})
            global_relationships = []
            async for rel_doc in relationships_cursor:
                rel_doc["_id"] = str(rel_doc["_id"])
                global_relationships.append(rel_doc)
            
            # Update cache
            self._update_cache(global_entities, global_relationships)
            
            logger.info(f"Loaded global graph state: {len(global_entities)} entities, {len(global_relationships)} relationships")
            
            return {
                "global_entities": global_entities,
                "global_relationships": global_relationships,
                "cache_hit": False,
                "total_entities": len(global_entities),
                "total_relationships": len(global_relationships)
            }
            
        except Exception as e:
            logger.error(f"Error loading global graph state: {str(e)}")
            return {
                "global_entities": [],
                "global_relationships": [],
                "cache_hit": False,
                "error": str(e)
            }
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid"""
        if self._cache_last_updated is None:
            return False
        
        time_since_update = (datetime.utcnow() - self._cache_last_updated).total_seconds()
        return time_since_update < self._cache_ttl_seconds
    
    def _update_cache(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]):
        """Update the global graph cache"""
        self._global_entities_cache = {entity["_id"]: entity for entity in entities}
        self._global_relationships_cache = {rel["_id"]: rel for rel in relationships}
        self._cache_last_updated = datetime.utcnow()
    
    async def get_global_entity_by_name_and_type(self, entity_name: str, entity_type: EntityType) -> Optional[Dict[str, Any]]:
        """Get a global entity by name and type"""
        try:
            # First check cache
            for entity in self._global_entities_cache.values():
                if (entity.get("entity_name") == entity_name and 
                    entity.get("entity_type") == entity_type):
                    return entity
            
            # If not in cache, query database
            entity_response = await EntityCollection.find_entity_by_name_and_type(entity_name, entity_type)
            if entity_response:
                entity_dict = entity_response.model_dump()
                entity_dict["_id"] = str(entity_response._id) if hasattr(entity_response, '_id') else None
                return entity_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting global entity {entity_name} ({entity_type}): {str(e)}")
            return None
    
    async def get_global_relationships_by_entity(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all global relationships for an entity"""
        try:
            # First check cache
            cached_relationships = []
            for rel in self._global_relationships_cache.values():
                if (rel.get("source_entity") == entity_name or 
                    rel.get("target_entity") == entity_name):
                    cached_relationships.append(rel)
            
            if cached_relationships:
                return cached_relationships
            
            # If not in cache, query database
            relationship_responses = await RelationshipCollection.get_relationships_by_entity(entity_name)
            relationships = []
            for rel_response in relationship_responses:
                rel_dict = rel_response.model_dump()
                rel_dict["_id"] = str(rel_response._id) if hasattr(rel_response, '_id') else None
                relationships.append(rel_dict)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting global relationships for entity {entity_name}: {str(e)}")
            return []
    
    async def process_document_against_global_graph(
        self, 
        document_id: str, 
        entities: List[Entity], 
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """Process new document against existing global graph using enhanced Reduce phase services"""
        try:
            logger.info(f"Processing document {document_id} against global graph: {len(entities)} entities, {len(relationships)} relationships")
            
            # Load global graph state
            global_state = await self.load_global_graph_state()
            if global_state.get("error"):
                return {
                    "document_id": document_id,
                    "error": f"Failed to load global graph state: {global_state['error']}",
                    "entities_processed": 0,
                    "relationships_processed": 0
                }
            
            processing_results = {
                "document_id": document_id,
                "entities_processed": len(entities),
                "relationships_processed": len(relationships),
                "global_entities_count": len(global_state["global_entities"]),
                "global_relationships_count": len(global_state["global_relationships"]),
                "entity_canonicalization_results": {},
                "contradiction_detection_results": {},
                "relationship_consolidation_results": {},
                "global_graph_updates": {},
                "errors": []
            }
            
            # Step 1: Entity Canonicalization with Global Context
            logger.info("Step 1: Processing entity canonicalization with global context...")
            try:
                canonicalization_results = await self.entity_canonicalizer.process_entity_canonicalization_with_context(
                    entities, global_state["global_entities"]
                )
                processing_results["entity_canonicalization_results"] = canonicalization_results
                logger.info(f"Entity canonicalization complete: {len(canonicalization_results.get('merge_operations', []))} merge operations")
            except Exception as e:
                error_msg = f"Error in entity canonicalization: {str(e)}"
                logger.error(error_msg)
                processing_results["errors"].append(error_msg)
            
            # Step 2: Contradiction Detection and Resolution
            logger.info("Step 2: Processing contradiction detection and resolution...")
            try:
                contradiction_results = await self.contradiction_detector.process_contradiction_detection_with_resolver(
                    relationships, self.contradiction_resolver
                )
                processing_results["contradiction_detection_results"] = contradiction_results
                logger.info(f"Contradiction processing complete: {len(contradiction_results.get('contradictions', []))} contradictions detected")
            except Exception as e:
                error_msg = f"Error in contradiction detection: {str(e)}"
                logger.error(error_msg)
                processing_results["errors"].append(error_msg)
            
            # Step 3: Relationship Consolidation
            logger.info("Step 3: Processing relationship consolidation...")
            try:
                consolidation_results = await self.relationship_consolidator.consolidate_relationships(relationships)
                processing_results["relationship_consolidation_results"] = consolidation_results
                logger.info(f"Relationship consolidation complete: {len(consolidation_results.get('consolidated_relationships', []))} consolidated relationships")
            except Exception as e:
                error_msg = f"Error in relationship consolidation: {str(e)}"
                logger.error(error_msg)
                processing_results["errors"].append(error_msg)
            
            # Step 4: Update Global Graph
            logger.info("Step 4: Updating global graph with processed results...")
            try:
                global_updates = await self._update_global_graph_with_results(
                    canonicalization_results,
                    contradiction_results,
                    consolidation_results
                )
                processing_results["global_graph_updates"] = global_updates
                logger.info(f"Global graph updates complete: {global_updates.get('entities_updated', 0)} entities, {global_updates.get('relationships_updated', 0)} relationships")
            except Exception as e:
                error_msg = f"Error updating global graph: {str(e)}"
                logger.error(error_msg)
                processing_results["errors"].append(error_msg)
            
            # Invalidate cache to force refresh on next access
            self._cache_last_updated = None
            
            logger.info(f"Document {document_id} processing complete against global graph")
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing document {document_id} against global graph: {str(e)}")
            return {
                "document_id": document_id,
                "error": str(e),
                "entities_processed": 0,
                "relationships_processed": 0
            }
    
    async def _update_global_graph_with_results(
        self,
        canonicalization_results: Dict[str, Any],
        contradiction_results: Dict[str, Any],
        consolidation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update global graph with processed results from Reduce phase services"""
        try:
            update_summary = {
                "entities_updated": 0,
                "entities_added": 0,
                "relationships_updated": 0,
                "relationships_added": 0,
                "merge_operations": 0,
                "contradiction_resolutions": 0,
                "consolidation_operations": 0,
                "errors": []
            }
            
            # Update entities based on canonicalization results
            if canonicalization_results.get("merge_operations"):
                for merge_op in canonicalization_results["merge_operations"]:
                    try:
                        await self._process_entity_merge_operation(merge_op)
                        update_summary["merge_operations"] += 1
                    except Exception as e:
                        error_msg = f"Error processing entity merge operation: {str(e)}"
                        logger.error(error_msg)
                        update_summary["errors"].append(error_msg)
            
            # Update relationships based on contradiction resolution results
            if contradiction_results.get("resolutions"):
                for resolution in contradiction_results["resolutions"]:
                    try:
                        await self._process_relationship_resolution(resolution)
                        update_summary["contradiction_resolutions"] += 1
                    except Exception as e:
                        error_msg = f"Error processing relationship resolution: {str(e)}"
                        logger.error(error_msg)
                        update_summary["errors"].append(error_msg)
            
            # Update relationships based on consolidation results
            if consolidation_results.get("consolidated_relationships"):
                for consolidation_result in consolidation_results["consolidated_relationships"]:
                    try:
                        await self._process_relationship_consolidation(consolidation_result)
                        update_summary["consolidation_operations"] += 1
                    except Exception as e:
                        error_msg = f"Error processing relationship consolidation: {str(e)}"
                        logger.error(error_msg)
                        update_summary["errors"].append(error_msg)
            
            return update_summary
            
        except Exception as e:
            logger.error(f"Error updating global graph with results: {str(e)}")
            return {"error": str(e)}
    
    async def _process_entity_merge_operation(self, merge_operation: Dict[str, Any]) -> bool:
        """Process a single entity merge operation"""
        try:
            source_entity_name = merge_operation.get("source_entity")
            target_entity_name = merge_operation.get("target_entity")
            confidence = merge_operation.get("confidence", 0.0)
            
            if confidence < 0.8:  # Only merge high-confidence entities
                logger.info(f"Skipping low-confidence entity merge: {source_entity_name} -> {target_entity_name} (confidence: {confidence})")
                return False
            
            # Find source entity in database
            source_entity = await EntityCollection.find_entity_by_name_and_type(
                source_entity_name, 
                merge_operation.get("source_entity_type")
            )
            
            if not source_entity:
                logger.warning(f"Source entity not found for merge: {source_entity_name}")
                return False
            
            # Find target entity in database
            target_entity = await EntityCollection.find_entity_by_name_and_type(
                target_entity_name,
                merge_operation.get("target_entity_type")
            )
            
            if not target_entity:
                logger.warning(f"Target entity not found for merge: {target_entity_name}")
                return False
            
            # Merge entities (combine aliases, paper_ids, section_ids, update frequency)
            merged_aliases = list(set(source_entity.aliases + target_entity.aliases))
            merged_paper_ids = list(set(source_entity.paper_ids + target_entity.paper_ids))
            merged_section_ids = list(set(source_entity.section_ids + target_entity.section_ids))
            merged_frequency = source_entity.frequency + target_entity.frequency
            
            # Update target entity with merged data
            await EntityCollection.update_entity_merge(
                str(target_entity._id),
                merged_aliases,
                merged_paper_ids,
                merged_section_ids,
                merged_frequency
            )
            
            # Delete source entity
            await EntityCollection.delete_entity(str(source_entity._id))
            
            logger.info(f"Successfully merged entities: {source_entity_name} -> {target_entity_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing entity merge operation: {str(e)}")
            return False
    
    async def _process_relationship_resolution(self, resolution: Dict[str, Any]) -> bool:
        """Process a single relationship resolution"""
        try:
            resolved_relationship = resolution.get("resolved_relationship")
            if not resolved_relationship:
                return False
            
            # Update or insert the resolved relationship
            relationship = Relationship(
                source_entity=resolved_relationship["source_entity"],
                target_entity=resolved_relationship["target_entity"],
                relationship_type=resolved_relationship["relationship_type"],
                relationship_strength=resolved_relationship["relationship_strength"],
                description=resolved_relationship["description"],
                paper_ids=resolved_relationship.get("paper_ids", []),
                section_ids=resolved_relationship.get("section_ids", [])
            )
            
            # Check if relationship already exists
            existing_relationship = await RelationshipCollection.find_relationship_by_entities_and_type(
                relationship.source_entity,
                relationship.target_entity,
                relationship.relationship_type
            )
            
            if existing_relationship:
                # Update existing relationship with Noisy-OR strength
                existing_strengths = [existing_relationship.relationship_strength, relationship.relationship_strength]
                new_strength = calculate_noisy_or_strength(existing_strengths)
                
                await RelationshipCollection.update_relationship_strength(
                    str(existing_relationship._id),
                    new_strength
                )
                
                # Update provenance
                merged_paper_ids = list(set(existing_relationship.paper_ids + relationship.paper_ids))
                merged_section_ids = list(set(existing_relationship.section_ids + relationship.section_ids))
                
                await RelationshipCollection.update_relationship_provenance(
                    str(existing_relationship._id),
                    merged_paper_ids,
                    merged_section_ids
                )
            else:
                # Insert new relationship
                await RelationshipCollection.insert_relationship(relationship)
            
            logger.info(f"Successfully processed relationship resolution: {relationship.source_entity} -> {relationship.target_entity}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing relationship resolution: {str(e)}")
            return False
    
    async def _process_relationship_consolidation(self, consolidation_result: Dict[str, Any]) -> bool:
        """Process a single relationship consolidation"""
        try:
            consolidated_rel = consolidation_result.get("consolidation_result", {}).get("consolidated_relationship")
            if not consolidated_rel:
                return False
            
            # Create consolidated relationship
            relationship = Relationship(
                source_entity=consolidated_rel["source_entity"],
                target_entity=consolidated_rel["target_entity"],
                relationship_type=consolidated_rel["relationship_type"],
                relationship_strength=consolidated_rel["relationship_strength"],
                description=consolidated_rel["description"],
                paper_ids=consolidated_rel.get("paper_ids", []),
                section_ids=consolidated_rel.get("section_ids", [])
            )
            
            # Check if relationship already exists
            existing_relationship = await RelationshipCollection.find_relationship_by_entities_and_type(
                relationship.source_entity,
                relationship.target_entity,
                relationship.relationship_type
            )
            
            if existing_relationship:
                # Update existing relationship with consolidated strength
                await RelationshipCollection.update_relationship_strength(
                    str(existing_relationship._id),
                    relationship.relationship_strength
                )
                
                # Update provenance
                await RelationshipCollection.update_relationship_provenance(
                    str(existing_relationship._id),
                    relationship.paper_ids,
                    relationship.section_ids
                )
            else:
                # Insert new consolidated relationship
                await RelationshipCollection.insert_relationship(relationship)
            
            logger.info(f"Successfully processed relationship consolidation: {relationship.source_entity} -> {relationship.target_entity}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing relationship consolidation: {str(e)}")
            return False
    
    async def update_global_entities(self, new_entities: List[Entity]) -> Dict[str, Any]:
        """Legacy method - use process_document_against_global_graph instead"""
        logger.warning("update_global_entities is deprecated. Use process_document_against_global_graph instead.")
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
                        # Update existing entity
                        await EntityCollection.update_entity_frequency(
                            str(existing_entity._id),
                            existing_entity.frequency + entity.frequency
                        )
                        await EntityCollection.add_entity_provenance(
                            str(existing_entity._id),
                            entity.paper_ids[0] if entity.paper_ids else "",
                            entity.section_ids[0] if entity.section_ids else ""
                        )
                        update_results["entities_merged"] += 1
                    else:
                        # Insert new entity
                        await EntityCollection.insert_entity(entity)
                        update_results["entities_added"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing entity {entity.entity_name}: {str(e)}"
                    logger.error(error_msg)
                    update_results["errors"].append(error_msg)
            
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
        """Legacy method - use process_document_against_global_graph instead"""
        logger.warning("update_global_relationships is deprecated. Use process_document_against_global_graph instead.")
        try:
            update_results = {
                "relationships_processed": len(new_relationships),
                "relationships_added": 0,
                "relationships_updated": 0,
                "errors": []
            }
            
            for relationship in new_relationships:
                try:
                    # Check if relationship already exists
                    existing_relationship = await RelationshipCollection.find_relationship_by_entities_and_type(
                        relationship.source_entity,
                        relationship.target_entity,
                        relationship.relationship_type
                    )
                    
                    if existing_relationship:
                        # Update existing relationship with Noisy-OR strength
                        existing_strengths = [existing_relationship.relationship_strength, relationship.relationship_strength]
                        new_strength = calculate_noisy_or_strength(existing_strengths)
                        
                        await RelationshipCollection.update_relationship_strength(
                            str(existing_relationship._id),
                            new_strength
                        )
                        
                        # Update provenance
                        merged_paper_ids = list(set(existing_relationship.paper_ids + relationship.paper_ids))
                        merged_section_ids = list(set(existing_relationship.section_ids + relationship.section_ids))
                        
                        await RelationshipCollection.update_relationship_provenance(
                            str(existing_relationship._id),
                            merged_paper_ids,
                            merged_section_ids
                        )
                        update_results["relationships_updated"] += 1
                    else:
                        # Insert new relationship
                        await RelationshipCollection.insert_relationship(relationship)
                        update_results["relationships_added"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing relationship {relationship.source_entity} -> {relationship.target_entity}: {str(e)}"
                    logger.error(error_msg)
                    update_results["errors"].append(error_msg)
            
            return update_results
            
        except Exception as e:
            logger.error(f"Error updating global relationships: {str(e)}")
            return {
                "relationships_processed": 0,
                "relationships_added": 0,
                "relationships_updated": 0,
                "errors": [str(e)]
            }
    
    async def get_global_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the global graph"""
        try:
            # Load global state
            global_state = await self.load_global_graph_state()
            
            if global_state.get("error"):
                return {"error": global_state["error"]}
            
            entities = global_state["global_entities"]
            relationships = global_state["global_relationships"]
            
            # Calculate entity statistics
            entity_types = {}
            entity_categories = {}
            for entity in entities:
                entity_type = entity.get("entity_type", "unknown")
                entity_category = entity.get("entity_category", "unknown")
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                entity_categories[entity_category] = entity_categories.get(entity_category, 0) + 1
            
            # Calculate relationship statistics
            relationship_types = {}
            for relationship in relationships:
                rel_type = relationship.get("relationship_type", "unknown")
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
            
            # Calculate average relationship strength
            strengths = [rel.get("relationship_strength", 0.0) for rel in relationships]
            avg_strength = sum(strengths) / len(strengths) if strengths else 0.0
            
            return {
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "entity_types_distribution": entity_types,
                "entity_categories_distribution": entity_categories,
                "relationship_types_distribution": relationship_types,
                "average_relationship_strength": avg_strength,
                "cache_hit": global_state.get("cache_hit", False),
                "last_updated": self._cache_last_updated.isoformat() if self._cache_last_updated else None
            }
            
        except Exception as e:
            logger.error(f"Error getting global graph statistics: {str(e)}")
            return {"error": str(e)}
    
    async def process_document_entities_and_relationships(
        self, 
        document_id: str, 
        entities: List[Entity], 
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """Legacy method - use process_document_against_global_graph instead"""
        logger.warning("process_document_entities_and_relationships is deprecated. Use process_document_against_global_graph instead.")
        return await self.process_document_against_global_graph(document_id, entities, relationships)
